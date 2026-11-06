# USF4 Reader

USF4 Reader is a free, open-source NVDA add-on for Ultra Street Fighter IV on Windows.
It reads supported menus, choices and notices as you navigate with the game's usual controls,
so you can follow your selections without a separate query command or OCR.

[Official website](https://deb-evelyn.com.br/USF4Reader/)
· [Download 0.3.8](https://github.com/mama-eva/USF4Reader/releases/download/v0.3.8/USF4Reader-0.3.8.nvda-addon)
· [Release notes](https://github.com/mama-eva/USF4Reader/releases/tag/v0.3.8)
· [Português](https://github.com/mama-eva/USF4Reader/blob/main/addon/doc/pt_BR/readme.md)

## Features

Reading is available in these supported areas; coverage within each area is still partial:

- Main menus and supported Options screens, including Sound Settings and Voice Language.
- Character selection, customization and Ultra Combo names.
- Trial selection, supported tasks, completion notices and result choices.
- Supported pause menus, confirmation questions and their selected answers.
- Player Data menus and record rows, including character, category and displayed values.
- Stage Select, Versus result choices, and supported startup and fight announcements.

The Versus result menu identifies each player's selection. Moving one player's cursor does not
repeat the other player's unchanged choice. Your NVDA voice and synthesizer settings stay in use.
The tested game installation uses English labels and helper messages, including when NVDA is
configured in Portuguese.

## Compatibility

Tested with **NVDA 2026.1** and the Windows edition of **Ultra Street Fighter IV** used by this project.
The add-on detects the game by its `SSFIV.exe` process name and reads builds that use a
compatible game layout. Compatibility with the Steam edition and other builds still needs
in-game verification.

## Installation and updates

1. Close the game and leave NVDA running.
2. Download and open `USF4Reader-0.3.8.nvda-addon`.
3. Confirm installation or update, then restart NVDA when prompted.
4. Open the game and navigate with your usual keyboard or controller.

Reading starts automatically when you return to the game. There are no add-on query shortcuts
to learn. If you update an existing installation, follow the same steps with the newer package.
Find future versions on the [Releases page](https://github.com/mama-eva/USF4Reader/releases/latest)
or the [official website](https://deb-evelyn.com.br/USF4Reader/).

### Uninstalling

In NVDA, open **Tools → Add-on Store** and find USF4 Reader in the installed add-ons list.
Choose **Remove**, confirm, and restart NVDA when prompted. To pause reading temporarily,
choose **Disable**.

## Known limitations

Some screens may remain silent, and these areas still need work:

- Command List pages, move details and their submenus.
- Intermittent Button Config reading and some other Options screens.
- Some confirmation questions, the matchup splash and other Versus transitions.
- Full coverage of online screens, Bonus Stages, stage variants and pause/result variants.
- Real-time combat statistics and cinematic subtitles displayed as images.

Stage Select reading and the corrected round announcements still await a listening check after
updating to 0.3.7. Character names in color and taunt unlock notices also need confirmation during
play.

See the [changelog](https://github.com/mama-eva/USF4Reader/blob/main/changelog.md) for version history.

## Reporting problems

Use [GitHub Issues](https://github.com/mama-eva/USF4Reader/issues) or email
[smartdebby29@gmail.com](mailto:smartdebby29@gmail.com). Tell me your add-on and NVDA versions,
the game mode, which screen you reached, what you expected to hear and the last announcement.
A screenshot is not required.

## License

USF4 Reader is free and open source under
[GPL-2.0-or-later](https://github.com/mama-eva/USF4Reader/blob/main/COPYING.txt).
Contributions, suggestions and reports of unread screens are welcome.

## Author and contact

**Débora Evelyn Lisboa**

[smartdebby29@gmail.com](mailto:smartdebby29@gmail.com)
