"""Automatic accessibility for SSFIV.exe. No keyboard gestures are bound."""

import api
import appModuleHandler
import speech
import ui

from .usf4reader.controller import Reader


class AppModule(appModuleHandler.AppModule):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.reader = Reader(self.processID, self._announce)

	def _announce(self, message):
		foreground = api.getForegroundObject()
		if foreground and foreground.processID == self.processID:
			speech.cancelSpeech()
			ui.message(message)

	def isBadUIAWindow(self, hwnd):
		# This DirectX game is read by this app module. UiaHasServerSideProvider can
		# block NVDA's main thread on its windows before appModule_gainFocus runs.
		return True

	def event_appModule_gainFocus(self):
		self.reader.focus(True)

	def event_appModule_loseFocus(self):
		self.reader.focus(False)

	def terminate(self):
		try:
			super().terminate()
		finally:
			self.reader.close()
