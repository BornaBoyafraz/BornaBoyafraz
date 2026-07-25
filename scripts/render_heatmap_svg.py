#!/usr/bin/env python3
"""Render contrib-heatmap.svg from data/contributions.json: the classic
53-week calendar plus an expressive 3D commit builder with weekday-specific
dialogue and 48 synchronized construction-site animations per daily scene.

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

WEEKDAY_STORIES = {
    0: {
        "shift": "MONDAY BLUEPRINT",
        "accent": "#58a6ff",
        "messages": [
            "Monday blueprint: loaded.",
            "Measure twice. Commit once.",
            "Raising today’s green block!",
            "Steady ladder, steady hands.",
            "Bonk! That was the bug.",
            "Quick coffee inspection…",
            "Face says tired. Git says go.",
            "Foundation locked. Nice.",
        ],
    },
    1: {
        "shift": "TOOLBOX TUESDAY",
        "accent": "#f7c948",
        "messages": [
            "Toolbox Tuesday reporting!",
            "Found a loose semicolon.",
            "Three dimensions, zero fear.",
            "Hammer says: ship it.",
            "Gravity filed a bug report.",
            "Ten-second snack deployment.",
            "Okay, back to the scaffold.",
            "Tuesday block: production-ready.",
        ],
    },
    2: {
        "shift": "MIDWEEK MILESTONE",
        "accent": "#a78bfa",
        "messages": [
            "Midweek milestone unlocked!",
            "Halfway up the scaffold.",
            "This block needs extra polish.",
            "Tap, test, tap, deploy.",
            "Whoa—Wednesday wobble!",
            "I’m debugging gravity.",
            "Tiny break. Huge ambition.",
            "Wednesday square: solid.",
        ],
    },
    3: {
        "shift": "THURSDAY LIFT",
        "accent": "#39c5cf",
        "messages": [
            "Thursday lift is online.",
            "Checking the 3D corners.",
            "Depth looks good from here.",
            "One clean strike coming up.",
            "The ladder moved. Rude.",
            "Hard hat saved the streak!",
            "Recharging builder energy…",
            "Thursday block: certified.",
        ],
    },
    4: {
        "shift": "FRIDAY SHIP",
        "accent": "#39d353",
        "messages": [
            "Friday ship crew: me.",
            "Last checks before launch.",
            "Green block looking glossy.",
            "Commit incoming—stand clear!",
            "Plot twist: comic tumble.",
            "I call that agile resting.",
            "One snack, then we ship.",
            "Friday square: launched!",
        ],
    },
    5: {
        "shift": "SATURDAY SIDE QUEST",
        "accent": "#ff8a3d",
        "messages": [
            "Saturday side quest started!",
            "Weekend build mode: ON.",
            "This square needs more depth.",
            "Hammer combo x3!",
            "Whoa—physics update!",
            "I meant to sit down.",
            "Snack acquired. Morale restored.",
            "Green block complete. GG.",
        ],
    },
    6: {
        "shift": "SUNDAY RESET",
        "accent": "#f778ba",
        "messages": [
            "Sunday maintenance shift.",
            "Quiet build, clean commit.",
            "Checking every tiny bolt.",
            "Soft tap. Strong square.",
            "Oops—scaffold yoga!",
            "Hydration checkpoint…",
            "Planning Monday’s comeback.",
            "Site secure. Rest well.",
        ],
    },
}


def message_animation_css(message_count: int) -> str:
    declarations = []
    keyframes = []
    slot = 100 / message_count
    for index in range(message_count):
        start = index * slot
        fade_in = start + 1.2
        hold = start + slot - 2.0
        end = start + slot - .6
        declarations.append(
            f".msg-{index}{{animation:builder-msg-{index} 30s 1.35s infinite both}}"
        )
        keyframes.append(
            f"@keyframes builder-msg-{index}{{"
            f"0%,{start:.2f}%{{opacity:0;transform:translateY(4px) scale(.96)}}"
            f"{fade_in:.2f}%,{hold:.2f}%{{opacity:1;transform:translateY(0) scale(1)}}"
            f"{end:.2f}%,100%{{opacity:0;transform:translateY(-2px) scale(.98)}}"
            "}"
        )
    return "".join(declarations + keyframes)


def builder_css(
    start_x: int,
    ground_x: int,
    ground_y: int,
    target_x: int,
    target_y: int,
    accent: str,
    message_count: int,
    fall_angle: int,
) -> str:
    message_css = message_animation_css(message_count)
    return f"""
<style>
  :root {{ --shift-accent:{accent}; }}
  #builder-route {{
    animation:builder-route 30s 1.35s ease-in-out infinite both;
  }}
  #builder-pose {{
    transform-box:fill-box;
    transform-origin:center bottom;
    animation:builder-pose 30s 1.35s ease-in-out infinite both;
  }}
  #builder-torso {{
    transform-box:fill-box;
    transform-origin:center bottom;
    animation:torso-breathe 2.2s ease-in-out infinite;
  }}
  #builder-head {{
    transform-box:fill-box;
    transform-origin:center bottom;
    animation:head-turn 7.5s ease-in-out infinite;
  }}
  #builder-mouth {{
    transform-box:fill-box;
    transform-origin:center;
    animation:mouth-talk .72s ease-in-out infinite alternate;
  }}
  .builder-eye {{
    transform-box:fill-box;
    transform-origin:center;
    animation:eye-blink 4.2s infinite;
  }}
  .builder-pupil {{ animation:pupil-look 6s ease-in-out infinite; }}
  .builder-brow.a {{ animation:brow-a 5.4s ease-in-out infinite; }}
  .builder-brow.b {{ animation:brow-b 5.4s ease-in-out infinite; }}
  #builder-arm-left {{
    transform-box:fill-box;
    transform-origin:right top;
    animation:arm-left 30s 1.35s ease-in-out infinite both;
  }}
  #builder-arm-right {{
    transform-box:fill-box;
    transform-origin:left top;
    animation:arm-right 30s 1.35s ease-in-out infinite both;
  }}
  #builder-hammer {{
    transform-box:view-box;
    transform-origin:23px 18px;
    animation:builder-hammer 30s 1.35s ease-in-out infinite both;
  }}
  .builder-leg.a {{
    transform-box:fill-box;
    transform-origin:center top;
    animation:leg-left .38s ease-in-out infinite alternate;
  }}
  .builder-leg.b {{
    transform-box:fill-box;
    transform-origin:center top;
    animation:leg-right .38s ease-in-out infinite alternate;
  }}
  #builder-hat {{
    transform-box:fill-box;
    transform-origin:center bottom;
    animation:hat-bob 2.15s ease-in-out infinite;
  }}
  #hat-glint {{ animation:hat-glint 3.8s ease-in-out infinite; }}
  #builder-shadow {{
    transform-box:fill-box;
    transform-origin:center;
    animation:shadow-squash 30s 1.35s ease-in-out infinite both;
  }}
  .builder-ladder {{
    transform-box:fill-box;
    transform-origin:center bottom;
    animation:ladder-cycle 30s 1.35s ease-in-out infinite both;
  }}
  #target-block {{
    transform-box:fill-box;
    transform-origin:center bottom;
    animation:target-lift 30s 1.35s ease-in-out infinite both;
  }}
  #target-top {{ animation:block-top-shimmer 2.4s ease-in-out infinite; }}
  #target-front {{ animation:block-front-glow 1.7s ease-in-out infinite; }}
  #target-side {{ animation:block-side-depth 3.1s ease-in-out infinite; }}
  .target-shine {{ animation:block-shine 2.8s linear infinite; }}
  .target-glow {{ animation:target-pulse 1.15s 1.35s ease-in-out infinite; }}
  .builder-dust.a {{ animation:dust-a 30s 1.35s infinite both; }}
  .builder-dust.b {{ animation:dust-b 30s 1.35s infinite both; }}
  .builder-dust.c {{ animation:dust-c 30s 1.35s infinite both; }}
  .builder-spark.a {{ animation:spark-a 30s 1.35s infinite both; }}
  .builder-spark.b {{ animation:spark-b 30s 1.35s infinite both; }}
  .builder-spark.c {{ animation:spark-c 30s 1.35s infinite both; }}
  #sweat-drop {{ animation:sweat-drop 30s 1.35s infinite both; }}
  .dizzy-star.a {{ animation:dizzy-a 30s 1.35s infinite both; }}
  .dizzy-star.b {{ animation:dizzy-b 30s 1.35s infinite both; }}
  #builder-toolbox {{
    transform-box:fill-box;
    transform-origin:center bottom;
    animation:toolbox-bounce 6.4s ease-in-out infinite;
  }}
  #toolbox-lid {{
    transform-box:fill-box;
    transform-origin:left bottom;
    animation:toolbox-lid 7.2s ease-in-out infinite;
  }}
  #builder-cone {{
    transform-box:fill-box;
    transform-origin:center bottom;
    animation:cone-wobble 4.8s ease-in-out infinite;
  }}
  #builder-blueprint {{
    transform-box:fill-box;
    transform-origin:left center;
    animation:blueprint-wave 8.4s ease-in-out infinite;
  }}
  #builder-zzz {{ animation:zzz-float 30s 1.35s infinite both; }}
  #builder-alert {{ animation:alert-pop 30s 1.35s infinite both; }}
  #shift-board {{
    transform-box:fill-box;
    transform-origin:center bottom;
    animation:shift-board 5.6s ease-in-out infinite;
  }}
  .builder-msg {{ opacity:0; filter:url(#bubble-shadow); }}
  {message_css}

  @keyframes builder-route {{
    0%,5% {{ transform:translate({start_x}px,{ground_y}px); }}
    12%,18% {{ transform:translate({ground_x}px,{ground_y}px); }}
    27%,58% {{ transform:translate({target_x}px,{target_y}px); }}
    63% {{ transform:translate({target_x + 4}px,{target_y + 2}px); }}
    69%,89% {{ transform:translate({ground_x + 5}px,{ground_y + 5}px); }}
    94% {{ transform:translate({ground_x}px,{ground_y}px); }}
    100% {{ transform:translate({start_x}px,{ground_y}px); }}
  }}
  @keyframes builder-pose {{
    0%,59%,94%,100% {{ transform:rotate(0deg) scale(1); }}
    62% {{ transform:rotate(14deg) scale(1.03,.97); }}
    67% {{ transform:rotate({fall_angle}deg) scale(.94); }}
    70%,88% {{ transform:rotate(0deg) scale(1.06,.72); }}
    91% {{ transform:rotate(-7deg) scale(.98,1.08); }}
  }}
  @keyframes torso-breathe {{
    0%,100% {{ transform:scale(1); }}
    50% {{ transform:scale(1.035,.975); }}
  }}
  @keyframes head-turn {{
    0%,20%,100% {{ transform:translateX(0) rotate(0); }}
    35%,48% {{ transform:translateX(1px) rotate(3deg); }}
    65%,78% {{ transform:translateX(-.5px) rotate(-2deg); }}
  }}
  @keyframes mouth-talk {{
    from {{ transform:scaleX(.8) scaleY(.65); }}
    to {{ transform:scaleX(1.12) scaleY(1.35); }}
  }}
  @keyframes eye-blink {{
    0%,45%,51%,100% {{ transform:scaleY(1); }}
    48% {{ transform:scaleY(.08); }}
  }}
  @keyframes pupil-look {{
    0%,18%,100% {{ transform:translateX(0); }}
    30%,48% {{ transform:translateX(1px); }}
    65%,82% {{ transform:translateX(-.7px); }}
  }}
  @keyframes brow-a {{
    0%,60%,100% {{ transform:translateY(0) rotate(0); }}
    68%,78% {{ transform:translateY(-1px) rotate(-8deg); }}
  }}
  @keyframes brow-b {{
    0%,60%,100% {{ transform:translateY(0) rotate(0); }}
    68%,78% {{ transform:translateY(-1px) rotate(8deg); }}
  }}
  @keyframes arm-left {{
    0%,20%,58%,100% {{ transform:rotate(0); }}
    24%,31% {{ transform:rotate(-32deg); }}
    34%,42% {{ transform:rotate(18deg); }}
    72%,88% {{ transform:rotate(-20deg); }}
  }}
  @keyframes arm-right {{
    0%,23%,60%,100% {{ transform:rotate(0); }}
    28%,56% {{ transform:rotate(-10deg); }}
    66% {{ transform:rotate(24deg); }}
    72%,88% {{ transform:rotate(-18deg); }}
  }}
  @keyframes builder-hammer {{
    0%,28%,59%,100% {{ transform:rotate(-55deg); }}
    31%,38%,45%,52% {{ transform:rotate(18deg); }}
    34%,41%,48%,55% {{ transform:rotate(-68deg); }}
  }}
  @keyframes leg-left {{
    from {{ transform:rotate(-22deg); }}
    to {{ transform:rotate(22deg); }}
  }}
  @keyframes leg-right {{
    from {{ transform:rotate(22deg); }}
    to {{ transform:rotate(-22deg); }}
  }}
  @keyframes hat-bob {{
    0%,100% {{ transform:translateY(0) rotate(0); }}
    50% {{ transform:translateY(-1px) rotate(-1deg); }}
  }}
  @keyframes hat-glint {{
    0%,25%,100% {{ opacity:.15; transform:translateX(-3px); }}
    45%,60% {{ opacity:1; transform:translateX(5px); }}
  }}
  @keyframes shadow-squash {{
    0%,25%,59%,94%,100% {{ transform:scale(1); opacity:.48; }}
    35%,55% {{ transform:scale(.72); opacity:.28; }}
    68%,88% {{ transform:scale(1.28,.7); opacity:.62; }}
  }}
  @keyframes ladder-cycle {{
    0%,8%,72%,100% {{ opacity:0; transform:skewX(0); }}
    12%,24% {{ opacity:.85; transform:skewX(-1deg); }}
    28%,60% {{ opacity:.82; transform:skewX(1deg); }}
    64%,69% {{ opacity:.9; transform:skewX(-3deg); }}
  }}
  @keyframes target-lift {{
    0%,27%,58%,100% {{ transform:translateY(0) scale(1); }}
    32%,54% {{ transform:translateY(-2px) scale(1.06); }}
    61% {{ transform:translateY(1px) scale(.98,1.04); }}
  }}
  @keyframes block-top-shimmer {{
    0%,100% {{ opacity:.72; }}
    50% {{ opacity:1; }}
  }}
  @keyframes block-front-glow {{
    0%,100% {{ filter:brightness(.92); }}
    50% {{ filter:brightness(1.24); }}
  }}
  @keyframes block-side-depth {{
    0%,100% {{ opacity:.72; }}
    50% {{ opacity:.95; }}
  }}
  @keyframes block-shine {{
    0% {{ transform:translateX(-9px); opacity:0; }}
    35%,55% {{ opacity:.75; }}
    100% {{ transform:translateX(12px); opacity:0; }}
  }}
  @keyframes target-pulse {{
    0%,100% {{ opacity:.2; stroke-width:1; }}
    50% {{ opacity:1; stroke-width:2.4; }}
  }}
  @keyframes dust-a {{
    0%,30%,57%,100% {{ opacity:0; transform:translate(0,0) scale(.5); }}
    33%,40%,47%,54% {{ opacity:.9; transform:translate(-4px,-5px) scale(1); }}
    36%,43%,50%,56% {{ opacity:0; transform:translate(-8px,-9px) scale(1.35); }}
  }}
  @keyframes dust-b {{
    0%,31%,58%,100% {{ opacity:0; transform:translate(0,0) scale(.5); }}
    34%,41%,48%,55% {{ opacity:.78; transform:translate(4px,-4px) scale(1); }}
    37%,44%,51%,57% {{ opacity:0; transform:translate(9px,-8px) scale(1.25); }}
  }}
  @keyframes dust-c {{
    0%,32%,59%,100% {{ opacity:0; transform:translate(0,0); }}
    35%,42%,49%,56% {{ opacity:.7; transform:translate(1px,-6px); }}
    38%,45%,52%,58% {{ opacity:0; transform:translate(2px,-11px); }}
  }}
  @keyframes spark-a {{
    0%,30%,56%,100% {{ opacity:0; transform:translate(0,0) rotate(0); }}
    33%,40%,47%,54% {{ opacity:1; transform:translate(-6px,-8px) rotate(90deg); }}
    36%,43%,50%,55% {{ opacity:0; transform:translate(-10px,-12px) rotate(180deg); }}
  }}
  @keyframes spark-b {{
    0%,31%,57%,100% {{ opacity:0; transform:translate(0,0) rotate(0); }}
    34%,41%,48%,55% {{ opacity:1; transform:translate(7px,-7px) rotate(-90deg); }}
    37%,44%,51%,56% {{ opacity:0; transform:translate(12px,-11px) rotate(-180deg); }}
  }}
  @keyframes spark-c {{
    0%,32%,58%,100% {{ opacity:0; transform:translate(0,0); }}
    35%,42%,49%,56% {{ opacity:.95; transform:translate(1px,-10px); }}
    38%,45%,52%,57% {{ opacity:0; transform:translate(2px,-15px); }}
  }}
  @keyframes sweat-drop {{
    0%,56%,70%,100% {{ opacity:0; transform:translateY(-2px); }}
    59% {{ opacity:1; transform:translateY(0); }}
    67% {{ opacity:0; transform:translateY(8px); }}
  }}
  @keyframes dizzy-a {{
    0%,61%,73%,100% {{ opacity:0; transform:rotate(0) translateX(0); }}
    65%,70% {{ opacity:1; transform:rotate(180deg) translateX(3px); }}
  }}
  @keyframes dizzy-b {{
    0%,62%,74%,100% {{ opacity:0; transform:rotate(0) translateX(0); }}
    66%,71% {{ opacity:1; transform:rotate(-180deg) translateX(-3px); }}
  }}
  @keyframes toolbox-bounce {{
    0%,72%,100% {{ transform:translateY(0); }}
    76% {{ transform:translateY(-2px); }}
    80% {{ transform:translateY(0); }}
  }}
  @keyframes toolbox-lid {{
    0%,66%,100% {{ transform:rotate(0); }}
    72%,82% {{ transform:rotate(-24deg); }}
  }}
  @keyframes cone-wobble {{
    0%,100% {{ transform:rotate(-2deg); }}
    50% {{ transform:rotate(3deg); }}
  }}
  @keyframes blueprint-wave {{
    0%,58%,100% {{ transform:scaleX(.45) rotate(0); opacity:.45; }}
    66%,84% {{ transform:scaleX(1) rotate(-3deg); opacity:1; }}
  }}
  @keyframes zzz-float {{
    0%,70%,91%,100% {{ opacity:0; transform:translate(0,3px) scale(.8); }}
    76% {{ opacity:1; transform:translate(0,0) scale(1); }}
    88% {{ opacity:0; transform:translate(6px,-9px) scale(1.2); }}
  }}
  @keyframes alert-pop {{
    0%,59%,72%,100% {{ opacity:0; transform:scale(.4) rotate(-15deg); }}
    63%,68% {{ opacity:1; transform:scale(1.1) rotate(5deg); }}
  }}
  @keyframes shift-board {{
    0%,100% {{ transform:rotate(-1deg); }}
    50% {{ transform:rotate(1deg); }}
  }}
  @media (prefers-reduced-motion:reduce) {{
    #builder-route,#builder-pose,#builder-torso,#builder-head,#builder-mouth,
    .builder-eye,.builder-pupil,.builder-brow,#builder-arm-left,
    #builder-arm-right,#builder-hammer,.builder-leg,#builder-hat,#hat-glint,
    #builder-shadow,.builder-ladder,#target-block,#target-top,#target-front,
    #target-side,.target-shine,.target-glow,.builder-dust,.builder-spark,
    #sweat-drop,.dizzy-star,#builder-toolbox,#toolbox-lid,#builder-cone,
    #builder-blueprint,#builder-zzz,#builder-alert,#shift-board,.builder-msg {{
      animation:none !important;
    }}
    .builder-msg {{ display:none; }}
    .builder-ladder {{ opacity:.55; }}
    .target-glow {{ opacity:.65; }}
  }}
</style>""".strip()


def speech_bubble(
    css_class: str,
    text: str,
    x: int,
    y: int,
    accent: str,
) -> list[str]:
    width, height = 176, 27
    return [
        f'<g class="builder-msg {css_class}" opacity="0">',
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="6" '
        f'fill="url(#bubble-bg)" stroke="{accent}" stroke-width="1.3"/>',
        f'<path d="M{x + width - 20} {y + height}h11l-4 7z" '
        f'fill="#161b22" stroke="{accent}" stroke-width="1"/>',
        f'<path d="M{x + 7} {y + 4}h{width - 14}" '
        f'stroke="#ffffff" stroke-opacity=".08" stroke-linecap="round"/>',
        f'<text x="{x + width / 2}" y="{y + 17}" text-anchor="middle" '
        f'fill="#f0f6fc" font-size="7.8" font-weight="700">{text}</text>',
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
    story = WEEKDAY_STORIES[target_date.weekday()]
    accent = story["accent"]
    messages = story["messages"]
    week = (target_date - first_sunday).days // 7
    row = (target_date.weekday() + 1) % 7
    square_x = ox + week * STEP
    square_y = oy + row * STEP

    # The worker's boots sit on the bottom row, then climb beside the target.
    target_worker_x = square_x - 37
    target_worker_y = square_y - 22
    ground_worker_x = target_worker_x
    ground_worker_y = oy + 6 * STEP + CELL - 35
    start_x = max(ox + 8, ground_worker_x - 78)

    ladder_top = square_y + 6
    ladder_bottom = oy + 6 * STEP + CELL - 1
    ladder_x1, ladder_x2 = square_x - 29, square_x - 17

    bubble_x = max(ox + 10, min(square_x - 214, width - 194))
    bubble_y = max(oy + 3, min(square_y - 34, oy + 54))
    fall_angles = [52, 64, 58, 70, 55, 76, 48]

    css = builder_css(
        start_x,
        ground_worker_x,
        ground_worker_y,
        target_worker_x,
        target_worker_y,
        accent,
        len(messages),
        fall_angles[target_date.weekday()],
    )

    scene = [
        f'<rect class="target-glow" x="{square_x - 4}" y="{square_y - 7}" '
        f'width="{CELL + 10}" height="{CELL + 11}" rx="5" fill="none" '
        f'stroke="{accent}"/>',
        '<g id="target-block" filter="url(#block-shadow)">',
        f'<polygon id="target-top" points="{square_x},{square_y} '
        f'{square_x + CELL},{square_y} {square_x + CELL + 4},{square_y - 4} '
        f'{square_x + 4},{square_y - 4}" fill="url(#block-top)"/>',
        f'<rect id="target-front" x="{square_x}" y="{square_y}" '
        f'width="{CELL}" height="{CELL}" rx="2" fill="url(#block-front)"/>',
        f'<polygon id="target-side" points="{square_x + CELL},{square_y} '
        f'{square_x + CELL + 4},{square_y - 4} '
        f'{square_x + CELL + 4},{square_y + CELL - 4} '
        f'{square_x + CELL},{square_y + CELL}" fill="#087f3e"/>',
        f'<path class="target-shine" d="M{square_x + 2} {square_y + 2}v7" '
        'stroke="#b7ffd1" stroke-width="1.4" stroke-linecap="round"/>',
        "</g>",
    ]

    if ladder_bottom - ladder_top > 8:
        scene.extend([
            '<g class="builder-ladder" stroke-linecap="round" '
            'filter="url(#builder-drop)">',
            f'<line x1="{ladder_x1 + 1}" y1="{ladder_top}" '
            f'x2="{ladder_x1 - 1}" y2="{ladder_bottom}" '
            'stroke="#7c4a03" stroke-width="4"/>',
            f'<line x1="{ladder_x1}" y1="{ladder_top}" '
            f'x2="{ladder_x1 - 2}" y2="{ladder_bottom}" '
            'stroke="url(#ladder-gold)" stroke-width="2"/>',
            f'<line x1="{ladder_x2 + 1}" y1="{ladder_top}" '
            f'x2="{ladder_x2 + 3}" y2="{ladder_bottom}" '
            'stroke="#7c4a03" stroke-width="4"/>',
            f'<line x1="{ladder_x2}" y1="{ladder_top}" '
            f'x2="{ladder_x2 + 2}" y2="{ladder_bottom}" '
            'stroke="url(#ladder-gold)" stroke-width="2"/>',
        ])
        for rung_y in range(ladder_top + 4, ladder_bottom, 7):
            progress = (rung_y - ladder_top) / max(1, ladder_bottom - ladder_top)
            left_x = ladder_x1 - round(progress * 2)
            right_x = ladder_x2 + round(progress * 2)
            scene.append(
                f'<line x1="{left_x}" y1="{rung_y}" '
                f'x2="{right_x}" y2="{rung_y}" '
                'stroke="#f7c948" stroke-width="1.6"/>'
            )
        scene.append("</g>")

    prop_y = oy + 6 * STEP + 4
    scene.extend([
        f'<g transform="translate({square_x - 92} {prop_y - 4})">',
        '<g id="builder-cone">',
        '<path d="M2 9L6 0l4 9z" fill="url(#cone-orange)" '
        'stroke="#7c2d12" stroke-width=".7"/>',
        '<path d="M4 5h4" stroke="#fff7ed" stroke-width="1.7"/>',
        '<rect x="0" y="9" width="12" height="2.5" rx="1" fill="#9a3412"/>',
        "</g></g>",
        f'<g transform="translate({square_x - 70} {prop_y})">',
        '<g id="builder-toolbox">',
        '<polygon points="0,1 14,1 17,-2 3,-2" fill="#a78bfa"/>',
        '<rect x="0" y="1" width="14" height="8" rx="1.5" '
        'fill="url(#toolbox-front)" stroke="#4c1d95" stroke-width=".8"/>',
        '<polygon points="14,1 17,-2 17,6 14,9" fill="#4c1d95"/>',
        '<g id="toolbox-lid">',
        '<path d="M4-2v-4h7v4" fill="none" stroke="#c4b5fd" stroke-width="1.4"/>',
        '<path d="M1 1h14" stroke="#e9d5ff" stroke-width="1.2"/>',
        "</g>",
        '<circle cx="7" cy="5" r="1" fill="#f7c948"/>',
        "</g></g>",
        f'<g transform="translate({square_x - 50} {prop_y + 1})">',
        '<g id="builder-blueprint">',
        '<path d="M0 0h18v8H0q3-4 0-8z" fill="#dbeafe" '
        'stroke="#58a6ff" stroke-width=".7"/>',
        '<path d="M4 2h10M4 4h7M4 6h9" stroke="#2563eb" '
        'stroke-width=".55" opacity=".8"/>',
        "</g></g>",
        f'<circle class="builder-dust a" opacity="0" cx="{square_x - 2}" '
        f'cy="{square_y + 8}" r="2.2" fill="#f7c948"/>',
        f'<circle class="builder-dust b" opacity="0" cx="{square_x + 4}" '
        f'cy="{square_y + 9}" r="1.7" fill="#c9d1d9"/>',
        f'<circle class="builder-dust c" opacity="0" cx="{square_x + 1}" '
        f'cy="{square_y + 6}" r="1.4" fill="#ffffff"/>',
        f'<path class="builder-spark a" opacity="0" '
        f'd="M{square_x + 1} {square_y + 2}l3-3M{square_x + 1} '
        f'{square_y - 1}l3 3" stroke="{accent}" stroke-width="1.2"/>',
        f'<path class="builder-spark b" opacity="0" '
        f'd="M{square_x + 7} {square_y + 3}l3-3M{square_x + 7} '
        f'{square_y}l3 3" stroke="#f7c948" stroke-width="1.2"/>',
        f'<circle class="builder-spark c" opacity="0" cx="{square_x + 5}" '
        f'cy="{square_y}" r="1.5" fill="#ffffff"/>',
        f'<g id="builder-route" transform="translate({target_worker_x} {target_worker_y})">',
        '<g id="builder-pose" filter="url(#builder-drop)">',
        '<ellipse id="builder-shadow" cx="15" cy="35" rx="15" ry="3" '
        'fill="#010409" opacity=".55"/>',
        '<g class="builder-leg a">',
        '<path d="M8 26h7v7H8z" fill="url(#overalls-3d)"/>',
        '<path d="M7 32h9v3H7z" fill="url(#boot-3d)"/>',
        "</g>",
        '<g class="builder-leg b">',
        '<path d="M16 26h7v7h-7z" fill="url(#overalls-3d)"/>',
        '<path d="M15 32h10v3H15z" fill="url(#boot-3d)"/>',
        "</g>",
        '<g id="builder-torso">',
        '<path d="M6 17q9-4 18 0v11H6z" fill="url(#shirt-3d)"/>',
        '<path d="M19 17h5v11h-5z" fill="#c2410c" opacity=".48"/>',
        '<path d="M9 18h12v10H9z" fill="url(#overalls-3d)"/>',
        '<path d="M11 18v-3M19 18v-3M10 23h10" fill="none" '
        'stroke="#c4b5fd" stroke-width="1.5"/>',
        '<rect x="13" y="20" width="5" height="4" rx="1" '
        'fill="#6d28d9" stroke="#ddd6fe" stroke-width=".5"/>',
        '<circle cx="11" cy="19" r=".8" fill="#f7c948"/>',
        '<circle cx="20" cy="19" r=".8" fill="#f7c948"/>',
        "</g>",
        '<g id="builder-arm-left">',
        '<path d="M7 18L2 25" stroke="url(#skin-3d)" stroke-width="4.5" '
        'stroke-linecap="round"/>',
        '<circle cx="2" cy="25" r="2.4" fill="#f2b38f"/>',
        "</g>",
        '<g id="builder-arm-right">',
        '<path d="M23 18l5 6" stroke="url(#skin-3d)" stroke-width="4.5" '
        'stroke-linecap="round"/>',
        '<circle cx="28" cy="24" r="2.4" fill="#f2b38f"/>',
        "</g>",
        '<g id="builder-head">',
        '<rect x="12" y="15" width="7" height="4" rx="2" fill="#c9825f"/>',
        '<circle cx="7" cy="10" r="2.5" fill="#d99570"/>',
        '<rect x="7" y="3" width="17" height="14" rx="6" '
        'fill="url(#skin-3d)" stroke="#9a5a3a" stroke-width=".65"/>',
        '<path d="M20 4q4 5 0 12h4V5z" fill="#b76e4c" opacity=".42"/>',
        '<path d="M7 8q2-6 6-5" fill="#5b2c17" opacity=".85"/>',
        '<g class="builder-brow a"><path d="M10 7h4" stroke="#5b2c17" '
        'stroke-width="1" stroke-linecap="round"/></g>',
        '<g class="builder-brow b"><path d="M17 7h4" stroke="#5b2c17" '
        'stroke-width="1" stroke-linecap="round"/></g>',
        '<g class="builder-eye">',
        '<rect x="10" y="8" width="4.5" height="3.5" rx="1.5" fill="#ffffff"/>',
        '<circle class="builder-pupil" cx="13" cy="9.8" r="1.05" fill="#0d1117"/>',
        "</g>",
        '<g class="builder-eye">',
        '<rect x="17" y="8" width="4.5" height="3.5" rx="1.5" fill="#ffffff"/>',
        '<circle class="builder-pupil" cx="20" cy="9.8" r="1.05" fill="#0d1117"/>',
        "</g>",
        '<circle cx="16" cy="12" r="1.35" fill="#d88761" '
        'stroke="#9a5a3a" stroke-width=".45"/>',
        '<circle cx="10" cy="13" r="1.2" fill="#fb7185" opacity=".32"/>',
        '<path id="builder-mouth" d="M13 14.2q3.4 3 6.8 0" fill="none" '
        'stroke="#7c2d12" stroke-width="1.15" stroke-linecap="round"/>',
        '<path d="M14 15.2h5" stroke="#ffffff" stroke-width=".65" opacity=".7"/>',
        '<g id="builder-hat">',
        '<path d="M7 5Q8-2 16-2t9 7z" fill="url(#hat-3d)" '
        'stroke="#9a6700" stroke-width=".7"/>',
        '<rect x="5" y="4" width="22" height="3.5" rx="1.7" '
        'fill="url(#hat-brim)"/>',
        '<path d="M15-1v6" stroke="#fff3b0" stroke-width="2" opacity=".65"/>',
        '<path id="hat-glint" d="M10 1q3-3 6-1" fill="none" '
        'stroke="#ffffff" stroke-width="1.2" stroke-linecap="round"/>',
        "</g>",
        "</g>",
        '<g id="builder-hammer">',
        '<path d="M23 18L31 24" stroke="url(#hammer-handle)" stroke-width="2.8" '
        'stroke-linecap="round"/>',
        '<path d="M29 20h10v6H29z" fill="url(#hammer-metal)" '
        'stroke="#57606a" stroke-width=".8"/>',
        '<path d="M31 20h8l-2-2h-5z" fill="#f0f6fc" opacity=".8"/>',
        "</g>",
        '<path id="sweat-drop" opacity="0" d="M25 8q3 4 0 6q-3-2 0-6" '
        'fill="#58a6ff"/>',
        '<text class="dizzy-star a" opacity="0" x="2" y="4" '
        'fill="#f7c948" font-size="6">★</text>',
        '<text class="dizzy-star b" opacity="0" x="27" y="2" '
        'fill="#ffffff" font-size="5">✦</text>',
        "</g>",
        '<text id="builder-zzz" opacity="0" x="25" y="1" '
        'fill="#a78bfa" font-size="7" font-weight="800">Zz</text>',
        '<g id="builder-alert" opacity="0">',
        '<circle cx="31" cy="2" r="5" fill="#f7c948" stroke="#7c4a03"/>',
        '<text x="31" y="4" text-anchor="middle" fill="#0d1117" '
        'font-size="7" font-weight="900">!</text>',
        "</g>",
        "</g>",
    ])

    scene.extend([
        '<g id="shift-board">',
        f'<rect x="{bubble_x + 7}" y="{bubble_y - 11}" width="116" '
        f'height="10" rx="4" fill="{accent}" opacity=".95"/>',
        f'<text x="{bubble_x + 65}" y="{bubble_y - 4}" text-anchor="middle" '
        f'fill="#0d1117" font-size="6.2" font-weight="900" '
        f'letter-spacing=".45">{story["shift"]}</text>',
        "</g>",
    ])

    for index, message in enumerate(messages):
        scene.extend(
            speech_bubble(f"msg-{index}", message, bubble_x, bubble_y, accent)
        )

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
        "<title>3D contribution heatmap with a weekday-aware animated commit builder</title>",
        """
<defs>
  <linearGradient id="hat-3d" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#fff3b0"/>
    <stop offset=".42" stop-color="#f7c948"/>
    <stop offset="1" stop-color="#b77900"/>
  </linearGradient>
  <linearGradient id="hat-brim" x1="0" y1="0" x2="0" y2="1">
    <stop stop-color="#ffe58f"/><stop offset="1" stop-color="#c98b00"/>
  </linearGradient>
  <linearGradient id="skin-3d" x1="0" y1="0" x2="1" y2="1">
    <stop stop-color="#ffd0b5"/><stop offset=".55" stop-color="#f2b38f"/>
    <stop offset="1" stop-color="#b96f4c"/>
  </linearGradient>
  <linearGradient id="shirt-3d" x1="0" y1="0" x2="1" y2="1">
    <stop stop-color="#ffb36b"/><stop offset=".5" stop-color="#ff8a3d"/>
    <stop offset="1" stop-color="#c2410c"/>
  </linearGradient>
  <linearGradient id="overalls-3d" x1="0" y1="0" x2="1" y2="1">
    <stop stop-color="#c4b5fd"/><stop offset=".48" stop-color="#8b5cf6"/>
    <stop offset="1" stop-color="#4c1d95"/>
  </linearGradient>
  <linearGradient id="boot-3d" x1="0" y1="0" x2="0" y2="1">
    <stop stop-color="#6e7681"/><stop offset="1" stop-color="#21262d"/>
  </linearGradient>
  <linearGradient id="hammer-metal" x1="0" y1="0" x2="1" y2="1">
    <stop stop-color="#ffffff"/><stop offset=".4" stop-color="#c9d1d9"/>
    <stop offset="1" stop-color="#57606a"/>
  </linearGradient>
  <linearGradient id="hammer-handle" x1="0" y1="0" x2="1" y2="1">
    <stop stop-color="#d6a26e"/><stop offset="1" stop-color="#7c4a2d"/>
  </linearGradient>
  <linearGradient id="ladder-gold" x1="0" y1="0" x2="1" y2="0">
    <stop stop-color="#fff3b0"/><stop offset=".45" stop-color="#f7c948"/>
    <stop offset="1" stop-color="#a56600"/>
  </linearGradient>
  <linearGradient id="toolbox-front" x1="0" y1="0" x2="1" y2="1">
    <stop stop-color="#a78bfa"/><stop offset="1" stop-color="#5b21b6"/>
  </linearGradient>
  <linearGradient id="cone-orange" x1="0" y1="0" x2="1" y2="1">
    <stop stop-color="#fed7aa"/><stop offset=".45" stop-color="#fb923c"/>
    <stop offset="1" stop-color="#c2410c"/>
  </linearGradient>
  <linearGradient id="block-top" x1="0" y1="0" x2="1" y2="1">
    <stop stop-color="#b7ffd1"/><stop offset="1" stop-color="#39d353"/>
  </linearGradient>
  <linearGradient id="block-front" x1="0" y1="0" x2="1" y2="1">
    <stop stop-color="#56e878"/><stop offset="1" stop-color="#0b8f43"/>
  </linearGradient>
  <linearGradient id="bubble-bg" x1="0" y1="0" x2="0" y2="1">
    <stop stop-color="#21262d"/><stop offset="1" stop-color="#0d1117"/>
  </linearGradient>
  <filter id="builder-drop" x="-40%" y="-40%" width="180%" height="200%"
          color-interpolation-filters="sRGB">
    <feDropShadow dx="1.5" dy="2" stdDeviation="1.2"
                  flood-color="#000000" flood-opacity=".72"/>
  </filter>
  <filter id="block-shadow" x="-50%" y="-70%" width="220%" height="240%"
          color-interpolation-filters="sRGB">
    <feDropShadow dx="2" dy="3" stdDeviation="1.4"
                  flood-color="#000000" flood-opacity=".76"/>
  </filter>
  <filter id="bubble-shadow" x="-20%" y="-50%" width="150%" height="220%"
          color-interpolation-filters="sRGB">
    <feDropShadow dx="1.4" dy="2" stdDeviation="1.6"
                  flood-color="#000000" flood-opacity=".72"/>
  </filter>
</defs>""".strip(),
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
