import traceback
import sys

from tkinter import Tk, END, DISABLED, WORD, TOP, BOTTOM, BOTH, X
from tkinter import ttk
import tkinter.scrolledtext as scrolledtext
from croquis.util import resource_path
from croquis.theme import apply_theme

WIDTH = 480
HEIGH = 260
PADDING = 12

BACKGROUND = "#C9C9C9"
CLOSE_LABEL = "Ok"


def show_error_modal(e: Exception, critical: bool = True):
    traceback.print_exception(e)
    _show_error_modal(str(e) + "\n" + traceback.format_exc() + traceback.format_exc())

    if critical:
        return sys.exit(-1)


def _show_error_modal(message: str):
    tk = Tk()
    apply_theme(tk)
    tk.iconbitmap(resource_path("icon.ico"))
    tk.geometry(f"{WIDTH}x{HEIGH}")
    tk.title("Fatal error")
    tk.resizable(False, False)

    root_frame = ttk.Frame(tk, padding=PADDING)
    root_frame.pack(fill=BOTH, expand=True)

    text = scrolledtext.ScrolledText(
        root_frame,
        font=("arial", 12),
        width=46,
        height=8,
        padx=PADDING,
        pady=PADDING,
        background=BACKGROUND,
        wrap=WORD,
    )
    text.insert(END, message)
    text.config(state=DISABLED)
    text.pack(side=TOP, fill=BOTH, expand=True)

    button_frame = ttk.Frame(root_frame)
    button_frame.pack(side=BOTTOM, fill=X, pady=(PADDING, 0))

    ttk.Button(
        button_frame,
        text=CLOSE_LABEL,
        command=tk.quit,
    ).pack(anchor="center")

    tk.mainloop()
