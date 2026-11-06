"""Cover game detection without needing an installed copy of the game."""

import struct
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "addon/appModules"))
from usf4reader.game_process import UnsupportedGame, connect
from usf4reader.game_state import (
	APP_CONTROLLER_RVA,
	CHILD_CONTROLLER_GETTER,
	CONTROLLER_VTABLE_RVA,
	ROOT_VTABLE_RVA,
)
from usf4reader.memory_reader import MemoryReadError


class GameProcessTests(unittest.TestCase):
	def setUp(self):
		self.base = 0x10000000
		self.pe_offset = 0x100
		self.getter = self.base + 0x380000
		self.segments = {
			self.base: b"MZ",
			self.base + 0x3C: struct.pack("<I", self.pe_offset),
			self.base + self.pe_offset: self._pe_header(0x14C, 0x10B),
			self.base + CONTROLLER_VTABLE_RVA: struct.pack("<I", self.base + 0x260000),
			self.base + ROOT_VTABLE_RVA + 0x24: struct.pack("<I", self.getter),
			self.getter: CHILD_CONTROLLER_GETTER,
			self.base + APP_CONTROLLER_RVA: bytes(4),
		}
		process = patch("usf4reader.game_process.ProcessMemory")
		self.addCleanup(process.stop)
		self.memory = process.start().return_value
		self.memory.image_path.return_value = r"C:\Steam Library\steamapps\common\Game\Ssfiv.Exe"
		self.memory.module.return_value = self.base, 0x9B0000
		self.memory.read.side_effect = self._read
		self.memory.u32.side_effect = lambda address: struct.unpack("<I", self._read(address, 4))[0]

	@staticmethod
	def _pe_header(machine, magic):
		return struct.pack("<4sHHIIIHHH", b"PE\0\0", machine, 4, 123, 0, 0, 224, 0, magic)

	def _read(self, address, length):
		result = self.segments[address]
		self.assertEqual(len(result), length)
		return result

	def test_accepts_compatible_layout_at_different_base_size_and_path_before_startup(self):
		for size in (0x980000, 0x9B0000):
			with self.subTest(size=size):
				self.memory.module.return_value = self.base, size
				with patch.object(Path, "open", side_effect=AssertionError("Executable opened")):
					self.assertEqual(connect(1234), (self.memory, self.base))
		self.memory.close.assert_not_called()

	def test_rejects_other_process_name_before_reading_memory(self):
		self.memory.image_path.return_value = r"C:\Games\OtherGame.exe"
		with self.assertRaisesRegex(UnsupportedGame, "requires the SSFIV.exe game process"):
			connect(1234)
		self.memory.read.assert_not_called()
		self.memory.close.assert_called_once()

	def test_rejects_invalid_or_out_of_range_header_before_following_it(self):
		for offset in (0, self.memory.module.return_value[1]):
			with self.subTest(offset=offset):
				self.segments[self.base + 0x3C] = struct.pack("<I", offset)
				with self.assertRaisesRegex(UnsupportedGame, "unsupported game layout"):
					connect(1234)
		self.memory.read.assert_called_with(self.base, 2)

	def test_rejects_wrong_architecture_or_optional_header_format(self):
		for machine, magic in ((0x8664, 0x20B), (0x14C, 0x20B)):
			with self.subTest(machine=machine, magic=magic):
				self.segments[self.base + self.pe_offset] = self._pe_header(machine, magic)
				with self.assertRaisesRegex(UnsupportedGame, "32-bit x86"):
					connect(1234)
		self.memory.close.assert_called()

	def test_rejects_same_name_when_the_game_layout_differs(self):
		self.segments[self.getter] = b"\x8b\x41\x48\xc3"
		with self.assertRaisesRegex(UnsupportedGame, "unsupported game layout"):
			connect(1234)
		self.memory.close.assert_called_once()

	def test_rejects_pointer_outside_the_image_without_reading_it(self):
		self.segments[self.base + ROOT_VTABLE_RVA + 0x24] = struct.pack("<I", 0x70000000)
		with self.assertRaisesRegex(UnsupportedGame, "unsupported game layout"):
			connect(1234)
		self.memory.close.assert_called_once()

	def test_read_failure_closes_handle_and_remains_retryable(self):
		self.memory.read.side_effect = MemoryReadError("Temporary read failure")
		with self.assertRaises(MemoryReadError):
			connect(1234)
		self.memory.close.assert_called_once()


if __name__ == "__main__":
	unittest.main()
