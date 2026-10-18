"""Reusable backend analysis for the Community Safety Resource Planner.

The functions consume the cleaned CSV outputs created by
Complete_LAPD_Data_Cleaning(1).ipynb. NIBRS and legacy data intentionally stay
separate because their row grains and coding systems differ.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import pandas as pd


NIBRS_REQUIRED = {
    "CaseNo",
    "Date_Occurred",
    "Area_Name",
    "Report_District_No",
    "Premise_Description",
}
LEGACY_REQUIRED = {
    "DR_NO",
    "Date_Occurred",
    "Area_Name",
    "Report_District_No",
}
YES_NO_FIELDS = (
    "Transit-related Crime",
    "Domestic Violence Crime",
    "Homeless-Victim Crime",
)
DAY_ORDER = (
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
)
CONTEXTS = {
    "all",
    "transit",
    "domestic_violence",
    "homeless_victim",
    "street_sidewalk_parking",
}


@dataclass(frozen=True)
class FilterSpec:
    """Explicit, UI-independent filters for either cleaned dataset."""

    areas: Sequence[str] | None = None
    districts: Sequence[int] | None = None
    start_date: str | pd.Timestamp | None = None
    end_date: str | pd.Timestamp | None = None
    days: Sequence[str] | None = None
    day_types: Sequence[str] | None = None
    start_hour: int | None = None
    end_hour: int | None = None
    offenses: Sequence[str] | None = None
    premises: Sequence[str] | None = None
    context: str = "all"


def _require_columns(frame: pd.DataFrame, columns: Iterable[str], job: str) -> None:
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise ValueError(f"{job} requires missing column(s): {', '.join(missing)}")


def _as_bool(series: pd.Series) -> pd.Series:
    """Interpret common exported true values; missing values remain False."""
    if pd.api.types.is_bool_dtype(series.dtype):
        return series.fillna(False).astype(bool)
    return series.astype("string").str.strip().str.lower().isin({"true", "1", "yes", "y"})


def _yes(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.lower().eq("yes").fillna(False)


def load_clean_data(path: str | Path, dataset: str) -> pd.DataFrame:
    """Load and enrich one canonical cleaned CSV without modifying the source."""
    dataset = dataset.lower()
    if dataset not in {"nibrs", "legacy"}:
        raise ValueError("dataset must be 'nibrs' or 'legacy'")
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Cleaned {dataset} CSV not found: {path}")

    frame = pd.read_csv(path, low_memory=False)
    _require_columns(frame, NIBRS_REQUIRED if dataset == "nibrs" else LEGACY_REQUIRED,
                     f"Loading {dataset}")
    return enrich_data(frame, dataset)


def enrich_data(frame: pd.DataFrame, dataset: str) -> pd.DataFrame:
    """Return a copy with stable date, time, day, and context fields."""
    dataset = dataset.lower()
    required = NIBRS_REQUIRED if dataset == "nibrs" else LEGACY_REQUIRED
    _require_columns(frame, required, f"Enriching {dataset}")
    result = frame.copy()
    result["Date_Occurred"] = pd.to_datetime(result["Date_Occurred"], errors="coerce")

    if "occurrence_hour" not in result.columns:
        if "Time_Occurred" not in result.columns:
            result["occurrence_hour"] = pd.Series(pd.NA, index=result.index, dtype="Int64")
        else:
            hhmm = pd.to_numeric(result["Time_Occurred"], errors="coerce")
            valid = hhmm.between(0, 2359) & (hhmm % 100).between(0, 59)
            result["occurrence_hour"] = (hhmm // 100).where(valid).astype("Int64")
    else:
        hour = pd.to_numeric(result["occurrence_hour"], errors="coerce")
        result["occurrence_hour"] = hour.where(hour.between(0, 23)).astype("Int64")

    result["day_name"] = result["Date_Occurred"].dt.day_name()
    result["day_type"] = result["day_name"].map(
        lambda x: "Weekend" if x in {"Saturday", "Sunday"} else
        ("Weekday" if pd.notna(x) else pd.NA)
    ).astype("string")
    result["premise_group_street_sidewalk_parking"] = (
        result.get("Premise_Description", pd.Series(pd.NA, index=result.index, dtype="string"))
        .astype("string")
        .str.contains(r"street|sidewalk|parking", case=False, na=False)
    )
    if "valid_coordinates" in result.columns:
        result["valid_coordinates"] = _as_bool(result["valid_coordinates"])
    else:
        result["valid_coordinates"] = False
    return result


def _selected(values: Sequence | None) -> list:
    return [] if values is None else list(values)


def apply_filters(frame: pd.DataFrame, spec: FilterSpec, dataset: str = "nibrs") -> pd.DataFrame:
    """Return rows matching all supplied filters; never mutate the input."""
    dataset = dataset.lower()
    result = frame.copy()
    _require_columns(result, {"Date_Occurred", "Area_Name", "Report_District_No"}, "Filtering")

    if _selected(spec.areas):
        result = result[result["Area_Name"].isin(spec.areas)]
    if _selected(spec.districts):
        districts = pd.to_numeric(result["Report_District_No"], errors="coerce")
        result = result[districts.isin(spec.districts)]
    if spec.start_date is not None:
        result = result[result["Date_Occurred"] >= pd.Timestamp(spec.start_date)]
    if spec.end_date is not None:
        result = result[result["Date_Occurred"] < pd.Timestamp(spec.end_date) + pd.Timedelta(days=1)]
    if _selected(spec.days):
        result = result[result["day_name"].isin(spec.days)]
    if _selected(spec.day_types):
        result = result[result["day_type"].isin(spec.day_types)]
    if spec.start_hour is not None:
        result = result[result["occurrence_hour"].ge(spec.start_hour)]
    if spec.end_hour is not None:
        result = result[result["occurrence_hour"].le(spec.end_hour)]
    if _selected(spec.premises):
        _require_columns(result, {"Premise_Description"}, "Premise filtering")
        result = result[result["Premise_Description"].isin(spec.premises)]

    if _selected(spec.offenses):
        offense_column = _offense_column(result, dataset)
        result = result[result[offense_column].isin(spec.offenses)]

    if dataset == "nibrs":
        if spec.context not in CONTEXTS:
            raise ValueError(f"Unknown context {spec.context!r}; choose one of {sorted(CONTEXTS)}")
        context_masks = {
            "all": pd.Series(True, index=result.index),
            "street_sidewalk_parking": result["premise_group_street_sidewalk_parking"],
        }
        flag_map = {
            "transit": "Transit-related Crime",
            "domestic_violence": "Domestic Violence Crime",
            "homeless_victim": "Homeless-Victim Crime",
        }
        if spec.context in flag_map:
            field = flag_map[spec.context]
            _require_columns(result, {field}, f"Context filter {spec.context}")
            context_masks[spec.context] = _yes(result[field])
        result = result[context_masks[spec.context]]
    elif spec.context != "all":
        raise ValueError("Context filters are available only for NIBRS data")
    return result.copy()


def _offense_column(frame: pd.DataFrame, dataset: str) -> str:
    candidates = ("NIBR Description", "NIBR Code") if dataset == "nibrs" else (
        "Crime_Description", "Crime_Code"
    )
    for column in candidates:
        if column in frame.columns:
            return column
    raise ValueError(f"Offense analysis requires one of: {', '.join(candidates)}")


def _context_masks(frame: pd.DataFrame) -> Mapping[str, pd.Series]:
    _require_columns(frame, set(YES_NO_FIELDS) | {"premise_group_street_sidewalk_parking"},
                     "NIBRS context metrics")
    return {
        "street_sidewalk_parking": frame["premise_group_street_sidewalk_parking"].fillna(False),
        "transit_related": _yes(frame["Transit-related Crime"]),
        "domestic_violence": _yes(frame["Domestic Violence Crime"]),
        "homeless_victim": _yes(frame["Homeless-Victim Crime"]),
    }


def nibrs_headline_metrics(frame: pd.DataFrame) -> dict[str, int | float]:
    """Return denominator-safe headline metrics for filtered NIBRS rows."""
    _require_columns(frame, {"CaseNo", "Report_District_No", "valid_coordinates"},
                     "NIBRS headline metrics")
    rows = len(frame)
    valid = int(frame["valid_coordinates"].fillna(False).sum())
    return {
        "selected_offense_rows": rows,
        "unique_cases": int(frame["CaseNo"].nunique(dropna=True)),
        "reporting_districts": int(frame["Report_District_No"].nunique(dropna=True)),
        "valid_coordinate_rows": valid,
        "valid_coordinate_share": valid / rows if rows else 0.0,
        "rows_missing_district": int(frame["Report_District_No"].isna().sum()),
    }


def context_cues(frame: pd.DataFrame) -> pd.DataFrame:
    """Return the four resource-cue counts and shares using all selected rows."""
    denominator = len(frame)
    rows = []
    for cue, mask in _context_masks(frame).items():
        count = int(mask.sum())
        rows.append({"cue": cue, "count": count,
                     "share_of_selected_rows": count / denominator if denominator else 0.0})
    return pd.DataFrame(rows, columns=["cue", "count", "share_of_selected_rows"])


def district_activity(frame: pd.DataFrame) -> pd.DataFrame:
    """Aggregate selected NIBRS rows by reporting district."""
    _require_columns(frame, {"Report_District_No", "CaseNo", "valid_coordinates"},
                     "District activity")
    columns = [
        "Report_District_No", "offense_rows", "unique_cases", "share_of_selection",
        "valid_coordinate_rows", "valid_coordinate_share", "street_sidewalk_parking",
        "transit_related", "domestic_violence", "homeless_victim",
    ]
    usable = frame[frame["Report_District_No"].notna()].copy()
    if usable.empty:
        return pd.DataFrame(columns=columns)
    for name, mask in _context_masks(usable).items():
        usable[name] = mask.astype(int)
    result = usable.groupby("Report_District_No", dropna=False).agg(
        offense_rows=("CaseNo", "size"),
        unique_cases=("CaseNo", "nunique"),
        valid_coordinate_rows=("valid_coordinates", "sum"),
        street_sidewalk_parking=("street_sidewalk_parking", "sum"),
        transit_related=("transit_related", "sum"),
        domestic_violence=("domestic_violence", "sum"),
        homeless_victim=("homeless_victim", "sum"),
    ).reset_index()
    denominator = len(frame)
    result["share_of_selection"] = result["offense_rows"] / denominator if denominator else 0.0
    result["valid_coordinate_share"] = (
        result["valid_coordinate_rows"] / result["offense_rows"]
    ).fillna(0.0)
    return result[columns].sort_values(
        ["offense_rows", "Report_District_No"], ascending=[False, True]
    ).reset_index(drop=True)


def hourly_distribution(frame: pd.DataFrame) -> pd.DataFrame:
    """Return all 24 hours, including zero-count hours."""
    _require_columns(frame, {"occurrence_hour"}, "Hourly distribution")
    counts = frame["occurrence_hour"].dropna().astype(int).value_counts().reindex(range(24), fill_value=0)
    return counts.rename_axis("occurrence_hour").rename("offense_rows").reset_index()


def day_hour_matrix(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a complete seven-day by 24-hour tidy grid."""
    _require_columns(frame, {"day_name", "occurrence_hour"}, "Day-hour matrix")
    index = pd.MultiIndex.from_product([DAY_ORDER, range(24)], names=["day_name", "occurrence_hour"])
    counts = (
        frame.dropna(subset=["day_name", "occurrence_hour"])
        .assign(occurrence_hour=lambda x: x["occurrence_hour"].astype(int))
        .groupby(["day_name", "occurrence_hour"]).size()
        .reindex(index, fill_value=0)
        .rename("offense_rows").reset_index()
    )
    return counts


def premise_summary(frame: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Return top premises plus Other; missing descriptions are labeled Unknown."""
    _require_columns(frame, {"Premise_Description"}, "Premise summary")
    if top_n < 1:
        raise ValueError("top_n must be at least 1")
    labels = frame["Premise_Description"].astype("string").fillna("Unknown")
    counts = labels.value_counts(dropna=False)
    top = counts.head(top_n)
    rows = [{"premise": str(label), "offense_rows": int(count)} for label, count in top.items()]
    other = int(counts.iloc[top_n:].sum())
    if other:
        rows.append({"premise": "Other", "offense_rows": other})
    return pd.DataFrame(rows, columns=["premise", "offense_rows"])


def build_review_queue(frame: pd.DataFrame, filter_summary: str = "All records") -> pd.DataFrame:
    """Return aggregate-only district evidence suitable for a human review queue."""
    result = district_activity(frame).copy()
    if result.empty:
        return result.assign(filter_summary=pd.Series(dtype="string"), why_shown=pd.Series(dtype="string"))
    result["filter_summary"] = filter_summary
    result["why_shown"] = result.apply(
        lambda row: (
            f"{int(row.offense_rows)} selected offense rows; "
            f"{int(row.street_sidewalk_parking)} street/sidewalk/parking; "
            f"{int(row.transit_related)} transit-related; "
            f"{int(row.domestic_violence)} domestic-violence; "
            f"{int(row.homeless_victim)} homeless-victim."
        ), axis=1,
    )
    return result


def legacy_headline_metrics(frame: pd.DataFrame) -> dict[str, int]:
    _require_columns(frame, {"DR_NO", "Report_District_No"}, "Legacy headline metrics")
    return {
        "legacy_rows": len(frame),
        "unique_legacy_records": int(frame["DR_NO"].nunique(dropna=True)),
        "reporting_districts": int(frame["Report_District_No"].nunique(dropna=True)),
    }


def legacy_monthly_trend(frame: pd.DataFrame) -> pd.DataFrame:
    """Count legacy rows by month, inserting zero-count months inside the observed range."""
    _require_columns(frame, {"Date_Occurred"}, "Legacy monthly trend")
    dates = pd.to_datetime(frame["Date_Occurred"], errors="coerce").dropna()
    if dates.empty:
        return pd.DataFrame(columns=["month", "legacy_rows"])
    months = dates.dt.to_period("M").dt.to_timestamp()
    calendar = pd.date_range(months.min(), months.max(), freq="MS")
    counts = months.value_counts().sort_index().reindex(calendar, fill_value=0)
    return counts.rename_axis("month").rename("legacy_rows").reset_index()


def legacy_area_summary(frame: pd.DataFrame) -> pd.DataFrame:
    _require_columns(frame, {"Area_Name"}, "Legacy area summary")
    labels = frame["Area_Name"].astype("string").fillna("Unknown")
    return (
        labels.value_counts(dropna=False).rename_axis("Area_Name").rename("legacy_rows")
        .reset_index().sort_values(["legacy_rows", "Area_Name"], ascending=[False, True])
        .reset_index(drop=True)
    )


def offense_summary(frame: pd.DataFrame, dataset: str, top_n: int = 20) -> pd.DataFrame:
    """Return the most frequent available offense descriptions/codes."""
    if top_n < 1:
        raise ValueError("top_n must be at least 1")
    column = _offense_column(frame, dataset.lower())
    labels = frame[column].astype("string").fillna("Unknown")
    return (
        labels.value_counts(dropna=False).head(top_n).rename_axis("offense")
        .rename("rows").reset_index()
    )
