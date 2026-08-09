#!/usr/bin/env python3
"""Collect profile stats straight from the GitHub API into data/github-stats.json.

The public github-readme-stats instances keep going down or hitting their
shared rate limit, which leaves broken "Something went wrong" cards on the
profile. This fetches the same numbers ourselves so the cards are ours.

Auth: GITHUB_TOKEN (Actions supplies one automatically) or GH_TOKEN. Without
a token the REST calls still work at 60/hr, which is enough to run locally.

Usage:  python scripts/fetch_github_stats.py
"""
import json
import os
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

USERNAME = "BornaBoyafraz"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "github-stats.json"
API = "https://api.github.com"

TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")


def get(path: str):
    req = urllib.request.Request(
        path if path.startswith("http") else f"{API}{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "profile-readme-stats",
            **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def all_repos() -> list[dict]:
    repos, page = [], 1
    while True:
        batch = get(f"/users/{USERNAME}/repos?per_page=100&type=owner&page={page}")
        repos.extend(batch)
        if len(batch) < 100:
            return repos
        page += 1


def language_bytes(repos: list[dict]) -> dict[str, int]:
    """Byte counts per language, which is what makes the split honest —
    counting repos would let a one-file project outweigh a real one."""
    totals: Counter[str] = Counter()
    for repo in repos:
        try:
            for lang, count in get(f"/repos/{USERNAME}/{repo['name']}/languages").items():
                totals[lang] += count
        except urllib.error.HTTPError:
            continue        # empty repo, or the listing raced a deletion
    return dict(totals.most_common())


def commit_count() -> int | None:
    """Search API is rate limited far more tightly than REST (30/hr), so a
    failure here is expected and must not take the whole card down."""
    try:
        return get(f"/search/commits?q=author:{USERNAME}&per_page=1")["total_count"]
    except (urllib.error.HTTPError, urllib.error.URLError, KeyError):
        return None


def main() -> None:
    user = get(f"/users/{USERNAME}")
    repos = [r for r in all_repos() if not r["fork"]]

    data = {
        "user": USERNAME,
        "followers": user["followers"],
        "following": user["following"],
        "repos": len(repos),
        "stars": sum(r["stargazers_count"] for r in repos),
        "forks": sum(r["forks_count"] for r in repos),
        "commits": commit_count(),
        "languages": language_bytes(repos),
    }

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1), encoding="utf-8")
    print(f"wrote {OUT} — {data['repos']} repos, {data['stars']} stars, "
          f"{data['commits']} commits, {len(data['languages'])} languages")


if __name__ == "__main__":
    main()
