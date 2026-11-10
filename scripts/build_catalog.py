#!/usr/bin/env python3
"""Publish a public, sharded, static archive catalogue for GitHub Pages.

Each shard is bounded to
500 records. This is a *discovery* index; the canonical archive remains JSONL.
"""
from __future__ import annotations
import hashlib,json,re
from pathlib import Path
from archive_data import ROOT,ARCHIVE,load_partition,build_manifest
OUT=ROOT/"docs"/"data"/"archive"
CATALOG=OUT/"catalog.json"
CHUNK=500
FIELDS=("record_id","event_id","title","published_at","first_seen","source",
        "source_id","kind","evidence_status","topics","url","doi",
        "publisher_hint","publisher_verified","screening_status","screening_version")
def build():
    OUT.mkdir(parents=True,exist_ok=True)
    manifest=build_manifest()
    months=[]
    for entry in manifest["partitions"]:
        filename=entry["file"]
        if not re.fullmatch(r"\d{4}-\d{2}\.jsonl",filename):raise ValueError("Invalid monthly filename")
        rows=load_partition(ARCHIVE/filename)
        rows.sort(key=lambda r:(r.get("published_at") or "",r["record_id"]),reverse=True)
        files=[]
        for ix in range(0,len(rows),CHUNK):
            part=rows[ix:ix+CHUNK]
            projected=[{k:r[k] for k in FIELDS if k in r} for r in part]
            file=f"{filename[:7]}-{ix//CHUNK+1:04d}.json"
            content=json.dumps({"schema_version":1,"month":filename[:7],"records":projected},
                               ensure_ascii=False,separators=(",",":"))+"\n"
            (OUT/file).write_text(content,encoding="utf-8")
            files.append({"file":file,"records":len(projected),
                          "sha256":hashlib.sha256(content.encode("utf-8")).hexdigest()})
        months.append({"month":filename[:7],"records":len(rows),"files":files})
    catalog={"schema_version":1,"total_records":manifest["total_records"],
             "scope":"public_metadata_only_not_verified_incidents",
             "months":list(reversed(months)),
             "date_basis":"first_seen"}
    if sum(row["records"] for row in months)!=catalog["total_records"]:
        raise ValueError("Catalogue archive count mismatch")
    CATALOG.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Published {catalog['total_records']} searchable metadata records in {sum(len(m['files']) for m in months)} shards")
    return catalog
if __name__=="__main__":build()
