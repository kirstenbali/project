"""
Phase 1 exploration - Community Safety Resource Planner (DSO 576)
Team: Kirsten Bali, Iyanna Blackburn, Vicky Huang, Yunbo Jia, Steven Eum

Reproduces every number in the Phase 1 PDF from the two raw CSVs using a
fixed random seed. Run it from the folder that contains the two CSV files:

    python phase1_exploration.py

The CSVs are NOT committed to the repo (see .gitignore). Download them from
data.lacity.org (LAPD NIBRS Offenses Dataset; Crime Data 2020 to 2024).

Expected values from the seed-42 sample are written in the comments next to
each print so anyone can check the output against the PDF.
"""

from pathlib import Path

import pandas as pd

SEED = 42
N = 4000
BASE_DIR = Path(__file__).resolve().parent
NIBRS_FILE = BASE_DIR / "LAPD_NIBRS_Offenses_Dataset.csv"
LEGACY_FILE = BASE_DIR / "Crime_Data_from_2020_to_2024.csv"

# "street, sidewalk or parking" as used on the dashboard sketch
OUTDOOR = [
    "Street/Parkway",
    "Sidewalk",
    "Highway / Road / Alley / Street",
    "Parking Lot / Garage / Drop Lot",
    "Parking underground/building",
]


def parse_dates(series, fmt):
    """Parse with the expected format; if that fails for every row, let pandas infer."""
    out = pd.to_datetime(series, format=fmt, errors="coerce")
    if out.isna().all():
        out = pd.to_datetime(series, errors="coerce")
    return out


def section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


# --------------------------------------------------------------------------
section("1. Load the two full files")
# --------------------------------------------------------------------------
nibrs = pd.read_csv(NIBRS_FILE, low_memory=False)
legacy = pd.read_csv(LEGACY_FILE, low_memory=False)

print("NIBRS full file rows: ", len(nibrs))    # expected 471,285
print("Legacy full file rows:", len(legacy))   # expected 1,004,894

print("\nNIBRS columns:")
print(list(nibrs.columns))
print("\nLegacy columns:")
print(list(legacy.columns))

# --------------------------------------------------------------------------
section("2. Data-quality finding: AREA NAME is space-padded in the NIBRS file")
# --------------------------------------------------------------------------
print("NIBRS AREA NAME string lengths:", nibrs["AREA NAME"].dropna().str.len().value_counts().to_dict())
print("Rows equal to 'Central' BEFORE .str.strip():", (nibrs["AREA NAME"] == "Central").sum())   # expected 0

nibrs["AREA NAME"] = nibrs["AREA NAME"].str.strip()

print("Rows equal to 'Central' AFTER  .str.strip():", (nibrs["AREA NAME"] == "Central").sum())   # expected > 0
print("Legacy AREA NAME string lengths:", legacy["AREA NAME"].dropna().str.len().value_counts().to_dict())
print("(legacy names are not padded, so no strip needed there)")

# --------------------------------------------------------------------------
section("3. Draw the fixed-seed samples used in the PDF")
# --------------------------------------------------------------------------
ns = nibrs.sample(n=N, random_state=SEED).copy()    # NIBRS sample
ls = legacy.sample(n=N, random_state=SEED).copy()   # legacy sample
print(f"Sampled {N} rows from each file with random_state={SEED}")

# --------------------------------------------------------------------------
section("4. NIBRS sample: numbers in 'Source and Scope' and 'Small pandas exploration'")
# --------------------------------------------------------------------------
print("NIBRS sample rows:            ", len(ns))                                          # 4,000
print("Distinct CaseNo:              ", ns["CaseNo"].nunique())                             # 3,997
print("Distinct AREA NAME:           ", ns["AREA NAME"].nunique())                          # 21
print("Valid nonzero LAT/LON pairs:  ", ((ns["LAT"] != 0) & (ns["LON"] != 0)).sum())       # 3,997
print("Transit-related Crime == Yes: ", (ns["Transit-related Crime"] == "Yes").sum())      # 121
print("Domestic Violence Crime == Yes:", (ns["Domestic Violence Crime"] == "Yes").sum())   # 369
print("Homeless-Victim Crime == Yes: ", (ns["Homeless-Victim Crime"] == "Yes").sum())      # 96
print("Victim Shot == Yes:           ", (ns["Victim Shot"] == "Yes").sum())                # 19

ns["occ_dt"] = parse_dates(ns["Date OCC"], "%Y %b %d %I:%M:%S %p")
print("Unparsed Date OCC in sample:  ", ns["occ_dt"].isna().sum())                        # should be 0
print("NIBRS sample date range:      ", ns["occ_dt"].min(), "to", ns["occ_dt"].max())

full_dt = parse_dates(nibrs["Date OCC"], "%Y %b %d %I:%M:%S %p")
print("NIBRS full-file date range:   ", full_dt.min(), "to", full_dt.max())
print("NIBRS offense rows by occurrence year:", {int(y): int(c) for y, c in full_dt.dt.year.value_counts().sort_index().tail(6).items()})
print("Rows occurring before the 2024-03-07 NIBRS cutover (reported later):", int((full_dt < "2024-03-07").sum()), "of", len(full_dt))
# Occurrence dates run back to 1800 because a few rows carry old or placeholder dates;
# the file itself covers offenses reported from the March 2024 NIBRS switch through Aug 2026.

# --------------------------------------------------------------------------
section("5. Legacy sample: numbers in 'Source and Scope'")
# --------------------------------------------------------------------------
print("Legacy sample rows:           ", len(ls))                                          # 4,000
print("Distinct DR_NO:               ", ls["DR_NO"].nunique())                             # 4,000
print("Distinct AREA NAME:           ", ls["AREA NAME"].nunique())                         # 21
print("Valid nonzero LAT/LON pairs:  ", ((ls["LAT"] != 0) & (ls["LON"] != 0)).sum())      # 3,993

ls["occ_dt"] = parse_dates(ls["DATE OCC"], "%Y %b %d %I:%M:%S %p")   # same format as NIBRS
print("Unparsed DATE OCC in sample:  ", ls["occ_dt"].isna().sum())                        # should be 0
print("Legacy occurrence years:      ", sorted(int(y) for y in ls["occ_dt"].dt.year.dropna().unique()))  # 2020..2024
print("Legacy rows with a 2nd crime code (Crm Cd 2):", ls["Crm Cd 2"].notna().sum())

# --------------------------------------------------------------------------
section("6. Dashboard sketch selection: Central, Fri-Sun, 8 PM to 11:59 PM")
# --------------------------------------------------------------------------
ns["dow"] = ns["occ_dt"].dt.dayofweek                     # Monday=0 ... Friday=4, Saturday=5, Sunday=6
ns["hour"] = (ns["Time OCC"] // 100).astype("Int64")      # HHMM integer -> hour of day

sel = ns[
    (ns["AREA NAME"] == "Central")
    & (ns["dow"].isin([4, 5, 6]))
    & (ns["hour"].between(20, 23))
]

print("Selection rows (offense rows tile):", len(sel))                                    # 29
print("Distinct CaseNo in selection:      ", sel["CaseNo"].nunique())                     # 29
print("Street/sidewalk/parking rows:      ", sel["Premise Desc"].isin(OUTDOOR).sum())      # 16
print("Transit-related == Yes:            ", (sel["Transit-related Crime"] == "Yes").sum())     # 1
print("Domestic Violence == Yes:          ", (sel["Domestic Violence Crime"] == "Yes").sum())   # 1
print("Homeless-Victim == Yes:            ", (sel["Homeless-Victim Crime"] == "Yes").sum())     # 1

print("\nRows per hour (hourly chart):")
print({int(h): int(c) for h, c in sel.groupby("hour").size().items()})                                               # {20: 7, 21: 7, 22: 11, 23: 4}

print("\nRows per reporting district (district chips):")
print(sel.groupby("RPT Dist No").size().sort_values(ascending=False).to_string())
# expected: 185 -> 3; 111, 135, 138, 161, 162, 182 -> 2 each; 14 other districts -> 1 each

print("\nPremise Desc counts in selection (supports the 'Lighting review' line):")
print(sel["Premise Desc"].value_counts().to_string())

print("\nPremise of the transit-related row (shown on the 'Transit support' line):")
print(sel.loc[sel["Transit-related Crime"] == "Yes", "Premise Desc"].tolist())

print("\nDone. Compare each value above with the expected numbers in the comments and with the PDF.")
