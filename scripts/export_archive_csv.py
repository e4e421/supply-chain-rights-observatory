#!/usr/bin/env python3
"""Generate an Excel-safe, UTF-8 CSV from the canonical monthly public JSONL archive.

Does not store personal data. Defaults to a local file under /tmp, never commits
generated CSV to the public repository. Columns are stable English identifiers.
"""
from __future__ import annotations
import argparse,csv,json,sys
from pathlib import Path
from archive_data import ARCHIVE,load_partition,build_manifest

COLUMNS=('record_id','event_id','title','published_at','first_seen','source','source_id',
         'kind','evidence_status','topics','url','doi','record_fingerprint')

def safe_cell(value):
    if value is None: return ''
    if isinstance(value,list): value='; '.join(map(str,value))
    value=''.join(' ' if ord(c)<32 or ord(c)==127 else c for c in str(value))
    if value.lstrip().startswith(('=','+','-','@')): return "'"+value
    return value

def export(destination):
    manifest=build_manifest()
    dest=Path(destination).resolve()
    if ARCHIVE.resolve()==dest or ARCHIVE.resolve() in dest.parents:
        raise ValueError('Refusing to write CSV into the canonical archive tree')
    if dest.exists() and dest.is_symlink():
        raise ValueError('Refusing to overwrite symbolic link')
    dest.parent.mkdir(parents=True,exist_ok=True)
    rows=0
    with dest.open('w',encoding='utf-8-sig',newline='') as out:
        writer=csv.writer(out,quoting=csv.QUOTE_MINIMAL)
        writer.writerow(COLUMNS)
        for path in sorted(ARCHIVE.glob('????-??.jsonl')):
            for record in load_partition(path):
                writer.writerow([safe_cell(record.get(k)) for k in COLUMNS])
                rows+=1
    if rows!=manifest['total_records']:
        raise ValueError('CSV count mismatch against archive manifest')
    print(f'CSV export: {rows} metadata records -> {dest}')
    return rows

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default='/tmp/scro-public-archive.csv',
                        help='Local export path outside versioned archive')
    args=parser.parse_args()
    export(args.output)
