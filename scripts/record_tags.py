"""Validation for editorial record tags, independent of review decisions."""
import re
import unicodedata

MAX_TAGS = 30
MAX_TAG_LENGTH = 64
RECORD_ID = re.compile(r'[0-9a-f]{18}')
SHA256 = re.compile(r'[0-9a-f]{64}')


def canonical_tag(text):
    return re.sub(r'\s+', '-', unicodedata.normalize('NFKC', text).strip().removeprefix('#').strip().lower())


def valid_tag(tag):
    if not isinstance(tag, str) or not 1 <= len(tag) <= MAX_TAG_LENGTH or canonical_tag(tag) != tag:
        return False
    return (unicodedata.category(tag[0])[0] in 'LN'
            and all(c in '-_' or unicodedata.category(c)[0] in 'LMN' for c in tag))


def valid_tags(tags):
    return (isinstance(tags, list) and len(tags) <= MAX_TAGS and all(valid_tag(tag) for tag in tags)
            and len(set(tags)) == len(tags))


def validate_tag_overlay(doc):
    catalog = doc.get('tag_catalog', [])
    assignments = doc.get('record_tags', {})
    if (not isinstance(catalog, list) or not all(valid_tag(tag) for tag in catalog)
            or len(set(catalog)) != len(catalog) or not isinstance(assignments, dict)):
        raise ValueError('Invalid tag catalogue')
    known = set(catalog)
    for rid, row in assignments.items():
        if not RECORD_ID.fullmatch(rid) or not isinstance(row, dict) or set(row) != {'tags', 'issue', 'issue_digest'}:
            raise ValueError('Invalid tag assignment')
        if not valid_tags(row['tags']) or not set(row['tags']) <= known:
            raise ValueError('Invalid record tags')
        if type(row['issue']) is not int or row['issue'] < 1 or not SHA256.fullmatch(str(row['issue_digest'])):
            raise ValueError('Invalid tag publication provenance')
