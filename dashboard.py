from __future__ import annotations

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

matplotlib.use("Agg")

from backend_analysis import (
    DAY_ORDER,
    FilterSpec,
    apply_filters,
    context_cues,
    day_hour_matrix,
    district_activity,
    enrich_data,
    hourly_distribution,
    legacy_area_summary,
    legacy_headline_metrics,
    legacy_monthly_trend,
    load_clean_data,
    nibrs_headline_metrics,
    premise_summary,
    time_of_day_summary,
)


NIBRS_PATH = Path(__file__).resolve().with_name("cleaned_LAPD_NIBRS_Offenses_Dataset.csv")
LEGACY_PATH = Path(__file__).resolve().with_name("cleaned_Crime_Data_from_2020_to_2024.csv")


st.set_page_config(page_title="Community Safety Resource Planner", layout="wide")

CUSTOM_CSS = """
<style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .page-header {
        background: linear-gradient(90deg, #0f172a 0%, #1e293b 100%);
        color: white;
        border-radius: 14px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 18px rgba(15, 23, 42, 0.12);
    }
    .page-header h1 {
        margin: 0 0 0.25rem 0;
        font-size: 2.1rem;
    }
    .page-header p {
        margin: 0;
        opacity: 0.85;
        font-size: 0.95rem;
    }
    .status-pill {
        display: inline-block;
        background: rgba(255,255,255,0.12);
        color: #e2e8f0;
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 999px;
        padding: 0.35rem 0.8rem;
        font-size: 0.72rem;
        margin-top: 0.7rem;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }
    .section-title {
        margin-top: 1.4rem;
        margin-bottom: 0.5rem;
        color: #0f172a;
    }
    .section-title h3 {
        margin-bottom: 0.2rem;
    }
    .section-title p {
        margin: 0;
        color: #475569;
        font-size: 0.88rem;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


@st.cache_data
def load_nibrs_data() -> pd.DataFrame:
    return load_clean_data(NIBRS_PATH, "nibrs")


@st.cache_data
def load_legacy_data() -> pd.DataFrame:
    return load_clean_data(LEGACY_PATH, "legacy")


def _safe_option_list(values: pd.Series | list[str] | None) -> list[str]:
    if values is None:
        return []
    if isinstance(values, pd.Series):
        values = values.dropna().astype(str).tolist()
    return sorted({str(v).strip() for v in values if str(v).strip()})


def render_day_hour_heatmap(frame: pd.DataFrame) -> None:
    heat = (
        day_hour_matrix(frame)
        .pivot(index="day_name", columns="occurrence_hour", values="offense_rows")
        .reindex(index=DAY_ORDER, columns=range(24), fill_value=0)
    )

    values = heat.to_numpy()
    fig, ax = plt.subplots(figsize=(14, 4.5))
    image = ax.imshow(values, cmap="Blues", aspect="auto")
    ax.set_xticks(range(24))
    ax.set_xticklabels([str(hour) for hour in range(24)], rotation=90)
    ax.set_yticks(range(len(DAY_ORDER)))
    ax.set_yticklabels(DAY_ORDER)
    ax.set_xlabel("Hour")
    ax.set_ylabel("Day")
    ax.set_title("Day-by-hour selected offense counts")
    fig.colorbar(image, ax=ax, label="Offense rows")

    for row_idx in range(values.shape[0]):
        for col_idx in range(values.shape[1]):
            value = int(values[row_idx, col_idx])
            if value:
                text_color = "white" if value > values.max() / 2 else "black"
                ax.text(col_idx, row_idx, str(value), ha="center", va="center", color=text_color)

    fig.tight_layout()
    st.pyplot(fig)


def _format_summary(
    spec: FilterSpec, dataset: str, geographic_only: bool = False
) -> str:
    bits: list[str] = []
    if spec.areas:
        bits.append(f"Areas: {', '.join(spec.areas)}")
    if spec.districts:
        bits.append(f"Districts: {', '.join(str(d) for d in spec.districts)}")
    if spec.start_date or spec.end_date:
        start = spec.start_date or "start"
        end = spec.end_date or "end"
        bits.append(f"Date: {start} to {end}")
    if spec.days:
        bits.append(f"Days: {', '.join(spec.days)}")
    if spec.day_types:
        bits.append(f"Day types: {', '.join(spec.day_types)}")
    if spec.time_blocks and set(spec.time_blocks) != {
        "Overnight", "Morning", "Afternoon", "Evening"
    }:
        bits.append(f"Time blocks: {', '.join(spec.time_blocks)}")
    elif spec.start_hour is not None or spec.end_hour is not None:
        bits.append(f"Hours: {spec.start_hour} to {spec.end_hour}")
    if spec.offenses:
        bits.append(f"Offenses: {', '.join(spec.offenses)}")
    if spec.premises:
        bits.append(f"Premises: {', '.join(spec.premises)}")
    if spec.valid_coordinates_only or geographic_only:
        bits.append("Geographic summary: valid coordinates only")
    if dataset == "nibrs" and (spec.contexts or spec.context != "all"):
        values = spec.contexts if spec.contexts is not None else [spec.context]
        bits.append(f"Contexts: {', '.join(str(v) for v in values)} ({spec.context_mode})")
    return "; ".join(bits) if bits else "All records"


with st.sidebar:
    st.header("Filters")
    st.caption("Current NIBRS Review")

    nibrs = load_nibrs_data()
    legacy = load_legacy_data()
    all_areas = _safe_option_list(nibrs["Area_Name"].dropna())
    all_premises = _safe_option_list(nibrs["Premise_Description"].dropna())
    all_offenses = _safe_option_list(nibrs["NIBR Description"].dropna())
    all_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    all_contexts = ["transit", "domestic_violence", "homeless_victim", "street_sidewalk_parking"]
    time_blocks = ["Overnight", "Morning", "Afternoon", "Evening"]
    min_date = pd.to_datetime(nibrs["Date_Occurred"].min()).date()
    max_date = pd.to_datetime(nibrs["Date_Occurred"].max()).date()

    filter_defaults = {
        "filter_areas": all_areas,
        "filter_districts": [],
        "filter_start_date": min_date,
        "filter_end_date": max_date,
        "filter_days": all_days,
        "filter_time_blocks": time_blocks,
        "filter_offenses": [],
        "filter_premises": [],
        "filter_contexts": [],
        "filter_context_mode": "OR",
        "filter_valid_coordinates": False,
    }
    for key, value in filter_defaults.items():
        st.session_state.setdefault(key, value)

    def reset_filter_state() -> None:
        for key, value in filter_defaults.items():
            st.session_state[key] = value

    selected_areas = st.multiselect("Area", all_areas, key="filter_areas")
    area_rows = (
        nibrs[nibrs["Area_Name"].astype("string").str.strip().isin(selected_areas)]
        if selected_areas else nibrs
    )
    district_values = area_rows["Report_District_No"].dropna()
    district_candidates = sorted({int(value) for value in district_values})
    st.session_state["filter_districts"] = [
        value for value in st.session_state["filter_districts"]
        if value in district_candidates
    ]
    selected_districts = st.multiselect(
        "Reporting district", district_candidates, key="filter_districts"
    )

    start_date = st.date_input(
        "Start date", min_value=min_date, max_value=max_date, key="filter_start_date"
    )
    end_date = st.date_input(
        "End date", min_value=min_date, max_value=max_date, key="filter_end_date"
    )
    selected_days = st.multiselect("Day", all_days, key="filter_days")
    selected_blocks = st.multiselect(
        "Time-of-day block", time_blocks, key="filter_time_blocks"
    )
    selected_offenses = st.multiselect(
        "Offense", all_offenses, key="filter_offenses"
    )
    selected_premises = st.multiselect(
        "Premise", all_premises, key="filter_premises"
    )
    selected_contexts = st.multiselect(
        "Context", all_contexts, key="filter_contexts"
    )
    context_mode = st.radio(
        "Context logic", ["OR", "AND"], horizontal=True, key="filter_context_mode"
    )
    valid_coords_only = st.checkbox(
        "Valid coordinates only (geographic summary)", key="filter_valid_coordinates"
    )
    st.button("Reset filters", on_click=reset_filter_state, width="stretch")


spec = FilterSpec(
    areas=(
        selected_areas
        if selected_areas and set(selected_areas) != set(all_areas)
        else None
    ),
    districts=[int(v) for v in selected_districts] if selected_districts else None,
    start_date=(
        start_date.isoformat()
        if start_date and (start_date != min_date or end_date != max_date)
        else None
    ),
    end_date=(
        end_date.isoformat()
        if end_date and (start_date != min_date or end_date != max_date)
        else None
    ),
    days=(
        selected_days
        if selected_days and set(selected_days) != set(all_days)
        else None
    ),
    day_types=None,
    time_blocks=(
        selected_blocks
        if selected_blocks and set(selected_blocks) != set(time_blocks)
        else None
    ),
    offenses=selected_offenses or None,
    premises=selected_premises or None,
    valid_coordinates_only=valid_coords_only,
    context="all",
    contexts=selected_contexts or None,
    context_mode=str(context_mode).lower(),
)

st.session_state["nibrs_filter_spec"] = spec

st.markdown(
    """
    <div class="page-header">
        <h1>Community Safety Resource Planner</h1>
        <p>Review recorded offense patterns, resource cues, and district activity for non-enforcement planning.</p>
        <span class="status-pill">Current NIBRS Review</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.info(
    "Active dataset: Current NIBRS Review | Row grain: offense rows | Denominator: filtered NIBRS offense rows | "
    "Warning: raw recorded offense counts are not population-adjusted risk measures."
)

nibrs_filtered = apply_filters(load_nibrs_data(), spec, dataset="nibrs")

if nibrs_filtered.empty:
    st.warning("No records match these filters.")
    st.stop()

metrics = nibrs_headline_metrics(nibrs_filtered)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Selected offense rows", metrics["selected_offense_rows"])
col2.metric("Unique cases", metrics["unique_cases"])
col3.metric("Reporting districts", metrics["reporting_districts"])
col4.metric("Valid-coordinate coverage", f"{metrics['valid_coordinate_rows']} ({metrics['valid_coordinate_share']:.1%})")
st.caption(
    "Coordinate coverage is calculated against all selected offense rows. "
    "The coordinate checkbox changes only the aggregate geographic-support view."
)

st.markdown('<div class="section-title"><h3>Resource cues</h3><p>Counts and shares for each context flag in the active selection.</p></div>', unsafe_allow_html=True)
cue_df = context_cues(nibrs_filtered)
st.dataframe(cue_df.style.format({"share_of_selected_rows": "{:.1%}"}), width="stretch", hide_index=True)

hourly = hourly_distribution(nibrs_filtered)
blocks = time_of_day_summary(nibrs_filtered)
st.markdown('<div class="section-title"><h3>Time patterns</h3><p>Hourly and time-of-day comparisons for the active NIBRS selection.</p></div>', unsafe_allow_html=True)
chart_col, block_col = st.columns(2)
with chart_col:
    st.bar_chart(hourly.set_index("occurrence_hour")["offense_rows"], width="stretch")
with block_col:
    st.bar_chart(blocks.set_index("time_of_day")["offense_rows"], width="stretch")

st.markdown('<div class="section-title"><h3>Day-by-hour heatmap</h3><p>Count rows by ordered day and hour, with missing combinations filled with zero.</p></div>', unsafe_allow_html=True)
render_day_hour_heatmap(nibrs_filtered)

st.markdown('<div class="section-title"><h3>District activity</h3><p>Which districts are carrying the most selected offense rows and resource cues.</p></div>', unsafe_allow_html=True)
district_table = district_activity(nibrs_filtered)
district_chart = district_table.set_index("Report_District_No")[["offense_rows"]]
st.bar_chart(district_chart, width="stretch")
st.caption(
    f"{metrics['rows_missing_district']} selected rows have no reporting district "
    "and are excluded from this district breakdown."
)
st.dataframe(district_table.style.format({"share_of_selection": "{:.1%}", "valid_coordinate_share": "{:.1%}"}), width="stretch", hide_index=True)

if valid_coords_only:
    geographic_rows = nibrs_filtered[nibrs_filtered["valid_coordinates"].fillna(False)]
    geographic_districts = (
        geographic_rows.dropna(subset=["Report_District_No"])
        .groupby("Report_District_No")
        .size()
        .rename("valid_coordinate_rows")
        .reset_index()
        .sort_values(["valid_coordinate_rows", "Report_District_No"], ascending=[False, True])
    )
    st.markdown(
        '<div class="section-title"><h3>Geographic support by district</h3>'
        '<p>Aggregate counts only; no coordinates or street addresses are shown.</p></div>',
        unsafe_allow_html=True,
    )
    st.dataframe(geographic_districts, width="stretch", hide_index=True)

premise = premise_summary(nibrs_filtered, top_n=10)
st.markdown('<div class="section-title"><h3>Premise summary</h3><p>Where the selected offenses occurred most often.</p></div>', unsafe_allow_html=True)
st.dataframe(premise, width="stretch", hide_index=True)

st.markdown('<div class="section-title"><h3>Review queue</h3><p>Districts explicitly selected for human planning review.</p></div>', unsafe_allow_html=True)
queue = st.session_state.setdefault("queue", [])
if not queue:
    st.caption("No districts added yet.")
else:
    st.dataframe(pd.DataFrame(queue), width="stretch", hide_index=True)

selected_for_queue = st.multiselect(
    "Choose a district to add",
    [str(int(v)) for v in district_table["Report_District_No"].astype(int).tolist()],
    default=[],
)
if st.button("Add selected district(s)"):
    for district in selected_for_queue:
        existing = [item["Report_District_No"] for item in queue]
        if district not in existing:
            row = district_table[district_table["Report_District_No"].astype(str) == district].iloc[0].to_dict()
            queue.append(
                {
                    "Report_District_No": district,
                    **{
                        key: int(row[key])
                        for key in (
                            "offense_rows",
                            "unique_cases",
                            "valid_coordinate_rows",
                            "street_sidewalk_parking",
                            "transit_related",
                            "domestic_violence",
                            "homeless_victim",
                            "any_cue_rows",
                        )
                    },
                    "valid_coordinate_share": float(row["valid_coordinate_share"]),
                    "share_of_selection": float(row["share_of_selection"]),
                    "filter_summary": _format_summary(spec, "nibrs", valid_coords_only),
                    "reviewed_at": pd.Timestamp.now().isoformat(timespec="seconds"),
                    "why_shown": (
                        f"{row['offense_rows']} selected offense rows; "
                        f"{row['street_sidewalk_parking']} street/sidewalk/parking; "
                        f"{row['transit_related']} transit-related; "
                        f"{row['domestic_violence']} domestic-violence; "
                        f"{row['homeless_victim']} homeless-victim."
                    ),
                }
            )
    st.rerun()

if queue:
    queue_districts = [item["Report_District_No"] for item in queue]
    remove_districts = st.multiselect("Remove district(s) from queue", queue_districts)
    queue_col, export_col = st.columns(2)
    if queue_col.button("Remove selected", disabled=not remove_districts):
        st.session_state["queue"] = [
            item for item in queue
            if item["Report_District_No"] not in remove_districts
        ]
        st.rerun()
    export_col.download_button(
        "Download queue CSV",
        data=pd.DataFrame(queue).to_csv(index=False),
        file_name="district_review_queue.csv",
        mime="text/csv",
        width="stretch",
    )

with st.expander("Current filter summary"):
    st.write(_format_summary(spec, "nibrs", valid_coords_only) or "All records")

with st.expander("Legacy Reference"):
    legacy_data = load_legacy_data()
    legacy_areas = _safe_option_list(legacy_data["Area_Name"])
    legacy_min_date = pd.to_datetime(legacy_data["Date_Occurred"].min()).date()
    legacy_max_date = pd.to_datetime(legacy_data["Date_Occurred"].max()).date()
    legacy_offense_column = (
        "Crime_Description" if "Crime_Description" in legacy_data.columns else "Crime_Code"
    )
    legacy_offenses = _safe_option_list(legacy_data[legacy_offense_column])
    legacy_premises = _safe_option_list(legacy_data["Premise_Description"]) \
        if "Premise_Description" in legacy_data.columns else []
    st.session_state.setdefault("legacy_areas", legacy_areas)
    st.session_state.setdefault("legacy_districts", [])
    st.session_state.setdefault("legacy_start_date", legacy_min_date)
    st.session_state.setdefault("legacy_end_date", legacy_max_date)
    st.session_state.setdefault("legacy_offenses", [])
    st.session_state.setdefault("legacy_premises", [])
    selected_legacy_areas = st.multiselect(
        "Legacy area", legacy_areas, key="legacy_areas"
    )
    legacy_area_rows = (
        legacy_data[
            legacy_data["Area_Name"].astype("string").str.strip().isin(selected_legacy_areas)
        ]
        if selected_legacy_areas else legacy_data
    )
    legacy_district_values = legacy_area_rows["Report_District_No"].dropna()
    legacy_district_candidates = sorted({int(value) for value in legacy_district_values})
    st.session_state["legacy_districts"] = [
        value for value in st.session_state["legacy_districts"]
        if value in legacy_district_candidates
    ]
    selected_legacy_districts = st.multiselect(
        "Legacy reporting district",
        legacy_district_candidates,
        key="legacy_districts",
    )
    legacy_start_date = st.date_input(
        "Legacy start date",
        min_value=legacy_min_date,
        max_value=legacy_max_date,
        key="legacy_start_date",
    )
    legacy_end_date = st.date_input(
        "Legacy end date",
        min_value=legacy_min_date,
        max_value=legacy_max_date,
        key="legacy_end_date",
    )
    selected_legacy_offenses = st.multiselect(
        "Legacy offense", legacy_offenses, key="legacy_offenses"
    )
    selected_legacy_premises = st.multiselect(
        "Legacy premise", legacy_premises, key="legacy_premises"
    ) if legacy_premises else []
    legacy_spec = FilterSpec(
        areas=selected_legacy_areas or None,
        districts=selected_legacy_districts or None,
        start_date=legacy_start_date.isoformat() if legacy_start_date else None,
        end_date=legacy_end_date.isoformat() if legacy_end_date else None,
        offenses=selected_legacy_offenses or None,
        premises=selected_legacy_premises or None,
    )
    legacy_filtered = apply_filters(legacy_data, legacy_spec, dataset="legacy")
    lifecycle = legacy_headline_metrics(legacy_filtered)
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Legacy rows", lifecycle["legacy_rows"])
    col_b.metric("Unique legacy records", lifecycle["unique_legacy_records"])
    col_c.metric("Reporting districts", lifecycle["reporting_districts"])
    st.line_chart(legacy_monthly_trend(legacy_filtered).set_index("month")["legacy_rows"])
    st.dataframe(legacy_area_summary(legacy_filtered), width="stretch", hide_index=True)

with st.expander("Data Notes"):
    st.markdown(
        """
        - Row grain is offense rows for NIBRS and reported records for legacy data.
        - Totals describe recorded offenses and are not population-adjusted rates.
        - Exact coordinates and street addresses are not displayed in the interface.
        - Context flags are descriptive evidence cues, not scores or resource allocations.
        - Valid-coordinate coverage uses all selected rows as its denominator.
        - The coordinate-only option affects only the aggregate geographic-support view.
        - Missing case identifiers are excluded from the unique-case count.
        - Current NIBRS and legacy records use separate filters and remain separate in the app.
        - Missing occurrence hours are retained unless a time-of-day block is selected.
        """
    )
