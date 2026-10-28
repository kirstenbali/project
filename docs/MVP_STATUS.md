# Phase 3 readiness

## Implemented in this branch

- Restore all filter widget defaults through a reset callback (SE09-01).
- Preserve the union of separated time blocks (CR-002 / historical CR-VH-01).
- Keep coordinate validity out of non-geographic denominators (YJ09-03).
- Preserve reporting-district IDs consistently across selection, lookup and queue storage (CR-VH-02).
- Add queue removal, clearing and aggregate CSV export; re-adding a district refreshes its snapshot without duplication.
- Keep the main app available without the optional legacy dataset. Legacy filters are separate from NIBRS.
- Handle empty selections and missing/invalid data without crashing; report exclusions.
- Bundle the full team NIBRS snapshot in a compact representation without original IDs, addresses or exact coordinates.
- Provide reproducible preparation, a source manifest, dependencies and automated regression/full-data checks.

The original change-request log is retained as historical audit evidence. Fixes are not part of main until this branch is reviewed and merged. Steven's original audit is still labeled AI-assisted with personal review pending; no personal review or team approval is claimed here.

## Verified locally

Nine automated tests pass. Full-data independent recount and actual widget tests confirm 471,285 offense rows, 423,245 unique cases, 470,605 coordinate-valid rows under the team's LA box, and 222,983 Overnight + Evening rows. Reset restores the full selection; the coordinate toggle preserves the common denominator. See validation-real-data.json.

## Must finish before submission

1. Review the changes and reconcile the branch with teammates. No roles, meetings or consent were invented.
2. Review the retained pre-2000 dates and agree whether to restrict the project's default period. This branch preserves the existing full-file scope transparently.
3. Obtain/prepare the optional full legacy CSV if the team wants to demonstrate Legacy Reference. It is currently not bundled or verified.
4. Deploy to an approved host; verify that the instructor can open the live app without signing in.
5. Record a 3–6 minute team walkthrough of the actual app, using the draft script as a guide. Upload it to a viewable destination and verify the link.
6. Add the verified live-app and video links to README.
7. Submit the live app, demo video and repository links as ONE team submission on Gradescope by November 9, 2026, 11 a.m. Pacific. Keep the app live through peer review.

The separate individual self/teammate performance review is a PDF due November 16, 11 a.m. Pacific. It must be written independently.
