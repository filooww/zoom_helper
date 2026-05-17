import json
import os
import sys


def app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(sys.argv[0]))


def schedule_path():
    return os.path.join(app_dir(), "schedule.json")


def settings_path():
    return os.path.join(app_dir(), "settings.json")


def _read_json(path, fallback):
    if not os.path.exists(path):
        return fallback
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return fallback


def _write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_schedule():
    return _read_json(schedule_path(), [])


def save_schedule(data):
    _write_json(schedule_path(), data)


def load_settings():
    return _read_json(settings_path(), {})


def save_settings(data):
    _write_json(settings_path(), data)
