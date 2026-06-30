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
        categories: dict[str, Category],
        geometry: tuple[int, int],
        main_menu_callback: Callable[[str], None],
    ):
        self.tk: Tk = tk
        self.canvas: Canvas = canvas
        self.imagesets: dict[str, ImageSet] = imagesets
        self.modes: dict[str, Mode] = modes
        self.categories: dict[str, Category] = categories
        self.picked_imagesets: set[str] = set()
        self.picked_mode: str | None = None
        self.menu_widget: int | None = None

        self.main_menu_callback = main_menu_callback

        self.imageset_buttons: dict[str, Checkbutton] = {}
        self.imageset_vars: dict[str, BooleanVar] = {}
        self.mode_buttons: dict[str, Button] = {}
        self.category_buttons: dict[str, Button] = {}

        self.width, self.height = geometry

        tk.title("Croquis")
        tk.bind("<Configure>", lambda e: self.configure(e))

    def delete_children(self):
        self.canvas.delete(self.menu_widget)

    def toggle_imageset(self, name: str):
        print("imageset", name, self.imageset_vars[name].get())
        if self.imageset_vars[name].get():
            self.picked_imagesets.add(name)
        else:
            self.picked_imagesets.discard(name)
        self._refresh_imageset_details()

    def select_category(self, name: str):
        print("category", name)
        matches = imagesets_matching_category(self.imagesets, self.categories[name])
        self.picked_imagesets = set(matches.keys())
        for imageset_name, var in self.imageset_vars.items():
            var.set(imageset_name in self.picked_imagesets)
        self._refresh_imageset_details()

    def _refresh_imageset_details(self):
        merged = merge_imagesets(
            self.imagesets[name] for name in self.picked_imagesets
        )
        self.imageset_tags_label.config(text=", ".join(sort_tags(merged.tags)))
        self.imageset_paths_label.config(text="\n".join(merged.paths))

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

    @staticmethod
    def _build_button_row(
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
            btn.grid(row=0, column=idx, sticky=W)
            buttons[name] = btn
        return buttons

    @staticmethod
    def _build_checkbutton_column(
        parent: Frame,
        names: Iterable[str],
        width: int,
        height: int,
        font,
        on_toggle: Callable[[str], None],
    ) -> tuple[dict[str, Checkbutton], dict[str, BooleanVar]]:
        buttons = {}
        variables = {}
        for idx, name in enumerate(names):
            var = BooleanVar(value=False)
            btn = Checkbutton(
                parent,
                text=name,
                variable=var,
                command=lambda x=name: on_toggle(x),
                width=width,
                height=height,
                relief=FLAT,
                font=font,
                selectcolor=SELECTED_OPTION_BUTTON_COLOR,
                anchor=W,
            )
            btn.grid(row=idx, column=0, sticky=W)
            buttons[name] = btn
            variables[name] = var
        return buttons, variables

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

        category_buttons_frame = self._table_cell(
            menu_frame,
            sum(MAIN_MENU_TABLE_COLS),
            MAIN_MENU_TABLE_ROWS[0],
            row=0,
            column=0,
            columnspan=3,
        )
        imageset_buttons_frame = self._table_cell(
            menu_frame, MAIN_MENU_TABLE_COLS[0], MAIN_MENU_TABLE_ROWS[1], row=1, column=0
        )
        mode_buttons_frame = self._table_cell(
            menu_frame, MAIN_MENU_TABLE_COLS[1], MAIN_MENU_TABLE_ROWS[1], row=1, column=1
        )
        start_button_frame = self._table_cell(
            menu_frame, MAIN_MENU_TABLE_COLS[2], MAIN_MENU_TABLE_ROWS[1], row=1, column=2
        )
        imageset_description_frame = self._table_cell(
            menu_frame, MAIN_MENU_TABLE_COLS[0], MAIN_MENU_TABLE_ROWS[2], row=2, column=0
        )
        mode_description_frame = self._table_cell(
            menu_frame,
            MAIN_MENU_TABLE_COLS[1] + MAIN_MENU_TABLE_COLS[2],
            MAIN_MENU_TABLE_ROWS[2],
            row=2,
            column=1,
            columnspan=2,
        )

        self.category_buttons = self._build_button_row(
            category_buttons_frame,
            self.categories,
            MAIN_MENU_CATEGORY_BUTTON_WIDTH,
            MAIN_MENU_CATEGORY_BUTTON_HEIGHT,
            MAIN_MENU_CATEGORY_BUTTON_FONT,
            self.select_category,
        )

        self.imageset_buttons, self.imageset_vars = self._build_checkbutton_column(
            imageset_buttons_frame,
            self.imagesets,
            MAIN_MENU_IMAGESET_BUTTON_WIDTH,
            MAIN_MENU_IMAGESET_BUTTON_HEIGH,
            MAIN_MENU_IMAGESET_BUTTON_FONT,
            self.toggle_imageset,
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
            command=lambda: self.start_session(self.picked_imagesets, self.picked_mode),
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

    def start_session(self, picked_imagesets: set[str], picked_mode: str | None):
        try:
            if not picked_imagesets or not picked_mode:
                return

            merged = merge_imagesets(
                self.imagesets[name] for name in picked_imagesets
            )
            if not merged.paths:
                return

            self.delete_children()
            start_session(
                self.tk,
                self.canvas,
                f"{', '.join(sorted(picked_imagesets))} - {picked_mode}",
                merged,
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
    categories: dict[str, Category],
    dimensions: tuple[int, int],
    callback: Callable[[str], None],
):
    print("MAIN MENU")

    app = MainMenuApp(tk, canvas, imagesets, modes, categories, dimensions, callback)
    app.draw_menu()

    default_mode = next((name for name, mode in modes.items() if mode.default), None)
    if default_mode:
        app.select_mode(default_mode)

    if imagesets:
        initial_imageset = random.choice(list(imagesets.keys()))
        app.imageset_vars[initial_imageset].set(True)
        app.toggle_imageset(initial_imageset)
