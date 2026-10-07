#!/usr/bin/env python3
"""
Step by step section of docs/assembly.md and docs/de/aufbau.md, written from site/assembly_steps.yaml.

The 3D guide on the project page and the written guide show the same steps with the same texts, so they
can never disagree. The pictures come from the 3D guide (tools/render_steps.mjs).

Usage:   python tools/assembly_docs.py            (update both files)
         python tools/assembly_docs.py --check    (exit 1 if a file is out of date)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
STEPS = ROOT / "site" / "assembly_steps.yaml"
DOCS = {"en": ROOT / "docs" / "assembly.md", "de": ROOT / "docs" / "de" / "aufbau.md"}
IMAGES = {"en": "images/steps", "de": "../images/steps"}
START, END = "<!-- steps:start (generated from site/assembly_steps.yaml) -->", "<!-- steps:end -->"
TEXT = {
    "en": {"step": "Step {i} of {n}", "need": "You need", "tip": "Tip", "guide": "see it in 3D"},
    "de": {"step": "Schritt {i} von {n}", "need": "Du brauchst", "tip": "Tipp", "guide": "in 3D ansehen"},
}
GUIDE = {
    "en": "https://tobi136b.github.io/co2-wall-sensor/assembly.html#step-{i}",
    "de": "https://tobi136b.github.io/co2-wall-sensor/de/assembly.html#step-{i}",
}


def section(lang: str) -> str:
    steps = yaml.safe_load(STEPS.read_text(encoding="utf-8"))
    t, n = TEXT[lang], len(steps)
    out = [START, ""]
    for i, s in enumerate(steps, 1):
        title = s["title"][lang]
        out += [
            f"### {t['step'].format(i=i, n=n)}: {title}",
            "",
            f'<img src="{IMAGES[lang]}/step_{i:02d}.png" width="60%" alt="{title}">',
            "",
            f"**{t['need']}:** {s['need'][lang]}",
            "",
            f"{s['text'][lang]} ([{t['guide']}]({GUIDE[lang].format(i=i)}))",
            "",
            f"> **{t['tip']}:** {s['tip'][lang]}",
            "",
        ]
    out.append(END)
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    stale = []
    for lang, path in DOCS.items():
        text = path.read_text(encoding="utf-8")
        if START not in text or END not in text:
            raise SystemExit(f"{path.relative_to(ROOT)}: markers {START!r} and {END!r} are missing")
        i, j = text.index(START), text.index(END) + len(END)
        new = text[:i] + section(lang) + text[j:]
        if new != text:
            stale.append(path)
            if not args.check:
                path.write_text(new, encoding="utf-8")
                print(f"updated: {path.relative_to(ROOT)}")
    if args.check and stale:
        for p in stale:
            print(f"::error::{p.relative_to(ROOT)} is out of date, run python tools/assembly_docs.py")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
