# Change requests - Module 9 audit

This audit applies to https://github.com/kirstenbali/project at app commit
`53645eff24eb73d9c80159f68bf03104fbeb8058`. Yunbo Jia's claim and request are recorded here
for team review and coordination.

## Claims

| Auditor | Feature | Number | Distinct evidence |
|---|---|---|---|
| Yunbo Jia | Valid coordinates only checkbox | Valid-coordinate coverage | Four invented rows, two with valid coordinates; actual Streamlit widget test and direct denominator calculation |

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
