#!/usr/bin/env python3
"""
Exploded animation for the README from the frames rendered in Fusion.

Render the frames with render_frames() in cad/fusion/render_views.py, then:

Usage:   python tools/build_gif.py FRAME_DIR
Output:  docs/images/exploded.gif
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "images" / "exploded.gif"
FRAME_MS = 70
HOLD_MS = 900  # assembled and fully exploded state


def load(path: Path) -> Image.Image:
    rgba = Image.open(path).convert("RGBA")
    bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    return Image.alpha_composite(bg, rgba).convert("RGB")


def main() -> int:
    frames_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if not frames_dir or not frames_dir.is_dir():
        print(__doc__)
        return 2
    paths = sorted(frames_dir.glob("frame_*.png"))
    frames = [load(p) for p in paths]
    count = len(frames)
    # one shared palette keeps the colours stable from frame to frame
    sheet = Image.new("RGB", (frames[0].width, frames[0].height * 4))
    for i, k in enumerate((0, count // 4, count // 2, 3 * count // 4)):
        sheet.paste(frames[k], (0, i * frames[0].height))
    palette = sheet.quantize(colors=128, method=Image.Quantize.MEDIANCUT)
    quant = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
    # hold where the animation rests: assembled (frame 0) and fully exploded (40 to 50 % of the loop)
    durations = [FRAME_MS] * count
    durations[0] = HOLD_MS
    durations[int(count * 0.45)] = HOLD_MS
    quant[0].save(OUT, save_all=True, append_images=quant[1:], duration=durations, loop=0, optimize=True, disposal=1)
    print(f"written: {OUT.relative_to(ROOT)} ({count} frames, {OUT.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
