from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st


DATA_PATH = Path(__file__).resolve().with_name("public_nibrs_heatmap_aggregates.csv")
DAY_ORDER = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
HOUR_ORDER = range(24)
MINIMUM_CELL_COUNT = 5
REQUIRED_COLUMNS = {
    "Report_District_No",
    "day_name",
    "occurrence_hour",
    "published_offense_rows",
}


@st.cache_data
def load_aggregates() -> pd.DataFrame:
    if not DATA_PATH.is_file():
        raise FileNotFoundError(f"Deployment aggregate data is missing: {DATA_PATH}")
    frame = pd.read_csv(DATA_PATH)
    missing = sorted(REQUIRED_COLUMNS - set(frame.columns))
    if missing:
        raise ValueError(f"Aggregate data is missing required columns: {', '.join(missing)}")
    if (frame["published_offense_rows"] < MINIMUM_CELL_COUNT).any():
        raise ValueError(
            f"Aggregate data contains cells below the {MINIMUM_CELL_COUNT}-row threshold."
        )
    return frame


st.set_page_config(page_title="Community Safety Resource Planner", layout="wide")
st.title("Community Safety Resource Planner")
st.caption("Privacy-limited, aggregate NIBRS review")
st.info(
    "This view reports aggregated offense rows for descriptive, non-enforcement planning. "
    "It is not a measure of population-adjusted risk and does not recommend resource allocation."
)

aggregates = load_aggregates()
districts = sorted(aggregates["Report_District_No"].dropna().astype(int).unique().tolist())
selected_district = st.selectbox("Reporting district", ["All districts", *districts])

if selected_district == "All districts":
    selected = aggregates
else:
    selected = aggregates[
        aggregates["Report_District_No"].astype(int) == int(selected_district)
    ]

counts = (
    selected.groupby(["day_name", "occurrence_hour"], as_index=False)["published_offense_rows"]
    .sum()
)
heatmap = (
    counts.pivot(index="day_name", columns="occurrence_hour", values="published_offense_rows")
    .reindex(index=DAY_ORDER, columns=HOUR_ORDER)
)

published_minimum = int(selected["published_offense_rows"].sum())
st.metric("Published offense-row minimum", f"{published_minimum:,}")
st.caption(
    "Each reporting-district/day/hour cell below 5 is suppressed. Blank heatmap cells mean "
    "zero or suppressed; shown totals sum only released cells and are lower bounds."
)

st.subheader("Day-by-hour heatmap")
st.dataframe(
    heatmap.style.background_gradient(cmap="Blues", axis=None).format("{:,.0f}", na_rep=""),
    width="stretch",
)

district_totals = (
    aggregates.groupby("Report_District_No", as_index=False)["published_offense_rows"]
    .sum()
    .sort_values(["published_offense_rows", "Report_District_No"], ascending=[False, True])
    .rename(columns={"published_offense_rows": "published_offense_row_minimum"})
)
st.subheader("Reporting-district activity")
st.bar_chart(district_totals.set_index("Report_District_No"))
st.dataframe(district_totals, width="stretch", hide_index=True)

with st.expander("Data notes and privacy limits"):
    st.markdown(
        """
        - The published file contains only reporting district, day name, hour, and aggregate counts.
        - Case identifiers, coordinates, addresses, victim demographics, and individual records are excluded.
        - Counts below 5 per district/day/hour cell are suppressed before publication.
        - Suppressed and zero-count cells are both blank; published totals are lower bounds.
        - This privacy-limited view does not support offense, premise, date-range, or individual-context filters.
        - Current and legacy records are not combined.
        """
    )
