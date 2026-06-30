from tkinter import Tk

import sv_ttk
import darkdetect


def apply_theme(tk: Tk) -> None:
    sv_ttk.set_theme(darkdetect.theme() or "dark", root=tk)
