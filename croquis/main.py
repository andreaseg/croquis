from tkinter import *
import sys
import os

from croquis.util import *
from croquis.constants import *
from croquis.session import start_session
from croquis.main_menu import start_main_menu
from croquis.error_modal import show_error_modal
from croquis.model import *
from croquis.config_editor import open_options_editor, open_imageset_editor

CONFIG_PATH = "config.toml"


def start():
    try:
        _start()
    except Exception as e:
        show_error_modal(e)

def _start():
    if not os.path.exists(CONFIG_PATH):
        print("No config.toml found, generating example configuration")
        with open(CONFIG_PATH, mode="w") as f:
            f.write(DEFAULT_CONFIG)

    config = load_config(CONFIG_PATH)

    print("Modes:")
    for mode_name, mode in config.mode.items():
        print(f" {mode_name}:")
        print(f"  - Default: {mode.default}")
        print(f"  - Timers: {mode.timers}")

    print("Imagests:")
    for session_name, session in config.imageset.items():
        print(f" {session_name}:")
        print(f"  - Tags: [{', '.join(session.tags)}]")
        print(f"  - Paths:")
        for path in session.paths:
            print(f"     - {path}")

    print("All tags:")
    for tag in config.tags():
        print(f"  - {tag}")

    if len(sys.argv) == 2:
        _, picked_session = sys.argv
        picked_mode = [
            mode_name for (mode_name, mode) in config.mode.items() if mode.default
        ][0]
        action = "session"
    elif len(sys.argv) == 3:
        _, picked_session, picked_mode = sys.argv
        action = "session"
    else:
        action = "main_menu"

    tk = Tk()
    tk.iconbitmap(resource_path("icon.ico"))
    tk.geometry(config.dimensions)

    width, height = [int(s) for s in config.dimensions.split("x")]

    canvas = Canvas(tk, width=width, height=height, background=BACKGROUND_COLOR)
    canvas.pack(fill="both", expand=True)

    current_screen = [None]

    def select_state(action: str):
        current_screen[0] = action

        if action == "session":
            if picked_session in config.imageset:
                session = config.imageset[picked_session]
            elif picked_session in config.category:
                matches = imagesets_matching_category(
                    config.imageset, config.category[picked_session]
                )
                session = merge_imagesets(matches.values())
            else:
                raise Exception(
                    f"'{picked_session}' not configured, add [imageset.{picked_session}] or [category.{picked_session}] to config.toml"
                )

            mode = config.mode[picked_mode]
            paths = session.paths

            print(f"Session: {picked_session}")
            print(f"Mode: {picked_mode}")
            print(f"Timers: {mode.timers}")

            if not paths:
                raise Exception(
                    f"No paths specified, add paths to session in config.toml"
                )

            print("Picked from bundles:")
            for path in paths:
                print(f" - {path}")
            start_session(
                tk,
                canvas,
                f"{picked_session} - {picked_mode}",
                session,
                mode,
                (width, height),
                select_state,
            )

        elif action == "main_menu":
            start_main_menu(
                tk,
                canvas,
                config.imageset,
                config.mode,
                config.category,
                (width, height),
                callback=select_state,
            )

        else:
            raise Exception(f"Unknow action type '{action}'")

    def on_config_saved():
        if current_screen[0] == "main_menu":
            select_state("main_menu")

    menu_bar = Menu(tk)
    menu_bar.add_command(
        label="Options...",
        command=lambda: open_options_editor(tk, config, CONFIG_PATH, on_config_saved),
    )
    menu_bar.add_command(
        label="Configure Images...",
        command=lambda: open_imageset_editor(tk, config, CONFIG_PATH, on_config_saved),
    )
    tk.config(menu=menu_bar)

    select_state(action)

    tk.mainloop()


if __name__ == "__main__":
    start()
