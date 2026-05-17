import threading
import tkinter as tk
from datetime import datetime
from tkinter import messagebox

from .autostart import is_autostart, set_autostart
from .config import COLORS as C
from .config import DAYS_EN, DAYS_SHORT, FONT
from .icons import apply_icon
from .sheets import sheet_url_to_csv, sync_from_sheets
from .storage import load_schedule, load_settings, save_settings
from .widgets import make_button, make_check, make_entry, make_label


class AdminWindow(tk.Toplevel):
    WINDOW_GEOMETRY = "520x600"

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("⚙ Admin Settings")
        self.resizable(False, False)
        self.geometry(self.WINDOW_GEOMETRY)
        self.configure(bg=C["page_bg"])
        apply_icon(self)

        self.settings = load_settings()
        self._build()

    def _build(self):
        header = tk.Frame(self, bg=C["warning_bg"], pady=12)
        header.pack(fill="x")
        tk.Label(
            header,
            text="⚙ Admin Mode",
            font=(FONT, 14, "bold"),
            fg=C["warning"],
            bg=C["warning_bg"],
        ).pack()

        make_label(self, "Google Sheets URL:", bold=True).pack(
            anchor="w", padx=20, pady=(16, 4)
        )

        self.url_var = tk.StringVar(value=self.settings.get("sheet_url", ""))
        make_entry(self, self.url_var).pack(fill="x", padx=20)

        make_label(
            self,
            "Columns: title, url, time, days, active",
            font_size=9,
            fg=C["text_muted"],
        ).pack(anchor="w", padx=20, pady=(4, 8))

        buttons = tk.Frame(self, bg=C["page_bg"])
        buttons.pack(fill="x", padx=20, pady=(0, 12))
        make_button(
            buttons, "💾 Save", C["blue_btn"], "white", self._save_url, padx=14, pady=8
        ).pack(side="left", padx=(0, 8))
        make_button(
            buttons,
            "🔄 Refresh Now",
            C["green_btn"],
            "white",
            self._sync_now,
            padx=14,
            pady=8,
        ).pack(side="left")

        self.status = tk.Label(
            self,
            text=self._status_text(),
            font=(FONT, 9),
            fg=C["text_muted"],
            bg=C["page_bg"],
            justify="left",
            wraplength=480,
        )
        self.status.pack(anchor="w", padx=20, pady=(0, 12))

        tk.Frame(self, height=1, bg=C["border"]).pack(fill="x", padx=20, pady=8)

        make_label(self, "Loaded schedule:", bold=True).pack(
            anchor="w", padx=20, pady=(4, 4)
        )

        list_frame = tk.Frame(self, bg=C["page_bg"])
        list_frame.pack(fill="both", expand=True, padx=20)
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        self.listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            font=(FONT, 9),
            height=6,
            bg=C["white"],
            fg=C["text_dark"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=C["border"],
        )
        self.listbox.pack(fill="both", expand=True)
        scrollbar.config(command=self.listbox.yview)
        self._refresh_list()

        self.autostart_var = tk.BooleanVar(value=is_autostart())
        make_check(
            self,
            "Launch automatically on system startup",
            self.autostart_var,
            command=self._toggle_autostart,
        ).pack(padx=20, anchor="w", pady=(10, 12))

    def _status_text(self):
        url = self.settings.get("sheet_url", "")
        last_sync = self.settings.get("last_sync", "")

        if not url:
            return "URL is not configured."
        if last_sync:
            return f"✅ Connected. Last sync at {last_sync}."
        return "✅ Connected. Click 'Refresh Now'."

    def _refresh_list(self):
        self.listbox.delete(0, "end")
        for entry in load_schedule():
            days = ",".join(
                DAYS_SHORT[DAYS_EN.index(d)]
                for d in entry.get("days", [])
                if d in DAYS_EN
            )
            marker = "✅" if entry.get("active", True) else "⬜"
            self.listbox.insert(
                "end",
                f"  {marker}  {entry['time']}  |  {entry['title']}  |  {days}",
            )

    def _save_url(self):
        value = self.url_var.get().strip()
        if not value.startswith("http"):
            messagebox.showwarning("Error", "Please enter a valid URL.", parent=self)
            return

        self.settings["sheet_url"] = sheet_url_to_csv(value)
        save_settings(self.settings)
        self.parent.settings = load_settings()
        self._sync_now()

    def _sync_now(self):
        url = self.settings.get("sheet_url", "")
        if not url:
            messagebox.showinfo("Error", "Save the URL first.", parent=self)
            return

        self.status.config(text="⏳ Loading...")
        threading.Thread(target=self._sync_worker, args=(url,), daemon=True).start()

    def _sync_worker(self, url):
        count, err = sync_from_sheets(url)
        self.after(0, lambda: self._after_sync(count, err))

    def _after_sync(self, count, err):
        if err:
            self.status.config(text=f"❌ Error: {err}")
            messagebox.showerror("Sync Error", err, parent=self)
            return

        self.settings["last_sync"] = datetime.now().strftime("%H:%M")
        save_settings(self.settings)
        self.status.config(
            text=f"✅ Loaded: {count} meetings. Time: {self.settings['last_sync']}"
        )
        self._refresh_list()

    def _toggle_autostart(self):
        try:
            set_autostart(self.autostart_var.get())
        except Exception as ex:
            messagebox.showerror("Error", str(ex), parent=self)
