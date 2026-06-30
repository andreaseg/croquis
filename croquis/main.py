from tkinter import *
import toml
import sys
import os

from croquis.util import *
from croquis.constants import *
from croquis.session import start_session
from croquis.main_menu import start_main_menu
from croquis.error_modal import show_error_modal
from croquis.model import *


def start():
    try:
        _start()
    except Exception as e:
        show_error_modal(e)

def _start():
    if not os.path.exists("config.toml"):
        print("No config.toml found, generating example configuration")
        with open("config.toml", mode="w") as f:
            f.write(DEFAULT_CONFIG)

    with open("config.toml", mode="r") as f:
        config = Config(**toml.loads(f.read()))

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

    print("Virtual imagesets:")
    imageset_copy = config.imageset
    config.imageset = {}
    for category_name, category in config.category.items():
        print(f" {category_name}")
        imagesets = {imageset_name: imageset for imageset_name, imageset in imageset_copy.items() if set(category.tags).issubset(set(imageset.tags)) }
        for imageset in imagesets:
            print(f"  - {imageset}")
        paths = {
            path for imageset in imagesets.values() for path in imageset.paths
        }
        tags = {
            tag for imageset in imagesets.values() for tag in imageset.tags
        }
        if paths:
            config.imageset[category_name] = ImageSet(
                tags,
                paths
            )

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

    def select_state(action: str):
        if action == "session":
            if not picked_session in config.imageset:
                raise Exception(
                    f"Session '{picked_session}' not configured, add [session.{picked_session}] to config.toml"
                )

            session = config.imageset[picked_session]
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
                (width, height),
                callback=select_state,
            )

        else:
            raise Exception(f"Unknow action type '{action}'")

    select_state(action)

    tk.mainloop()


if __name__ == "__main__":
    start()
