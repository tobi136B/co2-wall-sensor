#!/usr/bin/env python3
"""
Technische Zeichnung (A3, Massstab 1:1) fuer den CO2-Wandsensor.

Die Masse werden direkt aus dem Parameterblock von
cad/fusion/generate_enclosure/generate_enclosure.py gelesen, damit Zeichnung
und 3D-Modell immer zusammenpassen.

Aufruf:  python tools/zeichnung.py
Ausgabe: docs/zeichnung/co2_wandsensor_zeichnung.pdf  (+ PNG-Vorschau je Blatt)
"""
from __future__ import annotations

import datetime as _dt
import math
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Polygon, Rectangle, Circle, Arc  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "cad" / "fusion" / "generate_enclosure" / "generate_enclosure.py"
OUT_DIR = ROOT / "docs" / "zeichnung"

A3 = (420.0, 297.0)
MM = 1 / 25.4
LW_K = 0.5   # Koerperkante
LW_D = 0.25  # Masslinie
LW_V = 0.25  # verdeckt


# --------------------------------------------------------------------------- Parameter
def lade_parameter() -> dict:
    """Fuehrt nur den reinen Zahlen-Parameterblock des Generators aus."""
    text = GENERATOR.read_text(encoding="utf-8")
    start = text.index("# ===================== PARAMETER")
    ende = text.index("VI = adsk.core.ValueInput")
    ns: dict = {"math": math}
    exec(text[start:ende], ns)  # noqa: S102 (eigene, versionierte Datei)
    return {k: v for k, v in ns.items() if k.isupper()}


# --------------------------------------------------------------------------- Zeichenhelfer
class Blatt:
    def __init__(self, pdf: PdfPages, titel: str, nummer: int, gesamt: int, p: dict):
        self.pdf, self.p = pdf, p
        self.fig = plt.figure(figsize=(A3[0] * MM, A3[1] * MM))
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, A3[0])
        self.ax.set_ylim(0, A3[1])
        self.ax.set_aspect("equal")
        self.ax.axis("off")
        self._rahmen()
        self._schriftfeld(titel, nummer, gesamt)

    # ---- Grundelemente -------------------------------------------------------
    def linie(self, pts, lw=LW_K, ls="-", farbe="k"):
        xs, ys = zip(*pts)
        self.ax.plot(xs, ys, color=farbe, lw=lw, ls=ls, solid_capstyle="butt")

    def rrechteck(self, x0, y0, b, h, r=0.0, lw=LW_K, ls="-", fill=None):
        if r <= 0:
            patch = Rectangle((x0, y0), b, h, fill=fill is not None, fc=fill or "none", ec="k", lw=lw, ls=ls)
        else:
            patch = FancyBboxPatch((x0 + r, y0 + r), b - 2 * r, h - 2 * r,
                                   boxstyle=f"round,pad={r}", fill=fill is not None,
                                   fc=fill or "none", ec="k", lw=lw, ls=ls)
        self.ax.add_patch(patch)

    def poly(self, pts, lw=LW_K, ls="-", fill=None):
        self.ax.add_patch(Polygon(pts, closed=True, fill=fill is not None, fc=fill or "none",
                                  ec="k", lw=lw, ls=ls))

    def kreis(self, x, y, d, lw=LW_K, ls="-"):
        self.ax.add_patch(Circle((x, y), d / 2, fill=False, ec="k", lw=lw, ls=ls))

    def mittellinie(self, p0, p1):
        self.linie([p0, p1], lw=0.2, ls=(0, (12, 3, 2, 3)))

    def text(self, x, y, s, size=7, **kw):
        self.ax.text(x, y, s, fontsize=size, family="DejaVu Sans", **kw)

    def ansichtstitel(self, x, y, s):
        self.text(x, y, s, size=9, weight="bold", ha="center")

    # ---- Bemassung -------------------------------------------------------------
    def mass_h(self, x0, x1, y_ref, y_mass, wert=None, txt=None):
        """Horizontales Mass zwischen x0 und x1, Masslinie auf y_mass."""
        s = 1 if y_mass >= y_ref else -1
        for x in (x0, x1):
            self.linie([(x, y_ref + s * 1.0), (x, y_mass + s * 1.5)], lw=LW_D)
        self.ax.annotate("", xy=(x0, y_mass), xytext=(x1, y_mass),
                         arrowprops=dict(arrowstyle="<|-|>", lw=LW_D, color="k",
                                         shrinkA=0, shrinkB=0, mutation_scale=6))
        t = txt if txt is not None else _fmt(wert if wert is not None else abs(x1 - x0))
        self.text((x0 + x1) / 2, y_mass + 0.8, t, ha="center", va="bottom")

    def mass_v(self, y0, y1, x_ref, x_mass, wert=None, txt=None):
        s = 1 if x_mass >= x_ref else -1
        for y in (y0, y1):
            self.linie([(x_ref + s * 1.0, y), (x_mass + s * 1.5, y)], lw=LW_D)
        self.ax.annotate("", xy=(x_mass, y0), xytext=(x_mass, y1),
                         arrowprops=dict(arrowstyle="<|-|>", lw=LW_D, color="k",
                                         shrinkA=0, shrinkB=0, mutation_scale=6))
        t = txt if txt is not None else _fmt(wert if wert is not None else abs(y1 - y0))
        self.text(x_mass - 0.8, (y0 + y1) / 2, t, ha="right", va="center", rotation=90)

    def hinweis(self, x, y, xt, yt, s):
        self.ax.annotate(s, xy=(x, y), xytext=(xt, yt), fontsize=6.5, family="DejaVu Sans",
                         arrowprops=dict(arrowstyle="-|>", lw=LW_D, color="k", mutation_scale=5))

    # ---- Rahmen und Schriftfeld -----------------------------------------------
    def _rahmen(self):
        self.rrechteck(10, 10, A3[0] - 20, A3[1] - 20, lw=0.7)
        # Zonen an den Raendern
        for i in range(8):
            x = 10 + (i + 0.5) * (A3[0] - 20) / 8
            self.text(x, 5.5, str(i + 1), size=6, ha="center")
            self.text(x, A3[1] - 7.5, str(i + 1), size=6, ha="center")
        for i, ch in enumerate("ABCDEF"):
            y = A3[1] - 10 - (i + 0.5) * (A3[1] - 20) / 6
            self.text(5.5, y, ch, size=6, va="center")
            self.text(A3[0] - 7.5, y, ch, size=6, va="center")

    def _schriftfeld(self, titel, nummer, gesamt):
        x0, y0, b, h = A3[0] - 10 - 180, 10, 180, 36
        self.rrechteck(x0, y0, b, h, lw=0.7)
        for yy in (y0 + 9, y0 + 18, y0 + 27):
            self.linie([(x0, yy), (x0 + b, yy)], lw=0.3)
        for xx in (x0 + 45, x0 + 110, x0 + 145):
            self.linie([(xx, y0), (xx, y0 + h)], lw=0.3)
        heute = _dt.date.today().strftime("%d.%m.%Y")
        felder = [
            (x0 + 2, y0 + 30.5, "Projekt", "CO2-Wandsensor"),
            (x0 + 47, y0 + 30.5, "Benennung", titel),
            (x0 + 112, y0 + 30.5, "Werkstoff", "PETG (oder PLA)"),
            (x0 + 147, y0 + 30.5, "Massstab", "1:1"),
            (x0 + 2, y0 + 21.5, "Ersteller", "Tobias Schneider"),
            (x0 + 47, y0 + 21.5, "Allgemeintoleranz", "ISO 2768-m"),
            (x0 + 112, y0 + 21.5, "Datum", heute),
            (x0 + 147, y0 + 21.5, "Format", "A3"),
            (x0 + 2, y0 + 12.5, "Masse", "in mm"),
            (x0 + 47, y0 + 12.5, "Projektion", "ISO-E (Methode 1)"),
            (x0 + 112, y0 + 12.5, "Quelle", "generate_enclosure.py"),
            (x0 + 147, y0 + 12.5, "Blatt", f"{nummer} / {gesamt}"),
        ]
        for x, y, k, v in felder:
            self.text(x, y + 3.2, k, size=5, color="0.35")
            self.text(x, y - 0.3, v, size=7.5, weight="bold")
        self.text(x0 + 2, y0 + 3, "Generiert aus dem parametrischen Fusion-Modell. "
                  "Platzhaltermasse (SCD41, Glasdicke) vor dem Druck pruefen.", size=5.5, color="0.3")

    def speichern(self, png: Path):
        self.fig.savefig(png, dpi=110)
        self.pdf.savefig(self.fig)
        plt.close(self.fig)


def _fmt(v: float) -> str:
    return f"{v:.1f}".rstrip("0").rstrip(".").replace(".", ",")


# --------------------------------------------------------------------------- Blatt 1: Geraet
def blatt_geraet(bl: Blatt):
    p = bl.p
    W, H, D = p["W"], p["H"], p["D"]
    R = p["R_AUSSEN"]
    wb, wh = p["AKT_B"] + 1.0, p["AKT_H"] + 1.0
    f = p["FASE_FENSTER"]
    lcd_y = p["LCD_Y"]
    sw_y0, sw_l, sw_h = p["SW_Y0"], p["SW_L"], p["SW_H"]

    # ---------------- Vorderansicht (Zentrum cx, cy) ----------------
    cx, cy = 85.0, 132.0
    bl.ansichtstitel(cx, cy - H / 2 - 24, "Vorderansicht")
    bl.rrechteck(cx - W / 2, cy - H / 2, W, H, R)
    rf = p["R_FRONT"]
    bl.rrechteck(cx - W / 2 + rf, cy - H / 2 + rf, W - 2 * rf, H - 2 * rf, max(R - rf, 0.5), lw=0.2)
    bl.rrechteck(cx - wb / 2 - f, cy + lcd_y - wh / 2 - f, wb + 2 * f, wh + 2 * f, 1.0 + f, lw=0.3)
    bl.rrechteck(cx - wb / 2, cy + lcd_y - wh / 2, wb, wh, 1.0)
    bl.mittellinie((cx, cy - H / 2 - 5), (cx, cy + H / 2 + 5))
    bl.mittellinie((cx - W / 2 - 5, cy + lcd_y), (cx + W / 2 + 5, cy + lcd_y))
    bl.mass_h(cx - W / 2, cx + W / 2, cy - H / 2, cy - H / 2 - 12)
    bl.mass_v(cy - H / 2, cy + H / 2, cx - W / 2, cx - W / 2 - 12)
    bl.mass_h(cx - wb / 2, cx + wb / 2, cy + lcd_y + wh / 2, cy + H / 2 + 8, txt=_fmt(wb))
    bl.mass_v(cy + lcd_y - wh / 2, cy + lcd_y + wh / 2, cx + wb / 2, cx + W / 2 + 8, txt=_fmt(wh))
    bl.mass_v(cy + lcd_y + wh / 2, cy + H / 2, cx + W / 2, cx + W / 2 + 16)
    bl.hinweis(cx + W / 2 - 1.2, cy + H / 2 - 1.2, cx + W / 2 + 4, cy + H / 2 + 14, f"R{_fmt(R)}")
    bl.hinweis(cx - wb / 2 - f / 2, cy + lcd_y - wh / 2 - f / 2, cx - W / 2 - 4, cy - H / 2 + 6,
               f"Fase {_fmt(f)} x 45°\num Displayfenster")
    bl.text(cx, cy - 18, "Front geschlossen\n(keine Lueftung)", size=6.5, ha="center", color="0.35")

    # ---------------- Seitenansicht von links (rechts neben Vorderansicht) ----------------
    sx = cx + W / 2 + 55          # Vorderkante
    bl.ansichtstitel(sx + D / 2, cy - H / 2 - 24, "Seitenansicht von links")
    sk = [(sx + rf, cy + H / 2), (sx + D, cy + H / 2), (sx + D, cy - H / 2), (sx + rf, cy - H / 2)]
    bl.linie(sk)
    bl.ax.add_patch(Arc((sx + rf, cy + H / 2 - rf), 2 * rf, 2 * rf, theta1=90, theta2=180, lw=LW_K))
    bl.ax.add_patch(Arc((sx + rf, cy - H / 2 + rf), 2 * rf, 2 * rf, theta1=180, theta2=270, lw=LW_K))
    bl.linie([(sx, cy + H / 2 - rf), (sx, cy - H / 2 + rf)])
    bl.linie([(sx + p["DS"], cy + H / 2), (sx + p["DS"], cy - H / 2)], lw=0.2)  # Trennfuge Deckel
    # Schiene
    bl.rrechteck(sx + D, cy + sw_y0, sw_h, sw_l, lw=LW_K)
    # Seitenschlitze
    for o in (-7, -3.5, 0):
        yy = cy + p["YCM"] + o
        bl.rrechteck(sx + 3.5, yy - 0.7, p["ZB_Z"] - 1.5 - 3.5, 1.4, lw=0.35)
    bl.mass_h(sx, sx + D, cy - H / 2, cy - H / 2 - 12)
    bl.mass_h(sx, sx + D + sw_h, cy + H / 2, cy + H / 2 + 8)
    bl.mass_v(cy + sw_y0, cy + sw_y0 + sw_l, sx + D + sw_h, sx + D + sw_h + 8)
    bl.mass_v(cy - H / 2, cy + sw_y0, sx + D + sw_h, sx + D + sw_h + 16)
    bl.hinweis(sx + 3.5, cy + p["YCM"] - 3.5, sx - 18, cy - 20, "3x Lueftung\n1,4 x 5 je Seite")
    bl.hinweis(sx + p["DS"], cy + H / 2 - 6, sx + p["DS"] + 6, cy + H / 2 + 16, "Trennfuge\nRueckdeckel")

    # ---------------- Ansicht von unten (Methode 1: ueber der Vorderansicht) ----------------
    uy = cy + H / 2 + 58            # Vorderkante liegt oben, Rueckseite zur Vorderansicht
    bl.text(cx - W / 2 - 4, uy - D / 2, "Ansicht\nvon unten", size=9, weight="bold", ha="right", va="center")
    bl.rrechteck(cx - W / 2, uy - D, W, D, 1.0)
    xs = [-21 + 3.5 * i for i in range(13)]
    for x in xs:
        bl.rrechteck(cx + x - 0.7, uy - (p["ZB_Z"] - 1.5), 1.4, p["ZB_Z"] - 1.5 - 3.5, lw=0.35)
    bl.rrechteck(cx - p["SW_KOPF"] / 2, uy - D - sw_h, p["SW_KOPF"], sw_h, lw=0.4)
    bl.mass_h(cx + xs[0] - 0.7, cx + xs[-1] + 0.7, uy, uy + 6, txt=f"13 Schlitze 1,4 breit, Teilung 3,5 = {_fmt(xs[-1] - xs[0] + 1.4)}")
    bl.mass_v(uy - 3.5, uy - (p["ZB_Z"] - 1.5), cx + W / 2, cx + W / 2 + 8, txt="5")
    bl.text(cx + W / 2 + 18, uy - 8, "Luft stroemt von unten\ndurch die Sensorkammer\n(SCD41)", size=6.5, color="0.35")

    # ---------------- Rueckansicht ----------------
    rx, ry = 330.0, 132.0
    bl.ansichtstitel(rx, ry - H / 2 - 24, "Rueckansicht")
    bl.rrechteck(rx - W / 2, ry - H / 2, W, H, R)
    s = 0.2
    xl, xr, yb_, yt = p["XL"] + s, p["XR"] - s, p["YCH_B"] + s, p["YTOP_IN"] - s
    bl.rrechteck(rx + xl, ry + yb_, xr - xl, yt - yb_, 0, lw=0.35)
    # Schiene (Kopf sichtbar, Fuss verdeckt)
    bl.rrechteck(rx - p["SW_KOPF"] / 2, ry + sw_y0, p["SW_KOPF"], sw_l, lw=LW_K)
    bl.rrechteck(rx - p["SW_FUSS"] / 2, ry + sw_y0, p["SW_FUSS"], sw_l, lw=LW_V, ls=(0, (4, 2)))
    # Kabelaustritt (vom Betrachter hinten gesehen liegt +x rechts)
    kx0, kx1 = p["C3_X"] - 7, p["C3_X"] + 7
    ky0, ky1 = p["YSEP_B"] - 1, p["PY0"] + 9
    bl.rrechteck(rx + kx0, ry + ky0, kx1 - kx0, ky1 - ky0, 0, lw=LW_K)
    bpts = [(p["XL"] + 4.0, p["YCH_B"] + 4.0), (p["XR"] - 4.0, p["YCH_B"] + 4.0)]
    for bx, by in bpts:
        bl.kreis(rx + bx, ry + by, 3.4)
        bl.kreis(rx + bx, ry + by, 6.4, lw=0.3)
    bl.mittellinie((rx, ry - H / 2 - 5), (rx, ry + H / 2 + 5))
    bl.mass_h(rx - p["SW_KOPF"] / 2, rx + p["SW_KOPF"] / 2, ry + sw_y0 + sw_l, ry + H / 2 + 8)
    bl.mass_h(rx + bpts[0][0], rx + bpts[1][0], ry - H / 2, ry - H / 2 - 12)
    bl.mass_v(ry - H / 2, ry + bpts[0][1], rx + W / 2, rx + W / 2 + 8)
    bl.mass_h(rx + kx0, rx + kx1, ry + ky0, ry - 8, txt=_fmt(kx1 - kx0))
    bl.hinweis(rx + bpts[1][0], ry + bpts[1][1], rx + W / 2 + 14, ry - H / 2 + 14,
               "2x Senkung M3 (90°)\nEinschmelzmutter M3 x 5,7\nim Gehaeuse")
    bl.hinweis(rx + kx1, ry + ky1, rx + W / 2 + 4, ry + 4, "Kabelaustritt\nUSB-C Winkelstecker")
    bl.hinweis(rx - p["SW_KOPF"] / 2, ry + sw_y0 + 2, rx - W / 2 - 4, ry - 16,
               "Schwalbenschwanz\nFuss 12 / Kopf 16\nHoehe 3")

    # Detail Schwalbenschwanz
    dx, dy = 235.0, 222.0
    bl.ansichtstitel(dx + 15, dy + 26, "Detail Schiene (2:1)")
    k = 2.0
    pts = [(-p["SW_FUSS"] / 2, 0), (p["SW_FUSS"] / 2, 0), (p["SW_KOPF"] / 2, sw_h), (-p["SW_KOPF"] / 2, sw_h)]
    bl.poly([(dx + 15 + x * k, dy + y * k) for x, y in pts], fill="0.9")
    bl.linie([(dx - 5, dy), (dx + 35, dy)], lw=LW_K)
    bl.mass_h(dx + 15 - p["SW_FUSS"] * k / 2, dx + 15 + p["SW_FUSS"] * k / 2, dy, dy - 8, txt=_fmt(p["SW_FUSS"]))
    bl.mass_h(dx + 15 - p["SW_KOPF"] * k / 2, dx + 15 + p["SW_KOPF"] * k / 2, dy + sw_h * k, dy + sw_h * k + 6,
              txt=_fmt(p["SW_KOPF"]))
    bl.mass_v(dy, dy + sw_h * k, dx + 15 + p["SW_KOPF"] * k / 2, dx + 15 + p["SW_KOPF"] * k / 2 + 8, txt=_fmt(sw_h))
    bl.text(dx - 5, dy - 18, f"Spiel in der Nut: {_fmt(p['SW_SPIEL'])} je Seite", size=6.5, color="0.35")


# --------------------------------------------------------------------------- Blatt 2: Adapter
def blatt_adapter(bl: Blatt):
    p = bl.p
    WP, T = p["WP"], p["WP_T"]
    W, D = p["W"], p["D"]
    Rk = p["R_AUSSEN"] + (WP - W) / 2
    sp = p["SW_SPIEL"]
    y0n, y1n = p["SW_Y0"] - sp, p["SW_Y0"] + p["SW_L"] + sp
    kopf = p["SW_KOPF"] + 2 * sp
    fuss = p["SW_FUSS"] + 2 * sp

    # ---------------- Wandplatte Vorderansicht ----------------
    cx, cy = 95.0, 180.0
    bl.ansichtstitel(cx, cy + WP / 2 + 18, "Wandplatte Hohlwanddose, Vorderansicht")
    bl.rrechteck(cx - WP / 2, cy - WP / 2, WP, WP, Rk)
    bl.rrechteck(cx - W / 2, cy - W / 2, W, W, p["R_AUSSEN"], lw=0.2, ls=(0, (6, 3)))  # Geraetekontur
    bl.kreis(cx, cy, p["DOSE_RAND"], lw=LW_V, ls=(0, (4, 2)))
    bl.rrechteck(cx - kopf / 2, cy + y1n, kopf, p["SW_HUB"], 0)                 # Einsetzfenster
    bl.rrechteck(cx - fuss / 2, cy + y0n, fuss, y1n - y0n, 0)                   # Nut (Fuss)
    bl.rrechteck(cx - kopf / 2, cy + y0n, kopf, y1n - y0n, 0, lw=LW_V, ls=(0, (4, 2)))
    kx0, kx1 = p["C3_X"] - 7, p["C3_X"] + 7
    ky0, ky1 = p["YSEP_B"] - 2, p["PY0"] + 10
    # Vorderansicht: Betrachter vorn, +x des Modells liegt links
    bl.rrechteck(cx - kx1, cy + ky0, kx1 - kx0, ky1 - ky0, 0)
    for sx in (-30, 30):
        bl.rrechteck(cx + sx - 2, cy - 1.75, 4, 3.5, 0)
        bl.rrechteck(cx + sx - 3.3, cy - 3.3, 6.6, 6.6, 0, lw=0.3)
    bl.mittellinie((cx, cy - WP / 2 - 5), (cx, cy + WP / 2 + 5))
    bl.mittellinie((cx - WP / 2 - 5, cy), (cx + WP / 2 + 5, cy))
    for ys, va in ((cy + WP / 2 + 3, "bottom"), (cy - WP / 2 - 3, "top")):   # Schnittverlauf A-A
        bl.linie([(cx, ys - 2.5 if va == "bottom" else ys + 2.5), (cx, ys + 2.5 if va == "bottom" else ys - 2.5)], lw=1.0)
        bl.linie([(cx, ys), (cx + 6, ys)], lw=1.0)
        bl.ax.annotate("", xy=(cx + 6, ys), xytext=(cx, ys),
                       arrowprops=dict(arrowstyle="-|>", lw=0.8, color="k", mutation_scale=7))
        bl.text(cx + 8, ys, "A", size=9, weight="bold", va="center")
    bl.mass_h(cx - WP / 2, cx + WP / 2, cy - WP / 2, cy - WP / 2 - 12)
    bl.mass_v(cy - WP / 2, cy + WP / 2, cx - WP / 2, cx - WP / 2 - 12)
    bl.mass_h(cx - 30, cx + 30, cy - 4, cy - 22, txt="60 (Geraeteschrauben Dose)")
    bl.hinweis(cx + WP / 2 - 3.4, cy + WP / 2 - 3.4, cx + WP / 2 + 4, cy + WP / 2 + 8, f"R{_fmt(Rk)} (konzentrisch zu R{_fmt(p['R_AUSSEN'])})")
    bl.hinweis(cx + p["DOSE_RAND"] / 2 * 0.707, cy - p["DOSE_RAND"] / 2 * 0.707, cx + WP / 2 + 4, cy - WP / 2 - 6,
               f"Aussparung Dosenrand\nØ{_fmt(p['DOSE_RAND'])} x {_fmt(p['DOSE_RAND_T'])} tief (Rueckseite)")
    bl.hinweis(cx + kopf / 2, cy + y1n + p["SW_HUB"] / 2, cx + WP / 2 + 4, cy + 30,
               f"Einsetzfenster, Einschubweg {_fmt(p['SW_HUB'])}\n(verdeckt hinter dem Geraet)")
    bl.hinweis(cx - kx1, cy + ky0, cx - WP / 2 - 4, cy - WP / 2 + 2, "Kabeldurchlass\naus der Dose")
    bl.hinweis(cx + 30 + 3.3, cy + 3.3, cx + WP / 2 + 4, cy + 12, "2x Langloch 3,5 x 7\nSenkung 6,6 x 6,6 tief 2,5")

    # ---------------- Wandplatte Schnitt A-A ----------------
    ax_ = cx + WP / 2 + 70
    bl.ansichtstitel(ax_ + T / 2, cy + WP / 2 + 18, "Schnitt A-A (Mitte)")
    bl.rrechteck(ax_, cy - WP / 2, T, WP, 0, fill="0.88")
    # Nut + Fenster (weiss ausgespart)
    bl.rrechteck(ax_ - 0.01, cy + y0n, p["SW_H"] + sp, y1n - y0n + p["SW_HUB"], 0, fill="white")
    bl.rrechteck(ax_ + T - p["DOSE_RAND_T"], cy - p["DOSE_RAND"] / 2, p["DOSE_RAND_T"] + 0.01, p["DOSE_RAND"], 0,
                 fill="white")
    bl.mass_h(ax_, ax_ + T, cy - WP / 2, cy - WP / 2 - 12)
    bl.mass_h(ax_, ax_ + p["SW_H"] + sp, cy + y1n + p["SW_HUB"], cy + WP / 2 + 8, txt=_fmt(p["SW_H"] + sp))
    bl.mass_v(cy + y0n, cy + y1n + p["SW_HUB"], ax_ + T, ax_ + T + 10)
    bl.text(ax_ - 4, cy - WP / 2 - 22, "Geraet: oben einsetzen,\n15 mm nach unten schieben", size=6.5, color="0.35")

    # ---------------- Tischstaender Seitenansicht (in Gebrauchslage) ----------------
    t = math.tan(math.radians(p["NEIGUNG"]))
    H = p["H"]
    Z_V, Z_H = -2.0, 46.0
    YF = -H / 2 - 5.0 - t * (D - Z_V)

    def yb(z):
        return YF + t * (z - Z_V)

    # Drehung so, dass die Standflaeche waagrecht liegt (Geraet lehnt nach hinten)
    phi = -math.radians(p["NEIGUNG"])
    ox, oy = 268.0, 75.0             # Blattlage der vorderen Unterkante des Fusses

    def P(y, z):
        zz, yy = z - Z_V, y - (yb(Z_V) - 4)
        return (ox + zz * math.cos(phi) - yy * math.sin(phi), oy + zz * math.sin(phi) + yy * math.cos(phi))

    bl.ansichtstitel(ox + 35, 195, "Tischstaender, Seitenansicht in Gebrauchslage")
    bl.poly([P(yb(Z_V), Z_V), P(yb(Z_H), Z_H), P(yb(Z_H) - 4, Z_H), P(yb(Z_V) - 4, Z_V)], fill="0.92")
    y_top = p["SW_Y0"] + p["SW_L"] + p["SW_HUB"] + 4
    bl.poly([P(yb(D) - 2, D), P(y_top, D), P(y_top, D + 7), P(yb(D + 7) - 2, D + 7)], fill="0.92")
    bl.poly([P(yb(D + 7) - 1, D + 7), P(y_top - 12, D + 7), P(yb(D + 24) - 1, D + 24)], fill="0.92")
    geraet = [P(-H / 2, 0), P(H / 2, 0), P(H / 2, D), P(-H / 2, D)]
    bl.poly(geraet, lw=0.4, ls=(0, (10, 2, 2, 2)))
    bl.linie([(ox - 15, oy), (ox + 75, oy)], lw=0.3)                       # Tischebene
    for i in range(16):
        x = ox - 13 + i * 5.5
        bl.linie([(x, oy), (x - 3, oy - 3)], lw=0.2)
    fx0, fx1 = P(yb(Z_V) - 4, Z_V)[0], P(yb(Z_H) - 4, Z_H)[0]
    bl.mass_h(fx0, fx1, oy - 4, oy - 12, txt=_fmt(Z_H - Z_V))
    top = P(H / 2, 0)
    bl.linie([P(-H / 2, 0), (P(-H / 2, 0)[0], top[1] + 4)], lw=0.2, ls=(0, (4, 2)))
    bl.ax.add_patch(Arc(P(-H / 2, 0), 70, 70, theta1=90 - p["NEIGUNG"], theta2=90, lw=LW_D))
    bl.text(P(-H / 2, 0)[0] + 3, P(-H / 2, 0)[1] + 37, f"{_fmt(p['NEIGUNG'])}°", size=8)
    bl.hinweis(*P(-H / 2 + 0.5, D * 0.6), ox + 70, oy + 18, "5 mm Luftspalt:\nLueftung unten bleibt frei")
    bl.text(ox + 48, 170, "Geraet (strichpunktiert) wird von oben\nauf die Schiene gesetzt und\n15 mm nach unten geschoben.", size=6.5,
            color="0.35")


# --------------------------------------------------------------------------- Main
def main():
    p = lade_parameter()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = OUT_DIR / "co2_wandsensor_zeichnung.pdf"
    with PdfPages(pdf_path) as pdf:
        b1 = Blatt(pdf, "Geraet (Gehaeuse + Deckel)", 1, 2, p)
        blatt_geraet(b1)
        b1.speichern(OUT_DIR / "blatt1_geraet.png")
        b2 = Blatt(pdf, "Wandplatte und Tischstaender", 2, 2, p)
        blatt_adapter(b2)
        b2.speichern(OUT_DIR / "blatt2_adapter.png")
    print(f"Zeichnung geschrieben: {pdf_path}")


if __name__ == "__main__":
    main()
