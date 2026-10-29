# Streamlit deployment

## Deploy the aggregate app

Open https://share.streamlit.io/ and choose **Create app**, then enter:

| Setting | Value |
| --- | --- |
| Repository | `kirstenbali/project` |
| Branch | `main` |
| Main file path | `dashboard_public.py` |
| Python version | `3.12` |

Use these settings after the deployment dependency fix has been merged into `main`.
To test the fix before merging, select `codex/fix-public-deployment` instead.
The requirements include Matplotlib because pandas uses it to color the heatmap.

If the local dashboard's Deploy button says `dashboard.py` has not been pushed,
create the app directly on Community Cloud using the settings above. The local
shortcut's repository/branch detection is separate from choosing the files on
GitHub. Do not paste a localhost URL into the deployment form.

The aggregate CSV is already committed alongside this entry point; it does not
need the large cleaned CSVs on your laptop. Test the deployed URL without signing
in before submitting it.

## Choose the intended dashboard

The full Team Halo MVP, including the geographic LA heatmap, date/hour filters,
and cleaning reconciliation, is on branch `codex/halo-mvp-ready`, with entry point
`dashboard.py` and bundled `data/nibrs.parquet`. That is a different version from
the aggregate app described here. It contains record-level project data and needs
an explicit team decision about hosted data before publishing.

The aggregate app below has only district/day/hour counts. It cannot reproduce
the full MVP or meet the professor's geographic-map/date-filter feedback by itself.

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
