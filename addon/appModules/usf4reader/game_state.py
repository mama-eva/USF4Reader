"""Read validated event records. No scanning, hooks or remote function calls."""

import struct
from dataclasses import dataclass

from .battle import BattleReader
from .dialogs import DialogReader
from .interface import InterfaceReader
from .memory_reader import MemoryReadError
from .scaleform import ScaleformReader
from .startup import LOGOS, title_ready

# Addresses are relative to the loaded game module.
CODE_START_RVA = 0x1000
CODE_END_RVA = 0x5282E3
CHILD_CONTROLLER_GETTER = b"\x8b\x41\x44\xc3"  # mov eax, [ecx+0x44]; ret
APP_CONTROLLER_RVA = 0x66BE54
CONTROLLER_VTABLE_RVA = 0x55E22C
ROOT_VTABLE_RVA = 0x552C24
MAIN_MENU_VTABLE_RVA = 0x554A00
CHARACTER_VTABLES = {
	0x557458: "Versus",
	0x55709C: "Training",
	0x553D3C: "Arcade",
	0x558DD0: "Bonus stage",
}

MAIN_MENU_KEYS = (
	"ID_MEN_1000",
	"ID_MEN_1001",
	"ID_MEN_1002",
	"ID_MEN_1004",
	"ID_MEN_1005",
	"ID_MEN_1006",
	"ID_MEN_1007",
	"ID_TU3_MEN_0000",
	"ID_MEN_1008",
	"ID_BENCHMARK",
	"ID_QUIT",
)


@dataclass(frozen=True)
class GameState:
	screen: str
	mode: str | tuple = ""
	players: tuple = (None, None)
	events: tuple = ()
	detail: str = ""
	value: str | tuple = ""
	panels: tuple = ()
	lines: tuple = ()


class StateReader:
	def __init__(self, memory, base, known_codes):
		self.memory = memory
		self.base = base
		self.known_codes = frozenset(known_codes)
		self.scaleform = ScaleformReader(memory, base)
		character_keys = (
			{record["index"]: record["key"] for record in known_codes.values()}
			if isinstance(known_codes, dict)
			else {}
		)
		self.interface = InterfaceReader(self.scaleform, character_keys)
		self.battle = BattleReader(memory, base)
		self.dialogs = DialogReader(self.scaleform)

	def _controller(self, address):
		data = self.memory.read(address, 0x1B0)
		if struct.unpack_from("<I", data)[0] != self.base + CONTROLLER_VTABLE_RVA:
			raise MemoryReadError("Controlador fora do perfil")
		index = struct.unpack_from("<i", data, 0x1AC)[0]
		if not 0 <= index < 16:
			return None
		pos = 0x28 + index * 0x18
		event = struct.unpack_from("<I", data, pos)[0]
		status = struct.unpack_from("<I", data, pos + 0x10)[0]
		if not event or status != 6:
			return None
		return event, index, pos

	def _code(self, block, offset):
		# Verified live: inline buffer/pointer +0, size +16, capacity +20.
		length, capacity = struct.unpack_from("<II", block, offset + 16)
		if length == 0:
			return None
		if length != 3 or not length <= capacity <= 4096:
			raise MemoryReadError("String de personagem inconsistente")
		if capacity < 16:
			value = block[offset : offset + 4]
		else:
			pointer = struct.unpack_from("<I", block, offset)[0]
			value = self.memory.read(pointer, 4)
		if value[3] != 0:
			raise MemoryReadError("Código de personagem sem terminador")
		try:
			code = value[:3].decode("ascii")
		except UnicodeError as error:
			raise MemoryReadError("Código de personagem inválido") from error
		if code not in self.known_codes:
			raise MemoryReadError("Código de personagem fora do catálogo")
		return code

	def read(self):
		memory, base = self.memory, self.base
		initial = memory.u32(base + APP_CONTROLLER_RVA)
		if not initial:
			return GameState("initializing")
		controller = initial
		chain = []
		events = []
		state = GameState("unknown")
		for depth in range(8):
			current = self._controller(controller)
			if current is None:
				return GameState("transition")
			event, index, pos = current
			header = memory.read(event, 0x80)
			vtable, source = struct.unpack_from("<I4xI", header)
			if source != controller:
				raise MemoryReadError("Evento trocado durante a leitura")
			raw_name = header[12:44].split(b"\0", 1)[0]
			try:
				name = raw_name.decode("ascii")
			except UnicodeError as error:
				raise MemoryReadError("Nome de evento inválido") from error
			if not name or not all(c.isalnum() or c == "_" for c in name):
				raise MemoryReadError("Nome de evento fora do perfil")
			if depth == 0 and name != "Game":
				return GameState("initializing")
			if depth == 0 and vtable != base + ROOT_VTABLE_RVA:
				raise MemoryReadError("Evento raiz fora do perfil")
			chain.append((controller, index, pos, event))
			events.append(name)
			if depth == 0:
				dialog = self.dialogs.read(event)
				if dialog:
					state = GameState(dialog[0], events=tuple(events), detail=dialog[1], value=dialog[2])
					break
			rva = vtable - base
			if name in LOGOS and rva == LOGOS[name][0]:
				state = GameState("text", events=tuple(events), detail=LOGOS[name][1])
				break
			if name == "Opening" and rva == 0x559028:
				state = GameState("text", events=tuple(events), detail="Opening movie. Press Enter to skip.")
				break
			if name == "Title" and rva in (0x556EEC, 0x556FA4):
				state = (
					GameState("text", events=tuple(events), detail="Ultra Street Fighter IV. Press Enter.")
					if title_ready(self.scaleform, event)
					else GameState("transition")
				)
				break
			if name == "MainMenu" and rva == MAIN_MENU_VTABLE_RVA:
				root = self.scaleform.root(event)[-1]
				windows = self.interface.menus(root, "Main menu")
				if len(windows) == 1:
					window, title, label, value = windows[0]
					state = GameState(
						"mainMenu" if window == "item_main_menu" else "menu",
						mode=title,
						events=tuple(events),
						detail=label,
						value=value,
					)
				else:
					state = GameState("transition")
				break
			if name == "CharaSelect" and rva in CHARACTER_VTABLES:
				block = memory.read(event, 0x428)
				# Read the data twice to discard torn snapshots during cursor movement.
				if block != memory.read(event, len(block)):
					return GameState("transition")
				flags = struct.unpack_from("<I", block, 0x4C)[0]
				players = []
				for side in range(2):
					enabled = flags & (1 << side)
					blind = flags & (8 << side)
					players.append(
						self._code(block, 0x50 + side * 0x1EC + 0x3C) if enabled and not blind else None
					)
				panels = self.interface.character_panels(event, flags)
				state = GameState(
					"characterSelect", CHARACTER_VTABLES[rva], tuple(players), tuple(events), panels=panels
				)
				break
			if name == "StageSelect" and rva == 0x557704:
				stage = self.interface.stage_select(event)
				state = (
					GameState("menu", mode="ID_MEN_2101", events=tuple(events), detail=stage)
					if stage
					else GameState("transition")
				)
				break
			state = GameState("unknown", events=tuple(events), detail=name)
			# Only follow EC-bearing objects whose actual getter has the verified body.
			if not base + 0x529000 <= vtable <= base + 0x6366E3 - 40:
				raise MemoryReadError("Vtable de evento fora da seção de dados somente leitura")
			getter = memory.u32(vtable + 0x24)
			if not base + CODE_START_RVA <= getter < base + CODE_END_RVA:
				break
			if memory.read(getter, len(CHILD_CONTROLLER_GETTER)) != CHILD_CONTROLLER_GETTER:
				windows = []
				lines = []
				trial = None
				trial_lines = ()
				result_panels = ()
				record = None
				roots = (
					self.interface.player_data_roots(event)
					if name == "PlayerData" and rva == 0x557C14
					else self.interface.roots(event, vtable)
				)
				for sprite, root in roots:
					title = {
						"SOUND": "ID_OPT_0001",
						"CONTROLLER": "ID_OPT_0000",
						"DISPLAY": "ID_OPT_0002",
						"VOICE": "ID_OPT_2005",
						"PlayerData": "ID_MEN_1006",
					}.get(name, "ID_MEN_1007" if "Option" in events else name)
					if root:
						windows.extend(self.interface.menus(root, title))
						if name == "TrialMenu":
							trial = self.interface.trial(root) or trial
					if name in ("VersusFromChr", "VersusFromBtl", "Versus", "Prologue", "Epilogue"):
						lines.extend(self.interface.texts(sprite))
				if name == "PlayerData" and rva == 0x557C14 and not windows:
					record = self.interface.player_data_record(event)
					if record is None:
						lines.extend(self.interface.player_data_page(event))
				if name == "Battle":
					manager = self.battle.pause_manager()
					if manager:
						address, pause_vtable = manager
						extent = 0xC48 if pause_vtable == base + 0x556788 else 0x954
						for sprite, root in self.interface.roots(
							address, pause_vtable, extent=extent, start=0
						):
							if root:
								windows.extend(self.interface.menus(root, "Pause"))
						if self.battle.pause_manager() != manager:
							return GameState("transition")
					if rva == 0x5587F0:
						try:
							trial_lines, results = self.interface.trial_battle(event)
							if not windows:
								windows.extend(results)
						except MemoryReadError:
							pass
					if rva == 0x557414 and not windows:
						result_panels = self.interface.versus_result(event)
				if record is not None:
					state = (
						GameState(
							"records", mode=record[0], events=tuple(events), detail=record[1], value=record[2]
						)
						if record
						else GameState("transition")
					)
				elif result_panels:
					state = GameState("versusResult", events=tuple(events), panels=result_panels)
				elif len(windows) == 1:
					window, title, label, value = windows[0]
					state = GameState("menu", mode=title, events=tuple(events), detail=label, value=value)
				elif name == "Battle":
					state = GameState(
						"trialBattle" if trial_lines else "battle",
						events=tuple(events),
						detail=self.battle.announcement(),
						lines=trial_lines,
					)
				elif trial:
					state = GameState(
						"menu",
						mode="Trial",
						events=tuple(events),
						detail=f"Trial {trial[0] + 1}",
						lines=trial[1],
					)
				elif lines:
					state = GameState("text", events=tuple(events), lines=tuple(dict.fromkeys(lines)))
				break
			controller = struct.unpack_from("<I", header, 0x44)[0]
			if not controller:
				break
		# Revalidate all links after copying the leaf, never retain heap pointers between polls.
		if memory.u32(base + APP_CONTROLLER_RVA) != initial:
			return GameState("transition")
		for controller, index, pos, event in chain:
			if memory.u32(controller + 0x1AC) != index:
				return GameState("transition")
			if memory.u32(controller + pos) != event or memory.u32(controller + pos + 0x10) != 6:
				return GameState("transition")
		return state
