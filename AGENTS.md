# Team Halo — Community Safety Resource Planner

## Project structure

Read README.md before working on this project. Put changes in the corresponding files and folders:
- dashboard.py: Streamlit interface and interactions.
- backend_analysis.py: reusable analysis and business rules.
- prepare_data.py: reproducible data preparation.
- tests in test_*.py files: checks for the relevant behavior.
- docs/: project documentation.

Do not copy and paste reusable code. Extract shared logic into a suitable utility module and import it where needed. Keep interface code separate from calculations.

## Design rules

Use USC Trojan cardinal and gold as the design palette. Keep text readable, maintain sufficient contrast, and use consistent styling across the dashboard.

## Writing style

Use clear, direct language with concrete descriptions. Avoid repetitive AI writing patterns, especially “it's not X, it's Y” constructions and excessive em dashes.

## Data and verification

Preserve source data and document transformations. Keep offense rows distinct from unique cases. Explain missing data and limitations in plain language.

Run the tests relevant to each calculation or interaction changed. Report actual results and any remaining limitations. Never change expected test results merely to make a test pass.

Keep credentials out of source code. Follow the existing README instructions for local running and deployment.
