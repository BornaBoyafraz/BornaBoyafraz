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
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = "BornaBoyafraz"
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT = Path(__file__).resolve().parent.parent / "data" / "contributions.json"


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


def derive(days: list[dict]) -> dict:
    total = sum(d["count"] for d in days)
    best = max(days, key=lambda d: d["count"])

    # Promote the best day(s) to level 5 — the palette's neon top end.
    if best["count"] > 0:
        for d in days:
            if d["count"] == best["count"]:
                d["level"] = 5

    longest = current = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)
    # Current streak counts back from the end; today being empty (so far)
    # shouldn't break it.
    tail = list(reversed(days))
    if tail and tail[0]["count"] == 0 and tail[0]["date"] == dt.date.today().isoformat():
        tail = tail[1:]
    for d in tail:
        if d["count"] == 0:
            break
        current += 1

    months: dict[str, int] = {}
    for d in days:
        months[d["date"][:7]] = months.get(d["date"][:7], 0) + d["count"]

    return {
        "user": USERNAME,
        "fetched": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "total": total,
        "best": {"date": best["date"], "count": best["count"]},
        "streak_current": current,
        "streak_longest": longest,
        "months": months,
        "days": days,
    }


def main() -> None:
    data = derive(fetch_days())
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1), encoding="utf-8")
    print(f"wrote {OUT} — {data['total']} contributions, "
          f"streak {data['streak_current']}d (longest {data['streak_longest']}d)")


if __name__ == "__main__":
    main()
