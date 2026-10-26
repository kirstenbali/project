# Change requests - Module 9 audit

This audit applies to https://github.com/kirstenbali/project at app commit
`53645eff24eb73d9c80159f68bf03104fbeb8058`. Yunbo Jia, Steven Eum, Kirsten Bali's claim and request are recorded here
for team review and coordination.

## Claims

| Auditor | Feature | Number | Distinct evidence |
|---|---|---|---|
| Yunbo Jia | Valid coordinates only checkbox | Valid-coordinate coverage | Four invented rows, two with valid coordinates; actual Streamlit widget test and direct denominator calculation |
| Steven Y Eum (AI-assisted evidence; auditor review pending) | Reset filters | Unique cases | Six distinct invented offense rows with repeated/missing case IDs; real Reset widget interaction and independent Python loop/set count |
| Kirsten Bali | Time-of-day block multiselect | Hourly-distribution offense-row total | Four invented rows, one per block; Morning + Evening selection and independent membership count |
| Vicky Huang | Time-of-day block multiselect: Overnight + Evening | Selected offense rows | Three live UI checks, a four-row example, and an independent recount of the supplied raw NIBRS CSV; adds full-data count evidence to the filtering issue in CR-002 |

The Time-of-day block filter and Selected offense rows for Overnight + Evening are excluded from this claim because a teammate selected that topic.

## YJ09-03 - Keep geographic validity out of non-map denominators

- Status: Open; reproduced on the recorded commit.
- Requirement: `BUILD_SPEC.md` sections 3, 4 and 6 and acceptance check 6 say the coordinate toggle affects coordinate-dependent output only.
- Evidence: `dashboard.py:186-201`, `dashboard.py:221-237`, and `backend_analysis.py:282-284`, plus the four-row fixture and observed values recorded below.
- User action: leave the four-row fixture at default filters, then enable `Valid coordinates only`.
- Expected: headline remains 4 selected rows and coverage remains 2/4 = 50%; only geographic output may use the two-row subset.
- Actual: headline falls to 2 and coverage becomes 2/2 = 100%.
- Impact: the displayed coverage is 50 percentage points too high on this fixture and hides the two selected rows without valid coordinates.
- Cause: the checkbox filters the common frame before all headline and cue calculations.
- Requested change: retain the ordinary filtered table for headline, cue, and non-map denominators; derive a separate valid-coordinate subset only for geographic calculations.
- Acceptance: toggling this control leaves every non-geographic metric unchanged while coordinate-dependent output uses only valid rows.

## Reproduction and scope

The controlled fixture has four distinct offense rows with all ordinary filters equal. Their
`valid_coordinates` values are `True, False, True, False`. With the checkbox off, the UI shows
4 selected rows and `2 (50.0%)` coverage. With it on, the UI shows 2 selected rows and
`2 (100.0%)` coverage. The test substituted this invented fixture at the data-loader boundary
and exercised the real dashboard through Streamlit AppTest; it did not edit application source
or create fake production CSVs. The five supplied backend tests pass, but do not cover this UI
failure. Neither production input CSV is committed here, so production numbers and a deployed
app were not verified. This is a requested change, not a fix applied to the team's code.

## SE09-01 - Reset filters does not restore the Area selection

- Status: Open; reproduced by Codex at Steven's request. Steven's review of the evidence and conclusions is pending.
- Version: repository `8c2ea0d70359163ddfb4feb225740740ef52824a`; unchanged app source from `53645eff24eb73d9c80159f68bf03104fbeb8058`.
- Requirement: BUILD_SPEC.md section 3 requires Reset filters; section 2 describes the initial all-area selection.
- Reproducer: `audit_check_steven.py`. It injects six synthetic rows at `backend_analysis.load_clean_data` and runs the actual unchanged dashboard through Streamlit AppTest. No production CSV is created or modified.
- Fixture: three Central rows with CaseNo A, A, B; three West LA rows with C, C, missing. Each has a distinct synthetic offense ID, date 2026-10-19, time 09:00, STREET premise, TEST OFFENSE description, valid coordinates True and all three context flags No.
- Steps: start at defaults; choose Central only; click Reset filters.
- Expected after reset: Area = Central and West LA, selected offense rows = 6, Unique cases = 3.
- Actual: Area remains Central, selected offense rows = 3, Unique cases = 2. No application exception occurs.
- Cause: `dashboard.py:181-183` deletes the derived `nibrs_filter_spec` and reruns, but does not reset widget state. The retained Area widget (`dashboard.py:162`) constructs a new narrowed spec at lines 186-203.
- Impact: a planner can believe the full dataset is restored while still viewing a narrowed selection.
- Requested change: give filter widgets explicit state keys and reset their state through a callback before recomputing the spec. Restore all documented defaults.
- Acceptance: the six-row example restores both areas and 6/3 headline counts after reset; additionally verify date, district, day, time, offense, premise, context and coordinate controls and the filter-summary text.
- Scope: Area reset was directly tested; the other controls listed in acceptance remain untested. Full input data and deployment were not available. This request does not apply a fix.

## SE09-02 - Unique cases controlled check passes

- Status: Evidence recorded by Codex for Steven; auditor review pending. No metric arithmetic change requested.
- Definition: count distinct nonmissing CaseNo identifiers in the active NIBRS selection, as BUILD_SPEC.md section 4 specifies. Unit is identified cases; no denominator applies.
- Code: `backend_analysis.py:362-375`, specifically `int(frame["CaseNo"].nunique(dropna=True))` at line 370. UI filters the table at `dashboard.py:221` and displays this metric at line 231.
- Expected / actual backend results: all six rows 3/3; Central 2/2; West LA 1/1; empty 0/0. Removing the missing-ID row leaves 3 cases. The real AppTest headline shows 3 initially and 2 for Central.
- Independent method: a Python loop excludes missing IDs and inserts remaining CaseNo values into a set; its size is compared against the real backend result.
- Interpretation: repeated offense rows for A and C must not be counted as additional identified cases. The missing ID contributes no identified case. The reset bug affects which selection remains active, not the distinct-count formula.
- Reproduce: run `python audit_check_steven.py`; output is also saved in `steven-audit-evidence.json`. The `reset_matches_expected: false` observation records SE09-01.
- Environment: Python 3.12.14, pandas 3.1.0, Streamlit 1.66.1, matplotlib 3.11.2, pytest 9.1.1. The supplied backend test suite passes all five tests. Application requirements are unpinned.
- Limits: synthetic fixture only; absent production inputs, real case-ID uniqueness across years, alternate missing-value strings, all filter combinations and a live deployment were not verified. The empty case tests the backend; the UI uses its no-records warning.


## CR-002 — Preserve noncontiguous time-block selections

### Finding

The dashboard's `_time_block_hours` helper reduces selected blocks to the earliest start and latest end. Choosing Morning and Evening becomes 06:00-23:00, silently including Afternoon. In the four-row fixture, the hourly-distribution total is 3 instead of 2.

### Requirement

The time controls should include the periods planners explicitly select, and every chart should use the same accurately filtered rows. A multiselect should not silently include an unselected category.

### Requested change

1. Preserve selected block names in filter state.
2. Filter by membership in the union of selected blocks, not one minimum-to-maximum range.
3. Alternatively, replace the multiselect with a continuous hour-range control.
4. Make the filter summary list selected block names.
5. Add a regression test in which Morning plus Evening excludes a 14:00 row.

### Acceptance evidence

For `audit_check.py`, Morning plus Evening should include only hours 8 and 20. The 24-bin hourly distribution should sum to 2, with the 14:00 bin equal to zero.

### Scope and limitations

This request changes time-filter behavior only. It does not change the block definitions or hourly-distribution calculation.


## CR-VH-01 — Overnight + Evening includes unselected daytime records

- **Author:** Vicky Huang
- **Status:** Open; reproduced with AI-assisted checks. No application fix applied.
- **App version checked:** `53645eff24eb73d9c80159f68bf03104fbeb8058`
- **Related request:** CR-002. This entry adds evidence for a different block combination and the Selected offense rows metric, rather than claiming a separate root cause.

### Expected behavior

Selecting Overnight (hours 0–5) and Evening (hours 18–23) should exclude Morning and Afternoon. Because the selected periods do not overlap, their combined row count should equal their individual counts added together.

### Steps and results

Keep all areas and days selected, with no district, offense, premise, or context restriction. Leave Valid coordinates only unchecked. Use the supplied raw NIBRS CSV through the existing loader, with the file-derived date range of 1800-01-06 through 2026-08-22 inclusive. Change only the selected time blocks.

| Selection | Expected rows | Actual rows |
|---|---:|---:|
| Overnight only | 82,267 | 82,267 |
| Evening only | 140,716 | 140,716 |
| Overnight + Evening | 222,983 | 471,285 |

The excess is **248,302 rows**, exactly equal to Morning (100,213) plus Afternoon (148,089).

A four-row example at 01:00, 08:00, 14:00, and 20:00 also reproduces the issue: Overnight + Evening should return 2 rows but returns 4.

### Evidence and cause

`dashboard.py:104–116`, `_time_block_hours()`, takes the minimum start and maximum end, converting this selection into hours 0–23. `backend_analysis.py:274–277` applies that continuous interval. The headline metric then counts the incorrectly selected rows.

An independent standard-library CSV recount confirms the expected 222,983 rows without using the app’s filtering or metric functions. Supporting files are in `audit-evidence/`: `audit_check.py`, `audit-results.json`, and the Overnight, Evening, and combined filter/result screenshots.

### Requested change and verification

Preserve the union of selected hours and show those selections accurately in the filter summary, consistent with CR-002.

Verification should return:

- 2 rows for the four-row Overnight + Evening example.
- 222,983 rows for the recorded full-file selection.
- No records from hours 6–17 in that combined selection.

### Scope and limitations

These checks used the supplied raw CSV through the existing loader; the complete cleaning notebook was not run. The unusual default year 1800 was not validated. The results establish this filtering defect at the recorded version, not the accuracy of the source data or totals from a different cleaned dataset.

AI assisted with UI operations, code inspection, verification scripts, and evidence capture.
