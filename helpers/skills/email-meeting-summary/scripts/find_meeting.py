#!/usr/bin/env python3
"""Find calendar events in a ±N-day window, optionally filtered by keyword.

When a keyword matches multiple events (e.g. a recurring meeting), the script
picks the single most relevant occurrence:

  1. If --date is given, the event on that date.
  2. An event that started today (if any).
  3. The most recent past event (if no event is today).
  4. The soonest future event (if nothing has happened yet).

If no keyword is given, all events in the window are returned so the caller
can present a list and ask the user to choose.

Always outputs a calendar events list JSON object with an "items" array.
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone


def run_gws(*args: str) -> dict:
    try:
        result = subprocess.run(["gws", *args], capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired as e:
        stdout = (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        stderr = (e.stderr or b"").decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
        print(f"gws timed out after {e.timeout}s", file=sys.stderr)
        if stdout:
            print(f"stdout: {stdout.strip()}", file=sys.stderr)
        if stderr:
            print(f"stderr: {stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    except (OSError, subprocess.SubprocessError) as e:
        print(f"Error running gws: {e}", file=sys.stderr)
        sys.exit(1)
    stdout = "\n".join(
        line for line in result.stdout.splitlines() if not line.startswith("Using keyring")
    ).strip()
    if result.returncode != 0:
        print(f"gws error: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    if not stdout:
        print("gws returned no output", file=sys.stderr)
        sys.exit(1)
    return json.loads(stdout)


def event_start(event: dict) -> datetime:
    """Return the start time of an event as an aware datetime (UTC)."""
    raw = event.get("start", {}).get("dateTime") or event.get("start", {}).get("date", "")
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def pick_best(items: list[dict], now: datetime, date: str | None = None) -> list[dict]:
    """Given a list of matching events, return the single best one.

    Preference order:
      1. If date (YYYY-MM-DD) is given, the event on that date.
      2. An event that started today.
      3. The most recent past event.
    """
    if date:
        on_date = [e for e in items if event_start(e).astimezone().strftime("%Y-%m-%d") == date]
        if on_date:
            return [on_date[0]]

    today_str = now.astimezone().strftime("%Y-%m-%d")
    today_events = [
        e for e in items if event_start(e).astimezone().strftime("%Y-%m-%d") == today_str
    ]
    if today_events:
        return [today_events[0]]

    past = [e for e in items if event_start(e) <= now]
    if past:
        return [max(past, key=event_start)]

    return items


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="How many days back to search (default: 7)",
    )
    parser.add_argument(
        "keyword",
        nargs="?",
        default="",
        help="Optional keyword to filter events by title/description",
    )
    parser.add_argument(
        "--date",
        default="",
        metavar="YYYY-MM-DD",
        help="Restrict to a specific date when multiple occurrences match",
    )
    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    time_min = (now - timedelta(days=args.days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    time_max = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    params: dict = {
        "calendarId": "primary",
        "timeMin": time_min,
        "timeMax": time_max,
        "singleEvents": True,
        "orderBy": "startTime",
    }
    if args.keyword:
        params["q"] = args.keyword

    data = run_gws("calendar", "events", "list", "--params", json.dumps(params))
    items: list[dict] = data.get("items", [])

    # When a keyword was given and multiple events matched, pick the best one.
    if args.keyword and len(items) > 1:
        items = pick_best(items, now, date=args.date or None)

    data["items"] = items
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
