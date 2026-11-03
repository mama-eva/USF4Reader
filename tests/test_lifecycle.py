"""Exercise the NVDA adapter with explicit doubles, without changing NVDA configuration."""

import importlib
import queue
import sys
import threading
import time
import types
import unittest
from pathlib import Path
from unittest.mock import patch

DEV = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DEV / "addon" / "appModules"))
scheduled = queue.Queue()
fake_log = types.SimpleNamespace(warning=lambda *a, **kw: None, exception=lambda *a, **kw: None)
sys.modules.setdefault("core", types.SimpleNamespace(callLater=lambda delay, fn, *a: scheduled.put((fn, a))))
sys.modules.setdefault("logHandler", types.SimpleNamespace(log=fake_log))
from usf4reader import controller
from usf4reader.game_process import UnsupportedGame
from usf4reader.game_state import GameState


class LifecycleTests(unittest.TestCase):
	def test_queued_old_selection_is_discarded_after_cursor_moves(self):
		spoken = []
		reader = controller.Reader(1, spoken.append)
		reader._active = True
		reader._generation = 1
		old = GameState("mainMenu", detail="ID_MEN_1000")
		new = GameState("mainMenu", detail="ID_MEN_1001")
		reader.latest = new
		reader._deliver(1, old, "Arcade")
		self.assertEqual(spoken, [])
		reader._deliver(1, new, "Versus")
		self.assertEqual(spoken, ["Versus"])
		reader.close()

	def test_play_time_can_tick_before_delivery_but_cursor_and_focus_still_win(self):
		spoken = []
		reader = controller.Reader(1, spoken.append)
		reader.catalog = controller.Catalog(menus={"ID_PDT_1002": "TOTAL PLAY TIME"})
		reader._active = True
		reader._generation = 1
		old = GameState("records", mode=("PLAYER RECORDS",), detail="ID_PDT_1002", value=("01:00:00",))
		new = GameState("records", mode=old.mode, detail=old.detail, value=("01:00:01",))
		reader.latest = new
		reader._deliver(1, old, reader.catalog.describe(old))
		self.assertEqual(spoken, ["PLAYER RECORDS. TOTAL PLAY TIME: 01:00:01"])
		reader.latest = GameState("records", mode=old.mode, detail="Wins", value=("3",))
		reader._deliver(1, old, reader.catalog.describe(old))
		reader.latest = new
		reader._generation = 2
		reader._deliver(1, old, reader.catalog.describe(old))
		reader._active = False
		reader._deliver(2, old, reader.catalog.describe(old))
		self.assertEqual(len(spoken), 1)
		reader.close()

	def drain(self):
		while True:
			try:
				fn, args = scheduled.get_nowait()
			except queue.Empty:
				return
			fn(*args)

	def wait_for(self, predicate):
		end = time.monotonic() + 2
		while not predicate() and time.monotonic() < end:
			time.sleep(0.01)
		self.assertTrue(predicate())

	def test_foreground_worker_closes_handle_and_drops_queued_speech_on_blur(self):
		memory = types.SimpleNamespace(close=lambda: closed.set(), image_path=lambda: "C:/game/SSFIV.exe")
		closed = threading.Event()
		state = GameState("characterSelect", "Versus", ("RYU", "KEN"))
		spoken = []
		fake_reader = types.SimpleNamespace(read=lambda: state)
		with (
			patch.object(controller, "connect", return_value=(memory, 0x400000)),
			patch.object(controller, "StateReader", return_value=fake_reader),
			patch.object(controller.Catalog, "for_game", return_value=controller.Catalog()),
		):
			reader = controller.Reader(1, spoken.append)
			reader.focus(True)
			self.wait_for(lambda: not scheduled.empty())
			reader.focus(False)
			self.drain()
			self.assertEqual(spoken, [])
			self.wait_for(closed.is_set)
			self.assertIsNone(reader.current())
			reader.close()
			reader._thread.join(2)
			self.assertFalse(reader._thread.is_alive())

	def test_restart_on_records_loads_full_labels_before_announcing(self):
		memory = types.SimpleNamespace(close=lambda: None, image_path=lambda: "C:/game/SSFIV.exe")
		state = GameState("records", mode=("PLAYER RECORDS",), detail="ID_PDT_2006", value=("1 / 24",))
		spoken = []
		startup = controller.Catalog(menus={})
		complete = controller.Catalog(menus={"ID_PDT_2006": "TRIALS CLEARED"})
		with (
			patch.object(controller, "connect", return_value=(memory, 0x400000)),
			patch.object(controller, "StateReader", return_value=types.SimpleNamespace(read=lambda: state)),
			patch.object(controller.Catalog, "for_game", side_effect=[startup, complete]) as load_catalog,
		):
			reader = controller.Reader(1, spoken.append)
			try:
				reader.focus(True)
				self.wait_for(lambda: not scheduled.empty())
				self.drain()
				self.assertEqual(spoken, ["PLAYER RECORDS. TRIALS CLEARED: 1 of 24"])
				self.assertEqual(load_catalog.call_args_list[0].kwargs, {"startup": True})
				self.assertEqual(load_catalog.call_args_list[1].kwargs, {})
			finally:
				reader.close()
				reader._thread.join(2)

	def test_unsupported_executable_is_announced_once_without_retry_loop(self):
		spoken = []
		with patch.object(
			controller, "connect", side_effect=UnsupportedGame("Perfil incompatível.")
		) as connect:
			reader = controller.Reader(1, spoken.append)
			reader.focus(True)
			self.wait_for(lambda: not scheduled.empty())
			self.drain()
			self.assertEqual(spoken, ["USF4 Reader: Perfil incompatível."])
			self.assertEqual(connect.call_count, 1)
			reader.close()
			reader._thread.join(2)
			self.assertFalse(reader._thread.is_alive())

	def test_restart_on_result_loads_labels_for_both_players(self):
		memory = types.SimpleNamespace(close=lambda: None, image_path=lambda: "C:/game/SSFIV.exe")
		state = GameState(
			"versusResult", panels=((0, "result", "ID_PUS_0112", ""), (1, "result", "ID_PUS_0113", ""))
		)
		spoken = []
		startup = controller.Catalog(menus={})
		complete = controller.Catalog(menus={"ID_PUS_0112": "REMATCH", "ID_PUS_0113": "SELECT CHARACTER"})
		with (
			patch.object(controller, "connect", return_value=(memory, 0x400000)),
			patch.object(controller, "StateReader", return_value=types.SimpleNamespace(read=lambda: state)),
			patch.object(controller.Catalog, "for_game", side_effect=[startup, complete]),
		):
			reader = controller.Reader(1, spoken.append)
			try:
				reader.focus(True)
				self.wait_for(lambda: not scheduled.empty())
				self.drain()
				self.assertEqual(spoken, ["Versus result. Player 1: REMATCH. Player 2: SELECT CHARACTER"])
			finally:
				reader.close()
				reader._thread.join(2)

	def test_app_module_automatic_speech_without_keyboard_gestures(self):
		spoken, cancelled = [], []

		class Base:
			processID = 1

			def __init__(self, *args, **kwargs):
				pass

			def terminate(self):
				pass

		modules = {
			"api": types.SimpleNamespace(getForegroundObject=lambda: types.SimpleNamespace(processID=1)),
			"appModuleHandler": types.SimpleNamespace(AppModule=Base),
			"speech": types.SimpleNamespace(cancelSpeech=lambda: cancelled.append(True)),
			"ui": types.SimpleNamespace(message=spoken.append),
		}
		with patch.dict(sys.modules, modules):
			appModules = types.ModuleType("appModules")
			appModules.__path__ = [str(DEV / "addon" / "appModules")]
			with patch.dict(sys.modules, {"appModules": appModules}):
				module = importlib.import_module("appModules.ssfiv")
				app = module.AppModule()
				app._announce("Arcade")
				self.assertEqual(spoken, ["Arcade"])
				self.assertEqual(cancelled, [True])
				self.assertFalse(any(name.startswith("script_") for name in vars(module.AppModule)))
				app.terminate()
				self.assertTrue(app.reader._stop.is_set())


if __name__ == "__main__":
	unittest.main()
