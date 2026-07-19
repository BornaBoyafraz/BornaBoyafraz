#!/usr/bin/env python3
"""Render borna-ascii.svg: a monochrome ASCII artwork that types itself
in row by row (SMIL wipes — GitHub plays these inside <img>).

If source-prepped.png exists (see prep_photo.py), it is converted to an
ASCII portrait. Until then, a block-letter "BORNA" banner is rendered so
the README never shows a broken image.

Usage:  python scripts/make_ascii_svg.py
        STATIC=1 python scripts/make_ascii_svg.py   # frozen frame for previews
"""
import html
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source-prepped.png"
OUT = ROOT / "borna-ascii.svg"

RAMP = " .`:-=+*cs#%@"  # bright (sparse) -> dark (dense); space clears the bg
COLS = 100

FONT_SIZE = 12
CW = FONT_SIZE * 0.6   # monospace advance width
LH = FONT_SIZE         # tight leading so rows stack like pixels
PAD = 18

FG = "#c9d1d9"         # one light-gray ink — monochrome on purpose
BG = "#0d1117"
BORDER = "#30363d"
CURSOR = "#39d353"

STATIC = os.environ.get("STATIC") == "1"

BANNER = [
    "██████╗  ██████╗ ██████╗ ███╗   ██╗ █████╗ ",
    "██╔══██╗██╔═══██╗██╔══██╗████╗  ██║██╔══██╗",
    "██████╔╝██║   ██║██████╔╝██╔██╗ ██║███████║",
    "██╔══██╗██║   ██║██╔══██╗██║╚██╗██║██╔══██║",
    "██████╔╝╚██████╔╝██║  ██║██║ ╚████║██║  ██║",
    "╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝",
    "",
    "   python · unreal engine · unity · java",
]


def rows_from_image() -> list[str] | None:
    if not SRC.exists():
        return None
    from PIL import Image

    img = Image.open(SRC).convert("L")
    # A character cell is taller than it is wide, so squash vertically
    # by CW/LH to keep the face's proportions.
    n_rows = max(1, round(img.height / img.width * COLS * (CW / LH)))
    img = img.resize((COLS, n_rows), Image.LANCZOS)
    px = img.load()
    rows = []
    for y in range(n_rows):
        line = ""
        for x in range(COLS):
            v = px[x, y] / 255.0                      # 0 dark .. 1 bright
            line += RAMP[round((1.0 - v) * (len(RAMP) - 1))]
        rows.append(line.rstrip())
    return rows


def main() -> None:
    rows = rows_from_image() or BANNER
    width_cols = max(len(r) for r in rows)
    w = width_cols * CW + 2 * PAD
    h = len(rows) * LH + 2 * PAD

    # Stagger so the whole portrait prints in ~4s, then freezes. No looping.
    stagger = min(0.12, max(0.035, 4.0 / max(len(rows), 1)))
    dur = 0.45 if len(rows) <= 12 else 0.3

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" '
        f'font-size="{FONT_SIZE}">',
        f'<rect width="{w:.0f}" height="{h:.0f}" rx="10" fill="{BG}" stroke="{BORDER}"/>',
        "<defs>",
    ]

    if not STATIC:
        for i, row in enumerate(rows):
            if not row:
                continue
            y = PAD + i * LH
            row_w = len(row) * CW
            begin = i * stagger
            # Base width is FULL so renderers without SMIL still show the
            # finished art; the animation holds it at 0 through the
            # stagger delay, then wipes it open.
            total = begin + dur
            if begin > 0:
                anim = (f'<animate attributeName="width" values="0;0;{row_w:.1f}" '
                        f'keyTimes="0;{begin / total:.4f};1" begin="0s" '
                        f'dur="{total:.2f}s" fill="freeze"/>')
            else:
                anim = (f'<animate attributeName="width" from="0" to="{row_w:.1f}" '
                        f'begin="0s" dur="{dur}s" fill="freeze"/>')
            parts.append(
                f'<clipPath id="r{i}"><rect x="{PAD}" y="{y:.1f}" height="{LH}" '
                f'width="{row_w:.1f}">{anim}</rect></clipPath>'
            )
    parts.append("</defs>")

    for i, row in enumerate(rows):
        if not row:
            continue
        y = PAD + i * LH + FONT_SIZE * 0.8
        clip = "" if STATIC else f' clip-path="url(#r{i})"'
        parts.append(
            f'<text x="{PAD}" y="{y:.1f}" fill="{FG}" xml:space="preserve" '
            f'textLength="{len(row) * CW:.1f}" lengthAdjust="spacingAndGlyphs"{clip}>'
            f"{html.escape(row)}</text>"
        )
        if not STATIC:
            begin = i * stagger
            row_w = len(row) * CW
            # A small block cursor rides the wipe edge, then vanishes.
            parts.append(
                f'<rect x="{PAD}" y="{PAD + i * LH:.1f}" width="{CW:.1f}" height="{LH}" '
                f'fill="{CURSOR}" opacity="0">'
                f'<animate attributeName="x" from="{PAD}" to="{PAD + row_w:.1f}" '
                f'begin="{begin:.2f}s" dur="{dur}s" fill="freeze"/>'
                f'<animate attributeName="opacity" values="0;1" begin="{begin:.2f}s" '
                f'dur="0.01s" fill="freeze"/>'
                f'<animate attributeName="opacity" values="1;0" begin="{begin + dur:.2f}s" '
                f'dur="0.01s" fill="freeze"/></rect>'
            )

    parts.append("</svg>")
    OUT.write_text("\n".join(parts), encoding="utf-8")
    source = "portrait" if SRC.exists() else "banner fallback (no source-prepped.png yet)"
    print(f"wrote {OUT} ({len(rows)} rows, {source})")


if __name__ == "__main__":
    main()
