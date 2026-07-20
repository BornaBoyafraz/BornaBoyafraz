# Setup

This folder becomes your GitHub **profile repo** — a repo named exactly
`BornaBoyafraz` whose README renders on your profile page.

## 1. Publish it

This content currently lives in the `BornaBoyafrazProfile` repo. GitHub
only renders a profile README from a **public** repo named exactly
`BornaBoyafraz`, so to put it on the profile page:

1. Rename (or delete) the old private `BornaBoyafraz` repo — e.g. to
   `old-profile-readme` — in that repo's Settings.
2. Rename `BornaBoyafrazProfile` → `BornaBoyafraz` in Settings (or
   `gh repo rename BornaBoyafraz -R BornaBoyafraz/BornaBoyafrazProfile`).
3. Keep it public.

## 2. Regenerate the portrait (already done once)

`borna-ascii.svg` is the ASCII portrait built from your photo. To redo it
with a different photo, use a **Python 3.11** venv — the background
remover (`rembg` + `onnxruntime`) has no wheels for 3.12+:

```sh
python3.11 -m venv .venv-portrait && source .venv-portrait/bin/activate
pip install pillow numpy opencv-python-headless rembg onnxruntime
python scripts/prep_photo.py path/to/your-photo.jpg   # removes bg, crops, CLAHE -> source-prepped.png
python scripts/make_ascii_svg.py                      # source-prepped.png -> borna-ascii.svg
```

Use a well-lit photo with a clear subject; the script isolates you, crops
to your bounding box, boosts contrast, and composites onto white so only
you print (the background becomes spaces). `source-photo.*` and
`source-prepped.png` are gitignored — only `borna-ascii.svg` is committed.

## 3. Keep the heatmap fresh

`.github/workflows/update-profile-art.yml` re-scrapes your public
contribution calendar daily (~06:17 UTC) and commits a fresh
`contrib-heatmap.svg`. No token needed — it reads the public HTML at
`github.com/users/BornaBoyafraz/contributions`.

After the first push, open the repo's **Actions** tab and run
**Update profile art** once by hand (workflow_dispatch) to confirm it
commits a fresh SVG.

## 4. Edit your info

- Info card content (Now / Learning / links…): edit `ROWS` in
  `scripts/make_info_card.py`, then `python scripts/make_info_card.py`.
- Everything is animated SVG placed by the README — GitHub strips
  `<script>` and inline CSS from READMEs, but plays SMIL/CSS animations
  inside SVGs embedded via `<img>`.
- `STATIC=1 python scripts/<any make/render script>.py` emits a frozen
  frame for quick local previews.
