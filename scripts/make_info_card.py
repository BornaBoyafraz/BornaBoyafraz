#!/usr/bin/env python3
"""Render info-card.svg: a neofetch-style panel that fades in line by
line next to the ASCII art. Content lives here — edit ROWS below when
your projects or links change, then re-run.

Usage:  python scripts/make_info_card.py
        STATIC=1 python scripts/make_info_card.py   # frozen frame for previews
"""
import html
import os
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "info-card.svg"

TITLE = "borna@github"
ROWS = [
    ("Now",      "DRAKE · Antigen · OpportunityOS · SafeWalk"),
    ("Learning", "Machine Learning (help welcome!)"),
    ("Collab",   "Python & ML projects"),
    ("Ask me",   "Python · Unreal Engine · Unity · Java"),
    ("Web",      "bornaba.com"),
    ("LinkedIn", "in/bornaboyafraz"),
    ("Email",    "bornaboyafraz@gmail.com"),
]
SWATCHES = ["#ff5f56", "#ffbd2e", "#27c93f", "#39d353",
            "#58a6ff", "#bc8cff", "#f778ba", "#c9d1d9"]

FONT_SIZE = 13
CW = FONT_SIZE * 0.6
LINE_H = 24
PAD = 22
W = 490

KEY = "#39d353"
VAL = "#c9d1d9"
DIM = "#8b949e"
BG = "#0d1117"
BORDER = "#30363d"

STATIC = os.environ.get("STATIC") == "1"


def main() -> None:
    key_col = (max(len(k) for k, _ in ROWS) + 2) * CW  # "Key:" + gap
    n_lines = 2 + len(ROWS)                             # title + separator + rows
    h = PAD + n_lines * LINE_H + 14 + 16 + PAD          # + swatch strip

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h:.0f}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" '
        f'font-size="{FONT_SIZE}">',
        f'<rect width="{W}" height="{h:.0f}" rx="10" fill="{BG}" stroke="{BORDER}"/>',
    ]
    if not STATIC:
        # No base opacity:0 — renderers with CSS animations disabled must
        # still show the finished card. fill-mode:both hides each line
        # through its stagger delay when animations do run.
        parts.append(
            "<style>.l{animation:fi .5s ease-out both}"
            "@keyframes fi{from{opacity:0;transform:translateY(5px)}"
            "to{opacity:1;transform:none}}</style>"
        )

    def line(i: int, body: str) -> str:
        delay = "" if STATIC else f' class="l" style="animation-delay:{i * 0.35:.2f}s"'
        return f"<g{delay}>{body}</g>"

    y = PAD + FONT_SIZE
    parts.append(line(0, f'<text x="{PAD}" y="{y}" fill="{KEY}" font-weight="bold">'
                        f"{html.escape(TITLE)}</text>"))
    y += LINE_H
    sep = "─" * round((W - 2 * PAD) / CW)
    parts.append(line(1, f'<text x="{PAD}" y="{y}" fill="{DIM}" textLength="{W - 2 * PAD}" '
                        f'lengthAdjust="spacingAndGlyphs">{sep}</text>'))

    for i, (k, v) in enumerate(ROWS):
        y += LINE_H
        parts.append(line(i + 2,
            f'<text x="{PAD}" y="{y}" fill="{KEY}">{html.escape(k)}:</text>'
            f'<text x="{PAD + key_col:.0f}" y="{y}" fill="{VAL}">{html.escape(v)}</text>'))

    y += 14
    swatch = "".join(
        f'<rect x="{PAD + j * 22}" y="{y}" width="16" height="16" rx="3" fill="{c}"/>'
        for j, c in enumerate(SWATCHES)
    )
    parts.append(line(len(ROWS) + 2, swatch))

    parts.append("</svg>")
    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
