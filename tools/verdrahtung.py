#!/usr/bin/env python3
"""
Verdrahtungsplan als Grafik (docs/bilder/verdrahtung.png).

Die Pinbelegung wird aus esphome/co2-wandsensor.yaml gelesen, damit Plan und
Firmware nicht auseinanderlaufen.

Aufruf:  python tools/verdrahtung.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import yaml  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
YAML_DATEI = ROOT / "esphome" / "co2-wandsensor.yaml"
AUSGABE = ROOT / "docs" / "bilder" / "verdrahtung.png"


class _Lader(yaml.SafeLoader):
    """Laedt ESPHome-YAML inkl. !secret, ohne die Werte aufzuloesen."""


_Lader.add_constructor("!secret", lambda loader, node: f"<secret {node.value}>")


def pins() -> dict[str, str]:
    cfg = yaml.load(YAML_DATEI.read_text(encoding="utf-8"), Loader=_Lader)
    i2c, spi, disp = cfg["i2c"], cfg["spi"], cfg["display"][0]
    bl = next(o for o in cfg["output"] if o["id"] == "pwm_hintergrund")
    return {
        "SDA": i2c["sda"], "SCL": i2c["scl"],
        "CLK": spi["clk_pin"], "DIN": spi["mosi_pin"],
        "CS": disp["cs_pin"], "DC": disp["dc_pin"], "RST": disp["reset_pin"], "BL": bl["pin"],
    }


def main():
    p = pins()
    fig, ax = plt.subplots(figsize=(11, 6.2))
    ax.set_xlim(0, 110)
    ax.set_ylim(0, 66)
    ax.axis("off")
    farben = {"3V3": "#d62728", "GND": "#222222", "SDA": "#1f77b4", "SCL": "#17becf",
              "CLK": "#ff7f0e", "DIN": "#9467bd", "CS": "#2ca02c", "DC": "#8c564b",
              "RST": "#e377c2", "BL": "#bcbd22"}

    def modul(x, y, b, h, titel, sub, fc):
        ax.add_patch(FancyBboxPatch((x, y), b, h, boxstyle="round,pad=0.6,rounding_size=1.8",
                                    fc=fc, ec="#333", lw=1.2))
        ax.text(x + b / 2, y + h + 4.6, titel, ha="center", va="bottom", fontsize=12, weight="bold")
        ax.text(x + b / 2, y + h + 1.6, sub, ha="center", va="bottom", fontsize=8.5, color="#555")

    # ESP32-C3 in der Mitte
    ex, ey, eb, eh = 42, 8, 22, 44
    modul(ex, ey, eb, eh, "ESP32-C3 SuperMini", "USB-C = Strom + Flashen", "#eef3fb")
    # Display rechts, SCD41 links
    dx, dy, db, dh = 86, 14, 18, 38
    modul(dx, dy, db, dh, "Waveshare 2\" LCD", "ST7789V, 240x320, SPI", "#f4f4f4")
    sx, sy, sb, sh = 6, 26, 16, 20
    modul(sx, sy, sb, sh, "SCD41", "CO2 / Temp / Feuchte, I2C", "#f4f4f4")

    lcd = [("3V3", "VCC"), ("GND", "GND"), ("DIN", "DIN"), ("CLK", "CLK"),
           ("CS", "CS"), ("DC", "DC"), ("RST", "RST"), ("BL", "BL")]
    for i, (sig, pin) in enumerate(lcd):
        y = dy + dh - 4 - i * 4.4
        gpio = "3V3" if sig == "3V3" else "GND" if sig == "GND" else p[sig].replace("GPIO", "GPIO ")
        ax.plot([ex + eb, dx], [y, y], color=farben[sig], lw=2.4, solid_capstyle="round")
        ax.text(ex + eb - 1, y, gpio, ha="right", va="center", fontsize=8.5, family="monospace")
        ax.text(dx + 1, y, pin, ha="left", va="center", fontsize=8.5, family="monospace")
        ax.text((ex + eb + dx) / 2, y + 0.9, sig if sig not in ("3V3", "GND") else "", ha="center",
                fontsize=7, color=farben[sig])

    scd = [("3V3", "VDD"), ("GND", "GND"), ("SDA", "SDA"), ("SCL", "SCL")]
    for i, (sig, pin) in enumerate(scd):
        y = sy + sh - 4 - i * 4.4
        gpio = "3V3" if sig == "3V3" else "GND" if sig == "GND" else p[sig].replace("GPIO", "GPIO ")
        ax.plot([sx + sb, ex], [y, y], color=farben[sig], lw=2.4, solid_capstyle="round")
        ax.text(sx + sb - 1, y, pin, ha="right", va="center", fontsize=8.5, family="monospace")
        ax.text(ex + 1, y, gpio, ha="left", va="center", fontsize=8.5, family="monospace")

    ax.text(55, 2.2, "Alle Module mit 3,3 V aus dem ESP32-C3. Kabel mit ca. 6 cm Laenge reichen. "
            "Pinbelegung automatisch aus esphome/co2-wandsensor.yaml.", ha="center", fontsize=8.5, color="#555")
    AUSGABE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(AUSGABE, dpi=140, bbox_inches="tight", facecolor="white")
    print(f"Verdrahtungsplan geschrieben: {AUSGABE}")


if __name__ == "__main__":
    main()
