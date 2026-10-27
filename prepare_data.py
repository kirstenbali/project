"""Build compact app inputs from the team's original CSV snapshots.

Run: python prepare_data.py --nibrs data/raw/LAPD_NIBRS_Offenses_Dataset.csv
Optionally add --legacy data/raw/Crime_Data_from_2020_to_2024.csv.
Preserves all rows, records source hashes, and omits addresses/exact coordinates.
"""
import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd
from backend_analysis import load_clean_data, nibrs_headline_metrics

ROOT = Path(__file__).resolve().parent


def prepare(path, dataset):
    frame = load_clean_data(path, dataset)
    before = len(frame)
    for col in frame.select_dtypes(include=['object','string']).columns:
        frame[col] = frame[col].astype('string').str.strip().str.replace(r'\s+', ' ', regex=True)
        frame[col] = frame[col].mask(frame[col].eq(''), pd.NA)
    # Same approximate Los Angeles coordinate box used by the team's cleaning notebook.
    # This is a screening flag, not an administrative-boundary test.
    lat = pd.to_numeric(frame['LAT'], errors='coerce')
    lon = pd.to_numeric(frame['LON'], errors='coerce')
    frame['valid_coordinates'] = lat.between(33.5,34.9) & lon.between(-119.0,-117.5)
    original_metrics = nibrs_headline_metrics(frame) if dataset=='nibrs' else None
    columns = ['CaseNo' if dataset=='nibrs' else 'DR_NO','Date_Occurred',
               'Area_Name','Report_District_No','Premise_Description','occurrence_hour',
               'valid_coordinates']
    columns += (['NIBR Description','Transit-related Crime','Domestic Violence Crime',
                 'Homeless-Victim Crime'] if dataset=='nibrs' else ['Crime_Description'])
    compact=frame[columns].copy()
    key='CaseNo' if dataset=='nibrs' else 'DR_NO'
    # Equality-preserving pseudonyms support distinct counts; no original case IDs ship with the app.
    compact[key] = compact[key].map(lambda v: hashlib.sha256(str(v).encode()).hexdigest() if pd.notna(v) else None)
    for col in ['Area_Name','Report_District_No','Premise_Description','NIBR Description',
                'Crime_Description','Transit-related Crime','Domestic Violence Crime','Homeless-Victim Crime']:
        if col in compact:
            compact[col]=compact[col].astype('category')
    output=ROOT/'data'/f'{dataset}.parquet'
    output.parent.mkdir(exist_ok=True)
    compact.to_parquet(output,index=False,compression='zstd')
    assert len(compact)==before
    if dataset=='nibrs':
        assert nibrs_headline_metrics(compact)==original_metrics
    hasher=hashlib.sha256()
    with Path(path).open('rb') as source:
        for chunk in iter(lambda:source.read(1024*1024),b''):hasher.update(chunk)
    return {
        'source_filename':Path(path).name,'source_sha256':hasher.hexdigest(),
        'source_rows':before,'output_rows':len(compact),'output_bytes':output.stat().st_size,
        'date_min':str(frame.Date_Occurred.min()),'date_max':str(frame.Date_Occurred.max()),
        'missing_dates':int(frame.Date_Occurred.isna().sum()),
        'dates_before_2000':int((frame.Date_Occurred<pd.Timestamp('2000-01-01')).sum()),
        'valid_coordinate_rows':int(compact.valid_coordinates.sum()),
        'headline_metrics':original_metrics,
        'rules':['Preserve all rows; no merge or deduplication',
                 'Trim/collapse text whitespace; retain missing values',
                 'Parse occurrence dates and validate HHMM; retain invalids as missing',
                 'Coordinate screening: latitude 33.5–34.9, longitude -119.0–-117.5',
                 'Retain historical occurrence dates; warn in app',
                 'Remove exact coordinates, locations and personal attributes',
                 'Replace case identifiers with SHA-256 equality-preserving pseudonyms'],
        'source_folder':'https://drive.google.com/drive/folders/13klDDs4FziK34Z1WlA5TKu5uW5RT2uMU'
    }


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--nibrs',required=True,type=Path)
    parser.add_argument('--legacy',type=Path)
    args=parser.parse_args()
    manifest={'nibrs':prepare(args.nibrs,'nibrs')}
    if args.legacy:manifest['legacy']=prepare(args.legacy,'legacy')
    (ROOT/'data'/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))
