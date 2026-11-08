"""Offline tests for the collection perimeter, parsing, classification and exports."""
import importlib.util
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('collector', ROOT / 'scripts/update_data.py')
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)
spec2 = importlib.util.spec_from_file_location('validator', ROOT / 'scripts/validate_data.py')
validator = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(validator)
NOW = datetime(2026, 11, 8, 0, 0, tzinfo=timezone.utc)

class CollectorTests(unittest.TestCase):
    def test_network_destinations_allowlist(self):
        self.assertEqual(collector.public_https_url('https://news.google.com/rss/search?q=abc','news.google.com'), 'https://news.google.com/rss/search?q=abc')
        for url in ('http://news.google.com/rss', 'https://user:password@news.google.com/rss', 'https://127.0.0.1/', 'https://localhost/', 'file:///etc/passwd', 'https://news.google.com:8080/feed', 'https://news.google.com.evil.test/rss'):
            self.assertFalse(collector.public_https_url(url, 'news.google.com'))

    def test_dtd_xml_rejected(self):
        malicious = b'<!DOCTYPE rss [<!ENTITY example SYSTEM "file:///etc/passwd">]><rss><channel/></rss>'
        with self.assertRaises(ValueError):
            collector.parse_rss(malicious, {'id':'sample', 'name':'Sample'}, NOW)

    def test_rss_item_is_discovery_only(self):
        xml = b'''<?xml version="1.0"?><rss version="2.0"><channel>
        <item><title>Forced labour at supplier, article</title><link>https://news.google.com/rss/articles/123</link><pubDate>Sun, 08 Nov 2026 00:00:00 GMT</pubDate></item>
        <item><title>Bad redirect</title><link>http://localhost/private</link><pubDate>Sun, 08 Nov 2026 00:00:00 GMT</pubDate></item>
        </channel></rss>'''
        items = collector.parse_rss(xml, {'id':'forced-labour','name':'Test','topics':['forced-labour']}, NOW)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['kind'], 'discovery')
        self.assertEqual(items[0]['evidence_status'], 'Unverified discovery')
        self.assertIn('forced-labour', items[0]['topics'])

    def test_crossref_filters_unrelated_papers(self):
        def record(title, doi):
            return {'title':[title],'DOI':doi,'published':{'date-parts':[[2026,11,7]]}}
        payload = {'message':{'items':[
            record('Supply chain human rights due diligence and governance','10.1000/example.1'),
            record('Quantum mechanics in physics','10.1000/example.2'),
            record('Labour supply chains and forced work','https://bad.url')
        ]}}
        items = collector.parse_crossref(payload, {'id':'academic-hrdd','name':'Research'}, NOW)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['kind'], 'academic')
        self.assertEqual(items[0]['doi'], '10.1000/example.1')

    def test_openalex_doi_metadata_and_title_screen(self):
        payload={"results":[
            {"display_name":"Global value chains and worker rights in factories",
             "doi":"https://doi.org/10.1234/research.1",
             "publication_date":"2026-11-07",
             "primary_location":{"source":{"display_name":"Example Research Journal"}}},
            {"display_name":"Physics of clouds","doi":"https://doi.org/10.1234/research.2","publication_date":"2026-11-07"}
        ]}
        candidates=[]
        results=collector.parse_openalex(payload,{"id":"openalex-human-rights","name":"Academic"},NOW,candidates)
        self.assertEqual(len(results),1)
        self.assertEqual(len(candidates),2)
        self.assertEqual(results[0]['doi'],'10.1234/research.1')
        self.assertFalse(results[0]['publisher_verified'])

    def test_merge_preserves_first_seen_and_deduplicates(self):
        previous = {'id':'ignored','title':'Workplace safety at supplier','url':'https://news.google.com/rss/articles/42','published_at':'2026-11-07T00:00:00Z','kind':'discovery','first_seen':'2026-11-07T00:00:00Z'}
        previous['id'] = collector.stable_id(previous)
        new = previous.copy()
        new['first_seen'] = '2026-11-08T00:00:00Z'
        got = collector.merge_items([new], [previous], NOW)
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0]['first_seen'], '2026-11-07T00:00:00Z')

    def test_current_public_documents_validate(self):
        doc = json.loads((ROOT / 'docs/data/latest.json').read_text(encoding='utf-8'))
        self.assertTrue(validator.validate(doc))

if __name__ == '__main__':
    unittest.main()
