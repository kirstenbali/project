# Change requests - Module 9 audit

This audit applies to https://github.com/kirstenbali/project at app commit
`53645eff24eb73d9c80159f68bf03104fbeb8058`. Yunbo Jia's claim and request are recorded here
for team review and coordination.

## Claims

| Auditor | Feature | Number | Distinct evidence |
|---|---|---|---|
| Yunbo Jia | Valid coordinates only checkbox | Valid-coordinate coverage | Four invented rows, two with valid coordinates; actual Streamlit widget test and direct denominator calculation |
| Steven Y Eum (AI-assisted evidence; auditor review pending) | Reset filters | Unique cases | Six distinct invented offense rows with repeated/missing case IDs; real Reset widget interaction and independent Python loop/set count |
| Kirsten Bali | Valid coordinates only control | Selected offense rows and cue-share denominator | Four-row synthetic NIBRS fixture comparing toggle off versus on |

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


## CR-001 — Keep coordinate filtering out of shared headline denominators

### Finding

`apply_filters` removes rows with invalid coordinates when `valid_coordinates_only=True`. The dashboard creates one shared `nibrs_filtered` DataFrame and passes it to headline tiles, cues, time charts, district activity, premise summary, and the review queue. It also carries the checkbox into the Legacy Reference filter. In the reproducible fixture, the control changes selected offense rows from 4 to 2 and changes the transit cue share from 25% to 50%.

### Requirement

The build specification states that **Valid coordinates only** affects map/coordinate-based summaries only. It must not alter headline counts, non-map charts, or cue denominators. Acceptance check 6 requires the same behavior.

### Requested change

1. Remove `valid_coordinates_only` from the general-purpose row filtering path, or return separate base and coordinate-only frames.
2. Apply the coordinate mask only where a geographic component is calculated.
3. Keep `nibrs_headline_metrics` and `context_cues` on the base filtered frame.
4. Add a regression test using `audit_check.py` (or an equivalent unit test) that asserts the toggle does not change `selected_offense_rows`, `unique_cases`, or cue shares.
5. In the UI, describe the control as applying only to geographic output.

### Acceptance evidence

For the four-row fixture in `audit_check.py`, enabling the coordinate option should leave selected offense rows at 4, unique cases at 3, and transit share at 0.25, while a coordinate-dependent result uses the 2 valid-coordinate rows.

### Scope and limitations

This request changes data routing, not the definition of `valid_coordinates`. It does not authorize displaying exact coordinates or individual records.
