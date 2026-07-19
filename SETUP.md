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

## 2. Turn the banner into your portrait

Right now `borna-ascii.svg` is a block-letter "BORNA" banner. To replace
it with an ASCII portrait of your photo:

```sh
python3 -m venv .venv && source .venv/bin/activate
pip install -r scripts/requirements.txt
python scripts/prep_photo.py path/to/your-photo.jpg   # writes source-prepped.png
python scripts/make_ascii_svg.py                      # now renders the portrait
```

Use a well-lit photo with a clear subject; the script removes the
background, boosts contrast (CLAHE), and composites onto white so only
you print — the background becomes spaces.

Then commit `borna-ascii.svg` (you can gitignore `source-prepped.png` if
you don't want the photo derivative in the repo).

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
