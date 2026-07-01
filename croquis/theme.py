from tkinter import Tk

import sv_ttk
import darkdetect


def apply_theme(tk: Tk, theme: str = "auto") -> None:
    resolved = theme if theme in ("light", "dark") else (darkdetect.theme() or "dark")
    sv_ttk.set_theme(resolved, root=tk)
