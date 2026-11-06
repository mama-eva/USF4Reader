"""Find SSFIV.exe and check whether its loaded game layout can be read."""

import struct
from pathlib import Path

from .game_state import (
	APP_CONTROLLER_RVA,
	CHILD_CONTROLLER_GETTER,
	CODE_END_RVA,
	CODE_START_RVA,
	CONTROLLER_VTABLE_RVA,
	ROOT_VTABLE_RVA,
)
from .memory_reader import ProcessMemory

INCOMPATIBLE_LAYOUT = "This version of SSFIV.exe uses an unsupported game layout."


class UnsupportedGame(ValueError):
	pass


def connect(pid):
	memory = ProcessMemory(pid)
	try:
		if Path(memory.image_path()).name.casefold() != "ssfiv.exe":
			raise UnsupportedGame("USF4 Reader requires the SSFIV.exe game process.")
		base, size = memory.module()
		_check_image(memory, base, size)
		return memory, base
	except Exception:
		memory.close()
		raise


def _check_image(memory, base, size):
	if size < APP_CONTROLLER_RVA + 4 or memory.read(base, 2) != b"MZ":
		raise UnsupportedGame(INCOMPATIBLE_LAYOUT)
	pe_offset = memory.u32(base + 0x3C)
	if not 0x40 <= pe_offset <= size - 26:
		raise UnsupportedGame(INCOMPATIBLE_LAYOUT)
	header = memory.read(base + pe_offset, 26)
	if (
		header[:4] != b"PE\0\0"
		or struct.unpack_from("<H", header, 4)[0] != 0x14C
		or struct.unpack_from("<H", header, 20)[0] < 2
		or struct.unpack_from("<H", header, 24)[0] != 0x10B
	):
		raise UnsupportedGame("USF4 Reader requires a 32-bit x86 version of SSFIV.exe.")

	# Check the loaded layout even during startup, when the controller can still be null.
	# The root event's virtual getter must return the child controller field we read.
	controller_method = memory.u32(base + CONTROLLER_VTABLE_RVA)
	root_getter = memory.u32(base + ROOT_VTABLE_RVA + 0x24)
	if (
		not base + CODE_START_RVA <= controller_method < base + CODE_END_RVA
		or not base + CODE_START_RVA <= root_getter <= base + CODE_END_RVA - len(CHILD_CONTROLLER_GETTER)
		or memory.read(root_getter, len(CHILD_CONTROLLER_GETTER)) != CHILD_CONTROLLER_GETTER
	):
		raise UnsupportedGame(INCOMPATIBLE_LAYOUT)
