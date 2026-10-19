from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from backend_analysis import (
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


NIBRS_PATH = Path(__file__).resolve().with_name("LAPD_NIBRS_Offenses_Dataset.csv")
LEGACY_PATH = Path(__file__).resolve().with_name("Crime_Data_from_2020_to_2024.csv")


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


def _time_block_hours(selected_blocks: list[str]) -> tuple[int | None, int | None]:
    block_map = {
        "Overnight": (0, 5),
        "Morning": (6, 11),
        "Afternoon": (12, 17),
        "Evening": (18, 23),
    }
    hours = [block_map[b] for b in selected_blocks if b in block_map]
    if not hours:
        return None, None
    start = min(h[0] for h in hours)
    end = max(h[1] for h in hours)
    return start, end


def _format_summary(spec: FilterSpec, dataset: str) -> str:
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
    if spec.start_hour is not None or spec.end_hour is not None:
        bits.append(f"Hours: {spec.start_hour} to {spec.end_hour}")
    if spec.offenses:
        bits.append(f"Offenses: {', '.join(spec.offenses)}")
    if spec.premises:
        bits.append(f"Premises: {', '.join(spec.premises)}")
    if spec.valid_coordinates_only:
        bits.append("Valid coordinates only")
    if dataset == "nibrs" and (spec.contexts or spec.context != "all"):
        values = spec.contexts if spec.contexts is not None else [spec.context]
        bits.append(f"Contexts: {', '.join(str(v) for v in values)} ({spec.context_mode})")
    return "; ".join(bits) if bits else "All records"


with st.sidebar:
    st.header("Filters")
    st.caption("Current NIBRS Review")

    if "reset_filters" not in st.session_state:
        st.session_state.reset_filters = False

    nibrs = load_nibrs_data()
    legacy = load_legacy_data()
    all_areas = _safe_option_list(nibrs["Area_Name"].dropna())
    all_premises = _safe_option_list(nibrs["Premise_Description"].dropna())
    all_offenses = _safe_option_list(nibrs["NIBR Description"].dropna())
    all_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    all_contexts = ["transit", "domestic_violence", "homeless_victim", "street_sidewalk_parking"]

    selected_areas = st.multiselect("Area", all_areas, default=all_areas)
    district_candidates = sorted(
        {str(v) for v in nibrs.loc[nibrs["Area_Name"].isin(selected_areas), "Report_District_No"].dropna().astype(int).unique()}
    ) if selected_areas else sorted({str(v) for v in nibrs["Report_District_No"].dropna().astype(int).unique()})
    selected_districts = st.multiselect("Reporting district", district_candidates, default=[])

    start_date = st.date_input("Start date", value=pd.to_datetime(nibrs["Date_Occurred"].min()).date(), min_value=pd.to_datetime(nibrs["Date_Occurred"].min()).date(), max_value=pd.to_datetime(nibrs["Date_Occurred"].max()).date())
    end_date = st.date_input("End date", value=pd.to_datetime(nibrs["Date_Occurred"].max()).date(), min_value=pd.to_datetime(nibrs["Date_Occurred"].min()).date(), max_value=pd.to_datetime(nibrs["Date_Occurred"].max()).date())

    selected_days = st.multiselect("Day", all_days, default=all_days)
    selected_blocks = st.multiselect("Time-of-day block", ["Overnight", "Morning", "Afternoon", "Evening"], default=["Overnight", "Morning", "Afternoon", "Evening"])
    start_hour, end_hour = _time_block_hours(selected_blocks)

    selected_offenses = st.multiselect("Offense", all_offenses, default=[])
    selected_premises = st.multiselect("Premise", all_premises, default=[])
    selected_contexts = st.multiselect("Context", all_contexts, default=[])
    context_mode = st.radio("Context logic", ["OR", "AND"], horizontal=True)
    valid_coords_only = st.checkbox("Valid coordinates only")

    if st.button("Reset filters"):
        st.session_state.pop("nibrs_filter_spec", None)
        st.rerun()


spec = FilterSpec(
    areas=selected_areas or None,
    districts=[int(v) for v in selected_districts] if selected_districts else None,
    start_date=start_date.isoformat() if start_date else None,
    end_date=end_date.isoformat() if end_date else None,
    days=selected_days or None,
    day_types=None,
    start_hour=start_hour,
    end_hour=end_hour,
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

st.markdown('<div class="section-title"><h3>Resource cues</h3><p>Counts and shares for each context flag in the active selection.</p></div>', unsafe_allow_html=True)
cue_df = context_cues(nibrs_filtered)
st.dataframe(cue_df.style.format({"share_of_selected_rows": "{:.1%}"}), use_container_width=True, hide_index=True)

hourly = hourly_distribution(nibrs_filtered)
blocks = time_of_day_summary(nibrs_filtered)
heat = day_hour_matrix(nibrs_filtered).pivot(index="day_name", columns="occurrence_hour", values="offense_rows")
heat = heat.reindex(index=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], columns=range(24), fill_value=0)

st.markdown('<div class="section-title"><h3>Time patterns</h3><p>Hourly and time-of-day comparisons for the active NIBRS selection.</p></div>', unsafe_allow_html=True)
chart_col, block_col = st.columns(2)
with chart_col:
    st.bar_chart(hourly.set_index("occurrence_hour")["offense_rows"], use_container_width=True)
with block_col:
    st.bar_chart(blocks.set_index("time_of_day")["offense_rows"], use_container_width=True)

st.dataframe(
    heat.style.background_gradient(cmap="Blues").format("{:.0f}"),
    use_container_width=True,
    hide_index=True,
)

st.markdown('<div class="section-title"><h3>District activity</h3><p>Which districts are carrying the most selected offense rows and resource cues.</p></div>', unsafe_allow_html=True)
district_table = district_activity(nibrs_filtered)
st.dataframe(district_table.style.format({"share_of_selection": "{:.1%}", "valid_coordinate_share": "{:.1%}"}), use_container_width=True, hide_index=True)

premise = premise_summary(nibrs_filtered, top_n=10)
st.markdown('<div class="section-title"><h3>Premise summary</h3><p>Where the selected offenses occurred most often.</p></div>', unsafe_allow_html=True)
st.dataframe(premise, use_container_width=True, hide_index=True)

st.markdown('<div class="section-title"><h3>Review queue</h3><p>Districts explicitly selected for human planning review.</p></div>', unsafe_allow_html=True)
queue = st.session_state.setdefault("queue", [])
if not queue:
    st.caption("No districts added yet.")
else:
    st.dataframe(pd.DataFrame(queue), use_container_width=True, hide_index=True)

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
            queue.append({
                "Report_District_No": district,
                "offense_rows": int(row["offense_rows"]),
                "unique_cases": int(row["unique_cases"]),
                "filter_summary": _format_summary(spec, "nibrs"),
                "why_shown": f"{row['offense_rows']} selected offense rows; {row['street_sidewalk_parking']} street/sidewalk/parking."
            })
    st.rerun()

with st.expander("Current filter summary"):
    st.write(_format_summary(spec, "nibrs") or "All records")

with st.expander("Legacy Reference"):
    legacy_data = load_legacy_data()
    legacy_spec = FilterSpec(
        areas=selected_areas or None,
        districts=[int(v) for v in selected_districts] if selected_districts else None,
        start_date=start_date.isoformat() if start_date else None,
        end_date=end_date.isoformat() if end_date else None,
        days=selected_days or None,
        day_types=None,
        start_hour=start_hour,
        end_hour=end_hour,
        offenses=selected_offenses or None,
        premises=selected_premises or None,
        valid_coordinates_only=valid_coords_only,
        context="all",
        contexts=None,
        context_mode="or",
    )
    legacy_filtered = apply_filters(legacy_data, legacy_spec, dataset="legacy")
    lifecycle = legacy_headline_metrics(legacy_filtered)
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Legacy rows", lifecycle["legacy_rows"])
    col_b.metric("Unique legacy records", lifecycle["unique_legacy_records"])
    col_c.metric("Reporting districts", lifecycle["reporting_districts"])
    st.line_chart(legacy_monthly_trend(legacy_filtered).set_index("month")["legacy_rows"])
    st.dataframe(legacy_area_summary(legacy_filtered), use_container_width=True, hide_index=True)

with st.expander("Data Notes"):
    st.markdown(
        """
        - Row grain is offense rows for NIBRS and reported records for legacy data.
        - Totals are not population-adjusted risk measures.
        - Exact coordinates and street addresses are not displayed in the interface.
        - Context flags are transparent evidence cues, not risk scores.
        - Current NIBRS and legacy sections remain separate in the app.
        """
    )
