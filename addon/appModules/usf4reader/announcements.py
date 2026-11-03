"""Pure debounce and change detection, independent from NVDA and Windows."""


class Announcements:
	def __init__(self, catalog, debounce=0.10):
		self.catalog = catalog
		self.debounce = debounce
		self.candidate = None
		self.since = 0.0
		self.accepted = None

	def reset(self):
		self.candidate = None
		self.accepted = None

	def update(self, state, now):
		if state != self.candidate:
			time_tick = (
				state.screen == "records"
				and state.detail == "ID_PDT_1002"
				and self.candidate
				and self.candidate.screen == "records"
				and self.candidate.mode == state.mode
				and self.candidate.detail == state.detail
			)
			self.candidate = state
			if not time_tick:
				self.since = now
				return None
		if now - self.since < self.debounce or state == self.accepted:
			return None
		previous = self.accepted
		self.accepted = state
		if state.screen in ("transition", "initializing", "unknown"):
			return None
		if (
			state.screen == "trialBattle"
			and previous
			and previous.screen == "trialBattle"
			and state.lines == previous.lines
			and not state.detail
		):
			return None
		if (
			state.screen == "dialog"
			and previous
			and previous.screen == "dialog"
			and previous.detail == state.detail
		):
			return self.catalog.text(state.value) or None
		if (
			state.screen == "records"
			and previous
			and previous.screen == "records"
			and state.mode == previous.mode
		):
			if state.detail == previous.detail and state.detail == "ID_PDT_1002":
				return None
			return self.catalog.record_item(state) or None
		if (
			state.screen in ("mainMenu", "menu")
			and previous
			and previous.screen == state.screen
			and previous.mode == state.mode
		):
			return self.catalog.menu_item(state) or None
		if state.screen == "versusResult" and previous and previous.screen == state.screen:
			return (
				". ".join(self.catalog.panel(panel) for panel in state.panels if panel not in previous.panels)
				or None
			)
		if state.screen == "characterSelect" and previous and previous.screen == state.screen:
			if state.panels:
				return (
					". ".join(
						self.catalog.panel(panel) for panel in state.panels if panel not in previous.panels
					)
					or None
				)
			if previous.panels:
				return self.catalog.describe(state)
			if sum(code is not None for code in state.players) == 1 and state.players != previous.players:
				return next(self.catalog.character(code) for code in state.players if code)
			changes = [
				self.catalog.player(i, self.catalog.character(code))
				for i, code in enumerate(state.players)
				if code and code != previous.players[i]
			]
			return ". ".join(changes) or None
		return self.catalog.describe(state)
