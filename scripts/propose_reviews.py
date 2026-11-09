#!/usr/bin/env python3
"""Owner-authorized review Issue -> bounded data-only PR. Never approves or merges.

All JSON is data; no shell, eval, dynamic imports or user-controlled network targets.
GITHUB_TOKEN is used only in the GitHub-hosted job, never in published assets.
"""
from __future__ import annotations
import base64,json,os,re,sys
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from relevance_engine import ROOT,digest,fingerprint,validate_overlay,rules,public_url,ID
from build_relevance import load_records
REPO='e4e421/supply-chain-rights-observatory'
PATH='data/reviews/decisions.json'

def prepare(batch,records,overlay,actor,issue,issue_digest,now):
    validate_overlay(overlay)
    if not isinstance(batch,dict) or set(batch)!={'schema_version','decisions'} or batch['schema_version']!=1:raise ValueError('Invalid review batch')
    entries=batch['decisions']
    if not isinstance(entries,list) or not 1<=len(entries)<=25:raise ValueError('Expected 1-25 decisions')
    result=json.loads(json.dumps(overlay));seen=set()
    for row in entries:
        expected={'record_id','content_fingerprint','expected_review_digest','relevance','topics','publisher_confirmed','canonical_url','note'}
        if not isinstance(row,dict) or set(row)!=expected:raise ValueError('Unexpected review field')
        rid=row['record_id']
        if not isinstance(rid,str) or not ID.fullmatch(rid) or rid not in records or rid in seen:raise ValueError('Unknown or duplicate record')
        seen.add(rid)
        if row['content_fingerprint']!=fingerprint(records[rid]):raise ValueError('Source changed: refresh and re-review '+rid)
        if row['expected_review_digest']!=digest(overlay['records'].get(rid)):raise ValueError('Review conflict: refresh '+rid)
        result['records'][rid]={k:v for k,v in row.items() if k not in {'record_id','expected_review_digest'}}
        result['records'][rid].update(reviewed_at=now,reviewed_by=actor,issue=issue,issue_digest=issue_digest)
    validate_overlay(result)
    return result

def parse_body(body):
    if not isinstance(body,str) or len(body)>60000:raise ValueError('Review Issue too large')
    m=re.fullmatch(r'\s*SCRO_REVIEW_V1\s*```json\s*\n(.*)\n```\s*',body,re.S)
    if not m:raise ValueError('Expected SCRO_REVIEW_V1 JSON envelope; use the Workbench submit button')
    def pairs(items):
        result={}
        for key,value in items:
            if key in result:raise ValueError('Duplicate JSON key')
            result[key]=value
        return result
    return json.loads(m.group(1),object_pairs_hook=pairs)

def run():
    if os.environ.get('GITHUB_REPOSITORY')!=REPO or os.environ.get('GITHUB_REF')!='refs/heads/main':raise ValueError('Only default-branch workflow permitted')
    actor=os.environ['GITHUB_ACTOR'];owner=REPO.split('/')[0]
    if actor!=owner:raise ValueError('Only repository owner may prepare review proposals in v2.1')
    event=json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
    number=event.get('issue',{}).get('number') or event.get('inputs',{}).get('issue_number')
    if not re.fullmatch(r'[1-9]\d{0,9}',str(number or '')):raise ValueError('Invalid issue number')
    number=int(number)
    token=os.environ['GITHUB_TOKEN']
    def api(path,body=None,method=None):
        # All callers use fixed GitHub repository endpoints; original URLs are never fetched.
        req=Request('https://api.github.com/repos/'+REPO+'/'+path,
          data=json.dumps(body).encode() if body is not None else None,
          headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json',
                   'X-GitHub-Api-Version':'2022-11-28','Content-Type':'application/json','User-Agent':'SCRO-review-proposal'},
          method=method or ('POST' if body is not None else 'GET'))
        try:
            with urlopen(req,timeout=25) as r:return json.loads(r.read())
        except HTTPError as exc:raise RuntimeError('GitHub request failed: HTTP '+str(exc.code)) from None
    issue=api('issues/'+str(number))
    if issue.get('title')!='[Workbench review batch]' or issue.get('user',{}).get('login')!=owner or 'pull_request' in issue or issue.get('state')!='open':raise ValueError('Not an open owner-authored Workbench review batch')
    body=issue.get('body','');issue_hash=digest({'body':body,'updated_at':issue['updated_at']})
    batch=parse_body(body)
    current=api('contents/'+PATH+'?ref=main')
    overlay=json.loads(base64.b64decode(current['content']))
    local=json.loads((ROOT/PATH).read_text())
    if local!=overlay:raise ValueError('Default branch advanced; run preparation again')
    head=api('git/ref/heads/main')['object']['sha']
    # Check checkout revision as well, including the current discovery snapshot.
    import subprocess
    checkout=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    if checkout!=head:raise ValueError('Default branch advanced; run preparation again')
    content=prepare(batch,load_records(),overlay,actor,number,issue_hash,datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z'))
    again=api('issues/'+str(number))
    if digest({'body':again.get('body',''),'updated_at':again['updated_at']})!=issue_hash:raise ValueError('Issue edited during preparation; retry after reviewing it')
    branch='review/batch-'+str(number)+'-'+issue_hash[:12]
    existing=api('pulls?state=all&head='+owner+':'+branch)
    if existing:
        print('Review proposal already exists:',existing[0]['html_url']);return
    # Existing branch without PR is safe to resume; its sole data file is revalidated.
    try:api('git/ref/heads/'+branch)
    except RuntimeError as exc:
        if 'HTTP 404' not in str(exc):raise
        api('git/refs',{'ref':'refs/heads/'+branch,'sha':head})
    target=api('contents/'+PATH+'?ref='+branch)
    encoded=base64.b64encode((json.dumps(content,ensure_ascii=False,indent=2)+'\n').encode()).decode()
    api('contents/'+PATH,{'message':'review: propose owner decisions from issue '+str(number),'sha':target['sha'],'branch':branch,'content':encoded},'PUT')
    pr=api('pulls',{'head':branch,'base':'main','title':'Review '+str(len(batch['decisions']))+' research records (issue #'+str(number)+')',
      'body':'Owner-proposed data-only review. Check changed decisions and CI before manually merging. No event or allegation is verified by this proposal.\n\nIssue snapshot digest: `'+issue_hash+'`\n\nCloses #'+str(number)})
    print('Review proposal created:',pr['html_url'])
    summary=os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary,'a') as f:f.write('Review proposal: '+pr['html_url']+'\n\nApprove test workflows when prompted, inspect the diff, and merge manually. No changes have been published.\n')

if __name__=='__main__':
    try:run()
    except Exception as exc:
        print('Review proposal not published:',str(exc),file=sys.stderr);raise SystemExit(1)
