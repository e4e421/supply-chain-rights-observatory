import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from build_case_release import produce
import case_assist as assist
from case_model import validate_case,public_cases
from evaluate_case_matching import evaluate
from private_collection import migrate
from verify_case_deploy import verify
from watch_case_sources import compare, content_digest

class CaseTrackingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases=json.loads((ROOT/"cases/pilot.json").read_text())
    def test_public_cases_timeline_and_clocks(self):
        rows=public_cases(self.cases)
        self.assertEqual(len(rows),5)
        nickel=rows[0]
        self.assertEqual(nickel["follow_up_on"],"2026-12-01")
        response=next(s for s in nickel["sources"] if s["id"]=="bmw")
        self.assertEqual(response["published_on"],"2026-11-09")
        self.assertTrue(response["feed_published_at"].startswith("2026-11-10"))
        self.assertTrue(any(m["on"] is None for m in nickel["timeline"]))
    def test_private_fields_cannot_cross_public_schema(self):
        for path in [(),("timeline",0),("sources",0),("title",)]:
            c=copy.deepcopy(self.cases[0]);target=c
            for k in path:target=target[k]
            target["private_note"]="PRIVATE-CANARY"
            with self.subTest(path=path),self.assertRaises(ValueError):validate_case(c)
    def test_evidence_link_and_url_required(self):
        for mutation in ("source","url","date"):
            c=copy.deepcopy(self.cases[0])
            if mutation=="source":c["timeline"][0]["source"]="missing"
            if mutation=="url":c["sources"][0]["url"]="javascript:sample"
            if mutation=="date":c["timeline"][0]["on"]="2026-02-31"
            with self.assertRaises(ValueError):validate_case(c)
    def test_correction_and_withdrawal_override_pilot(self):
        c=copy.deepcopy(self.cases[0]);c["focus"]["zh"]="更正摘要"
        cases=public_cases(self.cases,[(c["id"],{"state":"approved","public":c,"note":"PRIVATE-CANARY"}),(self.cases[1]["id"],{"state":"withdrawn"})])
        self.assertEqual(cases[0]["focus"]["zh"],"更正摘要")
        self.assertEqual(len(cases),4);self.assertNotIn("PRIVATE-CANARY",str(cases))
    def test_release_contains_only_projected_sources_and_verified_revision(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);produce(out,self.cases,{"status":"partial","last_successful_collection":"2026-11-23T22:06:52Z"},"a"*40)
            manifest=json.loads((out/"data/release.json").read_text())
            verify(manifest,lambda path,limit:(out/path).read_bytes())
            approved={src["url"] for case in self.cases for src in case["sources"]}
            snap=json.loads((out/"data/latest.json").read_text())
            self.assertEqual({r["url"] for r in snap["items"]},approved)
            self.assertFalse(list(out.rglob("*.jsonl")))
            allowed={"cases.json","references.json","source-health.json","latest.json","record-index.json","build-info.json","release.json"}
            self.assertEqual({f.name for f in (out/"data").glob("*.json")},allowed)
            self.assertFalse((out/"data/relevance-validation-sample.json").exists())
            self.assertNotIn("github.com/e4e421/supply-chain-rights-observatory/issues/new",(out/"team/index.html").read_text())
            self.assertIn("3c977f8fb63d9db9d0",(out/"data/record-index.json").read_text())
            self.assertNotIn("a14ee2760fbb9718a3",(out/"data/record-index.json").read_text())
            self.assertEqual(len(list((out/"cases").glob("*/index.html"))),len(self.cases))
    def test_migration_inventory(self):
        counts=migrate()["counts"]
        self.assertEqual(counts["researchRecords"],json.loads((ROOT/"data/archive/manifest.json").read_text())["total_records"])
        self.assertEqual(counts["researchCandidates"],json.loads((ROOT/"data/candidates/manifest.json").read_text())["total_candidates"])
    def test_same_page_updates_and_navigation_noise(self):
        text="The monitoring agency describes the action taken by the company."
        html="<main><article>"+text+"</article></main>"
        d=content_digest(html)
        self.assertEqual(d,content_digest("<nav>menu changed</nav>"+html))
        self.assertEqual(compare({},d),"baseline")
        self.assertEqual(compare({"hash":d},d),"unchanged")
        self.assertEqual(compare({"hash":d},content_digest(html.replace("action","remedy"))),"changed")
    def test_bounded_llm_and_support_span(self):
        s=[{"id":"src","url":"https://example.org/source","visibility":"public","excerpt":"BMW replied on 2026-11-09."}]
        self.assertEqual(assist.packet({"sources":s}),s)
        c=self.cases[:1];point={"source_id":"src","evidence":s[0]["excerpt"],"kind":"response","actor":"BMW","date":"2026-11-09","summary_zh":"BMW 回應。","summary_en":"BMW responded."}
        r={"case_id":c[0]["id"],"disposition":"new_development","points":[point]}
        self.assertEqual(assist.validate(r,c,s),r)
        for k,bad in [("source_id","absent"),("evidence","absent"),("date","2026-11-18")]:
            with self.assertRaises(ValueError):assist.validate({**r,"points":[{**point,k:bad}]},c,s)
        with self.assertRaises(ValueError):assist.packet({"sources":[{**s[0],"visibility":"private"}]})
        with self.assertRaises(ValueError):assist.packet({"sources":[{**s[0],"private_note":"internal"}]})
        with self.assertRaises(ValueError):assist.validate({**r,"case_id":"invented"},c,s)
    def test_shortlist_fixture(self):
        scores=evaluate()
        self.assertEqual(scores["top1_correct"],scores["match_examples"])
        self.assertEqual(scores["unrelated_examples"],scores["correct_abstentions"])
    def test_production_workflow_uses_allowlist_release(self):
        flow=(ROOT/"deployment/firebase/refresh-and-publish.yml").read_text()
        self.assertIn("path: ./_release",flow);self.assertNotIn("git push",flow)
        self.assertNotIn("contents: write",flow);self.assertNotIn("OPENAI_API_KEY",flow)
        self.assertIn("case",flow)
