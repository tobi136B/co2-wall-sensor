#!/usr/bin/env python3
"""Release notes for GitHub: the CHANGELOG section of a version plus a description of the assets.

Usage:  python tools/release_notes.py 1.3.0 > release_notes.md
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = "https://tobi136b.github.io/co2-wall-sensor/"

ASSETS = f"""
### Downloads

| File | What it is |
|------|------------|
| `co2_wall_sensor_device.3mf`, `co2_wall_sensor_mounts.3mf` | print-ready plates, every part in its print orientation |
| `sensor_carrier_14x22.stl`, `sensor_carrier_15x20.stl` | sensor carrier, print the one matching your SCD41 board ([measure your sensor](https://github.com/tobi136B/co2-wall-sensor/blob/main/docs/measure-sensor.md)); the device plate contains the 14x22 carrier |
| `*.stl` | single print files |
| `co2_wall_sensor_assembly.step` | full assembly for any CAD program |
| `co2_wall_sensor_drawing_en.pdf`, `..._de.pdf` | technical drawing, A3 |
| `co2-wall-sensor-en-installer.factory.bin`, `...-de-installer...` | firmware of the [browser installer]({PAGE}), no credentials inside |
| `co2-wall-sensor-en.*.bin`, `co2-wall-sensor-de.*.bin` | CI builds of the own-build configuration (test only, CI credentials) |

The easiest way to flash: open the [project page]({PAGE}), connect the ESP32-C3 via USB and click **Install**.
Devices flashed this way show new releases as a firmware update in Home Assistant.

**Deutsch:** Druckfertige 3MF-Platten, einzelne STL, STEP, Zeichnung (EN/DE) und Firmware.
Am einfachsten flashen: [Projektseite]({PAGE}) öffnen, ESP32-C3 per USB anschließen, **Installieren** klicken.
"""


def enclosure_version() -> str:
    """Version of the printed parts, written by the Fusion export into cad/build_info.json."""
    info = json.loads((ROOT / "cad" / "build_info.json").read_text(encoding="utf-8"))
    return info["enclosure_version"]


def version_line(version: str) -> str:
    enc = enclosure_version()
    return (
        f"> **Release {version} · Enclosure v{enc}** (engraved on every printed part)  \n"
        f"> Parts that show v{enc} belong to this release. "
        f"**Deutsch:** Release {version}, Gehäuse v{enc} (auf jedem gedruckten Teil eingeprägt)."
    )


def section(version: str) -> str:
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    m = re.search(rf"^## \[?{re.escape(version)}\]?.*?$(.*?)(?=^## |\Z)", text, flags=re.M | re.S)
    if not m:
        return f"Release {version}."
    body = m.group(1).strip()
    return body.split("\n---")[0].strip()


if __name__ == "__main__":
    print(version_line(sys.argv[1]))
    print()
    print(section(sys.argv[1]))
    print(ASSETS)
