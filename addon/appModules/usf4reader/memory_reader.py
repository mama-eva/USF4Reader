"""Windows process access with query and read permissions only."""

import ctypes
import struct
from ctypes import wintypes as w


class MemoryReadError(OSError):
	def __init__(self, *args, operation="", address=None, size=None):
		super().__init__(*args)
		self.operation = operation
		self.address = address
		self.size = size


class MODULEENTRY32W(ctypes.Structure):
	_fields_ = [
		("dwSize", w.DWORD),
		("th32ModuleID", w.DWORD),
		("th32ProcessID", w.DWORD),
		("GlblcntUsage", w.DWORD),
		("ProccntUsage", w.DWORD),
		("modBaseAddr", ctypes.POINTER(ctypes.c_ubyte)),
		("modBaseSize", w.DWORD),
		("hModule", w.HMODULE),
		("szModule", w.WCHAR * 256),
		("szExePath", w.WCHAR * 260),
	]


class ProcessMemory:
	def __init__(self, pid):
		self.pid = pid
		self.handle = None
		self.k = ctypes.WinDLL("kernel32", use_last_error=True)
		self.k.OpenProcess.argtypes = (w.DWORD, w.BOOL, w.DWORD)
		self.k.OpenProcess.restype = w.HANDLE
		self.k.CloseHandle.argtypes = (w.HANDLE,)
		self.k.CloseHandle.restype = w.BOOL
		self.k.GetExitCodeProcess.argtypes = (w.HANDLE, ctypes.POINTER(w.DWORD))
		self.k.GetExitCodeProcess.restype = w.BOOL
		self.k.ReadProcessMemory.argtypes = (
			w.HANDLE,
			ctypes.c_void_p,
			ctypes.c_void_p,
			ctypes.c_size_t,
			ctypes.POINTER(ctypes.c_size_t),
		)
		self.k.ReadProcessMemory.restype = w.BOOL
		self.k.QueryFullProcessImageNameW.argtypes = (w.HANDLE, w.DWORD, w.LPWSTR, ctypes.POINTER(w.DWORD))
		self.k.QueryFullProcessImageNameW.restype = w.BOOL
		self.k.CreateToolhelp32Snapshot.argtypes = (w.DWORD, w.DWORD)
		self.k.CreateToolhelp32Snapshot.restype = w.HANDLE
		self.k.Module32FirstW.argtypes = (w.HANDLE, ctypes.POINTER(MODULEENTRY32W))
		self.k.Module32FirstW.restype = w.BOOL
		# PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_VM_READ, never VM_WRITE/OPERATION.
		self.handle = self.k.OpenProcess(0x1000 | 0x10, False, pid)
		if not self.handle:
			raise MemoryReadError(ctypes.get_last_error(), "OpenProcess falhou", operation="open")

	def image_path(self):
		buf = ctypes.create_unicode_buffer(32768)
		size = w.DWORD(len(buf))
		if not self.k.QueryFullProcessImageNameW(self.handle, 0, buf, ctypes.byref(size)):
			raise MemoryReadError(
				ctypes.get_last_error(), "Não foi possível consultar o executável", operation="query"
			)
		return buf.value

	def is_running(self):
		code = w.DWORD()
		if not self.handle or not self.k.GetExitCodeProcess(self.handle, ctypes.byref(code)):
			return False
		return code.value == 259  # STILL_ACTIVE

	def module(self):
		snap = self.k.CreateToolhelp32Snapshot(0x8 | 0x10, self.pid)
		if snap == ctypes.c_void_p(-1).value:
			raise MemoryReadError(ctypes.get_last_error(), "Snapshot de módulos falhou")
		try:
			entry = MODULEENTRY32W()
			entry.dwSize = ctypes.sizeof(entry)
			if not self.k.Module32FirstW(snap, ctypes.byref(entry)):
				raise MemoryReadError(ctypes.get_last_error(), "Module32First falhou")
			return ctypes.cast(entry.modBaseAddr, ctypes.c_void_p).value, entry.modBaseSize
		finally:
			self.k.CloseHandle(snap)

	def read(self, address, size):
		if not self.handle or not 0x10000 <= address <= 0xFFFFFFFF or not 0 < size <= 1024 * 1024:
			raise MemoryReadError("Endereço ou tamanho de leitura inválido")
		if address + size > 0x100000000:
			raise MemoryReadError("Leitura ultrapassa o espaço de endereços de 32 bits")
		buf = ctypes.create_string_buffer(size)
		got = ctypes.c_size_t()
		ok = self.k.ReadProcessMemory(self.handle, address, buf, size, ctypes.byref(got))
		if not ok or got.value != size:
			raise MemoryReadError(
				ctypes.get_last_error(),
				"Leitura de memória incompleta",
				operation="read",
				address=address,
				size=size,
			)
		return buf.raw

	def u32(self, address):
		return struct.unpack("<I", self.read(address, 4))[0]

	def close(self):
		if self.handle:
			self.k.CloseHandle(self.handle)
			self.handle = None

	def __enter__(self):
		return self

	def __exit__(self, *_):
		self.close()
