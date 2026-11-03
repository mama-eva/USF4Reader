"""Bind this research profile to the exact, authorized executable."""

import hashlib
import struct
from pathlib import Path

from .memory_reader import ProcessMemory

EXE_SHA256 = "a9017416ee8104cdde64d79f1e47697c1dfecb3d58496e4950945c3e37dea537"
IMAGE_SIZE = 0x9A0000


class UnsupportedGame(ValueError):
	pass


def validate_path(path):
	if Path(path).name.casefold() != "ssfiv.exe":
		raise UnsupportedGame("This build supports only the verified game installation.")


def verify_executable(path):
	validate_path(path)
	with Path(path).open("rb") as stream:
		digest = hashlib.file_digest(stream, "sha256").hexdigest()
	if digest != EXE_SHA256:
		raise UnsupportedGame("The game executable does not match the verified profile. Reading stopped.")


def connect(pid, verify=True):
	memory = ProcessMemory(pid)
	try:
		path = memory.image_path()
		validate_path(path)
		if verify:
			verify_executable(path)
		base, size = memory.module()
		if size != IMAGE_SIZE or memory.read(base, 2) != b"MZ":
			raise UnsupportedGame("The process image does not match the verified profile.")
		pe_offset = memory.u32(base + 0x3C)
		if pe_offset > 0x1000:
			raise UnsupportedGame("The executable header does not match the profile.")
		signature = memory.read(base + pe_offset, 26)
		if signature[:4] != b"PE\0\0" or struct.unpack_from("<H", signature, 4)[0] != 0x14C:
			raise UnsupportedGame("This profile requires the verified 32-bit x86 executable.")
		return memory, base
	except Exception:
		memory.close()
		raise
