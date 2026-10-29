from io import StringIO

import pandas as pd

from backend_analysis import (
    FilterSpec,
    apply_filters,
    build_review_queue,
    context_cues,
    day_hour_matrix,
    district_activity,
    enrich_data,
    hourly_distribution,
    legacy_monthly_trend,
    load_clean_data,
    nibrs_headline_metrics,
    premise_summary,
    time_of_day_summary,
)


def sample_nibrs():
    raw = pd.DataFrame({
        "CaseNo": ["A", "A", "B", "C"],
        "Date_Occurred": ["2026-10-16", "2026-10-16", "2026-10-17", "2026-10-18"],
        "Time_Occurred": [2030, 2330, 15, 1265],
        "Area_Name": ["Central", "Central", "Central", "West LA"],
        "Report_District_No": [101, 101, 102, pd.NA],
        "Premise_Description": ["STREET", "TRANSIT FACILITY", "PARKING LOT", pd.NA],
        "Transit-related Crime": ["No", "Yes", "No", "No"],
        "Domestic Violence Crime": ["No", "No", "Yes", "No"],
        "Homeless-Victim Crime": ["Yes", "No", "No", "No"],
        "valid_coordinates": [True, "Yes", False, False],
        "NIBR Description": ["X", "Y", "X", "Z"],
    })
    return enrich_data(raw, "nibrs")


def test_load_clean_data_accepts_file_objects():
    csv = StringIO(
        "CaseNo,Date_Occurred,Area_Name,Report_District_No,Premise_Description,"
        "valid_coordinates,Time_Occurred,Transit-related Crime,Domestic Violence Crime,"
        "Homeless-Victim Crime\n"
        "A,2026-10-16,Central,101,STREET,True,2030,No,No,Yes\n"
        "B,2026-10-17,West LA,102,PARKING LOT,Yes,800,Yes,No,No\n"
    )
    loaded = load_clean_data(csv, "nibrs")
    assert len(loaded) == 2
    assert set(loaded.columns) >= {"Date_Occurred", "occurrence_hour", "time_of_day"}


def test_filter_and_metrics():
    data = sample_nibrs()
    selected = apply_filters(
        data,
        FilterSpec(areas=["Central"], start_hour=20, end_hour=23),
        "nibrs",
    )
    assert len(selected) == 2
    metrics = nibrs_headline_metrics(selected)
    assert metrics["selected_offense_rows"] == 2
    assert metrics["unique_cases"] == 1
    assert metrics["valid_coordinate_rows"] == 2


def test_context_cues_and_districts_reconcile():
    data = sample_nibrs()
    cues = context_cues(data).set_index("cue")["count"].to_dict()
    assert cues == {
        "street_sidewalk_parking": 2,
        "transit_related": 1,
        "domestic_violence": 1,
        "homeless_victim": 1,
    }
    districts = district_activity(data)
    assert districts["offense_rows"].sum() == 3
    assert nibrs_headline_metrics(data)["rows_missing_district"] == 1


def test_valid_coordinates_toggle_keeps_non_geographic_denominators_constant():
    data = sample_nibrs()
    baseline = apply_filters(data, FilterSpec(), "nibrs")
    toggled = apply_filters(data, FilterSpec(valid_coordinates_only=True), "nibrs")

    assert len(toggled) == len(baseline)
    assert nibrs_headline_metrics(toggled)["selected_offense_rows"] == nibrs_headline_metrics(baseline)["selected_offense_rows"]
    baseline_cues = context_cues(baseline).set_index("cue")
    toggled_cues = context_cues(toggled).set_index("cue")
    assert toggled_cues["share_of_selected_rows"].equals(
        baseline_cues["share_of_selected_rows"]
    )


def test_complete_chart_shapes_and_queue_privacy():
    data = sample_nibrs()
    assert len(hourly_distribution(data)) == 24
    assert hourly_distribution(data)["offense_rows"].sum() == 3
    assert len(day_hour_matrix(data)) == 7 * 24
    assert premise_summary(data)["offense_rows"].sum() == len(data)
    queue = build_review_queue(data, "Area: all")
    assert len(queue) == 2
    assert "LAT" not in queue.columns and "LON" not in queue.columns
    assert queue["why_shown"].str.contains("selected offense rows").all()


def test_context_filter_supports_multi_select_or_mode_and_time_blocks():
    data = sample_nibrs()
    filtered = apply_filters(
        data,
        FilterSpec(contexts=["transit", "domestic_violence"], context_mode="or"),
        "nibrs",
    )
    assert len(filtered) == 2
    assert set(filtered["time_of_day"].unique()) == {"Evening", "Overnight"}
    blocks = time_of_day_summary(data)
    assert blocks["time_of_day"].tolist() == ["Overnight", "Morning", "Afternoon", "Evening"]
    assert blocks["offense_rows"].sum() == 3


def test_time_block_selection_uses_the_selected_union():
    data = sample_nibrs().drop(columns=["occurrence_hour", "time_of_day"])
    data["Time_Occurred"] = [800, 1400, 2000, 800]
    data = enrich_data(data, "nibrs")

    selected = apply_filters(
        data,
        FilterSpec(time_blocks=["Morning", "Evening"]),
        "nibrs",
    )
    hourly = hourly_distribution(selected).set_index("occurrence_hour")["offense_rows"]

    assert len(selected) == 3
    assert hourly.sum() == 3
    assert hourly.loc[8] == 2
    assert hourly.loc[14] == 0
    assert hourly.loc[20] == 1


def test_legacy_months_are_filled():
    legacy = pd.DataFrame({
        "Date_Occurred": pd.to_datetime(["2024-01-10", "2024-03-05"])
    })
    result = legacy_monthly_trend(legacy)
    assert result["legacy_rows"].tolist() == [1, 0, 1]
