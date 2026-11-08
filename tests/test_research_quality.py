"""Known positive and negative title fixtures; deterministic screening regression."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from research_quality import screen_title,publisher_hint,VERSION

class ScreeningTests(unittest.TestCase):
    def test_reject_audited_false_positives(self):
        for title in ("Dutch government charts its own AI course with €120 million - IO+",
                      "U.K. Bans Further Oil & Gas Drilling in North Sea - SupplyChainBrain",
                      "Is Burnham right about joining the EU single market without a referendum? - LSE",
                      "European nuclear energy supply chain: technology roadmap"):
            with self.subTest(title=title):
                self.assertEqual(screen_title(title)["status"],"excluded")
    def test_preserve_relevant_candidates(self):
        for title in ("Forced labour at textile supplier investigated",
                      "Global value chains and worker rights in garment production",
                      "Corporate human rights due diligence and supplier governance",
                      "Supply network traceability and worker grievances",
                      "Social sustainability in multi-tier procurement"):
            with self.subTest(title=title):
                self.assertEqual(screen_title(title)["status"],"candidate_relevant")
    def test_broader_academic_terminology(self):
        self.assertEqual(screen_title("Corporate accountability for human rights",academic=True)["status"],"candidate_relevant")
    def test_publisher_is_only_unverified_hint(self):
        self.assertEqual(publisher_hint("Supply chain forced labour claims - Example News"),"Example News")
        self.assertIsNone(publisher_hint("Supply chain forced labour claims"))
if __name__=="__main__":unittest.main()
