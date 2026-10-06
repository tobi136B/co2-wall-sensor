#!/usr/bin/env python3
"""
Collision check of the 3D assembly guide: no part may pass through another one.

Replays every motion of site/assembly.js with the same rules and timing (tools/assembly_model.py):

    enter     the move into every step: groups follow their stage waypoints, then the new parts fly in
    explode   the "take apart" slider, move by move, in every distinct state of the guide

At every sample, all visible parts are tested against each other (triangle intersection, python-fcl).
Parts that touch in the assembled device (a board in its rails, a screw in its insert) may keep
touching while they move apart along a single axis, which is how they are pulled out. Any other
contact is an error. The only exception: the display leaves through the window of the housing.

Usage:   python tools/assembly_check.py          (exit 1 on collisions)
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parent))
import assembly_model  # noqa: E402
import drawing  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
STEP_MM = 0.7  # largest distance a part moves between two samples (thinnest wall: 0.8 mm)
# the display leaves through the window to the front, as in the README animation (kept on purpose)
ALLOWED = {frozenset(("display", "housing")), frozenset(("display", "inserts"))}


def mesh_of(part: dict) -> trimesh.Trimesh | None:
    out = []
    for m in part["meshes"]:
        if m["type"] == "stl":
            out.append(trimesh.load(ROOT / "cad" / "stl" / m["file"], force="mesh"))
        elif m["type"] == "box":
            a, b = np.array(m["min"], float), np.array(m["max"], float)
            out.append(
                trimesh.creation.box(extents=b - a, transform=trimesh.transformations.translation_matrix((a + b) / 2))
            )
        elif m["type"] == "cyl":
            d = np.array(m["d"], float)
            d /= np.linalg.norm(d)
            t = trimesh.geometry.align_vectors([0, 0, 1], d)
            t[:3, 3] = np.array(m["p"], float) + d * m["len"] / 2
            out.append(trimesh.creation.cylinder(radius=m["r"], height=m["len"], transform=t, sections=20))
    return trimesh.util.concatenate(out) if out else None


# ----------------------------------------------------------------------------- motion rules (as in site/assembly.js)
def ease(t: float) -> float:
    return 4 * t**3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def stage_waypoints(data: dict, part: dict, stage: str) -> list[np.ndarray]:
    s = data["stages"].get(stage or "", {})
    for g in part["groups"]:
        if g in s:
            return [np.array(w, float) for w in s[g]]
    return []


def stage_path(data: dict, part: dict, a: str, b: str) -> list[np.ndarray]:
    """Waypoints from stage a to stage b: back along the waypoints of a, then out along those of b."""
    wa, wb = stage_waypoints(data, part, a), stage_waypoints(data, part, b)
    if a == b or (not wa and not wb):
        return [wa[-1] if wa else np.zeros(3)]
    pts = [wa[-1] if wa else np.zeros(3)] + wa[-2::-1] + [np.zeros(3)] + wb
    out = [pts[0]]
    for p in pts[1:]:
        if np.linalg.norm(p - out[-1]) > 1e-9:
            out.append(p)
    return out


def length(points: list[np.ndarray]) -> float:
    return float(sum(np.linalg.norm(b - a) for a, b in zip(points, points[1:], strict=False)))


def duration(points: list[np.ndarray], timing: dict) -> float:
    return max(timing["min_time"], length(points) / timing["speed"]) if len(points) > 1 else 0.0


def at(points: list[np.ndarray], u: float) -> np.ndarray:
    """Point at the fraction u of the arc length of the polyline."""
    total = length(points)
    if total == 0:
        return points[-1].copy()
    s = u * total
    for a, b in zip(points, points[1:], strict=False):
        seg = np.linalg.norm(b - a)
        if s <= seg:
            return a + (b - a) * (s / seg if seg else 0)
        s -= seg
    return points[-1].copy()


def enter_motion(data: dict, index: int) -> dict[str, tuple[list[np.ndarray], float, float]]:
    """Path, start time and duration of every visible part while the guide moves from step index-1 to index."""
    timing = data["timing"]
    steps = data["steps"]
    step = steps[index]
    prev = steps[index - 1] if index else {}
    motions = {}
    t_stage = 0.0
    for part in data["parts"]:
        intro = intro_step(data, part["id"])
        if intro < 0 or intro > index or intro == index:
            continue
        path = stage_path(data, part, prev.get("stage", ""), step.get("stage", ""))
        motions[part["id"]] = (path, 0.0, duration(path, timing))
        t_stage = max(t_stage, duration(path, timing))
    start = t_stage + timing["pause"]
    for pid in step.get("new", []):  # one part after the other, each starts when the previous one is in place
        part = part_by_id(data, pid)
        end = stage_path(data, part, step.get("stage", ""), step.get("stage", ""))[-1]
        off = step.get("from_part", {}).get(pid, step.get("from"))
        path = [end + np.array(off, float), end] if off else [end]
        motions[pid] = (path, start, duration(path, timing))
        start += duration(path, timing) + timing["pause"]
    return motions


def intro_step(data: dict, pid: str) -> int:
    for i, s in enumerate(data["steps"]):
        if pid in s.get("new", []):
            return i
    return -1


def part_by_id(data: dict, pid: str) -> dict:
    return next(q for q in data["parts"] if q["id"] == pid)


def explode_moves(data: dict, visible: set[str]) -> list[dict]:
    return [m for m in data["explode"] if set(m) & visible]


# ----------------------------------------------------------------------------- collision test
def eroded(mesh: trimesh.Trimesh, depth: float = 0.15) -> trimesh.Trimesh:
    """The mesh shrunk by about depth: faces that only touch no longer count as a collision."""
    m = mesh.copy()
    m.vertices = m.vertices - m.vertex_normals * depth
    return m


class Scene:
    """
    Three kinds of part pairs:
        touching   faces touch in the assembled device (a board on its ledge): tested shrunk by 0.15 mm,
                   so sliding along each other is fine but running into a boss is not
        nested     overlap even when shrunk (a screw in its insert, a board under spring preload):
                   may only move apart along one axis, the way they are pulled out
        all others tested exactly
    """

    def __init__(self, data: dict):
        self.data = data
        self.meshes = {q["id"]: m for q in data["parts"] if (m := mesh_of(q)) is not None}
        self.exact = self._manager(self.meshes)
        self.shrunk = self._manager({pid: eroded(m) for pid, m in self.meshes.items()})
        self.touching = self._pairs(self.exact)
        self.nested = self._pairs(self.shrunk)

    @staticmethod
    def _manager(meshes: dict) -> trimesh.collision.CollisionManager:
        manager = trimesh.collision.CollisionManager()
        for pid, m in meshes.items():
            manager.add_object(pid, m)
        return manager

    @staticmethod
    def _pairs(manager: trimesh.collision.CollisionManager) -> set[frozenset]:
        _, names = manager.in_collision_internal(return_names=True)
        return {frozenset(n) for n in names}

    def _hits(self, manager, offsets: dict[str, np.ndarray]) -> set[frozenset]:
        for k, pid in enumerate(self.meshes):
            # parts that are not shown yet wait far away, each in its own place
            off = offsets.get(pid, np.array([1e5 * (k + 1), 0, 0]))
            manager.set_transform(pid, trimesh.transformations.translation_matrix(off))
        hit, names = manager.in_collision_internal(return_names=True)
        return {frozenset(n) for n in names} if hit else set()

    def collisions(self, offsets: dict[str, np.ndarray]) -> list[tuple[str, str]]:
        exact = self._hits(self.exact, offsets)
        if not exact:
            return []
        shrunk = self._hits(self.shrunk, offsets) if exact & self.touching else set()
        bad = []
        for pair in exact:
            a, b = sorted(pair)
            if pair in ALLOWED:
                continue
            if pair in self.nested:
                if np.count_nonzero(np.abs(offsets[a] - offsets[b]) > 1e-6) <= 1:
                    continue  # pulled out of its seat along one axis
            elif pair in self.touching and pair not in shrunk:
                continue  # only sliding along each other
            bad.append((a, b))
        return bad


def check_enter(scene: Scene, index: int) -> list[str]:
    data = scene.data
    motions = enter_motion(data, index)
    end = max((t0 + d for _, t0, d in motions.values()), default=0.0)
    fastest = max((length(p) / d for p, _, d in motions.values() if d > 0), default=1.0)
    n = max(2, int(np.ceil(end * fastest * 2 / STEP_MM)))  # the eased speed peaks at about twice the mean
    errors = set()
    for t in np.linspace(0, end, n):
        offsets = {}
        for pid, (path, t0, d) in motions.items():
            if t < t0:
                continue  # a new part appears when its move starts
            u = 1.0 if d == 0 else min(1.0, max(0.0, (t - t0) / d))
            offsets[pid] = at(path, ease(u))
        for pair in scene.collisions(offsets):
            errors.add(f"step {index + 1} ({data['steps'][index]['title']['en']}), moving in: {pair[0]} hits {pair[1]}")
    return sorted(errors)


def check_explode(scene: Scene, index: int) -> list[str]:
    data = scene.data
    step = data["steps"][index]
    visible = {q["id"] for q in data["parts"] if 0 <= intro_step(data, q["id"]) <= index}
    base = {
        pid: stage_path(data, part_by_id(data, pid), step.get("stage", ""), step.get("stage", ""))[-1]
        for pid in visible
    }
    errors = set()
    done = {pid: np.zeros(3) for pid in visible}
    for k, move in enumerate(explode_moves(data, visible)):
        dist = max(np.linalg.norm(v) for v in move.values())
        for u in np.linspace(0, 1, max(2, int(np.ceil(dist / STEP_MM)) + 1)):
            offsets = {pid: base[pid] + done[pid] for pid in visible}
            for pid, v in move.items():
                if pid in visible:
                    offsets[pid] = offsets[pid] + np.array(v, float) * u
            for pair in scene.collisions(offsets):
                errors.add(f"step {index + 1}, take apart, move {k + 1} {sorted(move)}: {pair[0]} hits {pair[1]}")
        for pid, v in move.items():
            if pid in visible:
                done[pid] = done[pid] + np.array(v, float)
    return sorted(errors)


def main() -> int:
    data = assembly_model.model(drawing.load_parameters())
    scene = Scene(data)
    errors = []
    for i in range(len(data["steps"])):
        errors += check_enter(scene, i)
    # the slider in every distinct state: the parts it moves always come in the same order, so a state that
    # shows fewer parts in the same stage cannot collide when the full one does not
    last_of_state = {}
    for i, s in enumerate(data["steps"]):
        last_of_state[s.get("stage", "") or "assembled"] = i
    for i in sorted(set(last_of_state.values())):
        errors += check_explode(scene, i)
    for e in errors:
        print(f"::error::{e}")
    print(
        f"assembly guide: {len(data['steps'])} steps, {len(data['explode'])} disassembly moves, "
        f"{'FAIL' if errors else 'no collisions'}"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
