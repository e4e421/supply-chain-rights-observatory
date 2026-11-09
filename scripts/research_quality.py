"""Versioned keyword triage. Relevance is not claim verification; originals are retained."""
from relevance_engine import analyze, normalize as normalized, rules
VERSION=rules()['version']
def screen_title(title,academic=False):
    result=analyze({'title':title,'kind':'academic' if academic else 'discovery'})
    return {'status':'excluded' if result['level']=='low' else 'candidate_relevant',
            'reason':result['reason'],'version':VERSION,'relevance_level':result['level']}
def publisher_hint(title):
    value=str(title or '')
    if ' - ' not in value:return None
    candidate=value.rsplit(' - ',1)[1].strip()
    if not candidate or len(candidate)>85 or any(x in candidate.lower() for x in ('http://','https://')):return None
    return candidate
