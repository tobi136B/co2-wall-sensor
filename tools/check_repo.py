#!/usr/bin/env python3
"""
Repository consistency checks, run by the CI.

* English and German documents have the same structure (headings and images).
* The print files in cad/ were exported from the current parameters of the Fusion generator.
* Every link in the bill of materials is an absolute https link.

Usage:   python tools/check_repo.py            (check)
         python tools/check_repo.py --write    (write cad/build_info.json from the current parameters,
                                                only after exporting new print files from Fusion)
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "cad" / "fusion" / "generate_enclosure" / "generate_enclosure.py"
BUILD_INFO = ROOT / "cad" / "build_info.json"

DOC_PAIRS = [
    ("README.md", "README.de.md"),
    ("docs/assembly.md", "docs/de/aufbau.md"),
    ("docs/design.md", "docs/de/design.md"),
    ("docs/faq.md", "docs/de/faq.md"),
    ("docs/wiring.md", "docs/de/verdrahtung.md"),
]


def parameter_specs() -> list[tuple[str, float]]:
    """Same parsing as parameter_specs() in the Fusion generator."""
    text = GENERATOR.read_text(encoding="utf-8")
    block = text[text.index("# ===================== PARAMETERS") : text.index("\nEXPORT =")]
    ns: dict = {}
    exec(block, ns)  # noqa: S102 (versioned file from this repository)
    specs = []
    for line in block.splitlines():
        m = re.match(r"^([A-Z0-9_, ]+?)\s*=\s*([^#]+?)\s*(?:#\s*(.*))?$", line)
        if m:
            specs += [(n.strip(), ns[n.strip()]) for n in m.group(1).split(",")]
    return specs


def fingerprint() -> str:
    values = ";".join(f"{n}={float(v):.6g}" for n, v in parameter_specs())
    return hashlib.sha256(values.encode("utf-8")).hexdigest()


def structure(path: Path) -> tuple[list[int], int]:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    levels = [len(m.group(1)) for m in re.finditer(r"^(#{1,4}) ", text, flags=re.M)]
    images = len(re.findall(r"!\[|<img ", text))
    return levels, images


def check_docs() -> list[str]:
    errors = []
    for en, de in DOC_PAIRS:
        (le, ie), (ld, id_) = structure(ROOT / en), structure(ROOT / de)
        if le != ld:
            errors.append(f"{en} and {de} have different headings: {le} vs {ld}")
        if ie != id_:
            errors.append(f"{en} and {de} reference a different number of images: {ie} vs {id_}")
    return errors


def check_print_files() -> list[str]:
    if not BUILD_INFO.exists():
        return [f"{BUILD_INFO.relative_to(ROOT)} is missing, export the print files from Fusion"]
    info = json.loads(BUILD_INFO.read_text(encoding="utf-8"))
    errors = []
    if info.get("parameters_sha256") != fingerprint():
        errors.append(
            "The parameters in generate_enclosure.py changed after the print files were exported. "
            "Run the generator in Fusion with EXPORT = True and commit the new STL/STEP files."
        )
    for part in info.get("parts", []):
        if not (ROOT / "cad" / "stl" / f"{part}.stl").exists():
            errors.append(f"cad/stl/{part}.stl is missing")
    return errors


def check_bom() -> list[str]:
    errors = []
    with open(ROOT / "hardware" / "bom.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            for key in ("aliexpress", "amazon_de"):
                link = row.get(key) or ""
                if link and not link.startswith("https://"):
                    errors.append(f"bom.csv: {row['part']}: {key} is not an https link")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--write", action="store_true", help="write cad/build_info.json")
    args = ap.parse_args()
    if args.write:
        info = json.loads(BUILD_INFO.read_text(encoding="utf-8")) if BUILD_INFO.exists() else {}
        info["parameters_sha256"] = fingerprint()
        BUILD_INFO.write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
        print(f"written: {BUILD_INFO.relative_to(ROOT)}")
        return 0
    errors = check_docs() + check_print_files() + check_bom()
    for e in errors:
        print(f"::error::{e}")
    if not errors:
        print("repository checks passed")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
