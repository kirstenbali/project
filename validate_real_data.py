"""Independent CSV recount and actual-app check for the team's full NIBRS snapshot."""
import csv
import json
from pathlib import Path
from streamlit.testing.v1 import AppTest

root=Path(__file__).resolve().parent
rows=0; cases=set(); late=0; valid=0
with (root/'data/raw/LAPD_NIBRS_Offenses_Dataset.csv').open(encoding='utf-8-sig',newline='') as f:
    for row in csv.DictReader(f):
        rows+=1
        case=row['CaseNo'].strip()
        if case:cases.add(case)
        try:
            hhmm=int(row['Time OCC']); hour=hhmm//100; minute=hhmm%100
            if 0<=hour<=23 and 0<=minute<=59 and (hour<=5 or hour>=18):late+=1
        except (ValueError,TypeError):pass
        try:
            if 33.5<=float(row['LAT'])<=34.9 and -119<=float(row['LON'])<=-117.5:valid+=1
        except (ValueError,TypeError):pass
app=AppTest.from_file(str(root/'dashboard.py')).run(timeout=60)
assert not app.exception,[e.message for e in app.exception]
def count(label):return int(next(m.value for m in app.metric if m.label==label).replace(',',''))
assert count('Selected offense rows')==rows
assert count('Unique cases')==len(cases)
next(w for w in app.multiselect if w.label=='Time-of-day block').set_value(['Overnight','Evening']).run(timeout=60)
assert not app.exception
assert count('Selected offense rows')==late
next(w for w in app.button if w.label=='Reset filters').click().run(timeout=60)
assert count('Selected offense rows')==rows
next(w for w in app.checkbox if w.label=='Valid coordinates only').check().run(timeout=60)
assert count('Selected offense rows')==rows
report={'input':'full team NIBRS snapshot','independent_method':'stdlib csv.DictReader, Python set and numeric comparisons; not app filter/groupby',
        'expected_rows':rows,'expected_unique_cases':len(cases),'expected_overnight_evening_rows':late,
        'expected_la_box_valid_rows':valid,'app_default_matches':True,'app_time_blocks_match':True,
        'app_reset_matches':True,'app_coordinate_toggle_preserves_denominator':True,
        'scope':'Full-data read and selected widget paths; not a complete external-source audit or deployed-site check'}
(root/'docs'/'validation-real-data.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
