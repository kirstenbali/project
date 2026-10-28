"""Run the team's actual notebook transformations and save aggregate evidence.

Original files are read only. No individual records are exported.
"""
import argparse
import hashlib
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
NOTEBOOK = ROOT / 'Complete_LAPD_Data_Cleaning (1).ipynb'


def reconcile(paths):
    notebook = json.loads(NOTEBOOK.read_text())
    sources = {i: ''.join(c['source']) for i,c in enumerate(notebook['cells'])}
    result = {'notebook': NOTEBOOK.name,
              'notebook_sha256': hashlib.sha256(NOTEBOOK.read_bytes()).hexdigest(),
              'transformation_cells': [8,10,12,14,16,18],
              'datasets': [], 'quality_checks': []}
    for name,path in paths.items():
        requested = ['UniqueNIBRNo','CaseNo','Status','RPT Dist No'] if name=='nibrs' else ['DR_NO','Status','Rpt Dist No','Crm Cd 1','Crm Cd 2','Crm Cd 3','Crm Cd 4']
        columns = pd.read_csv(path, nrows=0).columns
        raw = pd.read_csv(path, dtype={c:'string' for c in requested if c in columns}, low_memory=False)
        key = 'UniqueNIBRNo' if name=='nibrs' else 'DR_NO'
        before_missing = int(raw[key].isna().sum())
        before_duplicates = int(raw.duplicated().sum())
        clean = {name: raw.copy(deep=True)}
        # Cell 10 explicitly addresses NIBRS flags; an empty frame lets it run
        # unchanged when reconciling legacy separately to bound memory use.
        clean.setdefault('nibrs', pd.DataFrame(columns=pd.Index([], dtype='str')))
        clean.setdefault('legacy', pd.DataFrame(columns=pd.Index([], dtype='str')))
        ns = {'pd':pd, 'raw':{name:raw}, 'clean':clean, 'display':lambda *a:None}
        for cell in [8,10,12,14,16,18]:
            exec(compile(sources[cell], f'{NOTEBOOK.name}:cell-{cell}', 'exec'), ns)
        cleaned = ns['clean'][name]
        assert len(cleaned)==len(raw)
        assert int(cleaned[key].isna().sum())==before_missing
        row = ns['reconciliation'].iloc[0].to_dict()
        row.update({'source_filename':path.name,
                    'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                    'exact_duplicate_rows_before':before_duplicates,
                    'exact_duplicate_rows_after':int(cleaned.duplicated().sum()),
                    'missing_keys_before':before_missing,
                    'missing_keys_after':int(cleaned[key].isna().sum())})
        result['datasets'].append(row)
        result['quality_checks'].extend(ns['quality_summary'].query('dataset == @name').to_dict('records'))
        print(json.dumps(row), flush=True)
        del raw,cleaned,clean,ns
    output = ROOT / 'data' / 'cleaning_reconciliation.json'
    output.write_text(json.dumps(result, indent=2, default=int)+'\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--nibrs',type=Path,required=True)
    parser.add_argument('--legacy',type=Path)
    args=parser.parse_args()
    paths={'nibrs':args.nibrs}
    if args.legacy: paths['legacy']=args.legacy
    reconcile(paths)
