#!/usr/bin/env python3
"""Render contrib-heatmap.svg from data/contributions.json: the classic
53-week calendar of rounded boxes, revealed once with a diagonal
line-after-line slide (CSS keyframes that play on load, then freeze).

Usage:  python scripts/render_heatmap_svg.py
        STATIC=1 python scripts/render_heatmap_svg.py   # frozen frame
"""
import datetime as dt
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"

PALETTE = ["#161b22", "#0e4429", "#006d32",
           "#26a641", "#39d353", "#69f0a0"]
#          none -> brightest (level 5 is a neon top end)

CELL, GAP = 11, 3
STEP = CELL + GAP
PAD = 18          # card padding
LEFT = 30         # weekday labels gutter
TOP = 26          # month labels gutter

BG = "#0d1117"
BORDER = "#30363d"
TEXT = "#8b949e"
BRIGHT = "#c9d1d9"

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

STATIC = os.environ.get("STATIC") == "1"


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    days = data["days"]

    first = dt.date.fromisoformat(days[0]["date"])
    first_sunday = first - dt.timedelta(days=(first.weekday() + 1) % 7)
    weeks = (dt.date.fromisoformat(days[-1]["date"]) - first_sunday).days // 7 + 1

    w = PAD + LEFT + weeks * STEP - GAP + PAD
    h = PAD + TOP + 7 * STEP - GAP + 16 + 14 + PAD

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" '
        f'font-size="11">',
        f'<rect width="{w}" height="{h}" rx="10" fill="{BG}" stroke="{BORDER}"/>',
    ]
    if not STATIC:
        # No base opacity:0 — renderers with CSS animations disabled must
        # still show the finished grid. fill-mode:both hides each cell
        # through its diagonal delay when animations do run.
        parts.append(
            "<style>.c{animation:dr .45s ease-out both}"
            "@keyframes dr{from{opacity:0;transform:translateY(-7px)}"
            "to{opacity:1;transform:none}}</style>"
        )

    ox, oy = PAD + LEFT, PAD + TOP

    # Month labels: mark each column where the month changes.
    seen = None
    for wk in range(weeks):
        month = (first_sunday + dt.timedelta(weeks=wk)).month
        if month != seen:
            if wk > 0 or weeks < 53:  # skip a cramped label on the very edge
                parts.append(f'<text x="{ox + wk * STEP}" y="{PAD + 12}" '
                             f'fill="{TEXT}">{MONTHS[month - 1]}</text>')
            seen = month

    for label, row in (("Mon", 1), ("Wed", 3), ("Fri", 5)):
        parts.append(f'<text x="{PAD}" y="{oy + row * STEP + CELL - 2}" '
                     f'fill="{TEXT}">{label}</text>')

    for d in days:
        date = dt.date.fromisoformat(d["date"])
        wk = (date - first_sunday).days // 7
        row = (date.weekday() + 1) % 7
        anim = "" if STATIC else (f' class="c" style="animation-delay:'
                                  f'{(wk + row) * 0.022:.3f}s"')
        parts.append(
            f'<rect x="{ox + wk * STEP}" y="{oy + row * STEP}" width="{CELL}" '
            f'height="{CELL}" rx="2.5" fill="{PALETTE[d["level"]]}"{anim}/>'
        )

    # Legend (left) + stats footer (right).
    ly = oy + 7 * STEP - GAP + 16
    parts.append(f'<text x="{ox}" y="{ly + 10}" fill="{TEXT}">Less</text>')
    for i, color in enumerate(PALETTE):
        parts.append(f'<rect x="{ox + 34 + i * STEP}" y="{ly}" width="{CELL}" '
                     f'height="{CELL}" rx="2.5" fill="{color}"/>')
    parts.append(f'<text x="{ox + 34 + len(PALETTE) * STEP + 4}" y="{ly + 10}" '
                 f'fill="{TEXT}">More</text>')

    stats = (f'{data["total"]:,} contributions in the last year · '
             f'streak {data["streak_current"]}d · longest {data["streak_longest"]}d · '
             f'best {data["best"]["count"]} on {data["best"]["date"]}')
    parts.append(f'<text x="{w - PAD}" y="{ly + 10}" text-anchor="end" '
                 f'fill="{BRIGHT}">{stats}</text>')

    parts.append("</svg>")
    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"wrote {OUT} ({weeks} weeks)")


if __name__ == "__main__":
    main()
