#!/usr/bin/env python3
"""
README animation from the frames rendered in Fusion (cad/fusion/render_views.py, render_hero()).

The frames show the device from assembled (t = 0) to apart (t = 1). Played forwards and backwards,
the device takes itself apart and assembles itself again; it rests a moment in both states.
Rendered at twice the size and scaled down, so the edges stay clean.

Usage:   python tools/build_gif.py FRAME_DIR
Output:  docs/images/exploded.gif
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "images" / "exploded.gif"
SIZE = (800, 500)
FRAME_MS = 40  # 25 frames per second
HOLD_ASSEMBLED_MS = 1100
HOLD_APART_MS = 1600


def load(path: Path) -> Image.Image:
    rgba = Image.open(path).convert("RGBA")
    white = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    return Image.alpha_composite(white, rgba).convert("RGB").resize(SIZE, Image.Resampling.LANCZOS)


def main() -> int:
    frames_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if not frames_dir or not frames_dir.is_dir():
        print(__doc__)
        return 2
    frames = [load(p) for p in sorted(frames_dir.glob("hero_*.png"))]
    count = len(frames)
    # one shared palette keeps the colours stable from frame to frame
    sheet = Image.new("RGB", (SIZE[0], SIZE[1] * 3))
    for k, idx in enumerate((0, count // 2, count - 1)):
        sheet.paste(frames[idx], (0, k * SIZE[1]))
    palette = sheet.quantize(colors=128, method=Image.Quantize.MEDIANCUT)
    quant = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
    loop = quant + quant[-2:0:-1]  # apart, then together again
    durations = [FRAME_MS] * len(loop)
    durations[0] = HOLD_ASSEMBLED_MS
    durations[count - 1] = HOLD_APART_MS
    loop[0].save(OUT, save_all=True, append_images=loop[1:], duration=durations, loop=0, optimize=True, disposal=1)
    print(f"written: {OUT.relative_to(ROOT)} ({len(loop)} frames, {OUT.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
