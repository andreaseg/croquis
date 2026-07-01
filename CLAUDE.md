# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Croquis is a Tkinter desktop app for timed figure-drawing practice: it cycles through
reference images from user-configured folders on a timer, full-screen, packaged as a
single Windows `.exe` via PyInstaller. See `README.md` for user-facing usage and
`config.toml` format.

The app is translatable (English/Japanese today) via a small hand-rolled catalog system
in `croquis/i18n.py`/`croquis/locales/` — see the dedicated note below. Every
user-facing string across `main_menu.py`, `config_editor.py`, and `session.py` routes
through `translate(key, language)`.

The menu/editor UI uses `ttk` (themed widgets) skinned by `sv-ttk`, applied once per
`Tk()` root via `croquis/theme.py:apply_theme(tk, theme)`. `theme` is `Config.theme`
(`"auto"`/`"light"`/`"dark"`, default `"auto"`) — `apply_theme` resolves `"light"`/
`"dark"` directly and falls back to OS auto-detection (`darkdetect`) for anything else
(`"auto"` or a garbage hand-edited value), so there's no separate validation needed for
`Config.theme`. `main.py` passes `config.theme` in; `error_modal.py` deliberately calls
`apply_theme(tk)` with no override (defaults to `"auto"`) since it can fire before
`config` is loaded (e.g. a malformed `config.toml`), so it can't assume a `Config`
object exists. Options → General re-applies the theme live via `apply_theme(self.tk,
self.config.theme)` in `MainMenuApp._on_config_saved()` right after a save, since
`sv_ttk.set_theme()` can be called again on the same root at any time — no restart
needed. The session screen (`session.py`) is intentionally NOT themed this way — see
its note below.

## Commands

```sh
poetry install --with dev   # install deps (Python 3.13–3.14, see pyproject.toml)
poetry run croquis          # run from source (== make run)
poetry run pytest           # run tests
poetry run pytest croquis/tests/test_util.py::test_parse_timer  # single test
poetry run pytest croquis/tests/test_model.py  # config/imageset/category helpers
poetry run pytest croquis/tests/test_monochrome.py  # greyscale/sepia transform
poetry run pytest croquis/tests/test_i18n.py  # translate() + ja catalog consistency
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
  the window). Holds the full `Config` object (not just the imageset/mode/category
  sub-dicts) plus the config path, because it also owns the Options/Configure Images
  menu bar (see `config_editor.py` below for why that lives here and not in `main.py`).
  Check one or more imagesets (`ttk.Checkbutton`s, multi-select) + pick a mode
  (`ttk.Radiobutton`s bound to one `StringVar` — native mutual-exclusion, no manual
  highlight-color toggling), "Start Session" merges the checked imagesets' tags/paths
  (`model.merge_imagesets`) and hands off to `session.start_session(...)`, passing
  `self.config.image_locations` through for path resolution. A `ttk.Checkbutton`
  ("Monochrome") above the Start Session button is a plain runtime `BooleanVar` on
  `MainMenuApp`, seeded from `Config.monochrome_default` (`__init__`'s
  `BooleanVar(value=config.monochrome_default)`) but not itself written back to
  `config.toml` when toggled — only its *starting* checked state is persisted
  (`Config.monochrome_default`, editable via Options → General); the live
  on/off state during a given main-menu session is read once when a session starts
  and passed straight through to `session.start_session(..., monochrome=...)`. Category
  buttons are one-shot presets — clicking one replaces the current checkbox selection
  with that category's matches (`model.imagesets_matching_category`); they carry no
  persistent selection state of their own. `_on_config_saved()` (the `on_saved`
  callback passed to both `open_options_editor`/`open_imageset_editor`) **must** call
  `self.delete_children()` before invoking `self.main_menu_callback("main_menu")` — this
  was missing once (a real shipped bug: saving Options/Configure Images left the old
  `menu_frame`/`menu_bar` alive while a brand-new `MainMenuApp` built a second one on
  top, visibly duplicating the main menu). `start_session()` already followed this
  tear-down-before-handoff rule; `_on_config_saved()` didn't, which is why the bug was
  scoped to the config-editor save path specifically. It also re-applies the theme live
  (`apply_theme(self.tk, self.config.theme)`) before tearing down, since `self.config`
  already reflects the saved values at that point (`replace_config_fields` ran inside
  `config_editor.py`'s `on_save()` before this callback fires).
- `croquis/session.py` — `SessionApp`: drives the actual timed/manual image sequence
  (`tick()` reschedules itself via `tk.after(1000, ...)`, storing the handle in
  `self._tick_after_id` so `delete_children()` can `after_cancel()` it — **this was a
  real shipped bug**: the handle used to be discarded, so quitting a timed session
  left one already-scheduled tick pending (ticks reschedule *before* the user can
  react, so this was true almost any time a session was quit); up to ~1s later it
  could fire after a brand-new session had already started on the same shared
  `Canvas`, and if it happened to land exactly when the old session's per-image timer
  crossed zero, it called `go_to_image()`/`load_image()` on the torn-down instance —
  which creates a fresh, entirely untracked `canvas.create_image(...)` that nothing
  ever cleans up (its "stale" widget IDs on `itemconfigure` are silent no-ops, *not*
  errors, confirmed by testing — only `create_*` calls actually leak). Symptom: a
  stray "ghost" image stuck on screen in a later session, since the new session has
  no way of knowing the orphaned item exists. `tick()` also has a belt-and-suspenders
  `if self.has_ended: return` guard at its top, matching `_apply_zen_visibility()`'s
  existing guard, in case any future path leaves a tick in flight some other way.
  `go_to_image(new_index)` is the single state-transition point — it's used both for
  advancing/going back *and* for
  redrawing the current image on window resize, so it has to distinguish "new image"
  (reset the per-image timer) from "same image, just resized" (keep the timer). `-1`
  (`SessionApp.NOT_SET`) does double duty as both "no timer running" and "before the
  first image" sentinel. Deliberately untouched by the ttk/`sv-ttk` restyle — its
  playback buttons are classic `tk.Button`s with explicit colors from `constants.py`,
  embedded via `canvas.create_window(...)` over the reference image; that's an
  intentional dark overlay aesthetic, not a "form," and explicit `background=`/`fg=`
  kwargs make it immune to theme changes regardless. `load_image()` applies
  `monochrome.apply_monochrome()` (if `self.monochrome`) in the same branch as the
  mirror transform, i.e. once per image *load*, cached on `self._image_file` — not
  once per resize-redraw, since it's deterministic and resizing reuses the cached,
  already-transformed image.
  **Pause is a menu, not a toggle button:** there's no separate ⏸/▶ pair anymore —
  Escape (or `keybindings['menu']`), Space, or the ☰ burger button (top-left, corner-
  anchored via `canvas.create_window(BUTTON_EDGE_OFFSET, BUTTON_EDGE_OFFSET,
  anchor="nw", ...)`, so it never needs a `redraw()` entry unlike the center-anchored
  menu buttons) all call `toggle_menu()`. `is_paused` is *repurposed* as "is the menu
  open," not a second flag alongside it — `tick()` already gates the countdown on
  `is_paused`, so opening the menu freezes the timer for free. The menu overlay
  (`resume_button_widget`, `exclude_button_widget`, `extend_timer_button_widget`,
  `quit_button_widget`) follows the "always create the widget, toggle
  `state=NORMAL`/`HIDDEN`" pattern established by `main_menu.py` — deliberately not
  conditional creation, since `canvas.coords(None, ...)` raises `TclError` while
  `canvas.delete(None)` is a silent no-op (an asymmetry that makes `None`-guarded
  widgets a real footgun in `redraw()`). `quit_button_widget` is a separate widget from
  `restart_widget` ("Back to menu," shown at natural end-of-sequence) rather than one
  button serving both triggers, to avoid the two visibility conditions fighting over
  it. `extend_timer_button_widget` is only shown in `open_menu()` when `not
  self.is_manual` (`self.timer` doesn't exist as a countdown in manual mode). Exclude
  is wired through a caller-supplied `on_exclude_image(path)` callback (default no-op)
  so `SessionApp` stays decoupled from `Config`/persistence — same shape as the
  existing `main_menu_callback`; the actual persistence (append to
  `Config.excluded_images`, `save_config`) lives in `main_menu.py`/`main.py`. Prev/next
  buttons and their `<Left>`/`<Right>` bindings are now conditional on `manual` (passed
  into `__init__` and stored as `self.is_manual` immediately, since binding setup
  happens inside `__init__` and needs it before `start_session()` could otherwise set
  it) — timed sessions advance on their own, so those controls are hidden/unbound
  rather than just inert. Keybindings for `menu`/`prev`/`next` come from
  `Config.keybindings` (falls back to `DEFAULT_KEYBINDINGS` if `None`); Space is a
  fixed alias to the same `toggle_menu()` action, not itself rebindable, to keep the
  Options → Keybindings UI to 3 clean rows instead of 4.
  **Zen mode** (`self.zen_mode`, from `Config.zen_mode`) hides the timer/path/progress
  text and the ☰ burger by default, revealing the text overlay only transiently.
  `zen_reveal()` sets a `time.monotonic()` deadline (`_zen_reveal_until`) and schedules
  a one-shot `tk.after(ZEN_REVEAL_SECONDS * 1000, ...)` to hide it again — using
  `time.monotonic()` rather than tracking Tk `after` state directly means the "is it
  currently revealed" check (`_apply_zen_visibility()`) is a pure read with no timer
  bookkeeping beyond the single cancel-and-replace on each new reveal (`after_cancel`
  the previous handle before scheduling a new one, so rapid triggers don't stack
  callbacks). `_zen_final_countdown_active()` is a *second*, independent reason to
  reveal — once `self.timer` drops to/below `util.zen_reveal_threshold(image_duration)`
  (tiered: longer images get a longer heads-up before their timer runs out), the
  countdown becomes visible persistently, not just for the transient window; `tick()`
  calls `_apply_zen_visibility()` every second so this turns on/off live as the
  countdown crosses the threshold. Manual mode never runs `tick()`, but it also has no
  countdown, so `_zen_final_countdown_active()` short-circuits `False` for
  `self.is_manual` — the transient reveal from each `next()`/`prev()`-driven
  `go_to_image()` call is the only mechanism needed there. `_apply_zen_visibility()`
  guards on `self.has_ended`, and `delete_children()` cancels any pending
  `_zen_reveal_after_id` — both defend against the exact class of bug the stale-
  keybinding fix above addressed: a scheduled callback outliving the widgets/session it
  was meant to affect. Per the user's explicit call, prev/next in manual mode are
  **not** gated by Zen mode at all (manual mode's only way to advance shouldn't
  disappear) — only the burger button and the timer/path/progress text are.
- `croquis/monochrome.py` — `apply_monochrome(image)`: perceptual greyscale (Pillow's
  `.convert("L")`, i.e. the same BT.601 weights as `LUMA_WEIGHTS` in `constants.py`)
  toned with a brightness-dependent sepia tint. The tint is built to preserve
  perceptual luminance *by construction*, not by tuning: `SEPIA_REFERENCE_COLOR` is
  normalized by its own BT.601 luminance into per-channel ratios, so blending grey
  toward `ratio * L` at any strength keeps the blended color's luminance at exactly
  `L` (a linear combination of two colors that each have luminance `L` also has
  luminance `L` — this is why the reference color's exact hue doesn't matter, only
  the ratios derived from it do). `MONOCHROME_TINT_STRENGTH` scales with `L` itself
  (`strength = TINT_STRENGTH * L/255`), which is what gives the "neutral shadows, warm
  highlights" look rather than a uniform tint. Bright channels do clip at 255 for very
  light pixels (verified: the R channel starts clipping around `L≈221`, i.e. the top
  ~13% of the range), which breaks exact luminance preservation right at the extreme
  highlights — expected and visually fine (mimics real sepia photos blowing out
  highlights), not a bug to fix.
- `croquis/model.py` — dataclasses for `config.toml`: `Config`, `Mode`, `ImageSet`,
  `Category`. Deserialization is hand-rolled in `__post_init__` (dict → dataclass), not a
  library; serialization is `save_config`/`load_config` (`dataclasses.asdict()` +
  `toml.dump()`/`toml.loads()`, round-trips cleanly including bools). **`Category` is
  just a tag spec, nothing more** — `config.imageset` always holds the real, raw
  imagesets; `imagesets_matching_category()` and `merge_imagesets()` are pure helpers
  used both by the CLI (resolving a category name passed as the session argument) and
  by `MainMenuApp` (category-button presets, multi-select merge at session start). They
  are never persisted back to `config.toml` — only `save_config` writes to disk.
  **Any new `Config` field needs a default** (e.g. `image_locations: list[str] =
  field(default_factory=list)`) — this dataclass is constructed straight from
  `toml.loads()` of whatever's on disk, so a required field with no default breaks
  loading every `config.toml` written before that field existed (this exact class of
  bug shipped once already — `category` — see git history / `DEFAULT_CONFIG` below).
  `keybindings: dict[str, str]` (default `dict(DEFAULT_KEYBINDINGS)`) and
  `excluded_images: list[str]` (default `[]`) follow the same rule; neither needs
  `__post_init__` handling since both are already TOML-native types that
  `asdict()`/`toml.dump()` round-trip as-is. `zen_mode: bool = False` is Config's first
  plain top-level bool field — distinct from `Mode.default`/`Mode.manual`, which are
  stored as quoted strings and parsed via `parse_bool()` in `Mode.__post_init__`; TOML
  has a native bool type too, so `zen_mode` round-trips as a bare `true`/`false`
  literal with no parsing step needed, same reasoning as the list/dict fields above.
  `theme: str = "auto"` follows the same no-`__post_init__`-needed pattern; it's
  deliberately unvalidated here (any string round-trips fine) — `theme.apply_theme()`
  is the one place that interprets it, and it already treats anything other than
  `"light"`/`"dark"` as "auto-detect," so a garbage hand-edited value degrades
  gracefully instead of needing a dataclass-level check. `language: str = "en"`
  follows the same pattern — unvalidated at the dataclass level (`i18n.translate()`
  already degrades gracefully for an unknown language, falling back to the English
  key). `Mode.get_label(language="en")` translates its "Manual"/"Timed"/"Click to go
  to next image" return values but leaves the raw timer expression (e.g. "4×30s
  3×1m") and `format_time()`'s output untranslated — those echo the user's own
  `[mode.X].timers` config syntax back at them, and translating the `s`/`m` unit
  letters would create a mismatch with what they'd actually type in `config.toml`.
  `monochrome_default: bool = False` follows the plain-bool pattern established by
  `zen_mode` — it only seeds `MainMenuApp.monochrome_var`'s initial checked state (see
  `main_menu.py` above), it isn't itself mutated when the checkbox is toggled during a
  session.
- `croquis/constants.py` — every layout/color magic number plus `DEFAULT_CONFIG` (the
  TOML template written out on first run). Keep `DEFAULT_CONFIG` in sync with `Config`'s
  fields — a first run with no `config.toml` constructs `Config(**toml.loads(DEFAULT_CONFIG))`
  directly, so a field this template doesn't demonstrate is a field new users never see,
  and a required field it's missing entirely is a crash on first launch.
  `DEFAULT_KEYBINDINGS = {"menu": "Escape", "prev": "Left", "next": "Right"}` is the
  single source of truth for both `Config.keybindings`'s default and the `[keybindings]`
  table in `DEFAULT_CONFIG` — keep them matching. The session button colors
  (`BUTTON_BACKGROUND_COLOR`, `PAUSE_BACKGROUND_COLOR`, `BUTTON_TEXT_COLOR`,
  `PAUSE_TEXT_COLOR`) were recolored to match monochrome mode's sepia tint using the
  *same math* as `monochrome.py`, but computed **offline via a throwaway script and
  hardcoded here as plain hex**, not imported live — `monochrome.py` already imports
  `LUMA_WEIGHTS`/`SEPIA_REFERENCE_COLOR` etc. from `constants.py`, so importing
  `monochrome.py` from here would cycle. If retuning these, regenerate them the same
  way (perceptual luminance of the original color → blend toward the sepia reference's
  luminance-normalized ratios at some strength) rather than hand-picking new hex values.
- `croquis/util.py` — config/timer parsing (`parse_timer`, `parse_bool`), image
  discovery (`images_in_path`, walks folders recursively). Path resolution for
  `image_locations`: `resolve_image_path(path, locations)` tries `os.path.join(location,
  path)` for each location and returns the first that `os.path.isdir`s, falling back to
  the raw path; `images_in_path`/`generate_random_image_sequence` always prepend `"."`
  to whatever locations they're given before resolving (so the app's own directory is
  never optional, regardless of config), which is also why old CWD-relative paths never
  needed migrating when this feature was added. `shorten_to_location(path, locations)`
  is the inverse, used by the config editor's "Add folder..." picker so newly-added
  folders get stored relative to whichever location contains them (shortest match wins)
  instead of as a full absolute path — remember `os.path.relpath` raises `ValueError`
  for cross-drive paths on Windows, must be caught. `resource_path()` (PyInstaller
  `_MEIPASS` vs dev-mode path resolution — needed for `icon.ico`) is unrelated to any of
  this, a separate concern for bundled app resources, not user image folders.
  `generate_random_image_sequence` used to crash (`ValueError` from `random.sample`)
  whenever the picked image set had fewer images than the mode's timer-slot count;
  `_sample_with_repeats()` fixes this by repeatedly `random.sample`-ing the *whole*
  pool and concatenating until enough images are collected (a full reshuffle per pass,
  not `random.choices`, which would cluster repeats unevenly) — an empty pool still
  raises, but with a friendly `Exception("No images found...")` caught by the existing
  `show_error_modal`/inline-error paths instead of a raw traceback. Both
  `images_in_path` and `generate_random_image_sequence` take an `excluded:
  Iterable[str] = ()` param (same shape as `locations`) for permanently-skipped images
  (`Config.excluded_images`); matching uses `normalize_path(path) ->
  os.path.normcase(os.path.abspath(path))`, not bare `os.path.abspath`, because
  Windows paths need case-folding too for a reliable comparison.
  `zen_reveal_threshold(image_duration)` is a small pure function backing Zen mode's
  "reveal the countdown when time is short" behavior (see `session.py` below) — kept
  here rather than inline in `session.py` specifically so the tiering logic
  (`ZEN_REVEAL_TIERS`/`ZEN_REVEAL_FALLBACK_SECONDS` in `constants.py`) is unit-testable
  without constructing any Tk widgets.
- `croquis/error_modal.py` — any uncaught exception from `start()` in `main.py` is caught
  and shown in a separate fatal-error Tk window (`show_error_modal`), then exits. It
  builds its own standalone `Tk()` (not a `Toplevel` off the main root — it can fire
  before that root exists), so it calls `theme.apply_theme()` itself rather than
  inheriting it. If a change can throw during startup/event handlers, know that it
  surfaces here rather than a traceback in a console.
- `croquis/config_editor.py` — `open_options_editor`/`open_imageset_editor`, opened from
  a native `tk.Menu` bar. **The menu bar is built in `MainMenuApp.draw_menu()` and torn
  down in `delete_children()`, not in `main.py`** — it used to live in `main.py`
  attached once at startup, which meant Options/Configure Images stayed visible during
  a session; its lifecycle now matches the main menu screen's, since `delete_children()`
  already runs both when returning to the menu and (via `MainMenuApp.start_session()`)
  when a session starts. Each editor opens a modal `Toplevel` of `ttk` widgets
  (`ttk.Treeview(show="tree")` stands in for the list widgets — `ttk` has no themed
  `Listbox` — see the iid gotcha below) that works on `copy.deepcopy(config)` so Cancel
  discards cleanly; on Save it validates inline (an in-window error `ttk.Label`, never
  `show_error_modal` — that calls `sys.exit`, which would kill the app over a typo),
  calls `save_config`, then `model.replace_config_fields(config, working)` to commit the
  validated copy into the live `Config` object, then an `on_saved` callback
  (`MainMenuApp._on_config_saved`) that re-enters `select_state("main_menu")` to redraw.
  **`Treeview` insert with a duplicate `iid` raises `TclError`, it does not silently
  coexist** (unlike `Listbox`, which just adds a visual duplicate row) — this matters
  for any folder list, since paths (`ImageSet.paths`, `Config.image_locations`) have no
  uniqueness constraint and a user can click "Add folder..." on the same folder twice;
  `_build_folder_list()` (shared by the per-imageset paths list and the Image Locations
  tab) uses a positional synthetic iid (`str(index)`, regenerated on every refresh)
  rather than the path string itself, for exactly this reason.
  `open_options_editor` also has a Keybindings tab (`ttk.Notebook`, alongside the
  existing General tab) for `menu`/`prev`/`next`: each row's "Change..." button opens a
  small blocking modal (`Toplevel` + `grab_set()` + `bind("<Key>", ...)` +
  `wait_window()` — the same blocking pattern `simpledialog.askstring` already uses
  elsewhere in this file) that captures the next `event.keysym` and closes itself,
  rejecting bare modifier keysyms (`Shift_L/R`, `Control_L/R`, `Alt_L/R`, `Caps_Lock`,
  `Num_Lock`, `Super_L/R` — syntactically bindable in Tk but never what a user means to
  rebind to) and keys already assigned to a different action, both via the same inline
  `error_var` label the rest of the editor uses (never `show_error_modal`, same
  reasoning as elsewhere in this file).
  The General tab's Zen mode checkbox (`zen_mode_var`), theme selector (`theme_var`),
  and language selector (`language_var`) all sit directly under the window size field,
  outside the per-mode `body`/`form_frame` area — they're top-level `Config` settings
  like `dimensions`, not scoped to an individual mode. `theme_var`/`language_var` are
  both `ttk.OptionMenu`s (same widget type already used for "Default mode:" below
  them, for consistency within this file), but `language_var` stores the *display
  label* ("English"/"日本語" from `LANGUAGE_LABELS`), not the raw code — `on_save()`
  reverse-looks-up the code via `next(code for code, label in LANGUAGE_LABELS.items()
  if label == language_var.get())`. `theme_var` doesn't need this indirection since
  its raw values (`"auto"`/`"light"`/`"dark"`) are already short, unqualified English
  words appropriate to show directly regardless of UI language. **`OPTIONS_WINDOW_SIZE` must be tall enough for the General tab's
  content or the Save/Cancel row at the bottom gets clipped** (a real shipped bug: the
  fixed `640x480` was 3px shorter than the tab's actual required height once the
  Keybindings tab and these two General-tab rows were added, so the buttons were
  offscreen until the user manually resized) — verify with
  `window.winfo_reqheight()` after `update_idletasks()` in a headless script if you add
  more rows here, rather than guessing a new constant.
- `croquis/theme.py` — `apply_theme(tk, theme="auto")`: `theme` is `Config.theme`;
  `"light"`/`"dark"` are used as-is, anything else (including `"auto"` or a bad
  hand-edited value) falls back to `darkdetect.theme()`-based OS detection. Wraps
  `sv_ttk.set_theme(resolved, root=tk)`. Must be called once per `Tk()` root that
  contains `ttk` widgets (themes are per-root, not process-global) — currently called
  from `main.py` (with `config.theme`), `error_modal.py` (no override — see its note
  above for why), and `MainMenuApp._on_config_saved()` (to re-apply live after an
  Options save). `sv_ttk.set_theme()` is safe to call repeatedly on the same root —
  that's how the live re-apply works, no special "already themed" guard needed.
- `croquis/i18n.py` — `translate(key, language="en", **kwargs) -> str`: `key` is the
  **English text itself** (gettext-style), not a synthetic namespaced key, so a
  missing/untranslated key degrades to readable English rather than a raw key string.
  Deliberately named `translate`, not the conventional gettext `_` — `_` is already
  used as a throwaway variable in this exact codebase (`session.py`'s
  `path, _, _ = self.imageset[self.index]`, also `main.py`/`util.py`), and a
  wildcard-imported `_` translate function would be silently shadowed the moment any
  function reassigns `_`, breaking every subsequent `_(...)` call in that scope.
  `language` is passed explicitly by the caller (from `Config.language`), not read
  from global state — keeps `translate()` a pure function, easy to unit test, no
  import-order/global-mutation hazards. Hand-rolled dict catalogs, not `gettext`/
  `.po`/`.mo` — no new dependency, and no `msgfmt` build tool (not present on Windows
  by default) needed to compile anything; `croquis/locales/ja.py` is a plain
  `TRANSLATIONS: dict[str, str]` that PyInstaller bundles automatically like any other
  `.py` module (no `resource_path()`/`--add-data` needed, unlike `icon.ico`).
  **Module-level string constants can't hold translatable text** — `constants.py` used
  to have `RESUME_BUTTON_TEXT`/`EXTEND_TIMER_BUTTON_TEXT`/etc. as plain strings
  computed once at import time; these were removed and replaced with `translate(...)`
  calls made fresh at each widget-creation call site (inside `start_session()`/
  `draw_menu()`, which already run fresh on every screen build/rebuild) — a constant
  can't respond to a runtime language change. `MENU_BUTTON_TEXT = "☰"` stays a
  constant since it's an icon glyph, not translatable text; same reasoning for the
  "⏪"/"⏩" prev/next glyphs in `session.py`. **"Live apply on save" needs zero extra
  plumbing** — Options can only be opened from the main menu (the menu bar is torn
  down when a session starts), so there's no mid-session language-switch case;
  `MainMenuApp._on_config_saved()` already fully tears down and rebuilds `MainMenuApp`
  (see its note above) after *any* Options save, so once a screen's strings route
  through `translate(key, self.config.language)`, a language change takes effect
  immediately after Save the same way theme does. Deliberately left untranslated (not
  an oversight): window titles built from the user's own data (`f"Croquis: {name}"` —
  "Croquis" is the product's proper name), the progress counter (`f"{index+1}/{len}"`
  — pure numeric notation, no linguistic content), `error_modal.py`'s "Fatal error"/
  "Ok" (can fire before `config` loads at all, same reasoning as its theme handling),
  and raw exception message text from `util.py`/`model.py` (e.g. `parse_timer`'s
  `"'{t}' is not a valid time expression"`) — the *surrounding* UI text in
  `config_editor.py`'s `error_var.set(...)` calls is translated
  (`translate("Mode '{name}': {error}", ...)`), but the embedded exception text itself
  stays English, consistent with `error_modal.py` being out of scope.
  `LANGUAGE_LABELS = {"en": "English", "ja": "日本語"}` in `config_editor.py` is
  deliberately **not** run through `translate()` — a language picker conventionally
  names each language in its own script regardless of the currently active UI
  language, so the dropdown always shows "English"/"日本語" no matter which one is
  currently selected.

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

**Testing Tkinter code without a display:** `croquis/tests/` covers pure logic only
(`test_util.py`, `test_model.py`, `test_monochrome.py`, `test_i18n.py`) — no GUI tests
are checked in. `test_i18n.py` includes a consistency check — for every key in
`locales.ja.TRANSLATIONS`, the set of `{placeholder}` names in the English key must
match the set in the Japanese value (via `re.findall(r"\{(\w+)\}", ...)`) — catching a
translator typo (e.g. `{new_key}` vs `{key}`) that would otherwise only surface as a
`KeyError` at runtime, in whichever language exposes it.
When you do need to drive real Tk widgets to verify behavior, construct the actual
`Tk()`/`Canvas`/app objects in a throwaway script (no `mainloop()` needed — call
`tk.update()` after state changes and inspect via `winfo_ismapped()`, `winfo_manager()`,
`.cget(...)`, `.invoke()` on buttons, etc.), which is how the menu/timer bugs above were
confirmed and verified fixed, and how the session pause-menu/keybinding-rebind behavior
was verified (a `CapturingSessionApp` subclass + temporary module-attribute monkeypatch
is one way to get at the `SessionApp` instance, since `start_session()` doesn't return
it).
