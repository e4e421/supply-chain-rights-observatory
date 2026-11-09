"""V2 owner-authorized review publication contracts; never changes GitHub in tests."""
import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from publish_reviews import (parse_publish_body,event_scope,valid_issue,
                             already_published,ISSUE_TITLE)
from relevance_engine import digest
from propose_reviews import prepare
from test_relevance_v21 import record,decision

def envelope(obj):
    fence=chr(96)*3
    return 'SCRO_PUBLISH_V2\n'+fence+'json\n'+json.dumps(obj)+'\n'+fence

class PublishReviewTests(unittest.TestCase):
    def test_v2_is_explicit_and_v1_is_not_an_auto_publish(self):
        obj={'schema_version':1,'decisions':[]}
        self.assertEqual(parse_publish_body(envelope(obj)),obj)
        with self.assertRaises(ValueError):
            parse_publish_body(envelope(obj).replace('SCRO_PUBLISH_V2','SCRO_REVIEW_V1'))
        with self.assertRaises(ValueError):
            parse_publish_body('SCRO_PUBLISH_V2 '+json.dumps(obj))
        fence=chr(96)*3
        duplicate='SCRO_PUBLISH_V2\n'+fence+'json\n{"schema_version":1,"decisions":[],"decisions":[]}\n'+fence
        with self.assertRaises(ValueError):
            parse_publish_body(duplicate)

    def test_only_owner_default_branch_and_allowed_events(self):
        base={'GITHUB_REPOSITORY':'e4e421/supply-chain-rights-observatory',
              'GITHUB_REF':'refs/heads/main','GITHUB_ACTOR':'e4e421','GITHUB_EVENT_NAME':'issues'}
        e={'action':'opened','issue':{'number':123}}
        self.assertEqual(event_scope(base,e),(123,'e4e421'))
        for wrong in [
            {**base,'GITHUB_ACTOR':'other'},
            {**base,'GITHUB_REF':'refs/heads/side'},
            {**base,'GITHUB_REPOSITORY':'other/repo'},
            {**base,'GITHUB_EVENT_NAME':'pull_request'}]:
            with self.subTest(wrong=wrong),self.assertRaises(ValueError):
                event_scope(wrong,e)
        with self.assertRaises(ValueError):
            event_scope(base,{'action':'edited','issue':{'number':123}})
        self.assertEqual(event_scope({**base,'GITHUB_EVENT_NAME':'workflow_dispatch'},
                    {'inputs':{'issue_number':'123'}}),(123,'e4e421'))

    def test_owner_confirmed_issue_only(self):
        body=envelope({'schema_version':1,'decisions':[{'fake':'fixture'}]})
        item={'title':ISSUE_TITLE,'state':'open','user':{'login':'e4e421'},'body':body}
        self.assertEqual(valid_issue(item,'e4e421')['schema_version'],1)
        for changed in [
          {**item,'user':{'login':'attacker'}},
          {**item,'state':'closed'},
          {**item,'title':'[Workbench review batch]'},
          {**item,'pull_request':{}}]:
          with self.subTest(changed=changed),self.assertRaises(ValueError):
              valid_issue(changed,'e4e421')

    def test_review_replay_is_idempotent_only_for_matching_issue_digest(self):
        r=record();d=decision(r)
        batch={'schema_version':1,'decisions':[d]}
        issuehash='a'*64
        published=prepare(batch,{r['record_id']:r},
            {'schema_version':1,'records':{}},'e4e421',17,issuehash,'2026-11-09T00:00:00Z')
        self.assertTrue(already_published(batch,published,17,issuehash))
        self.assertFalse(already_published(batch,published,18,issuehash))
        self.assertFalse(already_published(batch,published,17,'b'*64))
        self.assertFalse(already_published(batch,{'schema_version':1,'records':{}},17,issuehash))

    def test_source_contract_keeps_v1_for_sensitive_pr_review(self):
        legacy=(ROOT/'.github/workflows/propose-review.yml').read_text()
        fresh=(ROOT/'.github/workflows/publish-review.yml').read_text()
        self.assertIn('[Workbench review batch]',legacy)
        self.assertIn('[Publish Workbench review]',fresh)
        self.assertIn('github.actor == github.repository_owner',fresh)
        self.assertIn('actions: write',fresh)
        self.assertNotIn('pull-requests: write',fresh)
        self.assertIn('persist-credentials: false',fresh)
        code=(ROOT/'scripts/publish_reviews.py').read_text()
        self.assertNotIn("api(token,'pulls'",code)
        self.assertNotIn('approve_pull',code)

    def test_workbench_publication_explains_effect(self):
        js=(ROOT/'docs/workbench/review-panel.js').read_text()
        self.assertIn('SCRO_PUBLISH_V2',js)
        self.assertIn('[Publish Workbench review]',js)
        self.assertIn('authorizes automatic publication after validation',js)
        self.assertNotIn("const body='SCRO_REVIEW_V1",js)

    def test_no_new_api_keys_or_unrelated_collection(self):
        flow=(ROOT/'.github/workflows/refresh-and-publish.yml').read_text()
        self.assertIn('deploy_only:',flow)
        self.assertIn('!inputs.deploy_only',flow)
        script=(ROOT/'scripts/publish_reviews.py').read_text()
        self.assertIn('actions/workflows/refresh-and-publish.yml/dispatches',script)
        self.assertIn('"deploy_only":"true"',script)
        self.assertIn("Path(os.environ[",script)
        self.assertIn("contents/"+'"+PATH',script)
        self.assertNotIn('eval(',script)

if __name__=='__main__':
    unittest.main()
