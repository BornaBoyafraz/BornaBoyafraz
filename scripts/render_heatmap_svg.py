#!/usr/bin/env python3
"""Render contrib-heatmap.svg from data/contributions.json: the classic
53-week calendar plus an expressive 3D commit builder with weekday-specific
dialogue and synchronized construction-site animations per daily scene.

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
TOP = 34          # compact status note + month labels
FOOTER_GAP = 28   # clear workbench below the contribution cells

BG = "#0d1117"
BORDER = "#30363d"
TEXT = "#8b949e"
BRIGHT = "#c9d1d9"

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

STATIC = os.environ.get("STATIC") == "1"

# Eight beats per day, mapped to the loop: arrive, work x4, clock out,
# sleep, wake. Copy stays short so the bubble never crowds the calendar.
WEEKDAY_STORIES = {
    0: {
        "shift": "Monday",
        "accent": "#7897c5",
        "messages": [
            "Monday. Blueprint loaded.",
            "Measure twice, commit once.",
            "Squaring up today's block.",
            "That'll hold.",
            "Clean strike.",
            "Clocking out. Briefly.",
            "Compiling dreams…",
            "Back on the scaffold.",
        ],
    },
    1: {
        "shift": "Tuesday",
        "accent": "#b79b64",
        "messages": [
            "Toolbox open.",
            "Found a loose semicolon.",
            "Tightening the joints.",
            "Ship it.",
            "Level. Finally.",
            "Taking five.",
            "Tools on the charger…",
            "Nap merged. Resuming.",
        ],
    },
    2: {
        "shift": "Wednesday",
        "accent": "#9886b8",
        "messages": [
            "Midweek. Halfway up.",
            "This one needs polish.",
            "Tap, test, tap.",
            "Holding steady.",
            "Good enough to ship.",
            "Break time.",
            "Resting the hammer…",
            "Recharged. Back up.",
        ],
    },
    3: {
        "shift": "Thursday",
        "accent": "#6f9fa3",
        "messages": [
            "Checking the corners.",
            "Depth reads well.",
            "One clean strike.",
            "Square and true.",
            "Hard hat earned its keep.",
            "Stepping away.",
            "Off the clock…",
            "Lifting again.",
        ],
    },
    4: {
        "shift": "Friday",
        "accent": "#6d9b7b",
        "messages": [
            "Friday. Ship day.",
            "Last checks.",
            "Looking glossy.",
            "Stand clear — committing.",
            "Merged.",
            "Weekend branch.",
            "Dreaming of green…",
            "Stretch. Ship again.",
        ],
    },
    5: {
        "shift": "Saturday",
        "accent": "#b7886d",
        "messages": [
            "Weekend build mode.",
            "Side quest accepted.",
            "Adding some depth.",
            "Three taps, no bugs.",
            "Solid.",
            "Earned a break.",
            "Quest paused…",
            "Respawned. Building.",
        ],
    },
    6: {
        "shift": "Sunday",
        "accent": "#aa7f9d",
        "messages": [
            "Sunday maintenance.",
            "Quiet build, clean commit.",
            "Checking every bolt.",
            "Soft tap. Strong square.",
            "Tidy.",
            "Winding down.",
            "Planning the week…",
            "Reset complete.",
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
            # NB: the closing brace is a plain string, so it must NOT be
            # doubled — only f-string fragments escape braces. A stray "}}"
            # here emits ".msg-N{...}}" and kills every rule that follows.
            f".msg-{index}{{animation:builder-msg-{index} 30s 1.35s "
            "cubic-bezier(.22,.8,.28,1) infinite both}"
        )
        # For index 0 start is 0, and "0%,0.00%" is a duplicate selector that
        # makes the whole @keyframes block invalid.
        head = "0%" if start == 0 else f"0%,{start:.2f}%"
        keyframes.append(
            f"@keyframes builder-msg-{index}{{"
            f"{head}{{opacity:0;transform:translateY(4px) scale(.96)}}"
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
  /* Motion curves: EASE_MOVE settles with weight, EASE_SWING snaps on
     impact then recovers, EASE_SOFT is for idle secondary motion. */
  #builder-route {{
    animation:builder-route 30s 1.35s cubic-bezier(.45,.05,.25,1)
      infinite both;
  }}
  #builder-scale {{
    animation:builder-visibility 30s 1.35s cubic-bezier(.4,0,.2,1)
      infinite both;
  }}
  #builder-pose {{
    transform-box:fill-box;
    transform-origin:center bottom;
    animation:builder-pose 30s 1.35s cubic-bezier(.45,.05,.25,1) infinite both;
  }}
  #builder-torso {{
    transform-box:fill-box;
    transform-origin:center bottom;
    animation:torso-breathe 3.4s cubic-bezier(.37,0,.63,1) infinite both;
  }}
  #builder-head {{
    transform-box:fill-box;
    transform-origin:center bottom;
    animation:head-turn 9s cubic-bezier(.37,0,.63,1) infinite both;
  }}
  #builder-mouth {{
    transform-box:fill-box;
    transform-origin:center;
    animation:mouth-talk 30s 1.35s cubic-bezier(.4,0,.2,1) infinite both;
  }}
  .builder-eye {{
    transform-box:fill-box;
    transform-origin:center;
    animation:eye-blink 30s 1.35s cubic-bezier(.4,0,.2,1) infinite both;
  }}
  .builder-pupil {{
    animation:pupil-look 6s cubic-bezier(.4,0,.2,1) infinite both;
  }}
  .builder-brow.a {{
    animation:brow-a 5.4s cubic-bezier(.4,0,.2,1) infinite both;
  }}
  .builder-brow.b {{
    animation:brow-b 5.4s cubic-bezier(.4,0,.2,1) infinite both;
  }}
  #builder-arm-left {{
    transform-box:fill-box;
    transform-origin:right top;
    animation:arm-left 30s 1.35s cubic-bezier(.6,-0.1,.35,1.25) infinite both;
  }}
  #builder-arm-right {{
    transform-box:fill-box;
    transform-origin:left top;
    animation:arm-right 30s 1.35s cubic-bezier(.6,-0.1,.35,1.25) infinite both;
  }}
  #builder-hammer {{
    transform-box:view-box;
    transform-origin:23px 18px;
    animation:builder-hammer 30s 1.35s cubic-bezier(.7,-0.3,.3,1.5) infinite both;
  }}
  .builder-leg.a {{
    transform-box:fill-box;
    transform-origin:center top;
    animation:leg-left 30s 1.35s cubic-bezier(.5,.02,.5,.98) infinite both;
  }}
  .builder-leg.b {{
    transform-box:fill-box;
    transform-origin:center top;
    animation:leg-right 30s 1.35s cubic-bezier(.5,.02,.5,.98) infinite both;
  }}
  #builder-hat {{
    transform-box:fill-box;
    transform-origin:center bottom;
    animation:hat-bob 3.4s cubic-bezier(.37,0,.63,1) infinite both;
  }}
  #hat-glint {{
    animation:hat-glint 4.8s cubic-bezier(.4,0,.2,1) infinite both;
  }}
  #builder-shadow {{
    transform-box:fill-box;
    transform-origin:center;
    animation:shadow-squash 30s 1.35s cubic-bezier(.4,0,.2,1) infinite both;
  }}
  .builder-ladder {{
    transform-box:fill-box;
    transform-origin:center bottom;
    animation:ladder-cycle 30s 1.35s cubic-bezier(.4,0,.2,1) infinite both;
  }}
  #target-block {{
    transform-box:fill-box;
    transform-origin:center bottom;
    animation:target-lift 30s 1.35s cubic-bezier(.34,1.2,.64,1)
      infinite both;
  }}
  #target-top {{
    animation:block-top-shimmer 3.2s cubic-bezier(.4,0,.2,1) infinite both;
  }}
  #target-front {{
    animation:block-front-glow 2.6s cubic-bezier(.4,0,.2,1) infinite both;
  }}
  #target-side {{
    animation:block-side-depth 3.6s cubic-bezier(.4,0,.2,1) infinite both;
  }}
  .target-shine {{
    animation:block-shine 3.4s cubic-bezier(.4,0,.2,1) infinite both;
  }}
  .target-glow {{
    animation:target-pulse 1.6s 1.35s cubic-bezier(.4,0,.2,1)
      infinite both;
  }}
  .builder-dust.a {{ animation:dust-a 30s 1.35s infinite both; }}
  .builder-dust.b {{ animation:dust-b 30s 1.35s infinite both; }}
  .builder-dust.c {{ animation:dust-c 30s 1.35s infinite both; }}
  .builder-spark.a {{ animation:spark-a 30s 1.35s infinite both; }}
  .builder-spark.b {{ animation:spark-b 30s 1.35s infinite both; }}
  .builder-spark.c {{ animation:spark-c 30s 1.35s infinite both; }}
  #sweat-drop {{ animation:sweat-drop 30s 1.35s infinite both; }}
  .dizzy-star.a {{ animation:dizzy-a 30s 1.35s infinite both; }}
  .dizzy-star.b {{ animation:dizzy-b 30s 1.35s infinite both; }}
  #builder-zzz {{ animation:zzz-float 30s 1.35s infinite both; }}
  #builder-alert {{ animation:alert-pop 30s 1.35s infinite both; }}
  #bed-blanket {{
    transform-box:fill-box;
    transform-origin:center bottom;
    animation:bed-blanket 30s 1.35s cubic-bezier(.37,0,.63,1)
      infinite both;
  }}
  #bed-pillow {{
    transform-box:fill-box;
    transform-origin:center;
    animation:bed-pillow 30s 1.35s cubic-bezier(.37,0,.63,1)
      infinite both;
  }}
  #sleeping-builder {{
    transform-box:fill-box;
    transform-origin:center bottom;
    animation:sleeping-builder 30s 1.35s cubic-bezier(.4,0,.2,1)
      infinite both;
  }}
  #sleeping-body {{
    transform-box:fill-box;
    transform-origin:left bottom;
    animation:sleeping-breath 3.8s cubic-bezier(.37,0,.63,1) infinite both;
  }}
  #builder-bed {{
    animation:bed-presence 30s 1.35s cubic-bezier(.4,0,.2,1) infinite both;
  }}
  .builder-msg {{ opacity:0; filter:url(#bubble-shadow); }}
  {message_css}

  @keyframes builder-route {{
    0%,3% {{ transform:translate({start_x}px,{ground_y}px); }}
    17%,22% {{ transform:translate({ground_x}px,{ground_y}px); }}
    29%,59% {{ transform:translate({target_x}px,{target_y}px); }}
    64% {{ transform:translate({target_x + 4}px,{target_y + 2}px); }}
    70% {{ transform:translate({ground_x + 5}px,{ground_y}px); }}
    77%,100% {{ transform:translate({start_x}px,{ground_y}px); }}
  }}
  @keyframes builder-visibility {{
    0%,77%,94%,100% {{ opacity:1; }}
    81%,91% {{ opacity:0; }}
  }}
  @keyframes builder-pose {{
    0%,3%,17%,22%,29%,59%,60% {{
      transform:translateY(0) rotate(0deg) scale(1);
    }}
    5%,9%,13%,19%,24%,71%,75% {{
      transform:translateY(-.7px) rotate(-.8deg) scale(.995,1.005);
    }}
    7%,11%,15%,21%,27%,73% {{
      transform:translateY(0) rotate(.8deg) scale(1.01,.99);
    }}
    31%,38%,45%,52% {{
      transform:translateY(1px) rotate(0deg) scale(1.025,.975);
    }}
    34%,41%,48%,55% {{
      transform:translateY(-.4px) rotate(0deg) scale(.99,1.01);
    }}
    63% {{ transform:rotate(14deg) scale(1.03,.97); }}
    67% {{ transform:rotate({fall_angle}deg) scale(.94); }}
    71%,76% {{ transform:rotate(0deg) scale(1); }}
    80%,91% {{ transform:rotate(0deg) scale(1.06,.72); }}
    94% {{ transform:rotate(0deg) scale(.96,1.04); }}
    97% {{ transform:rotate(-5deg) scale(.98,1.08); }}
    100% {{ transform:rotate(0deg) scale(1); }}
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
    0%,10%,22%,29%,60%,72%,77%,94%,100% {{
      transform:scaleX(1) scaleY(.75);
    }}
    6%,18%,34%,40%,46%,52%,58% {{
      transform:scaleX(1.12) scaleY(1.35);
    }}
    80%,91% {{ transform:scaleX(.75) scaleY(.2); }}
    97% {{ transform:scaleX(1.18) scaleY(1.5); }}
  }}
  @keyframes eye-blink {{
    0%,6%,8%,17%,19%,31%,33%,44%,46%,58%,60%,73%,75%,77%,94%,100% {{
      transform:scaleY(1);
    }}
    7%,18%,32%,45%,59%,74%,80%,91% {{ transform:scaleY(.08); }}
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
    0%,28%,60%,69%,77%,94%,100% {{ transform:rotate(0); }}
    29.5%,36.5%,43.5%,50.5% {{ transform:rotate(-34deg); }}
    31%,38%,45%,52% {{ transform:rotate(17deg); }}
    32%,39%,46%,53% {{ transform:rotate(21deg); }}
    34%,41%,48%,55% {{ transform:rotate(-18deg); }}
    58% {{ transform:rotate(-4deg); }}
    80%,91% {{ transform:rotate(-12deg); }}
    97% {{ transform:rotate(-26deg); }}
  }}
  @keyframes arm-right {{
    0%,28%,60%,69%,77%,94%,100% {{ transform:rotate(0); }}
    32%,59% {{ transform:rotate(-10deg); }}
    66% {{ transform:rotate(24deg); }}
    80%,91% {{ transform:rotate(-10deg); }}
    97% {{ transform:rotate(20deg); }}
  }}
  @keyframes builder-hammer {{
    0%,28%,59%,77%,94%,100% {{ transform:rotate(-48deg); opacity:1; }}
    29.5%,36.5%,43.5%,50.5% {{ transform:rotate(-72deg); opacity:1; }}
    31%,38%,45%,52% {{ transform:rotate(16deg); opacity:1; }}
    32%,39%,46%,53% {{ transform:rotate(25deg); opacity:1; }}
    34%,41%,48%,55% {{ transform:rotate(-50deg); opacity:1; }}
    57% {{ transform:rotate(-58deg); opacity:1; }}
    80%,91% {{ transform:rotate(-55deg); opacity:0; }}
  }}
  @keyframes leg-left {{
    0%,3%,17%,22%,29%,69%,77%,100% {{ transform:rotate(0); }}
    5%,9%,13%,19%,24%,71%,75% {{ transform:rotate(-18deg); }}
    7%,11%,15%,21%,27%,73% {{ transform:rotate(18deg); }}
  }}
  @keyframes leg-right {{
    0%,3%,17%,22%,29%,69%,77%,100% {{ transform:rotate(0); }}
    5%,9%,13%,19%,24%,71%,75% {{ transform:rotate(18deg); }}
    7%,11%,15%,21%,27%,73% {{ transform:rotate(-18deg); }}
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
  @keyframes zzz-float {{
    0%,78%,92%,100% {{ opacity:0; transform:translate(0,3px) scale(.8); }}
    82% {{ opacity:1; transform:translate(0,0) scale(1); }}
    90% {{ opacity:0; transform:translate(6px,-9px) scale(1.2); }}
  }}
  @keyframes alert-pop {{
    0%,92%,98%,100% {{ opacity:0; transform:scale(.4) rotate(-15deg); }}
    94%,96% {{ opacity:1; transform:scale(1.1) rotate(5deg); }}
  }}
  @keyframes bed-blanket {{
    0%,77%,94%,100% {{ transform:translateY(2px) scaleY(.88); opacity:0; }}
    81%,91% {{ transform:translateY(-1px) scaleY(1.05); opacity:1; }}
    84%,88% {{ transform:translateY(-2px) scaleY(1.1); opacity:1; }}
  }}
  @keyframes bed-pillow {{
    0%,77%,94%,100% {{ transform:scale(1); }}
    81%,91% {{ transform:scale(.92,1.08); }}
  }}
  @keyframes sleeping-builder {{
    0%,78%,94%,100% {{ opacity:0; transform:translateY(2px); }}
    81%,91% {{ opacity:1; transform:translateY(0); }}
  }}
  @keyframes sleeping-breath {{
    0%,100% {{ transform:scaleY(.96); }}
    50% {{ transform:scaleY(1.05); }}
  }}
  @keyframes bed-presence {{
    0%,75% {{ opacity:0; }}
    80%,93% {{ opacity:1; }}
    97%,100% {{ opacity:0; }}
  }}
  @media (prefers-reduced-motion:reduce) {{
    .c,#builder-route,#builder-scale,#builder-pose,#builder-torso,#builder-head,#builder-mouth,
    .builder-eye,.builder-pupil,.builder-brow,#builder-arm-left,
    #builder-arm-right,#builder-hammer,.builder-leg,#builder-hat,#hat-glint,
    #builder-shadow,.builder-ladder,#target-block,#target-top,#target-front,
    #target-side,.target-shine,.target-glow,.builder-dust,.builder-spark,
    #sweat-drop,.dizzy-star,#builder-bed,
    #builder-zzz,#builder-alert,#bed-blanket,#bed-pillow,
    #sleeping-builder,#sleeping-body,.builder-msg {{
      animation:none !important;
    }}
    .builder-msg {{ display:none; }}
    .builder-ladder {{ opacity:.55; }}
    .target-glow {{ opacity:.65; }}
  }}
</style>""".strip()


FONT = 7.6            # compact, still legible at README scale
CHAR_W = 4.45         # monospace advance at FONT
PAD_X = 8
BUBBLE_H = 27
BUBBLE_MAX = 145
BUBBLE_MIN = 88


def bubble_width(text: str, caption: str) -> int:
    """Size the bubble to its own text, so it never blankets the calendar."""
    return round(min(BUBBLE_MAX, max(
        BUBBLE_MIN,
        len(text) * CHAR_W + PAD_X * 2,
        len(caption) * 3.1 + PAD_X * 2,
    )))


def speech_bubble(
    css_class: str,
    text: str,
    right: int,
    y: int,
    accent: str,
    caption: str,
) -> list[str]:
    """Bubbles are right-anchored so the tail stays put as widths vary."""
    width = bubble_width(text, caption)
    x = right - width
    tail = x + width - 17
    return [
        f'<g class="builder-msg {css_class}" opacity="0">',
        f'<path d="M{tail} {y + BUBBLE_H}h8l-3 5z" fill="#111722" '
        'stroke="#4b5565" stroke-width=".7"/>',
        f'<rect x="{x}" y="{y}" width="{width}" height="{BUBBLE_H}" rx="5" '
        'fill="url(#bubble-bg)" stroke="#4b5565" stroke-width=".8"/>',
        f'<path d="M{x + 1} {y + 5}v{BUBBLE_H - 10}" stroke="{accent}" '
        'stroke-width="2" stroke-linecap="round"/>',
        f'<text x="{x + PAD_X}" y="{y + 9}" fill="{accent}" '
        'font-size="5.5" font-weight="700" letter-spacing=".55">'
        f'{caption.upper()}</text>',
        f'<text x="{x + PAD_X}" y="{y + 20.5}" fill="#e2e8f0" '
        f'font-size="{FONT}" font-weight="600">{text}</text>',
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

    # A compact worker leaves the site bunk, then climbs beside the target.
    target_worker_x = square_x - 32
    target_worker_y = square_y - 18
    ground_worker_x = target_worker_x
    ground_worker_y = oy + 6 * STEP + CELL - 30
    start_x = max(ox + 8, ground_worker_x - 125)

    ladder_top = square_y + 6
    ladder_bottom = oy + 6 * STEP + CELL - 1
    ladder_x1, ladder_x2 = square_x - 29, square_x - 17

    # Keep dialogue in the header band; it should never mask contribution data.
    widest = max(bubble_width(m, story["shift"]) for m in messages)
    bubble_right = min(width - PAD, max(ox + widest, square_x + CELL + 4))
    bubble_y = 6
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
            'stroke="#2f353d" stroke-width="4"/>',
            f'<line x1="{ladder_x1}" y1="{ladder_top}" '
            f'x2="{ladder_x1 - 2}" y2="{ladder_bottom}" '
            'stroke="url(#ladder-gold)" stroke-width="2"/>',
            f'<line x1="{ladder_x2 + 1}" y1="{ladder_top}" '
            f'x2="{ladder_x2 + 3}" y2="{ladder_bottom}" '
            'stroke="#2f353d" stroke-width="4"/>',
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
                'stroke="#8b95a2" stroke-width="1.6"/>'
            )
        scene.append("</g>")

    prop_y = oy + 7 * STEP - GAP + 6
    bed_x = start_x
    bed_y = prop_y - 1
    scene.extend([
        '<g id="builder-bed" opacity="0" filter="url(#builder-drop)">',
        f'<ellipse cx="{bed_x + 27}" cy="{bed_y + 14}" rx="27" ry="2.5" '
        'fill="#010409" opacity=".48"/>',
        f'<rect x="{bed_x}" y="{bed_y + 2}" width="54" height="10" rx="4" '
        'fill="#aeb8c6" stroke="#586273" stroke-width=".8"/>',
        f'<polygon points="{bed_x},{bed_y + 10} {bed_x + 54},{bed_y + 10} '
        f'{bed_x + 50},{bed_y + 15} {bed_x + 2},{bed_y + 15}" '
        'fill="#343c48" stroke="#657083" stroke-width=".8"/>',
        f'<rect id="bed-pillow" x="{bed_x + 38}" y="{bed_y + 3}" '
        'width="14" height="7" rx="3" fill="#d9dee7" '
        'stroke="#7e899a" stroke-width=".6"/>',
        f'<path d="M{bed_x + 3} {bed_y + 15}v4M{bed_x + 49} '
        f'{bed_y + 15}v4" stroke="#8b949e" stroke-width="2"/>',
        "</g>",
        # Cone and blueprint retired — four props in a row read as clutter.
        # The toolbox alone sets the scene and sits clear of the bunk.
        f'<g transform="translate({square_x - 62} {prop_y})">',
        '<g id="builder-toolbox">',
        '<polygon points="0,1 14,1 17,-2 3,-2" fill="#78849a"/>',
        '<rect x="0" y="1" width="14" height="8" rx="1.5" '
        'fill="url(#toolbox-front)" stroke="#343d4c" stroke-width=".8"/>',
        '<polygon points="14,1 17,-2 17,6 14,9" fill="#343d4c"/>',
        '<g id="toolbox-lid">',
        '<path d="M4-2v-4h7v4" fill="none" stroke="#9aa6ba" stroke-width="1.2"/>',
        '<path d="M1 1h14" stroke="#c6cfdd" stroke-width="1"/>',
        "</g>",
        '<circle cx="7" cy="5" r=".9" fill="#c9a55f"/>',
        "</g></g>",
        f'<circle class="builder-dust a" opacity="0" cx="{square_x - 2}" '
        f'cy="{square_y + 8}" r="2.2" fill="#c9a55f"/>',
        f'<circle class="builder-dust b" opacity="0" cx="{square_x + 4}" '
        f'cy="{square_y + 9}" r="1.7" fill="#c9d1d9"/>',
        f'<circle class="builder-dust c" opacity="0" cx="{square_x + 1}" '
        f'cy="{square_y + 6}" r="1.4" fill="#ffffff"/>',
        f'<path class="builder-spark a" opacity="0" '
        f'd="M{square_x + 1} {square_y + 2}l3-3M{square_x + 1} '
        f'{square_y - 1}l3 3" stroke="{accent}" stroke-width="1.2"/>',
        f'<path class="builder-spark b" opacity="0" '
        f'd="M{square_x + 7} {square_y + 3}l3-3M{square_x + 7} '
        f'{square_y}l3 3" stroke="#c9a55f" stroke-width="1.2"/>',
        f'<circle class="builder-spark c" opacity="0" cx="{square_x + 5}" '
        f'cy="{square_y}" r="1.5" fill="#ffffff"/>',
        f'<g id="builder-route" transform="translate({target_worker_x} {target_worker_y})">',
        '<g id="builder-scale" transform="scale(.86)">',
        '<ellipse id="builder-shadow" cx="15" cy="35" rx="15" ry="3" '
        'fill="#010409" opacity=".46"/>',
        '<g id="builder-pose" filter="url(#builder-drop)">',
        '<g class="builder-leg a">',
        '<path d="M8.5 25h6.3l-.4 8H7.8z" fill="url(#overalls-3d)" '
        'stroke="#252d3a" stroke-width=".55"/>',
        '<path d="M7.4 31.5h7.3l1.2 3.5H6.5q-.6-2.3.9-3.5z" '
        'fill="url(#boot-3d)" stroke="#171c24" stroke-width=".55"/>',
        "</g>",
        '<g class="builder-leg b">',
        '<path d="M15.8 25h6.7l.7 8h-7z" fill="url(#overalls-3d)" '
        'stroke="#252d3a" stroke-width=".55"/>',
        '<path d="M16.1 31.5h7.2l2.1 3.5H15.3q-.5-2.2.8-3.5z" '
        'fill="url(#boot-3d)" stroke="#171c24" stroke-width=".55"/>',
        "</g>",
        '<g id="builder-torso">',
        '<path d="M7 17q8-4 16 0l-.8 11H7.8z" fill="url(#shirt-3d)" '
        'stroke="#252d3a" stroke-width=".6"/>',
        '<path d="M19 16.2q4 .6 4 2.2L22.2 28h-3.3z" fill="#29313d" '
        'opacity=".5"/>',
        '<path d="M10 17.5h10l1 10H9z" fill="url(#overalls-3d)" '
        'stroke="#252d3a" stroke-width=".55"/>',
        '<path d="M10.5 18l1-3M19.5 18l-1-3M10 23h11" fill="none" '
        'stroke="#9ba9c3" stroke-width="1.1" stroke-linecap="round"/>',
        '<rect x="13" y="20.5" width="5" height="3.5" rx=".8" '
        'fill="#465674" stroke="#9ba9c3" stroke-width=".45"/>',
        '<circle cx="10.8" cy="18.8" r=".65" fill="#c9a55f"/>',
        '<circle cx="20" cy="18.8" r=".65" fill="#c9a55f"/>',
        "</g>",
        '<g id="builder-arm-left">',
        '<path d="M7.5 18L2.5 25" stroke="#252d3a" stroke-width="4.8" '
        'stroke-linecap="round"/>',
        '<path d="M7.5 18L2.5 25" stroke="url(#skin-3d)" stroke-width="3.7" '
        'stroke-linecap="round"/>',
        '<circle cx="2.5" cy="25" r="2.1" fill="url(#skin-3d)" '
        'stroke="#704b38" stroke-width=".5"/>',
        "</g>",
        '<g id="builder-arm-right">',
        '<path d="M22.5 18l5 6" stroke="#252d3a" stroke-width="4.8" '
        'stroke-linecap="round"/>',
        '<path d="M22.5 18l5 6" stroke="url(#skin-3d)" stroke-width="3.7" '
        'stroke-linecap="round"/>',
        '<circle cx="27.5" cy="24" r="2.1" fill="url(#skin-3d)" '
        'stroke="#704b38" stroke-width=".5"/>',
        "</g>",
        '<g id="builder-head">',
        '<rect x="12" y="14.5" width="7" height="4" rx="2" '
        'fill="#b68162" stroke="#704b38" stroke-width=".45"/>',
        '<circle cx="7.8" cy="10.3" r="2.2" fill="#c99170" '
        'stroke="#704b38" stroke-width=".45"/>',
        '<path d="M8 8q0-5 5-5.5h5q6 .4 6 6v3q0 6-6 6h-5q-5 0-5-5z" '
        'fill="url(#skin-3d)" stroke="#704b38" stroke-width=".65"/>',
        '<path d="M20 3.6q4 1.8 4 5v3q0 4.4-4 5.6 2-5.8 0-13.6z" '
        'fill="#8e5f46" opacity=".3"/>',
        '<path d="M8.2 8q1.3-4.8 5.4-5.3" fill="none" stroke="#4b352b" '
        'stroke-width="1.1" stroke-linecap="round"/>',
        '<g class="builder-brow a"><path d="M10.2 7.1h3.7" '
        'stroke="#4b352b" stroke-width=".9" stroke-linecap="round"/></g>',
        '<g class="builder-brow b"><path d="M17.2 7.1h3.7" '
        'stroke="#4b352b" stroke-width=".9" stroke-linecap="round"/></g>',
        '<g class="builder-eye">',
        '<rect x="10.2" y="8.1" width="4" height="2.9" rx="1.35" '
        'fill="#f4f6f8"/>',
        '<circle class="builder-pupil" cx="12.8" cy="9.55" r=".88" '
        'fill="#17202b"/>',
        "</g>",
        '<g class="builder-eye">',
        '<rect x="17.1" y="8.1" width="4" height="2.9" rx="1.35" '
        'fill="#f4f6f8"/>',
        '<circle class="builder-pupil" cx="19.7" cy="9.55" r=".88" '
        'fill="#17202b"/>',
        "</g>",
        '<path d="M15.8 9.9l-.6 2 1.5.25" fill="none" stroke="#8b5c45" '
        'stroke-width=".65" stroke-linecap="round" stroke-linejoin="round"/>',
        '<path id="builder-mouth" d="M13.2 14q2.8 1.9 5.6 0" fill="none" '
        'stroke="#623d34" stroke-width=".95" stroke-linecap="round"/>',
        '<g id="builder-hat">',
        '<path d="M7.2 5Q8-2 16-2t8.8 7z" fill="url(#hat-3d)" '
        'stroke="#6f5628" stroke-width=".7"/>',
        '<rect x="5.3" y="4.2" width="21.4" height="3" rx="1.5" '
        'fill="url(#hat-brim)" stroke="#6f5628" stroke-width=".45"/>',
        '<path d="M15.2-1v5.8" stroke="#e4c77f" stroke-width="1.5" '
        'opacity=".7"/>',
        '<path id="hat-glint" d="M10.3 1.2q2.8-2.5 5.5-1.2" fill="none" '
        'stroke="#fff7dd" stroke-width=".8" stroke-linecap="round" '
        'opacity=".55"/>',
        "</g>",
        "</g>",
        '<g id="builder-hammer">',
        '<path d="M23 18L31 24" stroke="#30271f" stroke-width="3.4" '
        'stroke-linecap="round"/>',
        '<path d="M23 18L31 24" stroke="url(#hammer-handle)" '
        'stroke-width="2.3" stroke-linecap="round"/>',
        '<path d="M28.5 20.2h8.5l2 1.8v4h-10.5z" fill="url(#hammer-metal)" '
        'stroke="#424b57" stroke-width=".75"/>',
        '<path d="M37 20.2l2 1.8v4h-2z" fill="#c9a55f" opacity=".9"/>',
        '<path d="M30.2 21h5.5" stroke="#f0f3f7" stroke-width=".65" '
        'stroke-linecap="round" opacity=".65"/>',
        "</g>",
        '<path id="sweat-drop" opacity="0" d="M25 8q3 4 0 6q-3-2 0-6" '
        'fill="#7897c5"/>',
        '<path class="dizzy-star a" opacity="0" d="M2 4l4-2M4 0l1 4" '
        'stroke="#c9a55f" stroke-width="1" stroke-linecap="round"/>',
        '<path class="dizzy-star b" opacity="0" d="M27 2l4-1M29-1v4" '
        'stroke="#c6cfdd" stroke-width=".9" stroke-linecap="round"/>',
        "</g>",
        "</g>",
        '<text id="builder-zzz" opacity="0" x="36" y="20" '
        'fill="#9886b8" font-size="6.5" font-weight="700">Zz</text>',
        '<g id="builder-alert" opacity="0">',
        '<circle cx="31" cy="2" r="4.5" fill="#c9a55f" stroke="#6f5628" '
        'stroke-width=".7"/>',
        '<text x="31" y="4" text-anchor="middle" fill="#0d1117" '
        'font-size="6.5" font-weight="800">!</text>',
        "</g>",
        "</g>",
        '<g id="sleeping-builder" opacity="0" filter="url(#builder-drop)">',
        '<g id="sleeping-body">',
        f'<path d="M{bed_x + 13} {bed_y + 5}q13-5 29 2v7H'
        f'{bed_x + 13}z" fill="url(#shirt-3d)" stroke="#252d3a" '
        'stroke-width=".55"/>',
        f'<path d="M{bed_x + 18} {bed_y + 6}h19v8H{bed_x + 18}z" '
        'fill="url(#overalls-3d)" stroke="#252d3a" stroke-width=".5"/>',
        f'<circle cx="{bed_x + 36}" cy="{bed_y + 5}" r="2.4" '
        'fill="url(#skin-3d)" stroke="#704b38" stroke-width=".45"/>',
        "</g>",
        f'<circle cx="{bed_x + 45}" cy="{bed_y + 7}" r="6.5" '
        'fill="url(#skin-3d)" stroke="#704b38" stroke-width=".65"/>',
        f'<path d="M{bed_x + 40} {bed_y + 5}q2-3 5-3" fill="none" '
        'stroke="#4b352b" stroke-width="1.1" stroke-linecap="round"/>',
        f'<path d="M{bed_x + 41} {bed_y + 7}q1.4 1 2.8 0M'
        f'{bed_x + 46} {bed_y + 7}q1.4 1 2.8 0" fill="none" '
        'stroke="#4b352b" stroke-width=".75" stroke-linecap="round"/>',
        f'<path d="M{bed_x + 43} {bed_y + 10}q2 1.5 4 0" fill="none" '
        'stroke="#623d34" stroke-width=".75" stroke-linecap="round"/>',
        f'<path d="M{bed_x - 1} {bed_y + 16}q1-6 7-6t7 6z" '
        'fill="url(#hat-3d)" stroke="#6f5628" stroke-width=".6"/>',
        f'<rect x="{bed_x - 3}" y="{bed_y + 15}" width="18" height="2.5" '
        'rx="1.2" fill="url(#hat-brim)"/>',
        "</g>",
        f'<path id="bed-blanket" d="M{bed_x + 3} {bed_y + 4}h35v9H'
        f'{bed_x + 3}q3-4 0-9z" fill="{accent}" stroke="#252d3a" '
        'stroke-width=".7" opacity="0"/>',
    ])

    # The shift caption is folded into each compact note.
    for index, message in enumerate(messages):
        scene.extend(
            speech_bubble(
                f"msg-{index}",
                message,
                bubble_right,
                bubble_y,
                accent,
                story["shift"],
            )
        )

    return css, scene


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    days = data["days"]

    first = dt.date.fromisoformat(days[0]["date"])
    first_sunday = first - dt.timedelta(days=(first.weekday() + 1) % 7)
    weeks = (dt.date.fromisoformat(days[-1]["date"]) - first_sunday).days // 7 + 1

    w = PAD + LEFT + weeks * STEP - GAP + PAD
    h = PAD + TOP + 7 * STEP - GAP + FOOTER_GAP + 14 + PAD

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" '
        f'font-size="11" role="img">',
        "<title>3D contribution heatmap with a weekday-aware animated commit builder</title>",
        """
<defs>
  <linearGradient id="hat-3d" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#f2d79b"/>
    <stop offset=".42" stop-color="#d2a54a"/>
    <stop offset="1" stop-color="#8a6420"/>
  </linearGradient>
  <linearGradient id="hat-brim" x1="0" y1="0" x2="0" y2="1">
    <stop stop-color="#e8cd8e"/><stop offset="1" stop-color="#94701f"/>
  </linearGradient>
  <linearGradient id="skin-3d" x1="0" y1="0" x2="1" y2="1">
    <stop stop-color="#eec4a6"/><stop offset=".55" stop-color="#d6a382"/>
    <stop offset="1" stop-color="#a2704f"/>
  </linearGradient>
  <linearGradient id="shirt-3d" x1="0" y1="0" x2="1" y2="1">
    <stop stop-color="#8a95a5"/><stop offset=".5" stop-color="#606b7b"/>
    <stop offset="1" stop-color="#3a424e"/>
  </linearGradient>
  <linearGradient id="overalls-3d" x1="0" y1="0" x2="1" y2="1">
    <stop stop-color="#7d8fb5"/><stop offset=".48" stop-color="#4e5f85"/>
    <stop offset="1" stop-color="#2b3448"/>
  </linearGradient>
  <linearGradient id="boot-3d" x1="0" y1="0" x2="0" y2="1">
    <stop stop-color="#6e7681"/><stop offset="1" stop-color="#21262d"/>
  </linearGradient>
  <linearGradient id="hammer-metal" x1="0" y1="0" x2="1" y2="1">
    <stop stop-color="#dfe5ec"/><stop offset=".4" stop-color="#aab4c0"/>
    <stop offset="1" stop-color="#4d545e"/>
  </linearGradient>
  <linearGradient id="hammer-handle" x1="0" y1="0" x2="1" y2="1">
    <stop stop-color="#b08963"/><stop offset="1" stop-color="#6b4d32"/>
  </linearGradient>
  <linearGradient id="ladder-gold" x1="0" y1="0" x2="1" y2="0">
    <stop stop-color="#b6c0cc"/><stop offset=".45" stop-color="#828d9b"/>
    <stop offset="1" stop-color="#464e58"/>
  </linearGradient>
  <linearGradient id="toolbox-front" x1="0" y1="0" x2="1" y2="1">
    <stop stop-color="#768298"/><stop offset="1" stop-color="#3d4656"/>
  </linearGradient>
  <linearGradient id="block-top" x1="0" y1="0" x2="1" y2="1">
    <stop stop-color="#b7ffd1"/><stop offset="1" stop-color="#39d353"/>
  </linearGradient>
  <linearGradient id="block-front" x1="0" y1="0" x2="1" y2="1">
    <stop stop-color="#56e878"/><stop offset="1" stop-color="#0b8f43"/>
  </linearGradient>
  <linearGradient id="bubble-bg" x1="0" y1="0" x2="0" y2="1">
    <stop stop-color="#1b2330"/><stop offset="1" stop-color="#111722"/>
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
                parts.append(f'<text x="{ox + wk * STEP}" y="{oy - 11}" '
                             f'fill="{TEXT}" font-size="9">'
                             f'{MONTHS[month - 1]}</text>')
            seen = month

    for label, row in (("Mon", 1), ("Wed", 3), ("Fri", 5)):
        parts.append(f'<text x="{PAD}" y="{oy + row * STEP + CELL - 2}" '
                     f'fill="{TEXT}" font-size="8.5">{label}</text>')

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
    ly = oy + 7 * STEP - GAP + FOOTER_GAP
    parts.append(f'<text x="{ox}" y="{ly + 9}" fill="{TEXT}" '
                 'font-size="8.5">Less</text>')
    for i, color in enumerate(PALETTE):
        parts.append(f'<rect x="{ox + 34 + i * STEP}" y="{ly}" width="{CELL}" '
                     f'height="{CELL}" rx="2.5" fill="{color}"/>')
    parts.append(f'<text x="{ox + 34 + len(PALETTE) * STEP + 4}" y="{ly + 10}" '
                 f'fill="{TEXT}" font-size="8.5">More</text>')

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
                 f'fill="{BRIGHT}" font-size="8.5" letter-spacing=".05">'
                 f'{stats}</text>')

    parts.append("</svg>")
    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"wrote {OUT} ({weeks} weeks)")


if __name__ == "__main__":
    main()
