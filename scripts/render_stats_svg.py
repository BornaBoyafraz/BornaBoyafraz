#!/usr/bin/env python3
"""Render stats-card.svg and top-langs.svg from data/github-stats.json.

Self-hosted replacements for the github-readme-stats widgets, which kept
serving "Something went wrong / Maximum retries exceeded" once the shared
public instances hit their rate limit. Styling matches contrib-heatmap.svg.

Usage:  python scripts/render_stats_svg.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "github-stats.json"

BG = "#0d1117"
BORDER = "#30363d"
TEXT = "#8b949e"
BRIGHT = "#c9d1d9"
TITLE = "#a78bfa"
ACCENT = "#8b5cf6"

FONT = ('font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"'
        ' font-size="12"')

# Brand colours for the languages this profile actually contains; anything
# unrecognised falls back to a neutral so the bar never renders colourless.
LANG_COLORS = {
    "TypeScript": "#3178c6", "Python": "#3572A5", "JavaScript": "#f1e05a",
    "CSS": "#663399", "HTML": "#e34c26", "Java": "#b07219",
    "C#": "#178600", "C++": "#f34b7d", "C": "#555555",
    "PLpgSQL": "#336790", "Makefile": "#427819", "Shell": "#89e051",
    "Jupyter Notebook": "#DA5B0B", "Dockerfile": "#384d54", "Go": "#00ADD8",
    "Rust": "#dea584", "Ruby": "#701516", "Swift": "#F05138",
    "Kotlin": "#A97BFF", "PHP": "#4F5D95", "Vue": "#41b883",
}
FALLBACK = "#6e7681"


def shell(width: int, height: int, title: str, body: list[str]) -> str:
    """Card chrome shared by both widgets: rounded panel, rule, title row."""
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}" {FONT} role="img">',
        f"<title>{title}</title>",
        f'<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" '
        f'rx="10" fill="{BG}" stroke="{BORDER}"/>',
        f'<text x="20" y="30" fill="{TITLE}" font-size="14" '
        f'font-weight="700">{title}</text>',
        f'<line x1="20" y1="41" x2="{width - 20}" y2="41" '
        f'stroke="{BORDER}"/>',
        *body,
        "</svg>",
    ])


def stats_card() -> str:
    d = json.loads(DATA.read_text())
    rows = [
        ("Total Stars Earned", d["stars"]),
        ("Total Commits", d["commits"]),
        ("Public Repositories", d["repos"]),
        ("Followers", d["followers"]),
        ("Total Forks", d["forks"]),
    ]
    rows = [(label, value) for label, value in rows if value is not None]

    body = []
    y = 68
    for index, (label, value) in enumerate(rows):
        body.append(
            f'<text x="20" y="{y}" fill="{TEXT}">{label}</text>'
            f'<text x="330" y="{y}" fill="{BRIGHT}" font-weight="700" '
            f'text-anchor="end">{value:,}</text>'
        )
        # Hairline between rows, not after the last one.
        if index < len(rows) - 1:
            body.append(f'<line x1="20" y1="{y + 9}" x2="330" y2="{y + 9}" '
                        f'stroke="{BORDER}" stroke-opacity=".55"/>')
        y += 28
    return shell(350, y + 4, "GitHub Stats", body)


def top_langs(count: int = 6) -> str:
    d = json.loads(DATA.read_text())
    langs = list(d["languages"].items())[:count]
    total = sum(v for _, v in langs) or 1

    bar_x, bar_w, bar_y = 20, 310, 58
    body, offset = [], 0.0
    # Single stacked bar, then a two-column legend beneath it.
    for name, size in langs:
        share = size / total
        width = share * bar_w
        body.append(
            f'<rect x="{bar_x + offset:.2f}" y="{bar_y}" '
            f'width="{max(width, 0.6):.2f}" height="9" '
            f'fill="{LANG_COLORS.get(name, FALLBACK)}"/>'
        )
        offset += width

    y = bar_y + 30
    for index, (name, size) in enumerate(langs):
        col = index % 2
        x = bar_x + col * 158
        if col == 0 and index:
            y += 22
        pct = size / total * 100
        body.append(
            f'<circle cx="{x + 5}" cy="{y - 4}" r="5" '
            f'fill="{LANG_COLORS.get(name, FALLBACK)}"/>'
            f'<text x="{x + 16}" y="{y}" fill="{BRIGHT}">{name}</text>'
            f'<text x="{x + 148}" y="{y}" fill="{TEXT}" text-anchor="end">'
            f'{pct:.1f}%</text>'
        )

    # Round the bar by clipping it to a rounded rect of the same geometry.
    body.insert(0, f'<clipPath id="barclip"><rect x="{bar_x}" y="{bar_y}" '
                   f'width="{bar_w}" height="9" rx="4.5"/></clipPath>')
    body.insert(1, '<g clip-path="url(#barclip)">')
    body.insert(2 + len(langs), "</g>")
    return shell(350, y + 18, "Most Used Languages", body)


def main() -> None:
    (ROOT / "stats-card.svg").write_text(stats_card(), encoding="utf-8")
    (ROOT / "top-langs.svg").write_text(top_langs(), encoding="utf-8")
    print("wrote stats-card.svg and top-langs.svg")


if __name__ == "__main__":
    main()
