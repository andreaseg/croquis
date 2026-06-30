import copy
import re
from typing import Callable
from tkinter import *
from tkinter import simpledialog, messagebox, filedialog, ttk

from croquis.model import *
from croquis.util import parse_timer

OPTIONS_WINDOW_SIZE = "640x480"
IMAGESET_WINDOW_SIZE = "780x520"
ERROR_TEXT_COLOR = "#CC3333"


def _build_listbox_crud(
    parent: Frame,
    on_select: Callable[[str | None], None],
    on_add: Callable[[], None],
    on_remove: Callable[[str], None],
    on_rename: Callable[[str], None],
) -> Listbox:
    frame = Frame(parent)
    frame.pack(side=LEFT, fill=Y, padx=8, pady=8)

    listbox = Listbox(frame, exportselection=False, width=24, height=14)
    listbox.pack(side=TOP, fill=Y)

    def selected_name() -> str | None:
        selection = listbox.curselection()
        return listbox.get(selection[0]) if selection else None

    listbox.bind("<<ListboxSelect>>", lambda e: on_select(selected_name()))

    def do_rename():
        name = selected_name()
        if name:
            on_rename(name)

    def do_remove():
        name = selected_name()
        if name:
            on_remove(name)

    button_frame = Frame(frame)
    button_frame.pack(side=TOP, fill=X, pady=4)
    Button(button_frame, text="Add", command=on_add).pack(side=LEFT, padx=2)
    Button(button_frame, text="Rename", command=do_rename).pack(side=LEFT, padx=2)
    Button(button_frame, text="Remove", command=do_remove).pack(side=LEFT, padx=2)

    return listbox


def _refresh_listbox(listbox: Listbox, names: list[str], select: str | None = None):
    listbox.delete(0, END)
    for name in names:
        listbox.insert(END, name)
    if select is not None and select in names:
        idx = names.index(select)
        listbox.selection_set(idx)
        listbox.see(idx)


def _prompt_unique_name(
    parent: Toplevel, title: str, prompt: str, existing, initialvalue: str = ""
) -> str | None:
    name = simpledialog.askstring(title, prompt, initialvalue=initialvalue, parent=parent)
    if not name:
        return None
    if name in existing:
        messagebox.showerror(title, f"'{name}' already exists.", parent=parent)
        return None
    return name


def open_options_editor(
    tk: Tk, config: Config, config_path: str, on_saved: Callable[[], None]
):
    working = copy.deepcopy(config)

    window = Toplevel(tk)
    window.title("Options")
    window.geometry(OPTIONS_WINDOW_SIZE)
    window.transient(tk)
    window.grab_set()

    dims_frame = Frame(window)
    dims_frame.pack(side=TOP, fill=X, padx=8, pady=8)
    Label(dims_frame, text="Window size (WIDTHxHEIGHT):").pack(side=LEFT)
    dimensions_var = StringVar(value=working.dimensions)
    Entry(dims_frame, textvariable=dimensions_var, width=16).pack(side=LEFT, padx=8)

    body = Frame(window)
    body.pack(side=TOP, fill=BOTH, expand=True)

    selected_mode: list[str | None] = [None]

    def commit_form():
        name = selected_mode[0]
        if name is None or name not in working.mode:
            return
        mode = working.mode[name]
        mode.manual = manual_var.get()
        mode.timers = timers_var.get()

    def on_select_mode(name: str | None):
        commit_form()
        selected_mode[0] = name
        if name is None:
            manual_var.set(False)
            timers_var.set("")
            return
        mode = working.mode[name]
        manual_var.set(mode.manual)
        timers_var.set(mode.timers)

    def on_add_mode():
        name = _prompt_unique_name(window, "Add mode", "Mode name:", working.mode)
        if not name:
            return
        working.mode[name] = Mode(timers="1m", default=False, manual=False)
        refresh_modes(select=name)
        on_select_mode(name)
        refresh_default_menu()

    def on_remove_mode(name: str):
        if not messagebox.askyesno(
            "Remove mode", f"Remove mode '{name}'?", parent=window
        ):
            return
        del working.mode[name]
        if default_var.get() == name:
            default_var.set("")
        refresh_modes()
        on_select_mode(None)
        refresh_default_menu()

    def on_rename_mode(name: str):
        new_name = _prompt_unique_name(
            window, "Rename mode", "New name:", working.mode, initialvalue=name
        )
        if not new_name:
            return
        working.mode[new_name] = working.mode.pop(name)
        if default_var.get() == name:
            default_var.set(new_name)
        refresh_modes(select=new_name)
        on_select_mode(new_name)
        refresh_default_menu()

    mode_listbox = _build_listbox_crud(
        body, on_select_mode, on_add_mode, on_remove_mode, on_rename_mode
    )

    def refresh_modes(select: str | None = None):
        _refresh_listbox(mode_listbox, list(working.mode.keys()), select)

    form_frame = Frame(body)
    form_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=8, pady=8)

    manual_var = BooleanVar(value=False)
    Checkbutton(form_frame, text="Manual (click to advance)", variable=manual_var).pack(
        anchor=W
    )

    Label(form_frame, text="Timers (e.g. '3*30s 2m 5m'):").pack(anchor=W, pady=(8, 0))
    timers_var = StringVar(value="")
    Entry(form_frame, textvariable=timers_var, width=40).pack(anchor=W)

    Label(form_frame, text="Default mode:").pack(anchor=W, pady=(16, 0))
    default_var = StringVar(
        value=next((n for n, m in working.mode.items() if m.default), "")
    )
    default_menu_container = Frame(form_frame)
    default_menu_container.pack(anchor=W)

    def refresh_default_menu():
        for child in default_menu_container.winfo_children():
            child.destroy()
        names = list(working.mode.keys())
        if not names:
            Label(default_menu_container, text="(no modes)").pack()
            return
        if default_var.get() not in names:
            default_var.set(names[0])
        OptionMenu(default_menu_container, default_var, *names).pack()

    error_var = StringVar(value="")
    Label(window, textvariable=error_var, fg=ERROR_TEXT_COLOR).pack(
        side=TOP, fill=X, padx=8
    )

    def on_save():
        commit_form()

        if not re.match(r"^\d+x\d+$", dimensions_var.get().strip()):
            error_var.set("Window size must look like e.g. 1920x1200")
            return

        for name, mode in working.mode.items():
            if not mode.manual:
                try:
                    parse_timer(mode.timers)
                except Exception as e:
                    error_var.set(f"Mode '{name}': {e}")
                    return

        for name, mode in working.mode.items():
            mode.default = name == default_var.get()

        working.dimensions = dimensions_var.get().strip()

        save_config(working, config_path)
        replace_config_fields(config, working)
        window.destroy()
        on_saved()

    button_frame = Frame(window)
    button_frame.pack(side=BOTTOM, fill=X, padx=8, pady=8)
    Button(button_frame, text="Cancel", command=window.destroy).pack(side=RIGHT, padx=4)
    Button(button_frame, text="Save", command=on_save).pack(side=RIGHT, padx=4)

    refresh_modes()
    refresh_default_menu()
    if working.mode:
        first = next(iter(working.mode.keys()))
        mode_listbox.selection_set(0)
        on_select_mode(first)


def open_imageset_editor(
    tk: Tk, config: Config, config_path: str, on_saved: Callable[[], None]
):
    working = copy.deepcopy(config)

    window = Toplevel(tk)
    window.title("Configure Images")
    window.geometry(IMAGESET_WINDOW_SIZE)
    window.transient(tk)
    window.grab_set()

    notebook = ttk.Notebook(window)
    notebook.pack(side=TOP, fill=BOTH, expand=True)

    imageset_tab = Frame(notebook)
    category_tab = Frame(notebook)
    notebook.add(imageset_tab, text="Imagesets")
    notebook.add(category_tab, text="Categories")

    # --- Imagesets tab ---

    selected_imageset: list[str | None] = [None]

    def commit_imageset_form():
        name = selected_imageset[0]
        if name is None or name not in working.imageset:
            return
        imageset = working.imageset[name]
        imageset.tags = [
            tag.strip() for tag in imageset_tags_var.get().split(",") if tag.strip()
        ]
        imageset.paths = list(imageset_paths_listbox.get(0, END))

    def on_select_imageset(name: str | None):
        commit_imageset_form()
        selected_imageset[0] = name
        imageset_paths_listbox.delete(0, END)
        if name is None:
            imageset_tags_var.set("")
            return
        imageset = working.imageset[name]
        imageset_tags_var.set(", ".join(imageset.tags))
        for path in imageset.paths:
            imageset_paths_listbox.insert(END, path)

    def on_add_imageset():
        name = _prompt_unique_name(
            window, "Add imageset", "Imageset name:", working.imageset
        )
        if not name:
            return
        working.imageset[name] = ImageSet(tags=[], paths=[])
        refresh_imagesets(select=name)
        on_select_imageset(name)

    def on_remove_imageset(name: str):
        if not messagebox.askyesno(
            "Remove imageset", f"Remove imageset '{name}'?", parent=window
        ):
            return
        del working.imageset[name]
        refresh_imagesets()
        on_select_imageset(None)

    def on_rename_imageset(name: str):
        new_name = _prompt_unique_name(
            window, "Rename imageset", "New name:", working.imageset, initialvalue=name
        )
        if not new_name:
            return
        working.imageset[new_name] = working.imageset.pop(name)
        refresh_imagesets(select=new_name)
        on_select_imageset(new_name)

    imageset_listbox = _build_listbox_crud(
        imageset_tab,
        on_select_imageset,
        on_add_imageset,
        on_remove_imageset,
        on_rename_imageset,
    )

    def refresh_imagesets(select: str | None = None):
        _refresh_listbox(imageset_listbox, list(working.imageset.keys()), select)

    imageset_form = Frame(imageset_tab)
    imageset_form.pack(side=LEFT, fill=BOTH, expand=True, padx=8, pady=8)

    Label(imageset_form, text="Tags (comma-separated):").pack(anchor=W)
    imageset_tags_var = StringVar(value="")
    Entry(imageset_form, textvariable=imageset_tags_var, width=44).pack(anchor=W)

    Label(imageset_form, text="Folders:").pack(anchor=W, pady=(8, 0))
    imageset_paths_listbox = Listbox(imageset_form, width=54, height=10)
    imageset_paths_listbox.pack(anchor=W)

    def on_add_folder():
        path = filedialog.askdirectory(parent=window)
        if path:
            imageset_paths_listbox.insert(END, path)

    def on_remove_folder():
        selection = imageset_paths_listbox.curselection()
        if selection:
            imageset_paths_listbox.delete(selection[0])

    path_button_frame = Frame(imageset_form)
    path_button_frame.pack(anchor=W, pady=4)
    Button(path_button_frame, text="Add folder...", command=on_add_folder).pack(
        side=LEFT, padx=2
    )
    Button(path_button_frame, text="Remove selected", command=on_remove_folder).pack(
        side=LEFT, padx=2
    )

    # --- Categories tab ---

    selected_category: list[str | None] = [None]

    def commit_category_form():
        name = selected_category[0]
        if name is None or name not in working.category:
            return
        working.category[name].tags = [
            tag.strip() for tag in category_tags_var.get().split(",") if tag.strip()
        ]

    def on_select_category(name: str | None):
        commit_category_form()
        selected_category[0] = name
        if name is None:
            category_tags_var.set("")
            return
        category_tags_var.set(", ".join(working.category[name].tags))

    def on_add_category():
        name = _prompt_unique_name(
            window, "Add category", "Category name:", working.category
        )
        if not name:
            return
        working.category[name] = Category(tags=[])
        refresh_categories(select=name)
        on_select_category(name)

    def on_remove_category(name: str):
        if not messagebox.askyesno(
            "Remove category", f"Remove category '{name}'?", parent=window
        ):
            return
        del working.category[name]
        refresh_categories()
        on_select_category(None)

    def on_rename_category(name: str):
        new_name = _prompt_unique_name(
            window, "Rename category", "New name:", working.category, initialvalue=name
        )
        if not new_name:
            return
        working.category[new_name] = working.category.pop(name)
        refresh_categories(select=new_name)
        on_select_category(new_name)

    category_listbox = _build_listbox_crud(
        category_tab,
        on_select_category,
        on_add_category,
        on_remove_category,
        on_rename_category,
    )

    def refresh_categories(select: str | None = None):
        _refresh_listbox(category_listbox, list(working.category.keys()), select)

    category_form = Frame(category_tab)
    category_form.pack(side=LEFT, fill=BOTH, expand=True, padx=8, pady=8)

    Label(category_form, text="Tags (comma-separated):").pack(anchor=W)
    category_tags_var = StringVar(value="")
    Entry(category_form, textvariable=category_tags_var, width=44).pack(anchor=W)

    error_var = StringVar(value="")
    Label(window, textvariable=error_var, fg=ERROR_TEXT_COLOR).pack(
        side=TOP, fill=X, padx=8
    )

    def on_save():
        commit_imageset_form()
        commit_category_form()

        save_config(working, config_path)
        replace_config_fields(config, working)
        window.destroy()
        on_saved()

    button_frame = Frame(window)
    button_frame.pack(side=BOTTOM, fill=X, padx=8, pady=8)
    Button(button_frame, text="Cancel", command=window.destroy).pack(side=RIGHT, padx=4)
    Button(button_frame, text="Save", command=on_save).pack(side=RIGHT, padx=4)

    refresh_imagesets()
    refresh_categories()
    if working.imageset:
        first = next(iter(working.imageset.keys()))
        imageset_listbox.selection_set(0)
        on_select_imageset(first)
    if working.category:
        first = next(iter(working.category.keys()))
        category_listbox.selection_set(0)
        on_select_category(first)
