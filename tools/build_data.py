#!/usr/bin/env python3
"""
Regenerate the dashboard's country rows from the Member update workbook.

Reads  data/EW4All_Infrastructure_Member_Update.xlsx  ("Country data" sheet)
Writes the `var rows = [...]` array in index.html, between the
BEGIN ROWS / END ROWS markers. Nothing else in index.html is touched.

For each dimension the workbook holds a CURRENT value, its source, and an
UPDATED value a Member may have supplied. Where an UPDATED value is present it
wins and the source becomes "MU" (Member update); otherwise the current value
and its source are carried through unchanged.

Run locally with:  python3 tools/build_data.py
"""

import re
import sys
from pathlib import Path

try:
    from openpyxl import load_workbook
except ImportError:
    sys.exit("openpyxl is required:  pip install openpyxl")

ROOT = Path(__file__).resolve().parent.parent
WORKBOOK = ROOT / "data" / "EW4All_Infrastructure_Member_Update.xlsx"
PAGE = ROOT / "index.html"

ND = "No data / To be completed"

# Column indices on the "Country data" sheet, 0-based. Header is row 4;
# country rows start at row 5.
COL = {
    "name": 0, "region": 1, "subregion": 2,
    "delivery": 4, "delivery_src": 5, "delivery_new": 6,
    "stability": 8, "stability_src": 9, "stability_new": 10,
    "speed": 12, "speed_new": 13,
    "storage": 15, "storage_src": 16, "storage_new": 17,
    "software": 19, "software_src": 20, "software_new": 21,
    "note": 23,
}
FIRST_DATA_ROW = 5

# The workbook prints source names in full; the dashboard stores short tags.
SOURCE_TAG = {
    "Monitoring Campaign 2025": "SC",
    "Gap analysis, 18 Nov 2025": "RPT",
    "Gap analysis, 18 November 2025": "RPT",
    "AOMSUC 2025": "A25",
    "AOMSUC 2024": "A24",
    "Member update": "MU",
}


def cell(row, key):
    """Value of one cell as a stripped string."""
    idx = COL[key]
    if idx >= len(row):
        return ""
    v = row[idx].value
    return "" if v is None else str(v).strip()


def to_tag(text):
    """Turn a printed source name (possibly 'A + B') back into short tags."""
    text = (text or "").strip()
    if not text or text == "—":
        return ""
    parts = [SOURCE_TAG.get(p.strip(), p.strip()) for p in text.split("+")]
    return "/".join(p for p in parts if p)


def js(value):
    """A single-quoted JavaScript string literal."""
    return "'" + str(value).replace("\\", "\\\\").replace("'", "\\'") + "'"


def js_list(text):
    """A semicolon-separated cell as a JavaScript array literal.

    A semicolon inside brackets is part of the entry rather than a separator, so
    "CMACast (installed; not operational)" survives as one system.
    """
    if not text or text == ND:
        return "[]"

    items, buf, depth = [], "", 0
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        if ch == ";" and depth == 0:
            items.append(buf)
            buf = ""
        else:
            buf += ch
    items.append(buf)

    items = [i.strip() for i in items if i.strip()]
    return "[" + ",".join(js(i) for i in items) + "]"


def resolve(row, field):
    """Prefer a Member's updated value; fall back to the current record."""
    updated = cell(row, field + "_new")
    if updated:
        return updated, "MU"
    return cell(row, field) or ND, to_tag(cell(row, field + "_src"))


def build_rows():
    sheet = load_workbook(WORKBOOK, data_only=True)["Country data"]
    lines, count = [], 0

    for row in sheet.iter_rows(min_row=FIRST_DATA_ROW):
        name = cell(row, "name")
        if not name:
            continue

        delivery, delivery_src = resolve(row, "delivery")
        stability, stability_src = resolve(row, "stability")
        storage, storage_src = resolve(row, "storage")
        software, software_src = resolve(row, "software")
        speed = cell(row, "speed_new") or cell(row, "speed") or ND

        # Reception pathway was retired from the analysis. The field is kept so the
        # row shape stays stable, but it is never populated or displayed.
        fields = [
            js(name), js(cell(row, "region")), js(cell(row, "subregion")),
            js(ND), js(""),
            js_list(delivery), js(delivery_src),
            js(stability), js(stability_src),
            js(speed),
            js(storage), js(storage_src),
            js_list(software), js(software_src),
            js(cell(row, "note")),
        ]
        lines.append("    [" + ",".join(fields) + "]")
        count += 1

    return "  var rows = [\n" + ",\n".join(lines) + "\n  ];", count


def main():
    if not WORKBOOK.exists():
        sys.exit(f"workbook not found: {WORKBOOK}")

    rows_js, count = build_rows()
    page = PAGE.read_text(encoding="utf-8")

    pattern = re.compile(
        r"(/\* BEGIN ROWS.*?\*/\n)(.*?)(\n  /\* END ROWS \*/)",
        re.DOTALL,
    )
    if not pattern.search(page):
        sys.exit("BEGIN ROWS / END ROWS markers not found in index.html")

    updated = pattern.sub(lambda m: m.group(1) + rows_js + m.group(3), page, count=1)

    if updated == page:
        print(f"No change — {count} countries already current.")
        return

    PAGE.write_text(updated, encoding="utf-8")
    print(f"index.html updated from the workbook: {count} countries.")


if __name__ == "__main__":
    main()
