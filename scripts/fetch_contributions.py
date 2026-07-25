#!/usr/bin/env python3
"""Fetch the public contribution calendar — no GraphQL, no token.

GitHub serves the calendar as plain HTML at
https://github.com/users/<username>/contributions (the same fragment the
profile page embeds). We parse the day cells and the tooltip texts, then
write data/contributions.json with raw days plus derived stats.

Usage:  python scripts/fetch_contributions.py
Requires: requests, beautifulsoup4
"""
import datetime as dt
import json
import os
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = "BornaBoyafraz"
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT = Path(__file__).resolve().parent.parent / "data" / "contributions.json"
INCLUDE_REFRESH_COMMIT = os.environ.get("INCLUDE_REFRESH_COMMIT") == "1"


def fetch_days() -> list[dict]:
    resp = requests.get(URL, headers={"User-Agent": "profile-readme-art"}, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    tooltips = {tt.get("for"): tt.get_text(" ", strip=True)
                for tt in soup.find_all("tool-tip")}

    days = []
    for td in soup.select("td.ContributionCalendar-day[data-date]"):
        text = tooltips.get(td.get("id"), "")
        m = re.match(r"(\d+)\s+contribution", text.replace(",", ""))
        days.append({
            "date": td["data-date"],
            "count": int(m.group(1)) if m else 0,
            "level": int(td.get("data-level", 0)),
        })
    days.sort(key=lambda d: d["date"])
    if not days:
        raise SystemExit("no day cells found — did GitHub change the markup?")
    return days


def account_for_refresh_commit(
    days: list[dict],
    commit_date: dt.date,
    previous_days: list[dict] | None = None,
) -> None:
    """Include the commit that will publish this freshly generated data.

    The workflow fetches GitHub's calendar before its auto-commit exists.
    Without this adjustment, the committed card is permanently one
    contribution behind and can also lag a day behind on streaks. GitHub
    can also briefly return a pre-push calendar, so retain higher counts
    from the previously committed data until the public index catches up.
    """
    previous_by_date = {
        day["date"]: day
        for day in (previous_days or [])
    }
    for day in days:
        previous = previous_by_date.get(day["date"])
        if previous and previous["count"] > day["count"]:
            day["count"] = previous["count"]
            day["level"] = max(day["level"], previous["level"])

    date_string = commit_date.isoformat()
    try:
        today = next(day for day in days if day["date"] == date_string)
    except StopIteration as exc:
        raise SystemExit(f"refresh commit date {date_string} is outside the calendar") from exc

    today["count"] += 1

    # Estimate GitHub's next color level from the thresholds visible in the
    # fetched calendar. The exact count and streak stats do not depend on it.
    thresholds = {
        level: min(day["count"] for day in days if day["level"] == level)
        for level in range(1, 5)
        if any(day["level"] == level for day in days)
    }
    today["level"] = max(
        (level for level, threshold in thresholds.items()
         if today["count"] >= threshold),
        default=max(today["level"], 1),
    )


def derive(days: list[dict], today: dt.date | None = None) -> dict:
    today = today or dt.datetime.now(dt.timezone.utc).date()
    total = sum(d["count"] for d in days)
    best = max(days, key=lambda d: d["count"])

    # Promote the best day(s) to level 5 — the palette's neon top end.
    if best["count"] > 0:
        for d in days:
            if d["count"] == best["count"]:
                d["level"] = 5

    longest = run = 0
    run_start = longest_start = longest_end = None
    for d in days:
        if d["count"] > 0:
            if run == 0:
                run_start = d["date"]
            run += 1
            if run > longest:
                longest = run
                longest_start = run_start
                longest_end = d["date"]
        else:
            run = 0
            run_start = None

    # Current streak counts back from the end; today being empty (so far)
    # shouldn't break it.
    tail = list(reversed(days))
    if tail and tail[0]["count"] == 0 and tail[0]["date"] == today.isoformat():
        tail = tail[1:]
    current = 0
    current_end = current_start = None
    for d in tail:
        if d["count"] == 0:
            break
        if current == 0:
            current_end = d["date"]
        current_start = d["date"]
        current += 1

    months: dict[str, int] = {}
    for d in days:
        months[d["date"][:7]] = months.get(d["date"][:7], 0) + d["count"]

    return {
        "refreshed": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "user": USERNAME,
        "total": total,
        "best": {"date": best["date"], "count": best["count"]},
        "streak_current": current,
        "streak_current_start": current_start,
        "streak_current_end": current_end,
        "streak_longest": longest,
        "streak_longest_start": longest_start,
        "streak_longest_end": longest_end,
        "months": months,
        "days": days,
    }


def main() -> None:
    now = dt.datetime.now(dt.timezone.utc)
    previous_days = []
    if INCLUDE_REFRESH_COMMIT and OUT.exists():
        previous_days = json.loads(OUT.read_text(encoding="utf-8")).get("days", [])
    days = fetch_days()
    if INCLUDE_REFRESH_COMMIT:
        account_for_refresh_commit(days, now.date(), previous_days)
    data = derive(days, now.date())
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1), encoding="utf-8")
    print(f"wrote {OUT} — {data['total']} contributions, "
          f"streak {data['streak_current']}d (longest {data['streak_longest']}d)")


if __name__ == "__main__":
    main()
