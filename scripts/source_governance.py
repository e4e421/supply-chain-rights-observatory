#!/usr/bin/env python3
"""Source governance: editorial status is never inferred from HTTP response status.

Offline checks on every build, optional guarded availability probes on a weekly schedule.
The registry records editorial decisions and technical reachability separately.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import URLError,HTTPError

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/'sources/registry.json'
CANDIDATES=ROOT/'sources/candidates.json'
REFS=ROOT/'docs/data/references.json'
OUTPUT=ROOT/'docs/data/source-health.json'
ALLOWED={
 'commission.europa.eu','single-market-economy.ec.europa.eu','eur-lex.europa.eu',
 'www.ilo.org','www.business-humanrights.org','www.oecd.org','www.etui.org',
 'www.ituc-csi.org','scm.ethz.ch','www.crossref.org','news.google.com',
 'ec.europa.eu','www.bmas.bund.de','european-union.europa.eu',
 'www.worldbenchmarkingalliance.org','www.ela.europa.eu','www.eurofound.europa.eu'
}

# HTTPS links for candidate and manual-reference sources. Keep separate from probe hosts.
CANDIDATE_HOSTS={
 'www.reuters.com','www.theguardian.com','www.esgdive.com','www.esgtoday.com',
 'www.responsible-investor.com','www.hsfkramer.com','sustainable-procurement.org',
 'www.edie.net','www.iflr.com','news.mongabay.com','trellis.net'
}

def validate_manual_link(url):
    u=urlparse(str(url))
    if u.scheme!='https' or u.hostname not in CANDIDATE_HOSTS or u.username or u.password or u.port not in (None,443) or u.fragment:
        raise ValueError('Unexpected manual source URL authority')
    return u.hostname

def validate_link(url):
    u=urlparse(str(url))
    if u.scheme!='https' or u.hostname not in ALLOWED or u.username or u.password or u.port not in (None,443):
        raise ValueError('Unexpected source URL authority')
    return u.hostname

def validate(registry,candidates,refs):
    if registry.get('schema_version')!=1 or candidates.get('schema_version')!=1:
        raise ValueError('Invalid governance schema')
    ids=set()
    known_urls=set()
    for entry in registry.get('sources',[]):
        if not isinstance(entry,dict) or not re.fullmatch(r'[a-z0-9-]{3,60}',str(entry.get('id',''))):
            raise ValueError('Invalid source id')
        if entry['id'] in ids: raise ValueError('Duplicate source id')
        ids.add(entry['id'])
        if entry.get('status')!='curated_reference' or entry.get('auto_ingest') is not False:
            raise ValueError('Source promotion must be manual')
        if entry.get('licence_review_status') not in ('pending','approved_for_metadata','no_redistribution'):
            raise ValueError('Source licence review status missing or invalid')
        if entry.get('probe_enabled', True) is False:
            validate_manual_link(entry['url'])
        else:
            validate_link(entry['url'])
        if entry['url'] in known_urls: raise ValueError('Duplicated approved URL')
        known_urls.add(entry['url'])
        if entry.get('review_due') and not re.fullmatch(r'\d{4}-\d{2}-\d{2}',entry['review_due']):
            raise ValueError('Invalid review date')
    for item in refs:
        if item['url'] not in known_urls: raise ValueError('Reference is missing from curated registry')
    candidate_ids=set()
    candidate_urls=set()
    for item in candidates.get('candidates',[]):
        candidate_id=str(item.get('id',''))
        if (item.get('status')!='pending_review' or item.get('auto_ingest') is not False
                or not re.fullmatch(r'[a-z0-9-]{3,60}',candidate_id)
                or candidate_id in ids or candidate_id in candidate_ids):
            raise ValueError('Unapproved candidate promotion or duplicate candidate identifier')
        validate_manual_link(item['url'])
        if item['url'] in known_urls or item['url'] in candidate_urls:
            raise ValueError('Duplicate candidate or curated URL')
        candidate_ids.add(candidate_id)
        candidate_urls.add(item['url'])
    return True

class RedirectBlocker(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        # Reachability does not require following redirect to unrelated infrastructure.
        validate_link(newurl)
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def probe(url):
    try:
        validate_link(url)
        req=Request(url,headers={'User-Agent':'SupplyChainRightsObservatory/1.0 (public source-availability check)'},method='HEAD')
        with build_opener(RedirectBlocker()).open(req,timeout=6) as response:
            validate_link(response.url)
            return {'reachability':'responded','http_status':int(response.status)}
    except HTTPError as exc:
        # 403 and 405 do not mean a source is untrustworthy.
        return {'reachability':'http_restriction_or_error','http_status':int(exc.code)}
    except (URLError,ValueError,OSError,TimeoutError):
        return {'reachability':'not_confirmed','http_status':None}

def run(online=False):
    registry=json.loads(REGISTRY.read_text(encoding='utf-8'))
    candidates=json.loads(CANDIDATES.read_text(encoding='utf-8'))
    refs=json.loads(REFS.read_text(encoding='utf-8'))
    validate(registry,candidates,refs)
    previous=json.loads(OUTPUT.read_text(encoding='utf-8')) if OUTPUT.exists() else {}
    old={entry['id']:entry for entry in previous.get('sources',[])}
    now=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
    today=now[:10]
    entries=[]
    for entry in registry['sources']:
        prior=old.get(entry['id'],{})
        prior_failure=bool(prior.get('last_probe') and prior.get('reachability')!='responded')
        status={
            'id':entry['id'],
            'name':entry['name'],
            'authority_type':entry['authority_type'],
            'editorial_status':entry['status'],
            'last_editorial_review':entry.get('verified_on'),
            'review_due':entry.get('review_due'),
            'licence_review_status':entry.get('licence_review_status','pending'),
            'review_needed':not bool(entry.get('verified_on')) or bool(entry.get('review_due') and entry['review_due']<today),
            'reachability':prior.get('reachability','untested'),
            'http_status':prior.get('http_status'),
            'last_probe':prior.get('last_probe'),
            'consecutive_failures':prior.get('consecutive_failures',int(prior_failure))
        }
        if entry.get('probe_enabled', True) is False:
            status.update(reachability='manual_only', http_status=None, last_probe=None, consecutive_failures=0)
        elif online:
            result=probe(entry['url'])
            status.update(result)
            status['consecutive_failures']=0 if result['reachability']=='responded' else status['consecutive_failures']+1
            status['last_probe']=now
        entries.append(status)
    report={
        'schema_version':1,'method':'editorial_registry_plus_optional_HTTPS_HEAD',
        'editorial_review_is_manual':True,'http_reachability_does_not_verify_claims':True,
        'last_probe_run':now if online else previous.get('last_probe_run'),
        'approved_reference_count':len(entries),'pending_candidate_count':len(candidates.get('candidates',[])),
        'review_needed_count':sum(x['review_needed'] for x in entries),
        'review_overdue':sum(bool(x['review_due'] and x['review_due']<today) for x in entries),
        'licence_review_pending_count':sum(x['licence_review_status']=='pending' for x in entries),
        'sources':entries
    }
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f"Source registry: {len(entries)} curated references, {report['review_needed_count']} need editorial re-review; online probes: {online}")

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--online',action='store_true',help='Probe curated sources (HTTPS HEAD only); no content scraping')
    args=parser.parse_args()
    run(online=args.online)
