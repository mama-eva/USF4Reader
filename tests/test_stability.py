"""Recovery and read boundaries without requiring a running game or changing expectations."""

import struct
import sys
import time
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

DEV = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DEV / "addon/appModules"))
import test_lifecycle as lifecycle
from usf4reader import controller
from usf4reader.game_state import GameState
from usf4reader.memory_reader import MemoryReadError
from usf4reader.scaleform import ScaleformReader


class BoundedMemory:
	def __init__(self, pointer, data):
		self.pointer = pointer
		self.data = data

	def u32(self, address):
		return struct.unpack("<I", self.read(address, 4))[0]

	def read(self, address, size):
		if address == 0x10000 and size == 4:
			return struct.pack("<I", self.pointer)
		offset = address - self.pointer
		if 0 <= offset and offset + size <= len(self.data):
			return self.data[offset : offset + size]
		raise MemoryReadError(299, "Unmapped next page", operation="read", address=address, size=size)


class StabilityTests(unittest.TestCase):
	def setUp(self):
		lifecycle.LifecycleTests().drain()

	def wait_for(self, predicate, timeout=3):
		deadline = time.monotonic() + timeout
		while time.monotonic() < deadline:
			lifecycle.LifecycleTests().drain()
			if predicate():
				return
			time.sleep(0.01)
		self.fail("Worker did not reach the expected state")

	def test_valid_terminated_string_at_end_of_readable_page(self):
		memory = BoundedMemory(0x1FFF8, b"OPTIONS\0")
		self.assertEqual(ScaleformReader(memory, 0x400000).string(0x10000), "OPTIONS")

	def test_string_crossing_page_keeps_the_existing_logical_chunk_boundaries(self):
		memory = BoundedMemory(0x1FFF8, b"A" * 40 + b"\0" + b"\0" * 23)
		self.assertEqual(ScaleformReader(memory, 0x400000).string(0x10000), "A" * 40)

	def test_incomplete_string_without_terminator_is_not_announced(self):
		memory = BoundedMemory(0x1FFF8, b"OPTIONS!")
		with self.assertRaises(MemoryReadError):
			ScaleformReader(memory, 0x400000).string(0x10000)

	def run_worker(self, read, running=True):
		memory = types.SimpleNamespace(
			close=Mock(), is_running=lambda: running, image_path=lambda: "C:/game/SSFIV.exe"
		)
		fake_reader = types.SimpleNamespace(read=read, interface=types.SimpleNamespace(_paths={1: (2,)}))
		spoken = []
		connection = patch.object(controller, "connect", return_value=(memory, 0x400000))
		reader_patch = patch.object(controller, "StateReader", return_value=fake_reader)
		catalog_patch = patch.object(controller.Catalog, "for_game", return_value=controller.Catalog())
		self.addCleanup(connection.stop)
		self.addCleanup(reader_patch.stop)
		self.addCleanup(catalog_patch.stop)
		connect = connection.start()
		reader_patch.start()
		catalog_patch.start()
		worker = controller.Reader(1, spoken.append)
		self.addCleanup(lambda: (worker.close(), worker._thread.join(3)))
		worker.focus(True)
		return worker, memory, spoken, connect

	def test_two_partial_reads_recover_without_reopening_or_permission_speech(self):
		state = GameState("menu", mode="Options", detail="Sound Settings")
		error = MemoryReadError(299, "Partial copy", operation="read")
		read = Mock(side_effect=[error, error, state, state, state])

		def sample():
			if read.call_count >= 5:
				return state
			return read()

		worker, memory, spoken, connect = self.run_worker(sample)
		self.wait_for(lambda: bool(spoken))
		self.assertEqual(spoken, ["Options. Sound Settings"])
		self.assertEqual(connect.call_count, 1)
		memory.close.assert_not_called()
		self.assertEqual(worker.current(), state)

	def test_persistent_read_problem_is_reported_and_can_recover(self):
		error = MemoryReadError(299, "Partial copy", operation="read")
		state = GameState("menu", mode="Options", detail="Sound Settings")
		read = Mock(side_effect=error)
		with patch.object(controller, "READ_FAILURE_GRACE", 0):
			worker, memory, spoken, connect = self.run_worker(read)
			self.wait_for(lambda: bool(spoken))
			self.assertEqual(spoken, ["USF4 Reader: The current game screen could not be read."])
			read.side_effect = None
			read.return_value = state
			self.wait_for(lambda: len(spoken) == 2)
			self.assertEqual(spoken[-1], "Options. Sound Settings")
			self.assertEqual(connect.call_count, 1)
			memory.close.assert_not_called()

	def test_closed_game_does_not_announce_permission_error(self):
		read = Mock(side_effect=MemoryReadError(299, "Partial copy", operation="read"))
		_, memory, spoken, _ = self.run_worker(read, running=False)
		self.wait_for(lambda: bool(memory.close.call_count))
		self.assertEqual(spoken, [])

	def test_unexpected_reader_exception_closes_handle(self):
		read = Mock(side_effect=RuntimeError("reader bug"))
		_, memory, spoken, _ = self.run_worker(read)
		self.wait_for(lambda: bool(memory.close.call_count))
		self.assertEqual(spoken, [])


if __name__ == "__main__":
	unittest.main()
