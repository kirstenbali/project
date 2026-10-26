"""Reproduce Steven's Module 9 audit without production CSVs.

Run: python audit_check_steven.py
The app source is unchanged. Synthetic data is injected at its loader boundary.
"""
import json
import importlib.metadata
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from streamlit.testing.v1 import AppTest

import backend_analysis as backend


def fixture():
    return backend.enrich_data(pd.DataFrame({
        "UniqueNIBRNo": ["TEST1", "TEST2", "TEST3", "TEST4", "TEST5", "TEST6"],
        "CaseNo": ["A", "A", "B", "C", "C", None],
        "Date_Occurred": ["2026-10-19"] * 6,
        "Time_Occurred": [900] * 6,
        "Area_Name": ["Central"] * 3 + ["West LA"] * 3,
        "Report_District_No": [101] * 3 + [901] * 3,
        "Premise_Description": ["STREET"] * 6,
        "Transit-related Crime": ["No"] * 6,
        "Domestic Violence Crime": ["No"] * 6,
        "Homeless-Victim Crime": ["No"] * 6,
        "valid_coordinates": [True] * 6,
        "NIBR Description": ["TEST OFFENSE"] * 6,
    }), "nibrs")


def loader(_path, dataset):
    data = fixture()
    if dataset == "legacy":
        data = data.rename(columns={"CaseNo": "DR_NO"})
        data["Crime_Description"] = "TEST OFFENSE"
    return data


def independent_cases(rows):
    # Plain Python loop/set, independent of the app's pandas nunique.
    seen = set()
    for row in rows:
        value = row["CaseNo"]
        if value is not None and not pd.isna(value):
            seen.add(value)
    return len(seen)


def values(app):
    assert len(app.exception) == 0, [e.message for e in app.exception]
    return {m.label: m.value for m in app.metric[:4]}


def run():
    data = fixture()
    number_checks = []
    for name, frame in [
        ("all", data),
        ("Central", data[data.Area_Name == "Central"]),
        ("West LA", data[data.Area_Name == "West LA"]),
        ("empty", data.iloc[:0]),
    ]:
        expected = independent_cases(frame.to_dict("records"))
        actual = backend.nibrs_headline_metrics(frame)["unique_cases"]
        assert actual == expected
        number_checks.append({"selection": name, "offense_rows": len(frame),
                              "expected_unique_cases": expected, "actual_unique_cases": actual})

    # A second assumption check: excluding a row with a missing ID must not
    # remove any of the three identified cases.
    assert backend.nibrs_headline_metrics(data.dropna(subset=["CaseNo"]))["unique_cases"] == 3

    with patch.object(backend, "load_clean_data", side_effect=loader):
        app = AppTest.from_file(str(Path(__file__).with_name("dashboard.py")))
        app.run(timeout=30)
        initial = values(app)
        area = next(w for w in app.multiselect if w.label == "Area")
        area.set_value(["Central"]).run(timeout=30)
        filtered = values(app)
        selected = next(w for w in app.multiselect if w.label == "Area").value
        reset = next(w for w in app.button if w.label == "Reset filters")
        reset.click().run(timeout=30)
        after_reset = values(app)
        after_area = next(w for w in app.multiselect if w.label == "Area").value
        assert initial["Unique cases"] == "3"
        assert filtered["Unique cases"] == "2"
        report = {
            "fixture": [{"offense_row": f"TEST{i+1}", "CaseNo": case,
                         "Area_Name": area}
                        for i, (case, area) in enumerate(zip(
                            ["A", "A", "B", "C", "C", None],
                            ["Central"] * 3 + ["West LA"] * 3))],
            "environment": {p: importlib.metadata.version(p) for p in ["pandas", "streamlit", "matplotlib", "pytest"]},
            "number_checks": number_checks,
            "ui_initial": initial,
            "ui_filtered": filtered,
            "ui_after_reset": after_reset,
            "area_before_reset": selected,
            "area_after_reset": after_area,
            "reset_expected": {"Area": ["Central", "West LA"], "Selected offense rows": "6", "Unique cases": "3"},
            "reset_matches_expected": after_area == ["Central", "West LA"] and after_reset["Selected offense rows"] == "6",
        }
    print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == "__main__":
    run()
