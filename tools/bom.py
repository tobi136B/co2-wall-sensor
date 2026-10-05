#!/usr/bin/env python3
"""
Bill of materials: hardware/bom.csv is the only place for parts, prices and shop links.

The tables in README.md and README.de.md (between the bom markers) and the table on the
project page are generated from it.

Usage:   python tools/bom.py            (update the README tables)
         python tools/bom.py --check    (exit 1 if a README table is out of date)

Columns of hardware/bom.csv:
  qty                    quantity, empty for consumables
  part / part_de         name in English / German, **bold** allowed
  specification          details, used_for: where the part goes (both English, for the CSV only)
  price_eur_aliexpress   price in EUR with a dot, optional text in brackets: "8.99 (2 pcs)"
  aliexpress, amazon_de  full https links, empty if there is no offer
  A trailing " ¹" in a price refers to the footnote below the README table.
"""

from __future__ import annotations

import argparse
import csv
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_FILE = ROOT / "hardware" / "bom.csv"
READMES = {"en": ROOT / "README.md", "de": ROOT / "README.de.md"}
SHOPS = (("aliexpress", "price_eur_aliexpress"), ("amazon_de", "price_eur_amazon"))
START, END = "<!-- bom:start (generated from hardware/bom.csv) -->", "<!-- bom:end -->"
HEADER = {
    "en": "| Qty | Part | AliExpress | Amazon.de |\n|----:|------|-----------:|----------:|",
    "de": "| Anz. | Teil | AliExpress | Amazon.de |\n|----:|------|-----------:|----------:|",
}
WORDS_DE = {"pcs": "Stk.", "colours": "Farben", "OD": "AD"}


def rows() -> list[dict[str, str]]:
    """All parts that have at least one shop link."""
    with open(CSV_FILE, encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if any(r[shop] for shop, _ in SHOPS)]


def part_name(row: dict[str, str], lang: str) -> str:
    return row["part_de"] if lang == "de" and row.get("part_de") else row["part"]


def price_label(price: str, lang: str) -> tuple[str, str]:
    """'8.99 (2 pcs) ¹' -> ('8.99 € (2 pcs)', ' ¹'); without a price the label is 'Link'."""
    price = price.strip()
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
        for shop, price in SHOPS:
            if r[shop]:
                label, note = price_label(r[price], lang)
                cells.append(f"[{label}]({r[shop]}){note}")
            else:
                cells.append("")
        lines.append(f"| {r['qty']} | {part_name(r, lang)} | {cells[0]} | {cells[1]} |")
    return "\n".join(lines)


def html_rows(lang: str) -> str:
    out = []
    for r in rows():
        part = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html.escape(part_name(r, lang)))
        cells = []
        for shop, price in SHOPS:
            if r[shop]:
                label, _ = price_label(r[price], lang)
                cells.append(f'<a href="{html.escape(r[shop])}" rel="nofollow noopener">{html.escape(label)}</a>')
            else:
                cells.append("")
        out.append(
            f'          <tr><td class="qty">{r["qty"]}</td><td>{part}</td>'
            f'<td class="shop">{cells[0]}</td><td class="shop">{cells[1]}</td></tr>'
        )
    return "\n".join(out)


def check_links() -> list[str]:
    errors = []
    with open(CSV_FILE, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            for shop, _ in SHOPS:
                if r[shop] and not r[shop].startswith("https://"):
                    errors.append(f"bom.csv: {r['part']}: {shop} is not an https link")
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
