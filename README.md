# Community Safety Resource Planner

Team Halo · DSO 576 · USC Marshall

An interactive dashboard for an LAPD or City of Los Angeles planner reviewing where and when non-enforcement resources may warrant further investigation: outreach, lighting, transit support and victim services. It summarizes recorded offenses and creates an aggregate district review queue. It does not predict crime or automatically allocate resources.

## Intended User and Decisions
The primary user we designed this app for is a public-safety decision-maker, such as an LAPD operations manager, crime analyst, or community-safety coordinator.
This user needs to decide where and when limited resources—such as patrol coverage, outreach programs, or prevention efforts—should be concentrated.
Rather than reviewing thousands of individual records, the user can use this dashboard to answer the practical question: Which neighborhoods and times should be prioritized for further review of non-enforcement safety resources?

## Live App
https://project-bkecyaazl753e63swhydwx.streamlit.app/

## Demo Video
https://drive.google.com/file/d/1Ots6movaMRTyU1lQ3gVSYFBvezjr3H90/view?usp=sharing

## Run locally

Use Python 3.12.

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run dashboard.py
```

The bundled `data/nibrs.parquet` contains all 471,285 rows from the team's September 2026 NIBRS snapshot, with only the fields needed for the app. No street addresses, exact coordinates or original case IDs are bundled. Approximate 0.01-degree cell centers support the filterable LA heatmap. Case IDs are replaced with equality-preserving SHA-256 pseudonyms, so distinct-case totals remain reproducible. Aggregate exports contain district summaries only.

The app runs without the historical file. Legacy Reference clearly reports when it is unavailable. It never blocks Current NIBRS Review.

## Inputs and reproducible preparation

Original team snapshots: [LA Crime Data files](https://drive.google.com/drive/folders/13klDDs4FziK34Z1WlA5TKu5uW5RT2uMU). Access may require a USC account. Original source references are in `project-start.md`.

Place the original files in `data/raw/` (ignored by Git), then run:

```sh
python prepare_data.py --nibrs data/raw/LAPD_NIBRS_Offenses_Dataset.csv
# Optional historical input:
python prepare_data.py --nibrs data/raw/LAPD_NIBRS_Offenses_Dataset.csv --legacy data/raw/Crime_Data_from_2020_to_2024.csv
```

This writes compact Parquet input(s) and `data/manifest.json`, including source SHA-256, row reconciliation, date range and cleaning rules. It preserves all source rows, trims text, parses dates and hours, and applies the same approximate LA coordinate box as the team's cleaning notebook. It is a reproducible app-preparation path, not a claim that the full original notebook's audit has been completed.

The NIBRS snapshot covers occurrence dates through August 22, 2026; it also retains 135 dates before 2000. The app warns about these records, and users can restrict dates explicitly. Source coverage, reporting practices and the NIBRS transition limit comparisons over time. Source and processed row counts are both 471,285; distinct nonmissing case IDs: 423,245.

For an external data location, set `HALO_NIBRS_PATH` and optionally `HALO_LEGACY_PATH` to a CSV or Parquet path. Otherwise the app looks for bundled Parquet, cleaned notebook outputs, then raw CSVs.

## Verify

```sh
pip install -r requirements-dev.txt
python -m pytest -q
# With the original NIBRS CSV in data/raw/:
python validate_real_data.py
```

Regression tests exercise real Streamlit widgets with controlled inputs: reset, separated time blocks, coordinate denominators, padded district IDs, queue add/remove and empty states. Full-data validation independently recounts the original CSV with the Python standard library, then checks the actual dashboard. Results: `docs/validation-real-data.json`. No external deployment has been tested yet.

## How to interpret the dashboard

- Offense rows and unique cases differ: a case may have several offenses.
- Every cue share uses the selected offense-row denominator. Cues overlap and must not be added as separate populations.
- Coordinate validity affects only geographic coverage, never headline, cue or time totals.
- Time blocks are Overnight 00–05, Morning 06–11, Afternoon 12–17 and Evening 18–23. Selecting separated blocks excludes the gap.
- District identifiers preserve leading zeros.
- Queue entries are session-only snapshots; re-adding a district replaces its snapshot. Export before closing the browser. Export includes active filters, timestamp, reasons and limitations.
- Legacy records remain a separate historical reference with independent filters. They are not merged with NIBRS.

Missing values are retained, not treated as zero observations. Time filters exclude invalid/missing times. Missing districts are excluded from the district table and counted separately. Counts do not account for population, exposure, unreported harm, existing service capacity or causality.

## Professor feedback: map and cleaning reconciliation

The LA heatmap aggregates selected offense rows into 0.01-degree cells (about 1 km).
The sidebar date, hour, day, area and offense filters update both the map and headline counts.
Rows without screened coordinates are excluded from the map and counted explicitly.
Gold-to-cardinal colors use a square-root scale that rescales for each selection.
The map describes recorded offenses; it does not estimate population-adjusted risk.

Data notes includes an aggregate reconciliation produced from the actual team notebook
transformation cells and both original snapshots. Rebuild with:

```sh
python reconcile_team_cleaning.py --nibrs data/raw/LAPD_NIBRS_Offenses_Dataset.csv --legacy /path/to/Crime_Data_from_2020_to_2024.csv
python prepare_data.py --nibrs data/raw/LAPD_NIBRS_Offenses_Dataset.csv
```

The reconciliation records notebook/source hashes, before/after row and column counts,
missing keys, exact duplicates and quality flags. No rows are dropped. The app's compact
preparation remains a separate projection; the full cleaning notebook audits additional
fields and converts district codes to numbers, while the app preserves district strings.
The map implementation uses Streamlit's documented PyDeck interface:
https://docs.streamlit.io/develop/api-reference/charts/st.pydeck_chart

## Current Limitations
The dashboard reports raw incident counts rather than population-adjusted rates. A high count may reflect a larger population, more visitors, a larger geographic area, or differences in reporting—not necessarily a greater individual risk.
