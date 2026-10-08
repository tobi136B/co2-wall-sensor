#!/usr/bin/env python3
"""
Values of the Fusion generator that the online configurator needs (site/carrier.js).

The configurator builds only the sensor carrier. Everything that does not depend on the SCD41
board comes from the generator, so the browser and Fusion always build the same part.

Usage:   python tools/carrier_params.py OUT.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import drawing  # noqa: E402

BOARD_KEYS = ("SCD_W", "SCD_L", "SCD_PCB", "SCD_H", "SCD_SENSOR_X", "SCD_SENSOR_Y", "SCD_PAD_X")
# enclosure values used by build_sensor_carrier() and check_scd_fit()
BASE_KEYS = (
    "XL XR WALL Y_CHIN_LOW Y_DIV_LOW FLOOR_Z FLOOR_T COVER_SCREWS CARRIER_SCREWS BOSS_D BOSS_FILLET "
    "SCREW_CLEAR_D SCD_LIP SCD_STOP SPRING_X SPRING_W SPRING_L SPRING_T SPRING_HOOK SPRING_PRELOAD "
    "LOCK_POINTS LOCK_BOSS_Y1 CLEARANCE PLUG_BODY_D C3_X BOOT_Y BOOT_PLAY C3_Y0 C3_Z0 C3_W C3_PCB "
    "C3_PLAY C3_RIB C3_PCB_MAX MIN_WALL SCD_SLOT_W SCD_CHANNEL_W CLIP_LIP"
).split()


def data() -> dict:
    p = drawing.load_parameters()
    base = {}
    for k in BASE_KEYS:
        v = p[k]
        base[k] = [list(c) for c in v] if isinstance(v, list) else list(v) if isinstance(v, tuple) else v
    return {"base": base, "boards": p["SCD_BOARDS"]}


if __name__ == "__main__":
    Path(sys.argv[1]).write_text(json.dumps(data(), indent=1) + "\n", encoding="utf-8")
    print(f"written: {sys.argv[1]}")
