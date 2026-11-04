"""Smoke-check the deployable entry point without any local cleaned CSVs."""
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest


def test_bundled_aggregate_startup_and_district_filter():
    root = Path(__file__).resolve().parent
    data = pd.read_csv(root / "public_nibrs_heatmap_aggregates.csv")
    assert data["published_offense_rows"].ge(5).all()
    app = AppTest.from_file(str(root / "dashboard_public.py")).run(timeout=30)
    assert not app.exception
    assert int(app.metric[0].value.replace(",", "")) == int(data.published_offense_rows.sum())
    district = int(data.Report_District_No.iloc[0])
    app.selectbox[0].select(district).run(timeout=30)
    assert not app.exception
    expected = data.loc[data.Report_District_No.eq(district), "published_offense_rows"].sum()
    assert int(app.metric[0].value.replace(",", "")) == int(expected)
    assert any("lower bounds" in item.value for item in app.caption)
