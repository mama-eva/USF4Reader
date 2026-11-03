"""One internal NVDA thread: bounded reads while the game has focus."""

import threading
import time

import core
from logHandler import log

from .announcements import Announcements
from .game_process import UnsupportedGame, connect
from .game_state import GameState, StateReader
from .localization import Catalog
from .memory_reader import MemoryReadError

READ_FAILURE_GRACE = 1.5


class Reader:
	def __init__(self, pid, announce):
		self.pid = pid
		self.catalog = Catalog()
		self.announce = announce
		self.last_message = ""
		self.latest = None
		self._lock = threading.Lock()
		self._stop = threading.Event()
		self._wake = threading.Event()
		self._active = False
		self._generation = 0
		self._thread = None

	def focus(self, active):
		with self._lock:
			self._active = active
			self._generation += 1
			self.latest = None
		if active and (self._thread is None or not self._thread.is_alive()):
			self._thread = threading.Thread(target=self._run, name="USF4Reader", daemon=True)
			self._thread.start()
		self._wake.set()

	def current(self):
		with self._lock:
			return self.latest

	def close(self):
		with self._lock:
			self._active = False
			self._generation += 1
			self.latest = None
		self._stop.set()
		self._wake.set()
		# No join on NVDA's main thread. The worker owns and closes its only handle.

	def _deliver(self, generation, state, message):
		with self._lock:
			latest = self.latest
			time_tick = (
				state.screen == "records"
				and state.detail == "ID_PDT_1002"
				and latest
				and latest.screen == "records"
				and latest.mode == state.mode
				and latest.detail == state.detail
			)
			valid = (
				self._active
				and self._generation == generation
				and not self._stop.is_set()
				and (latest == state or time_tick)
			)
			if valid and time_tick and latest != state:
				message = message.replace(
					self.catalog.record_item(state), self.catalog.record_item(latest), 1
				)
		if valid:
			self.last_message = message
			self.announce(message)

	def _run(self):
		memory = None
		verified = False
		catalog_loaded = False
		startup_catalog_loaded = False
		last_generation = -1
		fatal_generation = -1
		last_log = None
		last_log_time = 0.0
		error_since = None
		gate = Announcements(self.catalog, debounce=0.04)
		try:
			while not self._stop.is_set():
				self._wake.clear()
				with self._lock:
					active, generation = self._active, self._generation
				if not active:
					error_since = None
					if memory:
						memory.close()
						memory = None
					self._wake.wait(0.5)
					continue
				if generation != last_generation:
					gate.reset()
					error_since = None
					last_generation = generation
				if fatal_generation == generation:
					self._wake.wait(0.5)
					continue
				delay = 0.08
				try:
					if memory is None:
						memory, base = connect(self.pid, verify=not verified)
						verified = True
						if not startup_catalog_loaded:
							self.catalog = Catalog.for_game(memory.image_path(), startup=True)
							gate = Announcements(self.catalog, debounce=0.04)
							startup_catalog_loaded = True
						reader = StateReader(memory, base, self.catalog.characters)
					state = reader.read()
					if not catalog_loaded and (
						state.screen
						in (
							"mainMenu",
							"menu",
							"records",
							"versusResult",
							"characterSelect",
							"battle",
							"trialBattle",
						)
						or state.screen == "text"
						and state.events
						and state.events[-1] in ("Opening", "Title")
					):
						# Short logos must not wait for all command-list labels to load.
						self.catalog = Catalog.for_game(memory.image_path())
						gate = Announcements(self.catalog, debounce=0.04)
						catalog_loaded = True
						state = reader.read()
					error_since = None
				except UnsupportedGame as error:
					state = GameState("diagnostic", detail=str(error))
					fatal_generation = generation
					# Publish terminal errors immediately; there will be no next polling sample.
					gate.reset()
					gate.update(state, time.monotonic() - 1)
				except MemoryReadError as error:
					now = time.monotonic()
					label = f"{type(error).__name__}: {error}; operation={error.operation}; address={error.address}; size={error.size}"
					signature = f"{type(error).__name__}: {error}; operation={error.operation}"
					if signature != last_log or now - last_log_time >= 30:
						log.warning("USF4 Reader: leitura indisponível: %s", label, exc_info=True)
						last_log, last_log_time = signature, now
					ended = memory is not None and not memory.is_running()
					if ended or (memory is None and error.errno in (31, 87)):
						if memory:
							memory.close()
							memory = None
						error_since = None
						state = GameState("transition")
						delay = 0.5
					elif memory is None and error.operation == "open" and error.errno == 5:
						state = GameState(
							"diagnostic",
							detail="The game could not be opened. Check the permission level of the game and NVDA.",
						)
						delay = 1.0
					else:
						if error_since is None:
							error_since = now
							gate.reset()
						if memory:
							# Re-resolve paths after a movie is replaced. The read handle remains valid.
							reader.interface._paths.clear()
						state = (
							GameState("diagnostic", detail="The current game screen could not be read.")
							if now - error_since >= READ_FAILURE_GRACE
							else GameState("transition")
						)
						if now - error_since >= READ_FAILURE_GRACE:
							delay = 0.25
				except Exception:
					log.exception("USF4 Reader: erro inesperado na leitura")
					if memory:
						memory.close()
						memory = None
					state = GameState("diagnostic", detail="The current game screen could not be read.")
					delay = 1.0
				with self._lock:
					if self._active and self._generation == generation:
						self.latest = state
				message = gate.update(state, time.monotonic())
				if message:
					core.callLater(0, self._deliver, generation, state, message)
				self._wake.wait(delay)
		except Exception:
			log.exception("USF4 Reader: monitor encerrado por erro inesperado")
		finally:
			if memory:
				memory.close()
