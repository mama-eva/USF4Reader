"""Run the installed NVDA window detector with a trapped provider call and our real policy."""

import ast
import marshal
import os
import sys
import types
import unittest
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch

DEV = Path(__file__).resolve().parents[1]
NVDA_LIBRARY = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "NVDA/library.zip"


def find_code(code, name):
	if code.co_name == name:
		return code
	for value in code.co_consts:
		if isinstance(value, types.CodeType):
			found = find_code(value, name)
			if found:
				return found
	return None


@unittest.skipUnless(NVDA_LIBRARY.is_file(), "Requires the installed NVDA window detector")
class UIABoundaryTests(unittest.TestCase):
	def setUp(self):
		with zipfile.ZipFile(NVDA_LIBRARY) as archive:
			code = marshal.loads(archive.read("UIAHandler/__init__.pyc")[16:])
		helper = find_code(code, "_isUIAWindowHelper")
		self.assertIsNotNone(helper)
		self.provider = Mock(side_effect=TimeoutError("Blocking provider probe was reached"))
		self.process_id = 4144
		self.game = types.SimpleNamespace(isGoodUIAWindow=lambda hwnd: False)
		self.other = types.SimpleNamespace(
			isGoodUIAWindow=lambda hwnd: False, isBadUIAWindow=lambda hwnd: False
		)
		parent = types.ModuleType("NVDAObjects")
		window = types.ModuleType("NVDAObjects.window")
		window.Window = types.SimpleNamespace(normalizeWindowClassName=lambda name: name)
		parent.window = window
		modules = patch.dict(sys.modules, {"NVDAObjects": parent, "NVDAObjects.window": window})
		modules.start()
		self.addCleanup(modules.stop)
		self.detector = types.FunctionType(
			helper,
			{
				"winUser": types.SimpleNamespace(
					getWindowThreadProcessID=lambda hwnd: (self.process_id, 1),
					getClassName=lambda hwnd: "GameWindow",
				),
				"globalVars": types.SimpleNamespace(appPid=9999),
				"goodUIAWindowClassNames": set(),
				"badUIAWindowClassNames": set(),
				"appModuleHandler": types.SimpleNamespace(
					getAppModuleFromProcessID=lambda pid: self.game if pid == 4144 else self.other
				),
				"winBindings": types.SimpleNamespace(
					uiAutomationCore=types.SimpleNamespace(UiaHasServerSideProvider=self.provider)
				),
			},
		)

	def test_previous_policy_reaches_the_call_seen_in_the_real_freeze(self):
		self.game.isBadUIAWindow = lambda hwnd: False
		with self.assertRaises(TimeoutError):
			self.detector(object(), 0x1234, False)
		self.provider.assert_called_once_with(0x1234)

	def test_game_policy_returns_before_the_blocking_native_call(self):
		tree = ast.parse((DEV / "addon/appModules/ssfiv.py").read_text(encoding="utf-8"))
		app = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "AppModule")
		policy = next(
			node for node in app.body if isinstance(node, ast.FunctionDef) and node.name == "isBadUIAWindow"
		)
		functions = {}
		exec(compile(ast.Module(body=[policy], type_ignores=[]), "ssfiv.py", "exec"), functions)
		self.game.isBadUIAWindow = types.MethodType(functions["isBadUIAWindow"], self.game)
		self.assertIs(self.detector(object(), 0x1234, False), False)
		self.provider.assert_not_called()

	def test_windows_of_other_processes_keep_the_normal_provider_detection(self):
		self.process_id = 5555
		with self.assertRaises(TimeoutError):
			self.detector(object(), 0x1234, False)
		self.provider.assert_called_once_with(0x1234)


if __name__ == "__main__":
	unittest.main()
