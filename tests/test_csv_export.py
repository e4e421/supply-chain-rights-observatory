"""CSV research export must preserve count and prevent spreadsheet formula injection."""
from __future__ import annotations
import csv,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import archive_data,export_archive_csv

class CsvExportTests(unittest.TestCase):
    def test_formula_strings_are_neutralized(self):
        for entry in ('=1+1','+SUM(1,2)','-2+3','@HYPERLINK("a")',' \t=HYPERLINK("a")'):
            self.assertTrue(export_archive_csv.safe_cell(entry).startswith("'"))
        self.assertEqual(export_archive_csv.safe_cell('Research study'),'Research study')

    def test_public_archive_exports_full_manifest_count(self):
        manifest=archive_data.build_manifest()
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/'public.csv'
            count=export_archive_csv.export(dest)
            self.assertEqual(count,manifest['total_records'])
            with dest.open(encoding='utf-8-sig',newline='') as handle:
                rows=list(csv.reader(handle))
            self.assertEqual(len(rows),count+1)
            self.assertEqual(rows[0][0],'record_id')
            self.assertIn('event_id',rows[0])
            if count: self.assertEqual(len(rows[1]),len(rows[0]))

if __name__=='__main__':
    unittest.main()
