# EW4All Satellite Infrastructure Dashboard — RA II and RA V

Satellite data **infrastructure** reported by National Meteorological and Hydrological
Services (NMHSs) across WMO Regional Association II (Asia) and Regional Association V
(South-West Pacific), in support of the Early Warnings for All (EW4All) initiative.

Prepared for the Joint RA II / RA V Task Team on Satellite Data and Products in Support
of EW4All (RA II/V JTT-SAT-EW4ALL).

## What the dashboard shows

Four infrastructure dimensions, each with a headline figure over the breakdown it is
derived from:

| Dimension | What it records |
| --- | --- |
| Delivery systems in use | Named broadcast services and portals a Member reports using |
| Internet connection stability | Reliability judged against operational use of 10-minute geostationary imagery |
| Long-term storage capacity | Whether satellite data can be archived beyond immediate operational use |
| Visualisation software | Tools forecasters use to view and analyse satellite data |

Four tabs: **Regional overview** (fixed regional summary), **Country data** (filterable
table, click a row for a country profile), **Data completeness** (who still needs to be
contacted), and **Definitions & sources** (per-field provenance and category definitions).

## Files

    index.html                     the whole dashboard — markup, styles, data and logic
    assets/wmo-logo-white.png      WMO logo used in the page header

No build step, no framework and no package manager. Open `index.html` in a browser, or
serve the folder over GitHub Pages.

## Updating the data

**The normal route — edit the workbook.** Country values are generated from
`data/EW4All_Infrastructure_Member_Update.xlsx`. Commit a new version of that file and a
GitHub Action rebuilds the dashboard and commits the result; the published page follows a
minute or so later. Nothing to install and no command to run.

    data/EW4All_Infrastructure_Member_Update.xlsx   the source of record for country values
    tools/build_data.py                            regenerates the rows in index.html
    .github/workflows/update-dashboard.yml          runs the generator on every push

On the workbook's "Country data" sheet each dimension has a **CURRENT** value with its
source and an **UPDATED** column for a Member's answer. Where an UPDATED value is present
it wins and the source is recorded as "Member update"; otherwise the current value and its
source carry through unchanged. Separate multiple systems or tools with a semicolon; a
semicolon inside brackets counts as part of the entry, not as a separator. To run the
generator yourself:

    pip install openpyxl
    python3 tools/build_data.py

**Editing the page directly** still works for anything the workbook does not cover —
category scales, the delivery routes with no reported users, field definitions. Those live
in `index.html` and are never overwritten by the generator, which replaces only the block
between the `BEGIN ROWS` and `END ROWS` markers.

All 57 country and territory records live in the `INFRA_DATA` object inside
`index.html`, under the `DATA SOURCE` comment banner (around line 160). One array entry
per Member, in this field order:

    [name, region, subregion, pathway, pathwaySrc, delivery[], deliverySrc,
     stability, stabSrc, speed, storage, storageSrc, software[], softwareSrc, note]

Edit a value there and reload — nothing else needs to change. Every value carries a
source tag: `SC` Monitoring Campaign 2025 scorecard, `RPT` gap analysis of
18 November 2025, `A24` AOMSUC country report 2024, `A25` AOMSUC country report 2025.
`No data / To be completed` means not reported; it is never read as a negative answer.

The `pathway` fields are retained in the data but unused: reception pathway was retired
from the analysis, so it is not displayed anywhere.

## Sources

- WMO Monitoring Data Collection Campaign, 2025
- AOMSUC country reports, 2024 and 2025 rounds
- EW4All Report: preliminary gap analysis, 18 November 2025

## Status

Working draft for Member validation. Not an agreed WMO position. Figures describe the
responding NMHSs rather than a full census, and response rates differ by question, so
denominators are stated with each figure.

Contact: WMO Space Programme.

## Note

The designations employed and the presentation of material herein do not imply the
expression of any opinion whatsoever on the part of the Secretariats of WMO or the United
Nations concerning the legal status of any country, area or territory, or of its
authorities, or concerning the delimitation of its borders. The mention of specific
companies or products does not imply that they are endorsed or recommended by WMO in
preference to others of a similar nature which are not mentioned or advertised.
