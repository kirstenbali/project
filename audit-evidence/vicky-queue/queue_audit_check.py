"""Vicky Huang's controlled audit of district counts and the review-queue widget.

Run: python -B queue_audit_check.py --project /path/to/team/app --out results.json
Uses invented rows and patches only the loader during the test. No CSV is needed.
No application source, teammate file, or production data is edited.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import importlib
import io
import json
import logging
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch
import warnings


def make_fixture(backend, pd, district_format="padded"):
    districts = {"padded": ["0101", "0101", "0101", "0102"],
                 "plain": ["101", "101", "101", "102"],
                 "integer": [101, 101, 101, 102]}[district_format]
    raw = pd.DataFrame({
        "CaseNo": ["A", "A", "B", "C"],
        "Date_Occurred": ["2026-10-19"] * 4,
        "Time_Occurred": [900, 1000, 1100, 1200],
        "Area_Name": ["Central"] * 4,
        "Report_District_No": districts,
        "Premise_Description": ["STREET"] * 4,
        "NIBR Description": ["TEST OFFENSE"] * 4,
        "valid_coordinates": [True] * 4,
        "Transit-related Crime": ["No"] * 4,
        "Domestic Violence Crime": ["No"] * 4,
        "Homeless-Victim Crime": ["No"] * 4,
    })
    return backend.enrich_data(raw, "nibrs")


def make_legacy(backend, pd):
    # Supporting invented data only, so the unmodified page can render Legacy Reference.
    return backend.enrich_data(pd.DataFrame({
        "DR_NO": ["L1"], "Date_Occurred": ["2026-10-19"],
        "Time_Occurred": [900], "Area_Name": ["Central"],
        "Report_District_No": [101], "Crime_Description": ["TEST OFFENSE"],
    }), "legacy")


def independent_counts(frame):
    # Python row counter, independent of pandas groupby and the app metric.
    return dict(Counter(str(row["Report_District_No"])
                        for row in frame.to_dict("records")
                        if row["Report_District_No"] is not None))


def backend_counts(backend, frame):
    table = backend.district_activity(frame)
    return {str(row.Report_District_No): int(row.offense_rows)
            for row in table.itertuples()}


def widget_case(project, backend, pd, st, AppTest, district_format):
    nibrs = make_fixture(backend, pd, district_format)
    legacy = make_legacy(backend, pd)

    def fixture_loader(path, dataset):
        return (nibrs if dataset == "nibrs" else legacy).copy()

    st.cache_data.clear()
    with patch.object(backend, "load_clean_data", side_effect=fixture_loader):
        app = AppTest.from_file(str(project / "dashboard.py"), default_timeout=30).run()
        assert not app.exception, [e.message for e in app.exception]
        before_queue = list(app.session_state["queue"])
        assert before_queue == []
        # Read the actual table passed to Streamlit, not just a backend result.
        table = next(d.value for d in app.dataframe
                     if {"Report_District_No", "offense_rows", "unique_cases"}.issubset(d.value.columns))
        visible_counts = {str(row.Report_District_No): int(row.offense_rows)
                          for row in table.itertuples()}
        picker = next(w for w in app.multiselect if w.label == "Choose a district to add")
        options = list(picker.options)
        assert options == ["101", "102"]
        picker.set_value(["101"]).run()
        assert not app.exception
        next(w for w in app.button if w.label == "Add selected district(s)").click().run()
        errors = [e.message for e in app.exception]
        queue = list(app.session_state["queue"])
        duplicate_click_count = None
        if not errors:
            assert len(queue) == 1 and queue[0]["offense_rows"] == 3
            next(w for w in app.button if w.label == "Add selected district(s)").click().run()
            assert not app.exception
            duplicate_click_count = len(app.session_state["queue"])
            assert duplicate_click_count == 1
        else:
            assert district_format == "padded"
            assert errors == ["single positional indexer is out-of-bounds"]
            assert queue == []
        return {"district_format": district_format, "visible_district_counts": visible_counts,
                "selector_options": options, "selected_option": "101",
                "expected_queue_rows": 1, "expected_offense_rows": 3,
                "actual_queue": queue, "exceptions": errors,
                "feature_matches_expected": not errors and len(queue) == 1,
                "queue_rows_after_duplicate_click": duplicate_click_count}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve()
    sys.path.insert(0, str(project))
    import pandas as pd
    import streamlit as st
    from streamlit.testing.v1 import AppTest
    backend = importlib.import_module("backend_analysis")
    names = ["dashboard.py", "backend_analysis.py", "BUILD_SPEC.md"]
    hashes = {n: hashlib.sha256((project / n).read_bytes()).hexdigest() for n in names}
    logging.getLogger("streamlit").setLevel(logging.ERROR)
    warnings.filterwarnings("ignore", category=UserWarning, module="altair")

    data = make_fixture(backend, pd)
    variants = {
        "all_rows": data,
        "repeated_case_changed_to_missing": data.assign(CaseNo=["A", None, "B", "C"]),
        "one_0101_row_removed": data.drop(index=1),
        "filtered_to_11_and_12": backend.apply_filters(data, backend.FilterSpec(start_hour=11, end_hour=12)),
        "empty_selection": data.iloc[0:0],
    }
    number_checks = []
    for label, frame in variants.items():
        expected = independent_counts(frame)
        actual = backend_counts(backend, frame)
        assert actual == expected, (label, expected, actual)
        number_checks.append({"case": label, "expected": expected, "actual": actual, "pass": True})
    assert number_checks[0]["actual"] == {"0101": 3, "0102": 1}
    assert number_checks[1]["actual"] == {"0101": 3, "0102": 1}
    assert number_checks[2]["actual"] == {"0101": 2, "0102": 1}
    assert number_checks[3]["actual"] == {"0101": 1, "0102": 1}
    assert number_checks[4]["actual"] == {}

    print("Running actual dashboard widgets with padded, plain, and integer district IDs...", flush=True)
    ui = [widget_case(project, backend, pd, st, AppTest, form)
          for form in ["padded", "plain", "integer"]]
    assert ui[0]["feature_matches_expected"] is False
    assert ui[1]["feature_matches_expected"] is True
    assert ui[2]["feature_matches_expected"] is True
    assert ui[0]["visible_district_counts"] == {"0101": 3, "0102": 1}

    tests = importlib.import_module("test_backend_analysis")
    original_tests = []
    for name in sorted(n for n in vars(tests) if n.startswith("test_")):
        getattr(tests, name)()
        original_tests.append({"test": name, "pass": True})
    for name, before in hashes.items():
        assert hashlib.sha256((project / name).read_bytes()).hexdigest() == before

    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=project,
                            capture_output=True, text=True, check=True).stdout.strip()
    result = {
        "auditor": "Vicky Huang", "audit_date": "2026-10-26",
        "request_id": "CR-VH-02", "repo_commit_checked": commit,
        "original_app_source_commit": "53645eff24eb73d9c80159f68bf03104fbeb8058",
        "source_sha256": hashes,
        "python": sys.version.split()[0], "pandas": pd.__version__, "streamlit": st.__version__,
        "fixture_kind": "Four invented offense rows; temporary loader patch; no production CSV used",
        "fixture": [{"row": "Q1", "district": "0101", "CaseNo": "A", "time_hhmm": 900},
                    {"row": "Q2", "district": "0101", "CaseNo": "A", "time_hhmm": 1000},
                    {"row": "Q3", "district": "0101", "CaseNo": "B", "time_hhmm": 1100},
                    {"row": "Q4", "district": "0102", "CaseNo": "C", "time_hhmm": 1200}],
        "other_fixture_fields": {"area": "Central", "date": "2026-10-19",
            "premise": "STREET", "offense": "TEST OFFENSE", "valid_coordinates": True,
            "transit_domestic_violence_homeless_victim": "No"},
        "ui_filters": "Default all-area/day/time settings; no district, offense, premise or context restriction; coordinate-only unchecked",
        "number_checks": number_checks, "widget_checks": ui,
        "existing_backend_tests": original_tests,
        "interpretation": "District offense-row counts pass controlled checks; Add selected district(s) fails for zero-padded IDs",
        "ai_assistance": "Fixture design, code tracing, test implementation/execution, evidence recording, and draft wording",
        "limits": "Controlled fixtures only; production prevalence, all identifier formats, deployment, and an integrated fix are not verified",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"number_checks_passed": len(number_checks),
        "padded_id_error": ui[0]["exceptions"],
        "padded_id_queue": ui[0]["actual_queue"],
        "plain_id_queue": ui[1]["actual_queue"],
        "integer_id_queue": ui[2]["actual_queue"],
        "original_tests_passed": len(original_tests), "results": str(args.out)}, indent=2), flush=True)


if __name__ == "__main__":
    main()
