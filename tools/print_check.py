#!/usr/bin/env python3
"""
Printability check of the STL files for a 0.4 mm nozzle.

Measures the wall thickness all over every part: points are sampled on the surface and a ray
is cast into the material along the inverted surface normal. A wall counts as thin when the
ray leaves the part through an opposite, roughly parallel face (this ignores chamfers and
fillets, where the ray leaves through a neighbouring face). Thin spots are grouped and
reported with their position in model coordinates (mm, as in the Fusion generator).

The letters of the engraved labels are surface details and are skipped.

    MIN_WALL   2 lines of a 0.4 mm nozzle (0.8 mm): thinner walls fail the check
    WARN_WALL  3 lines (1.2 mm): reported as a note

Usage:   python tools/print_check.py            (all parts, exit 1 on failures)
         python tools/print_check.py housing    (single parts)
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
STL = ROOT / "cad" / "stl"
NOZZLE = 0.4
MIN_WALL = 2 * NOZZLE
WARN_WALL = 3 * NOZZLE
SAMPLES_PER_MM2 = 6.0
GROUP = 2.0  # mm, thin points closer than this form one spot
LABEL_DEPTH = 0.4  # mm, depth of the engraved labels
LABEL_FACE = 40.0  # mm2, a face that carries a label is at least this large ...
LABEL_TRIANGLES = 200  # ... and is cut into many triangles by the letters


def thickness(mesh: trimesh.Trimesh) -> tuple[np.ndarray, np.ndarray]:
    """Points on the surface and the wall thickness measured from them (nan where undefined)."""
    count = int(max(2000, mesh.area * SAMPLES_PER_MM2))
    points, faces = trimesh.sample.sample_surface_even(mesh, count, seed=1)
    normals = mesh.face_normals[faces]
    origins = points - normals * 1e-3
    locations, index_ray, index_tri = mesh.ray.intersects_location(origins, -normals, multiple_hits=False)
    result = np.full(len(points), np.nan)
    opposite = np.einsum("ij,ij->i", mesh.face_normals[index_tri], normals[index_ray]) < -0.85
    dist = np.linalg.norm(locations - points[index_ray], axis=1)
    result[index_ray[opposite]] = dist[opposite]
    return points, result


def label_planes(mesh: trimesh.Trimesh) -> list[tuple[np.ndarray, np.ndarray, np.ndarray]]:
    """Large planar faces cut into many triangles: the faces that carry an engraved label."""
    planes = []
    for facet, area, normal, origin in zip(
        mesh.facets, mesh.facets_area, mesh.facets_normal, mesh.facets_origin, strict=True
    ):
        if area > LABEL_FACE and len(facet) > LABEL_TRIANGLES:
            pts = mesh.vertices[mesh.faces[facet].ravel()]
            planes.append((normal, origin, np.vstack([pts.min(axis=0), pts.max(axis=0)])))
    return planes


def in_label(centre: np.ndarray, planes: list) -> bool:
    for normal, origin, box in planes:
        depth = float(np.dot(origin - centre, normal))
        inside = np.all(centre >= box[0] - 0.5) and np.all(centre <= box[1] + 0.5)
        if -0.05 <= depth <= LABEL_DEPTH + 0.05 and inside:
            return True
    return False


def spots(points: np.ndarray, values: np.ndarray, limit: float) -> list[tuple[np.ndarray, float, int]]:
    """Groups of points thinner than limit: (centre, minimum, number of points)."""
    mask = values < limit
    pts, vals = points[mask], values[mask]
    groups: list[list[int]] = []
    unassigned = set(range(len(pts)))
    while unassigned:
        seed = unassigned.pop()
        group, queue = [seed], [seed]
        while queue:
            i = queue.pop()
            near = [j for j in list(unassigned) if np.linalg.norm(pts[j] - pts[i]) < GROUP]
            for j in near:
                unassigned.discard(j)
            group += near
            queue += near
        groups.append(group)
    out = [(pts[g].mean(axis=0), float(vals[g].min()), len(g)) for g in groups]
    return sorted(out, key=lambda s: s[1])


def check(name: str) -> tuple[list[str], list[str]]:
    mesh = trimesh.load(STL / f"{name}.stl", force="mesh")
    points, values = thickness(mesh)
    planes = label_planes(mesh)
    errors, hints = [], []
    for limit, target in ((MIN_WALL, errors), (WARN_WALL, hints)):
        for centre, minimum, n in spots(points, values, limit):
            if n < 3 or in_label(centre, planes):
                continue
            if (target is errors) == (minimum < MIN_WALL - 0.01):
                where = f"x {centre[0]:.1f}, y {centre[1]:.1f}, z {centre[2]:.1f}"
                target.append(f"{name}: wall {minimum:.2f} mm at {where}")
    return errors, hints


def main() -> int:
    names = sys.argv[1:] or sorted(p.stem for p in STL.glob("*.stl"))
    failed = False
    for name in names:
        errors, hints = check(name)
        for e in errors:
            print(f"::error::{e} (below {MIN_WALL:.1f} mm = 2 lines of a {NOZZLE} mm nozzle)")
        for h in hints:
            print(f"note: {h} (below {WARN_WALL:.1f} mm)")
        print(f"{name}: {'FAIL' if errors else 'ok'}")
        failed |= bool(errors)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
