# Croquis

A small desktop app for timed figure-drawing (croquis) practice. Point it at folders of
reference images, define how long each one should be shown, and it cycles through a
randomized session for you — full screen, with a timer, progress counter, and pause/skip
controls.

## Features

- **Timed sessions** — e.g. "4×30s, 3×1m, 2×2m, 2×3m, 1×5m" — images advance automatically.
- **Manual / classroom mode** — no timer, click or press the right arrow to advance.
- **Image sets** — group reference images by folder, tag them (e.g. `male`, `portrait`,
  `hands`), and mix and match at session start.
- **Categories** — virtual image sets built automatically from tags, so e.g. a "Figure"
  category can pull from every image set tagged `figure` without duplicating paths.
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
croquis "Portrait Male" Classic  # starts that image set with a specific mode
```

## Configuring `config.toml`

`config.toml` lives next to the executable (or in the repo root when running from source)
and is not checked into git — every artist's image library is different. Example:

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
  (searched recursively) and `tags` describing what's in them.
- **`[category.<name>]`** — a virtual image set assembled from every `[imageset]` whose
  tags are a superset of the category's tags. Useful for "give me everything tagged
  `figure`" without re-listing paths.

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
