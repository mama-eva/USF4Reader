"""Read the active game's AS2 windows, without running code in the game."""

import struct

from .memory_reader import MemoryReadError
from .stages import STAGE_KEYS

MAIN_WINDOWS = {
	"item_main_menu": "Main menu",
	"item_arcade": "ID_MEN_1000",
	"item_versus": "ID_MEN_1001",
	"item_versus_pvp": "ID_VRS_0000",
	"item_versus_pvc": "ID_VRS_0001",
	"item_versus_cvc": "ID_VRS_0002",
	"item_challenge": "ID_MEN_1004",
	"item_training": "ID_MEN_1005",
}

CUSTOM = (
	(
		"costume_",
		"ID_BTL_3101",
		("ID_BTL_3200", "ID_BTL_3201", "ID_BTL_3202", "ID_TU2_BTL_0000", "ID_TU2_BTL_0001"),
	),
	("color_", "ID_BTL_3102", tuple(f"ID_BTL_{i}" for i in range(3203, 3215))),
	("appeal_", "ID_BTL_3103", ("ID_BTL_3225",) + tuple(f"ID_BTL_{i}" for i in range(3215, 3225))),
	("comment_", "ID_BTL_3104", ("ID_BTL_3238",) + tuple(f"ID_BTL_{i}" for i in range(3226, 3237))),
	("version_", "ID_VERSION", tuple(f"ID_BTL_V{i:02}" for i in range(1, 13))),
)


class InterfaceReader:
	def __init__(self, scaleform, character_keys=None):
		self.sf = scaleform
		self.memory = scaleform.memory
		self.base = scaleform.base
		self._paths = {}
		self.character_keys = character_keys or {}
		self._record_ui_keys = None

	def roots(self, event, vtable, extent=0x400, start=0x44):
		"""Bounded native field discovery, cached as relative paths, never heap pointers.

		Native UI event fields contain either GFxMovieView* or a wrapper whose first
		field is GFxMovieView*. Both vtables and AS root types are verified before use.
		No address-space search, prototype traversal, or remote method calls.
		"""
		cache_key = (vtable, extent, start)
		paths = self._paths.get(cache_key)
		if paths is None:
			paths = []
			containers = [((), event, start, extent)]
			movies = set()
			# Option subevents own their UI through the native controller at +0x44.
			for owner_offset in (0x44, 0x48):
				try:
					owner = self.memory.u32(event + owner_offset)
					owner_vtable = self.memory.u32(owner)
					if (
						self.base + 0x529000 <= owner_vtable < self.base + 0x6366E3
						and owner_vtable != self.base + 0x55E22C
					):
						containers.append(((owner_offset,), owner, 0, 0x400))
				except OSError:
					continue
			for prefix, container, start, end in containers:
				block = self.memory.read(container + start, end - start)
				for offset in range(0, len(block), 4):
					pointer = struct.unpack_from("<I", block, offset)[0]
					if not 0x10000 <= pointer <= 0xFFFFFF00:
						continue
					try:
						first = self.memory.u32(pointer)
						indirect = first != self.base + 0x5CC480
						movie = first if indirect else pointer
						if not 0x10000 <= movie <= 0xFFFFFF00:
							continue
						if movie in movies:
							continue
						self.sf.movie_root(movie)
						movies.add(movie)
						paths.append(prefix + (offset + start,) + ((0,) if indirect else ()))
					except (OSError, ValueError):
						continue
					if len(paths) >= 16:
						break
			if paths:
				if len(self._paths) >= 64:
					self._paths.clear()
				self._paths[cache_key] = tuple(paths)
		result = []
		seen = set()
		for path in paths:
			try:
				movie = event
				for offset in path:
					movie = self.memory.u32(movie + offset)
				sprite, root = self.sf.movie_root(movie)
				if (root or sprite) not in seen and self.sf.visible(sprite):
					seen.add(root or sprite)
					result.append((sprite, root))
			except (OSError, ValueError):
				continue
		return result

	def menus(self, root, default_title):
		sf = self.sf
		fields = sf.members(root)
		# Native functions switch between dynWnd/bakWnd using is_active in controller options.
		active = sf.value(fields.get("is_active", (0, 0, 0)))
		windows = []
		for name, value in fields.items():
			if value[0] != 6 or name.startswith("__"):
				continue
			if name in ("expWnd", "help_text", "option_data"):
				continue
			if active is not None and name in ("dynWnd", "bakWnd"):
				if name != ("dynWnd" if active else "bakWnd"):
					continue
			try:
				selection = sf.window(value[1])
			except MemoryReadError:
				continue
			if selection is None:
				continue
			title = MAIN_WINDOWS.get(name, default_title)
			try:
				settings = sf.member(value[1], "setting_")
				title_obj = sf.member(settings[1], "title")
				actual_title = sf.field(title_obj[1], "name")
				if actual_title:
					title = str(actual_title)
			except MemoryReadError:
				pass
			windows.append((name, title, *selection))
		return windows

	def _player_data_root(self, event, offset, owner_vtable, handle_offset=0xC):
		# PlayerData's native menu owner (VA643d00/644390) stores a shared script
		# handle at +c. The handle's first field is the existing MovieView.
		try:
			owner = self.memory.u32(event + offset)
			self.sf._expect_vtable(owner, owner_vtable)
			handle = self.memory.u32(owner + handle_offset)
			counter = self.memory.u32(owner + handle_offset + 4)
			self.sf._expect_vtable(counter, 0x5C083C)
			if self.memory.u32(counter + 0xC) != handle:
				return None
			movie = self.memory.u32(handle)
			sprite, root = self.sf.movie_root(movie)
			if not root or not self.sf.visible(sprite):
				return None
			if (
				self.memory.u32(event + offset) != owner
				or self.memory.u32(owner + handle_offset) != handle
				or self.memory.u32(owner + handle_offset + 4) != counter
				or self.memory.u32(counter + 0xC) != handle
				or self.memory.u32(handle) != movie
			):
				return None
			return sprite, root
		except MemoryReadError:
			return None

	def player_data_roots(self, event):
		root = self._player_data_root(event, 0xA8, 0x557E80)
		if root:
			return [root]
		# Character Records selector: constructor VA64c780, binding VA64ca14.
		root = self._player_data_root(event, 0x6C, 0x5587BC, handle_offset=0x1C)
		if root and self.sf.field(root[1], "window_state") == "STATE_RUNNING":
			return [root]
		return []

	def stage_select(self, event):
		# VA638510 binds one of the controllers created by VA655970. Both store
		# the shared GFx reference at +10; the event itself is only 0x88 bytes.
		owner = self.memory.u32(event + 0x44)
		if not owner:
			return ""
		vtable = self.memory.u32(owner) - self.base
		if vtable not in (0x53ACB4, 0x53AD74):
			return ""
		view = self._player_data_root(event, 0x44, vtable, handle_offset=0x10)
		if not view:
			return ""
		_, root = view
		control_ref = self.sf.member(root, "ssc")
		if control_ref[0] != 6:
			return ""
		control = control_ref[1]
		if self.sf.field(control, "state_") != 3:
			return ""
		list_ref = self.sf.member(control, "mcc_list_")
		if list_ref[0] != 6:
			return ""
		items = self.sf.array(list_ref[1], maximum=16)
		if len(items) != 8 or items[1][0] != 6:
			return ""
		selector = items[1][1]
		if self.sf.field(selector, "csr_state_") != 0:
			return ""
		if not self.sf.visible(self.sf.sprite(self.sf.member(selector, "mc_"))):
			return ""
		code = self.sf.field(selector, "sel_stage_")
		if not isinstance(code, str) or code not in STAGE_KEYS:
			return ""
		if (
			self.sf.field(selector, "sel_stage_") != code
			or self.sf.field(selector, "csr_state_") != 0
			or self.sf.field(control, "state_") != 3
			or self.sf.member(root, "ssc") != control_ref
			or self.sf.member(control, "mcc_list_") != list_ref
			or self.sf.array(list_ref[1], maximum=16) != items
			or self._player_data_root(event, 0x44, vtable, handle_offset=0x10) != view
		):
			return ""
		return STAGE_KEYS[code]

	def versus_result(self, event):
		# VA635a50/639760 construct the shared result-menu reference inline at
		# +9b8, beyond both the pause manager and the generic event prefix.
		def movie():
			try:
				ref = event + 0x9B8
				handle, counter = self.memory.u32(ref), self.memory.u32(ref + 4)
				if not handle or not counter:
					return None
				self.sf._expect_vtable(counter, 0x5C083C)
				if self.memory.u32(counter + 0xC) != handle:
					return None
				view = self.memory.u32(handle)
				sprite, root = self.sf.movie_root(view)
				if not root or not self.sf.visible(sprite):
					return None
				if (
					self.memory.u32(ref) != handle
					or self.memory.u32(ref + 4) != counter
					or self.memory.u32(counter + 0xC) != handle
					or self.memory.u32(handle) != view
				):
					return None
				return root
			except MemoryReadError:
				return None

		root = movie()
		if not root:
			return ()
		panels, selections = [], []
		for side, name in enumerate(("wnd_1p_menu", "wnd_2p_menu")):
			ref = self.sf.member(root, name)
			if ref[0] != 6:
				return ()
			selected = self.sf.window(ref[1])
			selections.append((name, ref, selected))
			if selected:
				panels.append((side, "result", *selected))
		if movie() != root:
			return ()
		for name, ref, selected in selections:
			if self.sf.member(root, name) != ref or self.sf.window(ref[1]) != selected:
				return ()
		return tuple(panels)

	def _record_character_key(self, ui_id):
		if self._record_ui_keys is None:
			# Native-to-record UI IDs used by VA67db40. The two orders differ.
			indices = struct.unpack("<44i", self.memory.read(self.base + 0x55A9D8, 44 * 4))
			if sorted(indices) != list(range(44)):
				raise MemoryReadError("Record character mapping is outside the verified profile")
			self._record_ui_keys = {
				ui_index: self.character_keys[native_index]
				for native_index, ui_index in enumerate(indices)
				if isinstance(self.character_keys.get(native_index), str)
			}
		return self._record_ui_keys.get(ui_id, "")

	def player_data_record(self, event):
		"""Read the selected visible record row, including its displayed value."""
		owner = self.memory.u32(event + 0xA8)
		if not owner:
			return None
		owner_vtable = self.memory.u32(owner) - self.base
		if owner_vtable not in (0x557CE8, 0x557FA4):
			return None
		# Constructors VA641910 and 644b30 store the script reference at +24.
		view = self._player_data_root(event, 0xA8, owner_vtable, handle_offset=0x24)
		if not view:
			return ()
		_, root = view
		if self.sf.field(root, "window_state") != "STATE_RUNNING":
			return ()
		model_ref, window_ref = self.sf.member(root, "player_data"), self.sf.member(root, "dynWnd")
		if model_ref[0] != 6 or window_ref[0] != 6:
			return ()
		model, window = model_ref[1], window_ref[1]
		fields = self.sf.members(window)
		if self.sf.value(fields.get("wnd_state_", (0, 0, 0))) != "wait":
			return ()
		if not self.sf.visible(self.sf.sprite(fields.get("mc_", (0, 0, 0)))):
			return ()
		actual = self.sf.value(fields.get("actual_item_index_", (0, 0, 0)))
		local = self.sf.value(fields.get("item_index_", (0, 0, 0)))
		top = self.sf.value(fields.get("actual_item_index_of_displayed_top_", (0, 0, 0)))
		count = self.sf.value(fields.get("actual_item_num_", (0, 0, 0)))
		if not all(type(value) is int for value in (actual, local, top, count)):
			return ()
		items = self.sf.array(fields["item_list_"][1])
		names = self.sf.array(self.sf.member(model, "data_name_")[1])
		if not (
			0 <= actual < count == len(names) <= 128 and 0 <= local < len(items) and actual == top + local
		):
			return ()
		if items[local][0] != 6:
			return ()
		item = self.sf.members(items[local][1])
		name = self.sf.value(item.get("name_", (0, 0, 0)))
		if not isinstance(name, str) or not name or name == "_space_" or self.sf.value(names[actual]) != name:
			return ()
		group, data_type = self.sf.field(model, "data_group_"), self.sf.field(model, "data_type_")
		character_id = self.sf.field(model, "character_id_") if group == "GRP_CHARACTER_RECORD" else None
		context = self.player_data_page(event, navigation=False, expected_character=character_id)
		if not context:
			return ()
		values = []
		subs = self.sf.array(item["sub_"][1], maximum=8)
		types = self.sf.array(item["sub_type_"][1], maximum=8)
		if len(subs) != len(types):
			return ()
		for index, (sub, kind) in enumerate(zip(subs, types)):
			if sub[0] == 6 and self.sf.value(kind) == "spinbox":
				value = self.sf.widget(sub[1])
				if value:
					values.append("Rank " + value if data_type == "CR_WIN_PER" and index == 1 else value)
		if not values:
			return ()
		for key in ("actual_item_index_", "item_index_", "actual_item_index_of_displayed_top_", "wnd_state_"):
			if self.sf.member(window, key) != fields[key]:
				return ()
		if (
			self.sf.member(root, "player_data") != model_ref
			or self.sf.field(model, "data_group_") != group
			or self.sf.field(model, "data_type_") != data_type
			or character_id is not None
			and self.sf.field(model, "character_id_") != character_id
			or self._player_data_root(event, 0xA8, owner_vtable, handle_offset=0x24) != view
		):
			return ()
		return context, name, tuple(values)

	def player_data_page(self, event, *, navigation=True, expected_character=None):
		# Record-page constructor VA647a90/647af0 and live shared handles.
		page = self._player_data_root(event, 0xB8, 0x5580CC)
		if not page:
			return ()
		_, root = page
		if self.sf.field(root, "window_state") != "STATE_RUNNING":
			return ()
		window = self.sf.member(root, "dynWnd")
		if window[0] != 6:
			return ()
		fields = self.sf.members(window[1])
		if self.sf.value(fields.get("wnd_state_", (0, 0, 0))) != "wait":
			return ()
		if not self.sf.visible(self.sf.sprite(fields.get("mc_", (0, 0, 0)))):
			return ()
		title = self.sf.field(root, "title_name")
		if not isinstance(title, str) or not title:
			return ()
		lines = []
		heading = self._player_data_root(event, 0xB0, 0x557F6C)
		if heading:
			lines.extend(self.texts(heading[0]))
		character = self._player_data_root(event, 0xC0, 0x557C78)
		character_id = None
		if character and self.sf.field(character[1], "window_state") == "STATE_RUNNING":
			character_id = self.sf.field(character[1], "character_id")
			if expected_character is not None and character_id != expected_character:
				return ()
		elif expected_character is not None:
			character_id = expected_character
		if type(character_id) is int:
			key = self._record_character_key(character_id)
			if key:
				lines.append(key)
		lines.append(title)
		# Optional native navigation strip; its reference is inline rather than at +c.
		try:
			nav = self.memory.u32(event + 0x1F8) if navigation else 0
			if nav:
				handle = self.memory.u32(nav)
				counter = self.memory.u32(nav + 4)
				self.sf._expect_vtable(counter, 0x5C083C)
				if self.memory.u32(counter + 0xC) == handle:
					nav_sprite, nav_root = self.sf.movie_root(self.memory.u32(handle))
					if nav_root and self.sf.visible(nav_sprite):
						help_lines = list(self.texts(nav_sprite))
						for index in range(len(help_lines) - 3, -1, -1):
							if (
								help_lines[index].startswith("ID_KEY_")
								and help_lines[index + 1] == "/"
								and help_lines[index + 2].startswith("ID_KEY_")
							):
								help_lines[index : index + 3] = [
									help_lines[index] + "@/@" + help_lines[index + 2]
								]
						if self.memory.u32(event + 0x1F8) == nav and self.memory.u32(nav) == handle:
							lines.extend(help_lines)
		except MemoryReadError:
			pass
		if (
			self.sf.field(root, "title_name") != title
			or self.sf.field(root, "window_state") != "STATE_RUNNING"
		):
			return ()
		if (
			character
			and character_id is not None
			and (
				self.sf.field(character[1], "character_id") != character_id
				or self._player_data_root(event, 0xC0, 0x557C78) != character
			)
		):
			return ()
		return tuple(dict.fromkeys(lines))

	def texts(self, sprite):
		"""Read visible GFx text fields in display order, with a strict per-sample bound."""
		pending = [(sprite, 0)]
		visited = set()
		lines = []
		while pending and len(visited) < 256:
			current, depth = pending.pop()
			if current in visited or depth > 12:
				continue
			visited.add(current)
			if not self.sf.visible(current):
				continue
			if self.memory.u32(current) == self.base + 0x5C8B88:
				text = self.sf.text_field(current).strip()
				if text and text not in lines:
					lines.append(text)
			else:
				pending.extend((child, depth + 1) for child in reversed(self.sf.children(current)))
		return tuple(lines)

	def trial(self, root):
		fields = self.sf.members(root)
		if fields.get("cursor", (0,))[0] != 6:
			return None
		index = self.sf.field(fields["cursor"][1], "current_pos")
		if not isinstance(index, int) or not 0 <= index < 24:
			return None
		lines = []
		if fields.get("r_tasks", (0,))[0] == 7:
			tasks = self.sf.sprite(fields["r_tasks"])
			for task in range(8):
				parts = []
				for part in ("situation", "strong", "command"):
					text_field = self.sf.display_path(tasks, f"ins_task_{task}", f"ins_text_{part}")
					if self.sf.visible(text_field):
						text = self.sf.text_field(text_field).strip()
						if text:
							parts.append(text)
				if parts:
					lines.append(tuple(parts))
		if self.sf.field(fields["cursor"][1], "current_pos") != index:
			raise MemoryReadError("Trial selection changed")
		return index, tuple(lines)

	def trial_battle(self, event):
		"""TrialBattle owns the in-fight task display and completion menu separately."""
		lines = []
		menus = []
		for offset in (0xC98, 0xCE4):
			wrapper = self.memory.u32(event + offset)
			if not wrapper:
				continue
			sprite, root = self.sf.movie_root(self.memory.u32(wrapper))
			if not root or not self.sf.visible(sprite):
				continue
			if offset == 0xCE4:
				menus.extend(self.menus(root, "Trial complete"))
				continue
			fields = self.sf.members(root)
			if fields.get("r_tasks", (0,))[0] != 7:
				continue
			tasks = self.sf.sprite(fields["r_tasks"])
			for task in range(8):
				parts = []
				for part in ("situation", "strong", "command", "supplement"):
					text_field = self.sf.display_path(tasks, f"ins_task_{task}", f"ins_text_{part}")
					if self.sf.visible(text_field):
						text = self.sf.text_field(text_field).strip()
						if text:
							parts.append(text)
				if parts:
					lines.append(tuple(parts))
		return tuple(lines), menus

	def character_panels(self, event, flags):
		sf, memory = self.sf, self.memory
		control = memory.u32(event + 0x48)
		if not control:
			return ()
		sf._expect_vtable(control, 0x5317DC)
		panels = []
		for side in range(2):
			if not flags & (1 << side) or flags & (8 << side):
				continue
			for owner_offset, movie_offset, owner_vtable, kind in (
				(0x3C + side * 4, 0x144, 0x531AE0, "custom"),
				(0x44 + side * 4, 0x124, 0x532700, "ultra"),
				(0x4C + side * 4, 0x44, 0x531DA8, "handicap"),
			):
				if not flags & {"custom": 0x800, "ultra": 0x1000, "handicap": 0x2000}[kind]:
					continue
				owner = memory.u32(control + owner_offset)
				sf._expect_vtable(owner, owner_vtable)
				wrapper = memory.u32(owner + movie_offset)
				movie = memory.u32(wrapper)
				sprite, root = sf.movie_root(movie)
				if not root or not sf.visible(sprite):
					continue
				wnd = sf.member(root, "wnd")
				if wnd[0] != 6:
					continue
				fields = sf.members(wnd[1])
				if fields.get("mask_flag_", (0,))[0] == 2 and sf.value(fields["mask_flag_"]):
					continue
				if kind == "custom":
					index = sf.value(fields.get("sel_item_", (0, 0, 0)))
					if not isinstance(index, int) or not 0 <= index < len(CUSTOM):
						continue
					field, label, values = CUSTOM[index]
					value = sf.value(fields.get(field, (0, 0, 0)))
					if isinstance(value, int) and 0 <= value < len(values):
						panels.append((side, kind, label, values[value]))
				elif kind == "ultra":
					index = sf.value(fields.get("sel_id_", (0, 0, 0)))
					if isinstance(index, int) and 0 <= index < 3:
						selectors = sf.array(fields["_selectors"][1])
						selection_count = sf.value(fields.get("_selIndex", (0, 0, 0)))
						if isinstance(selection_count, int) and 0 < selection_count < len(selectors):
							selector = sf.sprite(selectors[selection_count])
							if sf.visible(selector):
								text_field = sf.display_path(selector, f"Item{index}", "ItemText")
								value = sf.text_field(text_field)
								panels.append((side, kind, "ID_BTL_3106", value))
				else:
					selector = sf.child(sprite, "Selector")
					if sf.visible(selector):
						index = sf.value(fields.get("handicap_index_", (0, 0, 0)))
						if isinstance(index, int) and 0 <= index < 5:
							panels.append(
								(side, kind, "ID_BTL_3105", ("100%", "75%", "50%", "25%", "Minimum")[index])
							)
		if memory.u32(event + 0x48) != control:
			raise MemoryReadError("Character interface changed")
		return tuple(panels)
