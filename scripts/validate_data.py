#!/usr/bin/env python3
"""Fail closed on malformed public data before deployment."""
import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
MAX_ITEMS = 240
REQUIRED = {'title', 'url', 'published_at', 'source', 'source_id', 'kind', 'evidence_status', 'topics', 'first_seen', 'id'}
TOPICS = {'policy','forced-labour','working-conditions','worker-voice','network','research','other'}


def validate(data):
    assert data.get('schema_version') == 1
    assert data.get('status') in {'not_started','ok','partial','failed'}
    assert isinstance(data.get('items'), list) and len(data['items']) <= MAX_ITEMS
    assert isinstance(data.get('sources'), list)
    assert isinstance(data.get('warnings'), list)
    assert all(isinstance(x, str) and len(x) <= 300 for x in data['warnings'])
    ids = set()
    for item in data['items']:
        assert isinstance(item, dict) and REQUIRED <= item.keys()
        assert not any(k.lower() in {'token','api_key','email','password','secret','private_key','authorization'} for k in item)
        assert isinstance(item['title'],str) and 0 < len(item['title']) <= 240
        assert isinstance(item['source'],str) and len(item['source']) <= 120
        assert item['kind'] in ('academic','discovery')
        assert item['evidence_status'] in ('Bibliographic record','Unverified discovery')
        assert isinstance(item['topics'],list) and set(item['topics']) <= TOPICS
        assert re.fullmatch(r'[0-9a-f]{18}',item['id']) and item['id'] not in ids
        ids.add(item['id'])
        url = urlparse(item['url'])
        assert url.scheme == 'https' and not url.username and not url.password and url.hostname
        assert url.hostname in ('news.google.com','doi.org')
        assert len(item['url']) <= 1000
        assert re.match(r'^\d{4}-\d{2}-\d{2}T',item['published_at'])
    for source in data['sources']:
        assert source['status'] in ('ok','failed')
        assert isinstance(source['items'],int) and source['items'] >= 0
    return True

if __name__ == '__main__':
    data = json.loads((ROOT/'docs/data/latest.json').read_text(encoding='utf-8'))
    assert validate(data)
    refs = json.loads((ROOT/'docs/data/references.json').read_text(encoding='utf-8'))
    assert isinstance(refs,list) and 3 <= len(refs) <= 30
    for ref in refs:
        u=urlparse(ref['url'])
        assert u.scheme=='https' and u.hostname and not u.username and not u.password
    print(f'Validated {len(data["items"])} research leads and {len(refs)} reference sources.')
