"""Deterministic relevance and review overlay. No AI, network, or source-derived trust scores."""
from __future__ import annotations
import hashlib, ipaddress, json, re, unicodedata
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
RULES=ROOT/'sources/relevance-rules.json'
LEVELS={'high','review','low'}
ID=re.compile(r'[a-f0-9]{18}')

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()

def normalize(value):
    return re.sub(r'\s+',' ',unicodedata.normalize('NFKC',str(value)).casefold().translate(str.maketrans({'–':'-','—':'-','’':"'"}))).strip()

@lru_cache(maxsize=1)
def rules():
    doc=json.loads(RULES.read_text(encoding='utf-8'))
    if doc.get('schema_version')!=1 or set(doc['topics'])!={'policy','forced-labour','working-conditions','worker-voice','network','research'}:
        raise ValueError('Invalid keyword dictionary')
    if not isinstance(doc.get('version'),str):raise ValueError('Missing rule version')
    return doc

@lru_cache(maxsize=512)
def pattern(term):
    s=normalize(term)
    # Literal matching only, with word boundaries outside CJK strings. No user regex.
    if re.search(r'[\u3400-\u9fff]',s):return re.compile(re.escape(s))
    return re.compile(r'(?<!\w)'+re.escape(s)+r'(?!\w)')

def analysis_input(record):
    title=str(record.get('title',''))[:1000]
    credit=record.get('publisher_hint')
    if isinstance(credit,str) and title.endswith(' - '+credit):title=title[:-len(credit)-3]
    fields={'title':title}
    # Generic descriptions and query/publisher names must NEVER count as content.
    if record.get('abstract_usage')=='permitted_metadata' and isinstance(record.get('abstract'),str):
        fields['abstract']=record['abstract'][:12000]
    return fields

def fingerprint(record):
    return digest({'input':analysis_input(record),'url':record.get('url'),'doi':record.get('doi'),'kind':record.get('kind')})

def analyze(record):
    doc=rules();fields=analysis_input(record);hits=[];groups=set();topics=set()
    for group,terms in doc['groups'].items():
        for term in terms:
            for field,text in fields.items():
                if pattern(term).search(normalize(text)):
                    hits.append({'group':group,'term':term,'field':field});groups.add(group)
    risk=bool(groups & {'forced','child','conditions','voice'})
    if 'policy_specific' in groups:
        level,reason='high','specific_hrdd_policy'
    elif 'supply' in groups and (risk or 'rights' in groups):
        level,reason='high','supply_and_labour_context'
    elif 'governance' in groups and ('rights' in groups or risk):
        level,reason='high','governance_and_rights'
    elif risk or 'rights' in groups or ('supply' in groups and 'governance' in groups):
        level,reason='review','incomplete_context'
    else:
        level,reason='low','insufficient_text_evidence'
    if 'policy_specific' in groups or ('governance' in groups and level!='low'):topics.add('policy')
    if 'forced' in groups:topics.add('forced-labour')
    if groups & {'child','conditions'}:topics.add('working-conditions')
    if 'voice' in groups:topics.add('worker-voice')
    if 'network' in groups and level!='low':topics.add('network')
    if record.get('kind')=='academic':topics.add('research')
    return {'rule_version':doc['version'],'rule_digest':digest(doc),'level':level,'reason':reason,
            'scope':'title_and_permitted_abstract' if 'abstract' in fields else 'title_only',
            'matched':hits,'suggested_topics':sorted(topics),'europe_mention': 'europe' in groups,
            'content_fingerprint':fingerprint(record),'claim_verified':False}

def public_url(value):
    if not isinstance(value,str) or not 8<=len(value)<=2048 or re.search(r'[\x00-\x20\x7f\\]',value):raise ValueError('Invalid public URL')
    u=urlsplit(value)
    if u.scheme!='https' or not u.hostname or u.username or u.password or u.port not in (None,443):raise ValueError('HTTPS without credentials required')
    host=u.hostname.lower()
    if '.' not in host or host.endswith(('.localhost','.local','.internal','.test')) or host in {'localhost','metadata.google.internal'}:raise ValueError('Private host forbidden')
    try:ipaddress.ip_address(host)
    except ValueError:pass
    else:raise ValueError('IP literal forbidden')
    return value

def validate_overlay(doc):
    if set(doc)!={'schema_version','records'} or doc['schema_version']!=1 or not isinstance(doc['records'],dict):raise ValueError('Invalid review overlay')
    for rid,entry in doc['records'].items():
        if not ID.fullmatch(rid):raise ValueError('Invalid record ID')
        allowed={'content_fingerprint','relevance','topics','publisher_confirmed','canonical_url','note','reviewed_at','reviewed_by','issue','issue_digest'}
        if set(entry)!=allowed:raise ValueError('Invalid review fields')
        if not re.fullmatch(r'[a-f0-9]{64}',entry['content_fingerprint']):raise ValueError('Invalid fingerprint')
        if entry['relevance'] not in {'include','exclude','needs_review'}:raise ValueError('Invalid relevance')
        if entry['topics'] is not None and (not isinstance(entry['topics'],list) or len(set(entry['topics']))!=len(entry['topics']) or any(t not in rules()['topics'] for t in entry['topics'])):raise ValueError('Invalid topics')
        if type(entry['publisher_confirmed']) is not bool:raise ValueError('Invalid publisher flag')
        if entry['canonical_url'] is not None:public_url(entry['canonical_url'])
        if entry['publisher_confirmed'] and not entry['canonical_url']:raise ValueError('Publisher confirmation requires original URL')
        if not isinstance(entry['note'],str) or len(entry['note'])>400 or re.search(r'[\x00-\x08\x0b-\x1f\x7f]',entry['note']):raise ValueError('Invalid public note')
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{0,38}',entry['reviewed_by']):raise ValueError('Invalid GitHub reviewer')
        if type(entry['issue']) is not int or entry['issue']<1:raise ValueError('Invalid issue')
        if not re.fullmatch(r'[a-f0-9]{64}',entry['issue_digest']):raise ValueError('Invalid issue digest')
        from datetime import datetime
        if datetime.fromisoformat(entry['reviewed_at'].replace('Z','+00:00')).tzinfo is None:raise ValueError('Timezone required')
    return doc

def decorate(record,decisions):
    rid=record.get('record_id') or record.get('id');analysis=analyze(record);review=decisions.get(rid)
    current=review is not None and review['content_fingerprint']==analysis['content_fingerprint']
    state='current' if current else 'stale' if review else 'unreviewed'
    effective=review['topics'] if current and review['topics'] is not None else analysis['suggested_topics']
    return {'analysis':analysis,'review_state':state,'review':review,'review_digest':digest(review),
            'effective_topics':effective,'included':not(current and review['relevance']=='exclude')}

def similarities(index,limit=4):
    # Transparent, bounded, keyword-concept overlap. Never creates event IDs.
    tokens={rid:{h['group']+':'+normalize(h['term']) for h in row['analysis']['matched'] if h['group'] not in {'europe','supply'}}
            for rid,row in index.items() if row['analysis']['level']!='low' and row['included']}
    from collections import defaultdict
    postings=defaultdict(list)
    for rid,values in tokens.items():
        for token in sorted(values):postings[token].append(rid)
    for rid,values in tokens.items():
        candidates=set()
        for token in sorted(values):candidates.update(postings[token][:250])
        matches=[]
        for other in sorted(candidates):
            if other==rid:continue
            shared=values&tokens[other];union=values|tokens[other]
            score=len(shared)/len(union) if union else 0
            if len(shared)>=2 and score>=.25:matches.append({'record_id':other,'overlap':round(score,3),'shared_terms':[x.split(':',1)[1] for x in sorted(shared)][:6]})
        index[rid]['similar']=sorted(matches,key=lambda x:(-x['overlap'],x['record_id']))[:limit]
    return index
