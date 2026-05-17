import os
import sys

from .config import APP_NAME, PLATFORM


def _executable_command():
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    return f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"'


def _windows_set(enable):
    import winreg

    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0,
        winreg.KEY_SET_VALUE,
    )
    try:
        if enable:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, _executable_command())
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
    finally:
        winreg.CloseKey(key)


def _windows_check():
    try:
        import winreg

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_READ,
        )
        try:
            winreg.QueryValueEx(key, APP_NAME)
            return True
        finally:
            winreg.CloseKey(key)
    except Exception:
        return False


def _macos_plist_path():
    return os.path.expanduser(
        f"~/Library/LaunchAgents/com.{APP_NAME.lower()}.plist"
    )


def _macos_set(enable):
    plist_path = _macos_plist_path()

    if not enable:
        if os.path.exists(plist_path):
            os.system(f"launchctl unload '{plist_path}'")
            os.remove(plist_path)
        return

    os.makedirs(os.path.dirname(plist_path), exist_ok=True)

    if getattr(sys, "frozen", False):
        args = f"<string>{sys.executable}</string>"
    else:
        args = (
            f"<string>{sys.executable}</string>\n\t\t"
            f"<string>{os.path.abspath(sys.argv[0])}</string>"
        )

    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
    <key>Label</key><string>com.{APP_NAME.lower()}</string>
    <key>ProgramArguments</key><array>
        {args}
    </array>
    <key>RunAtLoad</key><true/>
</dict></plist>"""

    with open(plist_path, "w") as f:
        f.write(plist_content)
    os.system(f"launchctl load '{plist_path}'")


def _macos_check():
    return os.path.exists(_macos_plist_path())


def set_autostart(enable):
    if PLATFORM == "Windows":
        _windows_set(enable)
    elif PLATFORM == "Darwin":
        _macos_set(enable)


def is_autostart():
    if PLATFORM == "Windows":
        return _windows_check()
    if PLATFORM == "Darwin":
        return _macos_check()
    return False
