# Community Safety Resource Planner - Phase 2 Build Specification

## 1. Current vision

The Community Safety Resource Planner is a local dashboard for an LAPD or City of Los Angeles public-safety planner who must decide which neighborhoods and time blocks deserve further human review for non-enforcement resources, such as outreach, lighting review, transit support, victim services, or late-night service capacity. It improves current practice by turning cleaned offense records into consistent, filterable summaries instead of requiring planners to manually scan individual records or compare disconnected spreadsheets.

The dashboard describes recorded offenses; it does not measure all harm, predict individual behavior, recommend enforcement, automatically allocate resources, or claim that any intervention caused a change.

### Core use cases

1. **Area and time review:** User selects an LAPD area, reporting district, days, and hours -> dashboard shows selected-record counts, hourly patterns, premise context, and district activity -> user decides which place and time combinations warrant further local review.
2. **Resource-context review:** User selects transit, domestic-violence, homeless-victim, or street/sidewalk/parking context -> dashboard shows transparent counts and shares for the filtered records -> user decides which non-enforcement service partners or evidence sources should be consulted.
3. **District review queue:** User filters the current NIBRS data and selects aggregated reporting districts -> dashboard shows why each district appears, its supporting counts, and the active denominator -> user adds districts to a human planning-review queue.
4. **Historical reference:** User selects a year, area, or broad legacy crime category -> dashboard shows separate 2020-2024 legacy trends -> user decides whether the current NIBRS pattern merits comparison with historical records. Current and legacy totals are never presented as one continuous series unless a validated crosswalk is added later.

## 2. MVP scope and starting view

The application opens on **Current NIBRS Review**, with all areas, all reporting districts, all days, all hours, and no context-only filter selected. A persistent banner states the source file, row grain, active denominator, and that results describe recorded offenses rather than population-adjusted risk.

### Navigation

1. **Current NIBRS Review** - primary MVP page.
2. **District Review Queue** - selected districts and their supporting evidence.
3. **Legacy Reference** - separate 2020-2024 descriptive trends.
4. **Data Notes** - definitions, cleaning rules, quality flags, limitations, and refresh information.

The first Phase 3 release may combine the first two sections on one page, but it must keep their analysis functions and state separate.

## 3. Filters and interactions

| Control | Source/derivation | Behavior |
|---|---|---|
| Dataset | Application section | Defaults to Current NIBRS. Legacy opens a separate view; datasets are never stacked. |
| Area | `Area_Name`, optionally `Area_No` | Multi-select; choices are sorted and limited to values present in the active dataset. |
| Reporting district | `Report_District_No` | Multi-select; available choices update to the chosen area(s). |
| Date range | `Date_Occurred` | Inclusive start and end dates; defaults to full available range. |
| Day | Derived `day_name` / `day_type` | Multi-select weekdays or Weekend/Weekday. |
| Hour range | Derived `occurrence_hour` | Inclusive 0-23 range. Rows with invalid/missing hours are excluded only when an hour filter is active. |
| Offense | NIBRS `NIBR Description` or `NIBR Code`; legacy `Crime_Description` or `Crime_Code` | Multi-select within the active dataset. Labels display descriptions when available. |
| Premise | `Premise_Description` | Multi-select; normalized display text from the cleaning workflow. |
| Context | NIBRS flags and premise grouping | Single-select: All, Transit, Domestic violence, Homeless victim, or Street/sidewalk/parking. Contexts are transparent filters, not risk scores. |
| Valid coordinates only | `valid_coordinates` | Affects map/coordinate-based summaries only, not headline counts or non-map charts. |

Every filter change recomputes tiles, district activity, hourly distribution, context breakdown, and queue candidates from the same filtered NIBRS rows. The interface includes **Reset filters** and a readable active-filter summary. Empty selections show a clear “No records match these filters” state rather than zeros that could be mistaken for observed values.

## 4. Metrics and visuals

### Current NIBRS Review

| Element | Question answered | Source and calculation | Relevant filters |
|---|---|---|---|
| Selected offense rows | How many offense-level records match? | Row count. Unit is an offense row; do not label it as unique cases. | All NIBRS filters |
| Unique cases | How many distinct cases are represented? | `nunique(CaseNo)`, excluding missing IDs. | All NIBRS filters |
| Reporting districts | How many districts are represented? | `nunique(Report_District_No)`, excluding missing values. | All NIBRS filters |
| Records with valid coordinates | How much of the selection can support an aggregate geographic view? | Sum of `valid_coordinates`; also display share of selected rows. | All filters; coordinate toggle does not alter denominator |
| Four resource cues | What context is visible in this selection? | Counts and shares for street/sidewalk/parking premises, `Transit-related Crime == "Yes"`, `Domestic Violence Crime == "Yes"`, and `Homeless-Victim Crime == "Yes"`. Each denominator is selected offense rows. | All NIBRS filters |
| District activity bar chart/table | Which reporting districts contain the most selected offense rows? | Group by `Report_District_No`; return offense-row count, unique cases, cue counts, and share of selection. Sort count descending, district ascending. | All NIBRS filters |
| Hourly distribution | At what hours were selected offenses recorded as occurring? | Group valid `occurrence_hour` values from 0-23 and reindex missing hours to zero. | All except hour filter remains reflected in result |
| Day-by-hour heatmap | When do selected records cluster across the week? | Count rows grouped by ordered day name and hour. Missing combinations become zero. | All NIBRS filters |
| Premise bar chart | In what settings did selected records occur? | Count rows by `Premise_Description`; display top 10 plus Other. Missing premise is labeled Unknown, not dropped silently. | All NIBRS filters |
| Review queue candidates | Why might a district warrant further human review? | One row per district with offense rows, unique cases, four cue counts, valid-coordinate count/share, active period, and filter summary. | All NIBRS filters |

Exact coordinates and street addresses are not displayed. If Phase 3 includes a map, coordinates must be aggregated to reporting district or another sufficiently broad geography.

### Legacy Reference

| Element | Question answered | Source and calculation | Relevant filters |
|---|---|---|---|
| Legacy records | How many distinct legacy reported-crime records match? | Row count and `nunique(DR_NO)` shown together. | Legacy filters |
| Monthly trend | How do legacy records vary over time? | Month-start derived from `Date_Occurred`; count rows per month and fill missing months with zero within the selected period. | Area, district, date, crime, premise |
| Area comparison | Which areas contain more legacy records in this sample/file? | Count rows by `Area_Name`; show denominator and avoid “safest/most dangerous” wording. | Legacy filters |
| Crime-category table | What descriptions appear most often? | Count by `Crime_Description`; code retained for validation. | Legacy filters |

No NIBRS-versus-legacy change percentage is calculated in the MVP because row definitions and coding systems differ.

## 5. Review-queue behavior

- Users may add or remove reporting districts from the queue; no district is added automatically.
- Each queue entry stores only the district identifier, current filter summary, aggregated metrics, and a timestamp/session label. It does not store individual rows, exact locations, or personal attributes.
- “Why shown” text is generated directly from the aggregate cue counts, for example: “18 selected offense rows; 7 street/sidewalk/parking; 2 transit-related.”
- Export produces a CSV of aggregated district rows and a plain-language limitations note.
- Sorting defaults to selected offense-row count descending, with district number ascending as the deterministic tie-breaker. The user may sort by any displayed cue.

## 6. Data contract

### Canonical inputs

- `cleaned_outputs/cleaned_LAPD_NIBRS_Offenses_Dataset.csv`
- `cleaned_outputs/cleaned_Crime_Data_from_2020_to_2024.csv`

These are produced by `Complete_LAPD_Data_Cleaning(1).ipynb`. The dashboard must not mutate them.

Required NIBRS fields for the primary MVP are `CaseNo`, `Date_Occurred`, `Time_Occurred` or `occurrence_hour`, `Area_Name`, `Report_District_No`, `Premise_Description`, `LAT`, `LON`, and `valid_coordinates`. The four cue fields are `Transit-related Crime`, `Domestic Violence Crime`, `Homeless-Victim Crime`, and `Premise_Description`. Offense labels use `NIBR Description` when present and fall back to `NIBR Code`.

Required legacy fields are `DR_NO`, `Date_Occurred`, `Area_Name`, `Report_District_No`, and `Crime_Description` or `Crime_Code`. Optional fields enrich a visual but must not prevent unrelated sections from loading.

The loader validates the minimum fields used by a requested function and raises a message naming missing columns. It parses exported dates, normalizes nullable booleans, and never treats missing flags as “Yes.”

### Important definitions

- **NIBRS unit of analysis:** one offense row. `CaseNo` may repeat and is not a duplicate-removal key.
- **Legacy unit of analysis:** one legacy reported-crime row identified by `DR_NO` in the cleaned file.
- **Selected denominator:** number of rows after current filters, before excluding invalid coordinates for geographic calculations.
- **Street/sidewalk/parking:** case-insensitive premise text containing `street`, `sidewalk`, or `parking`.
- **Weekend:** Saturday or Sunday. All other named days are weekdays.
- **Valid coordinates:** the cleaning notebook's `valid_coordinates` flag. The backend does not silently redefine it.
- Missing categories display as `Unknown` only for summaries; source data remains missing.

## 7. Architecture

| Component | Single responsibility | Input | Output |
|---|---|---|---|
| Cleaning notebook | Produce canonical clean files and quality evidence | Two source CSV files | Two cleaned CSVs plus audit files |
| Data loader | Read a cleaned CSV and restore types | File path and dataset name | DataFrame |
| Validator/enricher | Check required schema and create deterministic derived fields | DataFrame | Validated/enriched DataFrame |
| Filter engine | Apply explicit filter parameters without UI state | DataFrame plus filter object | Filtered DataFrame |
| Metric functions | Compute one reusable result each | Filtered DataFrame | Dictionary or tidy DataFrame |
| Queue builder | Create aggregate district evidence | Filtered NIBRS DataFrame | One row per district |
| UI layer (Phase 3) | Render controls and results; hold session queue | Backend outputs | Dashboard and export |

Functions do not read interface state, print results as their only output, or depend on global DataFrames. The UI calls backend functions with explicit inputs. This allows filters, charts, and exports to be tested separately.

## 8. Technical design

- Python, pandas, and a lightweight local dashboard framework such as Streamlit.
- CSV storage is appropriate for the current local MVP. Read each cleaned file once per session and cache by path and modification time in the UI layer.
- Aggregate only after filtering; cache repeated aggregate calls when the framework supports it.
- Use pandas nullable types and explicit date parsing. Do not coerce missing categories to valid flags.
- Keep dataset-specific logic in separate functions. A future crosswalk must be a versioned input with documented mappings and unmapped categories before any combined trend is enabled.
- Keep exact locations and individual-level fields out of UI tables and exports.

## 9. Build order

1. Run the cleaning notebook and confirm both canonical CSVs and audit outputs exist.
2. Load and validate the NIBRS cleaned file; create `day_name`, `day_type`, and context indicators.
3. Implement and test the pure filter function.
4. Implement headline metrics, context cues, district activity, hourly distribution, heatmap, premise summary, and queue candidates.
5. Build the Current NIBRS Review interface from those tested outputs.
6. Add session-based queue selection, removal, and aggregate CSV export.
7. Load and validate the legacy file; add separate monthly, area, and category summaries.
8. Add Data Notes, denominator labels, empty states, and quality/limitations messages.
9. Run the acceptance checks and a fresh-agent build test before submission.

## 10. Acceptance checks

1. With all filters reset, “Selected offense rows” equals the number of rows in the cleaned NIBRS CSV.
2. For every filter state, district activity counts sum to the selected row count excluding only rows with missing district; the UI reports that exclusion count.
3. The 24 hourly output rows are ordered 0-23 and their counts sum to selected rows with a valid occurrence hour.
4. Each cue count equals a direct boolean count from the same filtered rows and each share uses selected offense rows as its denominator.
5. Selecting an area limits reporting-district choices and every returned row belongs to that area selection.
6. Activating “valid coordinates only” changes only coordinate-dependent output; it does not change headline or cue denominators.
7. An empty filter result produces empty-state text, zero-row outputs with stable columns, and no division-by-zero errors.
8. Queue candidates contain one row per nonmissing reporting district, no exact coordinates or individual records, and deterministic sorting.
9. Legacy monthly output includes missing months as zeros and remains visually and analytically separate from NIBRS data.
10. Invalid paths or missing required columns raise clear, actionable errors naming the file or columns.
11. No view uses the words “risk,” “dangerous,” “safe,” or “recommended allocation” as a conclusion from raw counts.
12. A fresh coding agent can identify the inputs, backend calls, views, controls, definitions, build order, and completion checks without making a product or metric decision.

## 11. Known limitations and future work

Recorded offenses exclude unreported harm and do not account for population, foot traffic, service capacity, or exposure. Counts should not be interpreted as rates or causal evidence. The approximate Los Angeles coordinate flag is a screening rule, not boundary verification. A later version may add Census denominators, transit stops, 311/lighting requests, and provider capacity. Combined NIBRS/legacy trends require a validated, documented offense-and-premise crosswalk and explicit treatment of their different row grains.
