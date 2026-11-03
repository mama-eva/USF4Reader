"""Bounded, read-only AS2 member access for the verified local Scaleform build."""

import math
import struct

from .memory_reader import MemoryReadError


class ScaleformReader:
	def __init__(self, memory, base):
		self.memory = memory
		self.base = base
		self._slots = {}

	def _expect_vtable(self, address, rva):
		if self.memory.u32(address) != self.base + rva:
			raise MemoryReadError("Objeto Scaleform fora do perfil")

	def string(self, address):
		data_pointer = self.memory.u32(address)
		# ASStringNode stores its exact UTF-8 byte length at +0x14 in this build.
		# Property keys are short; read bounded chunks for longer UI text too.
		data = bytearray()
		offset = 0
		while offset < 4096:
			address = data_pointer + offset
			# Never cross an unreadable page just to fetch bytes after a valid terminator.
			size = min(64 - offset % 64, 4096 - offset, 4096 - address % 4096)
			chunk = self.memory.read(address, size)
			data.extend(chunk)
			if b"\0" in chunk:
				break
			offset += size
		end = data.find(b"\0")
		if end < 0:
			raise MemoryReadError("Nome de propriedade Scaleform excede o limite")
		return data[:end].decode("utf-8")

	def members(self, obj):
		"""Snapshot own fields only; never execute ActionScript or follow prototypes."""
		table = self.memory.u32(obj + 0x18)
		if not table:
			return {}
		count, mask = struct.unpack("<II", self.memory.read(table, 8))
		capacity = mask + 1
		if not 0 <= count <= capacity <= 2048 or capacity & mask:
			raise MemoryReadError("Invalid Scaleform member table")
		data = self.memory.read(table + 8, 24 * capacity)
		result = {}
		for offset in range(0, len(data), 24):
			link, key, kind, low, high, _ = struct.unpack_from("<6I", data, offset)
			if link != 0xFFFFFFFE and key:
				result[self.string(key)] = (kind & 255, low, high)
		if self.memory.u32(obj + 0x18) != table:
			raise MemoryReadError("Scaleform table changed")
		return result

	def value(self, raw):
		kind, low, high = raw
		if kind == 3:
			value = struct.unpack("<d", struct.pack("<II", low, high))[0]
			if not math.isfinite(value):
				raise MemoryReadError("Non-finite AS2 number")
			return int(value) if value.is_integer() else value
		if kind == 4:
			return struct.unpack("<i", struct.pack("<I", low))[0]
		if kind == 5:
			return self.string(low)
		if kind == 2:
			return bool(low & 255)
		return None

	def field(self, obj, name):
		return self.value(self.member(obj, name))

	def array(self, obj, maximum=128):
		self._expect_vtable(obj, 0x5CE41C)
		# GASArrayObject owns a GArray<Value*> at +0x30. Verified from live item_list_.
		header = self.memory.read(obj + 0x34, 12)
		pointer, size, capacity = struct.unpack("<III", header)
		if not 0 <= size <= capacity <= maximum:
			raise MemoryReadError("AS2 array exceeds its bound")
		if not size:
			return ()
		items = struct.unpack(f"<{size}I", self.memory.read(pointer, size * 4))
		result = []
		for address in items:
			if not address:
				result.append((0, 0, 0))
				continue
			kind, low, high = struct.unpack("<III", self.memory.read(address, 12))
			result.append((kind & 255, low, high))
		if self.memory.read(obj + 0x34, 12) != header:
			raise MemoryReadError("AS2 array changed")
		return tuple(result)

	def sprite(self, value):
		if value[0] != 7:
			raise MemoryReadError("Expected a MovieClip handle")
		sprite = self.memory.u32(value[1] + 4)
		self._expect_vtable(sprite, 0x5CCFD8)
		return sprite

	def visible(self, sprite):
		# _visible getter VA 0x7d9950: [character+0x90] & 1.
		# Parent native character pointer is +0x24 (verified live and from constructors).
		seen = set()
		for _ in range(24):
			if not sprite:
				return True
			if sprite in seen:
				raise MemoryReadError("Cyclic MovieClip parent chain")
			seen.add(sprite)
			if self.memory.u32(sprite) not in (self.base + 0x5CCFD8, self.base + 0x5C8B88):
				raise MemoryReadError("Unsupported display character type")
			if not self.memory.u32(sprite + 0x90) & 1:
				return False
			sprite = self.memory.u32(sprite + 0x24)
		raise MemoryReadError("MovieClip parent chain exceeds bound")

	def children(self, sprite):
		self._expect_vtable(sprite, 0x5CCFD8)
		header = self.memory.read(sprite + 0xAC, 12)
		pointer, count, capacity = struct.unpack("<III", header)
		if not 0 <= count <= capacity <= 512:
			raise MemoryReadError("Display list exceeds bound")
		if not count:
			return ()
		children = struct.unpack(f"<{count}I", self.memory.read(pointer, count * 4))
		if self.memory.read(sprite + 0xAC, 12) != header:
			raise MemoryReadError("Display list changed")
		return tuple(
			child
			for child in children
			if child and self.memory.u32(child) in (self.base + 0x5CCFD8, self.base + 0x5C8B88)
		)

	def child(self, sprite, name):
		for child in self.children(sprite):
			handle = self.memory.u32(child + 0x84)
			if handle and self.string(self.memory.u32(handle + 8)) == name:
				return child
		raise MemoryReadError("Display child not found: " + name)

	def display_path(self, sprite, *names):
		for name in names:
			sprite = self.child(sprite, name)
		return sprite

	def text_field(self, address):
		self._expect_vtable(address, 0x5C8B88)
		# GFxTextField's retained UTF-8 text is a tagged GString at +0xd0.
		# Read-only equivalent of the branch at VA 0x7e4b0e in GetMember.
		tagged = self.memory.u32(address + 0xD0)
		pointer = tagged & 0xFFFFFFFC
		size = self.memory.u32(pointer) & 0x7FFFFFFF
		if size > 4096:
			raise MemoryReadError("Text field exceeds bound")
		data = self.memory.read(pointer + 8, size + 1)
		if data[-1] or self.memory.u32(address + 0xD0) != tagged:
			raise MemoryReadError("Text field changed")
		return data[:-1].decode("utf-8")

	def rendered_text_field(self, address):
		"""Read the existing display text, after the game's localization substitutions."""
		self._expect_vtable(address, 0x5C8B88)
		# Native GetMember VA 7e4c27 -> DocView::GetText 7f49f0 -> 800720.
		# DocView is native+a4; StyledText is doc+10. Its paragraph vector is +14.
		# Each paragraph starts with a UTF-16 pointer and a length in code units.
		doc = self.memory.u32(address + 0xA4)
		styled = self.memory.u32(doc + 0x10)
		header = self.memory.read(styled + 0x14, 8)
		pointer, count = struct.unpack("<II", header)
		if not 0 < count <= 32:
			raise MemoryReadError("Rendered text paragraph count exceeds bound")
		entries = self.memory.read(pointer, count * 4)
		snapshots = []
		parts = []
		units = 0
		for paragraph in struct.unpack(f"<{count}I", entries):
			span = self.memory.read(paragraph, 8)
			text_pointer, length = struct.unpack("<II", span)
			units += length
			if units > 4096:
				raise MemoryReadError("Rendered text exceeds bound")
			data = self.memory.read(text_pointer, length * 2) if length else b""
			text = data.decode("utf-16-le").removesuffix("\0")
			if "\0" in text:
				raise MemoryReadError("Invalid rendered text")
			parts.append(text)
			snapshots.append((paragraph, span, text_pointer, data))
		for paragraph, span, text_pointer, data in snapshots:
			if self.memory.read(paragraph, 8) != span or (
				data and self.memory.read(text_pointer, len(data)) != data
			):
				raise MemoryReadError("Rendered text changed")
		if (
			self.memory.u32(address + 0xA4) != doc
			or self.memory.u32(doc + 0x10) != styled
			or self.memory.read(styled + 0x14, 8) != header
			or self.memory.read(pointer, count * 4) != entries
		):
			raise MemoryReadError("Rendered text document changed")
		self._expect_vtable(address, 0x5C8B88)
		return "".join(parts)

	def text_value(self, value, *, rendered=False):
		if value[0] == 5:
			return self.string(value[1])
		if value[0] == 6:
			# GASTextFieldObject constructor at VA 0x7df330 binds its native field at +34.
			self._expect_vtable(value[1], 0x5C85FC)
			address = self.memory.u32(value[1] + 0x34)
		elif value[0] == 7:
			address = self.memory.u32(value[1] + 4)
		else:
			return ""
		original = self.text_field(address)
		if rendered:
			try:
				text = self.rendered_text_field(address)
				if (
					text.strip()
					and not text.startswith("ID_")
					and "[CHARANAME]" not in text
					and self.text_field(address) == original
				):
					return text
			except (MemoryReadError, UnicodeError):
				pass
		return original

	def movie_root(self, movie):
		self._expect_vtable(movie, 0x5CC480)
		sprite = self.memory.u32(movie + 0x6C)
		self._expect_vtable(sprite, 0x5CCFD8)
		root = self.memory.u32(sprite + 0x1AC)
		if not root:
			return sprite, None
		self._expect_vtable(root, 0x5CEC9C)
		return sprite, root

	def widget(self, obj):
		fields = self.members(obj)
		if "text_" in fields:
			return str(self.value(fields["text_"]) or "")
		if "spin_list_" in fields and "index_" in fields:
			items = self.array(fields["spin_list_"][1])
			index = self.value(fields["index_"])
			if isinstance(index, int) and 0 <= index < len(items):
				return str(self.value(items[index]) or "")
			return ""
		if "switch_state_" in fields:
			return {"jp": "Japanese", "eng": "English"}.get(self.value(fields["switch_state_"]), "")
		if "index_" in fields:
			return str(self.value(fields["index_"]))
		return ""

	def window(self, obj):
		fields = self.members(obj)
		if not {"item_index_", "item_list_", "mc_", "wnd_state_"} <= fields.keys():
			return None
		if self.value(fields["wnd_state_"]) != "wait" or not self.visible(self.sprite(fields["mc_"])):
			return None
		items = self.array(fields["item_list_"][1])
		index = self.value(fields["item_index_"])
		if not isinstance(index, int) or not 0 <= index < len(items) or items[index][0] != 6:
			return None
		item = self.members(items[index][1])
		name = self.value(item.get("name_", (0, 0, 0)))
		if not name or not isinstance(name, str):
			return None
		value = ""
		for key in ("sub_", "spin_"):
			if item.get(key, (0,))[0] == 6:
				value = self.widget(item[key][1])
				break
		if self.member(obj, "item_index_") != fields["item_index_"]:
			raise MemoryReadError("Menu cursor changed")
		return str(name), value

	def member(self, obj, name):
		table = self.memory.u32(obj + 0x18)
		count, mask = struct.unpack("<II", self.memory.read(table, 8))
		capacity = mask + 1
		if not 0 < count <= capacity <= 2048 or capacity & mask:
			raise MemoryReadError("Tabela de membros Scaleform inválida")
		data = self.memory.read(table + 8, 24 * capacity)
		cache_key = (obj, table, name)
		cached = self._slots.get(cache_key)
		indices = [cached] if cached is not None and cached < capacity else []
		indices += [i for i in range(capacity) if i != cached]
		for i in indices:
			next_index, key, kind, low, high, _ = struct.unpack_from("<6I", data, i * 24)
			if next_index == 0xFFFFFFFE or not key:
				continue
			if self.string(key) != name:
				continue
			if self.memory.u32(obj + 0x18) != table:
				raise MemoryReadError("Tabela Scaleform mudou durante a leitura")
			if len(self._slots) >= 32:
				self._slots.clear()
			self._slots[cache_key] = i
			return kind & 0xFF, low, high
		raise MemoryReadError("Propriedade da interface não encontrada: " + name)

	def root(self, event):
		# MainMenuItem embedded at +0x234; its movie wrapper lives at +0x24.
		wrapper = self.memory.u32(event + 0x258)
		movie = self.memory.u32(wrapper)
		self._expect_vtable(movie, 0x5CC480)
		sprite = self.memory.u32(movie + 0x6C)
		self._expect_vtable(sprite, 0x5CCFD8)
		# Getter at VA 0x849b40 returns the existing AS object from sprite +0x1ac.
		root = self.memory.u32(sprite + 0x1AC)
		self._expect_vtable(root, 0x5CEC9C)
		return wrapper, movie, sprite, root

	def main_cursor(self, event):
		anchors = self.root(event)
		kind, window, _ = self.member(anchors[-1], "item_main_menu")
		if kind != 6:
			raise MemoryReadError("Janela principal Scaleform não é um objeto")
		self._expect_vtable(window, 0x5CE07C)
		kind, low, high = self.member(window, "item_index_")
		if kind not in (3, 4):
			raise MemoryReadError("Índice do cursor Scaleform não é numérico")
		value = float(self.value((kind, low, high)))
		if not math.isfinite(value) or not value.is_integer() or not 0 <= value <= 10:
			raise MemoryReadError("Índice do menu principal fora do intervalo")
		if self.root(event) != anchors:
			raise MemoryReadError("Interface Scaleform mudou durante a leitura")
		return int(value)
