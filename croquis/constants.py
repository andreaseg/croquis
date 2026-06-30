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

# Grid weights for the main menu's responsive layout, not pixel sizes.
# Columns: [imagesets, mode, start button]
MAIN_MENU_COL_WEIGHTS = [5, 3, 3]
# Rows: [category presets, imagesets/mode/start, description]
MAIN_MENU_ROW_WEIGHTS = [0, 3, 1]

DEFAULT_CONFIG = """
dimensions="1920x1200"

[mode.classic]
default = "True"
timers = "30s 30s 30s 1m 1m 1m 2m 2m 5m 10m"

[mode.classroom]
manual = "True"

[imageset.example1]
paths = [
#    "path-to-image-folder"
]

[imageset.example2]
paths = [
#    "path-to-image-folder"
]
""".strip()
