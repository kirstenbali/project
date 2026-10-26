"""Reproduce the time-block audit without modifying the team app or source CSV.

Run with the team's environment:
  .venv/bin/python /path/to/audit_check.py --project /path/to/project --out results.json
Only aggregate counts, synthetic fixtures, and file hashes are exported.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import importlib
import json
import sys
from collections import Counter
from datetime import datetime
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from pathlib import Path


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def extract_helper(path):
    # Extract only this pure function; importing dashboard.py would run its UI.
    tree = ast.parse(path.read_text())
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                and n.name == "_time_block_hours")
    namespace = {}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), namespace)
    return namespace["_time_block_hours"]


def independent_hour(value):
    # Separate standard-library implementation, not the app's pandas conversion.
    try:
        numeric = Decimal(value.strip())
        if not numeric.is_finite() or numeric != numeric.to_integral_value():
            return None
        hhmm = int(numeric)
    except (InvalidOperation, ValueError, AttributeError):
        return None
    if hhmm < 0 or hhmm > 2359 or hhmm % 100 > 59:
        return None
    return hhmm // 100


@lru_cache(maxsize=100000)
def independent_date(value):
    try:
        return datetime.strptime(value.strip(), "%Y %b %d %I:%M:%S %p")
    except (ValueError, AttributeError):
        return None


def independent_csv_counts(path, areas, start, end_exclusive):
    counts, diagnostics = Counter(), Counter()
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            diagnostics["csv_rows"] += 1
            if None in row:
                diagnostics["extra_field_rows"] += 1
                continue
            area = (row.get("AREA NAME") or "").strip().lower()
            if area not in areas:
                diagnostics["excluded_area"] += 1
                continue
            occurred = independent_date(row.get("Date OCC"))
            if occurred is None:
                diagnostics["unparsed_dates"] += 1
                continue
            if not start <= occurred < end_exclusive:
                diagnostics["outside_date_range"] += 1
                continue
            hour = independent_hour(row.get("Time OCC"))
            if hour is None:
                diagnostics["invalid_or_missing_hours"] += 1
                continue
            counts[hour] += 1
    blocks = {
        "Overnight": sum(counts[h] for h in range(0, 6)),
        "Morning": sum(counts[h] for h in range(6, 12)),
        "Afternoon": sum(counts[h] for h in range(12, 18)),
        "Evening": sum(counts[h] for h in range(18, 24)),
    }
    return {"blocks": blocks, "hourly": {str(h): counts[h] for h in range(24)},
            "diagnostics": dict(diagnostics)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--csv", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve()
    source = args.csv or project / "LAPD_NIBRS_Offenses_Dataset.csv"
    sys.path.insert(0, str(project))
    backend = importlib.import_module("backend_analysis")
    import pandas as pd
    helper = extract_helper(project / "dashboard.py")

    print("Running the existing backend checks...", flush=True)
    tests = importlib.import_module("test_backend_analysis")
    existing_checks = []
    for name in sorted(n for n in vars(tests) if n.startswith("test_")):
        getattr(tests, name)()
        existing_checks.append({"test": name, "result": "pass"})

    raw = pd.DataFrame({
        "CaseNo": ["A", "B", "C", "D"],
        "Date_Occurred": ["2026-10-16"] * 4,
        "Time_Occurred": [100, 800, 1400, 2000],
        "Area_Name": ["Central"] * 4,
        "Report_District_No": [101] * 4,
        "Premise_Description": ["STREET"] * 4,
        "valid_coordinates": [True] * 4,
    })
    small = backend.enrich_data(raw, "nibrs")
    ranges = {"Overnight": range(0, 6), "Morning": range(6, 12),
              "Afternoon": range(12, 18), "Evening": range(18, 24)}
    fixture_results = []
    for blocks in [["Evening"], ["Overnight", "Morning"], ["Overnight", "Evening"]]:
        low, high = helper(blocks)
        selected = backend.apply_filters(small, backend.FilterSpec(start_hour=low, end_hour=high))
        allowed = set().union(*(set(ranges[b]) for b in blocks))
        expected_ids = [r.CaseNo for r in raw.itertuples() if r.Time_Occurred // 100 in allowed]
        actual_ids = selected["CaseNo"].tolist()
        fixture_results.append({"blocks": blocks, "expected_ids": expected_ids,
                                "actual_ids": actual_ids, "expected": len(expected_ids),
                                "actual": backend.nibrs_headline_metrics(selected)["selected_offense_rows"],
                                "converted_hour_range": [low, high]})
    assert [r["actual"] for r in fixture_results] == [1, 2, 4]
    assert [r["expected"] for r in fixture_results] == [1, 2, 2]

    # Explicit boundary values for the proposed set-membership rule.
    boundary_times = [0, 559, 600, 1759, 1800, 2359, 2400, 1265, None]
    boundary = raw.iloc[[0] * len(boundary_times)].reset_index(drop=True)
    boundary["Time_Occurred"] = boundary_times
    boundary["CaseNo"] = [str(i) for i in range(len(boundary_times))]
    enriched = backend.enrich_data(boundary, "nibrs")
    chosen_hours = set(range(0, 6)) | set(range(18, 24))
    proposed_kept = enriched.loc[enriched["occurrence_hour"].isin(chosen_hours), "Time_Occurred"].tolist()
    assert proposed_kept == [0, 559, 1800, 2359]

    print("Loading the full NIBRS CSV with the unchanged app loader...", flush=True)
    frame = backend.load_clean_data(source, "nibrs")
    start = frame["Date_Occurred"].min().date().isoformat()
    end = frame["Date_Occurred"].max().date().isoformat()
    areas = sorted(frame["Area_Name"].dropna().astype(str).unique().tolist())
    common = dict(areas=areas, days=list(backend.DAY_ORDER), start_date=start, end_date=end)
    app_counts = {}
    for label, blocks in {"Overnight": ["Overnight"], "Evening": ["Evening"],
                          "Overnight + Evening": ["Overnight", "Evening"]}.items():
        low, high = helper(blocks)
        filtered = backend.apply_filters(frame, backend.FilterSpec(**common, start_hour=low, end_hour=high))
        app_counts[label] = backend.nibrs_headline_metrics(filtered)["selected_offense_rows"]

    print("Independently recounting CSV rows using the standard library...", flush=True)
    independent = independent_csv_counts(source, {a.strip().lower() for a in areas},
                                         datetime.fromisoformat(start),
                                         (pd.Timestamp(end) + pd.Timedelta(days=1)).to_pydatetime())
    counts = independent["blocks"]
    expected = counts["Overnight"] + counts["Evening"]
    actual = app_counts["Overnight + Evening"]
    excess = actual - expected
    assert app_counts["Overnight"] == counts["Overnight"] == 82267
    assert app_counts["Evening"] == counts["Evening"] == 140716
    assert actual == sum(counts.values()) == 471285
    assert expected == 222983
    assert excess == counts["Morning"] + counts["Afternoon"] == 248302
    # Validate the proposed filter as a scratch calculation, without editing the app.
    base = backend.apply_filters(frame, backend.FilterSpec(**common))
    proposed_count = int(base["occurrence_hour"].isin(chosen_hours).sum())
    assert proposed_count == expected

    result = {
        "audit_date": "2026-10-23",
        "app_commit": "53645eff24eb73d9c80159f68bf03104fbeb8058",
        "source_kind": "User-supplied raw CSV passed through the app's existing adapter/enricher; full cleaning notebook was not run",
        "source_bytes": source.stat().st_size,
        "source_sha256": sha256(source),
        "code_sha256": {n: sha256(project / n) for n in ["dashboard.py", "backend_analysis.py", "BUILD_SPEC.md"]},
        "python": sys.version.split()[0], "pandas": pd.__version__,
        "filters": {"areas": areas, "district": "none", "start_date_inclusive": start,
                    "end_date_inclusive": end, "days": list(backend.DAY_ORDER),
                    "offense": "none", "premise": "none", "context": "none",
                    "valid_coordinates_only": False},
        "existing_backend_checks": existing_checks,
        "synthetic_fixture": fixture_results,
        "boundary_input_hhmm": boundary_times,
        "proposed_rule_boundary_kept_hhmm": proposed_kept,
        "backend_counts_matching_live_ui": app_counts,
        "independent_csv": independent,
        "expected_combined": expected, "actual_combined": actual,
        "excess_rows": excess, "overstatement_percent_of_expected": excess / expected * 100,
        "proposed_union_count_scratch_only": proposed_count,
    }
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"expected": expected, "actual": actual, "excess": excess,
                      "independent_blocks": counts, "existing_tests_passed": len(existing_checks),
                      "result_file": str(args.out)}, indent=2), flush=True)


if __name__ == "__main__":
    main()
