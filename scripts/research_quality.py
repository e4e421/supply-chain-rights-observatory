"""Conservative, reproducible discovery screening; never a finding of wrongdoing.

This is a title-only *triage* tool. Candidate exclusion MUST NOT delete the raw
capture, and accepted records remain unverified until human corroboration.
Review the dictionaries with a labelled evaluation set before using as research outcomes.
"""
from __future__ import annotations
import re

VERSION="title-screen-v1.0"
HIGH_CONFIDENCE=(
    "forced labour","forced labor","modern slavery","human rights due diligence",
    "human rights in supply","child labour","child labor","worker exploitation",
    "labour exploitation","labor exploitation","supply chain due diligence",
    "csddd","cshddd","lieferkettensorgfaltspflichtengesetz","lksg",
    "human rights violation","human rights abuse","ethical sourcing",
    "responsible sourcing","supply chain slavery"
)
SUPPLY=("supply chain","supply network","supplier","subcontractor","procurement",
        "value chain","global value chain","garment industry","textile factory","factory workers",
        "corporate accountability","multinational enterprise","outsourcing","lead firm")
LABOUR=("labour","labor","worker","wage","union","collective bargaining","grievance",
        "occupational safety","workplace safety","human right","social sustainability",
        "due diligence","remedy","remediation","unsafe working","social auditing","working conditions")
NEGATIVE=("dutch government charts its own ai course","bans further oil & gas drilling",
          "joining the eu single market without a referendum")
def normalized(text):
    return re.sub(r"\s+"," ",str(text or "").casefold()).strip()
def screen_title(title,academic=False):
    x=normalized(title)
    if len(x)<12:
        return {"status":"excluded","reason":"missing_or_short_title","version":VERSION}
    if any(s in x for s in NEGATIVE):
        return {"status":"excluded","reason":"documented_false_positive","version":VERSION}
    if any(s in x for s in HIGH_CONFIDENCE):
        return {"status":"candidate_relevant","reason":"high_specificity_phrase","version":VERSION}
    s=any(s in x for s in SUPPLY)
    l=any(s in x for s in LABOUR)
    if s and l:
        return {"status":"candidate_relevant","reason":"supply_and_labour_terms","version":VERSION}
    if academic and ("human rights" in x and ("corporate" in x or "business" in x)):
        return {"status":"candidate_relevant","reason":"academic_corporate_human_rights","version":VERSION}
    return {"status":"excluded","reason":"insufficient_title_evidence","version":VERSION}

def publisher_hint(title):
    """Extract only a visible credit suffix. This is NOT publisher verification."""
    value=str(title or "")
    if " - " not in value: return None
    candidate=value.rsplit(" - ",1)[1].strip()
    if not candidate or len(candidate)>85 or any(x in candidate.lower() for x in ("http://","https://")):
        return None
    return candidate
