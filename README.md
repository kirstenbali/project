# Community Safety Resource Planner

A Streamlit dashboard for reviewing LAPD recorded-offense patterns and
aggregated district activity for non-enforcement planning.

## Run locally

Install dependencies and place the two input CSVs next to `dashboard.py`:

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
4. Configure access to both input CSVs before deploying. The app currently
   expects them alongside `dashboard.py`; the large data files are not stored
   in this repository. Do not commit the raw CSVs to GitHub.

The app cannot finish loading until the external data source is configured and
the dashboard loader is pointed to it.

## Run analysis tests

```powershell
python -m pytest -q
```
