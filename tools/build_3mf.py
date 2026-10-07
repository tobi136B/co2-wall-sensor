#!/usr/bin/env python3
"""
Print-ready 3MF plates: every part in its print orientation, arranged on a 220 x 220 mm bed.

Open the 3MF in PrusaSlicer, OrcaSlicer, Bambu Studio or Cura, choose your printer and PETG, slice.

Usage:   python tools/build_3mf.py
Output:  cad/3mf/co2_wall_sensor_device.3mf   housing, sensor carrier (14x22 board), back cover, both cable ports,
                                              lock tab
         cad/3mf/sensor_carrier_15x20.3mf     sensor carrier for the 15 x 20 mm board
         cad/3mf/co2_wall_sensor_mounts.3mf   wall plate, desk stand
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
STL = ROOT / "cad" / "stl"
OUT = ROOT / "cad" / "3mf"
BED = 220.0
GAP = 8.0

FLAT = np.eye(4)
ON_EDGE = trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0])  # lower edge (-y) onto the bed
FLIP = trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0])  # back face (+z) onto the bed
ON_SIDE = trimesh.transformations.rotation_matrix(math.pi / 2, [0, 1, 0])  # side face (+x) onto the bed

PLATES = {
    "co2_wall_sensor_device": [
        ("housing", FLAT),
        ("back_cover", FLAT),
        ("sensor_carrier_14x22", ON_EDGE),
        ("cable_port_back", FLIP),
        ("cable_port_bottom", FLIP),
        ("lock_tab", FLAT),
        ("desk_stand", ON_SIDE),  # on the plate as well, delete it in the slicer for a wall mount
    ],
    "co2_wall_sensor_mounts": [
        ("wall_plate", FLAT),
        ("desk_stand", ON_SIDE),
    ],
    "sensor_carrier_15x20": [
        ("sensor_carrier_15x20", ON_EDGE),
    ],
}


def oriented(name: str, transform: np.ndarray) -> trimesh.Trimesh:
    mesh = trimesh.load(STL / f"{name}.stl", force="mesh")
    mesh.apply_transform(transform)
    mesh.apply_translation(-mesh.bounds[0])  # lowest point on the bed, corner at the origin
    return mesh


def arrange(meshes: list[tuple[str, trimesh.Trimesh]]) -> list[tuple[str, trimesh.Trimesh]]:
    """Simple shelf packing, largest footprint first, the result is centred on the bed."""
    order = sorted(meshes, key=lambda m: -m[1].extents[0] * m[1].extents[1])
    x = y = row_h = 0.0
    placed = []
    for name, mesh in order:
        w, d = mesh.extents[0], mesh.extents[1]
        if x > 0 and x + w > BED:
            x, y, row_h = 0.0, y + row_h + GAP, 0.0
        mesh.apply_translation([x, y, 0])
        placed.append((name, mesh))
        x += w + GAP
        row_h = max(row_h, d)
    lo = np.min([m.bounds[0] for _, m in placed], axis=0)
    hi = np.max([m.bounds[1] for _, m in placed], axis=0)
    if hi[0] - lo[0] > BED or hi[1] - lo[1] > BED:
        raise SystemExit(f"parts do not fit on a {BED:.0f} mm bed")
    shift = [(BED - (hi[0] - lo[0])) / 2 - lo[0], (BED - (hi[1] - lo[1])) / 2 - lo[1], 0]
    for _, mesh in placed:
        mesh.apply_translation(shift)
    return placed


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for plate, parts in PLATES.items():
        scene = trimesh.Scene()
        for name, mesh in arrange([(n, oriented(n, t)) for n, t in parts]):
            scene.add_geometry(mesh, node_name=name, geom_name=name)
        out = OUT / f"{plate}.3mf"
        out.write_bytes(trimesh.exchange.threemf.export_3MF(scene))
        print(f"written: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
