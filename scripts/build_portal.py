#!/usr/bin/env python3
"""Build the public multi-page index without modifying canonical data or legacy sources.

Input: docs/ (data and existing workbench), portal/ (shared UI assets).
Output: _site/ only. The GitHub Pages deployment must upload _site, not docs.
Uses Python's standard library to build from local project files.
"""
from __future__ import annotations
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '_site'
REPO = 'https://github.com/e4e421/supply-chain-rights-observatory'
NAMES = [('','Research Portal'),('archive','Research Archive'),('sources','Source Directory'),
         ('policy','Policy Monitor'),('research','Research Framework'),('methodology','Data & Methodology')]
CSP = "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'none'; object-src 'none'; frame-src 'none'; upgrade-insecure-requests"
E = html.escape

def tx(text: str, tag: str='span', attrs: str='') -> str:
    return f'<{tag} data-pk="{E(text, quote=True)}" {attrs}>{E(text)}</{tag}>'

def link(path: str, label: str, cls: str='') -> str:
    return f'<a class="{cls}" href="{E(path, quote=True)}">{tx(label)}</a>'

def external(url: str, label: str) -> str:
    return f'<a href="{E(url, quote=True)}" target="_blank" rel="noopener noreferrer">{tx(label)} <span aria-hidden="true">↗</span></a>'

def searchbox(id: str='site-search') -> str:
    return f'<div class="portal-search" role="search"><label class="sr-only" for="{id}">{tx("Search public records")}</label><input id="{id}" type="search" maxlength="120" autocomplete="off" data-ph="Title, publisher, DOI or record ID" placeholder="Title, publisher, DOI or record ID"><button type="button" id="{id}-go">{tx("Search archive")}</button></div>'

def header(page: str, base: str) -> str:
    nav=''.join(f'<a href="{base}{route+"/" if route else "index.html"}"'+(' aria-current="page"' if route==page else '')+'>'+tx(name)+'</a>' for route,name in NAMES)
    return f'''<a class="skip-link" href="#main">{tx('Skip to content')}</a>
<header class="portal-header"><div class="portal-top">
<a class="portal-brand" href="{base}index.html"><b>SCRO</b><span>SUPPLY CHAIN<br>RIGHTS OBSERVATORY</span></a>
<div class="portal-actions"><label for="language-select" class="language-picker"><span class="sr-only">Language</span><select id="language-select" aria-label="Select website language"><option value="en">English</option><option value="zh">繁體中文</option><option value="de">Deutsch</option></select></label>
{link(base+'workbench/','Research Workbench','portal-workbench')}</div></div>
<nav class="portal-nav" aria-label="Main navigation">{nav}</nav></header>'''

def shell(page: str, title: str, subtitle: str, body: str, home=False) -> str:
    base='./' if not page or page=='record' else '../'
    intro='' if home else f'<div class="portal-intro"><div class="breadcrumbs">{link(base+"index.html","Research Portal")} / {tx(title)}</div>{tx(title,"h1")}{tx(subtitle,"p")}{searchbox()}</div>'
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="{E(subtitle, quote=True)}"><meta name="referrer" content="strict-origin-when-cross-origin">
<meta http-equiv="Content-Security-Policy" content="{CSP}"><title>{E(title)} | Supply Chain Rights Observatory</title>
<link rel="stylesheet" href="{base}styles.css"><link rel="stylesheet" href="{base}portal.css">
<script defer src="{base}i18n.js"></script><script defer src="{base}query.js"></script><script defer src="{base}portal.js"></script></head>
<body class="portal" data-page="{page or 'home'}" data-page-title="{E(title, quote=True)}">
{header(page,base)}<main id="main" class="portal-main">{intro}{body}</main>
<footer class="portal-footer"><b>Supply Chain Rights Observatory</b>
<div>{link(base+'methodology/','Methods & limitations')} · {external(REPO,'Source code')}</div></footer>
<noscript><p class="portal-notice">JavaScript is required for interactive search. Navigation and research guidance remain available. <a href="{REPO}/tree/main/data/archive">Public JSONL archive</a></p></noscript></body></html>'''

def option(value: str, label: str) -> str:
    return f'<option value="{value}" data-pk="{E(label, quote=True)}">{E(label)}</option>'

def field(id: str, label: str, inner: str) -> str:
    return f'<label for="{id}" class="portal-field">{tx(label)}{inner}</label>'

def topics() -> str:
    return ''.join(option(k,v) for k,v in [('all','All topics'),('policy','Policy & governance'),('forced-labour','Forced labour'),('working-conditions','Working conditions'),('worker-voice','Worker voice & remedy'),('network','Supply networks'),('research','Academic research')])

def build() -> None:
    if OUT.exists(): shutil.rmtree(OUT)
    shutil.copytree(ROOT/'docs',OUT,symlinks=False)
    for name in ('portal.js','portal.css','portal-translations.json'):
        shutil.copy2(ROOT/'portal'/name,OUT/name)
    cards=''.join(f'<a href="./{route}/" class="portal-card"><small>{num:02d}</small>{tx(title,"h2")}{tx(desc,"p")}{tx("Explore","span", "class=card-arrow")}</a>' for num,(route,title,desc) in enumerate([
        ('archive','Research Archive','Search historical publication records, dates, DOI and stable IDs.'),
        ('sources','Source Directory','Inspect institutional sources, editorial review and link availability.'),
        ('policy','Policy Monitor','Separate policy dates from publication dates and find official texts.'),
        ('research','Research Framework','Turn supply-network, governance and labour questions into searches.'),
        ('methodology','Data & Methodology','Understand field definitions, coverage, exports and research limitations.'),
        ('workbench','Research Workbench','Open the dense researcher workspace for daily data checks.')],1))
    home=f'''<section class="portal-hero"><div><p class="portal-kicker">SUPPLY CHAIN · HUMAN RIGHTS · LABOUR</p>
<h1>Where supply chains<br>meet <em>human rights.</em></h1>{tx('A public research index. Start with a search, then inspect the source.','p')}{searchbox()}
<div class="portal-hero-links">{link('./archive/','Browse historical records')} {link('./workbench/','Research Workbench')}</div></div>
<aside>{tx('Two ways to work','h2')}{tx('New here? Explore records and sources. Returning researcher? Open the Workbench.','p')}</aside></section>
<section class="portal-stats" aria-label="Dataset overview"><div>{tx('Historical records')}<strong id="home-total">—</strong></div><div>{tx('Curated reference sources')}<strong id="home-sources">—</strong></div><div>{tx('Last successful collection')}<strong id="home-updated">—</strong></div><div>{tx('Technical collection status')}<strong id="home-health">—</strong></div></section>
<section class="portal-sections">{tx('Explore the research index','h2')}<div class="portal-card-grid">{cards}</div></section>
<section id="signals"><div class="portal-section-heading">{tx('Latest research intelligence','h2')}{link('./workbench/?scope=latest','View all latest records')}</div><p id="home-status" role="status" aria-live="polite">Loading public data…</p><div id="home-latest" class="portal-record-list"></div></section>'''
    write('',shell('','Research Portal','Public research index for supply chains, human rights and labour.',home,True))
    archive=f'''<section class="portal-stats"><div>{tx('Historical records')}<strong id="archive-total">—</strong></div><div>{tx('First-observation partitions')}<strong id="archive-partitions">—</strong></div><div>{tx('Dataset build revision')}<code id="archive-revision">—</code></div></section>
<p class="portal-notice">{tx('Month groups use first observation. Date filters use publication date.')}</p>
<div class="portal-filter-grid">
{field('archive-month','First observed month','<select id="archive-month">'+option('all','All available months')+'</select>')}
{field('archive-search','Search title, publisher, DOI or record ID','<input id="archive-search" type="search" maxlength="120" autocomplete="off">')}
{field('archive-topic','Research theme','<select id="archive-topic">'+topics()+'</select>')}
{field('archive-kind','Record type','<select id="archive-kind">'+option('all','All types')+option('academic','Academic metadata')+option('discovery','Discovery leads')+'</select>')}
{field('archive-from','Published from','<input id="archive-from" type="date">')}
{field('archive-to','Published through','<input id="archive-to" type="date">')}
</div><p class="portal-help">{tx('Search terms use AND by default. Use OR for alternatives and quotes for exact phrases.')}</p>
<div class="portal-tools"><button id="archive-reset" type="button">{tx('Reset filters')}</button><button id="archive-export" type="button">{tx('Export filtered CSV')}</button><button id="archive-metadata" type="button">{tx('Export query metadata')}</button><button id="share-query" type="button">{tx('Copy shareable link')}</button>{link('../workbench/?scope=all','Advanced search')}{link('../sources/#academic-monitoring','Academic literature monitoring')}</div>
<p id="archive-coverage" class="portal-notice" role="status"></p><p id="archive-count" role="status" aria-live="polite">Loading archive…</p><div id="archive-results" class="portal-record-list"></div><button id="archive-show-more" type="button" hidden>{tx('Show more archive records')}</button>
<p id="portal-feedback" role="status" aria-live="polite"></p>
<details class="portal-document"><summary>{tx('Canonical data and integrity')}</summary>{tx('The browser has bounded loading. Partial coverage is labelled explicitly; the canonical JSONL archive is the long-term source.','p')}
{external(REPO+'/tree/main/data/archive','Public JSONL archive')} · {external(REPO+'/blob/main/data/archive/manifest.json','Integrity manifest')}</details>'''
    write('archive',shell('archive','Research Archive','Search historical publication records, dates, DOI and stable IDs.',archive))
    automatic_academic = [
        ('https://www.crossref.org/documentation/retrieve-metadata/rest-api/', 'Crossref',
         'Publisher-deposited bibliographic metadata and DOI lookup.'),
        ('https://help.openalex.org/api/', 'OpenAlex',
         'Bibliographic discovery through an open index of works and citations.'),
    ]
    manual_academic = [
        ('https://scholar.google.com/', 'Google Scholar',
         'Search across publications and set keyword or citation alerts on the platform.'),
        ('https://www.litmaps.com/', 'Litmaps',
         'Start from a seed paper, explore citation connections, and set up Monitor on the platform.'),
        ('https://www.semanticscholar.org/', 'Semantic Scholar',
         'Find related papers and follow new recommendations through Research Feeds.'),
        ('https://www.webofscience.com/wos/woscc/basic-search', 'Web of Science Core Collection',
         'Cross-check indexed records and citation trails. Access depends on your institution or plan.'),
    ]
    academic_channels = f'''<section class="portal-document" id="academic-monitoring" aria-labelledby="academic-monitoring-title">
{tx('Academic literature monitoring','h2','id="academic-monitoring-title"')}
{link('../archive/?kind=academic','Search academic records')}
{tx('Automatic metadata collection','h3')}
<ul id="academic-automatic">{''.join('<li>'+external(url,name)+' '+tx(use)+'</li>' for url,name,use in automatic_academic)}</ul>
{tx('External research and alerts','h3')}
{tx('Open these platforms to search or set up alerts in your own account where required. Their results and alerts are separate from this site’s database.','p')}
<ul id="academic-manual">{''.join('<li>'+external(url,name)+' '+tx(use)+'</li>' for url,name,use in manual_academic)}</ul>
{tx('For each lead, verify the DOI, publication version and peer-review status at the original source. Record the platform, search terms and date for reproducibility.','p')}
</section>'''
    sources=f'''<section id="data-availability" aria-labelledby="data-availability-title">
{tx('Source availability','h2','id="data-availability-title"')}
{tx('Green indicates a successful check. Yellow waits for the next scheduled attempt. Red asks for manual confirmation after three consecutive failures. Gray marks manual sources or checks with no recorded result.','p','class="portal-notice"')}
{tx('Automated collection feeds','h3')}
{tx('A successful retrieval can return zero matching records.','p','class="portal-help"')}
<div class="portal-table-wrap" tabindex="0" aria-labelledby="data-availability-title"><table class="portal-table"><thead><tr>{''.join(tx(x,'th','scope=col') for x in ['Collection feed','Availability','Matching records','Last attempt'])}</tr></thead><tbody id="source-feed-rows"></tbody></table></div>
</section>
{tx('Curated reference links','h2')}
{tx('Reference availability checks the website connection. For gray manual references, open the original link.','p','class="portal-help"')}
<div class="portal-filter-grid portal-source-filters">
{field('source-search','Search institutions','<input id="source-search" type="search" maxlength="120">')}
{field('source-category','Category','<select id="source-category">'+option('all','All categories')+'</select>')}
{field('source-review','Review filter','<select id="source-review">'+option('all','All sources')+option('needs','Editorial review needed')+option('licence','Licence review pending')+option('connection','Connection needs attention')+'</select>')}
</div><div class="portal-tools"><button id="share-query" type="button">{tx('Copy shareable link')}</button>{external(REPO+'/issues/new/choose','Propose a source or correction')}{link('#academic-monitoring','Academic literature monitoring')}</div>
<p id="source-count" role="status" aria-live="polite">Loading public data…</p><p id="portal-feedback" role="status"></p>
<div class="portal-table-wrap" tabindex="0" aria-label="Source directory"><table class="portal-table"><thead><tr>{''.join(tx(x,'th','scope=col') for x in ['Institution & research use','Category','Editorial review','Licence review','Availability'])}</tr></thead><tbody id="source-rows"></tbody></table></div>
<p class="portal-help">{tx('New automated collection hosts require a separate review.')}</p>
{academic_channels}'''
    write('sources',shell('sources','Source Directory','Inspect institutional sources, editorial review and link availability.',sources))
    csddd='https://commission.europa.eu/topics/business-and-industry/company-law-and-corporate-governance/corporate-sustainability-due-diligence_en'
    flr='https://single-market-economy.ec.europa.eu/single-market/goods/forced-labour-regulation/what-forced-labour-regulation-and-how-does-it-work_en'
    policy=f'''<p class="portal-notice">{tx('Reference timeline checked on 2026-11-09. Consult the current official text for applicability.')}</p><div class="portal-policy-grid">
<article class="portal-document"><span class="portal-tag">EU / FLR</span>{tx('EU Forced Labour Regulation','h2')}<time datetime="2027-12-14">2027-12-14</time>
{tx('Product prohibition becomes applicable. This regulation does not itself impose a corporate due-diligence procedure.','p')}{external(flr,'European Commission source')}<p>{link('../archive/?topic=forced-labour','Find related records')}</p></article>
<article class="portal-document"><span class="portal-tag">EU / CSDDD</span><h2>CSDDD</h2><dl>
{tx('National transposition deadline','dt')}<dd><time datetime="2028-07-26">2028-07-26</time></dd>{tx('Application of principal duties','dt')}<dd><time datetime="2029-07-26">2029-07-26</time></dd>{tx('Article 16 reporting: financial years beginning from','dt')}<dd><time datetime="2030-01-01">2030-01-01</time></dd></dl>
{tx('Based on the amended framework. Check the current official text and national implementation before coding exposure.','p')}{external(csddd,'European Commission source')}<p>{link('../archive/?topic=policy','Find related records')}</p></article></div>
<section class="portal-document">{tx('Keep four clocks separate','h2')}{tx('Policy timelines distinguish announcement, application, publication and first observation.','p')}
{link('../methodology/','Data & Methodology')} · {link('../sources/?category=EU%20LAW','Official legal sources')}</section>'''
    write('policy',shell('policy','Policy Monitor','Separate policy dates from publication dates and find official texts.',policy))
    # Reuse the research themes from the legacy page.
    old=(ROOT/'docs/index.html').read_text(encoding='utf-8')
    lens=re.search(r'<div class="lens-grid">(.*?)</div></div></section>',old,re.S)
    if not lens: raise ValueError('Legacy research framework anchor missing; review migration')
    articles=re.findall(r'<article class="lens-card">.*?</article>',lens.group(1),re.S)
    if len(articles)!=4:raise ValueError('Expected four research themes')
    for i,topic in enumerate(['network','policy','worker-voice','research']):
        articles[i]=articles[i].replace('</article>',f'<p>{link("../archive/?topic="+topic,"Find related records")}</p></article>')
    research=f'''<p class="portal-notice">{tx('Explore research themes in supply-chain governance and social sustainability.')}</p>
<div class="portal-card-grid">{''.join(articles)}</div>
<section class="portal-document">{tx('Literature discovery','h2')}{tx('Check the DOI, publication version and peer-review status at the publisher.','p')}{link('../archive/?kind=academic','Search academic records')} · {link('../sources/#academic-monitoring','Academic literature monitoring')}</section>'''
    write('research',shell('research','Research Framework','Turn supply-network, governance and labour questions into searches.',research))
    dictionary=[('record_id','Stable publication identifier.'),('event_id','Unassigned until a separately reviewed event-linking decision.'),('published_at','Publication timestamp supplied by the source.'),('first_seen','First observation by this collection pipeline.'),('publisher_hint','Publisher attribution supplied by the source.'),('evidence_status','Discovery or bibliographic class; not a verdict.'),('topics','Preliminary machine tags, not human-reviewed entity coding.')]
    methodology=f'''<section class="portal-document">{tx('Storage and retention','h2')}{tx('The latest view is capped at 240 records and 150 days. The monthly first-observation archive does not expire on that schedule.','p')}{tx('Corrections need an auditable review. A normal Git deletion does not erase public history.','p')}</section>
<section class="portal-document">{tx('Core field dictionary','h2')}<dl class="portal-dictionary">{''.join('<dt><code>'+field+'</code></dt><dd>'+tx(definition)+'</dd>' for field,definition in dictionary)}</dl></section>
<section class="portal-document">{tx('Coverage and research use','h2')}{tx('Search ranking, language, reporting and title screening introduce selection bias. Record counts must not be interpreted as violation rates.','p')}{tx('Full-text articles are not redistributed. Metadata reuse rights still require source-specific review.','p')}{link('../sources/?review=licence','Inspect licensing reviews')}</section>
<section class="portal-document">{tx('Updates and reproducibility','h2')}{tx('Collection is scheduled daily at 06:23 Taipei time; source checks run weekly. Schedules can be delayed. Use the actual collection timestamp.','p')}{tx('Record links remain stable across pages. CSV uses English field names; query metadata records filters, coverage and the build revision.','p')}{link('../archive/','Research Archive')} · {external(REPO+'/blob/main/CITATION.cff','Citation metadata')}</section>
<section class="portal-document">{tx('Technical documentation (English)','h2')}<ul>{''.join('<li>'+link('../'+file,label)+'</li>' for file,label in [('DATA_DICTIONARY.md','Data dictionary'),('DATASET_CARD.md','Dataset card'),('ARCHITECTURE.md','Data architecture'),('BACKUP_RECOVERY.md','Backup and recovery'),('SECURITY_QA.md','Security verification'),('ACCESSIBILITY_QA.md','Accessibility checks')])}</ul></section>'''
    write('methodology',shell('methodology','Data & Methodology','Understand field definitions, coverage, exports and research limitations.',methodology))
    write('record',shell('record','Research record','Inspect publication details and provenance.', '<section id="record-content" class="record-page" aria-live="polite"><p>Loading archive…</p></section>'+link('./archive/','Return to archive')))
    # Preserve the existing professional UI and its hard-won responsive layout.
    p=OUT/'workbench/index.html';wb=p.read_text(encoding='utf-8')
    wb=wb.replace('../index.html#sources','../sources/#data-availability').replace('../index.html#method','../methodology/')
    wb=wb.replace('<body class="wb">','<body class="wb" data-page="workbench" data-page-title="Research Workbench">')
    wb=wb.replace('</head>','<link rel="stylesheet" href="../portal.css"><script defer src="../portal.js"></script></head>')
    wnav='<nav class="portal-workbench-nav" aria-label="Research index">'+''.join(link('../'+route+'/',title) for route,title in NAMES if route)+'</nav>'
    wb=wb.replace('</header>','</header>'+wnav,1);p.write_text(wb,encoding='utf-8')

    # The editor is another view of the SAME Workbench, not a second database.
    # Resolve project-relative assets one directory deeper without using a <base>
    # element (the site's Content-Security-Policy explicitly disallows base-uri).
    edit=wb.replace('data-page="workbench" data-page-title="Research Workbench"',
                    'data-page="workbench-editor" data-page-title="Review Editor"')
    edit=edit.replace('<a class="wb-editor-link" href="./edit/" data-l10n="Open Review Editor">Open Review Editor</a>', '')
    editor_notice = ('<div class="wb-editor-notice">'
                     '<strong data-l10n="You are in the Review Editor">You are in the Review Editor</strong>'
                     '<a id="wb-return-to-reader" href="./"><span aria-hidden="true">←</span> '
                     '<span data-l10n="Return to the read-only view">Return to the read-only view</span></a></div>')
    edit=edit.replace('<header class="wb-header">', editor_notice+'\n  <header class="wb-header">', 1)
    edit=edit.replace('data-l10n="Research Workbench">Research Workbench',
                      'data-l10n="Review Editor">Review Editor')
    edit=edit.replace("connect-src 'self';","connect-src 'self' https://api.github.com;")
    def one_level_deeper(match):
        attr,original=match.group(1),match.group(2)
        if original.startswith('../'):new='../'+original
        elif original.startswith('./'):new='../'+original[2:]
        else:new=original
        return attr+'="'+new+'"'
    edit=re.sub(r'\b(href|src)="(\.\.?/[^"]*)"',one_level_deeper,edit)
    edit_path=OUT/'workbench/edit/index.html'
    edit_path.parent.mkdir(parents=True,exist_ok=True)
    edit_path.write_text(edit,encoding='utf-8')

    # Build a lightweight record locator; it contains no new research claims.
    catalog=json.loads((OUT/'data/archive/catalog.json').read_text(encoding='utf-8'))
    locator={}
    for month in catalog['months']:
        for part in month['files']:
            if not re.fullmatch(r'\d{4}-\d{2}-\d{4}\.json',part['file']):raise ValueError('Unsafe shard filename')
            shard=json.loads((OUT/'data/archive'/part['file']).read_text(encoding='utf-8'))
            for rec in shard['records']:
                rid=rec['record_id']
                if not re.fullmatch(r'[a-f0-9]{18}',rid) or rid in locator:raise ValueError('Invalid or duplicate archive ID')
                locator[rid]={'month':month['month'],'file':part['file']}
    if len(locator)!=catalog['total_records']:raise ValueError('Record index count mismatch')
    (OUT/'data/record-index.json').write_text(json.dumps({'schema_version':1,'records':locator},ensure_ascii=False)+'\n',encoding='utf-8')
    latest=json.loads((OUT/'data/latest.json').read_text(encoding='utf-8'))
    try:
        revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True,stderr=subprocess.DEVNULL).strip()
    except (OSError,subprocess.CalledProcessError):
        revision=os.environ.get('GITHUB_SHA','local-preview')
    build={'schema_version':1,'portal_version':'index-v1','git_revision':revision,
           'collection_generated_at':latest.get('generated_at'),
           'catalog_sha256':hashlib.sha256((OUT/'data/archive/catalog.json').read_bytes()).hexdigest(),
           'total_archive_records':catalog['total_records']}
    (OUT/'data/build-info.json').write_text(json.dumps(build,indent=2)+'\n',encoding='utf-8')
    # The deployment publishes the generated site files.
    print(f'Built 5 index subpages, homepage, record view and connected Workbench; {len(locator)} record locators.')

def write(page: str, content: str) -> None:
    path=OUT/('record.html' if page=='record' else page+'/index.html' if page else 'index.html')
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(content,encoding='utf-8')

if __name__=='__main__':build()
