"""Load interface labels from the user's game, without redistributing game resources."""

import os
from pathlib import Path

from .formats import FormatError, parse_m4s

LANGUAGES = frozenset(
	("ENG", "BRA", "FRA", "GER", "ITA", "SPA", "RUS", "JPN", "KOR", "CHI", "POL", "DUT", "CZE")
)


def load_game_text(game_path, language, *, groups=None):
	if language not in LANGUAGES:
		language = "ENG"
	root = Path(game_path).parent
	# Preserve the base-then-DLC ordering of the existing catalogs.
	ui_roots = [root / "resource/ui", *sorted((root / "dlc").glob("*/ui")), *sorted(root.glob("patch*/ui"))]
	paths = []
	for ui_root in ui_roots:
		if groups is not None:
			for group in groups:
				paths.extend((ui_root / group / "localize" / language).glob("*.m4s"))
			continue
		for current, directories, files in os.walk(ui_root):
			folder = Path(current)
			if folder.name == "localize":
				directories[:] = [name for name in directories if name == language]
			elif folder.parent.name == "localize" and folder.name == language:
				directories[:] = []
				paths.extend(folder / name for name in files if name.endswith(".m4s"))
	paths.sort(
		key=lambda p: (
			not p.relative_to(root).as_posix().startswith("resource/"),
			p.relative_to(root).as_posix(),
		)
	)
	if not paths or len(paths) > 1024:
		raise FormatError("Game interface text files are missing or exceed the supported limit.")
	labels = {}
	total = 0
	for path in paths:
		size = path.stat().st_size
		total += size
		if size > 2 * 1024 * 1024 or total > 32 * 1024 * 1024:
			raise FormatError("Game interface text exceeds the supported limit.")
		data = path.read_bytes()
		if len(data) != size:
			raise FormatError("Game interface text changed while reading.")
		actual_language, entries = parse_m4s(data)
		if actual_language != language:
			raise FormatError("Game interface text language does not match its folder.")
		labels.update(entries)
	return labels
