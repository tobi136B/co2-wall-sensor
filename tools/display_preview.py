#!/usr/bin/env python3
"""
Preview of the 320 x 240 display layout in all three air quality states and in the four window states.

This is a pixel mock-up of the lambda in esphome/common/base.yaml, intended for
the README and for design reviews without hardware. Positions and colours are
the same as in the firmware; fonts may differ slightly (Inter on the device).

Usage:   python tools/display_preview.py
Output:  docs/images/display_preview_{en,de}.png (air quality), docs/images/display_window_{en,de}.png (window)
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
        "airing_pill": "Airing",
        "sep": ".",
        "fc": "ventilate in ~{m} min",
        "hum": "HUMIDITY",
        "cool": "Open the window: cooler outside",
        "dry": "Airing dries the air",
        "warm": "Keep it shut: warmer outside",
        "short": "Air briefly: warmer outside",
        "airing": "Airing for 6 min",
        "fresh": "Fresh air: close the window",
        "cold": "Close the window: room cools down",
    },
    "de": {
        "good": "Gut",
        "moderate": "Mäßig",
        "ventilate": "Lüften!",
        "airing_pill": "Lüftet",
        "sep": ",",
        "fc": "lüften in ca. {m} min",
        "hum": "FEUCHTE",
        "cool": "Fenster auf: außen kühler",
        "dry": "Lüften trocknet die Luft",
        "warm": "Fenster zu: außen wärmer",
        "short": "Kurz stoßlüften: außen wärmer",
        "airing": "Lüftet seit 6 min",
        "fresh": "Luft frisch: Fenster zu",
        "cold": "Fenster zu: Raum kühlt aus",
    },
}
# (state, CO2, temperature, humidity, time, trend start, trend arrow, minutes until red, outdoor, window hint,
#  window: None without a contact, "closed", or the hint that colours the open window)
STATES = [
    ("good", 642, 21.4, 45, "08:15", 760, "falling", None, 14.5, None, "closed"),
    ("moderate", 1180, 22.1, 63, "13:40", 780, "rising", 44, 9.0, "dry", "closed"),
    ("ventilate", 1620, 25.6, 52, "19:05", 980, "steady", None, 17.5, "cool", "closed"),
]
# window contact from Home Assistant: shut (grey), airing (blue), fresh again (green), room cools down (orange)
WINDOW_STATES = [
    ("good", 655, 21.6, 47, "07:40", 700, "steady", None, 8.5, None, "closed"),
    ("ventilate", 1480, 21.2, 55, "10:20", 1650, "falling", None, 8.5, "airing", "airing"),
    ("good", 690, 20.4, 50, "10:31", 1450, "falling", None, 8.5, "fresh", "fresh"),
    ("good", 880, 18.6, 52, "10:36", 1400, "falling", None, 8.5, "cold", "cold"),
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


BLUE, ORANGE = (0x5A, 0xBE, 0xFF), (0xFF, 0xAA, 0x3C)  # col_cool and col_warm of the firmware
HINT_COLORS = {
    "cool": BLUE,
    "dry": BLUE,
    "warm": ORANGE,
    "short": ORANGE,
    "airing": BLUE,
    "fresh": COLORS["green"],
    "cold": ORANGE,
}


def window_icon(d: ImageDraw.ImageDraw, x_right: float, y_top: float, kind: str) -> None:
    """Window symbol like mdi-window-closed-variant / -open-variant, 22 px box, right aligned."""
    fill = COLORS["muted"] if kind == "closed" else HINT_COLORS[kind]
    x0, y0, x1, y1 = x_right - 19, y_top + 2, x_right - 3, y_top + 20
    w = s(2)
    if kind == "closed":
        d.rectangle([s(x0), s(y0), s(x1), s(y1)], outline=fill, width=w)
        d.line([s((x0 + x1) / 2), s(y0), s((x0 + x1) / 2), s(y1)], fill=fill, width=w)
        d.line([s(x0), s((y0 + y1) / 2), s(x1), s((y0 + y1) / 2)], fill=fill, width=w)
        return
    # open: frame on the left half, the sash swung out to the right as a parallelogram
    xm = (x0 + x1) / 2
    d.line([s(xm), s(y0), s(x0), s(y0), s(x0), s(y1), s(xm), s(y1)], fill=fill, width=w, joint="curve")
    d.polygon([s(xm), s(y0), s(x1 + 1), s(y0 - 2), s(x1 + 1), s(y1 + 2), s(xm), s(y1)], outline=fill, width=w)


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
    window: str | None = None,
) -> Image.Image:
    t = TEXT[lang]
    img = Image.new("RGB", (s(W), s(H)), (0, 0, 0))
    d = ImageDraw.Draw(img)
    level = COLORS[{"good": "green", "moderate": "yellow", "ventilate": "red"}[state]]

    text(d, (12, 8), clock, font(20, True), COLORS["text"])
    # WiFi glyph as three arcs
    for r in (4, 8, 12):
        d.arc([s(W - 24 - r), s(22 - r), s(W - 24 + r), s(22 + r)], 225, 315, fill=COLORS["muted"], width=s(2))
    if window:  # left of the WiFi symbol, only with a window contact (switch in Home Assistant)
        window_icon(d, W - 42, 10, window)

    pw, ph = 140, 26
    px, py = (W - pw) / 2, 9
    d.rounded_rectangle([s(px), s(py), s(px + pw), s(py + ph)], radius=s(ph / 2), fill=level)
    window_is_open = window not in (None, "closed")
    # red with an open window: the pill says you are airing instead of asking for it (as in the firmware)
    pill = t["airing_pill"] if state == "ventilate" and window_is_open else t[state]
    text(d, (W / 2, py + ph / 2 + 1), pill, font(14, True), (0, 0, 0), "mm")

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
    hint_end = 0
    if hint:  # only when opening the window really helps (or would make it worse), marker in front
        r = 4
        d.ellipse([s(17 - r), s(188 - r), s(17 + r), s(188 + r)], fill=HINT_COLORS[hint])
        text(d, (27, 196), t[hint], font(12, True), HINT_COLORS[hint], "ld")
        hint_end = 27 + d.textlength(t[hint], font=font(12, True)) / SCALE
    if forecast and not window_is_open:  # gives way to the hint when both do not fit side by side (as in the firmware)
        fc = t["fc"].format(m=forecast)
        if not hint or W - 12 - d.textlength(fc, font=font(12)) / SCALE > hint_end + 12:
            text(d, (W - 12, 196), fc, font(12), COLORS["muted"], "rd")

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


def sheet_of(lang: str, states: list, columns: int) -> Image.Image:
    tiles = [bezel(screen(lang, *st)) for st in states]
    gap = s(10)
    rows = math.ceil(len(tiles) / columns)
    tw, th = tiles[0].width, tiles[0].height
    sheet = Image.new("RGB", (columns * tw + gap * (columns + 1), rows * th + gap * (rows + 1)), (255, 255, 255))
    for i, tile in enumerate(tiles):
        sheet.paste(tile, (gap + (i % columns) * (tw + gap), gap + (i // columns) * (th + gap)))
    return sheet


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for lang in TEXT:
        for name, states, columns in (("display_preview", STATES, 3), ("display_window", WINDOW_STATES, 2)):
            out = OUT_DIR / f"{name}_{lang}.png"
            sheet_of(lang, states, columns).save(out, optimize=True)
            print(f"written: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
