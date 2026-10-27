from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st
from backend_analysis import (
    DAY_ORDER, TIME_OF_DAY_ORDER, FilterSpec, apply_filters, build_review_queue,
    context_cues, day_hour_matrix, district_activity, district_key,
    geographic_subset, hourly_distribution, legacy_area_summary,
    legacy_headline_metrics, legacy_monthly_trend, load_clean_data,
    nibrs_headline_metrics, premise_summary, time_of_day_summary,
)

ROOT = Path(__file__).resolve().parent

def data_path(dataset):
    name = "LAPD_NIBRS_Offenses_Dataset.csv" if dataset == "nibrs" else "Crime_Data_from_2020_to_2024.csv"
    candidates = [ROOT / "data" / f"{dataset}.parquet",
                  ROOT / "cleaned_outputs" / f"cleaned_{name}",
                  ROOT / "data" / "raw" / name, ROOT / name]
    configured = os.environ.get(f"HALO_{dataset.upper()}_PATH")
    if configured:
        return Path(configured)
    return next((p for p in candidates if p.is_file()), candidates[0])

NIBRS_PATH = data_path("nibrs")
LEGACY_PATH = data_path("legacy")
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


@st.cache_data(show_spinner="Loading offense records…", max_entries=2)
def load_nibrs_data():
    return load_clean_data(NIBRS_PATH, "nibrs")


@st.cache_data(show_spinner="Loading historical records…", max_entries=2)
def load_legacy_data():
    return load_clean_data(LEGACY_PATH, "legacy")


def options(values):
    return sorted({str(v).strip() for v in values.dropna() if str(v).strip()})


def reset_filters():
    for key in list(st.session_state):
        if key.startswith("filter_"):
            del st.session_state[key]


def clear_districts():
    st.session_state.pop("filter_districts", None)
    st.session_state.pop("queue_add", None)


def summary(spec):
    parts = []
    for label, values in [("Areas", spec.areas), ("Districts", spec.districts),
                          ("Days", spec.days), ("Time blocks", spec.time_blocks),
                          ("Offenses", spec.offenses), ("Premises", spec.premises),
                          ("Contexts", spec.contexts)]:
        if values:
            if label == "Areas" and set(values) == set(all_areas):
                parts.append("All areas")
            elif label == "Days" and set(values) == set(DAY_ORDER):
                parts.append("All days")
            else:
                parts.append(f"{label}: {', '.join(map(str, values))}")
    if spec.start_date is not None:
        parts.append(f"Dates: {spec.start_date} to {spec.end_date}")
    if spec.contexts:
        parts.append(f"Context logic: {spec.context_mode.upper()}")
    return "; ".join(parts) or "All records"


st.markdown('''<div class="page-header"><h1>Community Safety Resource Planner</h1>
<p>Explore where and when recorded offenses may warrant human review for non-enforcement resources.</p>
<span class="status-pill">Team Halo · DSO 576</span></div>''', unsafe_allow_html=True)
try:
    nibrs = load_nibrs_data()
except (FileNotFoundError, ValueError, OSError) as exc:
    st.error("The NIBRS dataset could not be loaded.")
    st.info("Prepare the team data using the README instructions, or set HALO_NIBRS_PATH to an existing dataset.")
    with st.expander("Data loading details"):
        st.code(str(exc))
    st.stop()

if nibrs.empty or nibrs["Date_Occurred"].dropna().empty:
    st.error("The NIBRS file has no records with valid occurrence dates. Check the input and cleaning report.")
    st.stop()

all_areas = options(nibrs["Area_Name"])
date_min = nibrs["Date_Occurred"].min().date()
date_max = nibrs["Date_Occurred"].max().date()
with st.sidebar:
    st.header("Explore records")
    st.caption("Filters apply to Current NIBRS Review.")
    st.button("Reset filters", on_click=reset_filters)
    areas = st.multiselect("Area", all_areas, default=all_areas,
                           key="filter_areas", on_change=clear_districts)
    district_source = nibrs[nibrs["Area_Name"].isin(areas)]
    district_options = sorted({district_key(v) for v in district_source["Report_District_No"].dropna()})
    districts = st.multiselect("Reporting district", district_options, key="filter_districts")
    use_dates = st.checkbox("Limit occurrence dates", key="filter_use_dates")
    dates = st.date_input("Occurrence date range", value=(date_min, date_max),
                         min_value=date_min, max_value=date_max,
                         key="filter_dates", disabled=not use_dates)
    days = st.multiselect("Day", list(DAY_ORDER), default=list(DAY_ORDER), key="filter_days")
    blocks = st.multiselect("Time-of-day block", list(TIME_OF_DAY_ORDER),
                            default=list(TIME_OF_DAY_ORDER), key="filter_blocks")
    offenses = st.multiselect("Offense", options(nibrs["NIBR Description"]), key="filter_offenses")
    premises = st.multiselect("Premise", options(nibrs["Premise_Description"]), key="filter_premises")
    contexts = st.multiselect("Context", ["transit", "domestic_violence", "homeless_victim",
                                         "street_sidewalk_parking"], key="filter_contexts")
    context_mode = st.radio("Context logic", ["OR", "AND"], horizontal=True, key="filter_context_mode")
    coords_only = st.checkbox("Valid coordinates only", key="filter_coordinates")
    st.caption("Coordinate selection affects the geographic coverage view only. Other totals stay unchanged.")

if use_dates and len(dates) != 2:
    st.info("Choose both a start and an end date.")
    st.stop()
if use_dates and dates[0] > dates[1]:
    st.error("Start date must be on or before end date.")
    st.stop()
spec = FilterSpec(areas=areas or None, districts=districts or None,
                  start_date=str(dates[0]) if use_dates else None,
                  end_date=str(dates[1]) if use_dates else None,
                  days=days or None, time_blocks=blocks if len(blocks) != 4 else None,
                  offenses=offenses or None, premises=premises or None,
                  contexts=contexts or None, context_mode=context_mode.lower(),
                  valid_coordinates_only=coords_only)
filtered = apply_filters(nibrs, spec)
# An explicitly cleared all-values widget means no records, not "all".
if not areas or not days:
    filtered = filtered.iloc[:0]
label = summary(spec)
st.caption(label)
st.info("Recorded offense rows are not population-adjusted risk. Resource cues can overlap; do not add their counts together.")
metrics = nibrs_headline_metrics(filtered)
cols = st.columns(4)
cols[0].metric("Selected offense rows", f"{metrics['selected_offense_rows']:,}")
cols[1].metric("Unique cases", f"{metrics['unique_cases']:,}")
cols[2].metric("Reporting districts", f"{metrics['reporting_districts']:,}")
cols[3].metric("Valid-coordinate coverage", f"{metrics['valid_coordinate_share']:.1%}", help=f"{metrics['valid_coordinate_rows']:,} valid-coordinate rows out of {len(filtered):,} selected rows")
st.caption(f"Source: {len(nibrs):,} rows · {NIBRS_PATH.name}. Unique cases exclude missing case IDs.")
if filtered.empty:
    st.warning("No records match these filters. Reset filters or broaden your selection.")
missing_dates = int(nibrs["Date_Occurred"].isna().sum())
old_dates = int((nibrs["Date_Occurred"] < pd.Timestamp("2000-01-01")).sum())
if old_dates:
    st.warning(f"The source retains {old_dates:,} occurrence dates before 2000. These are not silently corrected; use the date filter and consult Data Notes.")

overview, when, where, queue_tab, legacy_tab, notes = st.tabs([
    "Overview", "Time patterns", "Districts", "Review queue", "Legacy reference", "Data notes"])
with overview:
    st.subheader("Resource cues")
    st.caption("Each share uses all selected offense rows. One offense may carry more than one cue.")
    st.dataframe(context_cues(filtered).style.format({"share_of_selected_rows": "{:.1%}"}), hide_index=True)
    st.subheader("Premise summary")
    st.dataframe(premise_summary(filtered), hide_index=True)
with when:
    st.subheader("When were selected offenses recorded as occurring?")
    st.bar_chart(hourly_distribution(filtered).set_index("occurrence_hour")["offense_rows"])
    st.bar_chart(time_of_day_summary(filtered).set_index("time_of_day")["offense_rows"])
    heat = day_hour_matrix(filtered).pivot(index="day_name", columns="occurrence_hour", values="offense_rows")
    heat = heat.reindex(index=DAY_ORDER, columns=range(24), fill_value=0)
    st.dataframe(heat.style.background_gradient(cmap="Blues").format("{:,.0f}"))
    st.caption(f"{int(filtered['occurrence_hour'].isna().sum()):,} selected rows lack a valid hour and are excluded from time charts.")
with where:
    st.subheader("District activity")
    district_table = district_activity(filtered)
    st.dataframe(district_table.style.format({"share_of_selection": "{:.1%}", "valid_coordinate_share": "{:.1%}"}), hide_index=True)
    st.caption(f"{metrics['rows_missing_district']:,} selected rows have no district and are excluded from the district table.")
    st.subheader("Geographic coverage")
    geo = geographic_subset(filtered, coords_only)
    st.write(f"{len(geo):,} rows in the geographic subset; {len(filtered):,} remain in the headline denominator.")
    coverage = geo.groupby("Report_District_No", dropna=False).size().rename("geographic_rows").reset_index()
    st.dataframe(coverage, hide_index=True)
    st.caption("No individual coordinates or street addresses are displayed or exported.")
with queue_tab:
    st.subheader("Districts for human planning review")
    st.caption("Queue entries are snapshots of aggregate evidence when added. Changing filters does not alter saved entries. Re-add a district to update it.")
    candidates = build_review_queue(filtered, label)
    choices = [district_key(v) for v in candidates["Report_District_No"]]
    # Drop stale selections after any filter change.
    if "queue_add" in st.session_state:
        st.session_state.queue_add = [v for v in st.session_state.queue_add if v in choices]
    chosen = st.multiselect("Choose a district to add", choices, key="queue_add")
    queue = st.session_state.setdefault("queue", [])
    if st.button("Add selected district(s)", disabled=not chosen):
        by_id = {district_key(row["Report_District_No"]): row for row in candidates.to_dict("records")}
        for identifier in chosen:
            row = by_id.get(identifier)
            if row is None:
                continue
            row["Report_District_No"] = identifier
            row["added_at_utc"] = pd.Timestamp.now(tz="UTC").isoformat()
            queue[:] = [old for old in queue if district_key(old["Report_District_No"]) != identifier]
            queue.append(row)
        st.rerun()
    if queue:
        queue_frame = pd.DataFrame(queue)
        st.dataframe(queue_frame, hide_index=True)
        remove = st.multiselect("Districts to remove", [row["Report_District_No"] for row in queue], key="queue_remove")
        if st.button("Remove selected districts", disabled=not remove):
            queue[:] = [row for row in queue if row["Report_District_No"] not in remove]
            st.session_state.pop("queue_remove", None)
            st.rerun()
        export = queue_frame.copy()
        export["limitations"] = "Recorded offenses, not risk or causal evidence. Overlapping cues. Human review required."
        st.download_button("Download review queue CSV", export.to_csv(index=False).encode("utf-8"),
                           file_name="halo_review_queue.csv", mime="text/csv")
        if st.button("Clear review queue"):
            st.session_state.queue = []
            st.session_state.pop("queue_remove", None)
            st.rerun()
    else:
        st.caption("No districts added yet.")
with legacy_tab:
    st.subheader("Separate historical reference")
    st.caption("Legacy records have a different row grain. They are not merged with NIBRS or compared as a continuous trend. NIBRS date, offense and context filters do not apply here.")
    try:
        legacy = load_legacy_data()
    except (FileNotFoundError, ValueError, OSError):
        st.info("Historical data is not configured on this installation. The current NIBRS dashboard remains available.")
    else:
        legacy_areas = st.multiselect("Legacy area", options(legacy["Area_Name"]), key="legacy_areas")
        historical = legacy[legacy["Area_Name"].isin(legacy_areas)] if legacy_areas else legacy
        totals = legacy_headline_metrics(historical)
        st.metric("Legacy records", f"{totals['legacy_rows']:,}")
        st.line_chart(legacy_monthly_trend(historical).set_index("month")["legacy_rows"])
        st.dataframe(legacy_area_summary(historical), hide_index=True)
with notes:
    st.subheader("Read the numbers correctly")
    st.markdown("""
- **Offense rows:** records in the current filtered NIBRS table.
- **Unique cases:** distinct nonmissing case IDs; multiple offenses can belong to one case.
- **Cues:** contextual flags for planning review, not recommendations or proof that a resource will help.
- **Coverage:** valid-coordinate rows / all selected rows. The coordinate toggle never changes non-geographic totals.
- **Time blocks:** Overnight 00–05, Morning 06–11, Afternoon 12–17, Evening 18–23. Separated blocks remain separate.
- **Missing data:** retained; date/hour filters exclude rows missing that field. Missing districts are reported separately.
- **Limitations:** unreported harm, population, foot traffic, service availability and causal effects are not measured.
- **Review queue:** session-only aggregate snapshots; export before closing the browser.
""")
    st.write(f"Unparseable or missing source dates: {missing_dates:,}. Occurrence dates before 2000: {old_dates:,}.")
    manifest = ROOT / "data" / "manifest.json"
    if manifest.is_file():
        with st.expander("Data preparation and provenance"):
            st.json(manifest.read_text())
