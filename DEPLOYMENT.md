# Streamlit deployment

The privacy-limited Streamlit app entry point is `dashboard_public.py`. It uses
`public_nibrs_heatmap_aggregates.csv`, which contains only reporting district,
day name, hour, and aggregate offense-row counts.

The aggregate is created locally from the cleaned NIBRS file. Cells with fewer
than five rows are omitted before publication. Blank heatmap cells therefore
mean either zero or suppressed, and displayed totals are lower bounds. The
deployed app does not include case identifiers, victim demographics, exact
coordinates, addresses, or individual records.

Run the app from this directory with:

```powershell
python -m streamlit run dashboard_public.py
```

The full local dashboard remains `dashboard.py` and requires the complete
cleaned datasets. Do not deploy it with row-level data to a third-party host.
