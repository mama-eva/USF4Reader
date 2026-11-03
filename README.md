# USF4 Reader

USF4 Reader is an NVDA add-on that automatically reads supported menus, choices and notices in
Ultra Street Fighter IV for Windows. Navigate with your usual game controls and hear the selection
as it changes. No add-on query shortcuts or OCR are required.

**Author:** Débora Evelyn Lisboa  
**Contact:** [smartdebby29@gmail.com](mailto:smartdebby29@gmail.com)

[Download USF4 Reader 0.3.7](https://github.com/mama-eva/USF4Reader/releases/download/v0.3.7/USF4Reader-0.3.7.nvda-addon)
· [Release notes](https://github.com/mama-eva/USF4Reader/releases/tag/v0.3.7)

## Compatibility

- NVDA 2026.1 on Windows.
- The verified 32-bit `SSFIV.exe` edition of Ultra Street Fighter IV.

Supported executable SHA-256:

```text
a9017416ee8104cdde64d79f1e47697c1dfecb3d58496e4950945c3e37dea537
```

Compatibility with other executable editions or later NVDA releases has not been confirmed.
The game is not included.

## Install or update

1. Close the game and keep NVDA running.
2. Open `USF4Reader-0.3.7.nvda-addon` from the release assets.
3. Confirm installation or update, then restart NVDA when requested.
4. Open the game and navigate normally with your keyboard or controller.

Speech follows supported changes automatically. Your configured NVDA voice and synthesizer remain
under your control. The verified installation uses English game labels and English helper messages,
even when NVDA itself is set to Portuguese.

## Available reading

- Recognized main menus and submenus, including the selected item and supported values.
- Character selection, customization and Ultra Combo names.
- Trial selection, recognized tasks, completion notices and result choices.
- Recognized pause menus and confirmation questions, including the selected answer.
- Startup logos, the opening-movie skip notice and the title-screen Enter prompt.
- Recognized fight announcements such as Round, Fight! and K.O.
- Player Data navigation, the Character Records selector, and selected record rows with their
  character, category, label and displayed values.
- Stage Select navigation and the Versus result choices: Rematch, Select Character and Quit Versus.

On the Versus result screen, each player's selection is identified. Changing one player's choice
does not repeat the other player's unchanged choice.

## What's new in 0.3.7

- Added Stage Select reading.
- Added the Versus result menu and independent selection tracking for both players.
- Corrected round numbering so the first round is Round 1 and the second is Round 2.
- Retained the Player Data additions and stability improvements from the preceding test builds.

## Validation and known limitations

The release passed **101 automated tests**. Earlier regression checks were retained; one old
second-round expectation was corrected because it reproduced the numbering bug.

Live listening checks confirmed main-menu navigation, Options, Sound Settings, Voice Language,
Player Data lists and record values, and the Versus result menu. Stage Select and the round-number
correction were checked against real game captures and automated replay; a listening check of those
two changes after installing 0.3.7 is still pending.

Coverage is incomplete. Areas still requiring work or further checks include:

- Command List pages, move details and their submenus.
- Intermittent Button Config reading and remaining option-screen variants.
- Additional confirmation variants and some Versus transitions, including the matchup splash.
- Full coverage of online screens, Bonus Stages, stage variants and pause/result variants.
- Combat statistics and cinematic subtitles presented as images.

Unknown screens may remain silent. The recipient's name in color/taunt unlock notices still awaits
a new live listening check. These limits are not presented as completed features.

The add-on runs inside NVDA. No separate program needs to be started, and the original game files
are not changed.

## Version history

See [the changelog](https://github.com/mama-eva/USF4Reader/blob/main/changelog.md) for the release history. Version 0.3.7 is the first public GitHub
release; earlier versions were distributed for interactive testing.

The repository and release notes are in English. The distributed 0.3.7 package retains its Portuguese
user guide, and a Portuguese guide is retained as a translation.

## Feedback

Report a problem through [GitHub Issues](https://github.com/mama-eva/USF4Reader/issues) or email
[smartdebby29@gmail.com](mailto:smartdebby29@gmail.com). Include the add-on version, game mode,
screen and last spoken item. A screenshot is not required.

USF4 Reader is licensed under [GPL-2.0-or-later](https://github.com/mama-eva/USF4Reader/blob/main/COPYING.txt).
