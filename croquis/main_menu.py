from typing import Callable, Iterable
from tkinter import *
from tkinter import ttk
import random

from croquis.util import *
from croquis.constants import *
from croquis.session import start_session
from croquis.model import *
from croquis.error_modal import show_error_modal
from croquis.config_editor import open_options_editor, open_imageset_editor
from croquis.theme import apply_theme
from croquis.i18n import translate


class MainMenuApp:
    def __init__(
        self,
        tk: Tk,
        canvas: Canvas,
        config: Config,
        config_path: str,
        main_menu_callback: Callable[[str], None],
    ):
        self.tk: Tk = tk
        self.canvas: Canvas = canvas
        self.config: Config = config
        self.config_path: str = config_path
        self.imagesets: dict[str, ImageSet] = config.imageset
        self.modes: dict[str, Mode] = config.mode
        self.categories: dict[str, Category] = config.category
        self.picked_imagesets: set[str] = set()
        self.mode_var: StringVar = StringVar(value="")
        self.monochrome_var: BooleanVar = BooleanVar(value=config.monochrome_default)
        self.menu_frame: ttk.Frame | None = None
        self.menu_bar: Menu | None = None

        self.main_menu_callback = main_menu_callback

        self.imageset_buttons: dict[str, ttk.Checkbutton] = {}
        self.imageset_vars: dict[str, BooleanVar] = {}
        self.mode_buttons: dict[str, ttk.Radiobutton] = {}
        self.category_buttons: dict[str, ttk.Button] = {}

        tk.title("Croquis")

    def delete_children(self):
        if self.menu_frame is not None:
            self.menu_frame.destroy()
            self.menu_frame = None
        if self.menu_bar is not None:
            self.tk.config(menu="")
            self.menu_bar = None

    def _on_config_saved(self):
        apply_theme(self.tk, self.config.theme)
        self.delete_children()
        self.main_menu_callback("main_menu")

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

    def select_mode(self):
        name = self.mode_var.get()
        print("mode", name)
        if not name:
            return

        header, body, total_time = self.modes[name].get_label(self.config.language)
        self.mode_header_label.config(text=header)
        self.mode_body_label.config(text=body)
        self.mode_total_label.config(
            text=translate(
                "Total: {total_time}", self.config.language, total_time=total_time
            )
        )

    @staticmethod
    def _build_checkbutton_column(
        parent: ttk.Frame,
        names: Iterable[str],
        on_toggle: Callable[[str], None],
    ) -> tuple[dict[str, ttk.Checkbutton], dict[str, BooleanVar]]:
        buttons = {}
        variables = {}
        for idx, name in enumerate(names):
            var = BooleanVar(value=False)
            btn = ttk.Checkbutton(
                parent,
                text=name,
                variable=var,
                command=lambda x=name: on_toggle(x),
            )
            btn.grid(row=idx, column=0, sticky=W, pady=2)
            buttons[name] = btn
            variables[name] = var
        return buttons, variables

    @staticmethod
    def _build_radiobutton_column(
        parent: ttk.Frame,
        names: Iterable[str],
        variable: StringVar,
        on_select: Callable[[], None],
    ) -> dict[str, ttk.Radiobutton]:
        buttons = {}
        for idx, name in enumerate(names):
            btn = ttk.Radiobutton(
                parent,
                text=name,
                variable=variable,
                value=name,
                command=on_select,
            )
            btn.grid(row=idx, column=0, sticky=W, pady=2)
            buttons[name] = btn
        return buttons

    @staticmethod
    def _build_button_row(
        parent: ttk.Frame,
        names: Iterable[str],
        on_select: Callable[[str], None],
    ) -> dict[str, ttk.Button]:
        buttons = {}
        for idx, name in enumerate(names):
            btn = ttk.Button(parent, text=name, command=lambda x=name: on_select(x))
            btn.grid(row=0, column=idx, sticky=W, padx=(0, 6))
            buttons[name] = btn
        return buttons

    def draw_menu(self):
        language = self.config.language
        self.menu_bar = Menu(self.tk)
        self.menu_bar.add_command(
            label=translate("Options...", language),
            command=lambda: open_options_editor(
                self.tk, self.config, self.config_path, self._on_config_saved
            ),
        )
        self.menu_bar.add_command(
            label=translate("Configure Images...", language),
            command=lambda: open_imageset_editor(
                self.tk, self.config, self.config_path, self._on_config_saved
            ),
        )
        self.tk.config(menu=self.menu_bar)

        menu_frame = ttk.Frame(self.tk, padding=12)
        menu_frame.pack(fill=BOTH, expand=True)
        self.menu_frame = menu_frame

        for col, weight in enumerate(MAIN_MENU_COL_WEIGHTS):
            menu_frame.columnconfigure(col, weight=weight)
        for row, weight in enumerate(MAIN_MENU_ROW_WEIGHTS):
            menu_frame.rowconfigure(row, weight=weight)

        category_buttons_frame = ttk.Frame(menu_frame)
        category_buttons_frame.grid(
            row=0, column=0, columnspan=3, sticky=NSEW, pady=(0, 12)
        )

        imageset_buttons_frame = ttk.Labelframe(
            menu_frame, text=translate("Image sets", language)
        )
        imageset_buttons_frame.grid(row=1, column=0, sticky=NSEW, padx=(0, 8))

        mode_buttons_frame = ttk.Labelframe(menu_frame, text=translate("Mode", language))
        mode_buttons_frame.grid(row=1, column=1, sticky=NSEW, padx=8)

        start_button_frame = ttk.Frame(menu_frame)
        start_button_frame.grid(row=1, column=2, sticky=NSEW, padx=(8, 0))

        imageset_description_frame = ttk.Frame(menu_frame)
        imageset_description_frame.grid(
            row=2, column=0, sticky=NSEW, padx=(0, 8), pady=(12, 0)
        )

        mode_description_frame = ttk.Frame(menu_frame)
        mode_description_frame.grid(
            row=2, column=1, columnspan=2, sticky=NSEW, padx=8, pady=(12, 0)
        )

        self.category_buttons = self._build_button_row(
            category_buttons_frame, self.categories, self.select_category
        )

        self.imageset_buttons, self.imageset_vars = self._build_checkbutton_column(
            imageset_buttons_frame, self.imagesets, self.toggle_imageset
        )
        self.imageset_tags_label = ttk.Label(
            imageset_description_frame, font=("", 10, "bold")
        )
        self.imageset_tags_label.grid(row=0, column=0, sticky=W)
        self.imageset_paths_label = ttk.Label(
            imageset_description_frame, justify=LEFT
        )
        self.imageset_paths_label.grid(row=1, column=0, sticky=W)

        self.mode_buttons = self._build_radiobutton_column(
            mode_buttons_frame, self.modes, self.mode_var, self.select_mode
        )
        self.mode_header_label = ttk.Label(
            mode_description_frame, font=("", 10, "bold")
        )
        self.mode_header_label.grid(row=0, column=0, sticky=W)
        self.mode_body_label = ttk.Label(mode_description_frame, justify=LEFT)
        self.mode_body_label.grid(row=1, column=0, sticky=W)
        self.mode_total_label = ttk.Label(mode_description_frame, justify=LEFT)
        self.mode_total_label.grid(row=2, column=0, sticky=W)

        start_button_group = ttk.Frame(start_button_frame)
        start_button_group.pack(anchor=CENTER, expand=True)

        ttk.Checkbutton(
            start_button_group,
            text=translate("Monochrome", language),
            variable=self.monochrome_var,
        ).pack(anchor=CENTER, pady=(0, 8))

        ttk.Button(
            start_button_group,
            text=translate("Start Session", language),
            command=lambda: self.start_session(
                self.picked_imagesets, self.mode_var.get(), self.monochrome_var.get()
            ),
        ).pack(anchor=CENTER)

    def _on_exclude_image(self, path: str):
        normalized = normalize_path(path)
        if normalized not in {normalize_path(p) for p in self.config.excluded_images}:
            self.config.excluded_images.append(normalized)
            save_config(self.config, self.config_path)

    def start_session(
        self, picked_imagesets: set[str], picked_mode: str, monochrome: bool = False
    ):
        try:
            if not picked_imagesets or not picked_mode:
                return

            merged = merge_imagesets(
                self.imagesets[name] for name in picked_imagesets
            )
            if not merged.paths:
                return

            self.delete_children()
            self.canvas.pack(fill=BOTH, expand=True)
            start_session(
                self.tk,
                self.canvas,
                f"{', '.join(sorted(picked_imagesets))} - {picked_mode}",
                merged,
                self.modes[picked_mode],
                (self.tk.winfo_width(), self.tk.winfo_height()),
                self.main_menu_callback,
                self.config.image_locations,
                monochrome,
                self.config.excluded_images,
                self.config.keybindings,
                self._on_exclude_image,
                self.config.zen_mode,
                self.config.language,
            )
        except Exception as e:
            show_error_modal(e)


def start_main_menu(
    tk: Tk,
    canvas: Canvas,
    config: Config,
    config_path: str,
    callback: Callable[[str], None],
):
    print("MAIN MENU")

    app = MainMenuApp(tk, canvas, config, config_path, callback)
    app.draw_menu()

    default_mode = next(
        (name for name, mode in config.mode.items() if mode.default), None
    )
    if default_mode:
        app.mode_var.set(default_mode)
        app.select_mode()

    if config.imageset:
        initial_imageset = random.choice(list(config.imageset.keys()))
        app.imageset_vars[initial_imageset].set(True)
        app.toggle_imageset(initial_imageset)
