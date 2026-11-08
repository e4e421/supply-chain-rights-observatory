#!/usr/bin/env python3
"""Validate the complete public archive and review catalog before a deployment."""
from __future__ import annotations
import json, hashlib, sys
from pathlib import Path
from archive_data import ROOT, ARCHIVE, MANIFEST, PUBLIC_SUMMARY, build_manifest
from source_governance import validate as validate_sources, REGISTRY, CANDIDATES, REFS, OUTPUT

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

def validate_source_catalog():
    registry=json.loads(REGISTRY.read_text(encoding='utf-8'))
    candidates=json.loads(CANDIDATES.read_text(encoding='utf-8'))
    refs=json.loads(REFS.read_text(encoding='utf-8'))
    validate_sources(registry,candidates,refs)
    if OUTPUT.exists():
        report=json.loads(OUTPUT.read_text(encoding='utf-8'))
        if report.get('approved_reference_count')!=len(registry['sources']):
            raise ValueError('Source health status out of sync with curated references')
    print('Verified source register:',len(registry['sources']))
    return True

if __name__=='__main__':
    validate_archive()
    validate_source_catalog()
