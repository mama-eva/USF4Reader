# USF4 Reader changelog

## 0.3.7

- Added Stage Select reading and selection tracking.
- Added Rematch, Select Character and Quit Versus reading after a Versus match.
- Tracked each player's result choice independently.
- Corrected zero-based round numbering, including the previously silent first round.
- Preserved Player Data support and the stability corrections from earlier test builds.
- Prepared the first public repository with English documentation and release notes.

The Versus result menu was confirmed through live listening. Stage Select and the round-number
correction were verified with real game captures and automated replay; post-update listening checks
for those two changes remain pending. All 101 automated tests passed.

## 0.3.6

- Added Player Data menu navigation and Character Records character selection.
- Read selected Player Records and Character Records rows with category, label and displayed values.
- Followed scrolling lists and avoided repeating a running play-time counter.
- Corrected the Voice Language screen title.

Player Data lists and values were confirmed through live listening.

## 0.3.5

- Prevented a cause of NVDA freezes while identifying game windows.
- Improved startup-notice timing.
- Preserved recovery from incomplete reads without unnecessary reconnections.

Opening, main-menu, Options and Sound Settings navigation were confirmed without a recurring freeze
during the interactive checks. This does not guarantee that every remaining stability issue is resolved.

## 0.3.4

- Distinguished temporary read failures from permission problems.
- Recovered from transient failures without reopening a valid game connection.
- Corrected reading of terminated text near a readable-page boundary.

## 0.3.3

- Announced unlimited time as Infinite in English menus.
- Improved color and taunt unlock notices and avoided unresolved character-name placeholders.
- Preserved the Car Crusher unlock notice and previously supported questions.

## 0.3.2

- Read questions, notices and their selected answers.
- Followed changes between Yes and No.
- Added startup-logo, opening-skip and title-screen notices.
- Improved Trial instructions and completion/result reading.

## 0.3.1

- Read the Trial grid, challenge number and recognized instructions.
- Expanded pause-menu reading.

## 0.3.0

- Used the game's label language.
- Read supported submenu values, customization and Ultra Combo names.
- Added recognized fight announcements.
