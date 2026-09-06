#!/usr/bin/env python3
"""
Regenerate the dashboard's country rows from the Member update workbook.

Reads  data/EW4All_Infrastructure_Member_Update.xlsx  ("Country data" sheet)
Writes the `var rows = [...]` array in index.html, between the
BEGIN ROWS / END ROWS markers. Nothing else in index.html is touched.

The workbook is the source of record: one row per country or territory, one
column per field, edited in place. An empty cell, or the text "No data / To be
completed", means the value has not been reported — it is never read as a
negative answer.

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
    "delivery": 3, "delivery_src": 4,
    "stability": 5, "stability_src": 6,
    "speed": 7,
    "storage": 8, "storage_src": 9,
    "software": 10, "software_src": 11,
    "note": 12,
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


# Any of these, like an empty cell, means the value has not been reported.
EMPTY_TOKENS = {"", "none", "no data / to be completed", "not used", "n/a", "na", "-", "\u2014"}


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
    """A single-quoted JavaScript string literal, ASCII-only.

    Characters above ASCII are written as \\uXXXX escapes so index.html stays pure
    ASCII. That keeps it safe to copy and paste through editors and browsers that
    would otherwise mangle the encoding, and it renders identically.
    """
    text = str(value).replace("\\", "\\\\").replace("'", "\\'")
    out = []
    for ch in text:
        out.append(ch if ord(ch) < 128 else "\\u%04x" % ord(ch))
    return "'" + "".join(out) + "'"


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


def value_of(row, field):
    """A field's value, with the not-reported spellings normalised to ND."""
    raw = cell(row, field)
    return ND if raw.strip().lower() in EMPTY_TOKENS else raw


def build_rows():
    sheet = load_workbook(WORKBOOK, data_only=True)["Country data"]
    lines, count = [], 0

    for row in sheet.iter_rows(min_row=FIRST_DATA_ROW):
        name = cell(row, "name")
        if not name:
            continue

        delivery = value_of(row, "delivery")
        stability = value_of(row, "stability")
        storage = value_of(row, "storage")
        software = value_of(row, "software")
        speed = value_of(row, "speed")

        # Reception pathway was retired from the analysis. The field is kept so the
        # row shape stays stable, but it is never populated or displayed.
        fields = [
            js(name), js(cell(row, "region")), js(cell(row, "subregion")),
            js(ND), js(""),
            js_list(delivery), js(to_tag(cell(row, "delivery_src"))),
            js(stability), js(to_tag(cell(row, "stability_src"))),
            js(speed),
            js(storage), js(to_tag(cell(row, "storage_src"))),
            js_list(software), js(to_tag(cell(row, "software_src"))),
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
