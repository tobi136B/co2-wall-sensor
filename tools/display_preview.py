#!/usr/bin/env python3
"""
Preview of the 320 x 240 display layout in all three air quality states.

This is a pixel mock-up of the lambda in esphome/common/base.yaml, intended for
the README and for design reviews without hardware. Positions and colours are
the same as in the firmware; fonts may differ slightly (Inter on the device).

Usage:   python tools/display_preview.py
Output:  docs/images/display_preview_en.png, docs/images/display_preview_de.png
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "images"
W, H = 320, 240
SCALE = 2

COLORS = {
    "green": (0x2E, 0xCC, 0x71),
    "yellow": (0xF5, 0xB7, 0x00),
    "red": (0xE7, 0x4C, 0x3C),
    "text": (0xF2, 0xF2, 0xF2),
    "muted": (0x7A, 0x7F, 0x87),
    "line": (0x2A, 0x2E, 0x35),
}
TEXT = {
    "en": {
        "good": "Good",
        "moderate": "Moderate",
        "ventilate": "Ventilate!",
        "sep": ".",
        "fc": "ventilate in ~{m} min",
        "hum": "HUMIDITY",
        "cool": "Open the window: cooler outside",
        "dry": "Airing dries the air",
        "warm": "Keep it shut: warmer outside",
    },
    "de": {
        "good": "Gut",
        "moderate": "Mäßig",
        "ventilate": "Lüften!",
        "sep": ",",
        "fc": "lüften in ca. {m} min",
        "hum": "FEUCHTE",
        "cool": "Fenster auf: außen kühler",
        "dry": "Lüften trocknet die Luft",
        "warm": "Fenster zu: außen wärmer",
    },
}
# (state, CO2, temperature, humidity, time, trend start, trend arrow, minutes until red)
STATES = [
    ("good", 642, 21.4, 45, "08:15", 760, "falling", None),
    ("moderate", 1180, 22.1, 51, "13:40", 780, "rising", 44),
    ("ventilate", 1620, 23.0, 58, "19:05", 980, "steady", None),
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "Inter-Bold.ttf" if bold else "Inter-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for c in candidates:
        try:
            return ImageFont.truetype(c, size * SCALE)
        except OSError:
            continue
    return ImageFont.load_default()


def s(v: float) -> int:
    return int(round(v * SCALE))


def text(d: ImageDraw.ImageDraw, xy, txt, f, fill, anchor="la"):
    d.text((s(xy[0]), s(xy[1])), txt, font=f, fill=fill, anchor=anchor)


def arrow(d: ImageDraw.ImageDraw, x_right: float, y_top: float, kind: str, fill) -> None:
    """Trend arrow like mdi-arrow-top-right / -right / -bottom-right, 26 px box, right aligned."""
    cx, cy, r = x_right - 13, y_top + 13, 8
    dx, dy = {"rising": (1, -1), "steady": (1.414, 0), "falling": (1, 1)}[kind]
    tip = (cx + dx * r * 0.75, cy + dy * r * 0.75)
    tail = (cx - dx * r * 0.75, cy - dy * r * 0.75)
    d.line([s(tail[0]), s(tail[1]), s(tip[0]), s(tip[1])], fill=fill, width=s(3))
    # arrow head: two short strokes back from the tip
    ang = math.atan2(dy, dx)
    for a in (ang + 2.5, ang - 2.5):
        d.line([s(tip[0]), s(tip[1]), s(tip[0] + 6 * math.cos(a)), s(tip[1] + 6 * math.sin(a))], fill=fill, width=s(3))


HINT_COLORS = {"cool": (90, 190, 255), "dry": (90, 190, 255), "warm": (255, 170, 60)}


def screen(
    lang: str,
    state: str,
    co2: int,
    temp: float,
    hum: int,
    clock: str,
    start: int,
    trend: str,
    forecast,
    outdoor: float | None = None,
    hint: str | None = None,
) -> Image.Image:
    t = TEXT[lang]
    img = Image.new("RGB", (s(W), s(H)), (0, 0, 0))
    d = ImageDraw.Draw(img)
    level = COLORS[{"good": "green", "moderate": "yellow", "ventilate": "red"}[state]]

    text(d, (12, 8), clock, font(20, True), COLORS["text"])
    # WiFi glyph as three arcs
    for r in (4, 8, 12):
        d.arc([s(W - 24 - r), s(22 - r), s(W - 24 + r), s(22 + r)], 225, 315, fill=COLORS["muted"], width=s(2))

    pw, ph = 140, 26
    px, py = (W - pw) / 2, 9
    d.rounded_rectangle([s(px), s(py), s(px + pw), s(py + ph)], radius=s(ph / 2), fill=level)
    text(d, (W / 2, py + ph / 2 + 1), t[state], font(14, True), (0, 0, 0), "mm")

    text(d, (W / 2 - 18, 84), f"{co2}", font(62, True), level, "mm")
    text(d, (W - 14, 74), "ppm", font(13), COLORS["muted"], "rd")
    text(d, (W - 14, 94), "CO2", font(13), COLORS["muted"], "rd")
    arrow_col = {"rising": level, "steady": COLORS["muted"], "falling": COLORS["green"]}[trend]
    arrow(d, W - 14, 100, trend, arrow_col)

    # trend: smooth synthetic 3 h curve towards the current value
    gx, gy, gw, gh = 10, 132, 300, 64
    vals = [start + (co2 - start) * (i / 59) ** 1.6 + 25 * math.sin(i / 6) for i in range(60)]
    lo, hi = min(vals + [400]), max(vals) + 50
    pts = [(gx + i * gw / 59, gy + gh - (v - lo) / (hi - lo) * gh) for i, v in enumerate(vals)]
    for hx in range(1, 3):
        x = gx + hx * gw / 3
        d.line([s(x), s(gy), s(x), s(gy + gh)], fill=COLORS["line"], width=1)
    d.line([(s(x), s(y)) for x, y in pts], fill=level, width=s(2))
    d.line([s(10), s(199), s(W - 10), s(199)], fill=COLORS["line"], width=s(1))
    text(d, (12, 132), "3h", font(12), COLORS["muted"])
    if forecast:
        text(d, (W - 12, 196), t["fc"].format(m=forecast), font(12), COLORS["muted"], "rd")
    if hint:  # only when opening the window really helps (or would make it worse)
        text(d, (12, 196), t[hint], font(12, True), HINT_COLORS[hint], "ld")

    # footer: three columns with a small label above each value, like an instrument panel
    def column(x, label, value, colour, anchor):
        text(d, (x, 210), label, font(10, True), COLORS["muted"], anchor[0] + "m")
        text(d, (x, 228), value, font(19, True), colour, anchor[0] + "m")

    def celsius(v):
        return f"{v:.1f}".replace(".", t["sep"]) + " °C"

    column(14, "IN", celsius(temp), COLORS["text"], "l")
    if outdoor is not None:  # outdoor temperature from Home Assistant
        column(116, "OUT", celsius(outdoor), (175, 182, 190), "l")
        for x in (106, 214):
            d.line([s(x), s(205), s(x), s(234)], fill=COLORS["line"], width=s(1))
    column(W - 14, t["hum"], f"{hum} %", COLORS["text"], "r")
    return img


def bezel(img: Image.Image) -> Image.Image:
    pad = s(14)
    out = Image.new("RGB", (img.width + 2 * pad, img.height + 2 * pad), (255, 255, 255))
    d = ImageDraw.Draw(out)
    d.rounded_rectangle([0, 0, out.width - 1, out.height - 1], radius=s(16), fill=(24, 24, 26))
    out.paste(img, (pad, pad))
    return out


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for lang in TEXT:
        tiles = [bezel(screen(lang, *st)) for st in STATES]
        gap = s(10)
        sheet = Image.new(
            "RGB", (sum(t.width for t in tiles) + gap * (len(tiles) + 1), tiles[0].height + 2 * gap), (255, 255, 255)
        )
        x = gap
        for tile in tiles:
            sheet.paste(tile, (x, gap))
            x += tile.width + gap
        out = OUT_DIR / f"display_preview_{lang}.png"
        sheet.save(out, optimize=True)
        print(f"written: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
