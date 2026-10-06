#!/usr/bin/env python3
"""
README animation from the frames rendered in Fusion (cad/fusion/render_views.py, render_hero()).

Every frame comes with the camera of Fusion. The display content of tools/display_preview.py is
projected onto the glass of the display, so the device shows its real interface while it turns,
falls apart and assembles itself again. One GIF per language.

Usage:   python tools/build_gif.py FRAME_DIR
Output:  docs/images/hero_en.gif, docs/images/hero_de.gif
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import display_preview  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "images"
SIZE = (800, 500)
FRAME_MS = 60
HOLD_MS = 700


def project(cam: dict, points: list) -> list[tuple[float, float]]:
    """Perspective projection like the Fusion viewport (vertical field of view)."""
    eye, target, up = (np.array(cam[k], float) for k in ("eye", "target", "up"))
    w, h = cam["size"]
    f = target - eye
    f /= np.linalg.norm(f)
    r = np.cross(f, up)
    r /= np.linalg.norm(r)
    u = np.cross(r, f)
    s = (h / 2) / math.tan(cam["fov"] / 2)
    out = []
    for p in points:
        v = np.array(p, float) - eye
        out.append((w / 2 + (v @ r) / (v @ f) * s, h / 2 - (v @ u) / (v @ f) * s))
    return out


def homography(src: list, dst: list) -> list[float]:
    """Coefficients for Image.transform(PERSPECTIVE): maps output (dst) coordinates to input (src)."""
    a, b = [], []
    for (x, y), (u, v) in zip(dst, src, strict=True):
        a += [[x, y, 1, 0, 0, 0, -u * x, -u * y], [0, 0, 0, x, y, 1, -v * x, -v * y]]
        b += [u, v]
    return list(np.linalg.solve(np.array(a, float), np.array(b, float)))


def frame(png: Path, lang: str, i: int, count: int) -> Image.Image:
    cam = json.loads(png.with_suffix(".json").read_text(encoding="utf-8"))
    rgba = Image.open(png).convert("RGBA")
    base = Image.alpha_composite(Image.new("RGBA", rgba.size, (255, 255, 255, 255)), rgba)
    # the display shows its interface, the CO2 value breathes a little
    t = i / count
    co2 = round(620 + 22 * math.sin(2 * math.pi * t))
    ui = display_preview.screen(lang, "good", co2, 21.4, 45, "08:15", 760, "falling", None).convert("RGBA")
    quad = project(cam, cam["screen"])
    src = [(0, 0), (ui.width, 0), (ui.width, ui.height), (0, ui.height)]
    coeffs = homography(src, quad)
    warped = ui.transform(base.size, Image.Transform.PERSPECTIVE, coeffs, Image.Resampling.BICUBIC)
    mask = Image.new("L", ui.size, 255).transform(
        base.size, Image.Transform.PERSPECTIVE, coeffs, Image.Resampling.BILINEAR
    )
    base.paste(warped, (0, 0), mask)
    # crop the middle of the wide viewport to the GIF aspect ratio
    w, h = base.size
    cw = min(w, round(h * SIZE[0] / SIZE[1]))
    x0 = (w - cw) // 2
    return base.crop((x0, 0, x0 + cw, h)).convert("RGB").resize(SIZE, Image.Resampling.LANCZOS)


def build(frames_dir: Path, lang: str) -> Path:
    pngs = sorted(frames_dir.glob("hero_*.png"))
    count = len(pngs)
    frames = [frame(p, lang, i, count) for i, p in enumerate(pngs)]
    # one shared palette keeps the colours stable from frame to frame
    sheet = Image.new("RGB", (SIZE[0], SIZE[1] * 4))
    for k, idx in enumerate((0, count // 4, count // 2, 3 * count // 4)):
        sheet.paste(frames[idx], (0, k * SIZE[1]))
    palette = sheet.quantize(colors=128, method=Image.Quantize.MEDIANCUT)
    quant = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
    durations = [FRAME_MS] * count
    durations[0] = HOLD_MS * 2  # assembled, showing the display
    durations[count // 2] = HOLD_MS  # fully apart
    out = OUT_DIR / f"hero_{lang}.gif"
    quant[0].save(out, save_all=True, append_images=quant[1:], duration=durations, loop=0, optimize=True)
    print(f"written: {out.relative_to(ROOT)} ({count} frames, {out.stat().st_size // 1024} KB)")
    return out


def main() -> int:
    frames_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if not frames_dir or not frames_dir.is_dir():
        print(__doc__)
        return 2
    for lang in ("en", "de"):
        build(frames_dir, lang)
    return 0


if __name__ == "__main__":
    sys.exit(main())
