"""Regression tests for immutable public archives and curated source governance."""
from __future__ import annotations
import copy, hashlib, json, sys, tempfile, unittest
from pathlib import Path
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
       'topics':['policy'],'description':'Automatically discovered news lead. Trace the original reporting and independent evidence; no human rights violation is established by this record.',
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
    def test_owner_approved_media_are_manual_references(self):
        reg=json.loads(source_governance.REGISTRY.read_text())
        cand=json.loads(source_governance.CANDIDATES.read_text())
        refs=json.loads(source_governance.REFS.read_text())
        approved=[x for x in reg['sources'] if x.get('verification_level')=='owner_approved_for_manual_reference']
        self.assertEqual(len(approved),11)
        for source in approved:
            with self.subTest(source=source['id']):
                self.assertTrue(any(r['url']==source['url'] and r['name']==source['name'] for r in refs))
                self.assertFalse(any(x['id']==source['id'] for x in cand['candidates']))
                self.assertIs(source['auto_ingest'],False)
                self.assertIs(source['probe_enabled'],False)
                self.assertEqual(source['licence_review_status'],'pending')
                with self.assertRaises(ValueError):source_governance.validate_link(source['url'])
        self.assertTrue(source_governance.validate(reg,cand,refs))
        approved[0]['probe_enabled']=True
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

    def test_external_fetch_hosts_are_restricted(self):
        for url in ('http://www.ilo.org/','https://localhost/','https://example.com/',
                    'https://www.oecd.org:444/','https://www.oecd.org.evil.org/'):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):source_governance.validate_link(url)

if __name__=='__main__':
    unittest.main()
