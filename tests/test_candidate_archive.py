import hashlib,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import candidate_archive as ca
class CandidateAuditTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.old=(ca.ROOT_DIR,ca.MANIFEST)
  ca.ROOT_DIR=Path(self.tmp.name)/"candidates"
  ca.MANIFEST=ca.ROOT_DIR/"manifest.json"
 def tearDown(self):
  ca.ROOT_DIR,ca.MANIFEST=self.old
  self.tmp.cleanup()
 def sample(self):
  return {"kind":"discovery","title":"Government discusses unrelated AI research",
          "url":"https://news.google.com/rss/articles/example",
          "first_seen":"2026-11-08T10:00:00Z","published_at":"2026-11-08T09:00:00Z",
          "source_id":"worker-rights","evidence_status":"Unverified discovery",
          "screening_status":"excluded","screening_reason":"insufficient_title_evidence"}
 def test_capture_rejections_before_filter_and_idempotency(self):
  x=self.sample()
  self.assertEqual(ca.persist_candidates([x]),(1,1))
  self.assertEqual(ca.persist_candidates([x]),(1,0))
  self.assertEqual(ca.audit()["total_candidates"],1)
  rows=ca.read_month(ca.ROOT_DIR/"2026-11.jsonl")
  self.assertEqual(rows[0]["screening_status"],"excluded")
  self.assertFalse(rows[0]["publisher_verified"])
 def test_invalid_url_denied(self):
  x=self.sample();x["url"]="https://localhost/private"
  with self.assertRaises(ValueError):ca.persist_candidates([x])
if __name__=="__main__":unittest.main()
