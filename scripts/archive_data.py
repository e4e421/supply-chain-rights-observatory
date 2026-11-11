#!/usr/bin/env python3
"""Append-only public research leads in monthly JSONL files; never a private research database.

The archive stores public publication metadata. A validated
immutable snapshot is written at first sight; corrections need explicit review.
"""
from __future__ import annotations
import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from source_urls import public_record_url

ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=ROOT/'data'/'archive'
MANIFEST=ARCHIVE/'manifest.json'
PUBLIC_SUMMARY=ROOT/'docs'/'data'/'archive-summary.json'
HEX_ID=re.compile(r'^[0-9a-f]{18}$')
RECORD_KEYS=('id','kind','title','url','published_at','first_seen','source','source_id',
             'evidence_status','topics','description','doi','discovery_query_id',
             'publisher_hint','publisher_verified','canonical_url','screening_version',
             'screening_status','screening_reason','publisher_provenance',
             'retrieved_at','pipeline_version','original_language')
MAX_LINE_BYTES=8000
MAX_TOTAL_RECORDS=250000
PUBLIC_STATUS={'Unverified discovery','Bibliographic record'}

LEGACY_DESCRIPTIONS={
 '自動發現的新聞聚合線索；請追溯原始新聞與獨立佐證，不代表人權違規已獲證實。':'News lead collected from a public feed.',
 'Crossref 出版書目資料；DOI 與日期須核對出版商，研究方法與同儕審查狀態尚未人工查證。':'Crossref bibliographic record. Verify DOI and publication date with the publisher; methods and peer-review status have not been independently reviewed.'
}

def english_source_name(item):
    """Normalize existing Chinese labels to the English canonical feed names."""
    if not hasattr(english_source_name,'_names'):
        try:
            config=json.loads((ROOT/'sources'/'queries.json').read_text(encoding='utf-8'))
            english_source_name._names={row['id']:row['name'] for row in config['news_queries']+config['academic_queries']}
        except (OSError,ValueError,KeyError,TypeError):
            english_source_name._names={}
    source=english_source_name._names.get(item.get('source_id'))
    if source:
        return ('Crossref · ' if item.get('kind')=='academic' else '')+source
    return item.get('source','Unknown source')

def json_line(record):
    return json.dumps(record,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n'

def secure_record(item,now):
    if not isinstance(item,dict) or not HEX_ID.fullmatch(str(item.get('id',''))):
        raise ValueError('Invalid stable record id')
    if item.get('kind') not in ('academic','discovery') or item.get('evidence_status') not in PUBLIC_STATUS:
        raise ValueError('Unexpected evidence category')
    if not isinstance(item.get('title'),str) or not 0<len(item['title'])<=240:
        raise ValueError('Invalid title')
    if not public_record_url(item.get('url'),item.get('source_id')):
        raise ValueError('Untrusted archive URL')
    if not isinstance(item.get('topics'),list) or len(item['topics'])>12:
        raise ValueError('Invalid topic list')
    first=item.get('first_seen') or now
    try: stamp=datetime.fromisoformat(first.replace('Z','+00:00'))
    except (TypeError,ValueError,AttributeError) as exc: raise ValueError('Invalid first_seen') from exc
    if stamp.tzinfo is None or stamp.year<2020 or stamp.year>2100:
        raise ValueError('Out-of-bounds first_seen')
    row={key:item[key] for key in RECORD_KEYS if key in item}
    row['first_seen']=first
    row['source']=english_source_name(item)
    row['description']=LEGACY_DESCRIPTIONS.get(row.get('description'), row.get('description',''))
    row['record_id']=row.pop('id')
    row['event_id']=None  # No unreviewed allegation-to-event inference.
    row['archive_schema_version']=1
    row['capture_type']='public_metadata_only'
    row['record_fingerprint']=hashlib.sha256(
        json.dumps({'kind':row['kind'],'url':row['url'],'title':row['title'].casefold(),
                    'doi':row.get('doi')},sort_keys=True,ensure_ascii=False).encode('utf-8')
    ).hexdigest()
    if len(json_line(row).encode('utf-8'))>MAX_LINE_BYTES: raise ValueError('Record exceeds archive limit')
    return row

def partition(row):
    dt=datetime.fromisoformat(row['first_seen'].replace('Z','+00:00'))
    return f'{dt.year:04d}-{dt.month:02d}.jsonl'

def load_partition(path):
    records=[]
    if not path.exists(): return records
    if path.is_symlink() or path.stat().st_size>60_000_000: raise ValueError('Unsafe archive partition')
    with path.open(encoding='utf-8') as handle:
        for line in handle:
            if not line.strip(): continue
            if len(line.encode('utf-8'))>MAX_LINE_BYTES: raise ValueError('Oversized line')
            row=json.loads(line)
            if not isinstance(row,dict) or not HEX_ID.fullmatch(str(row.get('record_id',''))):
                raise ValueError('Malformed archive record')
            if row.get('event_id') is not None: raise ValueError('Unreviewed event ID in archive')
            records.append(row)
    return records

def build_manifest(now=None):
    by_id={}
    partitions=[]
    for path in sorted(ARCHIVE.glob('????-??.jsonl')):
        rows=load_partition(path)
        for row in rows:
            rid=row['record_id']
            if rid in by_id: raise ValueError(f'Duplicate archived record ID: {rid}')
            if partition(row)!=path.name: raise ValueError('Record in wrong monthly partition')
            if len(by_id)>=MAX_TOTAL_RECORDS: raise ValueError('Archive exceeds configured record capacity')
            by_id[rid]=row['record_fingerprint']
        content=path.read_bytes()
        partitions.append({'file':path.name,'records':len(rows),'sha256':hashlib.sha256(content).hexdigest(),
                           'bytes':len(content)})
    return {'schema_version':1,'format':'jsonl-monthly','public_metadata_only':True,
            'total_records':len(by_id),'partition_count':len(partitions),
            'partitions':partitions,'event_linkage':'manual_review_only'}

def persist(records, now):
    """Idempotent merge: append only never-before-seen metadata; reject hash collisions."""
    ARCHIVE.mkdir(parents=True,exist_ok=True)
    existing={}
    for path in sorted(ARCHIVE.glob('????-??.jsonl')):
        for row in load_partition(path):
            rid=row['record_id']
            if rid in existing: raise ValueError('Duplicate record_id in persistent archive')
            existing[rid]=row
    additions=defaultdict(list)
    for item in records:
        row=secure_record(item,now)
        rid=row['record_id']
        previous=existing.get(rid)
        if previous:
            if previous.get('record_fingerprint')!=row['record_fingerprint']:
                raise ValueError('Stable ID collision or changed original publication')
            continue
        existing[rid]=row
        additions[partition(row)].append(row)
    # Build in memory first: all records must be valid before any writes.
    prepared={}
    for filename,group in additions.items():
        path=ARCHIVE/filename
        before=path.read_text(encoding='utf-8') if path.exists() else ''
        prepared[path]=before+''.join(json_line(x) for x in sorted(group,key=lambda r:r['record_id']))
    for path,content in prepared.items():
        path.write_text(content,encoding='utf-8')
    manifest=build_manifest()
    old=json.loads(MANIFEST.read_text(encoding='utf-8')) if MANIFEST.exists() else None
    # Stable manifest timestamp when collection had no new information.
    manifest['updated_at']=now if additions or not old else old.get('updated_at',now)
    MANIFEST.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    summary={k:manifest[k] for k in ('schema_version','total_records','partition_count','updated_at','event_linkage')}
    summary['archive_url']='https://github.com/e4e421/supply-chain-rights-observatory/tree/main/data/archive'
    PUBLIC_SUMMARY.write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    return manifest['total_records'],sum(map(len,additions.values()))

if __name__=='__main__':
    from datetime import timezone
    snapshot=json.loads((ROOT/'docs/data/latest.json').read_text(encoding='utf-8'))
    total,added=persist(snapshot['items'],datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z'))
    print(f'Public archival records: {total}; new: {added}')
