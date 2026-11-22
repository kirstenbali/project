# Phase 5 offense filter review

## Review instructions (PORTS)

- **Purpose** — Address the Phase 3 feedback about unreadable offense labels.
- **Outputs** — Propose a display change, identify edge cases, and give a way to verify that filter results stay correct.
- **Rules** — Keep raw values as filter keys. Leave blank options out of the list. Keep distinct choices distinguishable.
- **Tools** — Use Claude and Grok to review the proposal, then Python, PyArrow and Streamlit AppTest to independently verify it.
- **Sources** — Use the Phase 3 instructor feedback, Phase 5 handout, `dashboard.py`, and `data/nibrs.parquet`.

## What changed

Both reviewers suggested retaining the existing filter keys and displaying cleaner names. Grok suggested that duplicate visible names could coexist if the keys differed. AppTest exposes the formatted labels as the widget options, so the implementation uses a short qualifier to distinguish duplicates, as Claude suggested.

In the current NIBRS sidebar, the main description appears first. Statute and charge details appear when needed to tell similarly named offenses apart. The filter still returns the same recorded offense rows for a given selection.

## Evidence

- `test_mvp.py::test_readable_offense_labels_keep_exact_filter_matches` exercises duplicate descriptions, a missing description, an exact selection, and reset.
- The bundled snapshot has 471,285 rows and 2,356 selectable descriptions. All 2,356 visible options are unique.
- Independent counts from the bundled Parquet match the app for Robbery (14,932) and Grand Theft Auto (29,681).
- After integration, verify the same selections in the deployed app and link the live results in the team response letter.
