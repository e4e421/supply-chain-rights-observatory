import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from confirm_release import INDEXES, verify
import publish_reviews
from record_aliases import publication_aliases
from relevance_engine import decorate, digest


class ReleaseVerificationTests(unittest.TestCase):
    def test_release_verification_rejects_stale_indexes_even_with_matching_revision(self):
        payloads = {path: b'{}' for path, _ in INDEXES.values()}
        expected = {'git_revision': 'a' * 40}
        expected.update({key: hashlib.sha256(payloads[path]).hexdigest() for key, (path, _) in INDEXES.items()})
        payloads['data/build-info.json'] = json.dumps(expected).encode()
        verify(expected, lambda path, maximum: payloads[path])
        payloads['data/publication-index.json'] = b'{"stale":true}'
        with self.assertRaises(ValueError):
            verify(expected, lambda path, maximum: payloads[path])

    def test_issue_stays_open_until_the_selected_revision_contains_its_batch(self):
        record = 'a' * 18
        revision = 'b' * 40
        number = '17'
        body = 'SCRO_PUBLISH_V2\n```json\n' + json.dumps({'schema_version': 1, 'decisions': [{'record_id': record}]}) + '\n```'
        issue = {'title': publish_reviews.ISSUE_TITLE, 'state': 'open', 'body': body, 'user': {'login': 'e4e421'}}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            event = root / 'event.json'
            event.write_text(json.dumps({'inputs': {'publication_issue': number}}))
            path = root / publish_reviews.PATH
            path.parent.mkdir(parents=True, exist_ok=True)
            env = dict(GITHUB_REPOSITORY=publish_reviews.REPO, GITHUB_REF='refs/heads/main',
                       GITHUB_EVENT_PATH=str(event), GITHUB_TOKEN='fixture', RELEASE_SHA=revision)
            with patch.dict(os.environ, env), patch.object(publish_reviews, 'ROOT', root), \
                 patch.object(publish_reviews.subprocess, 'check_output', return_value=revision), \
                 patch.object(publish_reviews, 'api', return_value=issue) as api:
                path.write_text(json.dumps({'records': {}}))
                with self.assertRaises(ValueError):
                    publish_reviews.finalize()
                self.assertEqual(api.call_count, 1)
                path.write_text(json.dumps({'records': {record: {'issue': 17, 'issue_digest': digest({'body': body})}}}))
                publish_reviews.finalize()
                self.assertEqual(api.call_args.args[2], 'PATCH')
                self.assertEqual(api.call_args.args[3]['state'], 'closed')


class AliasTests(unittest.TestCase):
    def test_matching_observations_are_grouped_but_different_tags_remain_independent(self):
        first, second = 'a' * 18, 'b' * 18
        row = {'record_id': first, 'kind': 'discovery', 'url': 'https://example.org/article',
               'title': 'Forced labour report - example.org', 'publisher_hint': 'example.org',
               'published_at': '2026-11-12T00:00:00Z', 'first_seen': '2026-11-12T06:00:00Z'}
        other = dict(row, record_id=second, title='Forced labour report - https://example.org/',
                     publisher_hint='https://example.org/')
        records = {first: row, second: other}
        index = {key: decorate(value, {}) for key, value in records.items()}
        self.assertEqual(publication_aliases(records, index, {}), {second: first})
        self.assertEqual(publication_aliases(records, index, {second: {'tags': ['iphone']}}), {})


if __name__ == '__main__':
    unittest.main()
