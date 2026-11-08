import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import build_catalog as c
import archive_data as a
class CatalogTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.old=(c.OUT,c.CATALOG,c.ARCHIVE,a.ARCHIVE,a.MANIFEST,a.PUBLIC_SUMMARY)
  root=Path(self.tmp.name)
  a.ARCHIVE=root/"archive";a.MANIFEST=a.ARCHIVE/"manifest.json";a.PUBLIC_SUMMARY=root/"pages"/"archive-summary.json"
  a.PUBLIC_SUMMARY.parent.mkdir(parents=True,exist_ok=True)
  c.ARCHIVE=a.ARCHIVE;c.OUT=root/"pages";c.CATALOG=c.OUT/"catalog.json"
 def tearDown(self):
  c.OUT,c.CATALOG,c.ARCHIVE,a.ARCHIVE,a.MANIFEST,a.PUBLIC_SUMMARY=self.old
  self.tmp.cleanup()
 def test_archive_month_catalog_reconstructs_metadata(self):
  row={"id":"a"*18,"kind":"discovery","title":"Supply chain worker rights report",
  "url":"https://news.google.com/rss/articles/1","published_at":"2026-11-05T00:00:00Z",
  "first_seen":"2026-11-08T01:00:00Z","source":"Sample","source_id":"sample",
  "evidence_status":"Unverified discovery","topics":["working-conditions"],
  "description":"Unverified news discovery"}
  a.persist([row],"2026-11-08T01:00:00Z")
  catalog=c.build()
  self.assertEqual(catalog["total_records"],1)
  self.assertEqual(catalog["months"][0]["month"],"2026-11")
  shard=json.loads((c.OUT/catalog["months"][0]["files"][0]["file"]).read_text())
  self.assertEqual(shard["records"][0]["record_id"],"a"*18)
if __name__=="__main__":unittest.main()
