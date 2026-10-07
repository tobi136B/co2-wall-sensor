#!/usr/bin/env python3
"""
Data of the interactive 3D assembly guide (site/assembly.html, site/assembly.js).

Every printed part comes as the STL of cad/stl, already in its assembled position. The bought
parts (display, SCD41, ESP32-C3, USB plug, inserts, screws, wires) are built here from the
parameters of the Fusion generator, so the guide always matches the current enclosure.

Coordinates in mm as in the generator: front face z = 0, wall towards +z, y up.
The x axis points to the left as seen from the front.

Usage:   python tools/assembly_model.py OUT_DIR
Output:  OUT_DIR/assembly.json, OUT_DIR/screen_en.png, OUT_DIR/screen_de.png and the STL files
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import display_preview  # noqa: E402
import drawing  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
STEPS = ROOT / "site" / "assembly_steps.yaml"

# colours: housing in anthracite, wall plate in switch white, as recommended in docs/assembly.md
PRINT_DARK = "#3b3f46"
PRINT_MID = "#4a4f57"
PRINT_LIGHT = "#5c626b"
PRINT_WHITE = "#eceae4"
PCB_BLUE = "#1d4e9e"
PCB_BLACK = "#1c1f24"
BRASS = "#c9a227"
STEEL = "#a7adb4"
GOLD = "#d9b23a"
RUBBER = "#202226"

# wire colours of docs/wiring.md (tools/wiring.py)
WIRE = {
    "3V3": "#d62728",
    "GND": "#2b2b2b",
    "SDA": "#1f77b4",
    "SCL": "#17becf",
    "CLK": "#ff7f0e",
    "DIN": "#9467bd",
    "CS": "#2ca02c",
    "DC": "#8c564b",
    "RST": "#e377c2",
    "BL": "#bcbd22",
}

INSERT_D, INSERT_L = 3.2, 3.0
SCREW_HEAD_D, SCREW_HEAD_H, SCREW_D, SCREW_L = 3.5, 1.1, 2.0, 4.0  # ISO 7380 M2 x 4


def box(x0, y0, z0, x1, y1, z1, color, mat="plastic"):
    return {"type": "box", "min": [x0, y0, z0], "max": [x1, y1, z1], "color": color, "mat": mat}


def cyl(p, d, length, dia, color, mat="metal"):
    """Cylinder from point p along the unit vector d."""
    return {"type": "cyl", "p": list(p), "d": list(d), "len": length, "r": dia / 2, "color": color, "mat": mat}


def insert(p, d=(0, 0, -1)):
    """Heat-set insert, p is the flush top, d points into the material."""
    return cyl(p, d, INSERT_L, INSERT_D, BRASS, "brass")


def screw(p, d):
    """M2 x 4 screw, p is where the head rests, d points into the material."""
    head = [p[i] - d[i] * SCREW_HEAD_H for i in range(3)]
    return [cyl(head, d, SCREW_HEAD_H, SCREW_HEAD_D, STEEL), cyl(p, d, SCREW_L, SCREW_D, STEEL)]


def stl(name, color):
    return {"type": "stl", "file": f"{name}.stl", "color": color, "mat": "print"}


def part(pid, en, de, groups, meshes):
    return {"id": pid, "name": {"en": en, "de": de}, "groups": groups, "meshes": meshes}


def wires_display(p: dict) -> list[dict]:
    """8 wires from the display connector over the back of the display to the ESP32-C3 (schematic path)."""
    top = p["LIP"] + p["GLASS_T"] + p["LCD_PCB"] + 6
    cx = p["BAY_X0"] + 7
    esp_x = p["C3_X"] - p["C3_W"] / 2 + 1.3
    esp_top = p["C3_Z0"] + p["C3_PCB"]
    names = ["3V3", "GND", "DIN", "CLK", "CS", "DC", "RST", "BL"]
    out = []
    for i, n in enumerate(names):
        y0 = p["LCD_Y"] + (i - 3.5) * 2.0
        y1 = p["C3_Y0"] + p["C3_H"] - 1.6 - i * 2.54
        lift = 14.0 + i * 0.45
        pts = [
            [cx, y0, top],
            [cx, y0, lift],
            [cx + 10, y0 - 1, lift + 0.5],
            [-4, (y0 + y1) / 2, lift + 1.5],
            [esp_x - 3, y1, esp_top + 2.5],
            [esp_x, y1, esp_top + 1.2],
            [esp_x, y1, esp_top],
        ]
        out.append({"color": WIRE[n], "points": pts, "label": n})
    return out


def wires_scd(p: dict) -> list[dict]:
    """4 wires from the SCD41 pads through the notch of the carrier to the ESP32-C3 (schematic path)."""
    pad_x = -p["SCD_PAD_X"]
    yc = p["SCD_Y0"] + p["SCD_L"] / 2
    esp_x = p["C3_X"] + p["C3_W"] / 2 - 1.3
    esp_top = p["C3_Z0"] + p["C3_PCB"]
    out = []
    for k, n in enumerate(["GND", "3V3", "SCL", "SDA"]):
        y0 = yc + (k - 1.5) * 2.54
        y1 = p["C3_Y0"] + p["C3_H"] - 1.6 - k * 2.54
        lift = 18.4 + k * 0.45
        pts = [
            [pad_x, y0, p["SCD_ZT"]],
            [pad_x, y0, lift - 2],
            [pad_x + 4, y0 + 1, lift],
            [p["C3_X"] - 3, p["C3_Y0"] + 4 + k, lift + 0.6],
            [esp_x + 3, y1, esp_top + 2.5],
            [esp_x, y1, esp_top + 1.2],
            [esp_x, y1, esp_top],
        ]
        out.append({"color": WIRE[n], "points": pts, "label": n})
    return out


def parts(p: dict) -> list[dict]:
    lip, glass_t, lcd_pcb = p["LIP"], p["GLASS_T"], p["LCD_PCB"]
    lcd_back = lip + glass_t + lcd_pcb
    cl = p["CLEARANCE"]
    zb = p["SCD_ZT"] - p["SCD_PCB"]
    sx, sy = -p["SCD_SENSOR_X"], p["SCD_Y0"] + p["SCD_L"] / 2 + p["SCD_SENSOR_Y"]
    c3x, c3y, c3z = p["C3_X"], p["C3_Y0"], p["C3_Z0"]
    c3top = c3z + p["C3_PCB"]
    mouth, usb_w = p["C3_MOUTH"], p["C3_USB_W"] / 2
    lock_y = -p["PLATE"] / 2 + 2.0 + p["INSERT_HOLE_D"] / 2 + 0.2
    lx0, lx1 = p["LOCK_POINTS"]

    display = [
        box(
            p["LCD_X"] - p["GLASS_W"] / 2 + 0.1,
            p["LCD_Y"] - p["GLASS_H"] / 2,
            lip,
            p["LCD_X"] + p["GLASS_W"] / 2 + 0.1,
            p["LCD_Y"] + p["GLASS_H"] / 2,
            lip + glass_t,
            "#0d1117",
            "glass",
        ),
        box(p["BAY_X0"] + cl, p["BAY_Y0"] + cl, lip + glass_t, p["BAY_X1"] - cl, p["BAY_Y1"] - cl, lcd_back, PCB_BLUE),
        box(p["BAY_X0"] + 4, p["LCD_Y"] - 10, lcd_back, p["BAY_X0"] + 10, p["LCD_Y"] + 10, lcd_back + 6, "#f1efe8"),
        {"type": "screen", "centre": [0, p["LCD_Y"], lip - 0.02], "size": [p["ACTIVE_W"], p["ACTIVE_H"]]},
    ]
    scd = [
        box(-p["SCD_W"] / 2, p["SCD_Y0"], zb, p["SCD_W"] / 2, p["SCD_TOP"], p["SCD_ZT"] - 0.01, PCB_BLACK),
        box(sx - 5.05, sy - 5.05, zb - p["SCD_H"], sx + 5.05, sy + 5.05, zb, "#b9bec5", "metal"),
    ]
    for k in range(4):
        y = p["SCD_Y0"] + p["SCD_L"] / 2 + (k - 1.5) * 2.54
        scd.append(cyl((-p["SCD_PAD_X"], y, p["SCD_ZT"] - 0.02), (0, 0, 1), 0.08, 1.6, GOLD, "brass"))
    esp = [
        box(c3x - p["C3_W"] / 2, c3y, c3z, c3x + p["C3_W"] / 2, c3y + p["C3_H"], c3top, PCB_BLUE),
        box(c3x - usb_w, mouth, c3top, c3x + usb_w, c3y + 7.0, p["SOCKET_TOP"], STEEL, "metal"),
        # the two buttons next to the socket, the tallest parts on the board
        box(c3x - 8.0, c3y + 2.5, c3top, c3x - 5.0, c3y + 5.5, c3top + p["C3_PARTS_H"], "#2a2d31"),
        box(c3x + 5.0, c3y + 2.5, c3top, c3x + 8.0, c3y + 5.5, c3top + p["C3_PARTS_H"], "#2a2d31"),
        box(c3x - 2.5, c3y + 10, c3top, c3x + 2.5, c3y + 15, c3top + 0.8, "#15171a"),
        box(c3x - 6.5, c3y + p["C3_H"] - 4.5, c3top, c3x + 1.5, c3y + p["C3_H"] - 1.2, c3top + 0.5, "#e8e4da"),
    ]
    for side in (-1, 1):
        for j in range(8):
            y = c3y + p["C3_H"] - 1.6 - j * 2.54
            esp.append(cyl((c3x + side * (p["C3_W"] / 2 - 1.3), y, c3top - 0.02), (0, 0, 1), 0.06, 1.5, GOLD, "brass"))
    # right-angle plug with a round aluminium body (measured), the cable leaves towards the wall
    z0 = p["PLUG_Z"] - p["PLUG_CAP"]
    z1 = z0 + p["PLUG_BODY_L"]
    plug = [
        box(c3x - 4.0, p["BOOT_Y"], p["PLUG_Z"] - 2.5, c3x + 4.0, mouth - 0.3, p["PLUG_Z"] + 2.5, RUBBER),
        cyl((c3x, p["BOOT_Y"], z0), (0, 0, 1), p["PLUG_BODY_L"], p["PLUG_BODY_D"], "#9aa1a9", "metal"),
        cyl((c3x, p["BOOT_Y"], z1), (0, 0, 1), p["PLUG_BOOT_L"], p["PLUG_BOOT_D"], RUBBER, "rubber"),
        cyl((c3x, p["BOOT_Y"], z1 + p["PLUG_BOOT_L"]), (0, 0, 1), 8, 3.6, "#3a3d42", "rubber"),
    ]
    inserts = [insert((x, y, lip + glass_t)) for x, y in p["LCD_HOLES"]]
    inserts += [insert((x, y, p["COVER_Z"])) for x, y in p["COVER_SCREWS"]]
    inserts += [insert((x, y, p["FLOOR_Z"])) for x, y in p["CARRIER_SCREWS"]]
    display_screws = [m for x, y in p["LCD_HOLES"] for m in screw((x, y, lcd_back), (0, 0, -1))]
    carrier_screws = [m for x, y in p["CARRIER_SCREWS"] for m in screw((x, y, p["FLOOR_Z"] + p["FLOOR_T"]), (0, 0, -1))]
    cover_screws = [m for x, y in p["COVER_SCREWS"] for m in screw((x, y, p["DEPTH"] - p["HEAD_H"]), (0, 0, -1))]
    y_tab = -p["BODY"] / 2 - 0.2
    lock_screw_housing = screw((lx0, y_tab - p["HEAD_H"], p["LOCK_Z"]), (0, 1, 0))
    lock_screw_plate = screw((lx1, lock_y, p["DEPTH"] - p["HEAD_H"]), (0, 0, 1))

    dev, car, wall = ["device"], ["device", "carrier"], ["wall"]
    return [
        part("housing", "Housing", "Gehäuse", dev, [stl("housing", PRINT_DARK)]),
        part("inserts", "10 heat-set inserts M2", "10 Einschmelzmuttern M2", dev, inserts),
        part("display", 'Display 2" (Waveshare)', 'Display 2" (Waveshare)', dev, display),
        part("display_screws", "4 screws M2 × 4", "4 Schrauben M2 × 4", dev, display_screws),
        part(
            "carrier",
            "Sensor carrier 13.5 × 21.75",
            "Sensorträger 13,5 × 21,75",
            car,
            [stl("sensor_carrier_14x22", PRINT_LIGHT)],
        ),
        part("scd41", "SCD41 sensor", "SCD41-Sensor", car, scd),
        part("esp32", "ESP32-C3 SuperMini", "ESP32-C3 SuperMini", car, esp),
        part("plug", "USB-C angled plug", "USB-C-Winkelstecker", car, plug),
        part("carrier_screws", "2 screws M2 × 4", "2 Schrauben M2 × 4", dev, carrier_screws),
        part("wires_display", "Display wires", "Displaylitzen", dev, [{"type": "tube", **w} for w in wires_display(p)]),
        part("wires_scd", "SCD41 wires", "SCD41-Litzen", car, [{"type": "tube", **w} for w in wires_scd(p)]),
        part("port", "Cable port module (back)", "Kabelport-Modul (hinten)", dev, [stl("cable_port_back", PRINT_MID)]),
        part("cover", "Back cover", "Rückdeckel", dev, [stl("back_cover", PRINT_MID)]),
        part("cover_screws", "4 screws M2 × 4", "4 Schrauben M2 × 4", dev, cover_screws),
        part("wall_plate", "Wall plate", "Wandplatte", wall, [stl("wall_plate", PRINT_WHITE)]),
        part(
            "lock_insert_housing",
            "Heat-set insert M2 (housing)",
            "Einschmelzmutter M2 (Gehäuse)",
            dev,
            [insert((lx0, -p["BODY"] / 2, p["LOCK_Z"]), (0, 1, 0))],
        ),
        part(
            "lock_insert_plate",
            "Heat-set insert M2 (wall plate)",
            "Einschmelzmutter M2 (Wandplatte)",
            wall,
            [insert((lx1, lock_y, p["DEPTH"]), (0, 0, 1))],
        ),
        part("lock_tab", "Lock tab (optional)", "Sicherungslasche (optional)", ["lock"], [stl("lock_tab", PRINT_DARK)]),
        part("lock_screw_housing", "Screw M2 × 4 (housing)", "Schraube M2 × 4 (Gehäuse)", ["lock"], lock_screw_housing),
        part(
            "lock_screw_plate", "Screw M2 × 4 (wall plate)", "Schraube M2 × 4 (Wandplatte)", ["lock"], lock_screw_plate
        ),
    ]


# Stages of the guide: offsets of whole groups, reached along the waypoints (and left the same way back),
# so the carrier leaves the housing through the open back before it moves down.
STAGES = {
    "carrier_out": {"carrier": [[0, 0, 40], [0, -50, 40]]},  # out of the back, then below: its front is visible
    "carrier_in": {},
    "device_away": {"device": [[0, 15, 0], [0, 15, -60]]},  # slid up off the rail, then pulled off the wall
    "device_slide": {},
}

# motion of site/assembly.js: every path is travelled at constant speed with ease in and out
TIMING = {"speed": 70.0, "min_time": 0.6, "pause": 0.12}  # mm/s, shortest move in s, pause between parts in s

CARRIER_UNIT = ["carrier", "scd41", "esp32", "plug", "wires_scd"]

# Disassembly for the "take apart" slider, in the order of a real disassembly. One move after the other,
# every move pulls its parts along a free path (tools/assembly_check.py proves that nothing passes through
# anything else). The inserts stay in their parts. Only the display leaves through the window to the front.
DISASSEMBLY = [
    {"lock_screw_housing": [0, -40, 0], "lock_screw_plate": [0, 0, -30]},
    {"lock_tab": [0, -22, 0]},
    {"wall_plate": [0, -15, 0], "lock_insert_plate": [0, -15, 0]},  # the device slides up off the rail
    {"wall_plate": [0, 0, 110], "lock_insert_plate": [0, 0, 110]},
    {"cover_screws": [0, 0, 18]},
    {"cover": [0, 0, 60], "cover_screws": [0, 0, 60]},
    {"port": [0, 0, 45]},
    {"port": [45, 0, 0]},
    {"carrier_screws": [0, 0, 20]},
    {"carrier_screws": [0, 55, 0]},
    {pid: [0, 0, 40] for pid in CARRIER_UNIT},
    {pid: [0, -50, 0] for pid in CARRIER_UNIT},
    {"plug": [0, -15, 0]},  # unplugged downwards, the carrier is open below the socket
    {"esp32": [0, 35, 0]},
    {"scd41": [0, 25, 0]},
    {"display_screws": [0, 0, 30]},
    {"display": [0, 0, -45]},
]


def model(p: dict) -> dict:
    steps = yaml.safe_load(STEPS.read_text(encoding="utf-8"))
    data = {
        "version": p.get("VERSION", ""),
        "parts": parts(p),
        "stages": STAGES,
        "steps": steps,
        "explode": DISASSEMBLY,
        "timing": TIMING,
    }
    ids = {q["id"] for q in data["parts"]}
    for i, s in enumerate(steps, 1):
        unknown = (set(s.get("new", [])) | set(s.get("from_part", {}))) - ids
        if unknown:
            raise SystemExit(f"assembly_steps.yaml step {i}: unknown parts {sorted(unknown)}")
        if s.get("stage") and s["stage"] not in STAGES:
            raise SystemExit(f"assembly_steps.yaml step {i}: unknown stage {s['stage']}")
    unknown = {pid for move in DISASSEMBLY for pid in move} - ids
    if unknown:
        raise SystemExit(f"DISASSEMBLY: unknown parts {sorted(unknown)}")
    return data


def write(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    p = drawing.load_parameters()
    data = model(p)
    (out / "assembly.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    files = {m["file"] for q in data["parts"] for m in q["meshes"] if m["type"] == "stl"}
    for f in sorted(files):
        shutil.copy2(ROOT / "cad" / "stl" / f, out / f)
    for lang in ("en", "de"):
        img = display_preview.screen(lang, "good", 620, 21.4, 45, "08:15", 760, "falling", None, 14.5)
        img.convert("RGB").save(out / f"screen_{lang}.png", optimize=True)
    print(f"written: {out} ({len(data['parts'])} parts, {len(data['steps'])} steps, {len(files)} STL files)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    write(Path(sys.argv[1]))
