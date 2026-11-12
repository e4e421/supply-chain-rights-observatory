#!/usr/bin/env python3
"""Validate the complete public archive and review catalog before a deployment."""
from __future__ import annotations
import json, hashlib, sys
from pathlib import Path
from archive_data import ROOT, ARCHIVE, MANIFEST, PUBLIC_SUMMARY, build_manifest
from source_governance import validate as validate_sources, REGISTRY, CANDIDATES, REFS, OUTPUT
from candidate_archive import ROOT_DIR as CANDIDATES_DIR, MANIFEST as CANDIDATES_MANIFEST, audit as audit_candidates
from validate_data import validate_references

def validate_archive():
    if not MANIFEST.exists():
        if any(ARCHIVE.glob('????-??.jsonl')): raise ValueError('Archive files exist but manifest is missing')
        print('Archive not initialized; a scheduled/manual collection will backfill the snapshot.')
        return 0
    manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
    reconstructed=build_manifest()
    for k in ('schema_version','format','public_metadata_only','total_records','partition_count','partitions','event_linkage'):
        if manifest.get(k)!=reconstructed[k]: raise ValueError('Archive checksum, inventory or schema mismatch: '+k)
    if not PUBLIC_SUMMARY.exists(): raise ValueError('Public archive summary missing')
    summary=json.loads(PUBLIC_SUMMARY.read_text(encoding='utf-8'))
    if summary.get('total_records') != reconstructed['total_records']:
        raise ValueError('Public archive summary inconsistent with archive')
    print('Verified archive records:',reconstructed['total_records'])
    return reconstructed['total_records']

def validate_candidate_archive():
    if not CANDIDATES_MANIFEST.exists():
        if any(CANDIDATES_DIR.glob('????-??.jsonl')):
            raise ValueError('Candidate partitions exist without manifest')
        print('Candidate archive not initialised yet')
        return 0
    expected=json.loads(CANDIDATES_MANIFEST.read_text(encoding='utf-8'))
    actual=audit_candidates()
    if expected != actual:
        raise ValueError('Candidate manifest digest or count mismatch')
    print('Verified candidate records:',actual['total_candidates'])
    return actual['total_candidates']

def validate_reference_health(registry, refs, report):
    validate_references(refs)
    source_rows=registry['sources']
    registry_by_url={row['url']:row['name'] for row in source_rows}
    if registry_by_url!={row['url']:row['name'] for row in refs}:
        raise ValueError('Reference directory identities differ from the curated registry')
    expected={row['id']:(row['name'],row['url'],row.get('probe_enabled',True)) for row in source_rows}
    rows=report.get('sources')
    if not isinstance(rows,list) or len(rows)!=len(expected) or report.get('approved_reference_count')!=len(expected):
        raise ValueError('Source health inventory differs from the curated registry')
    actual={}
    for row in rows:
        if not isinstance(row,dict) or not isinstance(row.get('probe_enabled'),bool):
            raise ValueError('Source health row is missing its reference policy')
        actual[row.get('id')]=(row.get('name'),row.get('url'),row['probe_enabled'])
    if expected!=actual:
        raise ValueError('Source health IDs, URLs, names or check policies differ from the curated registry')
    return True


def validate_source_catalog():
    registry=json.loads(REGISTRY.read_text(encoding='utf-8'))
    candidates=json.loads(CANDIDATES.read_text(encoding='utf-8'))
    refs=json.loads(REFS.read_text(encoding='utf-8'))
    validate_sources(registry,candidates,refs)
    report=json.loads(OUTPUT.read_text(encoding='utf-8'))
    validate_reference_health(registry,refs,report)
    print('Verified source register:',len(registry['sources']))
    return True

if __name__=='__main__':
    validate_archive()
    validate_candidate_archive()
    validate_source_catalog()
