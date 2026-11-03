"""Record navigation and a running timer must produce usable automatic speech."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "addon" / "appModules"))
from usf4reader.announcements import Announcements
from usf4reader.game_state import GameState
from usf4reader.localization import Catalog


class RecordSpeechTests(unittest.TestCase):
	def setUp(self):
		self.cat = Catalog(menus={"ID_PDT_1002": "TOTAL PLAY TIME", "ID_PDT_2006": "TRIALS CLEARED"})

	def test_timer_ticks_do_not_starve_initial_speech_or_repeat_it(self):
		gate = Announcements(self.cat, debounce=0.1)
		a = GameState("records", mode=("PLAYER RECORDS",), detail="ID_PDT_1002", value=("01:00:00",))
		b = GameState("records", mode=a.mode, detail=a.detail, value=("01:00:01",))
		self.assertIsNone(gate.update(a, 0))
		self.assertIsNone(gate.update(b, 0.05))
		self.assertEqual(gate.update(b, 0.11), "PLAYER RECORDS. TOTAL PLAY TIME: 01:00:01")
		c = GameState("records", mode=a.mode, detail=a.detail, value=("01:00:02",))
		self.assertIsNone(gate.update(c, 1.1))
		self.assertIsNone(gate.update(c, 2))

	def test_row_changes_speak_values_once_and_category_changes_keep_context(self):
		gate = Announcements(self.cat, debounce=0.04)
		a = GameState(
			"records", mode=("CHARACTER RECORDS", "Ken", "TOTAL PROGRESS"), detail="Wins", value=("2",)
		)
		b = GameState("records", mode=a.mode, detail="ID_PDT_2006", value=("1 / 24",))
		gate.update(a, 0)
		self.assertEqual(gate.update(a, 0.08), "CHARACTER RECORDS. Ken. TOTAL PROGRESS. Wins: 2")
		gate.update(b, 0.16)
		self.assertEqual(gate.update(b, 0.24), "TRIALS CLEARED: 1 of 24")
		self.assertIsNone(gate.update(b, 2))
		c = GameState(
			"records", mode=("CHARACTER RECORDS", "Ken", "RANKED MATCH PROGRESS"), detail="Wins", value=("0",)
		)
		gate.update(c, 3)
		self.assertEqual(gate.update(c, 3.08), "CHARACTER RECORDS. Ken. RANKED MATCH PROGRESS. Wins: 0")


if __name__ == "__main__":
	unittest.main()
