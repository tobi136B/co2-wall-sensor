#!/usr/bin/env python3
"""
Bill of materials: hardware/bom.yaml is the only place for parts, prices and shop links.

The tables in README.md and README.de.md (between the bom markers) and the table on the
project page are generated from it. The format is explained at the top of bom.yaml.

Usage:   python tools/bom.py            (update the README tables)
         python tools/bom.py --check    (exit 1 if a README table is out of date)
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
BOM_FILE = ROOT / "hardware" / "bom.yaml"
READMES = {"en": ROOT / "README.md", "de": ROOT / "README.de.md"}
SHOPS = ("aliexpress", "amazon")
KEYS = {"name", "name_de", "qty", "details", "used_for", *SHOPS}
START, END = "<!-- bom:start (generated from hardware/bom.yaml) -->", "<!-- bom:end -->"
HEADER = {
    "en": "| Qty | Part | AliExpress | Amazon.de |\n|----:|------|-----------:|----------:|",
    "de": "| Anz. | Teil | AliExpress | Amazon.de |\n|----:|------|-----------:|----------:|",
}
WORDS_DE = {"pcs": "Stk.", "colours": "Farben", "OD": "AD"}
# shown in a shop column without an offer, so no cell stays empty
ONLY = {
    "en": {"aliexpress": "Amazon only", "amazon": "AliExpress only"},
    "de": {"aliexpress": "nur Amazon", "amazon": "nur AliExpress"},
}


def load() -> list[dict]:
    """All parts, with a readable message for the usual typing errors."""
    try:
        parts = yaml.safe_load(BOM_FILE.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise SystemExit(f"bom.yaml: {e}") from e
    if not isinstance(parts, list):
        raise SystemExit("bom.yaml: expected a list of parts, each starting with '- name:'")
    return parts


def rows() -> list[dict]:
    """All parts that have at least one shop link."""
    return [p for p in load() if any(p.get(shop) for shop in SHOPS)]


def part_name(part: dict, lang: str) -> str:
    return str(part.get("name_de") or part["name"]) if lang == "de" else str(part["name"])


def price_label(price: object, lang: str) -> tuple[str, str]:
    """'8.99 (2 pcs) ¹' -> ('8.99 € (2 pcs)', ' ¹'); without a price the label is 'Link'."""
    price = f"{price:.2f}" if isinstance(price, (int, float)) else str(price or "").strip()
    note = ""
    if price.endswith("¹"):
        price, note = price[:-1].strip(), " ¹"
    if not price:
        return ("Link", note)
    label = re.sub(r"^(\d+(?:\.\d+)?)", r"\1 €", price)
    if lang == "de":
        label = re.sub(r"(\d)\.(\d)", r"\1,\2", label)
        for en, de in WORDS_DE.items():
            label = re.sub(rf"\b{en}\b", de, label)
    return (label, note)


def markdown_table(lang: str) -> str:
    lines = [HEADER[lang]]
    for r in rows():
        cells = []
        for shop in SHOPS:
            if r.get(shop):
                label, note = price_label(r[shop].get("price"), lang)
                cells.append(f"[{label}]({r[shop]['link']}){note}")
            else:
                cells.append(f"*{ONLY[lang][shop]}*")
        lines.append(f"| {r.get('qty', '')} | {part_name(r, lang)} | {cells[0]} | {cells[1]} |")
    return "\n".join(lines)


def html_rows(lang: str) -> str:
    out = []
    for r in rows():
        part = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html.escape(part_name(r, lang)))
        cells = []
        for shop in SHOPS:
            if r.get(shop):
                label, _ = price_label(r[shop].get("price"), lang)
                link = html.escape(r[shop]["link"])
                cells.append(f'<a href="{link}" rel="nofollow noopener">{html.escape(label)}</a>')
            else:
                cells.append(f'<span class="only">{ONLY[lang][shop]}</span>')
        out.append(
            f'          <tr><td class="qty">{r.get("qty", "")}</td><td>{part}</td>'
            f'<td class="shop">{cells[0]}</td><td class="shop">{cells[1]}</td></tr>'
        )
    return "\n".join(out)


def check_links() -> list[str]:
    """Every part has a name, no unknown keys, every shop block has an https link."""
    errors = []
    for i, part in enumerate(load(), 1):
        name = part.get("name") if isinstance(part, dict) else None
        if not name:
            errors.append(f"bom.yaml: part {i} has no name")
            continue
        for key in set(part) - KEYS:
            errors.append(f"bom.yaml: {name}: unknown key '{key}' (allowed: {', '.join(sorted(KEYS))})")
        for shop in SHOPS:
            offer = part.get(shop)
            if offer is None:
                continue
            link = offer.get("link", "") if isinstance(offer, dict) else ""
            if not str(link).startswith("https://"):
                errors.append(f"bom.yaml: {name}: {shop} needs 'link:' with a complete https link")
    return errors


def updated_readme(lang: str) -> tuple[str, str]:
    path = READMES[lang]
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if not pattern.search(text):
        raise SystemExit(f"{path.name}: bom markers missing")
    return text, pattern.sub(lambda _: f"{START}\n{markdown_table(lang)}\n{END}", text)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--check", action="store_true", help="only check, do not write")
    args = ap.parse_args()
    errors = check_links()
    for lang, path in READMES.items():
        if errors:
            break
        old, new = updated_readme(lang)
        if old == new:
            continue
        if args.check:
            errors.append(f"{path.name}: bill of materials is out of date, run python tools/bom.py")
        else:
            path.write_text(new, encoding="utf-8")
            print(f"updated: {path.name}")
    for e in errors:
        print(f"::error::{e}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
