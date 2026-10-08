#!/usr/bin/env python3
"""
Technical drawing (A3, scale 1:1) of the CO2 Wall Sensor, in English and German.

All dimensions are read from the PARAMETERS block of
cad/fusion/generate_enclosure/generate_enclosure.py, so drawing and 3D model
can never drift apart.

Usage:   python tools/drawing.py            (both languages)
         python tools/drawing.py --lang de  (German only)
Output:  docs/drawing/co2_wall_sensor_drawing_<lang>.pdf plus a PNG preview per sheet
"""

from __future__ import annotations

import argparse
import datetime as dt
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402
from matplotlib.patches import Arc, Circle, FancyBboxPatch, Polygon, Rectangle  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "cad" / "fusion" / "generate_enclosure" / "generate_enclosure.py"
OUT_DIR = ROOT / "docs" / "drawing"

A3 = (420.0, 297.0)
MM = 1 / 25.4
LW_BODY = 0.5
LW_DIM = 0.25
DASHED = (0, (4, 2))

TEXT = {
    "en": {
        "project": "Project",
        "project_v": "CO2 Wall Sensor",
        "title": "Title",
        "material": "Material",
        "material_v": "PETG (or PLA)",
        "scale": "Scale",
        "author": "Author",
        "tolerance": "General tolerance",
        "date": "Date",
        "format": "Format",
        "units": "Units",
        "units_v": "mm",
        "projection": "Projection",
        "projection_v": "ISO-E (first angle)",
        "source": "Source",
        "sheet": "Sheet",
        "footer": "Generated from the parametric Fusion model. Verify placeholder dimensions "
        "(SCD41 board) before printing.",
        "sheet1": "Device (housing + back cover)",
        "sheet2": "Wall plate and desk stand",
        "front": "Front view",
        "left": "Left side view",
        "below": "View\nfrom below",
        "rear": "Rear view",
        "detail": "Detail rail (2:1)",
        "front_closed": "Closed front\n(no vents)",
        "chamfer": "Chamfer {f} x 45°\naround display window",
        "side_vents": "{n} diamond vents\neach side",
        "split": "Parting line\nback cover",
        "slots": "vent mesh: {n} diamonds {d}, webs {w} = {v}",
        "airflow": "Air enters from below\nthrough the sensor\nchamber (SCD41)",
        "cover_screws": "4x Ø{c}\ncounterbore Ø{d} x {h}\nscrew M2 x 4 ISO 7380\ninsert M2 x 3 in housing",
        "cable_exit": "Cable port module\n(back: right-angle plug,\nplug slot {d} × {l})",
        "bottom_ko": "Cable port module {w} wide, swappable:\nPortBack or PortBottom (straight plug)",
        "lock": "Optional lock: insert M2 x 3\nfor the lock tab",
        "fasteners": "Fasteners (one screw type only)\n"
        "10 (+2) heat-set inserts M2 x 3, OD 3.2, hole Ø{hd} x {hl}\n"
        "10 (+2) button head screws M2 x 4, ISO 7380\n"
        "display 4 | cover 4 | carrier 2 | (+2 optional lock tab)",
        "dovetail": "Dovetail\nfoot 12 / head 16\nheight 3",
        "slot_clear": "Clearance in slot: {v} per side",
        "plate_front": "Wall plate for flush wall box, front view",
        "section": "Section A-A (centre)",
        "concentric": "R{r} (concentric to R{r0})",
        "rim": "Recess for box rim\nØ{d} x {t} deep (back)",
        "window": "Insertion window, travel {v}\n(hidden behind the device)",
        "cable_pass": "Cable passage\nfrom wall box",
        "screw_slots": "2x slot 3.5 x 7\nrecess 6.6 x 6.6, 2.5 deep",
        "spacing": "60 (box screws)",
        "insert_hint": "Device: insert from the front,\nslide 15 mm down",
        "stand": "Desk stand, side view in use",
        "gap": "5 mm air gap:\nvents stay free",
        "stand_hint": "Device (dash-dot) is placed\non the rail and slid\n15 mm down.",
    },
    "de": {
        "project": "Projekt",
        "project_v": "CO2-Wandsensor",
        "title": "Benennung",
        "material": "Werkstoff",
        "material_v": "PETG (oder PLA)",
        "scale": "Maßstab",
        "author": "Ersteller",
        "tolerance": "Allgemeintoleranz",
        "date": "Datum",
        "format": "Format",
        "units": "Maße",
        "units_v": "in mm",
        "projection": "Projektion",
        "projection_v": "ISO-E (Methode 1)",
        "source": "Quelle",
        "sheet": "Blatt",
        "footer": "Generiert aus dem parametrischen Fusion-Modell. Platzhaltermaße "
        "(SCD41-Platine) vor dem Druck prüfen.",
        "sheet1": "Gerät (Gehäuse + Rückdeckel)",
        "sheet2": "Wandplatte und Tischständer",
        "front": "Vorderansicht",
        "left": "Seitenansicht von links",
        "below": "Ansicht\nvon unten",
        "rear": "Rückansicht",
        "detail": "Detail Schiene (2:1)",
        "front_closed": "Front geschlossen\n(keine Lüftung)",
        "chamfer": "Fase {f} x 45°\num Displayfenster",
        "side_vents": "{n} Rauten\nje Seite",
        "split": "Trennfuge\nRückdeckel",
        "slots": "Lüftungsgitter: {n} Rauten {d}, Stege {w} = {v}",
        "airflow": "Luft strömt von unten\ndurch die Sensorkammer\n(SCD41)",
        "cover_screws": "4x Ø{c}\nSenkung Ø{d} x {h}\nSchraube M2 x 4 ISO 7380\nEinschmelzmutter M2 x 3",
        "cable_exit": "Kabelport-Modul\n(hinten: Winkelstecker,\nLangloch Stecker {d} × {l})",
        "bottom_ko": "Kabelport-Modul {w} breit, tauschbar:\nPortBack oder PortBottom (gerader Stecker)",
        "lock": "Optionale Sicherung: Mutter\nM2 x 3 für die Lasche",
        "fasteners": "Verbindungselemente (nur eine Schraubensorte)\n"
        "10 (+2) Einschmelzmuttern M2 x 3, AD 3,2, Bohrung Ø{hd} x {hl}\n"
        "10 (+2) Linsenkopfschrauben M2 x 4, ISO 7380\n"
        "Display 4 | Deckel 4 | Träger 2 | (+2 Sicherungslasche)",
        "dovetail": "Schwalbenschwanz\nFuß 12 / Kopf 16\nHöhe 3",
        "slot_clear": "Spiel in der Nut: {v} je Seite",
        "plate_front": "Wandplatte Hohlwanddose, Vorderansicht",
        "section": "Schnitt A-A (Mitte)",
        "concentric": "R{r} (konzentrisch zu R{r0})",
        "rim": "Aussparung Dosenrand\nØ{d} x {t} tief (Rückseite)",
        "window": "Einsetzfenster, Einschubweg {v}\n(verdeckt hinter dem Gerät)",
        "cable_pass": "Kabeldurchlass\naus der Dose",
        "screw_slots": "2x Langloch 3,5 x 7\nSenkung 6,6 x 6,6 tief 2,5",
        "spacing": "60 (Geräteschrauben Dose)",
        "insert_hint": "Gerät: vorne einsetzen,\n15 mm nach unten schieben",
        "stand": "Tischständer, Seitenansicht in Gebrauchslage",
        "gap": "5 mm Luftspalt:\nLüftung bleibt frei",
        "stand_hint": "Gerät (strichpunktiert) wird auf\ndie Schiene gesetzt und\n15 mm nach unten geschoben.",
    },
}


def load_parameters() -> dict:
    """Execute only the plain-number parameter block of the generator."""
    text = GENERATOR.read_text(encoding="utf-8")
    start = text.index("# ===================== PARAMETERS")
    end = text.index("VI = adsk.core.ValueInput")
    ns: dict = {"math": math}
    exec(text[start:end], ns)  # noqa: S102 (versioned file from this repository)
    return {k: v for k, v in ns.items() if k.isupper()}


class Sheet:
    """One A3 sheet with frame and title block."""

    def __init__(self, title: str, number: int, total: int, p: dict, lang: str):
        self.p, self.lang, self.t = p, lang, TEXT[lang]
        self.fig = plt.figure(figsize=(A3[0] * MM, A3[1] * MM))
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, A3[0])
        self.ax.set_ylim(0, A3[1])
        self.ax.set_aspect("equal")
        self.ax.axis("off")
        self._frame()
        self._title_block(title, number, total)

    # -- primitives -------------------------------------------------------------
    def line(self, pts, lw=LW_BODY, ls="-"):
        xs, ys = zip(*pts, strict=True)
        self.ax.plot(xs, ys, color="k", lw=lw, ls=ls, solid_capstyle="butt")

    def rect(self, x0, y0, w, h, r=0.0, lw=LW_BODY, ls="-", fill=None):
        if r <= 0:
            patch = Rectangle((x0, y0), w, h, fill=fill is not None, fc=fill or "none", ec="k", lw=lw, ls=ls)
        else:
            patch = FancyBboxPatch(
                (x0 + r, y0 + r),
                w - 2 * r,
                h - 2 * r,
                boxstyle=f"round,pad={r}",
                fill=fill is not None,
                fc=fill or "none",
                ec="k",
                lw=lw,
                ls=ls,
            )
        self.ax.add_patch(patch)

    def poly(self, pts, lw=LW_BODY, ls="-", fill=None):
        self.ax.add_patch(Polygon(pts, closed=True, fill=fill is not None, fc=fill or "none", ec="k", lw=lw, ls=ls))

    def circle(self, x, y, d, lw=LW_BODY, ls="-"):
        self.ax.add_patch(Circle((x, y), d / 2, fill=False, ec="k", lw=lw, ls=ls))

    def centre_line(self, p0, p1):
        self.line([p0, p1], lw=0.2, ls=(0, (12, 3, 2, 3)))

    def text(self, x, y, s, size=7, **kw):
        self.ax.text(x, y, s, fontsize=size, family="DejaVu Sans", **kw)

    def view_title(self, x, y, s):
        self.text(x, y, s, size=9, weight="bold", ha="center")

    def num(self, v: float) -> str:
        s = f"{v:.1f}".rstrip("0").rstrip(".")
        return s.replace(".", ",") if self.lang == "de" else s

    # -- dimensions -------------------------------------------------------------
    def dim_h(self, x0, x1, y_ref, y_dim, txt=None):
        s = 1 if y_dim >= y_ref else -1
        for x in (x0, x1):
            self.line([(x, y_ref + s * 1.0), (x, y_dim + s * 1.5)], lw=LW_DIM)
        self.ax.annotate(
            "",
            xy=(x0, y_dim),
            xytext=(x1, y_dim),
            arrowprops=dict(arrowstyle="<|-|>", lw=LW_DIM, color="k", shrinkA=0, shrinkB=0, mutation_scale=6),
        )
        self.text(
            (x0 + x1) / 2, y_dim + 0.8, txt if txt is not None else self.num(abs(x1 - x0)), ha="center", va="bottom"
        )

    def dim_v(self, y0, y1, x_ref, x_dim, txt=None):
        s = 1 if x_dim >= x_ref else -1
        for y in (y0, y1):
            self.line([(x_ref + s * 1.0, y), (x_dim + s * 1.5, y)], lw=LW_DIM)
        self.ax.annotate(
            "",
            xy=(x_dim, y0),
            xytext=(x_dim, y1),
            arrowprops=dict(arrowstyle="<|-|>", lw=LW_DIM, color="k", shrinkA=0, shrinkB=0, mutation_scale=6),
        )
        self.text(
            x_dim - 0.8,
            (y0 + y1) / 2,
            txt if txt is not None else self.num(abs(y1 - y0)),
            ha="right",
            va="center",
            rotation=90,
        )

    def note(self, x, y, xt, yt, s):
        self.ax.annotate(
            s,
            xy=(x, y),
            xytext=(xt, yt),
            fontsize=6.5,
            family="DejaVu Sans",
            arrowprops=dict(arrowstyle="-|>", lw=LW_DIM, color="k", mutation_scale=5),
        )

    # -- frame and title block ----------------------------------------------------
    def _frame(self):
        self.rect(10, 10, A3[0] - 20, A3[1] - 20, lw=0.7)
        for i in range(8):
            x = 10 + (i + 0.5) * (A3[0] - 20) / 8
            self.text(x, 5.5, str(i + 1), size=6, ha="center")
            self.text(x, A3[1] - 7.5, str(i + 1), size=6, ha="center")
        for i, ch in enumerate("ABCDEF"):
            y = A3[1] - 10 - (i + 0.5) * (A3[1] - 20) / 6
            self.text(5.5, y, ch, size=6, va="center")
            self.text(A3[0] - 7.5, y, ch, size=6, va="center")

    def _title_block(self, title, number, total):
        t = self.t
        x0, y0, w, h = A3[0] - 10 - 180, 10, 180, 36
        self.rect(x0, y0, w, h, lw=0.7)
        for yy in (y0 + 9, y0 + 18, y0 + 27):
            self.line([(x0, yy), (x0 + w, yy)], lw=0.3)
        for xx in (x0 + 45, x0 + 110, x0 + 145):
            self.line([(xx, y0), (xx, y0 + h)], lw=0.3)
        today = dt.date.today().strftime("%d.%m.%Y" if self.lang == "de" else "%Y-%m-%d")
        fields = [
            (x0 + 2, y0 + 30.5, t["project"], t["project_v"]),
            (x0 + 47, y0 + 30.5, t["title"], title),
            (x0 + 112, y0 + 30.5, t["material"], t["material_v"]),
            (x0 + 147, y0 + 30.5, t["scale"], "1:1"),
            (x0 + 2, y0 + 21.5, t["author"], "Tobias Schneider"),
            (x0 + 47, y0 + 21.5, t["tolerance"], "ISO 2768-m"),
            (x0 + 112, y0 + 21.5, t["date"], today),
            (x0 + 147, y0 + 21.5, t["format"], "A3"),
            (x0 + 2, y0 + 12.5, t["units"], t["units_v"]),
            (x0 + 47, y0 + 12.5, t["projection"], t["projection_v"]),
            (x0 + 112, y0 + 12.5, t["source"], "generate_enclosure.py"),
            (x0 + 147, y0 + 12.5, t["sheet"], f"{number} / {total}"),
        ]
        for x, y, k, v in fields:
            self.text(x, y + 3.2, k, size=5, color="0.35")
            self.text(x, y - 0.3, v, size=7.5, weight="bold")
        self.text(x0 + 2, y0 + 3, t["footer"], size=5.3, color="0.3")

    def save(self, pdf: PdfPages, png: Path):
        self.fig.savefig(png, dpi=110)
        pdf.savefig(self.fig)
        plt.close(self.fig)


# ----------------------------------------------------------------------------- sheet 1: device
def sheet_device(sh: Sheet):
    p, t = sh.p, sh.t
    W, D, R = p["BODY"], p["DEPTH"], p["R_CORNER"]
    ww, wh = p["ACTIVE_W"] + 1.0, p["ACTIVE_H"] + 1.0
    f, rf = p["WINDOW_CHAMFER"], p["R_FRONT"]
    y_top_in, lcd_y = p["Y_TOP_IN"], p["LCD_Y"]
    y_chin_low = p["Y_CHIN_LOW"]
    rail_y0, rail_l, rail_h = p["RAIL_Y0"], p["RAIL_L"], p["RAIL_H"]
    hv = p["VENT_HOLE"] / 2
    pz0 = p["PORT_Z0"]

    # front view
    cx, cy = 85.0, 132.0
    sh.view_title(cx, cy - W / 2 - 24, t["front"])
    sh.rect(cx - W / 2, cy - W / 2, W, W, R)
    sh.rect(cx - W / 2 + rf, cy - W / 2 + rf, W - 2 * rf, W - 2 * rf, max(R - rf, 0.5), lw=0.2)
    sh.rect(cx - ww / 2 - f, cy + lcd_y - wh / 2 - f, ww + 2 * f, wh + 2 * f, 1.0 + f, lw=0.3)
    sh.rect(cx - ww / 2, cy + lcd_y - wh / 2, ww, wh, 1.0)
    sh.centre_line((cx, cy - W / 2 - 5), (cx, cy + W / 2 + 5))
    sh.centre_line((cx - W / 2 - 5, cy + lcd_y), (cx + W / 2 + 5, cy + lcd_y))
    sh.dim_h(cx - W / 2, cx + W / 2, cy - W / 2, cy - W / 2 - 12)
    sh.dim_v(cy - W / 2, cy + W / 2, cx - W / 2, cx - W / 2 - 12)
    sh.dim_h(cx - ww / 2, cx + ww / 2, cy + lcd_y + wh / 2, cy + W / 2 + 8, txt=sh.num(ww))
    sh.dim_v(cy + lcd_y - wh / 2, cy + lcd_y + wh / 2, cx + ww / 2, cx + W / 2 + 8, txt=sh.num(wh))
    sh.dim_v(cy + lcd_y + wh / 2, cy + W / 2, cx + W / 2, cx + W / 2 + 16)
    sh.note(cx + W / 2 - 1.2, cy + W / 2 - 1.2, cx + W / 2 + 4, cy + W / 2 + 14, f"R{sh.num(R)}")
    sh.note(
        cx - ww / 2 - f / 2,
        cy + lcd_y - wh / 2 - f / 2,
        cx - W / 2 - 4,
        cy - W / 2 + 6,
        t["chamfer"].format(f=sh.num(f)),
    )
    sh.text(cx, cy - 18, t["front_closed"], size=6.5, ha="center", color="0.35")

    # left side view (first angle: right of the front view)
    sx = cx + W / 2 + 55
    sh.view_title(sx + D / 2, cy - W / 2 - 24, t["left"])
    sh.line([(sx + rf, cy + W / 2), (sx + D, cy + W / 2), (sx + D, cy - W / 2), (sx + rf, cy - W / 2)])
    sh.ax.add_patch(Arc((sx + rf, cy + W / 2 - rf), 2 * rf, 2 * rf, theta1=90, theta2=180, lw=LW_BODY))
    sh.ax.add_patch(Arc((sx + rf, cy - W / 2 + rf), 2 * rf, 2 * rf, theta1=180, theta2=270, lw=LW_BODY))
    sh.line([(sx, cy + W / 2 - rf), (sx, cy - W / 2 + rf)])
    cover_z = D - p["COVER_T"]
    sh.line([(sx + cover_z, cy + W / 2), (sx + cover_z, cy - W / 2)], lw=0.2)
    sh.rect(sx + D, cy + rail_y0, rail_h, rail_l)
    for u, v in p["VENT_SIDE"]:
        sh.poly([(sx + v + hv, cy + u), (sx + v, cy + u + hv), (sx + v - hv, cy + u), (sx + v, cy + u - hv)], lw=0.3)
    sh.line([(sx + pz0, cy - W / 2), (sx + pz0, cy - W / 2 + p["WALL"]), (sx + D, cy - W / 2 + p["WALL"])], lw=0.3)
    sh.dim_h(sx, sx + D, cy - W / 2, cy - W / 2 - 12)
    sh.dim_h(sx, sx + D + rail_h, cy + W / 2, cy + W / 2 + 8)
    sh.dim_v(cy + rail_y0, cy + rail_y0 + rail_l, sx + D + rail_h, sx + D + rail_h + 8)
    sh.dim_v(cy - W / 2, cy + rail_y0, sx + D + rail_h, sx + D + rail_h + 16)
    su, sv = p["VENT_SIDE"][0]
    sh.note(sx + sv, cy + su, sx - 18, cy - 20, t["side_vents"].format(n=len(p["VENT_SIDE"])))
    sh.note(sx + cover_z, cy + W / 2 - 6, sx + cover_z + 6, cy + W / 2 + 16, t["split"])

    # view from below (first angle: above the front view)
    uy = cy + W / 2 + 58
    sh.text(cx - W / 2 - 4, uy - D / 2, t["below"], size=9, weight="bold", ha="right", va="center")
    sh.rect(cx - W / 2, uy - D, W, D, 1.0)
    for u, v in p["VENT_BOTTOM"]:
        sh.poly([(cx + u + hv, uy - v), (cx + u, uy - v + hv), (cx + u - hv, uy - v), (cx + u, uy - v - hv)], lw=0.3)
    us = [c[0] for c in p["VENT_BOTTOM"]]
    vs = [c[1] for c in p["VENT_BOTTOM"]]
    sh.rect(cx - p["RAIL_HEAD"] / 2, uy - D - rail_h, p["RAIL_HEAD"], rail_h, lw=0.4)
    # seen from below the model +x axis points to the left, like in the front view
    bx0, bx1 = cx - p["PORT_X1"], cx - p["PORT_X0"]
    sh.rect(bx0, uy - D, bx1 - bx0, D - pz0, lw=0.4)
    lx = cx - p["LOCK_POINTS"][0]
    sh.circle(lx, uy - p["LOCK_Z"], p["INSERT_HOLE_D"])
    sh.dim_h(
        cx + min(us) - hv,
        cx + max(us) + hv,
        uy,
        uy + 6,
        txt=t["slots"].format(
            n=len(us), d=sh.num(2 * hv), w=sh.num(p["VENT_WEB"]), v=sh.num(max(us) - min(us) + 2 * hv)
        ),
    )
    sh.dim_v(uy - min(vs) + hv, uy - max(vs) - hv, cx + W / 2, cx + W / 2 + 8, txt=sh.num(max(vs) - min(vs) + 2 * hv))
    sh.dim_h(bx0, bx1, uy - D, uy - D - rail_h - 6, txt=sh.num(bx1 - bx0))
    sh.note(bx0 + 1, uy - D + 1, cx - W / 2 - 30, uy - D - 14, t["bottom_ko"].format(w=sh.num(bx1 - bx0)))
    sh.note(lx, uy - p["LOCK_Z"], cx - W / 2 - 30, uy + 4, t["lock"])
    sh.text(cx + W / 2 + 18, uy - 8, t["airflow"], size=6.5, color="0.35")

    # rear view
    rx, ry = 330.0, 132.0
    sh.view_title(rx, ry - W / 2 - 24, t["rear"])
    sh.rect(rx - W / 2, ry - W / 2, W, W, R)
    s = 0.2
    xl, xr = -W / 2 + p["WALL"] + s, W / 2 - p["WALL"] - s
    sh.rect(rx + xl, ry + y_chin_low + s, xr - xl, (y_top_in - s) - (y_chin_low + s), lw=0.35)
    sh.rect(rx - p["RAIL_HEAD"] / 2, ry + rail_y0, p["RAIL_HEAD"], rail_l)
    sh.rect(rx - p["RAIL_FOOT"] / 2, ry + rail_y0, p["RAIL_FOOT"], rail_l, lw=LW_DIM, ls=DASHED)
    kx0, kx1, ky0, ky1 = p["PORT_X0"], p["PORT_X1"], -W / 2 + p["WALL"], p["PORT_Y1"]
    sh.rect(rx + kx0, ry + ky0, kx1 - kx0, ky1 - ky0, lw=0.4)
    # boot hole: oblong by BOOT_PLAY up and down
    bd, bp = p["BOOT_D"], p["BOOT_PLAY"]
    sh.rect(rx + p["C3_X"] - bd / 2, ry + p["BOOT_Y"] - 0.5 - bd / 2, bd, bp + 0.5 + bd, bd / 2, lw=0.35)
    screws = p["COVER_SCREWS"]
    for bx, by in screws:
        sh.circle(rx + bx, ry + by, p["SCREW_CLEAR_D"])
        sh.circle(rx + bx, ry + by, p["HEAD_D"], lw=0.3)
    sh.centre_line((rx, ry - W / 2 - 5), (rx, ry + W / 2 + 5))
    sh.dim_h(rx - p["RAIL_HEAD"] / 2, rx + p["RAIL_HEAD"] / 2, ry + rail_y0 + rail_l, ry + rail_y0 + rail_l + 6)
    sh.dim_h(rx + screws[0][0], rx + screws[1][0], ry - W / 2, ry - W / 2 - 12)
    sh.dim_h(rx + screws[2][0], rx + screws[3][0], ry + W / 2, ry + W / 2 + 8)
    sh.dim_v(ry - W / 2, ry + screws[0][1], rx + W / 2, rx + W / 2 + 8)
    sh.dim_v(ry + screws[2][1], ry + W / 2, rx + W / 2, rx + W / 2 + 8)
    sh.note(
        rx + screws[1][0],
        ry + screws[1][1],
        rx + W / 2 + 12,
        ry - 14,
        t["cover_screws"].format(c=sh.num(p["SCREW_CLEAR_D"]), d=sh.num(p["HEAD_D"]), h=sh.num(p["HEAD_H"])),
    )
    boot = t["cable_exit"].format(d=sh.num(bd), l=sh.num(bd + bp + 0.5))
    sh.note(rx + kx1, ry + ky1, rx + W / 2 + 12, ry + 10, boot)
    sh.note(rx - p["RAIL_HEAD"] / 2, ry + rail_y0 + 2, rx - W / 2 - 4, ry - 16, t["dovetail"])

    # detail of the rail
    dx, dy, k = 235.0, 222.0, 2.0
    sh.view_title(dx + 15, dy + 26, t["detail"])
    foot, head = p["RAIL_FOOT"] / 2, p["RAIL_HEAD"] / 2
    pts = [(-foot, 0), (foot, 0), (head, rail_h), (-head, rail_h)]
    sh.poly([(dx + 15 + x * k, dy + y * k) for x, y in pts], fill="0.9")
    sh.line([(dx - 5, dy), (dx + 35, dy)])
    sh.dim_h(dx + 15 - p["RAIL_FOOT"] * k / 2, dx + 15 + p["RAIL_FOOT"] * k / 2, dy, dy - 8, txt=sh.num(p["RAIL_FOOT"]))
    sh.dim_h(
        dx + 15 - p["RAIL_HEAD"] * k / 2,
        dx + 15 + p["RAIL_HEAD"] * k / 2,
        dy + rail_h * k,
        dy + rail_h * k + 6,
        txt=sh.num(p["RAIL_HEAD"]),
    )
    sh.dim_v(
        dy, dy + rail_h * k, dx + 15 + p["RAIL_HEAD"] * k / 2, dx + 15 + p["RAIL_HEAD"] * k / 2 + 8, txt=sh.num(rail_h)
    )
    sh.text(dx - 5, dy - 18, t["slot_clear"].format(v=sh.num(p["RAIL_CLEARANCE"])), size=6.5, color="0.35")

    # fastener summary above the title block
    sh.rect(300, 205, 106, 26, lw=0.4)
    sh.text(
        302,
        218,
        t["fasteners"].format(hd=sh.num(p["INSERT_HOLE_D"]), hl=sh.num(p["INSERT_HOLE_L"])),
        size=6.5,
        va="center",
        linespacing=1.5,
    )


# ----------------------------------------------------------------------------- sheet 2: adapters
def sheet_adapters(sh: Sheet):
    p, t = sh.p, sh.t
    P_, T_ = p["PLATE"], p["PLATE_T"]
    W, D = p["BODY"], p["DEPTH"]
    Rk = p["R_CORNER"] + (P_ - W) / 2
    c = p["RAIL_CLEARANCE"]
    y0n, y1n = p["RAIL_Y0"] - c, p["RAIL_Y0"] + p["RAIL_L"] + c
    head, foot = p["RAIL_HEAD"] + 2 * c, p["RAIL_FOOT"] + 2 * c
    a = p["BOX_SCREW_SPACING"] / 2

    # wall plate front view
    cx, cy = 95.0, 180.0
    sh.view_title(cx, cy + P_ / 2 + 18, t["plate_front"])
    sh.rect(cx - P_ / 2, cy - P_ / 2, P_, P_, Rk)
    sh.rect(cx - W / 2, cy - W / 2, W, W, p["R_CORNER"], lw=0.2, ls=(0, (6, 3)))
    sh.circle(cx, cy, p["BOX_RIM_D"], lw=LW_DIM, ls=DASHED)
    sh.rect(cx - head / 2, cy + y1n, head, p["RAIL_TRAVEL"])
    sh.rect(cx - foot / 2, cy + y0n, foot, y1n - y0n)
    sh.rect(cx - head / 2, cy + y0n, head, y1n - y0n, lw=LW_DIM, ls=DASHED)
    kx0, kx1, ky0, ky1 = p["CABLE"]
    ky0, ky1 = ky0 - 1, ky1 + 1
    sh.rect(cx - kx1, cy + ky0, kx1 - kx0, ky1 - ky0)  # seen from the front, model +x is on the left
    lock_y = -P_ / 2 + 2.0 + p["INSERT_HOLE_D"] / 2 + 0.2
    sh.circle(cx - p["LOCK_POINTS"][1], cy + lock_y, p["INSERT_HOLE_D"])
    for sx in (-a, a):
        sh.rect(cx + sx - 2, cy - 1.75, 4, 3.5)
        sh.rect(cx + sx - 3.3, cy - 3.3, 6.6, 6.6, lw=0.3)
    sh.centre_line((cx, cy - P_ / 2 - 5), (cx, cy + P_ / 2 + 5))
    sh.centre_line((cx - P_ / 2 - 5, cy), (cx + P_ / 2 + 5, cy))
    for ys, up in ((cy + P_ / 2 + 3, True), (cy - P_ / 2 - 3, False)):
        sh.line([(cx, ys - 2.5 if up else ys + 2.5), (cx, ys + 2.5 if up else ys - 2.5)], lw=1.0)
        sh.ax.annotate(
            "", xy=(cx + 6, ys), xytext=(cx, ys), arrowprops=dict(arrowstyle="-|>", lw=0.8, color="k", mutation_scale=7)
        )
        sh.text(cx + 8, ys, "A", size=9, weight="bold", va="center")
    sh.dim_h(cx - P_ / 2, cx + P_ / 2, cy - P_ / 2, cy - P_ / 2 - 12)
    sh.dim_v(cy - P_ / 2, cy + P_ / 2, cx - P_ / 2, cx - P_ / 2 - 12)
    sh.dim_h(cx - a, cx + a, cy - 4, cy - P_ / 2 - 24, txt=t["spacing"])
    sh.note(
        cx + P_ / 2 - 3.4,
        cy + P_ / 2 - 3.4,
        cx + P_ / 2 + 4,
        cy + P_ / 2 + 8,
        t["concentric"].format(r=sh.num(Rk), r0=sh.num(p["R_CORNER"])),
    )
    sh.note(
        cx + p["BOX_RIM_D"] / 2 * 0.707,
        cy - p["BOX_RIM_D"] / 2 * 0.707,
        cx + P_ / 2 + 4,
        cy - P_ / 2 - 6,
        t["rim"].format(d=sh.num(p["BOX_RIM_D"]), t=sh.num(p["BOX_RIM_T"])),
    )
    sh.note(
        cx + head / 2,
        cy + y1n + p["RAIL_TRAVEL"] / 2,
        cx + P_ / 2 + 4,
        cy + 30,
        t["window"].format(v=sh.num(p["RAIL_TRAVEL"])),
    )
    sh.note(cx - kx1, cy + ky0, cx - P_ / 2 - 4, cy - P_ / 2 + 2, t["cable_pass"])
    sh.note(cx + a + 3.3, cy + 3.3, cx + P_ / 2 + 4, cy + 12, t["screw_slots"])

    # section A-A
    ax_ = cx + P_ / 2 + 70
    sh.view_title(ax_ + T_ / 2, cy + P_ / 2 + 18, t["section"])
    sh.rect(ax_, cy - P_ / 2, T_, P_, fill="0.88")
    sh.rect(ax_ - 0.01, cy + y0n, p["RAIL_H"] + c, y1n - y0n + p["RAIL_TRAVEL"], fill="white")
    sh.rect(ax_ + T_ - p["BOX_RIM_T"], cy - p["BOX_RIM_D"] / 2, p["BOX_RIM_T"] + 0.01, p["BOX_RIM_D"], fill="white")
    sh.dim_h(ax_, ax_ + T_, cy - P_ / 2, cy - P_ / 2 - 12)
    sh.dim_h(ax_, ax_ + p["RAIL_H"] + c, cy + y1n + p["RAIL_TRAVEL"], cy + P_ / 2 + 8, txt=sh.num(p["RAIL_H"] + c))
    sh.dim_v(cy + y0n, cy + y1n + p["RAIL_TRAVEL"], ax_ + T_, ax_ + T_ + 10)
    sh.text(ax_ - 4, cy - P_ / 2 - 22, t["insert_hint"], size=6.5, color="0.35")

    # desk stand in use (table plane horizontal, device leans back)
    tilt = math.tan(math.radians(p["TILT"]))
    z_front, z_back = -2.0, 46.0
    y_foot = -W / 2 - p["STAND_GAP"] - tilt * (D - z_front)

    def y_table(z):
        return y_foot + tilt * (z - z_front)

    phi = -math.radians(p["TILT"])
    ox, oy = 268.0, 75.0

    def P(y, z):
        zz, yy = z - z_front, y - (y_table(z_front) - 4)
        return (ox + zz * math.cos(phi) - yy * math.sin(phi), oy + zz * math.sin(phi) + yy * math.cos(phi))

    sh.view_title(ox + 35, 195, t["stand"])
    sh.poly(
        [
            P(y_table(z_front), z_front),
            P(y_table(z_back), z_back),
            P(y_table(z_back) - 4, z_back),
            P(y_table(z_front) - 4, z_front),
        ],
        fill="0.92",
    )
    y_top = p["RAIL_Y0"] + p["RAIL_L"] + p["RAIL_TRAVEL"] + 4
    sh.poly([P(y_table(D) - 2, D), P(y_top, D), P(y_top, D + 7), P(y_table(D + 7) - 2, D + 7)], fill="0.92")
    sh.poly([P(y_table(D + 7) - 1, D + 7), P(y_top - 12, D + 7), P(y_table(D + 24) - 1, D + 24)], fill="0.92")
    sh.poly([P(-W / 2, 0), P(W / 2, 0), P(W / 2, D), P(-W / 2, D)], lw=0.4, ls=(0, (10, 2, 2, 2)))
    sh.line([(ox - 15, oy), (ox + 75, oy)], lw=0.3)
    for i in range(16):
        x = ox - 13 + i * 5.5
        sh.line([(x, oy), (x - 3, oy - 3)], lw=0.2)
    fx0, fx1 = P(y_table(z_front) - 4, z_front)[0], P(y_table(z_back) - 4, z_back)[0]
    sh.dim_h(fx0, fx1, oy - 4, oy - 12, txt=sh.num(z_back - z_front))
    top = P(W / 2, 0)
    sh.line([P(-W / 2, 0), (P(-W / 2, 0)[0], top[1] + 4)], lw=0.2, ls=DASHED)
    sh.ax.add_patch(Arc(P(-W / 2, 0), 70, 70, theta1=90 - p["TILT"], theta2=90, lw=LW_DIM))
    sh.text(P(-W / 2, 0)[0] + 3, P(-W / 2, 0)[1] + 37, f"{sh.num(p['TILT'])}°", size=8)
    sh.note(*P(-W / 2 + 0.5, D * 0.6), ox + 70, oy + 18, t["gap"])
    sh.text(ox + 48, 170, t["stand_hint"], size=6.5, color="0.35")


def build(lang: str, p: dict):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    t = TEXT[lang]
    pdf_path = OUT_DIR / f"co2_wall_sensor_drawing_{lang}.pdf"
    with PdfPages(pdf_path) as pdf:
        s1 = Sheet(t["sheet1"], 1, 2, p, lang)
        sheet_device(s1)
        s1.save(pdf, OUT_DIR / f"sheet1_device_{lang}.png")
        s2 = Sheet(t["sheet2"], 2, 2, p, lang)
        sheet_adapters(s2)
        s2.save(pdf, OUT_DIR / f"sheet2_adapters_{lang}.png")
    print(f"written: {pdf_path.relative_to(ROOT)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--lang", choices=sorted(TEXT), action="append", help="language (default: all)")
    args = ap.parse_args()
    params = load_parameters()
    for lang in args.lang or sorted(TEXT):
        build(lang, params)


if __name__ == "__main__":
    main()
