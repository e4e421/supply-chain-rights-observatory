#!/usr/bin/env python3
"""Fetch public research leads and Crossref bibliographic records.

No secrets, scraping, analytics, accounts or generative inference. Discovery is not
verification; this script stores only public titles, dates and links.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener
from xml.etree import ElementTree
from research_quality import screen_title, publisher_hint, VERSION as SCREEN_VERSION

ROOT = Path(__file__).resolve().parents[1]
CONFIG_FILE = ROOT / 'sources' / 'queries.json'
OUTPUT_FILE = ROOT / 'docs' / 'data' / 'latest.json'
ALLOWED_FETCH_HOSTS = frozenset({'news.google.com', 'api.crossref.org'})
MAX_BYTES = 2_000_000
MAX_ITEMS = 240
MAX_AGE_DAYS = 150
MAX_PREVIOUS_AGE_DAYS = 150
TIMEOUT_SECONDS = 16
USER_AGENT = 'SupplyChainRightsObservatory/1.0 (+https://github.com/e4e421/supply-chain-rights-observatory; public academic metadata)'
TOPICS = ('policy', 'forced-labour', 'working-conditions', 'worker-voice', 'network', 'research', 'other')
KEYWORDS = {
    'forced-labour': ('forced labour', 'forced labor', 'modern slavery', 'trafficking', 'child labour', 'child labor'),
    'worker-voice': ('trade union', 'collective bargaining', 'worker voice', 'grievance', 'remedy', 'remediation', 'strike'),
    'working-conditions': ('wages', 'wage theft', 'occupational safety', 'working conditions', 'workplace safety', 'workers rights', 'labour rights', 'labor rights'),
    'network': ('supplier', 'supply chain', 'supply network', 'traceability', 'multi-tier', 'procurement'),
    'policy': ('due diligence', 'csddd', 'cshddd', 'regulation', 'legislation', 'lksg', 'enforcement', 'directive'),
}
DOI_PATTERN = re.compile(r'10\.\d{4,9}/[-._;()/:a-zA-Z0-9]+\Z')


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso(value):
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def clean_text(value, limit=240):
    value = re.sub(r'[\x00-\x1f\x7f]', ' ', str(value or ''))
    return re.sub(r'\s+', ' ', value).strip()[:limit]


def public_https_url(value, allowed_host=None):
    """Strictly limit input URL to absolute HTTPS without credentials or unsafe ports."""
    try:
        value = str(value)
        url = urlparse(value)
        if url.scheme != 'https' or not url.hostname or url.username or url.password or url.port not in (None, 443):
            return None
        host = url.hostname.lower()
        if (allowed_host and host != allowed_host) or host == 'localhost' or host.endswith('.localhost'):
            return None
        if host.endswith('.local') or host.endswith('.internal') or host.endswith('.invalid'):
            return None
        if re.fullmatch(r'[0-9.]+', host) or ':' in host:
            return None
        return value[:1000]
    except (ValueError, TypeError):
        return None


class RestrictedRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not any(public_https_url(newurl, host) for host in ALLOWED_FETCH_HOSTS):
            raise ValueError('Blocked external redirect outside allowlist')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_bytes(url):
    if not any(public_https_url(url, host) for host in ALLOWED_FETCH_HOSTS):
        raise ValueError('Feed URL host not allowlisted')
    req = Request(url, headers={'User-Agent': USER_AGENT, 'Accept': 'application/rss+xml, application/json, application/xml;q=0.9'})
    with build_opener(RestrictedRedirects()).open(req, timeout=TIMEOUT_SECONDS) as response:
        if not any(public_https_url(response.url, host) for host in ALLOWED_FETCH_HOSTS):
            raise ValueError('Unexpected final request destination')
        body = response.read(MAX_BYTES + 1)
        if len(body) > MAX_BYTES:
            raise ValueError('Response exceeds maximum size')
        return body


def date_from_rss(value):
    try:
        dt = parsedate_to_datetime(str(value))
        if not dt.tzinfo:
            dt = dt.replace(tzinfo=timezone.utc)
        return iso(dt)
    except (ValueError, TypeError, IndexError):
        return None


def date_from_crossref(record):
    for field in ('published-online', 'published-print', 'published', 'issued', 'created'):
        try:
            parts = record[field]['date-parts'][0]
            if len(parts) >= 1 and 1900 <= int(parts[0]) <= 2100:
                return iso(datetime(int(parts[0]), int(parts[1]) if len(parts) > 1 else 1, int(parts[2]) if len(parts) > 2 else 1, tzinfo=timezone.utc))
        except (ValueError, TypeError, IndexError, KeyError):
            continue
    return None


def classify(title, preset=()):
    lower = title.lower()
    matches = [topic for topic, terms in KEYWORDS.items() if any(term in lower for term in terms)]
    return [topic for topic in dict.fromkeys([*matches, *preset]) if topic in TOPICS] or ['other']


def stable_id(item):
    # Strip duplicate trackers; we only need a stable source/title identifier.
    key = f"{item['kind']}|{item.get('doi') or item['url']}|{item['title'].casefold()}"
    return hashlib.sha256(key.encode('utf-8')).hexdigest()[:18]


def parse_rss(body, config, now, candidates=None):
    upper = body[:1024].upper()
    if b'<!DOCTYPE' in body.upper() or b'<!ENTITY' in body.upper():
        raise ValueError('DTD and external entities are not accepted')
    root = ElementTree.fromstring(body)
    if root.tag != 'rss' and not root.tag.endswith('}rss'):
        raise ValueError('Expected RSS XML document')
    result = []
    for node in root.findall('./channel/item')[:80]:
        title = clean_text(node.findtext('title'))
        link = public_https_url((node.findtext('link') or '').strip(), 'news.google.com')
        if not title or not link:
            continue
        date = date_from_rss(node.findtext('pubDate'))
        if not date:
            continue  # Unknown dates are not silently labelled new.
        if not is_recent(date, now, MAX_AGE_DAYS):
            continue
        quality = screen_title(title)
        record = {
            'title': title, 'url': link, 'published_at': date,
            'source': clean_text(config['name'], 90), 'source_id': config['id'],
            'discovery_query_id': config['id'], 'publisher_hint': publisher_hint(title),
            'publisher_verified': False, 'canonical_url': None,
            'kind': 'discovery', 'evidence_status': 'Unverified discovery',
            'topics': classify(title, config.get('topics', [])),
            'description': 'Automatically discovered news lead. Trace the original reporting and independent evidence; no human rights violation is established by this record.',
            'screening_version': quality['version'], 'screening_status':quality['status'],
            'screening_reason':quality['reason'],
            'first_seen': iso(now)
        }
        if candidates is not None:
            candidates.append(record)
        if quality['status'] == 'candidate_relevant':
            result.append(record)
    return result


def parse_crossref(payload, config, now, candidates=None):
    result = []
    for record in payload.get('message', {}).get('items', [])[:35]:
        title = clean_text((record.get('title') or [''])[0])
        doi = str(record.get('DOI') or '').strip()
        published = date_from_crossref(record)
        if not title or not DOI_PATTERN.fullmatch(doi) or not published:
            continue
        if not is_recent(published, now, MAX_AGE_DAYS):
            continue
        quality=screen_title(title,academic=True)
        row = {
            'title': title, 'url': 'https://doi.org/' + quote(doi, safe='/._;():-'),
            'published_at': published, 'source': 'Crossref · ' + clean_text(config['name'], 65),
            'source_id': config['id'], 'discovery_query_id':config['id'],
            'publisher_hint':None, 'publisher_verified':False, 'canonical_url':None,
            'kind': 'academic', 'evidence_status': 'Bibliographic record',
            'topics': classify(title, ('research',)), 'doi': doi,
            'screening_version':quality['version'], 'screening_status':quality['status'],
            'screening_reason':quality['reason'],
            'description': 'Crossref bibliographic record. Verify DOI and publication date with the publisher; methods and peer-review status have not been independently reviewed.',
            'first_seen': iso(now)
        }
        if candidates is not None:
            candidates.append(row)
        if quality['status'] == 'candidate_relevant':
            result.append(row)
    return result


def is_recent(iso_date, now, age_days):
    try:
        dt = datetime.fromisoformat(iso_date.replace('Z', '+00:00'))
        return now - timedelta(days=age_days) <= dt <= now + timedelta(days=2)
    except (ValueError, TypeError):
        return False


def merge_items(new, previous, now):
    merged = {}
    for item in previous:
        if not isinstance(item, dict) or not is_recent(item.get('published_at'), now, MAX_PREVIOUS_AGE_DAYS):
            continue
        if item.get('kind') not in ('academic', 'discovery') or not public_https_url(item.get('url')):
            continue
        if not isinstance(item.get('title'), str) or not isinstance(item.get('id'), str):
            continue
        if item.get('kind') == 'academic' or screen_title(item.get('title'))['status'] == 'candidate_relevant':
            merged[item['id']] = item
    for item in new:
        item['id'] = stable_id(item)
        old = merged.get(item['id'])
        if old and old.get('first_seen'):
            item['first_seen'] = old['first_seen']
        merged[item['id']] = item
    return sorted(merged.values(), key=lambda x: (x.get('published_at') or '', x['id']), reverse=True)[:MAX_ITEMS]


def run():
    now = utc_now()
    config = json.loads(CONFIG_FILE.read_text(encoding='utf-8'))
    try:
        previous = json.loads(OUTPUT_FILE.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        previous = {}
    new_items, sources, warnings, candidates = [], [], [], []
    for config_item in config['news_queries']:
        query = config_item['query']
        url = 'https://news.google.com/rss/search?' + urlencode({'q':query, 'hl':'en-GB', 'gl':'GB', 'ceid':'GB:en'})
        sources.append(process_source(config_item, 'news', lambda: parse_rss(fetch_bytes(url), config_item, now, candidates), new_items, warnings, now))
    for config_item in config['academic_queries']:
        params = {'query.bibliographic':config_item['query'], 'filter': f'from-pub-date:{(now-timedelta(days=MAX_AGE_DAYS)).date().isoformat()}', 'rows':'75', 'select':'DOI,title,published,published-print,published-online,issued,created,type', 'sort':'published', 'order':'desc'}
        url = 'https://api.crossref.org/works?' + urlencode(params)
        def crossref_fetch(url=url, cfg=config_item):
            return parse_crossref(json.loads(fetch_bytes(url).decode('utf-8')), cfg, now, candidates)
        sources.append(process_source(config_item, 'academic', crossref_fetch, new_items, warnings, now))
    success = sum(x['status'] == 'ok' for x in sources)
    status = 'failed' if success == 0 or (not new_items and not previous.get('items')) else 'partial' if success < len(sources) else 'ok'
    merged = merge_items(new_items, previous.get('items', []), now)
    # Persist screened and excluded title-only candidates separately before filtering.
    from candidate_archive import persist_candidates
    candidate_total, candidate_new = persist_candidates(candidates)
    print(f'Candidate register: {candidate_total} total; {candidate_new} new; {len(new_items)} screened in')
    # Archive all accepted observations BEFORE the 240-item recent-snapshot cap.
    from archive_data import persist as persist_archive
    archived_total, archived_new = persist_archive([*new_items, *merged], iso(now))
    print(f'Permanent archive: {archived_total} public records, {archived_new} newly archived')
    # Prior successes remain visible even when this collection fails.
    last_success = iso(now) if status in ('ok', 'partial') else previous.get('last_successful_collection')
    output = {'schema_version':1, 'generated_at':iso(now),'last_successful_collection':last_success,
              'status':status,'sources':sources,'items':merged,'warnings':warnings[:20],
              'retrieval_quality':{
                  'screening_version':SCREEN_VERSION,'candidate_count':len(candidates),
                  'accepted_observations':len(new_items),'excluded_observations':len(candidates)-len(new_items),
                  'academic_records_accepted':sum(x.get('kind')=='academic' for x in new_items),
                  'candidate_archive_total':candidate_total,
                  'scope':'bounded RSS and Crossref result windows, not full web coverage'
              }}
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(output, ensure_ascii=False, indent=2)+'\n',encoding='utf-8')
    print(f'Collection status: {status}; sources ok: {success}/{len(sources)}; new: {len(new_items)}; retained: {len(merged)}')
    if status == 'failed':
        print('WARNING: no successful useful collection. The workflow must signal failure after publishing.', file=sys.stderr)


def process_source(item, kind, task, new_items, warnings, now):
    meta = {'id':item['id'],'name':item['name'],'type':kind,'status':'failed','last_attempt':iso(now),'items':0}
    try:
        entries = task()
        new_items.extend(entries)
        meta['status'] = 'ok'
        meta['items'] = len(entries)
    except (HTTPError, URLError, ValueError, KeyError, TypeError, ElementTree.ParseError, UnicodeError, TimeoutError, OSError) as exc:
        # Never print request headers, credentials, full responses, or environment variables.
        warning = f"{item['id']}: {type(exc).__name__} (see source connectivity and format)"
        warnings.append(warning)
        print(warning, file=sys.stderr)
    return meta


if __name__ == '__main__':
    run()
