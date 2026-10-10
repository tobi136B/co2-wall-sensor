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

import json
import sys
from pathlib import Path

import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parent))
import assembly_model  # noqa: E402
import drawing  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
HERO = ROOT / "cad" / "fusion" / "hero_motion.json"
STEP_MM = 0.7  # largest distance a part moves between two samples (thinnest wall: 0.8 mm)
# the display leaves through the window to the front, as in the README animation (kept on purpose)
ALLOWED = {frozenset(("display", "housing")), frozenset(("display", "inserts"))}
# the ESP32-C3 slides over the spring hook of its sled: allowed while it moves along its guides only
SLIDING = {frozenset(("carrier", "esp32"))}
WIRE_R = assembly_model.WIRE_R
WIRE_END = 2.0  # mm at both ends of a wire where it may touch its pad, its plug or the other wire on the same pad


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
        # the desk stand is not part of the guide, it is checked on its own (check_desk_stand)
        self.meshes["desk_stand"] = trimesh.load(ROOT / "cad" / "stl" / "desk_stand.stl", force="mesh")
        self.exact = self._manager(self.meshes)
        self.shrunk = self._manager({pid: eroded(m) for pid, m in self.meshes.items()})
        self.touching = self._pairs(self.exact)
        self.nested = self._pairs(self.shrunk) | SLIDING

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


def hero_offset(keys: list, t: float) -> np.ndarray:
    """Offset at t of a keyframe track [[t, [x, y, z]], ...], eased between the keyframes (as in render_views.py)."""
    if t <= keys[0][0]:
        return np.array(keys[0][1], float)
    for (t0, a), (t1, b) in zip(keys, keys[1:], strict=False):
        if t <= t1:
            u = ease((t - t0) / (t1 - t0)) if t1 > t0 else 1.0
            return np.array(a, float) + (np.array(b, float) - np.array(a, float)) * u
    return np.array(keys[-1][1], float)


def check_hero(scene: Scene) -> list[str]:
    """The README animation (cad/fusion/hero_motion.json) shows the parts of the Fusion design only."""
    motion = json.loads(HERO.read_text(encoding="utf-8"))
    ids, tracks = motion["ids"], motion["parts"]
    fastest = max(
        np.linalg.norm(np.array(b, float) - np.array(a, float)) / (t1 - t0)
        for keys in tracks.values()
        for (t0, a), (t1, b) in zip(keys, keys[1:], strict=False)
        if t1 > t0
    )
    first: dict[tuple[str, str], float] = {}
    for t in np.linspace(0, 1, int(np.ceil(fastest * 1.5 / STEP_MM)) + 1):  # eased peak speed is 1.5 x the mean
        offsets = {pid: np.zeros(3) for pid in ids.values()}
        for comp, keys in tracks.items():
            offsets[ids[comp]] = hero_offset(keys, t)
        for pair in scene.collisions(offsets):
            first.setdefault(pair, t)
    where = "README animation (cad/fusion/hero_motion.json)"
    return [f"{where} from t = {t:.3f}: {a} hits {b}" for (a, b), t in first.items()]


def check_desk_stand(scene: Scene) -> list[str]:
    """The device slides 15 mm down onto the desk stand, as onto the wall plate."""
    device = [q["id"] for q in scene.data["parts"] if "device" in q["groups"] and not q["id"].startswith("wires")]
    travel = scene.data["stages"]["device_away"]["device"][0][1]
    errors = set()
    for dy in np.linspace(travel, 0, int(np.ceil(travel / STEP_MM)) + 1):
        offsets = {pid: np.array([0, dy, 0]) for pid in device}
        offsets["desk_stand"] = np.zeros(3)
        for a, b in scene.collisions(offsets):
            errors.add(f"desk stand, sliding the device on: {a} hits {b}")
    return sorted(errors)


def _wire_samples(points: list, step: float = 0.3) -> tuple[np.ndarray, np.ndarray]:
    """Points along a wire and their distance from the nearer end."""
    pts = [np.array(points[0], float)]
    for q in points[1:]:
        q = np.array(q, float)
        n = max(1, int(np.ceil(np.linalg.norm(q - pts[-1]) / step)))
        a = pts[-1]
        pts += [a + (q - a) * k / n for k in range(1, n + 1)]
    pts = np.array(pts)
    run = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    return pts, np.minimum(run, run[-1] - run)


def check_wires(scene: Scene) -> list[str]:
    """In the assembled device every wire keeps its distance to every other wire and to every part."""
    wires = []
    for q in scene.data["parts"]:
        for m in q["meshes"]:
            if m["type"] == "tube":
                pts, end = _wire_samples(m["points"])
                wires.append((f"{q['id']} {m['label']}", pts[end > WIRE_END], m.get("r", WIRE_R)))
    errors = []
    for i, (na, a, ra) in enumerate(wires):
        for nb, b, rb in wires[i + 1 :]:
            d = np.min(np.linalg.norm(a[:, None, :] - b[None, :, :], axis=2))
            if d < ra + rb - 0.02:
                errors.append(f"wires: {na} and {nb} come {d:.2f} mm close (pass through each other)")
    for pid, mesh in scene.meshes.items():
        if pid == "desk_stand":
            continue
        for name, pts, r in wires:
            inside = trimesh.proximity.signed_distance(mesh, pts)  # positive inside the part
            worst = float(np.max(inside))
            if worst > -(r - 0.05):
                errors.append(f"wires: {name} runs into {pid} ({worst + r:.2f} mm)")
    return errors


def main() -> int:
    data = assembly_model.model(drawing.load_parameters())
    scene = Scene(data)
    errors = check_wires(scene)
    for i in range(len(data["steps"])):
        errors += check_enter(scene, i)
    # the slider in every distinct state: the parts it moves always come in the same order, so a state that
    # shows fewer parts in the same stage cannot collide when the full one does not
    last_of_state = {}
    for i, s in enumerate(data["steps"]):
        last_of_state[s.get("stage", "") or "assembled"] = i
    for i in sorted(set(last_of_state.values())):
        errors += check_explode(scene, i)
    errors += check_hero(scene)
    errors += check_desk_stand(scene)
    for e in errors:
        print(f"::error::{e}")
    print(
        f"assembly guide: {len(data['steps'])} steps, {len(data['explode'])} disassembly moves, "
        f"{'FAIL' if errors else 'no collisions'}"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
