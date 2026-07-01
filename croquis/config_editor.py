import copy
import re
from typing import Callable
from tkinter import Tk, Toplevel, StringVar, BooleanVar, END, LEFT, RIGHT, TOP, BOTTOM, X, Y, BOTH, W
from tkinter import simpledialog, messagebox, filedialog, ttk

from croquis.model import *
from croquis.util import parse_timer, shorten_to_location

OPTIONS_WINDOW_SIZE = "640x480"
IMAGESET_WINDOW_SIZE = "780x520"
ERROR_TEXT_COLOR = "#CC3333"


def _build_tree_crud(
    parent: ttk.Frame,
    on_select: Callable[[str | None], None],
    on_add: Callable[[], None],
    on_remove: Callable[[str], None],
    on_rename: Callable[[str], None],
) -> ttk.Treeview:
    frame = ttk.Frame(parent)
    frame.pack(side=LEFT, fill=Y, padx=8, pady=8)

    tree = ttk.Treeview(frame, show="tree", selectmode="browse", height=14)
    tree.column("#0", width=180)
    tree.pack(side=TOP, fill=Y)

    def selected_name() -> str | None:
        selection = tree.selection()
        return selection[0] if selection else None

    tree.bind("<<TreeviewSelect>>", lambda e: on_select(selected_name()))

    def do_rename():
        name = selected_name()
        if name:
            on_rename(name)

    def do_remove():
        name = selected_name()
        if name:
            on_remove(name)

    button_frame = ttk.Frame(frame)
    button_frame.pack(side=TOP, fill=X, pady=4)
    ttk.Button(button_frame, text="Add", command=on_add).pack(side=LEFT, padx=2)
    ttk.Button(button_frame, text="Rename", command=do_rename).pack(side=LEFT, padx=2)
    ttk.Button(button_frame, text="Remove", command=do_remove).pack(side=LEFT, padx=2)

    return tree


def _build_folder_list(
    parent: ttk.Frame,
    paths: list[str],
    shorten: Callable[[str], str] = lambda p: p,
) -> tuple[ttk.Treeview, Callable[[], None]]:
    tree = ttk.Treeview(parent, show="tree", selectmode="browse", height=10)
    tree.column("#0", width=480)
    tree.pack(anchor=W)

    def refresh():
        tree.delete(*tree.get_children())
        for idx, path in enumerate(paths):
            tree.insert("", "end", iid=str(idx), text=path)

    def on_add_folder():
        picked = filedialog.askdirectory(parent=parent)
        if picked:
            paths.append(shorten(picked))
            refresh()

    def on_remove_folder():
        selection = tree.selection()
        if selection:
            del paths[int(selection[0])]
            refresh()

    button_frame = ttk.Frame(parent)
    button_frame.pack(anchor=W, pady=4)
    ttk.Button(button_frame, text="Add folder...", command=on_add_folder).pack(
        side=LEFT, padx=2
    )
    ttk.Button(button_frame, text="Remove selected", command=on_remove_folder).pack(
        side=LEFT, padx=2
    )

    return tree, refresh


def _refresh_tree(tree: ttk.Treeview, names: list[str], select: str | None = None):
    tree.delete(*tree.get_children())
    for name in names:
        tree.insert("", "end", iid=name, text=name)
    if select is not None and select in names:
        tree.selection_set(select)
        tree.see(select)


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


_MODIFIER_ONLY_KEYSYMS = {
    "Shift_L",
    "Shift_R",
    "Control_L",
    "Control_R",
    "Alt_L",
    "Alt_R",
    "Caps_Lock",
    "Num_Lock",
    "Super_L",
    "Super_R",
}


def _prompt_for_key(parent: Toplevel) -> str | None:
    dialog = Toplevel(parent)
    dialog.title("Press a key")
    dialog.geometry("280x100")
    dialog.transient(parent)
    dialog.grab_set()
    ttk.Label(dialog, text="Press any key...", padding=20).pack(expand=True)

    captured: list[str] = []

    def on_key(event):
        if event.keysym in _MODIFIER_ONLY_KEYSYMS:
            return
        captured.append(event.keysym)
        dialog.destroy()

    dialog.bind("<Key>", on_key)
    dialog.focus_set()
    dialog.wait_window()
    return captured[0] if captured else None


def _build_error_label(window: Toplevel, error_var: StringVar) -> ttk.Label:
    style = ttk.Style()
    style.configure("Error.TLabel", foreground=ERROR_TEXT_COLOR)
    label = ttk.Label(window, textvariable=error_var, style="Error.TLabel")
    label.pack(side=TOP, fill=X, padx=8)
    return label


def open_options_editor(
    tk: Tk, config: Config, config_path: str, on_saved: Callable[[], None]
):
    working = copy.deepcopy(config)

    window = Toplevel(tk)
    window.title("Options")
    window.geometry(OPTIONS_WINDOW_SIZE)
    window.transient(tk)
    window.grab_set()

    notebook = ttk.Notebook(window)
    notebook.pack(side=TOP, fill=BOTH, expand=True)

    general_tab = ttk.Frame(notebook)
    keybindings_tab = ttk.Frame(notebook)
    notebook.add(general_tab, text="General")
    notebook.add(keybindings_tab, text="Keybindings")

    dims_frame = ttk.Frame(general_tab)
    dims_frame.pack(side=TOP, fill=X, padx=8, pady=8)
    ttk.Label(dims_frame, text="Window size (WIDTHxHEIGHT):").pack(side=LEFT)
    dimensions_var = StringVar(value=working.dimensions)
    ttk.Entry(dims_frame, textvariable=dimensions_var, width=16).pack(
        side=LEFT, padx=8
    )

    body = ttk.Frame(general_tab)
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

    mode_tree = _build_tree_crud(
        body, on_select_mode, on_add_mode, on_remove_mode, on_rename_mode
    )

    def refresh_modes(select: str | None = None):
        _refresh_tree(mode_tree, list(working.mode.keys()), select)

    form_frame = ttk.Frame(body)
    form_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=8, pady=8)

    manual_var = BooleanVar(value=False)
    ttk.Checkbutton(
        form_frame, text="Manual (click to advance)", variable=manual_var
    ).pack(anchor=W)

    ttk.Label(form_frame, text="Timers (e.g. '3*30s 2m 5m'):").pack(
        anchor=W, pady=(8, 0)
    )
    timers_var = StringVar(value="")
    ttk.Entry(form_frame, textvariable=timers_var, width=40).pack(anchor=W)

    ttk.Label(form_frame, text="Default mode:").pack(anchor=W, pady=(16, 0))
    default_var = StringVar(
        value=next((n for n, m in working.mode.items() if m.default), "")
    )
    default_menu_container = ttk.Frame(form_frame)
    default_menu_container.pack(anchor=W)

    def refresh_default_menu():
        for child in default_menu_container.winfo_children():
            child.destroy()
        names = list(working.mode.keys())
        if not names:
            ttk.Label(default_menu_container, text="(no modes)").pack()
            return
        if default_var.get() not in names:
            default_var.set(names[0])
        ttk.OptionMenu(
            default_menu_container, default_var, default_var.get(), *names
        ).pack()

    # --- Keybindings tab ---

    KEYBINDING_ACTION_LABELS = {
        "menu": "Open menu / pause",
        "prev": "Previous image (manual mode)",
        "next": "Next image (manual mode)",
    }

    error_var = StringVar(value="")

    keybinding_value_labels: dict[str, ttk.Label] = {}

    def refresh_keybinding_labels():
        for action, label in keybinding_value_labels.items():
            label.config(text=working.keybindings[action])

    def on_change_key(action: str):
        new_key = _prompt_for_key(window)
        if not new_key:
            return
        conflicting = next(
            (
                other
                for other, key in working.keybindings.items()
                if key == new_key and other != action
            ),
            None,
        )
        if conflicting:
            error_var.set(
                f"'{new_key}' is already bound to "
                f"'{KEYBINDING_ACTION_LABELS[conflicting]}'."
            )
            return
        working.keybindings[action] = new_key
        refresh_keybinding_labels()

    ttk.Label(
        keybindings_tab,
        text="Click Change..., then press the new key.",
        padding=(8, 8, 8, 0),
    ).grid(row=0, column=0, columnspan=3, sticky=W)

    for row, action in enumerate(("menu", "prev", "next"), start=1):
        ttk.Label(keybindings_tab, text=KEYBINDING_ACTION_LABELS[action]).grid(
            row=row, column=0, sticky=W, padx=8, pady=4
        )
        value_label = ttk.Label(keybindings_tab, text=working.keybindings[action])
        value_label.grid(row=row, column=1, sticky=W, padx=8)
        keybinding_value_labels[action] = value_label
        ttk.Button(
            keybindings_tab,
            text="Change...",
            command=lambda a=action: on_change_key(a),
        ).grid(row=row, column=2, sticky=W, padx=8)

    _build_error_label(window, error_var)

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

    button_frame = ttk.Frame(window)
    button_frame.pack(side=BOTTOM, fill=X, padx=8, pady=8)
    ttk.Button(button_frame, text="Cancel", command=window.destroy).pack(
        side=RIGHT, padx=4
    )
    ttk.Button(button_frame, text="Save", command=on_save).pack(side=RIGHT, padx=4)

    refresh_modes()
    refresh_default_menu()
    if working.mode:
        first = next(iter(working.mode.keys()))
        on_select_mode(first)
        mode_tree.selection_set(first)


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

    imageset_tab = ttk.Frame(notebook)
    category_tab = ttk.Frame(notebook)
    location_tab = ttk.Frame(notebook)
    notebook.add(imageset_tab, text="Imagesets")
    notebook.add(category_tab, text="Categories")
    notebook.add(location_tab, text="Image Locations")

    # --- Imagesets tab ---

    selected_imageset: list[str | None] = [None]
    imageset_paths: list[str] = []

    def commit_imageset_form():
        name = selected_imageset[0]
        if name is None or name not in working.imageset:
            return
        imageset = working.imageset[name]
        imageset.tags = [
            tag.strip() for tag in imageset_tags_var.get().split(",") if tag.strip()
        ]
        imageset.paths = list(imageset_paths)

    def on_select_imageset(name: str | None):
        commit_imageset_form()
        selected_imageset[0] = name
        imageset_paths.clear()
        if name is None:
            imageset_tags_var.set("")
            refresh_paths_tree()
            return
        imageset = working.imageset[name]
        imageset_tags_var.set(", ".join(imageset.tags))
        imageset_paths.extend(imageset.paths)
        refresh_paths_tree()

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

    imageset_tree = _build_tree_crud(
        imageset_tab,
        on_select_imageset,
        on_add_imageset,
        on_remove_imageset,
        on_rename_imageset,
    )

    def refresh_imagesets(select: str | None = None):
        _refresh_tree(imageset_tree, list(working.imageset.keys()), select)

    imageset_form = ttk.Frame(imageset_tab)
    imageset_form.pack(side=LEFT, fill=BOTH, expand=True, padx=8, pady=8)

    ttk.Label(imageset_form, text="Tags (comma-separated):").pack(anchor=W)
    imageset_tags_var = StringVar(value="")
    ttk.Entry(imageset_form, textvariable=imageset_tags_var, width=44).pack(anchor=W)

    ttk.Label(imageset_form, text="Folders:").pack(anchor=W, pady=(8, 0))
    imageset_paths_tree, refresh_paths_tree = _build_folder_list(
        imageset_form,
        imageset_paths,
        shorten=lambda p: shorten_to_location(p, working.image_locations),
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

    category_tree = _build_tree_crud(
        category_tab,
        on_select_category,
        on_add_category,
        on_remove_category,
        on_rename_category,
    )

    def refresh_categories(select: str | None = None):
        _refresh_tree(category_tree, list(working.category.keys()), select)

    category_form = ttk.Frame(category_tab)
    category_form.pack(side=LEFT, fill=BOTH, expand=True, padx=8, pady=8)

    ttk.Label(category_form, text="Tags (comma-separated):").pack(anchor=W)
    category_tags_var = StringVar(value="")
    ttk.Entry(category_form, textvariable=category_tags_var, width=44).pack(anchor=W)

    # --- Image Locations tab ---

    ttk.Label(
        location_tab,
        text="Folders to search for imageset paths, in addition to the app's own directory:",
        padding=(8, 8, 8, 0),
    ).pack(anchor=W)
    location_form = ttk.Frame(location_tab)
    location_form.pack(side=LEFT, fill=BOTH, expand=True, padx=8, pady=8)
    location_tree, refresh_locations = _build_folder_list(
        location_form, working.image_locations
    )
    refresh_locations()

    error_var = StringVar(value="")
    _build_error_label(window, error_var)

    def on_save():
        commit_imageset_form()
        commit_category_form()

        save_config(working, config_path)
        replace_config_fields(config, working)
        window.destroy()
        on_saved()

    button_frame = ttk.Frame(window)
    button_frame.pack(side=BOTTOM, fill=X, padx=8, pady=8)
    ttk.Button(button_frame, text="Cancel", command=window.destroy).pack(
        side=RIGHT, padx=4
    )
    ttk.Button(button_frame, text="Save", command=on_save).pack(side=RIGHT, padx=4)

    refresh_imagesets()
    refresh_categories()
    if working.imageset:
        first = next(iter(working.imageset.keys()))
        on_select_imageset(first)
        imageset_tree.selection_set(first)
    if working.category:
        first = next(iter(working.category.keys()))
        on_select_category(first)
        category_tree.selection_set(first)
