#!/usr/bin/env python3
"""Prep a photo for ASCII conversion: remove background, boost local
contrast with CLAHE, composite onto pure white.

Usage:  python scripts/prep_photo.py source-photo.jpg

Writes source-prepped.png (grayscale) next to the repo root.
Run this once per photo; it is not part of the daily workflow.
Requires: pillow, numpy, opencv-python, rembg
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "source-prepped.png"


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: python scripts/prep_photo.py <photo>")
    src = Path(sys.argv[1])

    # 1. Isolate the subject.
    subject = remove(Image.open(src)).convert("RGBA")

    # 2. CLAHE on the luminance channel — gives a flatly-lit face real
    #    highlights and shadows so the ASCII ramp has something to map.
    rgba = np.array(subject)
    gray = cv2.cvtColor(rgba[:, :, :3], cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    # 3. Composite onto pure white so the background maps to the blank
    #    end of the ramp (white -> spaces).
    alpha = rgba[:, :, 3].astype(np.float32) / 255.0
    out = (gray.astype(np.float32) * alpha + 255.0 * (1.0 - alpha)).astype(np.uint8)

    Image.fromarray(out, mode="L").save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
