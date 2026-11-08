"""Public, bounded, append-only capture of discovery candidates before relevance screening.

Store only the same public title/URL/date already exposed in feeds. Rejected
headlines remain labelled "not assessed" (NOT innocent or proven). This is
not a confidential interview or subject-level research database.
"""
from __future__ import annotations
import hashlib,json,re
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1]
ROOT_DIR=ROOT/"data"/"candidates"
MANIFEST=ROOT_DIR/"manifest.json"
LIMIT_BYTES=25_000_000
MAX_CANDIDATES=150000
def compact(row):
    return json.dumps(row,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n"
def month(first_seen):
    dt=datetime.fromisoformat(first_seen.replace("Z","+00:00"))
    if dt.tzinfo is None or not 2020<=dt.year<=2100: raise ValueError("Invalid first observation")
    return f"{dt.year:04d}-{dt.month:02d}.jsonl"
def row_for(item):
    url=urlparse(str(item.get("url","")))
    if (url.scheme!="https" or url.hostname not in {"news.google.com","doi.org"}
            or url.username or url.password or url.port not in (None,443)):
        raise ValueError("Untrusted public discovery URL")
    title=item.get("title")
    if not isinstance(title,str) or not 0<len(title)<=240:
        raise ValueError("Invalid title")
    if item.get("kind") not in ("academic","discovery"):
        raise ValueError("Invalid type")
    fields=("title","url","published_at","first_seen","source_id","kind","evidence_status")
    row={k:item[k] for k in fields if k in item}
    row["candidate_id"]=hashlib.sha256((str(item["kind"])+"|"+item["url"]+"|"+title.casefold()).encode()).hexdigest()[:24]
    row["research_status"]="unverified_discovery"
    row["screening_version"]=item.get("screening_version","legacy-unscreened")
    row["screening_status"]=item.get("screening_status","not_screened")
    row["screening_reason"]=item.get("screening_reason","not_screened")
    row["publisher_hint"]=item.get("publisher_hint")
    row["publisher_verified"]=False
    row["schema_version"]=1
    if len(compact(row).encode())>5000: raise ValueError("Candidate row too large")
    month(row["first_seen"])
    return row
def read_month(file):
    if not file.exists():return []
    if file.is_symlink() or file.stat().st_size>LIMIT_BYTES:raise ValueError("Unsafe candidate partition")
    rows=[]
    for ln in file.read_text(encoding="utf-8").splitlines():
        if not ln.strip():continue
        if len(ln.encode())>5000:raise ValueError("Oversized candidate line")
        row=json.loads(ln)
        if not re.fullmatch("[a-f0-9]{24}",str(row.get("candidate_id",""))):raise ValueError("Invalid candidate ID")
        rows.append(row)
    return rows
def audit():
    counts=0;manifest=[];seen=set()
    for file in sorted(ROOT_DIR.glob("????-??.jsonl")):
        rows=read_month(file)
        for row in rows:
            if row["candidate_id"] in seen:raise ValueError("Duplicate candidate")
            seen.add(row["candidate_id"])
            if month(row["first_seen"])!=file.name:raise ValueError("Wrong candidate month")
        counts+=len(rows)
        if counts>MAX_CANDIDATES:raise ValueError("Candidate archive capacity reached")
        content=file.read_bytes()
        manifest.append({"file":file.name,"records":len(rows),"sha256":hashlib.sha256(content).hexdigest()})
    return {"schema_version":1,"total_candidates":counts,"partitions":manifest}
def persist_candidates(items):
    ROOT_DIR.mkdir(parents=True,exist_ok=True)
    prior={}
    for f in sorted(ROOT_DIR.glob("????-??.jsonl")):
        for row in read_month(f):
            prior[row["candidate_id"]]=row
    additions={}
    for item in items:
        row=row_for(item)
        key=row["candidate_id"]
        if key in prior:continue
        prior[key]=row
        path=ROOT_DIR/month(row["first_seen"])
        additions.setdefault(path,[]).append(row)
    if len(prior)>MAX_CANDIDATES:raise ValueError("Candidate archive capacity reached")
    prepared={}
    for path,entries in additions.items():
        before=path.read_text(encoding="utf-8") if path.exists() else ""
        content=before+"".join(compact(row) for row in sorted(entries,key=lambda x:x["candidate_id"]))
        if len(content.encode())>LIMIT_BYTES:raise ValueError("Monthly candidate partition capacity reached")
        prepared[path]=content
    for path,content in prepared.items():path.write_text(content,encoding="utf-8")
    manifest=audit()
    MANIFEST.write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    return manifest["total_candidates"],sum(map(len,additions.values()))
