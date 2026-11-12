#!/usr/bin/env python3
"""Confirm that the exact checked build and its indexes are available on Pages."""
import hashlib
import json
import re
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

SITE = 'https://e4e421.github.io/supply-chain-rights-observatory/'
OUT = Path(__file__).resolve().parents[1] / '_site'
INDEXES = {
    'catalog_sha256': ('data/archive/catalog.json', 2_000_000),
    'source_health_sha256': ('data/source-health.json', 2_000_000),
    'relevance_sha256': ('data/relevance-index.json', 20_000_000),
    'publication_sha256': ('data/publication-index.json', 2_000_000),
}


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def read_public_file(path, maximum, query):
    request = Request(SITE + path + '?' + query, headers={
        'User-Agent': 'SCRO release verification', 'Accept-Encoding': 'identity', 'Cache-Control': 'no-cache'
    })
    with build_opener(NoRedirects()).open(request, timeout=8) as response:
        content = response.read(maximum + 1)
    if len(content) > maximum:
        raise ValueError('Published index exceeds its verification limit')
    return content


def verify(expected, read):
    live = json.loads(read('data/build-info.json', 65536))
    if live != expected:
        raise ValueError('Public build metadata differs from the selected release')
    for field, (path, maximum) in INDEXES.items():
        digest = hashlib.sha256(read(path, maximum)).hexdigest()
        if digest != expected.get(field):
            raise ValueError(f'Published file differs from the selected release: {path}')


def main():
    expected = json.loads((OUT / 'data/build-info.json').read_text(encoding='utf-8'))
    revision = expected.get('git_revision', '')
    if not re.fullmatch(r'[a-f0-9]{40}', revision):
        raise ValueError('The release is missing an immutable Git revision')
    for attempt in range(1, 7):
        query = urlencode({'release': revision, 'attempt': attempt})
        try:
            verify(expected, lambda path, maximum: read_public_file(path, maximum, query))
        except (OSError, ValueError) as error:
            print(f'Public release check {attempt}/6 pending: {error}', flush=True)
            if attempt < 6:
                time.sleep(5)
        else:
            print('Public release and index digests confirmed:', revision)
            return 0
    print('::error::The deployed revision and public indexes could not be confirmed')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
