import traceback
import sys
from typing import NoReturn

from tkinter import Tk, Frame, N, Button, END, DISABLED, WORD
import tkinter.scrolledtext as scrolledtext
from croquis.util import resource_path

WIDTH = 480
LABEL_HEIGHT = 180
BUTTON_AREA_HEIGH = 80
HEIGH = LABEL_HEIGHT + BUTTON_AREA_HEIGH
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
    tk.iconbitmap(resource_path("icon.ico"))
    tk.geometry(f"{WIDTH}x{HEIGH}")
    tk.title("Fatal error")
    tk.resizable(False, False)
    tk.grid_propagate(False)
    tk.configure(bg=BACKGROUND)

    error_message_frame = Frame(
        tk,
        height=LABEL_HEIGHT - 2 * PADDING,
        width=WIDTH - 2 * PADDING,
        background=BACKGROUND,
    )
    error_message_frame.grid(row=0)
    error_message_frame.grid_propagate(False)

    text = scrolledtext.ScrolledText(
        error_message_frame,
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
    text.grid()

    button_frame = Frame(
        tk, height=BUTTON_AREA_HEIGH, width=WIDTH, background=BACKGROUND
    )
    button_frame.grid(row=1)
    button_frame.grid_propagate(False)

    button = Button(
        button_frame,
        width=20,
        height=2,
        text=CLOSE_LABEL,
        command=tk.quit,
    )
    button.place(relx=0.5, rely=0.5, anchor=N)

    tk.mainloop()
