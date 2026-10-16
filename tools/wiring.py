#!/usr/bin/env python3
"""
Wiring diagram as an image, in English and German.

The pin assignment is read from esphome/common/base.yaml, so diagram and
firmware can never drift apart.

Usage:   python tools/wiring.py
Output:  docs/images/wiring_en.png, docs/images/wiring_de.png
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import yaml  # noqa: E402
from matplotlib import patheffects as pe  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
YAML_FILE = ROOT / "esphome" / "common" / "base.yaml"
OUT_DIR = ROOT / "docs" / "images"

TEXT = {
    "en": {
        "esp_sub": "USB-C = power + flashing",
        "lcd_sub": "ST7789V, 240x320, SPI",
        "scd_sub": "CO2 / temp / humidity, I2C",
        "footer": "All modules run on 3.3 V from the ESP32-C3. SCD41: about 8 cm of silicone wire in these colours. "
        "Display: the colours of the supplied Waveshare cable, check VCC and BL at the labels of the socket.\n"
        "Pins are read from esphome/common/base.yaml.",
        "colour": {
            "3V3": "purple",
            "GND": "white",
            "DIN": "green",
            "CLK": "orange",
            "CS": "yellow",
            "DC": "blue",
            "RST": "brown",
            "BL": "grey",
        },
        "colour_scd": {"3V3": "red", "GND": "black", "SDA": "blue", "SCL": "yellow"},
    },
    "de": {
        "esp_sub": "USB-C = Strom + Flashen",
        "lcd_sub": "ST7789V, 240x320, SPI",
        "scd_sub": "CO2 / Temp / Feuchte, I2C",
        "footer": "Alle Module mit 3,3 V aus dem ESP32-C3. SCD41: ca. 8 cm Silikonlitze in diesen Farben. "
        "Display: Farben des mitgelieferten Waveshare-Kabels, VCC und BL an der Beschriftung der Buchse prüfen.\n"
        "Pinbelegung automatisch aus esphome/common/base.yaml.",
        "colour": {
            "3V3": "lila",
            "GND": "weiß",
            "DIN": "grün",
            "CLK": "orange",
            "CS": "gelb",
            "DC": "blau",
            "RST": "braun",
            "BL": "grau",
        },
        "colour_scd": {"3V3": "rot", "GND": "schwarz", "SDA": "blau", "SCL": "gelb"},
    },
}


class _Loader(yaml.SafeLoader):
    """Loads ESPHome YAML including !secret without resolving the values."""


_Loader.add_constructor("!secret", lambda loader, node: f"<secret {node.value}>")


def pins() -> dict[str, str]:
    cfg = yaml.load(YAML_FILE.read_text(encoding="utf-8"), Loader=_Loader)
    i2c, spi, disp = cfg["i2c"], cfg["spi"], cfg["display"][0]
    bl = next(o for o in cfg["output"] if o["id"] == "backlight_pwm")
    return {
        "SDA": i2c["sda"],
        "SCL": i2c["scl"],
        "CLK": spi["clk_pin"],
        "DIN": spi["mosi_pin"],
        "CS": disp["cs_pin"],
        "DC": disp["dc_pin"],
        "RST": disp["reset_pin"],
        "BL": bl["pin"],
    }


def render(lang: str, p: dict[str, str]):
    t = TEXT[lang]
    fig, ax = plt.subplots(figsize=(11, 6.2))
    ax.set_xlim(0, 110)
    ax.set_ylim(0, 66)
    ax.axis("off")
    # display: the colours of the supplied Waveshare cable, SCD41: the silicone wire set of the bill of materials
    lcd_farben = {
        "3V3": "#8e44ad",  # lila
        "GND": "#ffffff",  # weiß
        "DIN": "#2ca02c",  # grün
        "CLK": "#ff7f0e",  # orange
        "CS": "#f2c500",  # gelb
        "DC": "#1f77b4",  # blau
        "RST": "#8c564b",  # braun
        "BL": "#9a9a9a",  # grau
    }
    scd_farben = {"3V3": "#d62728", "GND": "#222222", "SDA": "#1f77b4", "SCL": "#f2c500"}
    outline = [pe.Stroke(linewidth=3.6, foreground="#555"), pe.Normal()]  # keeps the white wire visible

    def module_box(x, y, b, h, titel, sub, fc):
        ax.add_patch(FancyBboxPatch((x, y), b, h, boxstyle="round,pad=0.6,rounding_size=1.8", fc=fc, ec="#333", lw=1.2))
        ax.text(x + b / 2, y + h + 4.6, titel, ha="center", va="bottom", fontsize=12, weight="bold")
        ax.text(x + b / 2, y + h + 1.6, sub, ha="center", va="bottom", fontsize=8.5, color="#555")

    # ESP32-C3 in der Mitte
    ex, ey, eb, eh = 42, 8, 22, 44
    module_box(ex, ey, eb, eh, "ESP32-C3 SuperMini", t["esp_sub"], "#eef3fb")
    # Display rechts, SCD41 links
    dx, dy, db, dh = 86, 14, 18, 38
    module_box(dx, dy, db, dh, 'Waveshare 2" LCD', t["lcd_sub"], "#f4f4f4")
    sx, sy, sb, sh = 6, 26, 16, 20
    module_box(sx, sy, sb, sh, "SCD41", t["scd_sub"], "#f4f4f4")

    lcd = [
        ("3V3", "VCC"),
        ("GND", "GND"),
        ("DIN", "DIN"),
        ("CLK", "CLK"),
        ("CS", "CS"),
        ("DC", "DC"),
        ("RST", "RST"),
        ("BL", "BL"),
    ]
    for i, (sig, pin) in enumerate(lcd):
        y = dy + dh - 4 - i * 4.4
        gpio = "3V3" if sig == "3V3" else "GND" if sig == "GND" else p[sig].replace("GPIO", "GPIO ")
        ax.plot([ex + eb, dx], [y, y], color=lcd_farben[sig], lw=2.4, solid_capstyle="round", path_effects=outline)
        ax.text(ex + eb - 1, y, gpio, ha="right", va="center", fontsize=8.5, family="monospace")
        ax.text(dx + 1, y, pin, ha="left", va="center", fontsize=8.5, family="monospace")
        ax.text(
            (ex + eb + dx) / 2,
            y + 0.9,
            t["colour"][sig],
            ha="center",
            fontsize=7,
            color="#666",
        )

    scd = [("3V3", "VDD"), ("GND", "GND"), ("SDA", "SDA"), ("SCL", "SCL")]
    for i, (sig, pin) in enumerate(scd):
        y = sy + sh - 4 - i * 4.4
        gpio = "3V3" if sig == "3V3" else "GND" if sig == "GND" else p[sig].replace("GPIO", "GPIO ")
        ax.plot([sx + sb, ex], [y, y], color=scd_farben[sig], lw=2.4, solid_capstyle="round")
        ax.text((sx + sb + ex) / 2, y + 0.9, t["colour_scd"][sig], ha="center", fontsize=7, color="#666")
        ax.text(sx + sb - 1, y, pin, ha="right", va="center", fontsize=8.5, family="monospace")
        ax.text(ex + 1, y, gpio, ha="left", va="center", fontsize=8.5, family="monospace")

    ax.text(55, 2.2, t["footer"], ha="center", fontsize=8.5, color="#555")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"wiring_{lang}.png"
    fig.savefig(out, dpi=140, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"written: {out.relative_to(ROOT)}")


def main():
    p = pins()
    for lang in TEXT:
        render(lang, p)


if __name__ == "__main__":
    main()
