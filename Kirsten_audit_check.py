"""Reproducible check for Kirsten Bali's Module 9 time-block audit."""

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


def dashboard_time_block_hours(selected_blocks):
    """Same conversion used by dashboard(1).py."""
    block_map = {
        "Overnight": (0, 5), "Morning": (6, 11),
        "Afternoon": (12, 17), "Evening": (18, 23),
    }
    hours = [block_map[block] for block in selected_blocks if block in block_map]
    if not hours:
        return None, None
    return min(hour[0] for hour in hours), max(hour[1] for hour in hours)


raw = pd.DataFrame({
    "CaseNo": ["A", "B", "C", "D"],
    "Date_Occurred": ["2026-10-19"] * 4,
    "Time_Occurred": ["0200", "0800", "1400", "2000"],
    "Area_Name": ["Central"] * 4,
    "Report_District_No": [101] * 4,
    "Premise_Description": ["HOME"] * 4,
    "valid_coordinates": [True] * 4,
    "Transit-related Crime": ["No"] * 4,
    "Domestic Violence Crime": ["No"] * 4,
    "Homeless-Victim Crime": ["No"] * 4,
    "NIBR Description": ["X"] * 4,
})

data = backend.enrich_data(raw, "nibrs")
selected_blocks = ["Morning", "Evening"]
start_hour, end_hour = dashboard_time_block_hours(selected_blocks)
actual = backend.apply_filters(
    data, backend.FilterSpec(start_hour=start_hour, end_hour=end_hour), "nibrs"
)
hourly = backend.hourly_distribution(actual)
actual_hours = actual["occurrence_hour"].astype(int).tolist()
actual_total = int(hourly["offense_rows"].sum())

# Independent expected calculation: membership in either selected block.
expected_hours = [int(hour) for hour in data["occurrence_hour"].dropna()
                  if 6 <= int(hour) <= 11 or 18 <= int(hour) <= 23]
expected_total = len(expected_hours)

print("Selected blocks:", selected_blocks)
print("Dashboard converts them to continuous range:", (start_hour, end_hour))
print("Expected included hours:", expected_hours)
print("Actual included hours:", actual_hours)
print("Expected hourly-distribution total:", expected_total)
print("Actual hourly-distribution total:", actual_total)

assert len(hourly) == 24
assert actual_total == len(actual)
assert actual_total == expected_total, (
    "FAIL: Morning + Evening should include 2 rows, but the dashboard's "
    f"continuous 06-23 range includes {actual_total}."
)

