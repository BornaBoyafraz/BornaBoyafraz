#!/usr/bin/env python3
"""Render contrib-heatmap.svg from data/contributions.json: the classic
53-week calendar plus an animated pixel-art commit builder who travels to
today's square, climbs when needed, works, tumbles, and takes a break.

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


def builder_css(
    start_x: int,
    ground_x: int,
    ground_y: int,
    target_x: int,
    target_y: int,
) -> str:
    return f"""
<style>
  #builder-route {{
    animation:builder-route 18s 1.35s ease-in-out infinite both;
  }}
  #builder-pose {{
    transform-box:fill-box;
    transform-origin:center bottom;
    animation:builder-pose 18s 1.35s ease-in-out infinite both;
  }}
  #builder-hammer {{
    transform-box:view-box;
    transform-origin:14px 12px;
    animation:builder-hammer 18s 1.35s ease-in-out infinite both;
  }}
  .builder-leg {{
    transform-box:fill-box;
    transform-origin:center top;
    animation:builder-step .34s ease-in-out infinite alternate;
  }}
  .builder-leg.b {{ animation-direction:alternate-reverse; }}
  .builder-ladder {{ animation:ladder-cycle 18s 1.35s infinite both; }}
  .target-glow {{ animation:target-pulse 1.15s 1.35s ease-in-out infinite; }}
  .builder-dust.a {{ animation:dust-a 18s 1.35s infinite both; }}
  .builder-dust.b {{ animation:dust-b 18s 1.35s infinite both; }}
  .builder-msg {{ opacity:0; }}
  .msg-build {{ animation:msg-build 18s 1.35s infinite both; }}
  .msg-commit {{ animation:msg-commit 18s 1.35s infinite both; }}
  .msg-oops {{ animation:msg-oops 18s 1.35s infinite both; }}
  .msg-rest {{ animation:msg-rest 18s 1.35s infinite both; }}
  .builder-eye {{ animation:builder-blink 4.1s infinite; }}

  @keyframes builder-route {{
    0%,7% {{ transform:translate({start_x}px,{ground_y}px); }}
    16%,23% {{ transform:translate({ground_x}px,{ground_y}px); }}
    36%,58% {{ transform:translate({target_x}px,{target_y}px); }}
    64% {{ transform:translate({target_x + 3}px,{target_y + 2}px); }}
    70%,92% {{ transform:translate({ground_x + 4}px,{ground_y + 4}px); }}
    100% {{ transform:translate({start_x}px,{ground_y}px); }}
  }}
  @keyframes builder-pose {{
    0%,58%,100% {{ transform:rotate(0deg) scaleY(1); }}
    63% {{ transform:rotate(18deg) scaleY(1); }}
    68% {{ transform:rotate(82deg) scaleY(.92); }}
    72%,91% {{ transform:rotate(0deg) scaleY(.76); }}
    94% {{ transform:rotate(0deg) scaleY(1.06); }}
  }}
  @keyframes builder-hammer {{
    0%,37%,59%,100% {{ transform:rotate(-48deg); }}
    40%,46%,52% {{ transform:rotate(16deg); }}
    43%,49%,55% {{ transform:rotate(-58deg); }}
  }}
  @keyframes builder-step {{
    from {{ transform:rotate(-18deg); }}
    to {{ transform:rotate(18deg); }}
  }}
  @keyframes ladder-cycle {{
    0%,10%,73%,100% {{ opacity:0; }}
    15%,67% {{ opacity:.78; }}
  }}
  @keyframes target-pulse {{
    0%,100% {{ opacity:.24; stroke-width:1; }}
    50% {{ opacity:1; stroke-width:2.2; }}
  }}
  @keyframes dust-a {{
    0%,39%,56%,100% {{ opacity:0; transform:translate(0,0); }}
    41%,47%,53% {{ opacity:.9; transform:translate(-3px,-4px); }}
    44%,50%,55% {{ opacity:0; transform:translate(-6px,-7px); }}
  }}
  @keyframes dust-b {{
    0%,40%,57%,100% {{ opacity:0; transform:translate(0,0); }}
    42%,48%,54% {{ opacity:.75; transform:translate(3px,-3px); }}
    45%,51%,56% {{ opacity:0; transform:translate(7px,-6px); }}
  }}
  @keyframes msg-build {{
    0%,29%,46%,100% {{ opacity:0; transform:translateY(3px); }}
    32%,43% {{ opacity:1; transform:translateY(0); }}
  }}
  @keyframes msg-commit {{
    0%,44%,59%,100% {{ opacity:0; transform:translateY(3px); }}
    47%,56% {{ opacity:1; transform:translateY(0); }}
  }}
  @keyframes msg-oops {{
    0%,61%,73%,100% {{ opacity:0; transform:translateY(3px); }}
    64%,70% {{ opacity:1; transform:translateY(0); }}
  }}
  @keyframes msg-rest {{
    0%,72%,94%,100% {{ opacity:0; transform:translateY(3px); }}
    76%,91% {{ opacity:1; transform:translateY(0); }}
  }}
  @keyframes builder-blink {{
    0%,46%,50%,100% {{ opacity:1; }}
    48% {{ opacity:0; }}
  }}
  @media (prefers-reduced-motion:reduce) {{
    #builder-route,#builder-pose,#builder-hammer,.builder-leg,.builder-ladder,
    .target-glow,.builder-dust,.builder-msg,.builder-eye {{
      animation:none !important;
    }}
    .builder-msg {{ display:none; }}
    .builder-ladder {{ opacity:.55; }}
    .target-glow {{ opacity:.65; }}
  }}
</style>""".strip()


def speech_bubble(css_class: str, text: str, x: int, y: int) -> list[str]:
    width, height = 132, 23
    return [
        f'<g class="builder-msg {css_class}" opacity="0">',
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="6" '
        f'fill="#161b22" stroke="#f7c948" stroke-width="1.2"/>',
        f'<path d="M{x + width - 19} {y + height}h10l-4 6z" '
        f'fill="#161b22" stroke="#f7c948" stroke-width="1"/>',
        f'<text x="{x + width / 2}" y="{y + 15}" text-anchor="middle" '
        f'fill="#f0f6fc" font-size="7.5" font-weight="700">{text}</text>',
        "</g>",
    ]


def builder_scene(
    days: list[dict],
    first_sunday: dt.date,
    ox: int,
    oy: int,
    width: int,
) -> tuple[str, list[str]]:
    target_date = dt.date.fromisoformat(days[-1]["date"])
    week = (target_date - first_sunday).days // 7
    row = (target_date.weekday() + 1) % 7
    square_x = ox + week * STEP
    square_y = oy + row * STEP

    # The worker's boots sit on the bottom row, then climb beside the target.
    target_worker_x = square_x - 24
    target_worker_y = square_y - 11
    ground_worker_x = target_worker_x
    ground_worker_y = oy + 6 * STEP + CELL - 22
    start_x = max(ox + 8, ground_worker_x - 54)

    ladder_top = square_y + 7
    ladder_bottom = oy + 6 * STEP + CELL - 1
    ladder_x1, ladder_x2 = square_x - 20, square_x - 12

    bubble_x = max(ox + 10, min(square_x - 158, width - 150))
    bubble_y = max(oy + 2, min(square_y - 29, oy + 58))

    css = builder_css(
        start_x,
        ground_worker_x,
        ground_worker_y,
        target_worker_x,
        target_worker_y,
    )

    scene = [
        f'<rect class="target-glow" x="{square_x - 2}" y="{square_y - 2}" '
        f'width="{CELL + 4}" height="{CELL + 4}" rx="4" fill="none" '
        f'stroke="#f7c948"/>',
    ]

    if ladder_bottom - ladder_top > 8:
        scene.extend([
            '<g class="builder-ladder" stroke="#f7c948" stroke-width="1.4" '
            'stroke-linecap="round">',
            f'<line x1="{ladder_x1}" y1="{ladder_top}" '
            f'x2="{ladder_x1}" y2="{ladder_bottom}"/>',
            f'<line x1="{ladder_x2}" y1="{ladder_top}" '
            f'x2="{ladder_x2}" y2="{ladder_bottom}"/>',
        ])
        for rung_y in range(ladder_top + 4, ladder_bottom, 6):
            scene.append(
                f'<line x1="{ladder_x1}" y1="{rung_y}" '
                f'x2="{ladder_x2}" y2="{rung_y}"/>'
            )
        scene.append("</g>")

    # Toolbox anchors the little construction scene even when no ladder is needed.
    scene.extend([
        f'<g transform="translate({square_x - 48} {oy + 6 * STEP + 6})">',
        '<rect x="0" y="0" width="14" height="7" rx="1.5" '
        'fill="#8b5cf6" stroke="#c4b5fd" stroke-width=".8"/>',
        '<path d="M4 0v-3h6v3" fill="none" stroke="#c4b5fd" stroke-width="1"/>',
        '<path d="M7 1v5" stroke="#c4b5fd" stroke-width=".8"/>',
        "</g>",
        f'<circle class="builder-dust a" opacity="0" cx="{square_x - 2}" '
        f'cy="{square_y + 8}" r="2.2" fill="#f7c948"/>',
        f'<circle class="builder-dust b" opacity="0" cx="{square_x + 4}" '
        f'cy="{square_y + 9}" r="1.7" fill="#c9d1d9"/>',
        f'<g id="builder-route" transform="translate({target_worker_x} {target_worker_y})">',
        '<g id="builder-pose">',
        '<ellipse cx="8" cy="22" rx="8" ry="2" fill="#010409" opacity=".55"/>',
        '<g class="builder-leg a">',
        '<rect x="4" y="17" width="4" height="5" rx="1" fill="#6d28d9"/>',
        '<rect x="3" y="21" width="6" height="2" rx="1" fill="#30363d"/>',
        "</g>",
        '<g class="builder-leg b">',
        '<rect x="9" y="17" width="4" height="5" rx="1" fill="#6d28d9"/>',
        '<rect x="9" y="21" width="6" height="2" rx="1" fill="#30363d"/>',
        "</g>",
        '<rect x="3" y="10" width="11" height="9" rx="2" fill="#ff8a3d"/>',
        '<path d="M6 11v8M11 11v8M6 15h5" stroke="#8b5cf6" '
        'stroke-width="2.4"/>',
        '<rect x="13" y="11" width="4" height="3" rx="1.5" fill="#f2b38f"/>',
        '<rect x="5" y="4" width="9" height="7" rx="2" fill="#f2b38f"/>',
        '<rect class="builder-eye" x="11" y="6" width="1.5" height="1.5" '
        'rx=".5" fill="#0d1117"/>',
        '<path d="M10 9h4" stroke="#7c2d12" stroke-width="1" '
        'stroke-linecap="round"/>',
        '<rect x="4" y="1" width="10" height="4" rx="2" fill="#f7c948"/>',
        '<rect x="2" y="4" width="14" height="2" rx="1" fill="#e3b341"/>',
        '<rect x="8" y="1" width="2" height="3" fill="#fff3b0" opacity=".75"/>',
        '<g id="builder-hammer">',
        '<path d="M14 12L20 15" stroke="#a3714f" stroke-width="2" '
        'stroke-linecap="round"/>',
        '<rect x="18" y="12" width="7" height="4" rx="1" '
        'fill="#c9d1d9" stroke="#6e7681" stroke-width=".7"/>',
        "</g>",
        "</g>",
        "</g>",
    ])

    for css_class, message in (
        ("msg-build", "Building today’s square!"),
        ("msg-commit", "One more commit!"),
        ("msg-oops", "Whoa—hard hat works!"),
        ("msg-rest", "Break time… zzz"),
    ):
        scene.extend(speech_bubble(css_class, message, bubble_x, bubble_y))

    return css, scene


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
        f'font-size="11" role="img">',
        "<title>Contribution heatmap with an animated commit construction worker</title>",
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
    builder_style, builder_parts = builder_scene(days, first_sunday, ox, oy, w)
    if not STATIC:
        parts.append(builder_style)

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

    parts.extend(builder_parts)

    # Legend (left) + stats footer (right).
    ly = oy + 7 * STEP - GAP + 16
    parts.append(f'<text x="{ox}" y="{ly + 10}" fill="{TEXT}">Less</text>')
    for i, color in enumerate(PALETTE):
        parts.append(f'<rect x="{ox + 34 + i * STEP}" y="{ly}" width="{CELL}" '
                     f'height="{CELL}" rx="2.5" fill="{color}"/>')
    parts.append(f'<text x="{ox + 34 + len(PALETTE) * STEP + 4}" y="{ly + 10}" '
                 f'fill="{TEXT}">More</text>')

    longest_start = dt.date.fromisoformat(data["streak_longest_start"])
    longest_end = dt.date.fromisoformat(data["streak_longest_end"])
    longest_range = f'{MONTHS[longest_start.month - 1]} {longest_start.day}–'
    if longest_start.month != longest_end.month:
        longest_range += f'{MONTHS[longest_end.month - 1]} '
    longest_range += str(longest_end.day)
    best_date = dt.date.fromisoformat(data["best"]["date"])
    best_label = f'{MONTHS[best_date.month - 1]} {best_date.day}'
    stats = (f'{data["total"]:,} last-year contributions · '
             f'current {data["streak_current"]}d · '
             f'longest {data["streak_longest"]}d ({longest_range}) · '
             f'best {data["best"]["count"]} ({best_label})')
    parts.append(f'<text x="{w - PAD}" y="{ly + 10}" text-anchor="end" '
                 f'fill="{BRIGHT}">{stats}</text>')

    parts.append("</svg>")
    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"wrote {OUT} ({weeks} weeks)")


if __name__ == "__main__":
    main()
