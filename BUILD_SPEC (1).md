# BUILD_SPEC — Community Safety Resource Planner

Phase 2 specification for the Phase 3 dashboard MVP. Team Halo, DSO 576, USC Marshall.
Companion documents: `docs/data_contract.md` (dataset columns), `docs/analysis_api.md`
(backend functions and JSON API), `docs/data_inspection.md` (evidence behind every definition),
`docs/fresh_agent_test.md` (dry-run findings and how they were resolved).
Analysis code lives in `src/`; this document describes behavior, not implementation.

## 1. Vision

**User.** A planner in LAPD's community-safety or the Mayor's Office of Community Safety team who
allocates non-enforcement resources: outreach workers, lighting reviews, transit support,
victim services, late-night service capacity.

**Decision.** Which reporting districts, and which days and hours, to send to human planning
review for one of those resources.

**Why this beats current practice.** Today the planner reads area-level monthly crime summaries
and anecdotes. The tool shows recorded offenses at district and hour grain, with the setting and
context flags that point to a resource type, and every number carries its denominator and the
rows it excludes. It produces an evidence queue for people to review. It does not rank
neighborhoods as dangerous, predict individuals, or recommend enforcement.

**Changes since Phase 1.** (1) Time-of-day comparison views were added (professor feedback) so
the tool supports scheduling, not only placing, resources. (2) Context cues are treated as
overlapping: tiles show "rows with any cue" and an overlap matrix, and no view adds cue counts
together (professor feedback). (3) Rows that occurred before the 2024-03-07 NIBRS cutover are
excluded by default and counted in a footnote instead of being silently included. (4) The
dataset is the current NIBRS file only. The legacy 2020–2024 file stays out of the MVP.

### Use cases (select → see → decide)

| # | User selects | Dashboard shows | User decides |
|---|---|---|---|
| UC1 Where | one area, a day type, a time block | tiles, district ranking with cue counts, district centroid map | which districts go to review |
| UC2 When | one or more areas and optionally a context cue | day × hour heatmap, hour profile of the selection against the city, time-block shares by area | which hours to schedule late-night capacity or outreach shifts |
| UC3 Which resource | one or more districts | context breakdown (overlapping cues), premise mix, offense mix | which resource type to request: lighting review, transit support, victim services, outreach |
| UC4 Hand-off | queue rows | review queue with plain-text reasons; "Add districts to review" export | what to send to human planning review |
| UC5 Trust | the Data notes tab | excluded-row counts, definitions, limitations | whether the evidence is strong enough to act |

## 2. Screens

Two front ends are built from the same analysis layer: **A** a Streamlit app
(`app/streamlit_app.py`, filters in the sidebar) and **B** a static HTML page (`web/`, filters in
a bar across the top) that calls the JSON API. Everything below applies to both unless marked.

**Starting view.** Overview tab, no filters applied. The label and footnote are rendered from
the analysis layer's strings and numbers, never retyped:

- label = `describe_selection(Selection())`, which reads `All areas · all days · all hours · all contexts`
- footnote = `"{rows_in_selection:,} offense rows shown · {rows_excluded_by_time:,} excluded (occurred before the 2024-03-07 cutover) · {dataset_eligible_rows:,} eligible rows in the file"`, all three values from `excluded_summary`. On the 2026-09 file that is 464,248 shown, 7,037 excluded, 464,248 eligible.

**Filter bar.** Changing any filter recomputes every tab. Each widget maps to one `Selection`
field; the UI never combines widgets itself.

| Filter | Widget | Selection field | Default |
|---|---|---|---|
| Area | multiselect of the 21 areas (options from `/meta` or the parquet categories) | `areas` | empty = all |
| Reporting district | multiselect of the districts of the chosen areas; disabled with the hint "choose an area first" when no area is chosen | `districts` | empty |
| Days | radio: All · Mon-Thu · Fri-Sun · Custom; Custom reveals a day-of-week multiselect. Mon-Thu/Fri-Sun set `day_type`; Custom sets `days_of_week` and clears `day_type` | `day_type` or `days_of_week` | All |
| Time | radio: Hour range · Time blocks. Hour range shows a 0–23 slider; Time blocks shows a multiselect of the six blocks and resets the slider to 0–23 | `hour_range` or `time_blocks` | Hour range 0–23 |
| Date range | date picker bounded by `/meta` `date_min`–`date_max` (eligible rows). Picker equal to its bounds sends `(None, None)` | `date_range` | full bounds |
| Complete months only | checkbox | `complete_months_only` | off |
| Offense family | multiselect, 12 families plus Unknown | `offense_families` | empty |
| Crime against | multiselect: Person · Property · Society · Mixed · Unknown (Mixed is NIBRS 90Z, All Other Offenses) | `crime_against` | empty |
| Premise group | multiselect, 11 groups | `premise_groups` | empty |
| Context cue | multiselect of the five registry cues, shown by label; a row is kept if it carries any chosen cue | `cues` | empty |
| Include rows before the cutover | checkbox labelled "Include rows that occurred before 2024-03-07 (also admits 135 rows dated before 2000)". When on, the date picker is disabled and `date_range` is `(None, None)` | `include_ineligible_time` | off |

**Tabs**

| Tab | Elements | Decision it supports |
|---|---|---|
| Overview | label and footnote; tile row 1: offense rows (caption "of {dataset_eligible_rows:,} eligible rows", or `dataset_rows` when pre-cutover rows are included), distinct cases, rows with any cue, rows with 2+ cues; tile row 2: one tile per cue in `RESOURCE_CUES`, in registry order, titled with the cue `label`, with the `resource` as caption and `"{share:.1%} of selection"` from the `_share` keys; the overlap note (`CUES_OVERLAP_NOTE`) under the tiles; area comparison bar chart of all 21 areas (offense rows, hover shows share), chosen areas highlighted; monthly trend line over the gap-free complete-month calendar from `monthly_trend`, months flagged `partial` drawn hollow, with the fixed caption "Spring 2024 reflects the NIBRS rollout, not a change in crime" | orient; pick an area |
| When | day × hour heatmap (7 × 24); hour profile: selected share per hour as bars against the reference share as a line, with the ratio in hover; time-block table with a `by` selector (area, district, premise group, offense family, day type), six block columns as shares | schedule hours |
| Where | district table from `counts_by_district`: offense rows, cases, share, the five cue counts; district map from the same table using `district_lat`/`district_lon` (whole-file district centroids stored in the data layer, rounded to about 100 m and present only for districts with at least 5 distinct locations, so markers never move with the filters and never stand for one offense), bubble size = offense rows, OpenStreetMap tiles, with a caption "N districts in this selection have no map marker" counted from null centroids in the table; premise group bar; offense family bar | pick districts |
| Review queue | top-N selector (1–200, default 10); queue table: offense rows, distinct cases, five cue counts, top premise, top offense family, peak time block, reason text; cue overlap matrix; "Add districts to review" downloads every displayed queue row as CSV (Streamlit: `st.download_button` with `review_csv`; HTML: link to `/queue.csv` with the current query string). No per-row checkboxes in the MVP; the planner narrows the queue with the filters and top-N | hand off |
| Data notes | `excluded_summary` as a table with two labelled blocks: the time block titled "Excluded from this view" (pre-cutover, pre-2000), or "Included although before the cutover" when the pre-cutover checkbox is on; and "In this view but missing a field" (no district, no coordinates); dataset totals; definitions table from `docs/data_contract.md`; limitations paragraph | trust |

**Interactions.**

- Any change to the Area filter, by widget or by click, drops chosen districts that are not in the chosen areas; clearing Area clears the district filter. Clicking an area bar on Overview replaces the Area multiselect with that area (Streamlit: set session state and rerun; HTML: set the controls and refetch).
- Clicking a district row on Where sets the Area filter to that district's area (if not already chosen) and adds the district to the Reporting district filter.
- Every chart title carries the label from `describe_selection`.
- Empty selection: tiles show zeros and every selection-only chart and table shows "No offense rows match this selection". The two reference views stay visible: the area comparison (always all 21 areas) and the reference line of the hour profile. The trend draws its zero-filled calendar.
- Reference views use `without_geography(selection)`: the area comparison is computed on it, and the hour profile compares the selection (bars) against it (line). The API does this inside `/areas` and `/hour-profile`; Streamlit calls `without_geography` itself.

## 3. Metrics and visuals

| Metric or visual | Question | Source columns | Calculation (function) | Filters |
|---|---|---|---|---|
| Offense rows | how many recorded offenses | `unique_nibr_no` | row count (`summary_tiles`) | all |
| Distinct cases | how many incidents | `case_no` | distinct count (`summary_tiles`) | all |
| Cue rows and shares (×5) | how many offenses carry each resource cue | `premise_group`, `is_transit`, `is_domestic_violence`, `is_homeless_victim`, `is_victim_shot` | rows where the cue mask is true and their share of the selection (`summary_tiles`); lighting = premise group Street/Sidewalk or Parking | all |
| Rows with any cue, with 2+ cues | how much the cues overlap | same | OR of masks / count ≥ 2 (`summary_tiles`) | all |
| Cue overlap matrix | which cues co-occur | same | 5 × 5 co-occurrence counts (`cue_overlap`) | all |
| Area comparison | which areas carry the selection | `area_name` | rows, cases, share, rows with any cue per area, all 21 shown (`area_comparison`) | all except area and district |
| Monthly trend | is volume changing | `occurrence_month`, `is_complete_month`, `date_range` | rows per complete month on a gap-free calendar, `partial` flag for months the date filter cuts (`monthly_trend`) | all |
| Day × hour heatmap | when offenses occur | `day_of_week`, `occurrence_hour` | 7 × 24 counts, zero-filled (`heatmap_day_hour`) | all |
| Hour profile vs reference | is this area's timing unusual | `occurrence_hour` | share per hour in the selection (bars) against `without_geography(selection)` (line), plus ratio (`hour_profile_comparison`) | all |
| Time-block comparison | which blocks dominate | `time_block` and the `by` column | rows per block per group, shares within group (`time_block_comparison`) | all |
| District ranking | which districts carry the selection | `district_id`, `case_no`, cue columns, `district_lat`, `district_lon` | rows, cases, share, five cue counts, whole-file district centroid; NA districts excluded and counted (`counts_by_district`) | all |
| Premise, offense breakdown | what settings and offense types | `premise_group`, `offense_family` | rows and share (`premise_breakdown`, `offense_breakdown`) | all |
| Review queue | why a district appears | all of the above per district | top-N by offense rows; reason lists non-zero cue counts; no composite score (`review_queue`) | all |
| Excluded summary | what the default view leaves out, and what the visible rows lack | `time_eligibility`, `district_id`, `valid_coordinates` | time exclusions counted ignoring eligibility; district and coordinate gaps counted on the visible rows; dataset totals (`excluded_summary`) | all |

## 4. Architecture

Three layers, each with a written contract, each testable alone.

| Layer | Artifact | Contract | Depends on |
|---|---|---|---|
| Data | `Complete_LAPD_Data_Cleaning.ipynb` → `cleaned_outputs/…csv` → `src/build_dataset.py` → `data/nibrs_analysis.parquet`; lookups `src/premise_groups.csv`, `src/nibrs_offense_codes.csv` | `docs/data_contract.md` | raw CSV |
| Analysis | `src/analysis.py`: `Selection`, `RESOURCE_CUES`, pure functions; `src/api.py`: FastAPI JSON adapter | `docs/analysis_api.md` | parquet columns only |
| Presentation A | `app/streamlit_app.py` | calls `src/analysis.py` directly | analysis functions |
| Presentation B | `web/index.html`, `web/app.js` (Plotly.js) | calls `src/api.py` endpoints | JSON API |

Rules. The UI never computes a metric, share, or denominator; it renders what the analysis layer
returns. A new cue is one registry entry in `src/analysis.py` and appears in tiles, context
breakdown, queue and overlap without UI changes. A cleaning change that keeps the contract needs
no analysis or UI edits. Both front ends must show identical numbers for the same selection
because they call the same functions.

Two front ends are built on purpose, to compare Streamlit with a plain HTML page on build
effort, responsiveness, and deployability. The comparison is written up in Phase 3.

## 5. Technical choices

| Choice | Decision | Why (measured on the 2026-09 file) |
|---|---|---|
| Storage | one Parquet file, 17 MB, 34 columns, categoricals | `read_parquet` 0.2 s once pandas is imported, about 1.1 s cold including imports; 57 MB in memory. The cleaned CSV takes 2.9 s and 147 MB for the same columns |
| Query engine | pandas in memory | one-area selection filters in 6 ms; tiles, districts, hours and queue together 24 ms; whole-frame heatmap, areas and time blocks 113 ms. No need for DuckDB or Postgres |
| Caching | Streamlit `st.cache_data` on the loader; API loads once at startup | nothing else is slow enough to cache |
| Charts | Plotly in Streamlit and Plotly.js in HTML | same visual grammar in both UIs keeps the comparison fair |
| Map | district centroid bubbles on OpenStreetMap tiles | the parquet holds no row coordinates, only one whole-file centroid per district, so the privacy boundary is enforced by the data layer rather than by UI discipline |
| HTML back end | FastAPI, 17 GET endpoints (15 JSON, `/queue.csv`, `/web/` static files), same query parameters everywhere, CORS open for GET | keeps one metric implementation; the HTML page is served by the same process at `http://127.0.0.1:8000/web/` |
| Running | see README: `python -m streamlit run app/streamlit_app.py` and `uvicorn src.api:app`, both from the repository root | one process serves API and HTML; no path shims |
| Deployment later | Streamlit Community Cloud for A; any small Python host for B | parquet is small enough to ship with the app |
| Rebuild | `python src/build_dataset.py` after re-running the notebook | 6 s |

## 6. Build order

1. Run `pytest` on the committed `data/nibrs_analysis.parquet` (rebuild via notebook → `build_dataset.py` only if the source changed). Nothing else starts until green.
2. Streamlit Overview tab: sidebar filters, label, footnote, tiles, area comparison, trend. Check tiles against acceptance A3.
3. Streamlit When, Where, Review queue (with export), Data notes.
4. Start the API, check `/meta` and `/tiles` against the Streamlit numbers, and open `http://127.0.0.1:8000/web/` (the placeholder page in `web/` is served by the same process).
5. HTML page in `web/`: filter bar and tiles, then charts, then queue and export. Files added to `web/` are served without a restart.
6. Parity pass on the acceptance selection in both UIs. Write the Streamlit-vs-HTML comparison.

## 7. Acceptance checks

| # | Check |
|---|---|
| A1 | `pytest` passes, including the Phase 1 reproduction: seed-42 sample of 4,000 rows, Central, Fri-Sun, 20–23 gives 29 rows, 16 lighting, 1 transit, 1 victim services, 1 outreach, hours 7/7/11/4 |
| A2 | Default view shows 464,248 offense rows and the footnote reports 7,037 excluded |
| A3 | Selection `Central · Fri-Sun · 20:00-23:59 · all contexts` shows the same tile values in Streamlit, in `/tiles?areas=Central&day_type=Fri-Sun&hour_min=20&hour_max=23`, and in `summary_tiles` run from Python (3,433 offense rows, 3,162 cases, 1,807 lighting, 218 transit, 225 victim services, 140 outreach, 25 victim shot, 2,197 with any cue) |
| A4 | Changing the Context filter changes tiles, district table, hourly chart and queue, and the label updates |
| A5 | Hour charts always show 24 hours; heatmap always 7 × 24, zeros included |
| A6 | Tiles show "rows with any cue" and it is never larger than the sum of cue tiles; the overlap matrix is reachable from the queue tab |
| A7 | No street address or raw coordinate is displayed anywhere; the map shows district centroids only |
| A8 | Export CSV contains the queue columns plus a `selection` column with the label |
| A9 | Choosing Central in the Area filter leaves all 21 bars in the area comparison, with Central highlighted |
| A10 | Cold start under 5 s; any filter change re-renders under 1 s on a laptop |
| A11 | Filtering to one district and one cue that leaves a single offense row shows the map marker at the district's centroid from `/districts`, identical to its position with no filters; a district with a null centroid shows no marker and is counted in the caption |
| A12 | A date range inside one month renders that month hollow (`partial`) on the trend; a selection with no rows in some month still shows that month at zero |

## 8. Out of scope for the MVP

Forecasts, individual or district risk scores, per-capita rates (no ACS denominators yet), the
legacy 2020–2024 file (needs a validated crime-code and premise crosswalk), causal claims about
resources, and anything at address level. Recorded offenses are not all harm; the Data notes tab
says so on screen.
