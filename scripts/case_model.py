"""Validate the complete public projection before a case can enter a Pages artifact."""
from datetime import date, datetime
import hashlib
import json
import re
from urllib.parse import urlsplit

SLUG = re.compile(r"[a-z][a-z0-9-]{1,70}")
KINDS = {"report", "response", "no_response", "commitment", "procedure", "worker_voice", "remedy", "correction"}
GAPS = {"response", "procedure", "voice", "remedy"}

def keys(row, names):
    if not isinstance(row, dict) or set(row) != set(names.split()):
        raise ValueError("Unexpected or missing publication fields")

def plain(value, limit=700):
    if not isinstance(value, str) or not 0 < len(value.strip()) <= limit or any(ord(ch)<32 for ch in value):
        raise ValueError("Invalid public text")
    return value

def bilingual(value):
    keys(value, "en zh")
    for text in value.values():
        plain(text)

def day(value):
    if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
        raise ValueError("Use an ISO calendar date")

def source_url(value):
    plain(value, 1600)
    p = urlsplit(value)
    if (p.scheme != "https" or not p.hostname or "." not in p.hostname or p.username is not None
            or p.password is not None or p.port not in (None,443) or any(c.isspace() for c in value)):
        raise ValueError("Invalid public source URL")
    return value

def validate_case(row):
    keys(row, "id title place rights_holders focus follow_up_on follow_up gap source_checked_on sources timeline")
    if not SLUG.fullmatch(row["id"]) or not re.fullmatch("[A-Z]{2}",row["place"]) or row["gap"] not in GAPS:
        raise ValueError("Invalid case ID, country or follow-up category")
    for field in ("title","rights_holders","focus","follow_up"):
        bilingual(row[field])
    day(row["source_checked_on"])
    if row["follow_up_on"] is not None:
        day(row["follow_up_on"])
    if not isinstance(row["sources"],list) or not 1 <= len(row["sources"]) <= 100:
        raise ValueError("A case requires public sources")
    ids = set()
    for src in row["sources"]:
        keys(src,"id publisher url published_on record_id feed_published_at first_seen_at")
        if not SLUG.fullmatch(src["id"]) or src["id"] in ids:
            raise ValueError("Invalid or duplicate source ID")
        ids.add(src["id"])
        plain(src["publisher"],160)
        source_url(src["url"])
        if src["published_on"] is not None:
            day(src["published_on"])
        if src["record_id"] is not None and not re.fullmatch(r"[0-9a-f]{18}",src["record_id"]):
            raise ValueError("Invalid source record ID")
        for name in ("feed_published_at","first_seen_at"):
            if src[name] is not None and datetime.fromisoformat(src[name].replace("Z","+00:00")).tzinfo is None:
                raise ValueError("Observation timestamp needs timezone")
    if not isinstance(row["timeline"],list) or not 1 <= len(row["timeline"]) <= 250:
        raise ValueError("A timeline requires cited milestones")
    for item in row["timeline"]:
        keys(item,"on actor kind source text")
        if item["source"] not in ids or item["kind"] not in KINDS:
            raise ValueError("Unknown evidence or milestone type")
        plain(item["actor"],160)
        bilingual(item["text"])
        if item["on"] is not None:
            day(item["on"])
    return row

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def public_cases(pilots, decisions=()):
    cases={}
    for row in pilots:
        validate_case(row)
        if row["id"] in cases:
            raise ValueError("Duplicate case ID")
        cases[row["id"]]=row
    for case_id, approval in decisions:
        if approval["state"] == "withdrawn":
            cases.pop(case_id,None)
        elif approval["state"] == "approved":
            case=validate_case(approval["public"])
            if case["id"] != case_id:
                raise ValueError("Publication ID mismatch")
            cases[case_id]=case
        else:
            raise ValueError("Unknown editorial publication decision")
    return list(cases.values())
