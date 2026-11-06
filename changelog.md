# USF4 Reader changelog

## 0.3.8

- Detects Ultra Street Fighter IV by its `SSFIV.exe` process name and allows compatible Windows builds
  with different executable checksums or image sizes.
- Announces when the loaded game layout is unsupported.

The Steam edition and other builds still need in-game verification.

## 0.3.7

- Added reading for Stage Select and the Versus result menu: Rematch, Select Character and Quit Versus.
- Followed each player's result choice separately.
- Corrected round numbering, including the previously silent first round.
- Retained Player Data reading and earlier stability improvements.

Stage Select reading and the corrected round announcements still need a listening check after
updating to this version. See the README for all known limitations.

## 0.3.6

- Added Player Data navigation and Character Records character selection.
- Read selected record rows with their character, category and displayed values, including after scrolling.
- Avoided repeating the total play-time counter while it changes.
- Corrected the Voice Language screen title.

## 0.3.5

- Reduced NVDA freezes during game navigation.
- Improved the timing of startup notices.
- Improved recovery when reading is briefly interrupted.

## 0.3.4

- Distinguished temporary reading interruptions from permission problems.
- Improved recovery when moving between screens.
- Reduced cases where menu text was not announced.

## 0.3.3

- Announced unlimited time as Infinite in English menus.
- Improved color and taunt unlock notices and avoided reading unfinished character-name text.
- Preserved the Car Crusher unlock notice and supported questions.

Character names in color and taunt unlock notices still need confirmation during play.

## 0.3.2

- Read questions, notices and their selected answers, including changes between Yes and No.
- Added startup-logo, opening-skip and title-screen notices.
- Improved Trial instructions and completion/result reading.

## 0.3.1

- Read the Trial grid, challenge number and supported instructions.
- Expanded pause-menu reading.

## 0.3.0

- Used the game's label language.
- Read supported submenu values, customization and Ultra Combo names.
- Added supported fight announcements.
