"""Import the historical catalogue with read-back, or collect new observations privately."""
import argparse
import json
from pathlib import Path

import archive_data
import candidate_archive
import update_data
from case_model import digest
from case_store import Firestore

ROOT=Path(__file__).resolve().parents[1]
def read(path): return json.loads((ROOT/path).read_text())

def load_history():
    records={}
    for path in sorted(archive_data.ARCHIVE.glob("????-??.jsonl")):
        for row in archive_data.load_partition(path):
            key=row["record_id"]
            if key in records: raise ValueError("Duplicate archive ID")
            records[key]=row
    candidates={}
    for path in sorted(candidate_archive.ROOT_DIR.glob("????-??.jsonl")):
        for row in candidate_archive.read_month(path): candidates[row["candidate_id"]]=row
    manifest=read("data/archive/manifest.json");cm=read("data/candidates/manifest.json")
    audit=archive_data.build_manifest()
    if audit["partitions"]!=manifest["partitions"] or len(records)!=manifest["total_records"] or candidate_archive.audit()!=cm:
        raise ValueError("Historical manifest mismatch")
    reviews=read("data/reviews/decisions.json")
    return {"researchRecords":records,"researchCandidates":candidates,"researchReviews":{
        **{rid+"-"+digest(row):dict(row,record_id=rid) for rid,row in reviews["records"].items()},
        "catalogue-"+digest({k:v for k,v in reviews.items() if k!="records"}):{k:v for k,v in reviews.items() if k!="records"}}}

def identity(row):
    return (row["kind"],row["url"],row["title"].casefold(),row.get("doi"))

def migrate(db=None):
    tables=load_history()
    counts={k:len(v) for k,v in tables.items()}
    summary={"counts":counts,"fingerprint":digest({k:{rid:digest(x) for rid,x in sorted(v.items())} for k,v in tables.items()})}
    if db:
        for table,rows in tables.items(): db.immutable(table,rows)
        db.put("caseOps","migration",{"fingerprint":summary["fingerprint"],"counts":json.dumps(counts),"verified":True})
    print(json.dumps(summary))
    return summary

def collect(db):
    marker=db.get("caseOps","migration")
    if not marker or not marker.get("verified"):
        raise ValueError("Run the read-back-verified historical import before the first private collection")
    now=update_data.utc_now(); stamp=update_data.iso(now)
    config=read("sources/queries.json")
    monitors=read("cases/monitoring.json")
    for m in monitors:
        config["news_queries"].append({"id":"case-"+m["id"],"name":"Case watch · "+m["id"],
            "query":m["query"],"locale":m["locale"],"topics":[]})
    accepted,sources,_,candidates=update_data.collect_sources(config,now)
    records={}
    for obs in accepted:
        row=archive_data.secure_record(dict(obs,id=update_data.stable_id(obs)),stamp)
        records.setdefault(row["record_id"],row)
    pool={};leads={}
    for obs in candidates:
        row=candidate_archive.row_for(obs);pool.setdefault(row["candidate_id"],row)
        if row["source_id"].startswith("case-"):
            case_id=row["source_id"][5:]
            leads[case_id+"-"+row["candidate_id"]]={"case_id":case_id,"id":row["candidate_id"],
                "title":row["title"],"url":row["url"],"status":"possible_match"}
    db.immutable("caseLeads",leads)
    db.immutable("researchCandidates",pool,identity)
    db.immutable("researchRecords",records,identity)
    successes=sum(x["status"]=="ok" for x in sources)
    previous=db.get("caseOps","collection") or {}
    status="failed" if not successes else "ok" if successes==len(sources) else "partial"
    db.put("caseOps","collection",{"status":status,"last_attempted_collection":stamp,
        "last_successful_collection":stamp if successes else previous.get("last_successful_collection"),
        "sources":json.dumps([{k:x[k] for k in ("id","status","items") if k in x} for x in sources])})
    print(f"Private collection: {status}; {len(records)} accepted IDs; {len(pool)} candidate IDs")
    if not successes: raise RuntimeError("No source succeeded")
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("operation",choices=["inventory","migrate","collect","freshness"]);action=p.parse_args().operation
    if action=="inventory": migrate()
    elif action=="migrate": migrate(Firestore())
    elif action=="collect": collect(Firestore())
    else:
        from check_freshness import collection_age
        from datetime import datetime,timezone
        collection_age(Firestore().get("caseOps","collection") or {},datetime.now(timezone.utc),18)
