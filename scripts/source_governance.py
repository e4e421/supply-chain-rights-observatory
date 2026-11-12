#!/usr/bin/env python3
"""Source governance: editorial status is never inferred from HTTP response status.

Offline checks on every build, optional guarded availability probes on a weekly schedule.
The registry records editorial decisions and technical reachability separately.
"""
from __future__ import annotations
import argparse, json, re
from datetime import datetime, timezone
from fnmatch import fnmatchcase
from pathlib import Path
from time import sleep
from urllib.parse import quote, urlparse, urlsplit
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

# Candidate URLs are displayable, with a separate list for active reference checks.
CANDIDATE_HOSTS={
 'www.reuters.com','www.theguardian.com','www.esgdive.com','www.esgtoday.com',
 'www.responsible-investor.com','www.hsfkramer.com','sustainable-procurement.org',
 'www.edie.net','www.iflr.com','news.mongabay.com','trellis.net'
}
GUARDED_PROBE_HOSTS={
 'www.esgtoday.com','www.hsfkramer.com','sustainable-procurement.org',
 'www.edie.net','www.iflr.com','news.mongabay.com','trellis.net'
}
PROBE_AGENT='SupplyChainRightsObservatory'
PROBE_HEADERS={'User-Agent':PROBE_AGENT+'/1.0 (public source-availability check)'}
ROBOTS_LIMIT=500*1024
# HSF Kramer's published robots policy requests a five-second crawl interval.
PROBE_DELAYS={'www.hsfkramer.com':5}

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
        if entry.get('metadata_reuse_notice'):
            validate_link(entry['metadata_reuse_notice'])
        probe_enabled=entry.get('probe_enabled', True)
        if not isinstance(probe_enabled,bool):
            raise ValueError('Invalid reference probe setting')
        if not probe_enabled or urlparse(entry['url']).hostname in GUARDED_PROBE_HOSTS:
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
    def __init__(self, validate_redirect=validate_link, delay=0):
        self.validate_redirect=validate_redirect
        self.delay=delay

    def redirect_request(self,req,fp,code,msg,headers,newurl):
        self.validate_redirect(newurl)
        redirected=super().redirect_request(req,fp,code,msg,headers,newurl)
        if redirected is not None:
            redirected.method=req.get_method()
            if self.delay:
                sleep(self.delay)
        return redirected

def robots_path(value):
    # Match percent-encoded unreserved characters equivalently and preserve encoded delimiters.
    def normalize_escape(match):
        char=chr(int(match[1],16))
        return char if re.fullmatch(r'[A-Za-z0-9._~-]',char) else match[0].upper()
    value=quote(value,safe='!#$%&\'()*+,-./:;=?@[]_~')
    return re.sub(r'%([0-9a-fA-F]{2})',normalize_escape,value)

def robots_allows(text,url):
    groups={}
    agents=[]
    rules_seen=False
    for line in text.splitlines():
        name,separator,value=line.partition('#')[0].partition(':')
        if not separator:
            continue
        name,value=name.strip().lower(),value.strip()
        if name=='user-agent':
            if rules_seen:
                agents=[]
                rules_seen=False
            agent=value.casefold()
            agents.append(agent)
            groups.setdefault(agent,[])
        elif agents and name in ('allow','disallow'):
            rules_seen=True
            if value.startswith('/'):
                for agent in agents:
                    groups[agent].append((robots_path(value),name=='allow'))
    target=urlsplit(url)
    path=robots_path((target.path or '/')+('?' + target.query if target.query else ''))
    best=(0,True)
    for rule,allow in groups.get(PROBE_AGENT.casefold(),groups.get('*',[])):
        pattern=rule[:-1] if rule.endswith('$') else rule+'*'
        pattern=re.sub(r'([?\[\]])',r'[\1]',pattern)
        if fnmatchcase(path,pattern):
            best=max(best,(len(rule.rstrip('$').replace('*','')),allow))
    return best[1]

class PolicyRestricted(ValueError):
    pass

def robots_rules(url, same_host, delay):
    robots_url=urlsplit(url)._replace(path='/robots.txt',query='',fragment='').geturl()
    try:
        request=Request(robots_url,headers=PROBE_HEADERS,method='GET')
        with build_opener(RedirectBlocker(same_host,delay)).open(request,timeout=6) as response:
            same_host(response.url)
            contents=response.read(ROBOTS_LIMIT+1)
            if len(contents)>ROBOTS_LIMIT or contents.lstrip().startswith(b'<'):
                raise ValueError('Unexpected robots response')
            return contents.decode('utf-8-sig')
    except HTTPError as exc:
        if exc.code in (404,410):
            return ''
        if exc.code in (401,403):
            raise PolicyRestricted('Robots rules are access restricted') from exc
        raise URLError('Robots rules could not be verified') from exc

def probe(url):
    try:
        validate_target=validate_link
        host=urlsplit(url).hostname
        delay=PROBE_DELAYS.get(host,0)
        if host in GUARDED_PROBE_HOSTS:
            def same_host(target):
                if validate_manual_link(target)!=host:
                    raise ValueError('Unexpected reference redirect host')
            same_host(url)
            rules=robots_rules(url,same_host,delay)
            def validate_target(target):
                same_host(target)
                if not robots_allows(rules,target):
                    raise PolicyRestricted('Path disallowed by robots rules')
        validate_target(url)
        if delay:
            sleep(delay)
        req=Request(url,headers=PROBE_HEADERS,method='HEAD')
        with build_opener(RedirectBlocker(validate_target,delay)).open(req,timeout=6) as response:
            validate_target(response.url)
            return {'reachability':'responded','http_status':int(response.status)}
    except PolicyRestricted:
        return {'reachability':'policy_restricted','http_status':None}
    except HTTPError as exc:
        # 403 and 405 do not mean a source is untrustworthy.
        return {'reachability':'http_restriction_or_error','http_status':int(exc.code)}
    except (URLError,ValueError,OSError,TimeoutError) as exc:
        result={'reachability':'not_confirmed','http_status':None}
        if isinstance(getattr(exc,'reason',exc),TimeoutError):
            result['failure_kind']='timeout'
        return result


def probe_failure_kind(status):
    code=status.get('http_status')
    if code==429:
        return 'rate_limited'
    if code in (401,403,405) or status.get('reachability')=='policy_restricted':
        return 'access_restricted'
    if status.get('reachability')=='http_restriction_or_error':
        return 'http_error'
    if status.get('reachability')=='not_confirmed':
        return status.get('failure_kind') or 'connection_unconfirmed'
    return None

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
        enabled=entry.get('probe_enabled',True)
        if (prior.get('reachability')=='manual_only' or
                prior.get('url',entry['url'])!=entry['url'] or
                prior.get('probe_enabled',enabled)!=enabled):
            prior={}
        prior_failure=bool(prior.get('last_probe') and prior.get('reachability') not in ('responded','policy_restricted'))
        status={
            'id':entry['id'],
            'name':entry['name'],
            'url':entry['url'],
            'probe_enabled':enabled,
            'authority_type':entry['authority_type'],
            'editorial_status':entry['status'],
            'last_editorial_review':entry.get('verified_on'),
            'review_due':entry.get('review_due'),
            'licence_review_status':entry.get('licence_review_status','pending'),
            'review_needed':not bool(entry.get('verified_on')) or bool(entry.get('review_due') and entry['review_due']<today),
            'reachability':prior.get('reachability','untested'),
            'http_status':prior.get('http_status'),
            'last_probe':prior.get('last_probe'),
            'last_successful_probe':prior.get('last_successful_probe',prior.get('last_probe') if prior.get('reachability')=='responded' else None),
            'failure_kind':prior.get('failure_kind'),
            'consecutive_failures':prior.get('consecutive_failures',int(prior_failure))
        }
        if entry.get('metadata_reuse_notice'):
            status['metadata_reuse_notice']=entry['metadata_reuse_notice']
        if not enabled:
            status.update(reachability='manual_only', http_status=None, last_probe=None, last_successful_probe=None, consecutive_failures=0)
        elif online:
            result=probe(entry['url'])
            status['failure_kind']=None
            status.update(result)
            status['consecutive_failures']=0 if result['reachability'] in ('responded','policy_restricted') else status['consecutive_failures']+1
            status['last_probe']=now
            if result['reachability']=='responded':
                status['last_successful_probe']=now
        status['failure_kind']=probe_failure_kind(status)
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
