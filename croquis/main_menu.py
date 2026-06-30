from typing import Callable, Iterable
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

        self.main_menu_callback = main_menu_callback

        self.imageset_buttons: dict[str, Button] = {}
        self.mode_buttons: dict[str, Button] = {}

        self.width, self.height = geometry

        tk.title("Croquis")
        tk.bind("<Configure>", lambda e: self.configure(e))

    def delete_children(self):
        self.canvas.delete(self.menu_widget)

    def select_imageset(self, name: str):
        print("imageset", name)
        self.picked_imageset = name
        self._highlight(self.imageset_buttons, name)

        imageset = self.imagesets[name]
        self.imageset_tags_label.config(text=", ".join(sort_tags(imageset.tags)))
        self.imageset_paths_label.config(text="\n".join(imageset.paths))

    def select_mode(self, name: str):
        print("mode", name)
        self.picked_mode = name
        self._highlight(self.mode_buttons, name)

        header, body, total_time = self.modes[name].get_label()
        self.mode_header_label.config(text=header)
        self.mode_body_label.config(text=body)
        self.mode_total_label.config(text=f"Total: {total_time}")

    @staticmethod
    def _highlight(buttons: dict[str, Button], selected: str):
        for name, button in buttons.items():
            background = (
                SELECTED_OPTION_BUTTON_COLOR
                if name == selected
                else UNSELECTED_OPTION_BUTTON_COLOR
            )
            button.config(bg=background)

    @staticmethod
    def _build_button_column(
        parent: Frame,
        names: Iterable[str],
        width: int,
        height: int,
        font,
        on_select: Callable[[str], None],
    ) -> dict[str, Button]:
        buttons = {}
        for idx, name in enumerate(names):
            btn = Button(
                parent,
                text=name,
                command=lambda x=name: on_select(x),
                width=width,
                height=height,
                relief=FLAT,
                font=font,
            )
            btn.grid(row=idx, column=0, sticky=W)
            buttons[name] = btn
        return buttons

    def draw_menu(self):
        menu_frame = Frame(self.tk, background=BACKGROUND_COLOR)
        menu_frame.pack(fill=BOTH, expand=True)
        self.menu_widget = self.canvas.create_window(
            12,
            12,
            anchor="nw",
            window=menu_frame,
            width=self.width - 12,
            height=self.height - 12,
        )

        imageset_buttons_frame = self._table_cell(
            menu_frame, MAIN_MENU_TABLE_COLS[0], MAIN_MENU_TABLE_ROWS[0], row=0, column=0
        )
        mode_buttons_frame = self._table_cell(
            menu_frame, MAIN_MENU_TABLE_COLS[1], MAIN_MENU_TABLE_ROWS[0], row=0, column=1
        )
        start_button_frame = self._table_cell(
            menu_frame, MAIN_MENU_TABLE_COLS[2], MAIN_MENU_TABLE_ROWS[0], row=0, column=2
        )
        imageset_description_frame = self._table_cell(
            menu_frame, MAIN_MENU_TABLE_COLS[0], MAIN_MENU_TABLE_ROWS[1], row=1, column=0
        )
        mode_description_frame = self._table_cell(
            menu_frame,
            MAIN_MENU_TABLE_COLS[1] + MAIN_MENU_TABLE_COLS[2],
            MAIN_MENU_TABLE_ROWS[1],
            row=1,
            column=1,
            columnspan=2,
        )

        self.imageset_buttons = self._build_button_column(
            imageset_buttons_frame,
            self.imagesets,
            MAIN_MENU_IMAGESET_BUTTON_WIDTH,
            MAIN_MENU_IMAGESET_BUTTON_HEIGH,
            MAIN_MENU_IMAGESET_BUTTON_FONT,
            self.select_imageset,
        )
        self.imageset_tags_label = Label(
            imageset_description_frame,
            font=("arial", 12, "bold"),
            fg="#FFFFFF",
            background=BACKGROUND_COLOR,
            justify=LEFT,
            anchor="w",
        )
        self.imageset_tags_label.grid(row=0, column=0, sticky=W)
        self.imageset_paths_label = Label(
            imageset_description_frame,
            font="arial",
            fg="#FFFFFF",
            background=BACKGROUND_COLOR,
            justify=LEFT,
            anchor="w",
        )
        self.imageset_paths_label.grid(row=1, column=0, sticky=W)

        self.mode_buttons = self._build_button_column(
            mode_buttons_frame,
            self.modes,
            MAIN_MENU_MODE_BUTTON_WIDTH,
            MAIN_MENU_MODE_BUTTON_HEIGH,
            MAIN_MENU_MODET_BUTTON_FONT,
            self.select_mode,
        )
        self.mode_header_label = Label(
            mode_description_frame,
            font=("arial", 12, "bold"),
            fg="#FFFFFF",
            background=BACKGROUND_COLOR,
            justify=LEFT,
            anchor="w",
        )
        self.mode_header_label.grid(row=0, column=0, sticky=W)
        self.mode_body_label = Label(
            mode_description_frame,
            font="arial",
            fg="#FFFFFF",
            background=BACKGROUND_COLOR,
            justify=LEFT,
            anchor="w",
        )
        self.mode_body_label.grid(row=1, column=0, sticky=W)
        self.mode_total_label = Label(
            mode_description_frame,
            font="arial",
            fg="#FFFFFF",
            background=BACKGROUND_COLOR,
            justify=LEFT,
            anchor="w",
        )
        self.mode_total_label.grid(row=2, column=0, sticky=W)

        Button(
            start_button_frame,
            text=MAIN_MENU_START_BUTTON_TEXT,
            command=lambda: self.start_session(self.picked_imageset, self.picked_mode),
            width=MAIN_MENU_START_BUTTON_WIDTH,
            height=MAIN_MENU_START_BUTTON_HEIGHT,
            relief=FLAT,
            font=MAIN_MENU_START_BUTTON_FONT,
        ).pack()

    @staticmethod
    def _table_cell(
        parent: Frame, width: int, height: int, row: int, column: int, columnspan: int = 1
    ) -> Frame:
        frame = Frame(parent, width=width, height=height, background=BACKGROUND_COLOR, border=0)
        frame.grid_propagate(False)
        frame.grid(row=row, column=column, columnspan=columnspan, sticky=NW)
        return frame

    def configure(self, event):
        width = self.tk.winfo_width()
        height = self.tk.winfo_height()

        if (
            ((self.width, self.height) != (width, height))
            and width > 256
            and height > 256
        ):
            self.width = width
            self.height = height
            if self.menu_widget:
                self.canvas.itemconfigure(
                    self.menu_widget, width=width - 12, height=height - 12
                )

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

    default_mode = next((name for name, mode in modes.items() if mode.default), None)
    if default_mode:
        app.select_mode(default_mode)

    app.select_imageset(random.choice(list(imagesets.keys())))
