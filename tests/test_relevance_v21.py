"""Controlled regression fixtures, not independent human-validation ground truth."""
import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from relevance_engine import analyze,decorate,digest,fingerprint,public_url,similarities
from propose_reviews import prepare,parse_body
from evaluate_relevance_v21 import evaluate

def record(title='Supplier forced labour investigation',rid='a'*18):
    return {'record_id':rid,'title':title,'kind':'discovery','url':'https://example.org/report','published_at':'2026-11-01T00:00:00Z','topics':['policy']}

def decision(r):
    return {'record_id':r['record_id'],'content_fingerprint':fingerprint(r),'expected_review_digest':digest(None),'relevance':'include','topics':['forced-labour'],'publisher_confirmed':False,'canonical_url':None,'note':'Public review fixture'}

def reviewed(r,d=None):
    return prepare({'schema_version':1,'decisions':[d or decision(r)]},{r['record_id']:r},{'schema_version':1,'records':{}},'reviewer',1,'b'*64,'2026-11-09T00:00:00Z')

class KeywordTests(unittest.TestCase):
    def test_english_german_chinese_high_priority(self):
        for title in ['Supplier forced labor scandal','Zwangsarbeit bei einem Zulieferer','供應商涉及強迫勞動調查','CSDDD implementation update','Menschenrechtliche Sorgfaltspflicht','工廠工安與欠薪爭議','Supplier trade union bargaining']:
            with self.subTest(title=title):self.assertEqual(analyze(record(title))['level'],'high')
    def test_ambiguous_context_not_high(self):
        for title in ['Forced labour','Human rights conference','Supply chain due diligence strategy']:
            self.assertEqual(analyze(record(title))['level'],'review')
    def test_false_positive_word_boundaries(self):
        for title in ['Laboratory supplier equipment','European Union referendum','AI charts in the Netherlands','Oil drilling technology supply chain','ESG Today week in review']:
            self.assertEqual(analyze(record(title))['level'],'low',title)
    def test_no_generic_disclaimer_or_query_leak(self):
        r=record('New battery product');r.update(description='forced labour in supplier factories',source='supplier human rights',publisher_hint='Forced Labour Daily',topics=['forced-labour'])
        self.assertEqual(analyze(r)['level'],'low');self.assertEqual(analyze(r)['suggested_topics'],[])
    def test_abstract_permission_and_scope(self):
        r=record('New policy');r['abstract']='Supplier human rights due diligence'
        self.assertEqual(analyze(r)['level'],'low')
        r['abstract_usage']='permitted_metadata';self.assertEqual(analyze(r)['level'],'high');self.assertEqual(analyze(r)['scope'],'title_and_permitted_abstract')
    def test_negation_is_not_claim_confirmation(self):
        a=analyze(record('Supplier denies forced labour claims'));self.assertEqual(a['level'],'high');self.assertFalse(a['claim_verified'])
    def test_case_unicode_normalization(self):
        self.assertEqual(analyze(record('ＳＵＰＰＬＩＥＲ forced LABOUR'))['level'],'high')
    def test_title_credit_does_not_supply_context(self):
        r=record('Company results - Supplier Human Rights');r['publisher_hint']='Supplier Human Rights';self.assertEqual(analyze(r)['level'],'low')
    def test_same_input_deterministic(self):
        self.assertEqual(analyze(record()),analyze(record()))
    def test_europe_signal_is_not_required(self):
        r=analyze(record('Garment industry wage theft in Bangladesh'));self.assertEqual(r['level'],'high');self.assertFalse(r['europe_mention'])

class ReviewTests(unittest.TestCase):
    def test_manual_review_survives_reanalysis(self):
        r=record();doc=reviewed(r);before=copy.deepcopy(r);a=decorate(r,doc['records']);self.assertEqual(a['effective_topics'],['forced-labour']);self.assertEqual(r,before)
        r['topics']=['research'];self.assertEqual(decorate(r,doc['records'])['review_state'],'current')
    def test_changed_text_requires_re_review(self):
        r=record();doc=reviewed(r);r['title']='Completely changed title';a=decorate(r,doc['records']);self.assertEqual(a['review_state'],'stale');self.assertTrue(a['included'])
    def test_exclusion_not_deletion(self):
        r=record();d=decision(r);d['relevance']='exclude';doc=reviewed(r,d);self.assertFalse(decorate(r,doc['records'])['included']);self.assertIn('title',r)
    def test_stale_review_conflict_rejected(self):
        r=record();doc=reviewed(r)
        with self.assertRaises(ValueError):prepare({'schema_version':1,'decisions':[decision(r)]},{r['record_id']:r},doc,'reviewer',2,'b'*64,'2026-11-09T01:00:00Z')
    def test_fingerprint_mismatch_rejected(self):
        r=record();d=decision(r);d['content_fingerprint']='0'*64
        with self.assertRaises(ValueError):reviewed(r,d)
    def test_unknown_fields_rejected(self):
        r=record();d=decision(r);d['is_admin']=True
        with self.assertRaises(ValueError):reviewed(r,d)
    def test_missing_url_cannot_confirm_publisher(self):
        r=record();d=decision(r);d['publisher_confirmed']=True
        with self.assertRaises(ValueError):reviewed(r,d)
    def test_public_link_restrictions(self):
        for url in ['javascript:alert(1)','https://127.0.0.1/x','https://localhost/x','https://user:pass@example.org','https://site.local','https://[::1]/','https://example.org:999/x']:
            with self.subTest(url=url),self.assertRaises(ValueError):public_url(url)
    def test_duplicate_json_keys_rejected(self):
        with self.assertRaises(ValueError):parse_body('SCRO_REVIEW_V1\n```json\n{"schema_version":1,"schema_version":2}\n```')
    def test_batch_duplicates_rejected(self):
        r=record();d=decision(r)
        with self.assertRaises(ValueError):prepare({'schema_version':1,'decisions':[d,d]},{r['record_id']:r},{'schema_version':1,'records':{}},'reviewer',1,'b'*64,'2026-11-09T00:00:00Z')
    def test_no_independent_labels_no_accuracy_claim(self):
        self.assertIsNone(evaluate({'cases':[{'title':'Supplier forced labour','human_label':None}]})['precision'])
    def test_similarity_is_candidate_only(self):
        rows=[record('Supplier forced labour and wage theft','a'*18),record('Factory forced labour and wage theft','b'*18)]
        idx=similarities({r['record_id']:decorate(r,{}) for r in rows});self.assertTrue(idx['a'*18]['similar']);self.assertNotIn('event_id',idx['a'*18]['similar'][0])
    def test_six_stable_topics(self):
        from relevance_engine import rules
        self.assertEqual(len(rules()['topics']),6)
if __name__=='__main__':unittest.main()
