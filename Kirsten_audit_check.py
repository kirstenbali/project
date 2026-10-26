"""Reproducible checks for Kirsten Bali's Module 9 audit.

Run from the module9_submission folder with:
    python audit_check.py
"""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

import pandas as pd


BACKEND_PATH = Path(__file__).parents[1] / "upload" / "backend_analysis (1).py"
spec = spec_from_file_location("backend_analysis", BACKEND_PATH)
backend = module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = backend
spec.loader.exec_module(backend)


raw = pd.DataFrame(
    {
        "CaseNo": ["A", "A", "B", "C"],
        "Date_Occurred": ["2026-10-19"] * 4,
        "Time_Occurred": ["0800", "0900", "2200", "1200"],
        "Area_Name": ["Central"] * 4,
        "Report_District_No": [101, 101, 102, 102],
        "Premise_Description": ["STREET", "STORE", "SIDEWALK", "HOME"],
        "valid_coordinates": [True, False, True, False],
        "Transit-related Crime": ["Yes", "No", "No", "No"],
        "Domestic Violence Crime": ["No", "No", "Yes", "No"],
        "Homeless-Victim Crime": ["No", "No", "No", "No"],
        "NIBR Description": ["X", "Y", "Z", "W"],
    }
)

data = backend.enrich_data(raw, "nibrs")
baseline = backend.apply_filters(data, backend.FilterSpec(), "nibrs")
coordinate_toggle = backend.apply_filters(
    data, backend.FilterSpec(valid_coordinates_only=True), "nibrs"
)

baseline_metrics = backend.nibrs_headline_metrics(baseline)
toggle_metrics = backend.nibrs_headline_metrics(coordinate_toggle)
baseline_cues = backend.context_cues(baseline).set_index("cue")
toggle_cues = backend.context_cues(coordinate_toggle).set_index("cue")

print("Hand-calculated fixture: 4 offense rows, 3 unique cases, 2 valid-coordinate rows")
print("Baseline metrics:", baseline_metrics)
print("Toggle metrics:", toggle_metrics)
print(
    "Baseline transit count/share:",
    int(baseline_cues.loc["transit_related", "count"]),
    float(baseline_cues.loc["transit_related", "share_of_selected_rows"]),
)
print(
    "Toggle transit count/share:",
    int(toggle_cues.loc["transit_related", "count"]),
    float(toggle_cues.loc["transit_related", "share_of_selected_rows"]),
)

assert baseline_metrics["selected_offense_rows"] == 4
assert baseline_metrics["unique_cases"] == 3
assert baseline_metrics["valid_coordinate_rows"] == 2
assert baseline_metrics["valid_coordinate_share"] == 0.5
assert baseline_cues.loc["transit_related", "count"] == 1
assert baseline_cues.loc["transit_related", "share_of_selected_rows"] == 0.25

# These assertions encode the build-spec requirement that the coordinate toggle
# must not alter headline counts or non-map cue denominators. They fail against
# the audited backend, documenting the defect.
assert toggle_metrics["selected_offense_rows"] == 4, (
    "FAIL: coordinate toggle changed selected_offense_rows from 4 to "
    f"{toggle_metrics['selected_offense_rows']}"
)
assert toggle_cues.loc["transit_related", "share_of_selected_rows"] == 0.25

