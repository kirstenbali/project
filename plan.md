# Data Cleaning Plan

## Scope and evidence

This plan covers the two LAPD datasets loaded by `Kirsten_DataCleaning.ipynb`:

- **LAPD NIBRS Offenses Dataset**: 471,285 rows and 31 source columns in the full-data checks. The recorded row grain is one offense record, identified by `UniqueNIBRNo`.
- **Crime Data from 2020 to 2024**: 1,004,894 rows in the project exploration notes. The notebook identifies 28 source columns; the row grain is one report, identified by `DR_NO`.

The NIBRS recommendations below use the full-data profile in `full_data_checks.txt` and `cleaning_rules.md`. The legacy source CSV is not present in the workspace, so its rules are proposed from the schema and sample checks in the notebook and `phase1_exploration.py`; run the validation checklist on the full source before finalizing them. Preserve raw files and apply rules to separate cleaned copies. Do not merge or stack these datasets until a documented, tested crime-category crosswalk exists.

## General rules

- Convert empty strings and whitespace-only values to missing values, but do not replace missing categorical, date, or count values with zero or a made-up label.
- Trim surrounding whitespace from text. Normalize internal whitespace only where it is formatting noise; do not title-case descriptions or alter official codes.
- Preserve source code fields as strings where leading zeroes or code formatting may carry meaning. Keep descriptive labels alongside their codes.
- Retain records with missing non-key fields. Remove rows only for a documented, confirmed duplicate or invalid record, and report row counts before and after each removal.
- Keep exact addresses and precise coordinates out of public dashboard outputs. Publish aggregated counts with suitable disclosure controls for small groups.

## NIBRS column rules

The profile found no exact duplicate rows, no missing `CaseNo` or `UniqueNIBRNo`, and a unique `UniqueNIBRNo` on all 471,285 rows. Repeated `CaseNo` values are expected: 90,878 rows are involved in a repeated case number. `AREA NAME` is padded in every source row. Date and count findings are listed where relevant below.

| Source column | Proposed cleaning rule |
|---|---|
| `CaseNo` | Keep as a string identifier; trim whitespace and preserve leading zeroes. Repeats are valid when offense identifiers differ. |
| `UniqueNIBRNo` | Keep as a trimmed, uppercase string identifier. Validate non-nullness and uniqueness; do not manufacture an identifier if absent. |
| `Date Rptd` | Parse to datetime using the source format; retain unparseable or absent values as missing and report failures. There are 7,416 missing values and no observed parse failures. |
| `Date OCC` | Parse to datetime and retain missing values. Add review flags for dates before 2000 and before the NIBRS cutover (2024-03-07); do not delete those records automatically. The profile found 135 dates before 2000 and 7,037 before cutover. |
| `Time OCC` | Keep the source HHMM value as an integer where valid. Validate hour 0-23 and minute 0-59; derive `occ_hour` as integer division by 100 only after validation. No missing or invalid values were found; observed range is 0-2359. |
| `AREA` | Keep as an integer code; validate against the LAPD area-code reference and consistency with `AREA NAME`. |
| `AREA NAME` | Trim surrounding whitespace and retain the official label/capitalization. All 471,285 source values were padded; trimming did not change the number of distinct areas (21). |
| `RPT Dist No` | Keep as a district identifier (nullable integer or string consistently across the pipeline); validate allowed values and relation to `AREA`. Do not infer a district from coordinates. |
| `TotalOffenseCount` | Keep as a nonnegative integer; validate values are at least 1. Observed range is 1-13 with no values below 1. |
| `Group` | Trim and preserve as a categorical source value; preserve missingness (14,220 missing). Validate against the publisher's code list. |
| `NIBR Code` | Preserve as a trimmed string code, including any leading zeroes; preserve missingness (557 missing) and validate against the NIBRS code list. |
| `NIBR Description` | Trim whitespace and preserve the source description; do not infer a description where missing. |
| `Crime Against` | Trim and preserve as a categorical value; retain missingness (1,699 missing) and check values against the codebook. |
| `Premise Cd` | Preserve as a trimmed string code to retain formatting and leading zeroes; map blanks to missing. Missing in 21,999 rows. |
| `Premise Desc` | Trim and preserve the official label; keep missing values (48 observed) and validate code/description pairs when both are present. |
| `Weapon Used Cd` | Preserve as a string code; keep missing values as missing, not as a fabricated "no weapon" category. Missing in 332,339 rows (70.52%). |
| `Weapon Desc` | Trim and preserve the source label; keep missing values and check consistency with `Weapon Used Cd`. Missing in 332,339 rows (70.52%). |
| `Status` | Convert to nullable integer; preserve missingness (472 rows) and validate code values against the status reference. |
| `Status Desc` | Trim and preserve the source label; preserve missingness (470 rows). Check code/description agreement and investigate the two-row missingness difference without filling it automatically. |
| `TotalVictimCount` | Keep as a nonnegative integer; observed range is 0-44 with no negative values. Do not replace zero with missing. |
| `Victim Shot` | Standardize only recognized yes/no spellings to `Yes`/`No`; map blanks to missing and flag any unrecognized value. Keep as a category or nullable boolean with a separate missing state. |
| `Domestic Violence Crime` | Apply the same yes/no normalization and validation as `Victim Shot`; preserve missingness if present. |
| `Hate Crime` | Apply the same yes/no normalization and validation as `Victim Shot`; preserve missingness if present. |
| `Gang-related Crime` | Apply the same yes/no normalization and validation as `Victim Shot`; preserve missingness if present. |
| `Transit-related Crime` | Apply the same yes/no normalization and validation as `Victim Shot`; preserve missingness if present. |
| `Homeless-Victim Crime` | Apply the same yes/no normalization and validation as `Victim Shot`; preserve missingness if present. |
| `Homeless-Suspect Crime` | Apply the same yes/no normalization and validation as `Victim Shot`; preserve missingness if present. |
| `Homeless-Arrestee Crime` | Apply the same yes/no normalization and validation as `Victim Shot`; preserve missingness if present. |
| `LOCATION` | Trim and collapse repeated whitespace without changing address text. Retain only in a restricted analytical copy; omit from public dashboard extracts and avoid publishing exact incident locations. |
| `LAT` | Keep as nullable numeric. Mark zero, missing, non-finite, and out-of-area values invalid for mapping; do not drop their offense records. The profile found 132 missing coordinate pairs and 547 `(0, 0)` pairs. |
| `LON` | Apply the same coordinate checks as `LAT`; validate as a paired coordinate, not independently. Add a `coordinate_valid` flag; 679 rows were unavailable or unusable in the profile. |

## Legacy 2020-2024 column rules

The legacy CSV is not available for full-data inspection in this workspace. These rules are provisional and should be confirmed with full-data counts, valid-value lists, and parser-failure checks. The notebook/exploration notes report 1,004,894 rows, unique `DR_NO` values in a 4,000-row sample, occurrence years 2020-2024, and 7 absent `LAT`/`LON` pairs in that sample.

| Source column | Proposed cleaning rule |
|---|---|
| `DR_NO` | Preserve as a string incident identifier, retaining leading zeroes. Check missingness and uniqueness over the full file; do not use as a numeric measure. |
| `Date Rptd` | Parse to datetime with the actual source format, then validate failures and plausible date range. Retain missing values; do not split into date/time components unless both are needed downstream. |
| `DATE OCC` | Parse to datetime with the actual source format and validate against `Date Rptd`; retain missing values and flag occurrence dates after report dates or outside the dataset period for review. |
| `TIME OCC` | Validate as HHMM (hour 0-23, minute 0-59); preserve the source value and derive an integer hour only after validation. |
| `AREA` | Keep as a nullable integer area code; check against the LAPD reference and `AREA NAME`. |
| `AREA NAME` | Trim surrounding whitespace and preserve the official label; validate area-code/name consistency. |
| `Rpt Dist No` | Keep as a district identifier; use a consistent nullable integer or string type and validate values and area relationships. |
| `Part 1-2` | Keep as a nullable categorical/code field; validate its observed categories against the source definition. Do not treat it as a count. |
| `Crm Cd` | Preserve as a string crime code; validate against the LAPD code list and keep separate from its description. |
| `Crm Cd Desc` | Trim and preserve the source label; check consistency with `Crm Cd` and do not rewrite labels without an approved mapping. |
| `Mocodes` | Preserve as a string of multiple codes. Normalize whitespace around delimiters only; do not treat the whole field as one category or silently discard unknown codes. Split to a child/bridge table only if analysis needs one row per code. |
| `Vict Age` | Convert valid values to nullable integer. Profile negative and out-of-range values; preserve documented unknown/unspecified codes such as zero rather than treating them as a real age without checking the data dictionary. |
| `Vict Sex` | Trim and preserve source categories. Normalize only documented equivalent spellings; keep unknown or missing distinct and consult the source codebook before recoding. Treat as sensitive. |
| `Vict Descent` | Preserve source codes as strings and keep missing/unknown distinct. Apply labels only from an approved LAPD reference; treat as sensitive and avoid unnecessary dashboard breakdowns. |
| `Premis Cd` | Preserve as a string code, including leading zeroes; keep missing values and validate against `Premis Desc`. |
| `Premis Desc` | Trim and preserve source label; do not infer missing labels from loosely matching text. Check code/description pairs. |
| `Weapon Used Cd` | Preserve as a string code; retain missingness and distinguish "not recorded" from any explicit no-weapon code. |
| `Weapon Desc` | Trim and preserve source label; retain missingness and validate against `Weapon Used Cd`. |
| `Status` | Preserve as a trimmed string/code (or nullable integer only after confirming codes are numeric and formatting is immaterial); validate against the source reference. |
| `Status Desc` | Trim and preserve label; check consistency with `Status` and retain missing values. |
| `Crm Cd 1` | Preserve as a nullable string crime code; validate against the code list. Treat as an associated classification, not an additional report row. |
| `Crm Cd 2` | Preserve as a nullable string crime code; the project exploration notes confirm this field is populated on some records. Do not count it as another incident or drop the row when it is missing. |
| `Crm Cd 3` | Preserve as a nullable string crime code; do not count it as another incident or infer a value. |
| `Crm Cd 4` | Preserve as a nullable string crime code; do not count it as another incident or infer a value. |
| `LOCATION` | Trim/collapse formatting whitespace without altering the address. Restrict access and exclude exact addresses from dashboard outputs. |
| `Cross Street` | Convert blanks to missing and trim surrounding/repeated whitespace. Keep separate from `LOCATION`; do not geocode or infer a cross street during cleaning. |
| `LAT` | Keep as nullable numeric; flag zero, missing, non-finite, or out-of-area coordinates as unusable for mapping. Preserve the report row and validate with `LON`. |
| `LON` | Keep as nullable numeric and validate as a coordinate pair with `LAT`; do not use `(0, 0)` as a real location. Keep the report row if coordinates are invalid. |

## Derived dashboard fields

- Derive occurrence date, hour, day of week, and analysis time block from validated occurrence date/time fields. Keep source date/time columns for traceability.
- Count NIBRS offense rows by `UniqueNIBRNo`; count legacy reports by `DR_NO`. Do not count `CaseNo` or secondary `Crm Cd 1`-`Crm Cd 4` values as separate rows without explicitly defining a different metric.
- Keep datasets separate in storage and analysis. Their row grains, schemas, and coverage differ; the NIBRS source has a cutover in March 2024, while the legacy source covers 2020-2024.
- For maps, filter to `coordinate_valid` rows. For non-map tables and charts, retain records with invalid coordinates.
- Use aggregated area, district, and time-block outputs for dashboards. Review small-cell disclosure risk and suppress or combine counts according to the project's reporting policy.

## Required validation before publishing

1. Record source filename, retrieval date, row count, column count, and data types; retain an untouched raw copy.
2. Profile missing and blank values, distinct categories, numeric ranges, date ranges, and parse failures for every source column.
3. Check identifier missingness/uniqueness and exact duplicate rows. Validate expected repeated case/report relationships without removing them automatically.
4. Validate code/description pairs, yes/no categories, time formats, count ranges, date ordering, and coordinate bounds against the publisher's documentation.
5. Confirm cleaned row counts and document every excluded row. Add before/after examples for each transformation and run record-level spot checks.
6. Reconcile dashboard totals to the declared row grain and verify that missing values have not been counted as zero or silently discarded.