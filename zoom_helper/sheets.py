import csv
import io
import urllib.request

from .config import DAYS_EN
from .ssl_setup import SSL_CTX
from .storage import save_schedule


def sheet_url_to_csv(url):
    url = url.strip()
    if not url:
        return ""
    if "output=csv" in url or url.endswith(".csv"):
        return url
    if "/spreadsheets/d/" in url:
        try:
            doc_id = url.split("/spreadsheets/d/")[1].split("/")[0]
            gid = "0"
            if "gid=" in url:
                gid = url.split("gid=")[1].split("&")[0].split("#")[0]
            return (
                f"https://docs.google.com/spreadsheets/d/{doc_id}"
                f"/export?format=csv&gid={gid}"
            )
        except Exception:
            pass
    return url


def _parse_row(row):
    row = {k.strip().lower(): (v or "").strip() for k, v in row.items() if k}
    title = row.get("title", "")
    url = row.get("url", "")
    time_value = row.get("time", "")
    if not title or not url or not time_value:
        return None

    days = [d.strip().lower() for d in row.get("days", "").split(",") if d.strip()]
    days = [d for d in days if d in DAYS_EN] or DAYS_EN[:]

    active_raw = row.get("active", "yes").lower()
    active = active_raw in ("yes", "y", "true", "1")

    return {
        "title": title,
        "url": url,
        "time": time_value,
        "days": days,
        "active": active,
    }


def sync_from_sheets(csv_url, timeout=15):
    try:
        request = urllib.request.Request(
            csv_url, headers={"User-Agent": "ZoomHelper/1.0"}
        )
        with urllib.request.urlopen(request, timeout=timeout, context=SSL_CTX) as resp:
            data = resp.read().decode("utf-8-sig")
    except Exception as e:
        return 0, str(e)

    try:
        reader = csv.DictReader(io.StringIO(data))
        entries = [parsed for row in reader if (parsed := _parse_row(row))]
        save_schedule(entries)
        return len(entries), None
    except Exception as e:
        return 0, f"Failed to parse spreadsheet: {e}"
