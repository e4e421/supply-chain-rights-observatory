import copy
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from check_freshness import collection_age
import source_governance
from update_data import parse_rss, process_source
from validate_archive import validate_reference_health
from validate_data import validate_references


class ReferenceIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.registry = json.loads((ROOT / 'sources/registry.json').read_text())
        self.refs = json.loads((ROOT / 'docs/data/references.json').read_text())
        self.health = {
            'approved_reference_count': len(self.registry['sources']),
            'sources': [
                dict(id=row['id'], name=row['name'], url=row['url'], probe_enabled=row.get('probe_enabled', True))
                for row in self.registry['sources']
            ],
        }

    def test_reference_directory_can_grow_past_thirty(self):
        self.assertTrue(validate_references(self.refs + [dict(self.refs[0], url='https://example.org/new-reference')]))

    def test_source_health_checks_id_url_name_and_policy(self):
        self.assertTrue(validate_reference_health(self.registry, self.refs, self.health))
        for key, value in [('id', 'wrong-id'), ('url', 'https://example.org/old-url'),
                           ('name', 'Wrong source'), ('probe_enabled', not self.health['sources'][0]['probe_enabled'])]:
            with self.subTest(key=key):
                wrong = copy.deepcopy(self.health)
                wrong['sources'][0][key] = value
                with self.assertRaises(ValueError):
                    validate_reference_health(self.registry, self.refs, wrong)

    def test_registry_reference_replacement_cannot_pass_on_count_alone(self):
        refs = copy.deepcopy(self.refs)
        refs[0]['url'] = 'https://example.org/replacement'
        with self.assertRaises(ValueError):
            validate_reference_health(self.registry, refs, self.health)

    def test_replacing_reference_url_discards_previous_probe(self):
        old = copy.deepcopy(self.health)
        row = old['sources'][0]
        row.update(url='https://example.org/old', reachability='responded', http_status=200,
                   last_probe='2026-11-11T05:00:00Z')
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'source-health.json'
            output.write_text(json.dumps(old))
            with patch.object(source_governance, 'OUTPUT', output):
                source_governance.run()
            report = json.loads(output.read_text())
        self.assertTrue(validate_reference_health(self.registry, self.refs, report))
        self.assertEqual(report['sources'][0]['reachability'], 'untested')
        self.assertIsNone(report['sources'][0]['last_probe'])


class CollectionFreshnessTests(unittest.TestCase):
    def test_collection_age_uses_success_not_last_attempt_or_last_addition(self):
        snapshot = {
            'last_successful_collection': '2026-11-12T03:00:00Z',
            'generated_at': '2026-11-13T01:00:00Z',
        }
        now = datetime(2026, 11, 12, 21, tzinfo=timezone.utc)
        self.assertEqual(collection_age(snapshot, now, 18), timedelta(hours=18))
        with self.assertRaises(ValueError):
            collection_age(snapshot, now + timedelta(minutes=1), 18)

    def test_missing_or_ambiguous_timestamp_is_an_alert(self):
        now = datetime(2026, 11, 12, 21, tzinfo=timezone.utc)
        for stamp in (None, '2026-11-12T03:00:00', '2026-11-13T01:00:00Z'):
            with self.subTest(stamp=stamp), self.assertRaises(ValueError):
                collection_age({'last_successful_collection': stamp}, now, 18)

    def test_received_and_accepted_observations_are_independent(self):
        now = datetime(2026, 11, 12, 6, tzinfo=timezone.utc)
        xml = b'<rss><channel><item><title>Forced labour in the supply chain</title><link>https://news.google.com/rss/articles/1</link><pubDate>Thu, 12 Nov 2026 05:00:00 GMT</pubDate></item><item><title>No usable date</title></item></channel></rss>'
        metrics = {}
        accepted = parse_rss(xml, {'id': 'test-feed', 'name': 'Test'}, now, counts=metrics)
        self.assertEqual(metrics['received_items'], 2)
        self.assertEqual(len(accepted), 1)

    def test_http_failure_is_reported_without_request_data(self):
        def rate_limited():
            raise HTTPError('https://example.org/', 429, 'rate limit', {}, None)

        now = datetime(2026, 11, 12, 6, tzinfo=timezone.utc)
        warnings = []
        status = process_source({'id': 'test-feed', 'name': 'Test'}, 'news', rate_limited, [], warnings, now)
        self.assertEqual((status['status'], status['http_status'], status['failure_kind']), ('failed', 429, 'rate_limited'))
        self.assertNotIn('example.org', warnings[0])


if __name__ == '__main__':
    unittest.main()
