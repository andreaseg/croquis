# Croquis

A small desktop app for timed figure-drawing (croquis) practice. Point it at folders of
reference images, define how long each one should be shown, and it cycles through a
randomized session for you — full screen, with a timer, progress counter, and pause/skip
controls.

## Features

- **Timed sessions** — e.g. "4×30s, 3×1m, 2×2m, 2×3m, 1×5m" — images advance automatically.
- **Manual / classroom mode** — no timer, click or press the right arrow to advance.
- **Image sets** — group reference images by folder, tag them (e.g. `male`, `portrait`,
  `hands`), and check as many as you like before starting a session — paths and tags
  from every checked image set are pooled together.
- **Categories** — one-click presets: clicking a category checks every image set whose
  tags match it, so e.g. a "Figure" category can select every image set tagged `figure`
  without checking each one by hand. You can still fine-tune the selection afterward.
- **In-app configuration** — add/edit/remove image sets, categories, modes, and the
  window size from the **Options...** / **Configure Images...** menu, no need to hand-edit
  `config.toml`.
- **Pause, skip back/forward, random mirroring** of images during a session.
- Packaged as a single `croquis.exe` — no Python install required to run it.

## Running it

**Just want to draw?** Grab `croquis.exe` and run it from a folder that contains your
`config.toml` (see below). On first run, if no `config.toml` exists, one is generated for
you with example entries to fill in.

**Running from source:**

```sh
poetry install
poetry run croquis
```

or, from a checkout with `make`:

```sh
make run
```

### Command line

```sh
croquis                          # opens the main menu
croquis "Portrait Male"          # starts that image set immediately, using the default mode
croquis Portrait Classic         # also accepts a category name, with a specific mode
```

## Configuring

The easiest way to add image sets, categories, and modes, or change the window size, is
the in-app editor: open the **Options...** menu for the window size and modes, or
**Configure Images...** for image sets and categories. Changes save straight back to
`config.toml` and apply immediately, no restart needed.

You can still hand-edit `config.toml` directly if you prefer. It lives next to the
executable (or in the repo root when running from source) and is not checked into git —
every artist's image library is different. Example:

```toml
dimensions = "1920x1200"

[mode.Classic]
default = "True"
timers = "4*30s 3*1m 2*2m 2*3m 5m"

[mode.Classroom]
manual = "True"

[imageset."Portrait Male"]
tags = ["portrait", "male"]
paths = [
    "C:/references/portraits/male",
]

[category."Portrait"]
tags = ["portrait"]
```

- **`[mode.<name>]`** — a drawing mode. Either `timers = "<n>*<duration> ..."`
  (`s`econds/`m`inutes, e.g. `"3*30s 2m"`) for a timed session, or `manual = "True"` for a
  click-to-advance session. Mark one mode `default = "True"` to preselect it in the menu.
- **`[imageset.<name>]`** — a named group of reference images: a list of folder `paths`
  (searched recursively) and `tags` describing what's in them. Each one shows up as a
  checkbox in the main menu; check as many as you want before starting a session.
- **`[category.<name>]`** — a one-click preset button in the main menu: clicking it
  checks every `[imageset]` whose tags are a superset of the category's tags. Useful for
  "give me everything tagged `figure`" without checking each image set by hand.

## Building the executable

```sh
make build
```

This runs PyInstaller (via the `build-exe` poetry script) and copies the resulting
`croquis.exe` into the project root.

## Development

```sh
poetry install --with dev
poetry run pytest      # run tests
poetry run ruff format # format
poetry run ruff check  # lint
```
