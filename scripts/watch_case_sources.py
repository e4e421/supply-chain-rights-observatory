"""Detect revisions of allowlisted public case pages and queue private review."""
import hashlib
from html.parser import HTMLParser
import json
import os
import re
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from urllib.robotparser import RobotFileParser
from datetime import datetime,timezone
from pathlib import Path

from case_model import public_cases,source_url
from case_store import Firestore,read_publications

ROOT=Path(__file__).resolve().parents[1]
AGENT="SupplyChainRightsObservatory"
LIMIT=2_000_000
class SameHost(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        source_url(newurl)
        if urlsplit(req.full_url).netloc!=urlsplit(newurl).netloc:
            raise ValueError("Cross-host redirect requires review")
        return super().redirect_request(req,fp,code,msg,headers,newurl)

class Visible(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden=0; self.section=0; self.article=[]; self.text=[]
    def handle_starttag(self,tag,attrs):
        if tag in ("script","style","nav","footer","header","aside","noscript"): self.hidden+=1
        if tag in ("article","main"): self.section+=1
    def handle_endtag(self,tag):
        if tag in ("script","style","nav","footer","header","aside","noscript"): self.hidden=max(0,self.hidden-1)
        if tag in ("article","main"): self.section=max(0,self.section-1)
    def handle_data(self,data):
        if not self.hidden:
            self.text.append(data)
            if self.section: self.article.append(data)
def content_digest(html):
    view=Visible();view.feed(html);view.close()
    text=" ".join(" ".join(view.article or view.text).split())
    if len(text)<50: raise ValueError("Insufficient readable content")
    return hashlib.sha256(text.encode()).hexdigest()
def compare(previous,current):
    if not previous.get("hash"): return "baseline"
    return "unchanged" if previous["hash"]==current else "changed"
def fetch(opener,url,headers):
    return opener.open(Request(url,headers={"User-Agent":AGENT,**headers}),timeout=12)
def permitted(opener,url,cache):
    h=urlsplit(url).netloc
    if h not in cache:
        r=RobotFileParser()
        try:
            with fetch(opener,"https://"+h+"/robots.txt",{}) as reply:
                content=reply.read(250001)
            if len(content)>250000: raise ValueError("Large robots file")
            r.parse(content.decode("utf-8","replace").splitlines())
        except HTTPError as e:
            if e.code in (404,410): r.allow_all=True
            else: raise
        cache[h]=r
    return cache[h].can_fetch(AGENT,url)

def check(db,cases,allowed,opener=None):
    opener=opener or build_opener(SameHost()); robots={};targets={}
    for case in cases:
        for src in case["sources"]:
            url=source_url(src["url"])
            if urlsplit(url).hostname in allowed: targets.setdefault(url,set()).add(case["id"])
    for url,ids in targets.items():
        key=hashlib.sha256(url.encode()).hexdigest()
        prior=db.get("caseChecks",key) or {}
        now=datetime.now(timezone.utc).isoformat(timespec="seconds")
        state={**prior,"url":url,"last_checked_at":now,"case_ids":json.dumps(sorted(ids))}
        try:
            if not permitted(opener,url,robots): raise ValueError("Robots policy")
            headers={"Accept":"text/html"}
            if prior.get("etag"): headers["If-None-Match"]=prior["etag"]
            if prior.get("modified"): headers["If-Modified-Since"]=prior["modified"]
            with fetch(opener,url,headers) as response:
                if response.headers.get_content_type() not in ("text/html","application/xhtml+xml"): raise ValueError("Non-HTML source")
                body=response.read(LIMIT+1)
                if len(body)>LIMIT: raise ValueError("Page exceeds size limit")
                new=content_digest(body.decode(response.headers.get_content_charset() or "utf-8","replace"))
                status=compare(prior,new)
                if status=="changed":
                    # Write the queue first; retry after a failed checkpoint reuses the same transition ID.
                    change=hashlib.sha256((key+prior["hash"]+new+prior.get("last_change_at","")).encode()).hexdigest()
                    db.put("sourceChanges",change,{"case_id":", ".join(sorted(ids)),"url":url,"observed_at":now,"status":"needs_review","old_hash":prior["hash"],"new_hash":new})
                state.update(hash=new,etag=response.headers.get("ETag",""),modified=response.headers.get("Last-Modified",""),status=status)
                if status in ("changed","baseline"):state["last_change_at"]=now
        except HTTPError as e: state["status"]="unchanged" if e.code==304 and prior.get("hash") else "http_"+str(e.code)
        except (OSError,ValueError,LookupError): state["status"]="unavailable"
        db.put("caseChecks",key,state)
    print(f"Checked {len(targets)} allowlisted case source URLs")
if __name__=="__main__":
    db=Firestore()
    approved=public_cases(json.loads((ROOT/"cases/pilot.json").read_text()),read_publications(db))
    hosts=set(filter(None,(s.strip().lower() for s in os.getenv("CASE_WATCH_HOSTS","").split(","))))
    check(db,approved,hosts)
