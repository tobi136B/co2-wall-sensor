#!/usr/bin/env python3
"""
Measuring sketch for SCD41 breakout boards, in English and German.

Shows which values of the Fusion generator (SCD_W, SCD_L, SCD_PCB, SCD_H, SCD_SENSOR_X,
SCD_PAD_X) belong to which dimension of the board. The example values are read from the
profile '14x22' in SCD_BOARDS of the generator, so sketch and CAD cannot drift apart.

Usage:   python tools/measure_sketch.py
Output:  docs/images/measure_sensor_en.png, docs/images/measure_sensor_de.png
"""

from __future__ import annotations

import ast
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Rectangle  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "cad" / "fusion" / "generate_enclosure" / "generate_enclosure.py"
OUT_DIR = ROOT / "docs" / "images"
PROFILE = "14x22"

TEXT = {
    "en": {
        "front": "Front view, as mounted (sensor towards you)",
        "side": "Side view",
        "rail": "rail",
        "pads": "pads",
        "insert": "insert from the top",
        "stop": "end stop",
        "hook": "spring hook",
        "footer": "SCD_W: across the rails   SCD_L: slide direction   SCD_PCB: board only, at the edge   "
        "SCD_H: sensor above the board\nSCD_SENSOR_X / SCD_PAD_X: centre of the sensor / of the pad column, "
        "measured from the board centre (right and up are +).  Example: profile {p}",
    },
    "de": {
        "front": "Vorderansicht, eingebaut (Sensor zeigt zu dir)",
        "side": "Seitenansicht",
        "rail": "Schiene",
        "pads": "Lötpunkte",
        "insert": "von oben einschieben",
        "stop": "Anschlag",
        "hook": "Federhaken",
        "footer": "SCD_W: quer zwischen den Schienen   SCD_L: Schieberichtung   SCD_PCB: nur Platine, am Rand   "
        "SCD_H: Sensor über der Platine\nSCD_SENSOR_X / SCD_PAD_X: Mitte des Sensors / der Lötpunktreihe, "
        "gemessen ab Platinenmitte (rechts und oben sind +).  Beispiel: Profil {p}",
    },
}

BOARD = "#1f4e9c"
SENSOR = "#3a3a3a"
CARRIER = "#9aa3ad"
DIM = "#c0392b"


def profile() -> dict[str, float]:
    """SCD_BOARDS[PROFILE] from the generator, read without importing Fusion modules."""
    tree = ast.parse(GENERATOR.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "SCD_BOARDS" for t in node.targets):
            return _eval_boards(node.value)[PROFILE]
    raise SystemExit("SCD_BOARDS not found in the generator")


def _eval_boards(node: ast.AST) -> dict[str, dict[str, float]]:
    out = {}
    for key, value in zip(node.keys, node.values, strict=True):
        out[ast.literal_eval(key)] = {kw.arg: ast.literal_eval(kw.value) for kw in value.keywords}
    return out


def dim(ax, p0, p1, text, offset=(0, 0), rotation=0):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="<->", mutation_scale=10, color=DIM, lw=1.2))
    mx, my = (p0[0] + p1[0]) / 2 + offset[0], (p0[1] + p1[1]) / 2 + offset[1]
    ax.text(
        mx,
        my,
        text,
        color=DIM,
        ha="center",
        va="center",
        fontsize=9,
        rotation=rotation,
        bbox={"facecolor": "white", "edgecolor": "none", "pad": 1},
    )


def draw(lang: str, p: dict[str, float]) -> Path:
    t = TEXT[lang]
    w, length, pcb, h = p["SCD_W"], p["SCD_L"], p["SCD_PCB"], p["SCD_H"]
    sx, pad_x = p["SCD_SENSOR_X"], p["SCD_PAD_X"]
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(11, 5.6), gridspec_kw={"width_ratios": [2.3, 1]})

    # front view: board centred at the origin, x to the right, y up
    for sgn in (-1, 1):
        ax.add_patch(
            Rectangle(
                (sgn * (w / 2 + 0.15) - (1.2 if sgn < 0 else 0), -length / 2 - 1.5),
                1.2,
                length + 3,
                facecolor=CARRIER,
                edgecolor="none",
            )
        )
        ax.add_patch(
            Rectangle(
                (sgn * w / 2 - (0.8 if sgn > 0 else 0), -length / 2 - 0.75),
                0.8,
                0.6,
                facecolor="#6b737c",
                edgecolor="none",
            )
        )
    ax.text(-w / 2 - 0.75, length / 2 + 2.2, t["rail"], ha="center", fontsize=8, color="#555")
    ax.text(w / 2 + 0.75, length / 2 + 2.2, t["rail"], ha="center", fontsize=8, color="#555")
    ax.text(0, -length / 2 - 2.4, t["stop"], ha="center", fontsize=8, color="#555")
    ax.add_patch(Rectangle((-w / 2, -length / 2), w, length, facecolor=BOARD, edgecolor="black", lw=1))
    ax.add_patch(Rectangle((sx - 5.05, -5.05), 10.1, 10.1, facecolor=SENSOR, edgecolor="black", lw=1))
    ax.add_patch(Rectangle((sx - 3.0, -3.0), 6.0, 6.0, facecolor="#e8e8e8", edgecolor="none"))
    if abs(pad_x) > 1e-6:
        for i in range(4):
            ax.add_patch(plt.Circle((pad_x, (i - 1.5) * 2.54), 0.55, facecolor="#d4af37", edgecolor="black", lw=0.6))
        ax.text(
            pad_x + (2.2 if pad_x < 0 else -2.2),
            0,
            t["pads"],
            rotation=90,
            ha="center",
            va="center",
            fontsize=8,
            color="white",
        )
    ax.add_patch(Rectangle((1.0 - 2.0, length / 2 - 0.4), 4.0, 1.2, facecolor="#6b737c", edgecolor="none"))
    ax.text(3.6, length / 2 + 2.2, t["hook"], ha="center", fontsize=8, color="#555")
    ax.add_patch(
        FancyArrowPatch(
            (w / 2 + 6, length / 2 + 4),
            (w / 2 + 6, length / 2 - 2),
            arrowstyle="-|>",
            mutation_scale=14,
            color="#2e7d32",
            lw=2,
        )
    )
    ax.text(w / 2 + 6.6, length / 2 + 1, t["insert"], rotation=90, va="center", fontsize=8, color="#2e7d32")

    dim(ax, (-w / 2, -length / 2 - 4.2), (w / 2, -length / 2 - 4.2), f"SCD_W = {w:g}")
    dim(ax, (-w / 2 - 4, -length / 2), (-w / 2 - 4, length / 2), f"SCD_L = {length:g}", rotation=90)
    dim(ax, (0, length / 2 + 4.2), (sx, length / 2 + 4.2), f"SCD_SENSOR_X = {sx:g}", offset=(0, 1.1))
    ax.plot([0, 0], [-length / 2, length / 2 + 4.6], ls=":", color="black", lw=0.8)
    ax.plot([sx, sx], [5.05, length / 2 + 4.6], ls=":", color="black", lw=0.8)
    if abs(pad_x) > 1e-6:
        dim(ax, (0, -length / 2 + 1.2), (pad_x, -length / 2 + 1.2), f"SCD_PAD_X = {pad_x:g}", offset=(0, 1.0))
        ax.plot([pad_x, pad_x], [-length / 2 + 0.6, -3.8], ls=":", color="white", lw=0.8)
    ax.set_xlim(-w / 2 - 7, w / 2 + 9)
    ax.set_ylim(-length / 2 - 6.5, length / 2 + 7.5)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(t["front"], fontsize=11)

    # side view: board vertical, sensor towards the front (left)
    bx.add_patch(Rectangle((0, -length / 2), pcb, length, facecolor=BOARD, edgecolor="black", lw=1))
    bx.add_patch(Rectangle((-h, -5.05), h, 10.1, facecolor=SENSOR, edgecolor="black", lw=1))
    bx.add_patch(Rectangle((pcb, -length / 2 - 1.5), 2.0, length + 3, facecolor=CARRIER, edgecolor="none"))
    dim(bx, (0, length / 2 + 2.0), (pcb, length / 2 + 2.0), f"SCD_PCB = {pcb:g}", offset=(0, 1.4))
    dim(bx, (-h, -length / 2 - 2.0), (0, -length / 2 - 2.0), f"SCD_H = {h:g}", offset=(0, -1.4))
    bx.set_xlim(-h - 3, pcb + 6)
    bx.set_ylim(-length / 2 - 6.5, length / 2 + 7.5)
    bx.set_aspect("equal")
    bx.axis("off")
    bx.set_title(t["side"], fontsize=11)

    fig.text(0.5, 0.02, t["footer"].format(p=PROFILE), ha="center", fontsize=8.5, color="#333")
    out = OUT_DIR / f"measure_sensor_{lang}.png"
    fig.savefig(out, dpi=140, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out


def main():
    p = profile()
    for lang in TEXT:
        print("written:", draw(lang, p).relative_to(ROOT))


if __name__ == "__main__":
    main()
