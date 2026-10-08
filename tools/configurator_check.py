#!/usr/bin/env python3
"""
The online configurator builds the same sensor carrier as Fusion.

For every known SCD41 board, the carrier is built with site/carrier.js in Node (manifold-3d) and compared
with the Fusion export in cad/stl: same bounding box, nearly the same volume (Fusion engraves a label, the
browser does not) and every point of the Fusion surface lies on the browser surface.

Usage:   python tools/configurator_check.py      (needs node and npm install manifold-3d in tools/)
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parent))
import carrier_params  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
VOLUME_TOL = 0.02  # relative, the engraved label of the Fusion part is about 0.3 %
SURFACE_TOL = 0.15  # mm, tessellation of the cylinders


def main() -> int:
    errors = []
    with tempfile.TemporaryDirectory() as tmp:
        params = Path(tmp) / "params.json"
        data = carrier_params.data()
        params.write_text(json.dumps(data), encoding="utf-8")
        for name in data["boards"]:
            out = Path(tmp) / f"{name}.stl"
            subprocess.run(["node", str(ROOT / "tools" / "carrier_stl.mjs"), str(params), name, str(out)], check=True)
            web = trimesh.load(out, force="mesh")
            cad = trimesh.load(ROOT / "cad" / "stl" / f"sensor_carrier_{name}.stl", force="mesh")
            dv = abs(web.volume - cad.volume) / cad.volume
            db = np.abs(web.bounds - cad.bounds).max()
            pts, _ = trimesh.sample.sample_surface_even(cad, 4000, seed=1)
            _, dist, _ = trimesh.proximity.closest_point(web, pts)
            # points of the engraved label lie up to its depth below the browser surface
            far = float(np.mean(dist > SURFACE_TOL))
            print(f"{name}: volume {web.volume:.1f} / {cad.volume:.1f} mm3, bounds {db:.3f} mm, off surface {far:.1%}")
            if dv > VOLUME_TOL:
                errors.append(f"{name}: volume differs by {dv:.1%}")
            if db > 0.05:
                errors.append(f"{name}: bounding box differs by {db:.2f} mm")
            if far > 0.03:
                errors.append(f"{name}: {far:.1%} of the Fusion surface is not on the configurator part")
    for e in errors:
        print(f"::error::{e}")
    if not errors:
        print("configurator matches the Fusion export")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
