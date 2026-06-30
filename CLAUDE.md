# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Croquis is a Tkinter desktop app for timed figure-drawing practice: it cycles through
reference images from user-configured folders on a timer, full-screen, packaged as a
single Windows `.exe` via PyInstaller. See `README.md` for user-facing usage and
`config.toml` format.

## Commands

```sh
poetry install --with dev   # install deps (Python 3.13–3.14, see pyproject.toml)
poetry run croquis          # run from source (== make run)
poetry run pytest           # run tests
poetry run pytest croquis/tests/test_util.py::test_parse_timer  # single test
poetry run ruff format      # format (== make format)
poetry run ruff check       # lint — expect a large pre-existing count from the
                             # wildcard-import style below; don't try to fix those
make build                  # PyInstaller build via build.py, copies croquis.exe to repo root
```

There's no `config.toml` checked in (gitignored, per-user image library). Running the app
without one generates an example from `constants.DEFAULT_CONFIG`.

## Architecture

**One Tk root + one Canvas, two screens drawn onto it.** `croquis/main.py` creates a
single `Tk()` and `Canvas` and owns a `select_state(action)` closure that swaps between
the two "screens" by drawing onto that same canvas — there are no separate windows.
`select_state("main_menu")` builds a `MainMenuApp`; `select_state("session")` builds a
`SessionApp`. Each screen's app object is responsible for deleting its own canvas items
(`delete_children()`) before handing control back via a callback, and for re-binding
`<Configure>`/keyboard events on `tk` (binding replaces, not stacks, so only the active
screen's handlers are live).

- `croquis/main_menu.py` — `MainMenuApp`: pick an imageset + mode, "Start Session" hands
  off to `session.start_session(...)`.
- `croquis/session.py` — `SessionApp`: drives the actual timed/manual image sequence
  (`tick()` reschedules itself via `tk.after(1000, ...)`; `go_to_image(new_index)` is the
  single state-transition point — it's used both for advancing/going back *and* for
  redrawing the current image on window resize, so it has to distinguish "new image"
  (reset the per-image timer) from "same image, just resized" (keep the timer). `-1`
  (`SessionApp.NOT_SET`) does double duty as both "no timer running" and "before the
  first image" sentinel.
- `croquis/model.py` — dataclasses for `config.toml`: `Config`, `Mode`, `ImageSet`,
  `Category`. Deserialization is hand-rolled in `__post_init__` (dict → dataclass), not a
  library. **`Category` is just a tag spec** — the actual "virtual imageset" it expands to
  (union of paths/tags from every real imageset whose tags are a superset of the
  category's) is computed in `main.py:_start()`, not in `model.py`.
- `croquis/constants.py` — every layout/color magic number plus `DEFAULT_CONFIG` (the
  TOML template written out on first run).
- `croquis/util.py` — config/timer parsing (`parse_timer`, `parse_bool`), image discovery
  (`images_in_path`, walks folders recursively), `resource_path()` (PyInstaller `_MEIPASS`
  vs dev-mode path resolution — needed for `icon.ico`).
- `croquis/error_modal.py` — any uncaught exception from `start()` in `main.py` is caught
  and shown in a separate fatal-error Tk window (`show_error_modal`), then exits. If a
  change can throw during startup/event handlers, know that it surfaces here rather than
  a traceback in a console.

**Codebase convention:** files use `from tkinter import *` / `from croquis.x import *`
throughout (Tk constants like `FLAT`, `W`, `NW` are used unqualified). This is intentional
existing style, not an oversight — match it rather than switching to qualified imports in
files that already use the wildcard style.

**Tkinter geometry manager gotcha (bit us once, see git history on `fix/menu-and-timer-bugs`):**
a single parent can't have children under both `grid` and `pack` — but inside a widget
that's itself embedded via `canvas.create_window(...)`, Tk silently skips the usual
conflict error instead of raising, so a broken mix (e.g. `grid()` to place + `pack()`/
`pack_forget()` to show/hide) won't crash, it'll just silently fail to hide anything.
Prefer `grid_remove()`/`grid()` for runtime show/hide of grid-placed widgets, or — better,
per the current `main_menu.py` pattern — reuse one set of widgets and update their text
instead of building one widget set per item and toggling visibility.

**Testing Tkinter code without a display:** `croquis/tests/` currently only covers pure
logic (`test_util.py`: `parse_timer`, `scale_rect_to_bounds`) — no GUI tests exist. When
you do need to drive real Tk widgets to verify behavior, you can construct the actual
`Tk()`/`Canvas`/app objects in a throwaway script (no `mainloop()` needed — call
`tk.update()` after state changes and inspect via `winfo_ismapped()`, `winfo_manager()`,
`.cget(...)`, etc.), which is how the menu/timer bugs above were confirmed and verified
fixed.
