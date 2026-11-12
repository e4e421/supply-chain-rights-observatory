"""Static regression tests for the second GitHub Pages entrypoint."""
import re
import unittest
from pathlib import Path
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1]
HOME=(ROOT/"docs/index.html").read_text(encoding="utf-8")
WB=(ROOT/"docs/workbench/index.html").read_text(encoding="utf-8")
JS=(ROOT/"docs/workbench/workbench.js").read_text(encoding="utf-8")
CSS=(ROOT/"docs/workbench/workbench.css").read_text(encoding="utf-8")
class Markup(HTMLParser):
 def __init__(self):
  super().__init__(); self.ids=set();self.links=[];self.lang=None
 def handle_starttag(self,tag,attrs):
  d=dict(attrs)
  if tag=="html":self.lang=d.get("lang")
  if "id" in d:self.ids.add(d["id"])
  if tag=="script":self.links.append(d.get("src"))
class WorkbenchContractTests(unittest.TestCase):
 def test_two_distinct_public_frontends(self):
  self.assertIn('href="./workbench/"',HOME)
  self.assertIn('href="../index.html"',WB)
  m=Markup();m.feed(WB)
  self.assertEqual(m.lang,"en")
  self.assertIn("../i18n.js",m.links)
  self.assertIn("../query.js",m.links)
  self.assertIn("./workbench.js",m.links)
  required=["wb-search","wb-sort","wb-searchable-count","wb-tbody","wb-detail",
            "wb-count","wb-export","wb-share","wb-save","wb-saved-list","wb-more",
            "wb-legacy-month","wb-legacy-month-value","wb-clear-legacy-month"]
  self.assertTrue(set(required).issubset(m.ids))
  self.assertTrue({"wb-scope","wb-month","wb-latest-count","wb-archive-count"}.isdisjoint(m.ids))
  self.assertNotIn("data-scope=",WB)
  self.assertNotIn("wb-quality", m.ids)
 def test_public_research_safety(self):
  self.assertIn("Content-Security-Policy",WB)
  self.assertNotIn("innerHTML",JS)
  self.assertNotIn("eval(",JS)
  self.assertNotIn("document.write(",JS)
  self.assertIn("textContent",JS)
  self.assertIn("noopener noreferrer",JS)
  self.assertIn("csvCell",JS)
  self.assertIn("MAX_FILES=24",JS)
  self.assertIn("coveragePartial",JS)
  self.assertNotIn("sourceInfo()",JS)
 def test_bloomberg_style_workflow(self):
  self.assertIn("localStorage",JS)
  self.assertIn("history.replaceState",JS)
  self.assertIn("window.SCRO_QUERY",JS)
  self.assertIn("keydown",JS)
  self.assertIn("j",JS)
  self.assertIn("wb-table",WB)
  self.assertIn("grid-template-columns",CSS)
  self.assertIn("max-width:820px",CSS)
 def test_language_contract(self):
  for language in ["zh","de"]:
   self.assertIn(language+":{",JS)
  self.assertIn("data-l10n",WB)
  self.assertIn("Research Workbench",WB)
if __name__=="__main__":unittest.main()
