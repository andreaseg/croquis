BACKGROUND_COLOR = "#121212"

TEXT_SHADOW_OFFSET = 1
TEXT_SHADOW_COLOR = "#000000"

# PAUSE_TEXT_COLOR and BUTTON_TEXT_COLOR ("the whites") below are sepia-tinted
# using the same luminance-preserving math as monochrome.py (computed offline,
# not a live import - monochrome.py already imports LUMA_WEIGHTS/
# SEPIA_REFERENCE_COLOR from this module, so the reverse import would cycle),
# at a low tint strength (0.12) for a barely-perceptible warm cream rather
# than clinical white. Backgrounds stay their original neutral grey - only
# the whites get the sepia treatment.
PAUSE_BACKGROUND_COLOR = "#706B6B"

PAUSE_FONT = ("arial", 40)
PAUSE_TEXT_COLOR = "#FFFCE9"

PATH_FONT = ("arial", 10)
PATH_TEXT_COLOR = "#A0A0A0"

TIMER_FONT = ("arial", 20)
TIMER_TEXT_COLOR = "#A0A0A0"

PROGRESS_FONT = ("arial", 20)
PROGRESS_TEXT_COLOR = "#A0A0A0"

BUTTON_BACKGROUND_COLOR = "#303030"
BUTTON_TEXT_COLOR = "#FFFCE9"
BUTTON_FONT = ("arial", 12)
# Half the gap between the prev/next buttons' centers. Used to be 60 to leave
# room for a pause/play button between them; now that pause is a separate
# burger button (top-left corner), prev/next sit right next to each other.
BUTTON_POSITION_OFFSET = 35
BUTTON_WIDTH = 6
BUTTON_HEIGHT = 1
BUTTON_EDGE_OFFSET = 8

EXTEND_TIMER_SECONDS = 30

ZEN_REVEAL_SECONDS = 3  # brief overlay duration on new image / unpause / extend timer

# Tiered (duration_threshold, reveal_seconds) pairs, checked in order via
# util.zen_reveal_threshold() - the countdown becomes persistently visible once
# an image's remaining time drops to/below reveal_seconds, longer images get a
# longer heads-up before their timer runs out.
ZEN_REVEAL_TIERS = [(600, 60), (120, 30), (30, 10)]
ZEN_REVEAL_FALLBACK_SECONDS = 5

# Vertical layout of the pause/menu overlay, relative to the screen center.
# MENU_BUTTON_Y_OFFSET is the first button's offset; each subsequent button
# adds MENU_BUTTON_SPACING. The buttons (width=20, height=2, font arial 16)
# render at 66px tall (confirmed via winfo_reqheight()), so spacing must
# clear that to leave any visible gap - this leaves a ~7px gap.
MENU_TITLE_Y_OFFSET = -150
MENU_BUTTON_Y_OFFSET = -60
MENU_BUTTON_SPACING = 73

# MENU_BUTTON_TEXT is an icon glyph, not translatable text, so it stays a
# plain constant. The other button-label strings that used to live here
# (RESUME_BUTTON_TEXT, EXCLUDE_BUTTON_TEXT, EXTEND_TIMER_BUTTON_TEXT,
# QUIT_BUTTON_TEXT, MAIN_MENU_START_BUTTON_TEXT,
# MAIN_MENU_MONOCHROME_TOGGLE_TEXT) moved to translate(...) calls at their
# widget-creation call sites - a module-level constant is computed once at
# import time and can't respond to a runtime language change.
MENU_BUTTON_TEXT = "☰"

# Rebindable session keyboard shortcuts. Space is always also bound to "menu"
# as a fixed, non-rebindable alias - see session.py.
DEFAULT_KEYBINDINGS = {"menu": "Escape", "prev": "Left", "next": "Right"}

# ITU-R BT.601 perceptual luma weights - matches Pillow's own "L" (greyscale)
# conversion, used both directly and as the basis for the sepia toning below.
LUMA_WEIGHTS = (0.299, 0.587, 0.114)

# A reference "sepia" brown. Only its ratios (relative to its own perceptual
# luminance) matter - see monochrome.py - so this can be any warm brown that
# looks right, the math guarantees the toning preserves perceptual brightness
# regardless of which reference color is picked here.
SEPIA_REFERENCE_COLOR = (112, 66, 20)

# How strongly the sepia hue shows at full brightness (0 = pure greyscale,
# 1 = fully saturated sepia at white). Kept low for a "slight" tint - shadows
# stay neutral, only highlights pick up warmth, like graphite on paper.
MONOCHROME_TINT_STRENGTH = 0.35

# Grid weights for the main menu's responsive layout, not pixel sizes.
# Columns: [imagesets, mode, start button]
MAIN_MENU_COL_WEIGHTS = [5, 3, 3]
# Rows: [category presets, imagesets/mode/start, description]
MAIN_MENU_ROW_WEIGHTS = [0, 3, 1]

DEFAULT_CONFIG = """
dimensions="1920x1200"
image_locations = ["images"]
excluded_images = []
zen_mode = false
theme = "auto"
language = "en"
monochrome_default = false

[keybindings]
menu = "Escape"
prev = "Left"
next = "Right"

[mode.classic]
default = "True"
timers = "30s 30s 30s 1m 1m 1m 2m 2m 5m 10m"

[mode.classroom]
manual = "True"

[imageset.example1]
tags = ["example"]
paths = [
#    "path-to-image-folder"
]

[imageset.example2]
tags = ["example"]
paths = [
#    "path-to-image-folder"
]

[category.example]
tags = ["example"]
""".strip()
