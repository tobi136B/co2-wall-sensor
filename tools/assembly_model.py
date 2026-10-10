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

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import display_preview  # noqa: E402
import drawing  # noqa: E402
import wiring  # noqa: E402

PINS = {k: v for k, v in wiring.pins().items()} | {"3V3": "3V3", "GND": "GND"}

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


# ESP32-C3 SuperMini, seen from the back with the USB-C socket at the bottom: pin rows from the top end down
ESP_PINS = {
    -1: ["GPIO0", "GPIO1", "GPIO2", "GPIO3", "GPIO4", "3V3", "GND", "5V"],  # row on the -x side
    1: ["GPIO21", "GPIO20", "GPIO10", "GPIO9", "GPIO8", "GPIO7", "GPIO6", "GPIO5"],  # row on the +x side
}
DISPLAY_ORDER = ["3V3", "GND", "DIN", "CLK", "CS", "DC", "RST", "BL"]  # PH2.0 connector, from the bottom up
WIRE_R = 0.42  # radius of the wires in site/assembly.js
PITCH = 1.0  # display wires side by side in the cable clip
PITCH_PLUG = 2.0  # contact pitch of the PH2.0 connector


def esp_pad(p: dict, signal: str) -> np.ndarray:
    """Pad of a signal on the top face of the ESP32-C3 (the side towards the back)."""
    gpio = PINS.get(signal, signal)
    for side, row in ESP_PINS.items():
        if gpio in row:
            j = row.index(gpio)
            x = p["C3_X"] + side * (p["C3_W"] / 2 - 1.3)
            return np.array([x, p["C3_Y0"] + p["C3_H"] - 1.6 - j * 2.54, p["C3_Z0"] + p["C3_PCB"]])
    raise KeyError(signal)


def _rot(v: np.ndarray, axis: np.ndarray, deg: float) -> np.ndarray:
    a = np.radians(deg)
    k = axis / np.linalg.norm(axis)
    return v * np.cos(a) + np.cross(k, v) * np.sin(a) + k * np.dot(k, v) * (1 - np.cos(a))


class Ribbon:
    """Centre line of a flat cable with the direction s in which its wires lie side by side (a turtle).

    bend() turns about s (out of the plane of the cable), turn() in its plane. A turn with a radius larger
    than half the cable width keeps every wire on its own concentric arc, so no wire crosses another one.
    """

    def __init__(self, start, heading, spread):
        self.p = np.array(start, float)
        self.t = np.array(heading, float)
        self.s = np.array(spread, float)
        self.samples = [(self.p.copy(), self.s.copy())]

    def straight(self, length: float, step: float = 0.8) -> Ribbon:
        n = max(1, int(np.ceil(length / step)))
        for _ in range(n):
            self.p = self.p + self.t * (length / n)
            self.samples.append((self.p.copy(), self.s.copy()))
        return self

    def _arc(self, axis: np.ndarray, deg: float, radius: float, towards: np.ndarray) -> Ribbon:
        centre = self.p + towards * radius
        n = max(2, int(np.ceil(abs(np.radians(deg)) * radius / 0.6)))
        r0 = self.p - centre
        t0, s0 = self.t.copy(), self.s.copy()
        for k in range(1, n + 1):
            d = deg * k / n
            self.p = centre + _rot(r0, axis, d)
            self.t, self.s = _rot(t0, axis, d), _rot(s0, axis, d)
            self.samples.append((self.p.copy(), self.s.copy()))
        return self

    def bend(self, towards, deg: float, radius: float) -> Ribbon:
        """Turn the heading towards the direction 'towards' (perpendicular to s) about the axis s."""
        u = np.array(towards, float)
        axis = np.cross(self.t, u)
        return self._arc(axis, deg, radius, u)

    def turn(self, towards_spread: bool, deg: float, radius: float) -> Ribbon:
        """Turn in the plane of the cable, to the side of +s (True) or -s (False)."""
        u = self.s if towards_spread else -self.s
        axis = np.cross(self.t, u)
        return self._arc(axis, deg, radius, u)

    def wires(self, offsets, pitch_start=None, taper=0.0):
        """Wire polylines: centre + offset * s. With pitch_start the offsets start wider and narrow over taper mm."""
        out = []
        steps = zip(self.samples, self.samples[1:], strict=False)
        dist = np.cumsum([0.0] + [np.linalg.norm(b[0] - a[0]) for a, b in steps])
        for o in offsets:
            pts = []
            for (c, sv), d in zip(self.samples, dist, strict=True):
                k = 1.0
                if pitch_start and taper > 0 and d < taper:
                    u = d / taper
                    k = pitch_start + (1.0 - pitch_start) * (3 * u * u - 2 * u * u * u)
                pts.append(c + sv * o * k)
            out.append(pts)
        return out


def _r(points) -> list[list[float]]:
    return [[round(float(c), 3) for c in q] for q in points]


def _line(a, b, step: float = 0.8) -> list[np.ndarray]:
    a, b = np.array(a, float), np.array(b, float)
    n = max(1, int(np.ceil(np.linalg.norm(b - a) / step)))
    return [a + (b - a) * k / n for k in range(1, n + 1)]


def _drop(start, pad, z_cross: float, y_cross: float) -> list[np.ndarray]:
    """From a point of the cable up over the other wires, across to the pad row and down onto the pad."""
    x0, y0, _ = start
    pts = _line(start, [x0, y_cross, z_cross], 0.5)
    pts += _line(pts[-1], [pad[0], y_cross, z_cross])
    pts += _line(pts[-1], [pad[0], pad[1], pad[2] + 1.6], 0.5)
    pts += _line(pts[-1], pad, 0.4)
    return pts


def wires_display(p: dict) -> list[dict]:
    """The 8 wires of the cable that stays plugged into the display.

    From the plug the flat cable runs along the back of the display to the side wall and bends up, shifting
    upwards in its own plane while it rises. It bends over towards the ESP32-C3, shifts up a little more
    (so it passes above the right post of the bridge), turns down in its own plane and runs under the bridge
    of the sled, over the middle of the board. Every wire leaves the cable at the height of its pad: up over the
    other wires, across to its pad row and down onto the pad. Every bend in the plane of the cable has a radius
    larger than half the cable width, so no wire crosses another one.
    """
    lcd_back = p["LIP"] + p["GLASS_T"] + p["LCD_PCB"]
    y_pcb1 = p["LCD_Y"] + p["LCD_H"] / 2
    yc = y_pcb1 - (p["PH2_Y0"] + p["PH2_Y1"]) / 2
    zc = lcd_back + 2.9
    z_bar = p["C3_Z0"] + p["BRIDGE_H"] - p["BRIDGE_BAR"]  # underside of the bar of the bridge
    z_run = z_bar - WIRE_R - 0.1
    z_socket = p["C3_Z0"] + p["C3_PCB"] + p["C3_USB_H"]  # top of the USB-C socket
    z_low = z_socket + WIRE_R + 0.05  # the cable over the board, below the bridge
    z_cross = z_low + 2 * WIRE_R + 0.1  # wires that leave the cable cross over it here
    x_plug = p["LCD_X"] + p["LCD_W"] / 2 + 0.5
    xr = p["LCD_CABLE_X1"] - 1.2  # the riser stays inside the measured 67 mm
    r_up, r = 1.5, 4.0  # bends out of the plane, turns in the plane (half the cable is 3.5 + 0.42 mm)
    half = 3.5 * PITCH + WIRE_R
    post_x0 = p["C3_X"] + p["C3_W"] / 2 + p["C3_PLAY"] + 1.15 + 0.3  # inner face of the right post
    y_app = p["C3_EXT_Y1"] + half + 0.4  # height of the cable while it passes above the right post
    rise = z_run - zc - 2 * r_up  # straight part of the riser
    a1 = float(np.degrees(np.arcsin(min(1.0, rise / (2 * r)))))
    dy1 = 2 * r * (1 - np.cos(np.radians(a1)))
    dy2 = y_app - yc - dy1
    a2 = float(np.degrees(np.arccos(1 - dy2 / (2 * r))))
    rib = Ribbon([x_plug, yc, zc], [1, 0, 0], [0, 1, 0])
    rib.straight(xr - r_up - x_plug)
    rib.bend([0, 0, 1], 90, r_up)
    rib.turn(True, a1, r).turn(False, a1, r)  # S upwards while rising
    rib.bend([-1, 0, 0], 90, r_up)
    rib.turn(True, a2, r).turn(False, a2, r)  # the rest of the way up, done before the post
    if rib.p[0] < post_x0 + 1.2 + WIRE_R + 0.2:
        raise SystemExit("display cable: it reaches the right post of the bridge before it is high enough")
    x_q = p["C3_X"] + r  # start of the quarter turn down
    rib.straight(rib.p[0] - x_q)
    rib.turn(False, 90, r)  # down, s becomes -x
    offsets = [(i - 3.5) * PITCH for i in range(8)]
    lines = rib.wires(offsets, pitch_start=PITCH_PLUG / PITCH, taper=6.0)
    y_free = p["BRIDGE_Y0"] - 1.0  # below the bridge the cable drops onto its lower level
    pads = {n: esp_pad(p, n) for n in DISPLAY_ORDER}
    out = []
    for i, n in enumerate(DISPLAY_ORDER):
        pts = lines[i]
        x = pts[-1][0]
        pad = pads[n]
        left = pad[0] < p["C3_X"]
        y_cross = pad[1] + (0.75 if left else -0.75)
        pts = pts + _line(pts[-1], [x, y_free, z_run])
        pts += _line(pts[-1], [x, y_free - 2.0, z_low])
        pts += _line(pts[-1], [x, y_cross + 0.5, z_low])
        pts += _line(pts[-1], [x, y_cross, z_cross], 0.4)
        pts += _line(pts[-1], [pad[0], y_cross, z_cross])
        pts += _line(pts[-1], [pad[0], y_cross, pad[2] + 1.0], 0.5)
        pts += _line(pts[-1], pad, 0.4)
        out.append({"color": WIRE[n], "points": _r(pts), "label": n})
    return out


SCD_WIRE_R = 0.3  # AWG 30 silicone wire


def wires_scd(p: dict) -> list[dict]:
    """4 thin wires from the SCD41 pads to the ESP32-C3.

    They leave the pads side by side in the relief groove behind the board, pass the upper board edge and run
    in front of the left rail to the wire slot, each one on its own level. Side by side through the slot and
    along the clip channel on the back of the carrier, then up over the left guide of the ESP32-C3 and up beside
    the board, stacked, until each one turns onto its pad.
    """
    r = SCD_WIRE_R
    pad_x = -p["SCD_PAD_X"]
    yc = p["SCD_Y0"] + p["SCD_L"] / 2
    g = 0.15
    z_lip = p["SCD_ZT"] - p["SCD_PCB"] - g - p["SCD_LIP"]  # front face of the rails
    x_lip = -(p["SCD_W"] / 2 - p["SCD_LIP"])  # inner edge of the left rail
    slot_x = -(p["SCD_W"] / 2 + g + 1.2 + p["MIN_WALL"] + p["SCD_SLOT_W"] / 2)
    top = p["FLOOR_Z"] + p["FLOOR_T"]
    yw = p["Y_DIV_LOW"] - p["SCD_CHANNEL_W"]  # inner face of the clip
    x_ch = p["SPRING_X"] - p["SPRING_W"] / 2 - 1.6  # end of the clip
    gx = p["C3_X"] - p["C3_W"] / 2 - p["C3_PLAY"] - 0.575  # middle of the left guide
    z_guide = p["C3_Z0"] + p["C3_PCB_MAX"] + 0.5
    z_relief = p["SCD_ZT"] + 0.33
    y_edge = p["SCD_TOP"] + r + 0.05  # just past the upper board edge
    out = []
    for k, n in enumerate(["GND", "3V3", "SCL", "SDA"]):
        y0 = yc + (k - 1.5) * 2.54
        lane = pad_x + (k - 1.5) * 2 * r  # side by side in the relief groove
        lane2 = x_lip + r + 0.25 + k * 2 * r  # beside the rail, in front of the carrier
        z_front = z_lip - r - 0.2 - k * (2 * r + 0.05)  # each wire on its own level in front of the rail
        cy = yw + r + k * 2 * r  # side by side in the slot and in the clip channel
        cz = top + 0.45
        z_up = z_guide + r + 0.15 + k * (2 * r + 0.1)
        pad = esp_pad(p, n)
        pts = [np.array([pad_x, y0, p["SCD_ZT"]])]
        pts += _line(pts[-1], [lane, y0 + 0.8, z_relief], 0.4)
        pts += _line(pts[-1], [lane, y_edge, z_relief])
        pts += _line(pts[-1], [lane, y_edge + 0.5, p["SCD_ZT"] - 0.45], 0.3)
        pts += _line(pts[-1], [lane2, y_edge + 3.0, p["SCD_ZT"] - 0.6], 0.4)
        pts += _line(pts[-1], [lane2, y_edge + 3.5, z_front], 0.4)
        pts += _line(pts[-1], [slot_x, cy, z_front])
        pts += _line(pts[-1], [slot_x, cy, cz])
        pts += _line(pts[-1], [x_ch, cy, cz])
        pts += _line(pts[-1], [x_ch + 3.0, cy, z_up])
        pts += _line(pts[-1], [gx, cy, z_up])
        pts += _line(pts[-1], [gx, pad[1] - 0.75, z_up])
        pts += _line(pts[-1], [pad[0], pad[1] - 0.75, z_up])
        pts += _line(pts[-1], [pad[0], pad[1] - 0.75, pad[2] + 1.0], 0.5)
        pts += _line(pts[-1], pad, 0.4)
        out.append({"color": WIRE[n], "points": _r(pts), "label": n, "r": r})
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
    x_pcb1, y_pcb1 = p["LCD_X"] + p["LCD_W"] / 2, p["LCD_Y"] + p["LCD_H"] / 2
    yc = y_pcb1 - (p["PH2_Y0"] + p["PH2_Y1"]) / 2

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
        # PH2.0 connector and the plug of the cable, the cable leaves towards the side wall
        box(
            x_pcb1 - p["PH2_X1"],
            y_pcb1 - p["PH2_Y1"],
            lcd_back,
            x_pcb1 - p["PH2_X0"],
            y_pcb1 - p["PH2_Y0"],
            lcd_back + p["LCD_PLUG_H"],
            "#f1efe8",
        ),
        box(x_pcb1 - p["PH2_X0"], yc - 8.6, lcd_back + 0.4, x_pcb1 + 0.5, yc + 8.6, lcd_back + 5.4, "#dcd6c8"),
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
        box(c3x - 7.4, c3y + 2.5, c3top, c3x - 5.0, c3y + 5.5, c3top + p["C3_PARTS_H"], "#2a2d31"),
        box(c3x + 5.0, c3y + 2.5, c3top, c3x + 7.4, c3y + 5.5, c3top + p["C3_PARTS_H"], "#2a2d31"),
        box(c3x - 2.5, c3y + 10, c3top, c3x + 2.5, c3y + 15, c3top + 0.8, "#15171a"),
        box(c3x - 6.0, c3y + p["C3_H"] - 4.5, c3top, c3x + 1.5, c3y + p["C3_H"] - 1.2, c3top + 0.5, "#e8e4da"),
    ]
    for side in (-1, 1):
        for j in range(8):
            y = c3y + p["C3_H"] - 1.6 - j * 2.54
            esp.append(cyl((c3x + side * (p["C3_W"] / 2 - 1.3), y, c3top - 0.02), (0, 0, 1), 0.06, 1.5, GOLD, "brass"))
    # 90 degree USB-C adapter in the socket, its body points to the wall, the cable is plugged in behind it
    ay = (p["ADAPTER_Y0"] + mouth) / 2
    a_w = p["ADAPTER_W"] / 2
    adapter = [
        box(c3x - a_w, p["ADAPTER_Y0"], p["ADAPTER_Z0"], c3x + a_w, mouth - 0.3, p["ADAPTER_Z1"], "#2b2e33", "metal"),
        box(
            c3x - p["PLUG_W"] / 2,
            ay - p["PLUG_H"] / 2,
            p["ADAPTER_Z1"],
            c3x + p["PLUG_W"] / 2,
            ay + p["PLUG_H"] / 2,
            p["ADAPTER_Z1"] + 16,
            RUBBER,
            "rubber",
        ),
        cyl((c3x, ay, p["ADAPTER_Z1"] + 16), (0, 0, 1), 14, 3.6, "#3a3d42", "rubber"),
    ]
    inserts = [insert((x, y, lip + glass_t)) for x, y in p["LCD_HOLES"]]
    inserts += [insert((x, y, p["COVER_Z"])) for x, y in p["COVER_SCREWS"]]
    inserts += [insert((x, y, p["FLOOR_Z"])) for x, y in p["CARRIER_SCREWS"]]
    display_screws = [m for x, y in p["LCD_HOLES"] for m in screw((x, y, lcd_back), (0, 0, -1))]
    carrier_screws = [m for x, y in p["CARRIER_SCREWS"] for m in screw((x, y, p["FLOOR_Z"] + p["FLOOR_T"]), (0, 0, -1))]
    cover_screws = [m for x, y in p["COVER_SCREWS"] for m in screw((x, y, p["DEPTH"] - p["HEAD_H"]), (0, 0, -1))]
    # M4 screws into wall plugs: pan head in the recess of the plate, shank through the slot
    z_seat = p["DEPTH"] + 3.0
    a = p["BOX_SCREW_SPACING"] / 2
    wall_screws = []
    for x in (-a, a):
        wall_screws += [
            cyl((x, 0, z_seat - 2.8), (0, 0, 1), 2.8, 7.6, STEEL),
            cyl((x, 0, z_seat), (0, 0, 1), 26, 4.0, STEEL),
        ]

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
        part("carrier_screws", "2 screws M2 × 4", "2 Schrauben M2 × 4", dev, carrier_screws),
        part("wires_display", "Display cable", "Displaykabel", dev, [{"type": "tube", **w} for w in wires_display(p)]),
        part("wires_scd", "SCD41 wires", "SCD41-Litzen", car, [{"type": "tube", **w} for w in wires_scd(p)]),
        part("adapter", "USB-C 90° adapter and cable", "USB-C-Winkeladapter mit Kabel", car, adapter),
        part(
            "cover",
            "Back cover",
            "Rückdeckel",
            dev,
            [stl("back_cover", PRINT_MID)],
        ),
        part("cover_screws", "4 screws M2 × 4", "4 Schrauben M2 × 4", dev, cover_screws),
        part("wall_plate", "Wall plate", "Wandplatte", wall, [stl("wall_plate", PRINT_WHITE)]),
        part("wall_screws", "2 screws M4 with wall plugs", "2 Schrauben M4 mit Dübeln", wall, wall_screws),
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

CARRIER_UNIT = ["carrier", "scd41", "esp32", "adapter", "wires_scd"]

# Disassembly for the "take apart" slider, in the order of a real disassembly. One move after the other,
# every move pulls its parts along a free path (tools/assembly_check.py proves that nothing passes through
# anything else). The inserts stay in their parts. Only the display leaves through the window to the front.
DISASSEMBLY = [
    {"wall_plate": [0, -15, 0], "wall_screws": [0, -15, 0]},  # the device slides up off the rail
    {"wall_plate": [0, 0, 160], "wall_screws": [0, 0, 160]},
    {"cover_screws": [0, 0, 18]},
    {"cover": [0, 0, 100], "cover_screws": [0, 0, 100]},  # past the end of the cable in the adapter
    {"wires_display": [0, 0, 45]},
    {"carrier_screws": [0, 0, 20]},
    {"carrier_screws": [0, 55, 0]},
    {pid: [0, 0, 40] for pid in CARRIER_UNIT},
    {pid: [0, -50, 0] for pid in CARRIER_UNIT},
    {"adapter": [0, -25, 0]},  # unplugged downwards, the carrier is open below the socket
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
