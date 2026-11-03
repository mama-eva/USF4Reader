import json
import re
from pathlib import Path

from .game_text import load_game_text


class Catalog:
	def __init__(self, language="ENG", *, menus=None):
		data = Path(__file__).parent / "data"
		self.language = language
		self.characters = json.loads((data / "characters.json").read_text(encoding="utf-8"))["characters"]
		if menus is not None:
			self.menus = menus
			return
		path = data / f"ui_{language}.json"
		if not path.is_file():
			path = data / "ui_ENG.json"
			self.language = "ENG"
		# Local regression captures can still use private catalogs. They are not distributed.
		self.menus = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}

	@classmethod
	def for_game(cls, game_path, *, startup=False):
		language = game_language(game_path)
		return cls(
			language, menus=load_game_text(game_path, language, groups=("msg_box",) if startup else None)
		)

	def text(self, value):
		if not value:
			return ""
		if isinstance(value, tuple):
			return " ".join(filter(None, (self.text(part) for part in value)))
		if "@/@" in value:
			parts = value.split("@/@")
			if not 1 < len(parts) <= 4:
				return ""
			labels = [self.text(part) for part in parts]
			return " or ".join(labels) if all(labels) else ""
		strength = {"ID_CMD_CMN_0023": "Light", "ID_CMD_CMN_0024": "Medium", "ID_CMD_CMN_0025": "Heavy"}
		if value in strength:
			return strength[value]
		text = self.menus.get(value, value)
		if text.startswith("ID_"):
			return ""
		# The game uses these tags for formatting and controller icons.
		text = re.sub(r"<[^>]*>", " ", text)
		if self.language == "ENG":
			# Spell out the glyph so a Portuguese NVDA symbol dictionary cannot translate it.
			text = text.replace("\u221e", "Infinite")
			# A missing rendered field must never invent the recipient of an unlock.
			if text in (
				"You unlocked a new color for [CHARANAME]!",
				"You unlocked a new taunt for [CHARANAME]!",
			):
				text = text.replace(" for [CHARANAME]", "")
		return " ".join(text.replace("\\n", " ").split())

	def menu_item(self, state):
		item = ": ".join(filter(None, (self.text(state.detail), self.text(state.value))))
		return ". ".join(filter(None, (item, *(self.text(line) for line in state.lines))))

	def character(self, code):
		if code == "RND":
			return "Random"
		if code in self.characters:
			character = self.characters[code]
			return self.text(character.get("key")) or character["name"]
		return "Unknown character"

	def record_item(self, state):
		value = self.text(state.value)
		if self.language == "ENG":
			fraction = re.fullmatch(r"(\d+)\s*/\s*(\d+)", value)
			if fraction:
				value = f"{fraction[1]} of {fraction[2]}"
		return ": ".join(filter(None, (self.text(state.detail), value)))

	def player(self, side, text):
		return f"Player {side + 1}: {text}"

	def panel(self, panel):
		side, kind, name, value = panel
		text = ": ".join(filter(None, (self.text(name), self.text(value))))
		return self.player(side, text)

	def describe(self, state):
		if state is None:
			return "USF4 Reader: waiting for the game."
		if state.screen == "characterSelect":
			if state.panels:
				return ". ".join(self.panel(panel) for panel in state.panels)
			if sum(code is not None for code in state.players) == 1:
				return "Character select. " + next(self.character(code) for code in state.players if code)
			names = [self.player(i, self.character(code)) for i, code in enumerate(state.players) if code]
			return ". ".join(["Character select"] + names)
		if state.screen == "mainMenu":
			item = self.menu_item(state)
			return "Main menu. " + item if item else "Main menu."
		if state.screen == "menu":
			if state.mode == "Trial":
				return self.menu_item(state)
			return ". ".join(filter(None, (self.text(state.mode), self.menu_item(state))))
		if state.screen == "records":
			context = state.mode if isinstance(state.mode, tuple) else (state.mode,)
			return ". ".join(filter(None, (*(self.text(part) for part in context), self.record_item(state))))
		if state.screen == "versusResult":
			return ". ".join(["Versus result"] + [self.panel(panel) for panel in state.panels])
		if state.screen == "dialog":
			question, choice = self.text(state.detail), self.text(state.value)
			if not choice:
				return question
			return question + (" " if question.endswith(("?", "!", ".")) else ". ") + choice
		if state.screen == "trialBattle":
			if state.detail == "Clear":
				return "Trial complete."
			if state.detail and state.detail != "Ready? Go!":
				return self.text(state.detail)
			instructions = ". ".join(filter(None, (self.text(line) for line in state.lines)))
			return "Ready? Go! " + instructions if state.detail == "Ready? Go!" else instructions
		if state.screen in ("text", "battle"):
			return (
				". ".join(filter(None, (self.text(line) for line in state.lines)))
				if state.lines
				else self.text(state.detail)
			)
		if state.screen == "diagnostic":
			return "USF4 Reader: " + state.detail
		if state.screen in ("initializing", "transition"):
			return "Loading."
		labels = {"Opening": "Opening", "Title": "Title screen"}
		return labels.get(state.detail, "")


def game_language(game_path):
	"""Read the game's own locale setting; NVDA/UI language never overrides it."""
	aliases = {
		"english": "ENG",
		"brazilian": "BRA",
		"portuguese": "BRA",
		"french": "FRA",
		"german": "GER",
		"italian": "ITA",
		"spanish": "SPA",
		"russian": "RUS",
		"japanese": "JPN",
		"koreana": "KOR",
		"korean": "KOR",
		"schinese": "CHI",
		"tchinese": "CHI",
		"polish": "POL",
		"dutch": "DUT",
		"czech": "CZE",
	}
	try:
		config = (Path(game_path).parent / "steam_api.ini").read_text(encoding="utf-8-sig")
		match = re.search(r"^\s*Language\s*=\s*([a-z]+)", config, re.I | re.M)
		return aliases.get(match[1].lower(), "ENG") if match else "ENG"
	except (OSError, UnicodeError):
		return "ENG"
