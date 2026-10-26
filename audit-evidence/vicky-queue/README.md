# Vicky Huang: active audit CR-VH-02

Vicky's active individual topic is adding districts to Review queue and verifying district `offense_rows`. Earlier time-block evidence in the parent folder remains historical support for CR-002; it was not deleted and the underlying issue was not marked resolved.

## Reproduce

From the team app root, with pandas, Streamlit, and matplotlib installed:

```bash
python -B audit-evidence/vicky-queue/queue_audit_check.py --project . --out queue-audit-recheck.json
```

No production CSV is needed. The script supplies four invented rows at the data-loader boundary and drives the unchanged dashboard through Streamlit AppTest. It does not modify the dashboard, backend, teammate files, or production data. The recorded app source matches commit `53645eff24eb73d9c80159f68bf03104fbeb8058`; repository state checked was `b8566aabb593d98bb9c90f061483a8d4fa807ad8`.

## Evidence

- Districts `0101,0101,0101,0102`, CaseNo values `A,A,B,C`, same date/area and otherwise default controls.
- Independent Python Counter and backend/table counts agree: 3 offense rows for 0101 and 1 for 0102.
- Select the actual dropdown option `101` and click Add selected district(s): the padded-string case raises an IndexError and leaves the queue empty.
- The same records with plain string or integer district IDs add one queue entry with 3 offense rows. Repeated Add does not create a duplicate in those controls.
- Five district-count checks pass, including a missing CaseNo, removed offense row, active-hour restriction, and empty selection. All five original backend tests pass.

`queue-audit-results.json` records expected/actual outcomes, actual widget exceptions and queue state, the synthetic fixture, code hashes, and runtime versions. A successful checker run means the original failure and controls were reproduced; the application has not been repaired. These are controlled checks, not a measurement of production prevalence or proof for every identifier format.

AI assisted with test design/execution, source inspection, evidence recording, and writing. Vicky's interpretation is that changing an identifier's representation does not change the district entity or its record count.
