# Vicky Huang: supporting evidence for CR-VH-01

Audited app commit: `53645eff24eb73d9c80159f68bf03104fbeb8058`. Checks were performed October 23, 2026 with AI assistance.

This evidence supplements CR-002 with Overnight + Evening and the Selected offense rows metric. The app was not repaired or changed by this audit.

## Reproduce

From the team app folder, using an environment with the project dependencies:

```bash
python -B audit-evidence/audit_check.py --project . --out audit-results-vicky-recheck.json
```

The full-data check also requires the exact user-supplied raw `LAPD_NIBRS_Offenses_Dataset.csv` in the app folder, or its path passed with `--csv`. That CSV is not uploaded here. The recorded input SHA-256 is `351d664ef395fd23682ec259d86b2aeeab747d9ff428bd74d71e2d310ba0cae6`. Check the original app commit and input hash to reproduce the recorded counts.

The checker runs the five existing backend checks, extracts the original pure dashboard helper without running the UI, tests a synthetic four-row example and boundaries, compares full-data backend counts, and independently counts raw CSV hours with the standard library. Assertions verify the original failure; a successful check does not mean the app has been fixed. An unavailable input or changed app can prevent the recorded results from reproducing.

## Results

| Selection | Expected rows | Observed UI/backend rows |
|---|---:|---:|
| Overnight | 82,267 | 82,267 |
| Evening | 140,716 | 140,716 |
| Overnight + Evening | 222,983 | 471,285 |

The extra 248,302 rows equal Morning (100,213) plus Afternoon (148,089).

- `*-filter.png` and `*-result.png`: paired UI screenshots for each selection.
- `audit-results.json`: aggregate counts, synthetic fixtures, boundary checks, original test results, source hashes, and exact filter settings.
- `environment.txt`: Python and installed package versions for this run.

All areas/days were selected; district, offense, premise, and context were unrestricted; coordinate-only was unchecked. The inclusive file-derived dates were 1800-01-06 through 2026-08-22. These are raw-input checks through the existing adapter. The full cleaning notebook and the unusual earliest date were not validated. No raw records, exact locations, or individual homework report are included.
