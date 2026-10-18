# Community Safety Resource Planner

This repository contains the Module 5 data-cleaning workflow for the Halo
team's DSO 576 project.

## Project question

Which Los Angeles neighborhoods, reporting districts, and time blocks should
be reviewed for additional non-enforcement safety resources such as outreach,
lighting review, transit support, victim services, or late-night service
capacity?

The project uses recorded-offense counts as descriptive evidence for human
planning review. It does not recommend enforcement, predict individual
behavior, or claim that recorded counts measure all harm.

## Data source

**Dataset:** LAPD NIBRS Offenses Dataset
**Publisher:** Los Angeles Police Department
**Source:** https://data.lacity.org/Public-Safety/LAPD-NIBRS-Offenses-Dataset/k7nn-b2ep/about_data
**Analysis/retrieval record date:** September 28, 2026
**Source filename:** `LAPD_NIBRS_Offenses_Dataset.csv`
**Rows used in this run:** 471,285
**Columns in the original file:** 31

The large source and full cleaned CSV files are intentionally excluded from
Git. Download the original CSV from the source page and place it in the
repository root with this exact filename:

```text
LAPD_NIBRS_Offenses_Dataset.csv
```

The legacy 2020–2024 crime dataset is not merged with the NIBRS data. Its
crime-code and premise categories require a validated crosswalk before the two
schemas can be compared.

## Environment setup

From the repository folder, create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run the cleaning script

```bash
source .venv/bin/activate
python clean_nibrs.py
```

To reproduce and save the full validation output:

```bash
python clean_nibrs.py | tee full_data_checks.txt
```

## Run the notebook

Open `homework5_cleaning.ipynb` in VS Code and select the
`DSO576 Project (.venv)` Kernel. Then:

1. Click `Restart`.
2. Click `Run All`.
3. Confirm that no cell reports an error.
4. Confirm that all five record checks pass.
5. Save the notebook with outputs visible.

## Expected outputs

| File | Purpose | Git status |
|---|---|---|
| `LAPD_NIBRS_Offenses_Cleaned.csv` | Full cleaned dataset | Ignored because of size |
| `nibrs_clean_sample.csv` | 50-row safe inspection sample | Included |
| `five_record_checks.csv` | Five original-to-cleaned checks | Included |
| `full_data_checks.txt` | Full-data validation evidence | Included |
| `homework5_report.md` | Completed 14-item report | Included |

The safe sample omits exact `LOCATION`, `LAT`, and `LON` values. All checks are
performed on the complete dataset, not only on the sample.

## Cleaning decisions

The proposed rules were documented before cleaning in `cleaning_rules.md`.
The workflow:

- preserves the original DataFrame and cleans a separate copy;
- trims surrounding whitespace from text fields;
- converts report and occurrence dates to datetime values;
- converts `Status` to nullable integer;
- derives `occ_hour` from HHMM occurrence time;
- flags occurrence dates before 2000 and before the NIBRS cutover;
- flags unavailable or unusable coordinates without deleting the offense row;
- retains repeated `CaseNo` values when they have separate offense IDs;
- preserves missing values instead of replacing them with zero.

## Reproducibility result

A fresh Kernel restart followed by `Run All` recreated the outputs from the
original CSV. The run started and ended with 471,285 rows, retained unique
`UniqueNIBRNo` values, and passed all five individual record checks.

## Repository files

| File | Description |
|---|---|
| `clean_nibrs.py` | Full inspection, cleaning, validation, and output workflow |
| `homework5_cleaning.ipynb` | Reproducible notebook and displayed evidence |
| `cleaning_rules.md` | Proposed rules written before cleaning |
| `homework5_report.md` | Completed Homework 5 checklist and explanations |
| `full_data_checks.txt` | Results from checks on all 471,285 rows |
| `nibrs_clean_sample.csv` | Safe 50-row sample containing difficult cases |
| `five_record_checks.csv` | Five record-level validation checks |
| `requirements.txt` | Python dependencies |
| `phase1_exploration.py` | Earlier Phase 1 project exploration |

## Limitations

Recorded offenses do not include unreported harm, population exposure,
resource availability, or program impact. The results are descriptive and
should not be interpreted as causal evidence or neighborhood danger scores.
