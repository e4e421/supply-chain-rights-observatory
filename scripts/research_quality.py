"""Versioned keyword triage. Relevance is not claim verification; originals are retained."""
from relevance_engine import analyze, normalize as normalized, rules, source_exclusion_reason
VERSION=rules()['version']
def screen_title(title,academic=False,publisher=None):
    record={'title':title,'kind':'academic' if academic else 'discovery'}
    exclusion=source_exclusion_reason({**record,'publisher_hint':publisher})
    if exclusion:
        return {'status':'excluded','reason':exclusion,'version':VERSION,'relevance_level':'low'}
    result=analyze(record)
    return {'status':'excluded' if result['level']=='low' else 'candidate_relevant',
            'reason':result['reason'],'version':VERSION,'relevance_level':result['level']}
def publisher_hint(title):
    value=str(title or '')
    if ' - ' not in value:return None
    candidate=value.rsplit(' - ',1)[1].strip()
    if not candidate or len(candidate)>85 or any(x in candidate.lower() for x in ('http://','https://')):return None
    return candidate
