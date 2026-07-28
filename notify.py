"""
Codeforces -> Discord contest reminder bot.

What it does:
1. Calls the Codeforces API (contest.list) to get all contests.
2. Filters down to contests that haven't started yet ("BEFORE" phase).
3. Skips any contest whose start time is further away than REMIND_WINDOW_HOURS
   (so you don't get spammed months in advance).
4. Skips any contest it has already announced (tracked in notified.json).
5. Posts an embed to your Discord webhook for each newly-in-window contest.
6. Saves the updated "already notified" list back to notified.json.

Designed to be run on a schedule (e.g. GitHub Actions cron). Since Actions
runs are stateless, notified.json is committed back to the repo by the
workflow after each run so the bot remembers what it already posted.
"""

import json
import os
import sys
from pathlib import Path

import requests

CF_API_URL = "https://codeforces.com/api/contest.list"
STATE_FILE = Path(__file__).parent / "notified.json"

# How far ahead (in hours) a contest needs to be before we start reminding
# about it. 48 means: start posting reminders once a contest is within 2 days.
REMIND_WINDOW_HOURS = int(os.environ.get("REMIND_WINDOW_HOURS", "48"))


def load_notified_ids() -> set[int]:
    if not STATE_FILE.exists():
        return set()
    try:
        data = json.loads(STATE_FILE.read_text())
        return set(data.get("notified", []))
    except (json.JSONDecodeError, OSError):
        return set()


def save_notified_ids(ids: set[int]) -> None:
    STATE_FILE.write_text(json.dumps({"notified": sorted(ids)}, indent=2))


def fetch_upcoming_contests() -> list[dict]:
    resp = requests.get(CF_API_URL, params={"gym": "false"}, timeout=15)
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("status") != "OK":
        raise RuntimeError(f"Codeforces API error: {payload}")
    return [c for c in payload["result"] if c["phase"] == "BEFORE"]


def build_embed(contest: dict) -> dict:
    start_unix = contest["startTimeSeconds"]
    duration_min = contest["durationSeconds"] // 60
    url = f"https://codeforces.com/contests/{contest['id']}"
    return {
        "title": contest["name"],
        "url": url,
        "color": 0x1F8ACB,
        "fields": [
            {
                "name": "Starts",
                # Discord renders <t:UNIX:R> as a live relative countdown,
                # e.g. "in 5 hours", localized to each viewer's timezone.
                "value": f"<t:{start_unix}:F> (<t:{start_unix}:R>)",
                "inline": False,
            },
            {
                "name": "Duration",
                "value": f"{duration_min // 60}h {duration_min % 60}m",
                "inline": True,
            },
            {
                "name": "Type",
                "value": contest.get("type", "n/a"),
                "inline": True,
            },
        ],
    }


def post_to_discord(webhook_url: str, contest: dict) -> None:
    payload = {"embeds": [build_embed(contest)]}
    resp = requests.post(webhook_url, json=payload, timeout=15)
    # Discord returns 204 No Content on success.
    if resp.status_code >= 300:
        raise RuntimeError(
            f"Discord webhook failed ({resp.status_code}): {resp.text}"
        )


def main() -> int:
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("ERROR: DISCORD_WEBHOOK_URL env var is not set.", file=sys.stderr)
        return 1

    notified = load_notified_ids()
    upcoming = fetch_upcoming_contests()

    now_cutoff_seconds = REMIND_WINDOW_HOURS * 3600
    import time
    now = int(time.time())

    to_announce = [
        c
        for c in upcoming
        if c["id"] not in notified
        and (c["startTimeSeconds"] - now) <= now_cutoff_seconds
    ]

    # Announce soonest-starting contests first.
    to_announce.sort(key=lambda c: c["startTimeSeconds"])

    if not to_announce:
        print("No new contests to announce.")
        return 0

    for contest in to_announce:
        print(f"Announcing: {contest['name']} ({contest['id']})")
        post_to_discord(webhook_url, contest)
        notified.add(contest["id"])

    save_notified_ids(notified)
    print(f"Announced {len(to_announce)} contest(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
