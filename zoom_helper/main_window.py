import threading
import time
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox

from .config import (
    APP_TITLE,
    AUTO_JOIN_SECONDS,
    COLORS as C,
    DAYS_SHORT,
    FONT,
    HEADER_CLICK_THRESHOLD,
    HEADER_CLICK_WINDOW_SEC,
    SYNC_INTERVAL_SEC,
)
from .icons import apply_icon
from .scheduler import next_lecture, open_zoom
from .sheets import sync_from_sheets
from .storage import load_settings, save_settings
from .widgets import HoverButton


class App(tk.Tk):
    WINDOW_GEOMETRY = "460x560"
    TICK_INTERVAL_MS = 1000
    EMPTY_TICK_INTERVAL_MS = 5000
    UNCONFIGURED_TICK_INTERVAL_MS = 2000

    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.resizable(False, False)
        self.geometry(self.WINDOW_GEOMETRY)
        self.configure(bg=C["page_bg"])
        apply_icon(self)

        self.settings = load_settings()
        self.current_lecture = None
        self.current_lecture_dt = None
        self._fired = set()
        self._header_clicks = []

        self._build_ui()
        self._setup_admin_shortcut()
        self._auto_sync_loop()
        self._tick()

    def _setup_admin_shortcut(self):
        for combo in (
            "<F12>",
            "<Control-Shift-A>",
            "<Control-Shift-a>",
            "<Command-Shift-A>",
            "<Command-Shift-a>",
        ):
            self.bind_all(combo, lambda e: self._open_admin())

    def _build_ui(self):
        header = tk.Frame(self, bg=C["header_blue"], height=70)
        header.pack(fill="x")
        header.pack_propagate(False)

        header_label = tk.Label(
            header,
            text="📹  Zoom Helper",
            font=(FONT, 17, "bold"),
            fg="white",
            bg=C["header_blue"],
            cursor="arrow",
        )
        header_label.pack(expand=True)

        header.bind("<Button-1>", self._on_header_click)
        header_label.bind("<Button-1>", self._on_header_click)

        outer = tk.Frame(self, bg=C["page_bg"])
        outer.pack(fill="both", expand=True, padx=20, pady=20)

        self.card = tk.Frame(
            outer,
            bg=C["card_bg"],
            highlightthickness=2,
            highlightbackground=C["card_border"],
            highlightcolor=C["card_border"],
        )
        self.card.pack(fill="both", expand=True)

        inner = tk.Frame(self.card, bg=C["card_bg"])
        inner.pack(fill="both", expand=True, padx=24, pady=22)

        self.label_subtitle = tk.Label(
            inner,
            text="Next meeting:",
            font=(FONT, 13),
            fg=C["text_label"],
            bg=C["card_bg"],
        )
        self.label_subtitle.pack(anchor="center", pady=(0, 6))

        self.label_title = tk.Label(
            inner,
            text="—",
            font=(FONT, 20, "bold"),
            fg=C["text_dark"],
            bg=C["card_bg"],
            wraplength=340,
            justify="center",
        )
        self.label_title.pack(anchor="center", pady=(0, 14))

        self.label_when = tk.Label(
            inner, text="", font=(FONT, 13), fg=C["blue_dk"], bg=C["card_bg"]
        )
        self.label_when.pack(anchor="center", pady=(0, 4))

        self.label_countdown = tk.Label(
            inner,
            text="",
            font=(FONT, 26, "bold"),
            fg=C["blue_accent"],
            bg=C["card_bg"],
        )
        self.label_countdown.pack(anchor="center", pady=(6, 18))

        self.join_btn = HoverButton(
            inner,
            text="▶  Join Zoom Meeting",
            bg=C["blue_btn"],
            fg="white",
            command=self._join_now,
            width=340,
            height=54,
            font_size=15,
            bold=True,
        )
        self.join_btn.pack(anchor="center")

        self.auto_msg = tk.Label(
            inner,
            text="",
            font=(FONT, 11),
            fg=C["warning"],
            bg=C["card_bg"],
            wraplength=340,
            justify="center",
        )
        self.auto_msg.pack(anchor="center", pady=(12, 0))

    def _tick(self):
        if not self.settings.get("sheet_url"):
            self._render_unconfigured()
            self.after(self.UNCONFIGURED_TICK_INTERVAL_MS, self._tick)
            return

        entry, dt = next_lecture()
        self.current_lecture = entry
        self.current_lecture_dt = dt

        if not entry:
            self._render_empty()
            self.after(self.EMPTY_TICK_INTERVAL_MS, self._tick)
            return

        self._render_lecture(entry, dt)
        self.after(self.TICK_INTERVAL_MS, self._tick)

    def _render_unconfigured(self):
        self.label_subtitle.config(text="Not configured yet")
        self.label_title.config(text="Add your schedule\nspreadsheet URL")
        self.label_when.config(text="")
        self.label_countdown.config(text="")
        self.join_btn.set_enabled(False)
        self.auto_msg.config(
            text="Open settings with F12\nor click the blue header 5 times",
            fg=C["text_muted"],
        )

    def _render_empty(self):
        self.label_subtitle.config(text="Schedule is empty")
        self.label_title.config(text="No meetings right now")
        self.label_when.config(text="")
        self.label_countdown.config(text="")
        self.join_btn.set_enabled(False)
        self.auto_msg.config(text="")

    def _render_lecture(self, entry, dt):
        self.label_subtitle.config(text="Next meeting:")
        self.label_title.config(text=entry["title"])
        self.label_when.config(text=self._format_when(dt))

        now = datetime.now()
        diff_sec = (dt - now).total_seconds()

        if diff_sec > 3600:
            self._render_far_future(diff_sec)
        elif diff_sec > AUTO_JOIN_SECONDS:
            self._render_near_future(diff_sec)
        elif diff_sec > 0:
            self._render_imminent(int(diff_sec))
        else:
            self._handle_meeting_started(entry, dt, diff_sec)

    @staticmethod
    def _format_when(dt):
        now = datetime.now()
        if dt.date() == now.date():
            return f"Today at {dt.strftime('%H:%M')}"
        if dt.date() == now.date() + timedelta(days=1):
            return f"Tomorrow at {dt.strftime('%H:%M')}"
        return f"{DAYS_SHORT[dt.weekday()]}, {dt.strftime('%b %d at %H:%M')}"

    def _render_far_future(self, diff_sec):
        hours = int(diff_sec // 3600)
        minutes = int((diff_sec % 3600) // 60)
        self.label_countdown.config(
            text=f"⏱  in {hours}h {minutes}m", fg=C["blue_accent"]
        )
        self.join_btn.set_enabled(True)
        self.join_btn.set_colors(C["blue_btn"], "white")
        self.auto_msg.config(text="")

    def _render_near_future(self, diff_sec):
        minutes = int(diff_sec // 60)
        seconds = int(diff_sec % 60)
        text = f"⏱  in {minutes}m {seconds}s" if minutes > 0 else f"⏱  in {seconds}s"
        self.label_countdown.config(text=text, fg=C["blue_accent"])
        self.join_btn.set_enabled(True)
        self.join_btn.set_colors(C["blue_btn"], "white")
        self.auto_msg.config(text="")

    def _render_imminent(self, seconds_left):
        self.label_countdown.config(text=f"⏱  {seconds_left}s", fg=C["warning"])
        self.auto_msg.config(
            text=f"Auto-joining in {seconds_left} seconds.\nOr click the button now.",
            fg=C["warning"],
        )
        self.join_btn.set_colors(C["green_btn"], "white")

    def _handle_meeting_started(self, entry, dt, diff_sec):
        key = (dt.date().isoformat(), entry["title"], entry["time"])

        if key not in self._fired and diff_sec > -60:
            self._fired.add(key)
            self._auto_join_fire()
            return

        mins_ago = int(-diff_sec // 60)
        self.label_countdown.config(
            text=f"🔴 In progress ({mins_ago}m)", fg=C["red_dk"]
        )
        self.auto_msg.config(
            text="Click the button to join the ongoing meeting.", fg=C["red_dk"]
        )
        self.join_btn.set_enabled(True)
        self.join_btn.set_colors(C["green_btn"], "white")

    def _auto_join_fire(self):
        if not self.current_lecture:
            return
        open_zoom(self.current_lecture)
        self.deiconify()
        self.lift()
        self.auto_msg.config(
            text="✅ Zoom opened! If the window didn't appear,\nclick the button again."
        )
        self.label_countdown.config(text="✅ Connecting...", fg=C["green_btn"])

    def _join_now(self):
        if not self.current_lecture:
            messagebox.showinfo(APP_TITLE, "No meetings right now.")
            return

        if self.current_lecture_dt:
            key = (
                self.current_lecture_dt.date().isoformat(),
                self.current_lecture["title"],
                self.current_lecture["time"],
            )
            self._fired.add(key)

        open_zoom(self.current_lecture)
        self.auto_msg.config(text="✅ Opening Zoom...", fg=C["green_btn"])

    def _auto_sync_loop(self):
        url = self.settings.get("sheet_url", "")
        if url:
            threading.Thread(target=self._sync_worker, args=(url,), daemon=True).start()
        self.after(SYNC_INTERVAL_SEC * 1000, self._auto_sync_loop)

    def _sync_worker(self, url):
        count, err = sync_from_sheets(url)
        if not err:
            self.settings["last_sync"] = datetime.now().strftime("%H:%M")
            save_settings(self.settings)

    def _open_admin(self):
        from .admin_window import AdminWindow

        AdminWindow(self)

    def _on_header_click(self, event):
        now = time.time()
        self._header_clicks = [
            t for t in self._header_clicks if now - t < HEADER_CLICK_WINDOW_SEC
        ]
        self._header_clicks.append(now)
        if len(self._header_clicks) >= HEADER_CLICK_THRESHOLD:
            self._header_clicks = []
            self._open_admin()
