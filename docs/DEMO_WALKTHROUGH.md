# Draft team walkthrough — about 4 minutes

Record the real deployed app. Explain only behavior you have personally checked. Replace this outline with your own wording and divide speaking parts with the team; this draft does not represent completed narration or team agreement.

## 0:00–0:35 — User and decision

“This is Community Safety Resource Planner. Our intended user is a city or LAPD community-safety planner deciding which districts and time periods need further review for outreach, lighting, transit support or victim services. We turn recorded offenses into consistent, filterable summaries. The app supports human review; it does not automatically allocate resources.”

## 0:35–1:10 — Explain the default numbers

Open the app and show the source caption. On this snapshot, the default view contains 471,285 offense rows and 423,245 distinct nonmissing cases. Explain why one case can contain multiple offense rows. Explain coordinate coverage as valid rows divided by selected rows. Mention the snapshot ends in August 2026 and is not a live crime feed.

## 1:10–2:10 — Change filters and interpret results

Choose Central, then select Overnight and Evening only. Open Time patterns and show that the daytime hours are excluded. Point out that charts and counts use the same selection. Open Overview and explain one resource cue: its count and its share of the selected rows. Cues can overlap; do not add them as distinct populations.

## 2:10–2:55 — District review and export

Open Districts; explain offense rows, cases and share of selection. Open Review queue, choose one district and add it. Show its active filters and reason text, then download the aggregate CSV. Explain that this is a snapshot for human review, not an automatically justified resource allocation. Demonstrate removal.

## 2:55–3:35 — A difficult case and reset

Choose an area and a day/context combination that yields no records, or clear the Area selection to demonstrate the explicit empty state. Show the message and zero totals. Click Reset filters and verify the full counts return. Optionally show that toggling Valid coordinates only changes the geographic subset, not the common denominator.

## 3:35–4:10 — Limitations

Open Data notes. Explain that reported offenses are not all harm and counts lack population/exposure denominators. The source includes unusual historical dates; these are retained and warned about rather than silently corrected. Explain that additional data and human judgment are needed before deciding which resources to deploy.

## Before recording

- Use the public deployed URL and confirm no viewer sign-in is required.
- Rehearse the exact empty-state and queue flow once.
- Remove personal browser/email tabs from the recording frame.
- Check audio, readable labels, duration and the video link's viewer access.
- Do not describe the optional legacy view as working unless its data has been added and checked.
