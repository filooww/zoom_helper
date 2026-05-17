import tkinter as tk

from .config import COLORS as C
from .config import FONT


class HoverButton(tk.Canvas):
    CORNER_RADIUS = 12
    DARKEN_AMOUNT = 25
    DISABLED_FILL = "#CFCFD9"

    def __init__(
        self,
        parent,
        text,
        bg,
        fg,
        command,
        width=320,
        height=56,
        font_size=16,
        bold=True,
        **kwargs,
    ):
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=parent["bg"],
            highlightthickness=0,
            **kwargs,
        )
        self.bg = bg
        self.fg = fg
        self.hover_bg = self._darken(bg)
        self.command = command
        self.text = text
        self.font = (FONT, font_size, "bold" if bold else "normal")
        self.w = width
        self.h = height
        self._enabled = True

        self._draw(bg)
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", lambda e: self._on_hover(True))
        self.bind("<Leave>", lambda e: self._on_hover(False))
        self.configure(cursor="hand2")

    def _darken(self, hex_color):
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        r = max(0, r - self.DARKEN_AMOUNT)
        g = max(0, g - self.DARKEN_AMOUNT)
        b = max(0, b - self.DARKEN_AMOUNT)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _draw(self, fill):
        self.delete("all")
        r = self.CORNER_RADIUS
        self.create_oval(0, 0, 2 * r, 2 * r, fill=fill, outline=fill)
        self.create_oval(self.w - 2 * r, 0, self.w, 2 * r, fill=fill, outline=fill)
        self.create_oval(0, self.h - 2 * r, 2 * r, self.h, fill=fill, outline=fill)
        self.create_oval(
            self.w - 2 * r, self.h - 2 * r, self.w, self.h, fill=fill, outline=fill
        )
        self.create_rectangle(r, 0, self.w - r, self.h, fill=fill, outline=fill)
        self.create_rectangle(0, r, self.w, self.h - r, fill=fill, outline=fill)
        self.create_text(
            self.w // 2, self.h // 2, text=self.text, fill=self.fg, font=self.font
        )

    def _on_click(self, event):
        if self._enabled and self.command:
            self.command()

    def _on_hover(self, hovering):
        if self._enabled:
            self._draw(self.hover_bg if hovering else self.bg)

    def set_colors(self, bg, fg=None):
        self.bg = bg
        self.hover_bg = self._darken(bg)
        if fg:
            self.fg = fg
        self._draw(bg)

    def set_text(self, text):
        self.text = text
        self._draw(self.bg)

    def set_enabled(self, enabled):
        self._enabled = enabled
        if enabled:
            self.configure(cursor="hand2")
            self._draw(self.bg)
        else:
            self.configure(cursor="")
            self._draw(self.DISABLED_FILL)


def bind_clipboard(widget):
    def cut(event=None):
        try:
            widget.event_generate("<<Cut>>")
        except Exception:
            pass
        return "break"

    def copy(event=None):
        try:
            widget.event_generate("<<Copy>>")
        except Exception:
            pass
        return "break"

    def paste(event=None):
        try:
            widget.event_generate("<<Paste>>")
        except Exception:
            pass
        return "break"

    def select_all(event=None):
        widget.select_range(0, "end")
        widget.icursor("end")
        return "break"

    for key in ("c", "C"):
        widget.bind(f"<Command-{key}>", copy)
        widget.bind(f"<Control-{key}>", copy)
    for key in ("v", "V"):
        widget.bind(f"<Command-{key}>", paste)
        widget.bind(f"<Control-{key}>", paste)
    for key in ("x", "X"):
        widget.bind(f"<Command-{key}>", cut)
        widget.bind(f"<Control-{key}>", cut)
    for key in ("a", "A"):
        widget.bind(f"<Command-{key}>", select_all)
        widget.bind(f"<Control-{key}>", select_all)

    menu = tk.Menu(widget, tearoff=0)
    menu.add_command(label="Cut", command=cut)
    menu.add_command(label="Copy", command=copy)
    menu.add_command(label="Paste", command=paste)
    menu.add_separator()
    menu.add_command(label="Select All", command=select_all)

    def show_menu(event):
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    widget.bind("<Button-3>", show_menu)
    widget.bind("<Button-2>", show_menu)
    widget.bind("<Control-Button-1>", show_menu)


def make_button(parent, text, bg, fg, command, padx=10, pady=6, font_size=10):
    return tk.Button(
        parent,
        text=text,
        font=(FONT, font_size),
        bg=bg,
        fg=fg,
        activebackground=bg,
        activeforeground=fg,
        relief="flat",
        padx=padx,
        pady=pady,
        cursor="hand2",
        bd=0,
        command=command,
    )


def make_entry(parent, textvariable, font_size=11, bold=False):
    entry = tk.Entry(
        parent,
        textvariable=textvariable,
        font=(FONT, font_size, "bold" if bold else "normal"),
        bg=C["white"],
        fg=C["text_dark"],
        insertbackground=C["text_dark"],
        relief="solid",
        bd=1,
        highlightthickness=1,
        highlightbackground=C["border"],
        highlightcolor=C["blue_accent"],
    )
    bind_clipboard(entry)
    return entry


def make_label(parent, text, font_size=10, bold=False, fg=None, bg=None):
    return tk.Label(
        parent,
        text=text,
        font=(FONT, font_size, "bold" if bold else "normal"),
        fg=fg or C["text_dark"],
        bg=bg or C["page_bg"],
    )


def make_check(parent, text, variable, bg=None, command=None):
    bg = bg or C["page_bg"]
    return tk.Checkbutton(
        parent,
        text=text,
        variable=variable,
        font=(FONT, 10),
        fg=C["text_dark"],
        bg=bg,
        activebackground=bg,
        activeforeground=C["text_dark"],
        selectcolor=C["white"],
        relief="flat",
        command=command,
    )
