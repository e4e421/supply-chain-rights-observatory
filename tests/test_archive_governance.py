"""Regression tests for immutable public archives and curated source governance."""
from __future__ import annotations
import copy, hashlib, json, sys, tempfile, unittest
from email.message import Message
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import archive_data
import source_governance

def item(title='Supplier due diligence',url='https://news.google.com/rss/articles/test1',
         first_seen='2026-11-08T00:00:00Z'):
    return {'id':hashlib.sha256((url+'|'+title.lower()).encode()).hexdigest()[:18],
       'kind':'discovery','title':title,'url':url,
       'published_at':'2026-11-07T00:00:00Z','first_seen':first_seen,
       'source':'EU due diligence & supply chain law','source_id':'eu-policy',
       'topics':['policy'],'description':'News lead collected from a public feed.',
       'evidence_status':'Unverified discovery'}

class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.old=(archive_data.ARCHIVE,archive_data.MANIFEST,archive_data.PUBLIC_SUMMARY)
        archive_data.ARCHIVE=self.root/'data/archive'
        archive_data.MANIFEST=archive_data.ARCHIVE/'manifest.json'
        archive_data.PUBLIC_SUMMARY=self.root/'docs/data/archive-summary.json'
        archive_data.PUBLIC_SUMMARY.parent.mkdir(parents=True)
        self.now='2026-11-08T13:00:00Z'
    def tearDown(self):
        archive_data.ARCHIVE,archive_data.MANIFEST,archive_data.PUBLIC_SUMMARY=self.old
        self.temp.cleanup()
    def test_backfill_partition_manifest_and_idempotency(self):
        one=item()
        two=item('Union grievances','https://news.google.com/rss/articles/test2','2026-10-08T00:00:00Z')
        total,added=archive_data.persist([one,two],self.now)
        self.assertEqual((total,added),(2,2))
        self.assertEqual(len(list(archive_data.ARCHIVE.glob('*.jsonl'))),2)
        manifest=json.loads(archive_data.MANIFEST.read_text())
        self.assertEqual(manifest['total_records'],2)
        self.assertEqual(len(manifest['partitions']),2)
        old={p.name:p.read_bytes() for p in archive_data.ARCHIVE.glob('*.jsonl')}
        self.assertEqual(archive_data.persist([one,two],self.now),(2,0))
        self.assertEqual({p.name:p.read_bytes() for p in archive_data.ARCHIVE.glob('*.jsonl')},old)
    def test_stable_id_collision_rejected_without_overwrite(self):
        row=item()
        archive_data.persist([row],self.now)
        original=(archive_data.ARCHIVE/'2026-11.jsonl').read_bytes()
        wrong={**row,'title':'Different allegation under the same ID'}
        with self.assertRaises(ValueError):
            archive_data.persist([wrong],self.now)
        self.assertEqual(original,(archive_data.ARCHIVE/'2026-11.jsonl').read_bytes())
    def test_reject_private_or_unsafe_archive_urls(self):
        for link in ('http://news.google.com/a','https://127.0.0.1/a',
                    'https://user:password@news.google.com/x',
                    'https://news.google.com:1234/a',
                    'https://news.google.com.evil.test/a'):
            with self.subTest(link=link):
                with self.assertRaises(ValueError):
                    archive_data.secure_record(item(url=link),self.now)
    def test_legacy_chinese_source_is_normalized(self):
        row=item()
        row['source']='歐盟盡職調查與供應鏈法規'
        archived=archive_data.secure_record(row,self.now)
        self.assertEqual(archived['source'],'EU due diligence & supply chain law')
        self.assertIsNone(archived['event_id'])
        self.assertEqual(archived['record_id'],row['id'])
    def test_manifest_digest_changes_if_partition_tampered(self):
        archive_data.persist([item()],self.now)
        manifest=json.loads(archive_data.MANIFEST.read_text())
        path=archive_data.ARCHIVE/'2026-11.jsonl'
        path.write_text(path.read_text().replace('Supplier due diligence','Supplier security diligence'))
        revised=archive_data.build_manifest()
        self.assertNotEqual(manifest['partitions'][0]['sha256'],revised['partitions'][0]['sha256'])

MANUAL_MEDIA = {
    'media-reuters', 'media-guardian', 'media-esgdive', 'media-responsible-investor',
}
MEDIA_URL = 'https://www.hsfkramer.com/insights'
ROBOTS_URL = 'https://www.hsfkramer.com/robots.txt'


class ProbeResponse(BytesIO):
    def __init__(self, url, body=b'', content_type='text/plain'):
        super().__init__(body)
        self.url = url
        self.status = 200
        self.headers = Message()
        self.headers['Content-Type'] = content_type

    def geturl(self):
        return self.url

    def getcode(self):
        return self.status


class GovernanceTests(unittest.TestCase):
    def test_approved_sources_must_match_reference_directory(self):
        reg=json.loads(source_governance.REGISTRY.read_text())
        cand=json.loads(source_governance.CANDIDATES.read_text())
        refs=json.loads(source_governance.REFS.read_text())
        self.assertTrue(source_governance.validate(reg,cand,refs))
        self.assertGreaterEqual(len(reg['sources']),15)
    def test_unapproved_candidates_never_auto_promoted(self):
        reg=json.loads(source_governance.REGISTRY.read_text())
        cand=json.loads(source_governance.CANDIDATES.read_text())
        refs=json.loads(source_governance.REFS.read_text())
        rogue=copy.deepcopy(reg)
        rogue['sources'][0]['auto_ingest']=True
        with self.assertRaises(ValueError):source_governance.validate(rogue,cand,refs)
    def test_owner_approved_media_probe_scope_keeps_manual_ingestion(self):
        reg=json.loads(source_governance.REGISTRY.read_text())
        cand=json.loads(source_governance.CANDIDATES.read_text())
        refs=json.loads(source_governance.REFS.read_text())
        approved=[x for x in reg['sources'] if x.get('verification_level')=='owner_approved_for_manual_reference']
        self.assertEqual(len(approved),11)
        self.assertEqual({source['id'] for source in approved if source['probe_enabled'] is False},
                         MANUAL_MEDIA)
        for source in approved:
            with self.subTest(source=source['id']):
                self.assertTrue(any(r['url']==source['url'] and r['name']==source['name'] for r in refs))
                self.assertFalse(any(x['id']==source['id'] for x in cand['candidates']))
                self.assertIs(source['auto_ingest'],False)
                self.assertEqual(source['licence_review_status'],'pending')
        self.assertTrue(source_governance.validate(reg,cand,refs))
        restricted = next(source for source in approved if source['id'] == 'media-reuters')
        restricted['probe_enabled'] = True
        with self.assertRaises(ValueError):source_governance.validate(reg,cand,refs)

    def test_candidate_links_and_auto_ingest_are_restricted(self):
        reg=json.loads(source_governance.REGISTRY.read_text())
        refs=json.loads(source_governance.REFS.read_text())
        candidate={'id':'candidate-test','url':'https://www.reuters.com/world/','status':'pending_review','auto_ingest':False}
        cand={'schema_version':1,'candidates':[candidate]}
        self.assertTrue(source_governance.validate(reg,cand,refs))
        for malformed in ('http://www.reuters.com','https://user:secret@www.reuters.com/',
                          'https://www.reuters.com.evil.org/','https://localhost/',
                          'https://www.reuters.com:8443/'):
            with self.subTest(malformed=malformed):
                with self.assertRaises(ValueError):source_governance.validate_manual_link(malformed)
        unsafe=copy.deepcopy(cand)
        unsafe['candidates'][0]['auto_ingest']=True
        with self.assertRaises(ValueError):source_governance.validate(reg,unsafe,refs)
        duplicate=copy.deepcopy(cand)
        duplicate['candidates'].append(copy.deepcopy(duplicate['candidates'][0]))
        with self.assertRaises(ValueError):source_governance.validate(reg,duplicate,refs)

    def test_reference_probe_tracks_consecutive_failures_without_offline_increment(self):
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'source-health.json'
            with patch.object(source_governance,'OUTPUT',output), patch.object(source_governance,'probe') as probe:
                def first():
                    return json.loads(output.read_text())['sources'][0]['consecutive_failures']
                probe.return_value={'reachability':'not_confirmed','http_status':None}
                for expected in (1,2,3):
                    source_governance.run(online=True)
                    self.assertEqual(first(),expected)
                    source_governance.run()
                    self.assertEqual(first(),expected)
                probe.return_value={'reachability':'responded','http_status':200}
                source_governance.run(online=True)
                self.assertEqual(first(),0)
                registry = json.loads(source_governance.REGISTRY.read_text())
                manual_urls = {source['url'] for source in registry['sources']
                               if source['id'] in MANUAL_MEDIA}
                probed_urls = {args[0] for args, _ in probe.call_args_list}
                self.assertTrue(manual_urls.isdisjoint(probed_urls))
                self.assertIn(MEDIA_URL, probed_urls)

    def test_newly_enabled_probe_has_no_stale_manual_status(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'source-health.json'
            output.write_text(json.dumps({'sources': [
                {'id': 'media-hsfkramer', 'reachability': 'manual_only',
                 'http_status': None, 'last_probe': None, 'consecutive_failures': 0},
            ]}))
            with patch.object(source_governance, 'OUTPUT', output):
                source_governance.run()
            rows = {row['id']: row for row in json.loads(output.read_text())['sources']}
            self.assertEqual(rows['media-hsfkramer']['reachability'], 'untested')
            self.assertEqual(rows['media-reuters']['reachability'], 'manual_only')

    def test_policy_restriction_clears_previous_probe_failures(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'source-health.json'
            output.write_text(json.dumps({'sources': [
                {'id': 'media-hsfkramer', 'reachability': 'not_confirmed',
                 'last_probe': '2026-11-08T00:00:00Z', 'consecutive_failures': 2},
            ]}))
            result = {'reachability': 'policy_restricted', 'http_status': None}
            with patch.object(source_governance, 'OUTPUT', output):
                with patch.object(source_governance, 'probe', return_value=result):
                    source_governance.run(online=True)
            rows = {row['id']: row for row in json.loads(output.read_text())['sources']}
            self.assertEqual(rows['media-hsfkramer']['reachability'], 'policy_restricted')
            self.assertEqual(rows['media-hsfkramer']['consecutive_failures'], 0)

    def test_external_fetch_hosts_are_restricted(self):
        for url in ('http://www.ilo.org/','https://localhost/','https://example.com/',
                    'https://www.oecd.org:444/','https://www.oecd.org.evil.org/'):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):source_governance.validate_link(url)


class ProbeTests(unittest.TestCase):
    def test_robots_selects_project_group_and_longest_matching_path(self):
        rules = """User-agent: *
Disallow: /

User-agent: SupplyChainRightsObservatory
Disallow: /insights
Allow: /insights/public
"""
        self.assertTrue(source_governance.robots_allows(rules, MEDIA_URL + '/public/report'))
        self.assertFalse(source_governance.robots_allows(rules, MEDIA_URL + '/private'))
        self.assertTrue(source_governance.robots_allows(rules, 'https://www.hsfkramer.com/about'))

    def test_media_checks_robots_before_head_without_reading_page_content(self):
        page = ProbeResponse(MEDIA_URL, content_type='text/html')
        with patch.object(source_governance, 'build_opener') as build:
            with patch.object(page, 'read', side_effect=AssertionError('HEAD read content')):
                opener = build.return_value
                opener.open.side_effect = [
                    ProbeResponse(ROBOTS_URL, b'User-agent: *\nAllow: /\n'),
                    page,
                ]
                self.assertEqual(source_governance.probe(MEDIA_URL),
                                 {'reachability': 'responded', 'http_status': 200})
        requests = [args[0] for args, _ in opener.open.call_args_list]
        self.assertEqual([(req.get_method(), req.full_url) for req in requests],
                         [('GET', ROBOTS_URL), ('HEAD', MEDIA_URL)])

    def test_missing_robots_can_use_head(self):
        for code in (404, 410):
            with self.subTest(code=code), patch.object(source_governance, 'build_opener') as build:
                opener = build.return_value
                opener.open.side_effect = [
                    HTTPError(ROBOTS_URL, code, 'Not available', Message(), None),
                    ProbeResponse(MEDIA_URL),
                ]
                self.assertEqual(source_governance.probe(MEDIA_URL),
                                 {'reachability': 'responded', 'http_status': 200})
                self.assertEqual(opener.open.call_args_list[1].args[0].get_method(), 'HEAD')

    def test_robots_restrictions_skip_head(self):
        for denial in (
            ProbeResponse(ROBOTS_URL, b'User-agent: *\nDisallow: /insights\n'),
            HTTPError(ROBOTS_URL, 401, 'Unauthorized', Message(), None),
            HTTPError(ROBOTS_URL, 403, 'Forbidden', Message(), None),
        ):
            with self.subTest(denial=denial), patch.object(source_governance, 'build_opener') as build:
                opener = build.return_value
                opener.open.side_effect = [denial]
                self.assertEqual(source_governance.probe(MEDIA_URL),
                                 {'reachability': 'policy_restricted', 'http_status': None})
                self.assertEqual(opener.open.call_count, 1)

    def test_robots_unavailable_or_invalid_skips_head(self):
        for unavailable in (
            HTTPError(ROBOTS_URL, 429, 'Rate limited', Message(), None),
            HTTPError(ROBOTS_URL, 503, 'Service unavailable', Message(), None),
            ProbeResponse(ROBOTS_URL, b'<html><title>Login</title></html>', 'text/html'),
        ):
            with self.subTest(unavailable=unavailable):
                with patch.object(source_governance, 'build_opener') as build:
                    opener = build.return_value
                    opener.open.side_effect = [unavailable]
                    self.assertEqual(source_governance.probe(MEDIA_URL),
                                     {'reachability': 'not_confirmed', 'http_status': None})
                    self.assertEqual(opener.open.call_count, 1)

    def test_existing_institution_probes_only_head(self):
        url = 'https://www.ilo.org/'
        with patch.object(source_governance, 'build_opener') as build:
            opener = build.return_value
            opener.open.side_effect = [ProbeResponse(url)]
            self.assertEqual(source_governance.probe(url),
                             {'reachability': 'responded', 'http_status': 200})
            req = opener.open.call_args.args[0]
            self.assertEqual((req.get_method(), req.full_url), ('HEAD', url))

    def test_guarded_head_redirects_keep_method_origin_and_policy(self):
        redirects = [
            (MEDIA_URL + '/public', 'responded'),
            ('https://www.oecd.org/', 'not_confirmed'),
            (MEDIA_URL + '/private', 'policy_restricted'),
        ]
        for target, reachability in redirects:
            with self.subTest(target=target), patch.object(source_governance, 'build_opener') as build:
                opener = build.return_value

                def open_request(req, **kwargs):
                    if req.full_url == ROBOTS_URL:
                        return ProbeResponse(ROBOTS_URL, b'User-agent: *\nDisallow: /insights/private\n')
                    handler = build.call_args.args[0]
                    redirected = handler.redirect_request(req, None, 301, 'Moved', Message(), target)
                    self.assertEqual(redirected.get_method(), 'HEAD')
                    return ProbeResponse(redirected.full_url)

                opener.open.side_effect = open_request
                self.assertEqual(source_governance.probe(MEDIA_URL)['reachability'], reachability)


if __name__=='__main__':
    unittest.main()
