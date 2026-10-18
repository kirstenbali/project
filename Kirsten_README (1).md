# Community Safety Resource Planner - Module 6 Data Cleaning

## Author

Kirsten Bali  
USC DSO 576 - Module 6

Branch Name: cleaning-kirstenbali

Branch URL: https://github.com/iyannab562/dso576-project/tree/cleaning-kirstenbali

Commit ID: 9cefad7395917a343c6eae1e0ce255a95181be4c


## Project purpose

This project cleans and validates LAPD offense data for a dashboard that helps users examine recorded offenses by area, reporting district, time, premise, and clearly defined context fields. The dashboard is intended to support human review of possible non-enforcement safety resources. It does not predict individual behavior, create individual risk scores, or recommend enforcement action.

## Data sources and versions

### Primary dataset

- **Name:** LAPD NIBRS Offenses Dataset
- **Source:** Los Angeles Police Department data supplied for the DSO 576 course project
- **File:** `LAPD_NIBRS_Offenses_Dataset.csv`
- **Dataset copy received:** September 22, 2026
- **Size of supplied copy:** 471,285 rows and 31 columns
- **Role in this submission:** Primary dataset cleaned and validated in the notebook

### Secondary dataset

- **Name:** Crime Data from 2020 to 2024
- **Source:** Los Angeles Police Department data supplied for the DSO 576 course project
- **File:** `Crime_Data_from_2020_to_2024.csv`
- **Dataset copy received:** September 22, 2026
- **Size of supplied copy:** 1,004,894 rows and 28 columns
- **Role in this submission:** Retained as a separate historical dataset. It is not merged with the NIBRS data because the offense-code and premise-category crosswalk has not yet been validated.

The received date identifies the version of the files used for this assignment. If the files are downloaded again from the public data portal, record the new retrieval date because the row counts and values may change.

## Source preservation and access instructions

1. Obtain the two original CSV files from the course project materials or the LAPD open-data source used by the project team.
2. Place the files in `data/raw/` using the exact filenames shown below:

   ```text
   data/raw/LAPD_NIBRS_Offenses_Dataset.csv
   data/raw/Crime_Data_from_2020_to_2024.csv
   ```

3. Do not edit either original CSV manually.
4. The notebook loads the original NIBRS file into pandas and performs cleaning on a copy of the DataFrame.
5. Cleaned datasets and validation evidence are written to separate output folders. The raw files are never overwritten.

If the data cannot be included in the submission because of file-size limits, obtain the original files from the project team's approved course or LAPD data source, place them in `data/raw/`, and then rerun the notebook.


## How to run the notebook in Jupyter

1. Open a terminal in the project folder.
2. Start JupyterLab:

   ```bash
   jupyter lab
   ```

   Jupyter Notebook can be used instead:

   ```bash
   jupyter notebook
   ```

3. Open `Kirsten_DataCleaning.ipynb`.
4. Confirm that both original CSV files are present in `data/raw/`.
5. In JupyterLab, select **Kernel > Restart Kernel and Run All Cells**.
6. In classic Jupyter Notebook, select **Kernel > Restart & Run All**.
7. Confirm the restart when prompted.
8. Allow every cell to run from top to bottom without manually changing intermediate values.
9. Check that no cell ends with an error and that the expected output files are recreated.

Restarting the kernel clears variables left over from earlier work. Running all cells from the beginning demonstrates that the results can be reproduced from the original data without manual spreadsheet edits.

## Expected output files

After a successful run, the following files should be created:

| Output file | Purpose |
|---|---|
| `cleaned_NIBRS_sample.csv` | These are 50 cleaned rows of the NIBRS dataset. I chose them because they demostrate that the cleaning rules work properly. These include flag values such as, missing latitude or longitude, the time reported before the time occurred, coordinates equal to zero, coordinates outside broad Los Angeles boundaries, missing premise descriptions, missing weapon descriptions, repeated CaseNo values with different UniqueNIBRNo values, unusually high victim counts, missing report dates, and missing NIBR offense codes|
| `cleaned_Legacy_sample.csv` | These are 50 cleaned rows of the Legacy dataset. Just like the primary dataset, I chose those 50 rows from the Legacy dataset because they demostrate that the cleaning rules work properly. These include flag values such as, missing latitude or longitude, coordinates equal to zero, and missing codes and descriptions. |

The supplied NIBRS file should produce these central reconciliation results under the documented rules:

- Starting rows: 471,285
- Exact duplicate rows: 0
- Unique `UniqueNIBRNo` values: 471,285
- Rows removed: 0
- Final rows: 471,285

Suspicious or missing values are retained and flagged when a defensible correction cannot be inferred.

## Cleaning and validation overview

The notebook performs the following work:

- Preserves the original source files.
- Converts occurrence and report dates using an explicit date format.
- Validates `Time OCC` as an HHMMSS value.
- Removes leading and trailing whitespace from text fields.
- Preserves official descriptions, codes, identifiers, and meaningful capitalization.
- Checks the Yes/No context fields for unexpected categories.
- Evaluates exact duplicates separately from repeated case numbers.
- Retains justified missing values rather than inventing replacements.
- Validates latitude, longitude, victim counts, LAPD area codes, and reporting district codes.
- Flags suspicious values for review instead of automatically deleting them.
- Reconciles starting and final row counts.

## Known limitations

Recorded offenses do not measure unreported incidents, population exposure, service availability, or program impact. Missing and zero coordinates reduce map coverage. Suspicious historical dates cannot be corrected without additional source information. The NIBRS and legacy datasets remain separate until the offense and premise mappings are validated. Dashboard results should be aggregated and used for human planning review, not individual-level conclusions.
