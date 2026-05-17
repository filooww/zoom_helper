import webbrowser
from datetime import datetime, timedelta

from .config import DAYS_EN
from .storage import load_schedule


PAST_GRACE_PERIOD_SEC = 300


def next_lecture():
    schedule = load_schedule()
    now = datetime.now()
    best_entry = None
    best_dt = None

    for entry in schedule:
        if not entry.get("active", True):
            continue

        try:
            meeting_time = datetime.strptime(entry["time"], "%H:%M").time()
        except ValueError:
            continue

        days = entry.get("days", DAYS_EN)

        for day_offset in range(8):
            candidate_date = now.date() + timedelta(days=day_offset)
            day_code = DAYS_EN[candidate_date.weekday()]
            if day_code not in days:
                continue

            candidate_dt = datetime.combine(candidate_date, meeting_time)
            if (candidate_dt - now).total_seconds() < -PAST_GRACE_PERIOD_SEC:
                continue

            if best_dt is None or candidate_dt < best_dt:
                best_entry, best_dt = entry, candidate_dt
            break

    return best_entry, best_dt


def open_zoom(entry):
    url = entry.get("url", "").strip()
    if url:
        webbrowser.open(url)
