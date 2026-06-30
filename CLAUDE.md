# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Croquis is a Tkinter desktop app for timed figure-drawing practice: it cycles through
reference images from user-configured folders on a timer, full-screen, packaged as a
single Windows `.exe` via PyInstaller. See `README.md` for user-facing usage and
`config.toml` format.

The menu/editor UI uses `ttk` (themed widgets) skinned by `sv-ttk`, applied once per
`Tk()` root via `croquis/theme.py:apply_theme()` and following the OS light/dark setting
(`darkdetect`). The session screen (`session.py`) is intentionally NOT themed this way —
see its note below.

## Commands

```sh
poetry install --with dev   # install deps (Python 3.13–3.14, see pyproject.toml)
poetry run croquis          # run from source (== make run)
poetry run pytest           # run tests
poetry run pytest croquis/tests/test_util.py::test_parse_timer  # single test
poetry run pytest croquis/tests/test_model.py  # config/imageset/category helpers
poetry run ruff format      # format (== make format)
poetry run ruff check       # lint — expect a large pre-existing count from the
                             # wildcard-import style below; don't try to fix those
make build                  # PyInstaller build via build.py, copies croquis.exe to repo root
```

There's no `config.toml` checked in (gitignored, per-user image library). Running the app
without one generates an example from `constants.DEFAULT_CONFIG`.

## Architecture

**One Tk root, one shared Canvas used only by the session screen, no separate windows
for menu vs. session.** `croquis/main.py` creates a single `Tk()` and `Canvas`, and owns
a `select_state(action)` closure that switches between the two "screens." The `Canvas`
is `pack()`/`pack_forget()`'d around this switch (`select_state("session")` packs it,
`select_state("main_menu")` forgets it) — `MainMenuApp` does **not** embed in the canvas
(it used to; this was changed during the ttk restyle, see `main_menu.py` below), it's a
plain `ttk.Frame` packed directly into `tk`. One asymmetry to know: menu→session does
*not* go through `select_state` — `MainMenuApp.start_session()` calls
`session.start_session(...)` directly (and packs the canvas itself first) — only
session→menu (`SessionApp.restart()` calling the `main_menu_callback`) and the CLI's
initial direct-to-session launch go through `select_state`. Each screen's app object is
responsible for tearing down its own widgets (`delete_children()`) before handing control
back, and for re-binding keyboard events on `tk` (binding replaces, not stacks, so only
the active screen's handlers are live).

- `croquis/main_menu.py` — `MainMenuApp`: all `ttk` widgets, responsive (`columnconfigure`/
  `rowconfigure` weights + `sticky="nsew"`, not fixed pixel sizes — resizes/reflows with
  the window). Check one or more imagesets (`ttk.Checkbutton`s, multi-select) + pick a
  mode (`ttk.Radiobutton`s bound to one `StringVar` — native mutual-exclusion, no manual
  highlight-color toggling), "Start Session" merges the checked imagesets' tags/paths
  (`model.merge_imagesets`) and hands off to `session.start_session(...)`. Category
  buttons are one-shot presets — clicking one replaces the current checkbox selection
  with that category's matches (`model.imagesets_matching_category`); they carry no
  persistent selection state of their own.
- `croquis/session.py` — `SessionApp`: drives the actual timed/manual image sequence
  (`tick()` reschedules itself via `tk.after(1000, ...)`; `go_to_image(new_index)` is the
  single state-transition point — it's used both for advancing/going back *and* for
  redrawing the current image on window resize, so it has to distinguish "new image"
  (reset the per-image timer) from "same image, just resized" (keep the timer). `-1`
  (`SessionApp.NOT_SET`) does double duty as both "no timer running" and "before the
  first image" sentinel. Deliberately untouched by the ttk/`sv-ttk` restyle — its
  playback buttons are classic `tk.Button`s with explicit colors from `constants.py`,
  embedded via `canvas.create_window(...)` over the reference image; that's an
  intentional dark overlay aesthetic, not a "form," and explicit `background=`/`fg=`
  kwargs make it immune to theme changes regardless.
- `croquis/model.py` — dataclasses for `config.toml`: `Config`, `Mode`, `ImageSet`,
  `Category`. Deserialization is hand-rolled in `__post_init__` (dict → dataclass), not a
  library; serialization is `save_config`/`load_config` (`dataclasses.asdict()` +
  `toml.dump()`/`toml.loads()`, round-trips cleanly including bools). **`Category` is
  just a tag spec, nothing more** — `config.imageset` always holds the real, raw
  imagesets; `imagesets_matching_category()` and `merge_imagesets()` are pure helpers
  used both by the CLI (resolving a category name passed as the session argument) and
  by `MainMenuApp` (category-button presets, multi-select merge at session start). They
  are never persisted back to `config.toml` — only `save_config` writes to disk.
- `croquis/constants.py` — every layout/color magic number plus `DEFAULT_CONFIG` (the
  TOML template written out on first run).
- `croquis/util.py` — config/timer parsing (`parse_timer`, `parse_bool`), image discovery
  (`images_in_path`, walks folders recursively), `resource_path()` (PyInstaller `_MEIPASS`
  vs dev-mode path resolution — needed for `icon.ico`).
- `croquis/error_modal.py` — any uncaught exception from `start()` in `main.py` is caught
  and shown in a separate fatal-error Tk window (`show_error_modal`), then exits. It
  builds its own standalone `Tk()` (not a `Toplevel` off the main root — it can fire
  before that root exists), so it calls `theme.apply_theme()` itself rather than
  inheriting it. If a change can throw during startup/event handlers, know that it
  surfaces here rather than a traceback in a console.
- `croquis/config_editor.py` — `open_options_editor`/`open_imageset_editor`, opened from
  a native `tk.Menu` bar set up in `main.py` (Options.../Configure Images...). Each opens
  a modal `Toplevel` of `ttk` widgets (`ttk.Treeview(show="tree")` stands in for the
  4 name/path lists — `ttk` has no themed `Listbox` — see the iid gotcha below) that
  works on `copy.deepcopy(config)` so Cancel discards cleanly; on Save it validates
  inline (an in-window error `ttk.Label`, never `show_error_modal` — that calls
  `sys.exit`, which would kill the app over a typo), calls `save_config`, then
  `model.replace_config_fields(config, working)` to commit the validated copy into the
  live `Config` object `main.py` already holds by reference, then an `on_saved` callback
  that re-enters `select_state("main_menu")` to redraw. **`Treeview` insert with a
  duplicate `iid` raises `TclError`, it does not silently coexist** (unlike `Listbox`,
  which just adds a visual duplicate row) — this matters specifically for the
  imageset-folder-paths list, since `ImageSet.paths` has no uniqueness constraint and a
  user can click "Add folder..." on the same folder twice; that list uses a positional
  synthetic iid (`str(index)`, regenerated on every refresh) rather than the path string
  itself, for exactly this reason.
- `croquis/theme.py` — `apply_theme(tk)`: one-line wrapper around
  `sv_ttk.set_theme(darkdetect.theme(), root=tk)`. Must be called once per `Tk()` root
  that contains `ttk` widgets (themes are per-root, not process-global) — currently
  called from `main.py` and `error_modal.py`.

**Codebase convention:** files use `from tkinter import *` / `from croquis.x import *`
throughout (Tk constants like `FLAT`, `W`, `NW` are used unqualified). This is intentional
existing style, not an oversight — match it rather than switching to qualified imports in
files that already use the wildcard style. **Exception: `config_editor.py` and
`error_modal.py` import explicit names instead of `from tkinter import *`.** This is
deliberate, not an inconsistency to "fix" — both files use `ttk` widgets exclusively
(`ttk.Button`, `ttk.Label`, etc.), and classic `tkinter` defines widgets of the *same
names* (`Button`, `Label`, ...) that render unthemed. A wildcard `tkinter` import in
these files would let a typo'd unqualified `Button(...)` silently compile and run as a
plain, un-themed widget instead of raising `NameError` — the explicit import list is a
guard against that, not a style preference. `main_menu.py` mixes `ttk` widgets with
`from tkinter import *` for the constants (`W`, `BOTH`, `NSEW`, ...) but is careful to
always qualify widget classes as `ttk.X`; if extending it, keep that qualification
discipline rather than copying the wildcard-only style from `session.py`.

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
