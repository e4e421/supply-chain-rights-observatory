"""Build the production Pages artifact from a field-validated case catalogue."""
import argparse
from datetime import datetime, timezone
import hashlib
from html import escape
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

import build_portal as legacy
from case_model import public_cases
from case_store import Firestore, read_publications

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"_release"
KINDS={"report":("Report","報導"),"response":("Response","已回應"),"no_response":("No response recorded","來源註記未回應"),
       "commitment":("Commitment","承諾"),"procedure":("Procedure","程序進展"),"worker_voice":("Worker voice","勞工觀點"),
       "remedy":("Remedy","補救"),"correction":("Correction","更正")}
GAPS={"response":("Response due","待回應"),"remedy":("Remedy evidence","待補救證據"),"voice":("Rights-holder perspective","待權利人觀點"),"procedure":("Procedure to verify","待查程序")}
def words(en,zh):
    return '<span lang="en" class="en">'+escape(en)+'</span><span lang="zh-Hant" class="zh">'+escape(zh)+'</span>'
def loc(obj): return words(obj["en"],obj["zh"])
def write(root,path,content):
    f=root/path
    f.parent.mkdir(parents=True,exist_ok=True)
    f.write_text(content,encoding="utf-8")
def put(root,path,data):
    write(root,path,json.dumps(data,ensure_ascii=False,separators=(",",":"))+"\n")
def tags_for_root(body,base,head,extra="",team=False):
    csp="default-src 'none'; style-src 'self'; script-src 'self'; img-src 'self'; connect-src 'self' https://api.github.com"
    if team: csp+=" https://identitytoolkit.googleapis.com https://firestore.googleapis.com"
    csp+="; font-src 'self'; form-action 'none'; base-uri 'none'; frame-src 'none'; object-src 'none'"
    nav=''.join(f'<a data-local href="{base}{path}/">{words(en,zh)}</a>' for path,en,zh in [
        ("cases","Cases","案件"),("workbench","Source search","來源搜尋"),("sources","Directory","來源目錄"),("policy","Policy","政策"),("research","Research","研究"),("team","Team","研究後台")])
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="referrer" content="no-referrer"><meta http-equiv="Content-Security-Policy" content="{csp}">
<title>{escape(head)} | Supply Chain Rights Observatory</title><link rel="stylesheet" href="{base}case.css">
<script defer src="{base}case.js"></script>{extra}</head><body><a href="#main" class="skip">{words("Skip to content","跳至內容")}</a>
<header><a data-local class="brand" href="{base}index.html">Supply Chain Rights Observatory</a><nav>{nav}<select id="lang" aria-label="Language / 語言"><option value="en">EN</option><option value="zh">繁中</option></select></nav></header>
<main id="main">{body}</main><footer><a data-local href="{base}methodology/">{words("Methods and publication scope","研究方法與公開範圍")}</a></footer></body></html>'''

def index(cases,base,collection,run):
    options=[("all","All cases","所有案件"),("recent","New developments in 7 days","近七日有進展"),("due","Due within 7 days or overdue","七日內到期或逾期")]
    options.extend((k,*v) for k,v in GAPS.items())
    filters=''.join(f'<option value="{k}">{zh} · {en}</option>' for k,en,zh in options)
    cards=[]
    for case in sorted(cases,key=lambda c:(c["follow_up_on"] is None,c["follow_up_on"] or "",c["id"])):
        source_dates={s["id"]:s["published_on"] or "" for s in case["sources"]}
        latest=max(case["timeline"],key=lambda m:m["on"] or source_dates[m["source"]])
        dated=[m["on"] or source_dates[m["source"]] for m in case["timeline"]]
        search=escape(" ".join([case["id"],case["rights_holders"]["zh"],case["rights_holders"]["en"],
                                *(m["actor"] for m in case["timeline"]),*(s["publisher"] for s in case["sources"])]),quote=True)
        cards.append(f'''<article class="card" data-search="{search}" data-gap="{case["gap"]}" data-due="{case["follow_up_on"] or ""}" data-latest="{max(dated,default="")}">
<p class="meta">{case["place"]} · {words(*GAPS[case["gap"]])}</p>
<h2><a data-local href="{base}cases/{case["id"]}/">{loc(case["title"])}</a></h2><p>{loc(case["focus"])}</p>
<p><strong>{words("Latest documented change","最近有據進展")}</strong> · {loc(latest["text"])}</p>
<p class="gap">{words("Next check","下次查核")} · {case["follow_up_on"] or words("Historical case","歷史案例")}</p></article>''')
    return f'''<div class="hero"><h1>{words("Case tracking","供應鏈人權案件追蹤")}</h1><p>{words("Trace changes, responses and remedy to their sources.","從原始來源追蹤案件進展、企業回應與補救成效。")}</p></div>
<div class="meta">{words("Last successful collection (UTC)","最近成功蒐集（UTC）")} · {escape(collection or "—")}<br>
{words("Confirmed Pages publication (UTC)","已確認的 Pages 發布（UTC）")} · <span id="release-time" data-run="{escape(run)}">—</span></div>
<h2>{words("Tracking queue","追蹤清單")}</h2><div class="controls">
<label>{words("Search cases","搜尋案件")} <input type="search" id="case-search"></label><label>{words("Follow-up","追蹤條件")} <select id="case-filter">{filters}</select></label>
<span role="status"><b id="count">{len(cases)}</b> {words("cases","案")}</span></div><div class="grid">{''.join(cards)}</div>'''

def detail(c):
    src_by={s["id"]:s for s in c["sources"]}
    milestones=[]
    for item in c["timeline"]:
        s=src_by[item["source"]]
        ref=f'<a href="{escape(s["url"],quote=True)}">{escape(s["publisher"])}</a>'
        event_day=item["on"] or words("Exact day unspecified","確切日期未載")
        milestones.append(f'<li><p class="meta">{event_day} · {words(*KINDS[item["kind"]])} · {escape(item["actor"])}</p><p>{loc(item["text"])}</p><small>{ref}</small></li>')
    source_rows=[]
    for s in c["sources"]:
        source_rows.append(f'<li class="evidence"><a href="{escape(s["url"],quote=True)}">{escape(s["publisher"])}</a> · {words("Source date","來源日期")} {escape(s["published_on"] or "—")} · RSS {escape(s["feed_published_at"] or "—")} · {words("First observation","首次收錄")} {escape(s["first_seen_at"] or "—")}</li>')
    return f'''<div class="hero"><p class="meta">{c["place"]} · {escape(c["id"])}</p><h1>{loc(c["title"])}</h1><p>{loc(c["focus"])}</p>
<p>{words("Rights holders","權利受影響者")} · {loc(c["rights_holders"])}</p></div><section class="panel"><strong>{words(*GAPS[c["gap"]])}</strong>
<p>{loc(c["follow_up"])}</p><p class="meta">{words("Next editorial check","編審預定查核日")} · {c["follow_up_on"] or "—"}</p></section>
<h2>{words("Timeline","案件時間線")}</h2><ol class="timeline">{''.join(milestones)}</ol>
<h2>{words("Source dates and provenance","來源日期與出處")}</h2><ul>{''.join(source_rows)}</ul><p class="meta">{words("Sources last checked","最近核對來源")} · {c["source_checked_on"]}</p>'''

def public_index(root,cases,meta,revision):
    rows={}
    for case in cases:
        for src in case["sources"]:
            rid=src["record_id"] or hashlib.sha256(src["url"].encode()).hexdigest()[:18]
            first=src["first_seen_at"] or case["source_checked_on"]+"T00:00:00Z"
            row={"record_id":rid,"event_id":case["id"],"title":case["title"]["en"]+" · "+src["publisher"],
                 "source":src["publisher"],"publisher_hint":src["publisher"],"source_id":"case-evidence",
                 "published_at":src["published_on"]+"T00:00:00Z" if src["published_on"] else None,
                 "first_seen":first,"kind":"discovery","evidence_status":"Cited case source","url":src["url"],"topics":[]}
            if rid in rows:
                previous=rows[rid]
                if previous["url"]!=row["url"]: raise ValueError("Public record ID collision")
                if case["id"] not in previous["case_ids"]:
                    previous["case_ids"].append(case["id"])
                    previous["event_id"]=None
                continue
            row["case_ids"]=[case["id"]]
            rows[rid]=row
    months={}
    for row in rows.values(): months.setdefault(row["first_seen"][:7],[]).append(row)
    groups=[];locator={}
    for month,items in sorted(months.items(),reverse=True):
        files=[]
        for i in range(0,len(items),500):
            chunk=items[i:i+500];file=f"{month}-{i//500+1:04d}.json"
            path="data/archive/"+file
            put(root,path,{"schema_version":1,"month":month,"records":chunk})
            files.append({"file":file,"records":len(chunk),"sha256":hashlib.sha256((root/path).read_bytes()).hexdigest()})
            for row in chunk: locator[row["record_id"]]={"month":month,"file":file}
        groups.append({"month":month,"records":len(items),"files":files})
    put(root,"data/archive/catalog.json",{"schema_version":1,"scope":"approved_case_sources","total_records":len(rows),"months":groups})
    put(root,"data/record-index.json",{"schema_version":1,"records":locator})
    put(root,"data/latest.json",{"schema_version":1,**meta,"sources":[],"items":[dict(row,id=rid) for rid,row in rows.items()]})
    put(root,"data/build-info.json",{"schema_version":1,"git_revision":revision,"catalog_sha256":hashlib.sha256((root/"data/archive/catalog.json").read_bytes()).hexdigest()})

def produce(out, cases, meta, revision, run="", config=None):
    # This directory starts empty. Never copy docs/data, review exports, or the old _site tree.
    if any(out.iterdir()): raise ValueError("Release staging must start empty")
    assets=("styles.css","i18n.js","collection-time.js","query.js","workbench/index.html","workbench/workbench.css",
            "workbench/workbench.js","workbench/record-tags.js","workbench/pagination.css")
    for name in assets:
        dst=out/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/"docs"/name,dst)
    for name in ("portal.js","portal.css","portal-translations.json"): shutil.copyfile(ROOT/"portal"/name,out/name)
    for name in ("case.css","case.js","team.js"): shutil.copyfile(ROOT/"cases"/name,out/name)
    old=legacy.OUT
    try:
        legacy.OUT=out
        legacy.build_reference_pages()
        for page in ("sources","policy","research"):
            fp=out/page/"index.html"
            page_text=fp.read_text().replace('<nav class="portal-nav" aria-label="Main navigation">','<nav class="portal-nav" aria-label="Main navigation"><a href="../cases/">Cases · 案件</a>')
            page_text=re.sub(r'<noscript>.*?</noscript>','',page_text,flags=re.S)
            fp.write_text(page_text)
    finally: legacy.OUT=old
    ref=json.loads((ROOT/"docs/data/references.json").read_text())
    put(out,"data/references.json",[{k:r[k] for k in ("category","name","mode","url","use") if k in r} for r in ref])
    health=json.loads((ROOT/"docs/data/source-health.json").read_text())
    fields="id name url authority_type editorial_status last_editorial_review review_due licence_review_status review_needed reachability http_status last_probe last_successful_probe failure_kind consecutive_failures".split()
    put(out,"data/source-health.json",{"sources":[{k:r[k] for k in fields if k in r} for r in health["sources"]]})
    public_index(out,cases,meta,revision)
    put(out,"data/cases.json",{"schema_version":1,"cases":cases})
    put(out,"team/config.json",config or {})
    write(out,".nojekyll","")
    for page,base in [("index.html","./"),("cases/index.html","../")]:
        write(out,page,tags_for_root(index(cases,base,meta.get("last_successful_collection"),run),base,"Case tracking"))
    for item in cases:
        write(out,"cases/"+item["id"]+"/index.html",tags_for_root(detail(item),"../../",item["title"]["en"]))
    wb=out/"workbench/index.html"
    wb.write_text(wb.read_text().replace('<header class="wb-header">','<header class="wb-header"><a href="../cases/">Cases · 案件</a><a href="../team/">Team · 研究後台</a>').replace("../index.html#sources","../sources/").replace("../index.html#method","../methodology/"))
    # Preserve old routes without exposing an archive beyond the approved source index.
    for path,target in [("workbench/edit/index.html","../../team/"),("archive/index.html","../workbench/")]:
        write(out,path,f'<!doctype html><meta charset="utf-8"><title>Observatory</title><a id="route" href="{target}">Continue / 繼續</a><script src="{target}../route.js"></script>')
    write(out,"record.html",tags_for_root('<h1>'+words("Publication record","出版紀錄")+'</h1><a id="record-link" href="workbench/">'+words("Open source search","開啟來源搜尋")+'</a>','./',"Record",'<script defer src="./route.js"></script>'))
    write(out,"route.js","const r=document.querySelector('#route'); if(r)location.replace(r.href+location.search+location.hash);const a=document.querySelector('#record-link');if(a){const id=new URLSearchParams(location.search).get('id');if(/^[0-9a-f]{18}$/.test(id)){a.href+='?record='+id;location.replace(a.href);}}")
    method=words("Only sources cited in released cases appear in public search and CSV. Case milestones identify who said or did what. A published allegation, an actor’s response and verified remedy are recorded separately.", "公開搜尋與 CSV 收錄已發布案件引用的來源。每一筆進展標明行動者，分別記錄指控、當事方回應及可佐證的補救。")
    write(out,"methodology/index.html",tags_for_root("<h1>"+words("Methods","研究方法")+"</h1><p>"+method+"</p>","../","Methods"))
    body=(ROOT/"cases/team.html").read_text()
    write(out,"team/index.html",tags_for_root(body,"../","Private research desk",'<script defer src="../team.js"></script>',team=True))
    put(out,"data/release.json",{"revision":revision,"workflow_run":run,"collection":meta,
        "case_count":len(cases),"cases_sha256":hashlib.sha256((out/"data/cases.json").read_bytes()).hexdigest()})

def attach_pilot(site):
    """Add case tracking to the existing portal while the private backend is provisioned."""
    cases=public_cases(json.loads((ROOT/"cases/pilot.json").read_text()))
    meta=json.loads((site/"data/latest.json").read_text())
    for name in ("case.css","case.js","team.js"):
        shutil.copyfile(ROOT/"cases"/name,site/name)
    write(site,"cases/index.html",tags_for_root(index(cases,"../",meta.get("last_successful_collection"),os.getenv("GITHUB_RUN_ID","")),"../","Case tracking"))
    for case in cases:
        write(site,"cases/"+case["id"]+"/index.html",tags_for_root(detail(case),"../../",case["title"]["en"]))
    put(site,"data/cases.json",{"schema_version":1,"cases":cases})
    stamp=json.loads((site/"data/build-info.json").read_text())
    stamp["cases_sha256"]=hashlib.sha256((site/"data/cases.json").read_bytes()).hexdigest()
    put(site,"data/build-info.json",stamp)
    put(site,"team/config.json",{})
    write(site,"team/index.html",tags_for_root((ROOT/"cases/team.html").read_text(),"../","Private research desk",
        '<script defer src="../team.js"></script>',team=True))
    for page in ("index.html","workbench/index.html","sources/index.html","policy/index.html","research/index.html","methodology/index.html"):
        f=site/page;base="./" if page=="index.html" else "../"
        content=f.read_text()
        anchor='<header class="wb-header">' if page.startswith("workbench") else '<nav class="portal-nav" aria-label="Main navigation">'
        if anchor not in content: raise ValueError("Case navigation anchor missing: "+page)
        f.write_text(content.replace(anchor,anchor+'<a href="'+base+'cases/">Cases · 案件追蹤</a>',1))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--firebase",action="store_true")
    args=parser.parse_args()
    snap=json.loads((ROOT/"docs/data/latest.json").read_text()) if (ROOT/"docs/data/latest.json").exists() else {}
    meta={k:snap.get(k) for k in ("status","last_successful_collection","last_attempted_collection")}
    approvals=[];config={}
    if args.firebase:
        db=Firestore();approvals=list(read_publications(db))
        status=db.get("caseOps","collection")
        if status: meta={k:status.get(k) for k in meta}
        config={"project":os.environ["FIREBASE_PROJECT_ID"],"apiKey":os.environ["FIREBASE_WEB_API_KEY"]}
    cases=public_cases(json.loads((ROOT/"cases/pilot.json").read_text()),approvals)
    revision=os.environ.get("GITHUB_SHA") or subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
    with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
        root=Path(tmp)/"release";root.mkdir()
        produce(root,cases,meta,revision,os.getenv("GITHUB_RUN_ID",""),config)
        if OUT.exists(): shutil.rmtree(OUT)
        shutil.move(str(root),OUT)
    print(f"Case release built: {len(cases)} cases")
if __name__=="__main__": main()
