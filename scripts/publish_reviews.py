#!/usr/bin/env python3
"""Owner-authored V2 Issue -> validated review-data commit -> deploy-only dispatch.

The V1 GitHub PR workflow remains available for editorial review.
"""
from __future__ import annotations
import base64
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from propose_reviews import REPO, PATH, prepare, parse_body
from relevance_engine import ROOT, digest
from build_relevance import load_records

ISSUE_TITLE = "[Publish Workbench review]"
ISSUE_MARKER = "SCRO_PUBLISH_V2"

def parse_publish_body(body):
    if not isinstance(body,str) or not re.fullmatch(r"\s*SCRO_PUBLISH_V2\s*```json\s*\n.*\n```\s*",body,re.S):
        raise ValueError("Expected explicit SCRO_PUBLISH_V2 Issue envelope")
    return parse_body(body.replace(ISSUE_MARKER,"SCRO_REVIEW_V1",1))

def event_scope(env,event):
    if env.get("GITHUB_REPOSITORY")!=REPO or env.get("GITHUB_REF")!="refs/heads/main":
        raise ValueError("Publishing limited to default branch")
    owner=REPO.partition("/")[0]
    if env.get("GITHUB_ACTOR")!=owner:
        raise ValueError("Only repository owner may authorize auto-publication")
    if env.get("GITHUB_EVENT_NAME") not in ("issues","workflow_dispatch"):
        raise ValueError("Unsupported event")
    if env["GITHUB_EVENT_NAME"]=="issues" and event.get("action")!="opened":
        raise ValueError("Only an opened Issue may trigger publication")
    number=(event.get("issue") or {}).get("number") or (event.get("inputs") or {}).get("issue_number")
    if not re.fullmatch(r"[1-9][0-9]{0,9}",str(number or "")):
        raise ValueError("Invalid review Issue number")
    return int(number),owner

def valid_issue(issue,owner):
    if (issue.get("title")!=ISSUE_TITLE or issue.get("state")!="open"
            or issue.get("user",{}).get("login")!=owner or "pull_request" in issue):
        raise ValueError("Only open owner-authored V2 publication Issues accepted")
    return parse_publish_body(issue.get("body",""))

def already_published(batch,overlay,number,issue_hash):
    rows=batch.get("decisions")
    tags=batch.get("tag_changes",[])
    if not isinstance(rows,list) or not isinstance(tags,list) or not (rows or tags):return False
    for changes, records in ((rows,overlay["records"]),(tags,overlay.get("record_tags",{}))):
        for change in changes:
            if not isinstance(change,dict) or not isinstance(change.get("record_id"),str):return False
            saved=records.get(change["record_id"],{})
            if saved.get("issue")!=number or saved.get("issue_digest")!=issue_hash:return False
    return True

def api(token,path,method="GET",data=None):
    body=json.dumps(data).encode("utf-8") if data is not None else None
    req=Request("https://api.github.com/repos/"+REPO+"/"+path,data=body,method=method,
        headers={"Authorization":"Bearer "+token,"Accept":"application/vnd.github+json",
                 "X-GitHub-Api-Version":"2022-11-28","User-Agent":"SCRO-reviewed-publication",
                 "Content-Type":"application/json"})
    try:
        with urlopen(req,timeout=30) as response:
            content=response.read(2_000_000)
            return json.loads(content) if content else {}
    except HTTPError as ex:
        raise RuntimeError("GitHub API HTTP "+str(ex.code)+" for "+method+" "+path.split("?")[0]) from None

def preview(new_content):
    """Build and test candidate data before updating the GitHub review file."""
    (ROOT/PATH).write_text(json.dumps(new_content,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    safe_env={k:v for k,v in os.environ.items() if k not in ("GITHUB_TOKEN","GH_TOKEN")}
    for cmd in ([sys.executable,"scripts/build_portal.py"],
                [sys.executable,"scripts/build_relevance.py"],
                [sys.executable,"scripts/test_portal.py"],
                [sys.executable,"scripts/test_review_browser.py"]):
        subprocess.run(cmd,cwd=ROOT,check=True,timeout=180,env=safe_env)

def run():
    evt=json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
    number,owner=event_scope(os.environ,evt)
    token=os.environ["GITHUB_TOKEN"]
    issue=api(token,"issues/"+str(number))
    batch=valid_issue(issue,owner)
    issue_hash=digest({"body":issue["body"]})
    issue_modified_at=issue["updated_at"]

    remote=api(token,"contents/"+PATH+"?ref=main")
    overlay=json.loads(base64.b64decode(remote["content"]))
    local=json.loads((ROOT/PATH).read_text(encoding="utf-8"))
    if overlay!=local:raise ValueError("Review database differs from checked-out main")
    head=api(token,"git/ref/heads/main")["object"]["sha"]
    checkout=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
    if checkout!=head:raise ValueError("Main advanced; re-run from latest main")

    if already_published(batch,overlay,number,issue_hash):
        print("Same batch already published, retrying deploy-only dispatch")
        published_sha=head
    else:
        content=prepare(batch,load_records(),overlay,owner,number,issue_hash,
            datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"))
        preview(content)
        again=api(token,"issues/"+str(number))
        if (again["state"]!="open" or again.get("title")!=ISSUE_TITLE
                or again.get("updated_at")!=issue_modified_at
                or digest({"body":again.get("body","")})!=issue_hash):
            raise ValueError("Issue edited during validation")
        if api(token,"git/ref/heads/main")["object"]["sha"]!=head:
            raise ValueError("Main advanced during validation")
        payload=base64.b64encode((json.dumps(content,ensure_ascii=False,indent=2)+"\n").encode()).decode()
        saved=api(token,"contents/"+PATH,"PUT",{
            "message":"review: publish owner-confirmed public decisions (issue #"+str(number)+") [skip ci]",
            "content":payload,"sha":remote["sha"],"branch":"main"})
        published_sha=saved["commit"]["sha"]
        print("Public review metadata committed:",published_sha)

    # GITHUB_TOKEN pushes do not trigger Pages; workflow_dispatch is supported.
    api(token,"actions/workflows/refresh-and-publish.yml/dispatches","POST",
        {"ref":"main","inputs":{"deploy_only":"true"}})
    api(token,"issues/"+str(number)+"/comments","POST",{
        "body":"Review metadata committed as "+published_sha+
            ". A deploy-only Pages run was requested. No allegation or event identity is verified."})
    api(token,"issues/"+str(number),"PATCH",{"state":"closed","state_reason":"completed"})
    print("Owner review publication completed:",number,published_sha)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"],"a",encoding="utf-8") as out:
            out.write("Review metadata committed: "+published_sha+
                ". Deploy-only workflow dispatched; confirm its result separately.\n")

if __name__=="__main__":
    try:run()
    except Exception as exc:
        print("Owner review auto-publication stopped: "+str(exc),file=sys.stderr)
        raise SystemExit(1)
