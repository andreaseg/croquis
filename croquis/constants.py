BACKGROUND_COLOR = "#121212"

TEXT_SHADOW_OFFSET = 1
TEXT_SHADOW_COLOR = "#000000"

PAUSE_BACKGROUND_COLOR = "#706B6B"

PAUSE_FONT = ("arial", 40)
PAUSE_TEXT_COLOR = "#FFFFFF"

PATH_FONT = ("arial", 10)
PATH_TEXT_COLOR = "#A0A0A0"

TIMER_FONT = ("arial", 20)
TIMER_TEXT_COLOR = "#A0A0A0"

PROGRESS_FONT = ("arial", 20)
PROGRESS_TEXT_COLOR = "#A0A0A0"

BUTTON_BACKGROUND_COLOR = "#303030"
BUTTON_TEXT_COLOR = "#FFFFFF"
BUTTON_FONT = ("arial", 12)
BUTTON_POSITION_OFFSET = 60
BUTTON_WIDTH = 6
BUTTON_HEIGHT = 1
BUTTON_EDGE_OFFSET = 8

MAIN_MENU_START_BUTTON_TEXT = "Start Session"
MAIN_MENU_MONOCHROME_TOGGLE_TEXT = "Monochrome"

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
