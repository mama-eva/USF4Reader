"""Read modal message boxes owned by RootEvent, before the obscured game screen."""

from .memory_reader import MemoryReadError


class DialogReader:
	def __init__(self, scaleform):
		self.sf = scaleform
		self.memory = scaleform.memory
		self.base = scaleform.base

	def read(self, root_event):
		# Root initializer VA 0x5ef590 owns two shared MessageBoxUtil layers.
		# Layer +94 has depth 0; +84 has depth -16. Inspect the upper layer first.
		for offset in (0x94, 0x84):
			active = False
			try:
				util = self.memory.u32(root_event + offset)
				if not util:
					continue
				counter = self.memory.u32(root_event + offset + 4)
				self.sf._expect_vtable(counter, 0x552BC4)
				if self.memory.u32(counter + 0xC) != util:
					return "transition", "", ""
				window = self.memory.u32(util + 0xC)
				if not window:
					continue
				active = True
				self.sf._expect_vtable(window, 0x5582BC)
				if self.memory.u32(window + 0x54) != 1:
					return "transition", "", ""
				question = ""
				choice = ""
				for slot in (4, 0xC):
					wrapper = self.memory.u32(window + slot)
					if not wrapper:
						continue
					sprite, root = self.sf.movie_root(self.memory.u32(wrapper))
					if not root or not self.sf.visible(sprite):
						continue
					wnd = self.sf.member(root, "dynWnd")
					if wnd[0] != 6:
						continue
					fields = self.sf.members(wnd[1])
					if self.sf.value(fields.get("wnd_state_", (0, 0, 0))) != "wait":
						return "transition", "", ""
					if fields.get("mc_", (0,))[0] != 7 or not self.sf.visible(self.sf.sprite(fields["mc_"])):
						continue
					help_value = fields.get("help_tf_", (0, 0, 0))
					text = self.sf.text_value(help_value)
					if text in ("ID_DLG_3003", "ID_DLG_3004"):
						text = self.sf.text_value(help_value, rendered=True)
					if text:
						question = text
					item = self.sf.window(wnd[1])
					if item:
						choice = item[0]
				if (
					self.memory.u32(root_event + offset) != util
					or self.memory.u32(util + 0xC) != window
					or self.memory.u32(window + 0x54) != 1
				):
					return "transition", "", ""
				if question:
					return "dialog", question, choice
				return "transition", "", ""
			except (MemoryReadError, UnicodeError):
				if active:
					return "transition", "", ""
		return None
