"""Offline tests for the collection perimeter, parsing, classification and exports."""
import importlib.util
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

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

    def test_official_atom_retains_original_links_and_filters_titles(self):
        feed = {'id':'eurostat-social-news','name':'Eurostat','publisher':'Eurostat',
                'url':'https://ec.europa.eu/eurostat/example-feed'}
        body = b"""<feed xmlns="http://www.w3.org/2005/Atom">
          <entry><title>Forced labour in supply chains</title><link href="/eurostat/release"/>
          <published>2026-11-08T01:15:00+01:00</published><summary>Do not archive this</summary></entry>
          <entry><title>Industrial energy output</title><link href="/eurostat/unrelated"/>
          <published>2026-11-08T00:00:00Z</published></entry>
          <entry><title>Forced labour</title><link href="https://eur-lex.europa.eu/misplaced"/>
          <published>2026-11-08T00:00:00Z</published></entry>
        </feed>"""
        candidates, counts = [], {}
        rows = collector.parse_official_feed(body, feed, NOW, candidates, counts)
        self.assertEqual(counts, {'received_items':3,'usable_items':2})
        self.assertEqual(len(candidates), 2)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row['url'], 'https://ec.europa.eu/eurostat/release')
        self.assertEqual(row['published_at'], '2026-11-08T00:15:00Z')
        self.assertEqual(row['publisher_hint'], 'Eurostat')
        self.assertNotIn('Do not archive this', json.dumps(row))
        row['id'] = collector.stable_id(row)
        from archive_data import secure_record
        from candidate_archive import row_for
        self.assertEqual(secure_record(row, row['first_seen'])['url'], row['url'])
        self.assertEqual(row_for(row)['url'], row['url'])

    def test_official_rss_valid_empty_and_incompatible_entries(self):
        feed = {'id':'eur-lex-oj-l','name':'EUR-Lex','publisher':'EUR-Lex',
                'url':'https://eur-lex.europa.eu/EN/display-feed.rss?rssId=222'}
        xml = b"""<rss><channel><item><title>Forced labour regulation</title>
          <link>https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=OJ:L_202600001</link>
          <pubDate>Sun, 08 Nov 2026 00:00:00 GMT</pubDate></item></channel></rss>"""
        self.assertEqual(len(collector.parse_official_feed(xml, feed, NOW)), 1)
        self.assertEqual(collector.parse_official_feed(b'<rss><channel/></rss>', feed, NOW), [])
        with self.assertRaises(ValueError):
            collector.parse_official_feed(xml.replace(b'<pubDate>',b'<unknown>').replace(b'</pubDate>',b'</unknown>'), feed, NOW)

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

    def test_collection_tracks_attempts_and_clears_streak_on_valid_empty_response(self):
        with tempfile.TemporaryDirectory() as folder:
            config=Path(folder)/'queries.json';output=Path(folder)/'latest.json'
            config.write_text(json.dumps({'news_queries':[], 'academic_queries':[],
                'openalex_queries':[{'id':'openalex-test','name':'Test','query':'workers'}]}))
            responses=[b'{}', b'{"results":null}', b'{}', b'{"results":[]}']
            with patch.multiple(collector, CONFIG_FILE=config, OUTPUT_FILE=output), \
                 patch.object(collector, 'fetch_bytes', side_effect=responses), \
                 patch('archive_data.persist', return_value=(0,0)), \
                 patch('candidate_archive.persist_candidates', return_value=(0,0)):
                for expected in (1,2,3,0):
                    collector.run()
                    source=json.loads(output.read_text())['sources'][0]
                    self.assertEqual(source['consecutive_failures'],expected)
                    self.assertEqual(source['status'],'failed' if expected else 'ok')
                    self.assertEqual(source['items'],0)

    def test_current_public_documents_validate(self):
        doc = json.loads((ROOT / 'docs/data/latest.json').read_text(encoding='utf-8'))
        self.assertTrue(validator.validate(doc))

if __name__ == '__main__':
    unittest.main()
