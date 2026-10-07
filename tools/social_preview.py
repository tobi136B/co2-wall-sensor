#!/usr/bin/env python3
"""
Social preview of the repository (GitHub settings, link previews of the project page).

Composes the current render docs/images/hero_wall.png with the title and the CO2 scale, so the preview
always shows the current enclosure. Uses the Inter font when it is installed.

Usage:   python tools/social_preview.py
Output:  docs/images/social_preview.png (1280 x 640)
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
IMAGES = ROOT / "docs" / "images"
SIZE = (1280, 640)
BG = (238, 240, 241)
INK = (29, 34, 38)
MUTED = (93, 102, 110)
SCALE = [((46, 204, 113), 0.375), ((245, 183, 0), 0.25), ((231, 76, 60), 0.375)]


def font(size: int, weight: str = "Regular") -> ImageFont.FreeTypeFont:
    for name in (
        f"/usr/share/fonts/opentype/inter/Inter-{weight}.otf",
        f"Inter-{weight}.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if weight != "Regular"
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def main() -> None:
    img = Image.new("RGB", SIZE, BG)
    d = ImageDraw.Draw(img)
    d.text((72, 190), "CO2 Wall Sensor", font=font(76, "ExtraBold"), fill=INK, anchor="ls")
    for k, line in enumerate(("CO2, temperature and humidity", "for Home Assistant. Wall or desk.")):
        d.text((72, 280 + k * 44), line, font=font(31), fill=MUTED, anchor="ls")
    x, w = 72, 520
    for colour, part in SCALE:
        d.rectangle([x, 392, x + w * part, 410], fill=colour)
        x += w * part
    # round ends of the scale
    d.ellipse([63, 392, 81, 410], fill=SCALE[0][0])
    d.ellipse([72 + w - 9, 392, 72 + w + 9, 410], fill=SCALE[-1][0])
    d.text((72, 456), "ESP32-C3 · SCD41 · ESPHome · 3D printed", font=font(23), fill=MUTED, anchor="ls")
    render = Image.open(IMAGES / "hero_wall.png").convert("RGBA")
    render = render.crop(render.getbbox())
    render.thumbnail((520, 520), Image.Resampling.LANCZOS)
    img.paste(render, (980 - render.width // 2, 320 - render.height // 2), render)
    out = IMAGES / "social_preview.png"
    img.save(out, optimize=True)
    print(f"written: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
