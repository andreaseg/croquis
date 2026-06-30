from typing import Callable
from tkinter import *
import random

from croquis.util import *
from croquis.constants import *
from croquis.session import start_session
from croquis.model import *
from croquis.error_modal import show_error_modal


class MainMenuApp:
    def __init__(
        self,
        tk: Tk,
        canvas: Canvas,
        imagesets: dict[str, ImageSet],
        modes: dict[str, Mode],
        geometry: tuple[int, int],
        main_menu_callback: Callable[[str], None],
    ):
        self.tk: Tk = tk
        self.canvas: Canvas = canvas
        self.imagesets: dict[str, ImageSet] = imagesets
        self.modes: dict[str, Mode] = modes
        self.picked_imageset: str | None = None
        self.picked_mode: str | None = None
        self.menu_widget: int | None = None
        self.image_resize = None

        self.main_menu_callback = main_menu_callback

        self.imageset_buttons: dict[str, Button] = {}
        self.mode_buttons: dict[str, Button] = {}
        self.imageset_path: dict[str, LabelFrame] = {}
        self.mode_description: dict[str, LabelFrame] = {}

        self.width, self.height = geometry

        tk.title("Croquis")

        tk.bind("<ButtonRelease-1>", self.left_click)
        tk.bind("<Configure>", lambda e: self.configure(e))

    def delete_children(self):
        self.canvas.delete(self.menu_widget)

    def select_imageset(self, name: str):
        print("imageset", name)
        self.picked_imageset = name
        for imagesetname, button_widget in self.imageset_buttons.items():
            if imagesetname == name:
                background = SELECTED_OPTION_BUTTON_COLOR
            else:
                background = UNSELECTED_OPTION_BUTTON_COLOR

            button_widget.config(bg=background)

        for imagesetname, path_widgets in self.imageset_path.items():
            if imagesetname == name:
                path_widgets.pack()
            else:
                path_widgets.pack_forget()

    def select_mode(self, name: str):
        print("mode", name)
        self.picked_mode = name

        for modename, mode_widget in self.mode_buttons.items():
            if modename == name:
                background = SELECTED_OPTION_BUTTON_COLOR
            else:
                background = UNSELECTED_OPTION_BUTTON_COLOR

            mode_widget.config(bg=background)

        for modename, mode_desc_widget in self.mode_description.items():
            if modename == name:
                mode_desc_widget.pack()
            else:
                mode_desc_widget.pack_forget()

    def draw_menu(self):
        menu_frame = Frame(
            self.tk, background=BACKGROUND_COLOR, width=1500, height=1200
        )
        menu_frame.pack(fill=BOTH, expand=True)
        self.menu_widget = self.canvas.create_window(
            12,
            12,
            anchor="nw",
            window=menu_frame,
            width=self.width - 12,
            height=self.height - 12,
        )

        debug_frames = False

        imageset_buttons_frame = Frame(
            menu_frame,
            width=MAIN_MENU_TABLE_COLS[0],
            height=MAIN_MENU_TABLE_ROWS[0],
            background="green" if debug_frames else BACKGROUND_COLOR,
            border=0,
        )
        imageset_buttons_frame.grid_propagate(False)
        imageset_buttons_frame.grid(row=0, column=0, sticky=NW)

        mode_buttons_frame = Frame(
            menu_frame,
            width=MAIN_MENU_TABLE_COLS[1],
            height=MAIN_MENU_TABLE_ROWS[0],
            background="red" if debug_frames else BACKGROUND_COLOR,
            border=0,
        )
        mode_buttons_frame.grid_propagate(False)
        mode_buttons_frame.grid(row=0, column=1, sticky=NW)

        imageset_description_frame = Frame(
            menu_frame,
            width=MAIN_MENU_TABLE_COLS[0],
            height=MAIN_MENU_TABLE_ROWS[1],
            background="blue" if debug_frames else BACKGROUND_COLOR,
            border=0,
        )
        imageset_description_frame.grid_propagate(False)
        imageset_description_frame.grid(row=1, column=0, sticky=NW)

        mode_description_frame = Frame(
            menu_frame,
            width=MAIN_MENU_TABLE_COLS[1] + MAIN_MENU_TABLE_COLS[2],
            height=MAIN_MENU_TABLE_ROWS[1],
            background="yellow" if debug_frames else BACKGROUND_COLOR,
            border=0,
        )
        mode_description_frame.grid_propagate(False)
        mode_description_frame.grid(row=1, column=1, columnspan=2, sticky=NW)

        start_button_frame = Frame(
            menu_frame,
            width=MAIN_MENU_TABLE_COLS[2],
            height=MAIN_MENU_TABLE_ROWS[0],
            background="pink" if debug_frames else BACKGROUND_COLOR,
            border=0,
        )
        start_button_frame.grid_propagate(False)
        start_button_frame.grid(row=0, column=2, sticky=NW)

        for imageset_idx, (imagesetname, imageset) in enumerate(self.imagesets.items()):
            btn = Button(
                imageset_buttons_frame,
                text=imagesetname,
                command=lambda x=imagesetname: self.select_imageset(x),
                width=MAIN_MENU_IMAGESET_BUTTON_WIDTH,
                height=MAIN_MENU_IMAGESET_BUTTON_HEIGH,
                relief=FLAT,
                font=MAIN_MENU_IMAGESET_BUTTON_FONT,
            )
            self.imageset_buttons[imagesetname] = btn
            btn.grid(row=imageset_idx, column=0, sticky=W)

            text_frame = LabelFrame(
                imageset_description_frame,
                width=MAIN_MENU_TABLE_COLS[0] - 12,
                height=MAIN_MENU_TABLE_ROWS[1],
                background=BACKGROUND_COLOR,
                border=0,
            )
            text_frame.grid_propagate(False)  # Disables resize from grid children
            text_frame.grid(row=imageset_idx, column=0, sticky=W)
            text_frame.pack_forget()
            self.imageset_path[imagesetname] = text_frame

            Label(
                text_frame,
                font=("arial", 12, "bold"),
                text=", ".join(sort_tags(imageset.tags)),
                fg="#FFFFFF",
                background=BACKGROUND_COLOR,
            ).grid(row=0, column=0, sticky=W)

            for path_idx, path in enumerate(imageset.paths):
                Label(
                    text_frame,
                    font="arial",
                    text=path,
                    fg="#FFFFFF",
                    background=BACKGROUND_COLOR,
                ).grid(row=path_idx + 1, column=0, sticky=W)

        for mode_idx, (modename, mode) in enumerate(self.modes.items()):
            btn = Button(
                mode_buttons_frame,
                text=modename,
                command=lambda x=modename: self.select_mode(x),
                width=MAIN_MENU_MODE_BUTTON_WIDTH,
                height=MAIN_MENU_MODE_BUTTON_HEIGH,
                relief=FLAT,
                font=MAIN_MENU_MODET_BUTTON_FONT,
            )
            self.mode_buttons[modename] = btn
            btn.grid(row=mode_idx, column=0, sticky=W)

            label_header, label_body, label_time = mode.get_label()
            text_frame = LabelFrame(
                mode_description_frame,
                width=MAIN_MENU_TABLE_COLS[1] + MAIN_MENU_TABLE_COLS[2],
                height=MAIN_MENU_TABLE_ROWS[1],
                background=BACKGROUND_COLOR,
                border=0,
            )
            text_frame.grid_propagate(False)  # Disables resize from grid children
            text_frame.pack_forget()
            self.mode_description[modename] = text_frame

            Label(
                text_frame,
                font=("arial", 12, "bold"),
                text=label_header,
                fg="#FFFFFF",
                background=BACKGROUND_COLOR,
            ).grid(row=0, column=0, sticky=W)
            Label(
                text_frame,
                font="arial",
                text=label_body,
                # wraplength=20,
                fg="#FFFFFF",
                background=BACKGROUND_COLOR,
            ).grid(row=1, column=0, sticky=W)
            Label(
                text_frame,
                font="arial",
                text="Total: " + label_time,
                fg="#FFFFFF",
                background=BACKGROUND_COLOR,
            ).grid(row=2, column=0, sticky=W)

        btn = Button(
            start_button_frame,
            text=MAIN_MENU_START_BUTTON_TEXT,
            command=lambda: self.start_session(self.picked_imageset, self.picked_mode),
            width=MAIN_MENU_START_BUTTON_WIDTH,
            height=MAIN_MENU_START_BUTTON_HEIGHT,
            relief=FLAT,
            font=MAIN_MENU_START_BUTTON_FONT,
        )
        # btn = RoundedButton(
        #    start_button_frame,
        #    text=MAIN_MENU_START_BUTTON_TEXT,
        #    command=lambda: self.start_session(self.picked_imageset, self.picked_mode),
        #    width=200,
        #    height=40,
        #    font=MAIN_MENU_START_BUTTON_FONT,
        #   bg=BACKGROUND_COLOR,
        #    color="#00FF00",
        #    border_color="#0000FF",
        #    border=2,
        #    cornerradius=16,
        #    padding=0
        # )
        # btn.grid(row=0, column=0, sticky=W)
        btn.pack()
        self.start_widget = id

    def left_click(self, event):
        self.image_resize = event

    def configure(self, event):
        width = self.tk.winfo_width()
        height = self.tk.winfo_height()

        if (
            ((self.width, self.height) != (width, height))
            and width > 256
            and height > 256
        ):
            print(f"Resize to {width}x{height}")
            self.width = width
            self.height = height
            # TODO self.draw_menu()

    def start_session(self, picked_imageset: str | None, picked_mode: str | None):
        try:
            if (
                picked_imageset
                and picked_mode
                and self.imagesets[picked_imageset].paths
            ):
                self.delete_children()
                start_session(
                    self.tk,
                    self.canvas,
                    f"{picked_imageset} - {picked_mode}",
                    self.imagesets[picked_imageset],
                    self.modes[picked_mode],
                    (self.width, self.height),
                    self.main_menu_callback,
                )
        except Exception as e:
            show_error_modal(e)


def start_main_menu(
    tk: Tk,
    canvas: Canvas,
    imagesets: dict[str, ImageSet],
    modes: dict[str, Mode],
    dimensions: tuple[int, int],
    callback: Callable[[str], None],
):
    print("MAIN MENU")

    app = MainMenuApp(tk, canvas, imagesets, modes, dimensions, callback)
    app.draw_menu()
    for modename, mode in modes.items():
        if mode.default:
            app.select_mode(modename)
        break

    app.select_imageset(random.choice(list(imagesets.keys())))
