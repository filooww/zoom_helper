import os
import sys
import tkinter as tk

from .config import PLATFORM


def _assets_dir():
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS if hasattr(sys, "_MEIPASS") else os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "assets")


def apply_icon(window):
    assets = _assets_dir()

    if PLATFORM == "Windows":
        ico = os.path.join(assets, "icon.ico")
        if os.path.exists(ico):
            try:
                window.iconbitmap(ico)
                return
            except Exception:
                pass

    png = os.path.join(assets, "icon.png")
    if os.path.exists(png):
        try:
            photo = tk.PhotoImage(file=png)
            window.iconphoto(True, photo)
            window._icon_ref = photo
        except Exception:
            pass
