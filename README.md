# Community Safety Resource Planner

A Streamlit dashboard for reviewing LAPD recorded-offense patterns and
aggregated district activity for non-enforcement planning.

## Run locally

Install dependencies. When both input CSVs are next to `dashboard.py`, the app
loads them automatically:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run dashboard.py --server.port 8502
```

The required files are `LAPD_NIBRS_Offenses_Dataset.csv` and
`Crime_Data_from_2020_to_2024.csv`. Counts describe recorded rows; they are not
population-adjusted rates, risk scores, or causal evidence. Exact coordinates
and street addresses are not displayed.

## Deploy on Streamlit Community Cloud

1. Connect the GitHub repository and select the branch to deploy.
2. Set the app file path to `dashboard.py`.
3. Streamlit Cloud installs packages from `requirements.txt`.
4. The large input CSVs are not stored in this repository. When the deployed
   app starts without local CSVs, upload both files in the sidebar. Each upload
   can be up to 200 MB. The files are read by the running app and are not
   committed to GitHub.

The uploaded files are held in app memory and Streamlit's app cache. Re-upload
both files if the app restarts or the cache is cleared. For larger datasets or
frequent use, configure durable external storage instead.

## Run analysis tests

```powershell
python -m pytest -q
```
