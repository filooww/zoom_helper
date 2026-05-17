# 📹 Zoom Helper

A lightweight desktop app that automatically opens Zoom meetings on schedule.
The schedule is stored in a shared Google Spreadsheet, so it can be managed
centrally for multiple computers at once.

---

## 📋 Features

- Displays the next upcoming meeting with a live countdown
- **10 seconds before start** — shows a warning "Joining in X sec"
- **At meeting time** — automatically opens the Zoom URL
- **Join now** button for joining ahead of time
- Syncs with the Google Spreadsheet every 5 minutes
- Optional autostart at system boot
- Works on Windows and macOS

---

## 🖼 Interface

The main window shows:
1. Title of the next meeting
2. When it happens (e.g. "Today at 14:00")
3. A countdown timer
4. A large "Join Zoom Meeting" button

If there are no upcoming meetings — shows "No meetings right now".

On first launch, when no spreadsheet URL is configured yet, the app shows
"Not configured yet — add your schedule spreadsheet URL" and instructions
on how to open the settings.

---

## ⚙️ Architecture

```
┌──────────────────┐       reads CSV every 5 minutes
│ Google Sheets    │ ◀───────────────────────────────┐
│ (shared sheet)   │                                  │
└────────┬─────────┘                                  │
         │                                            │
         │ edited by admin                   ┌───────┴────────┐
         │                                    │ Zoom Helper    │
         ▼                                    │ on user PCs    │
┌──────────────────┐                          └────────────────┘
│   Administrator  │
└──────────────────┘
```

- Schedule lives in one shared Google Spreadsheet
- Apps on user machines pull updates automatically
- No backend server or API required

---

## 📦 Project Structure

```
zoom_helper/
├── main.py                    — entry point
├── README.md
├── assets/                    — icons and resources
│   ├── icon.ico               — Windows icon
│   ├── icon.png               — fallback PNG (256x256)
│   ├── icon_1024.png          — high-res for macOS
│   └── icon.iconset/          — source for .icns generation
└── zoom_helper/               — application package
    ├── __init__.py
    ├── config.py              — colors, fonts, constants
    ├── ssl_setup.py           — SSL context with certifi fallback
    ├── storage.py             — schedule.json and settings.json
    ├── sheets.py              — Google Sheets CSV sync
    ├── autostart.py           — Windows/macOS autostart manager
    ├── scheduler.py           — next meeting lookup, open Zoom URL
    ├── icons.py               — load and apply window icons
    ├── widgets.py             — HoverButton, entries, clipboard
    ├── main_window.py         — main App window
    └── admin_window.py        — admin settings window
```

Module responsibilities:

| Module | Responsibility |
|---|---|
| `config` | Constants: colors, fonts, day names, timing intervals |
| `ssl_setup` | Build a working SSL context (handles macOS cert issues) |
| `storage` | Read/write JSON files next to the executable |
| `sheets` | Convert Sheets URL to CSV, fetch and parse rows |
| `autostart` | Toggle and detect autostart on Windows (registry) and macOS (LaunchAgent) |
| `scheduler` | Compute the next upcoming meeting from the cached schedule |
| `icons` | Apply platform-specific window icons |
| `widgets` | Reusable UI helpers — buttons, entries with clipboard support |
| `main_window` | Main `App(tk.Tk)` window with countdown and join button |
| `admin_window` | `AdminWindow(tk.Toplevel)` with URL input and autostart toggle |

---

## 🚀 Setup

### Step 1. Create the Google Spreadsheet

1. Open https://sheets.google.com → new spreadsheet
2. Create the following columns in the first row:

| title | url | time | days | active |
|---|---|---|---|---|
| Morning Standup | https://zoom.us/j/123... | 10:00 | mon,tue,wed,thu,fri | yes |
| Weekly Review | https://zoom.us/j/456... | 16:00 | fri | yes |

**Column reference:**
- **title** — meeting name
- **url** — full Zoom URL (with password if any)
- **time** — start time in `HH:MM` format (24-hour)
- **days** — weekdays, comma-separated, no spaces: `mon,wed,fri`
- **active** — `yes` or `no` (use `no` to temporarily disable a row)

3. Click **Share** → change to **"Anyone with the link" → Viewer**
4. Copy the link — you'll paste it into the app later

**Day codes:** `mon` `tue` `wed` `thu` `fri` `sat` `sun`

---

### Step 2. Install Python and dependencies

Download Python 3.10+ from https://www.python.org/downloads/

⚠️ On Windows, check the **"Add Python to PATH"** option during install.

In your terminal / command prompt:

```bash
pip install pyinstaller certifi
```

`certifi` is required for HTTPS to Google Sheets, especially on macOS.

---

### Step 3. Run from source

```bash
python3 main.py
```

To open the admin panel immediately on launch:

```bash
python3 main.py --admin
```

---

### Step 4. Build the executable

⚠️ **Note:** PyInstaller does not support cross-compilation. To get a `.exe`,
you must build **on a Windows machine**. On macOS the output is a Mac binary,
not a Windows `.exe`.

#### On Windows

```bash
pyinstaller --onefile --windowed --collect-all certifi ^
  --icon assets/icon.ico ^
  --add-data "assets;assets" ^
  --name ZoomHelper main.py
```

Output: `dist\ZoomHelper.exe`

#### On macOS

First, generate the `.icns` file from the iconset (one-time):

```bash
iconutil -c icns assets/icon.iconset -o assets/icon.icns
```

Then build:

```bash
pyinstaller --onefile --windowed --collect-all certifi \
  --icon assets/icon.icns \
  --add-data "assets:assets" \
  --name ZoomHelper main.py
```

Output: `dist/ZoomHelper`

#### Flags

- `--onefile` — bundle everything into a single executable
- `--windowed` — no terminal window
- `--collect-all certifi` — embed SSL certificates (required)
- `--icon` — set the application icon
- `--add-data` — bundle the `assets` folder so the icon shows in the window too

PyInstaller automatically picks up all modules from the `zoom_helper` package
imported via `main.py`, so no extra flags are needed for code.

---

### Step 5. Deploy to user machines

1. Copy `ZoomHelper.exe` (or the Mac binary) to the user's computer
2. Launch it — the main window appears with the "Not configured" message
3. Press **F12** to open the admin panel
4. Paste the Google Sheets URL → click **💾 Save**
5. Verify the schedule loads — meetings should appear in the list
6. Tick **"Launch automatically on system startup"**
7. Close the admin window — the app keeps running in the background

---

## 🔧 Admin Panel

Hidden settings panel, not accessible to regular users. Three ways to open:

1. **F12** — keyboard shortcut
2. **Ctrl+Shift+A** (Windows) / **Cmd+Shift+A** (Mac)
3. **5 clicks** on the blue header (within 3 seconds)

What you can do in the admin panel:

- **Google Sheets URL** — paste/edit the URL, save it
- **💾 Save** — saves URL and triggers immediate sync
- **🔄 Refresh Now** — forces a sync without changing the URL
- **Loaded schedule** — list of all meetings currently in the cache
- **Launch automatically on system startup** — toggles autostart

The URL input field supports standard clipboard shortcuts:
- **Cmd+C / Ctrl+C** — copy
- **Cmd+V / Ctrl+V** — paste
- **Cmd+X / Ctrl+X** — cut
- **Cmd+A / Ctrl+A** — select all
- Right-click (or Ctrl+Click on Mac) — context menu with Cut/Copy/Paste

---

## 📂 Runtime Files

The app creates two files next to itself:

- **`schedule.json`** — local schedule cache (works offline if internet drops)
- **`settings.json`** — saved settings (sheet URL, last sync time)

Both can be safely deleted — the app will recreate them.

---

## ❗ Troubleshooting

### Zoom doesn't open

- Make sure the URL in the spreadsheet starts with `https://`
- Zoom Desktop Client must be installed
- The system clock must be set correctly

### SSL CERTIFICATE_VERIFY_FAILED error (macOS)

```bash
pip3 install certifi
```

When building the executable, always use the `--collect-all certifi` flag.

### "Network error" when syncing

- Check your internet connection
- Open the spreadsheet URL (with `/edit` at the end) in an incognito browser
  window — the sheet should load without requiring login
- In the admin panel, click "🔄 Refresh Now" to see the exact error

### App doesn't start at boot

- Open the admin panel and toggle the autostart checkbox
- On Windows, antivirus may block the executable — add it to exclusions

### Windows Defender removes the .exe

Unsigned executables built with PyInstaller are sometimes flagged as
suspicious. Possible solutions:

- Add the file to Windows Defender exclusions
- Sign the .exe with a code-signing certificate (paid)
- Use an installer (NSIS, Inno Setup) — reduces false positives

### Paste (Cmd+V) doesn't work in the URL field

Try right-clicking the field → "Paste" from the context menu.
Both keyboard shortcuts and the menu are built in.

---

## 📝 Changing the schedule

1. Open your Google Spreadsheet
2. Add, edit, or remove rows
3. Changes propagate to all running apps within 5 minutes

No need to rebuild or redistribute the executable.

---

## 🎯 Technical Details

- **Language:** Python 3.10+
- **GUI:** tkinter (standard library)
- **Networking:** urllib + certifi
- **Platforms:** Windows 10/11, macOS 11+
- **Executable size:** 10–15 MB
- **Memory usage:** ~50 MB
- **Network traffic:** 2–5 KB every 5 minutes (one GET to Google Sheets)
- **Dev dependencies:** `certifi`, `pyinstaller`
- **User dependencies:** a browser that handles Zoom URLs
