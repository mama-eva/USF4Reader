"""Read the actual HUD announcement currently on screen in the verified build."""

import struct

from .memory_reader import MemoryReadError

ANNOUNCEMENTS = {
	0x28: "Final round",
	0x30: "Extra round",
	0x38: "Fight!",
	0x40: "K.O.",
	0x48: "Double K.O.",
	0x50: "Time over",
	0x58: "Draw",
	0x60: "Perfect",
	0x68: "You win",
	0x70: "You lose",
	0x78: "Player 1 wins",
	0x80: "Player 2 wins",
	0x88: "Success",
	0x90: "Clear",
	0x98: "Ready? Go!",
}


class BattleReader:
	def __init__(self, memory, base):
		self.memory, self.base = memory, base

	def pause_manager(self):
		memory, base = self.memory, self.base
		try:
			unit = memory.u32(base + 0x68E4B0 + 0x88)
			if not unit or memory.u32(unit) != base + 0x54C5C4:
				return None
			manager = memory.u32(unit + 8)
			if not manager:
				return None
			vtable = memory.u32(manager)
			if vtable - base not in (0x556684, 0x5566C4, 0x556704, 0x556744, 0x556788, 0x5567C8):
				return None
			return manager, vtable
		except MemoryReadError:
			return None

	def announcement(self):
		memory, base = self.memory, self.base
		# GetSingleton at VA 0x5d6150 returns this static object, not a heap pointer.
		system = base + 0x68E4B0
		if memory.u32(system) != base + 0x54CDD4:
			return ""
		hud = memory.u32(system + 0x68)
		if not hud or memory.u32(hud) != base + 0x54886C:
			return ""
		unit = memory.u32(hud + 0x20)
		if not unit or memory.u32(unit) != base + 0x548DD0:
			return ""
		view = memory.u32(unit + 0x38)
		if not view or memory.u32(view) != base + 0x548E20:
			return ""
		block = memory.read(view, 0xD4)
		active = struct.unpack_from("<I", block, 0xD0)[0]
		text = ""
		if active:
			if active == struct.unpack_from("<I", block, 0x20)[0]:
				round_index = struct.unpack("<H", memory.read(active + 0x2C, 2))[0]
				if 0 <= round_index < 99:
					text = f"Round {round_index + 1}"
				if struct.unpack("<H", memory.read(active + 0x2C, 2))[0] != round_index:
					raise MemoryReadError("HUD round changed")
			else:
				for offset, label in ANNOUNCEMENTS.items():
					if active == struct.unpack_from("<I", block, offset)[0]:
						text = label
						break
		if memory.u32(system + 0x68) != hud or memory.u32(view + 0xD0) != active:
			raise MemoryReadError("HUD announcement changed")
		return text
