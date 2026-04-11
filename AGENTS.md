# Repository Guidelines

## Project Structure & Module Organization

This repository is a small PySide6 desktop app for browsing and downloading assets from `KonshinHaoshin/mygoxmujica_archive`.

- `main.py` starts the app and opens the mirror-selection flow.
- `ui_main.py` contains the main window and most UI behavior.
- `github_api.py`, `download_thread.py`, `preview_worker.py`, and `cache.py` hold API, download, preview, and caching logic.
- `mirror_dialog.py`, `announcement_dialog.py`, and `github_hosts_updater.py` contain supporting dialogs and utilities.
- `style.qss`, `icon.*`, `down_arrow_cute.png`, and `7-Zip/` are bundled runtime assets.
- Build output goes to `build/` and `dist/`; avoid editing generated files directly.

## Build, Test, and Development Commands

- `.venv/Scripts/pip install PySide6 python-dotenv requests` installs runtime dependencies.
- `.venv/Scripts/python main.py` runs the app locally.
- `pyinstaller -w -F main.py --icon=icon.ico --add-data "style.qss;." --add-data "down_arrow_cute.png;." --add-data "icon.png;."` builds the Windows executable.

If you do not use the checked-in virtual environment, substitute your local `python` and `pip` commands.

## Coding Style & Naming Conventions

- Follow existing Python style: 4-space indentation, snake_case for functions/variables, PascalCase for Qt widget and thread classes.
- Keep changes focused; this project favors small, reviewable edits over broad refactors.
- Preserve Chinese UI copy unless the task explicitly changes user-facing text.
- Reuse existing helpers such as `resource_path()` and current signal/slot patterns before adding new abstractions.

## Testing Guidelines

There is no automated test suite yet. Verify changes with targeted manual checks:

- launch via `main.py`
- load repository folders and file lists
- test preview, download, and mirror switching for the affected path
- if packaging-related, run the PyInstaller build and confirm bundled assets still resolve

Document what you verified in the PR or handoff note.

## Commit & Pull Request Guidelines

Recent history prefers short, imperative commit subjects, usually with prefixes like `feat:`, `fix:`, or `refactor:`. Keep commits scoped to one change, for example: `fix: prevent preview thread shutdown crash`.

PRs should include:

- a concise summary of behavior changes
- linked issue or task context when available
- manual verification steps
- screenshots or short recordings for UI changes

## Security & Configuration Tips

- Put `GITHUB_TOKEN` in `.env`; do not hardcode secrets.
- Be careful with `github_hosts_updater.py`, which changes the Windows hosts file and may require admin rights.
- Do not commit generated caches, local env changes, or files from `build/` and `dist/` unless explicitly needed.
