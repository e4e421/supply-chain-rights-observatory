#!/usr/bin/env python3
"""Real Chrome tests of the generated deployment; test-only probe is never published."""
import html,json,re,shutil,subprocess,tempfile
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import urlencode
ROOT=Path(__file__).resolve().parents[1]
CHROME=next((shutil.which(x) for x in ('google-chrome','chromium','chromium-browser','google-chrome-stable') if shutil.which(x)),None)
PROBE=r'''
(async()=>{
 const errors=[];window.addEventListener('error',e=>errors.push(e.message));
 for(let i=0;i<100&&!window.__PORTAL_READY__&&!window.__PORTAL_ERROR__;i++)await new Promise(r=>setTimeout(r,75));
 const page=document.body.dataset.page;
 const check=(value,message)=>{if(!value)errors.push(message);};
 const initial=new URL(location.href);
 const isReader=href=>new URL(href).pathname.endsWith('/workbench/');
 const fixtureRecord='__UTC_TEST_RECORD_ID__';
 const fixtureMonth='__UTC_TEST_FIRST_SEEN_MONTH__';
 const monthFilter=()=>document.getElementById('wb-first-seen-month');
 const monthOptionsReady=()=>[...(monthFilter()?.options||[])].some(option=>option.value===fixtureMonth);
 const picker=document.getElementById('language-select');
 const lang=picker.value;
 const dateLocale={en:'en-GB',zh:'zh-TW',de:'de-DE',es:'es-ES'}[lang];
 const utcDay=new Intl.DateTimeFormat(dateLocale,{timeZone:'UTC',year:'numeric',month:'2-digit',day:'2-digit'})
   .format(new Date('2026-11-10T19:39:16Z'));
 const dispatch=(id,value,event)=>{const control=document.getElementById(id);control.value=value;control.dispatchEvent(new Event(event,{bubbles:true}));};
 check(window.__PORTAL_READY__,'Portal did not finish loading');
 check(document.documentElement.lang===({en:'en',zh:'zh-Hant',de:'de',es:'es'})[initial.searchParams.get('lang')||'en'],'Incorrect language');
 check(!document.querySelector('#site-search, #archive-search, #archive-results'),'Duplicate portal search UI');
 if(document.documentElement.lang==='es'){
  check(picker.value==='es'&&picker.options[picker.options.length-1].textContent==='Español','Spanish picker option missing');
  check(picker.getAttribute('aria-label')==='Seleccionar el idioma del sitio','Spanish accessible label missing');
  check(window.SCRO_I18N.formatNumber(12345)===new Intl.NumberFormat('es-ES').format(12345),'Spanish number formatting is incorrect');
 }
 if(page==='home'){
  check(document.querySelectorAll('.portal-record').length>0,'Homepage records absent');
  check([...document.querySelectorAll('main a')].some(a=>isReader(a.href)),'Homepage Workbench search entry missing');
 }
 if(page==='sources'){
  check(document.querySelectorAll('#source-rows tr').length>1,'Source directory absent');
  check(document.querySelector('#source-feed-rows .is-ok'),'Successful collection feed status missing');
  check(document.querySelector('#source-feed-rows .is-retry'),'Retry status missing');
  check(document.querySelector('#source-feed-rows .is-review'),'Manual confirmation status missing');
  check(document.querySelector('#source-rows .is-ok'),'Successful reference status missing');
  check(document.querySelector('#source-rows .is-manual'),'Manual reference status missing');
  const media=[...document.querySelectorAll('#source-rows td small')].filter(n=>n.textContent.startsWith('media-'));
  const manualStatus={en:'Not checked automatically','zh-Hant':'未執行自動連線檢查',de:'Nicht automatisch geprüft',es:'Comprobación automática no realizada'}[document.documentElement.lang];
  check(media.length===11&&media.every(n=>n.closest('tr').lastElementChild.textContent.includes(manualStatus)),
    'Approved manual media missing or mislabelled');
  const section=document.getElementById('academic-monitoring');
  const expectedTitle={en:'Academic literature monitoring','zh-Hant':'學術文獻觀察',de:'Beobachtung wissenschaftlicher Literatur',es:'Seguimiento de literatura académica'};
  check(section?.querySelector('h2')?.textContent===expectedTitle[document.documentElement.lang],'Academic monitoring section missing or untranslated');
  const hosts=id=>[...document.querySelectorAll('#'+id+' a')].map(a=>new URL(a.href).hostname).join(',');
  check(hosts('academic-automatic')==='www.crossref.org,help.openalex.org','Incorrect automated academic source list');
  check(hosts('academic-manual')==='scholar.google.com,www.litmaps.com,www.semanticscholar.org,www.webofscience.com','Incorrect external academic channel list');
  const academic=section?.querySelector('a[href*="kind=academic"]');
  check(academic&&isReader(academic.href)&&new URL(academic.href).searchParams.get('kind')==='academic',
   'Academic Workbench shortcut missing');
  const q=document.getElementById('source-search');q.value='NO_MATCH_9031';q.dispatchEvent(new Event('input',{bubbles:true}));
  check(document.getElementById('source-count').textContent.startsWith('0 /'),'Source filter failed');
  q.value='';q.dispatchEvent(new Event('input',{bubbles:true}));
 }
 if(page==='record'){
  const root=document.getElementById('record-content');
  check(root.textContent.includes(initial.searchParams.get('id')||'UNEXPECTED'),'Stable record link failed');
  check(root.querySelector('dd')?.textContent===utcDay,'Record publication day differs from UTC');
  check([...root.querySelectorAll('dd')].some(d=>d.textContent.endsWith(' UTC')),'Record observation timestamp lacks UTC');
  const back=document.getElementById('record-return-to-search');
  check(back&&isReader(back.href),'Record return link did not target the Workbench');
  if(back){
   const old=new URLSearchParams(initial.searchParams.get('back')||'');
   const returned=new URL(back.href).searchParams;
   for(const [prior,current] of [
    ['q','q'],['month','firstSeenMonth'],['topic','topics'],['kind','kind'],['from','from'],['to','to'],['tag','tag']
   ]){
    if(old.has(prior))check(returned.get(current)===old.get(prior),'Record return lost '+current);
   }
   if(!old.size)check(returned.get('record')===fixtureRecord,'Record return did not keep the current record selected');
   check(returned.get('lang')===lang&&!returned.has('relevance'),'Record return language or editor filter is wrong');
  }
 }
 if(page==='workbench'&&initial.searchParams.has('q')){
  check(document.getElementById('wb-search').value===initial.searchParams.get('q'),'Redirect lost search input');
  check(document.getElementById('wb-kind').value===(initial.searchParams.get('kind')||'all'),'Redirect lost record type');
  check(document.getElementById('wb-from').value===(initial.searchParams.get('from')||'')&&
   document.getElementById('wb-to').value===(initial.searchParams.get('to')||''),'Redirect lost dates');
  const topics=[...document.querySelectorAll('[name=wb-topic]:checked')].map(input=>input.value);
  check(topics.join(',')===(initial.searchParams.get('topics')||''),'Redirect lost research topics');
  for(let i=0;i<60&&!monthOptionsReady();i++)await new Promise(resolve=>setTimeout(resolve,50));
  check(monthFilter()?.value===initial.searchParams.get('firstSeenMonth'),'Redirect lost the first-observed month');
  check(!document.querySelector('#wb-tbody [data-record-id]'),'Zero-result URL filter failed');
 }else if(page==='workbench'){
  for(let i=0;i<60&&!document.querySelector('[data-record-id]');i++)await new Promise(r=>setTimeout(r,50));
  check(document.querySelectorAll('[data-record-id]').length>0,'Workbench records absent');
  const rail=document.querySelector('.wb-filters').getBoundingClientRect();
  for(const id of ['wb-from','wb-to']){const r=document.getElementById(id).getBoundingClientRect();check(r.left>=rail.left-2&&r.right<=rail.right+2,'Date control overflow');}
  const wrap=document.querySelector('.wb-table-wrap'),prev=document.getElementById('wb-prev'),next=document.getElementById('wb-next');
  check(Boolean(prev&&next),'Result pagination controls absent');
  if(prev&&next){
   const expected=Number(document.getElementById('wb-count').dataset.total),ids=[];
   check(Number.isInteger(expected)&&expected>0,'Invalid total matching count');
   check(prev.disabled,'Previous page enabled on first page');
   for(let step=0;step<400;step++){
    const rows=[...document.querySelectorAll('#wb-tbody [data-record-id]')];
    check(rows.length<=40,'Too many rows mounted');
    check(wrap.scrollHeight<=wrap.clientHeight+2,'Nested vertical result overflow');
    if(rows.length)check(rows.at(-1).getBoundingClientRect().bottom<=wrap.getBoundingClientRect().bottom+2,'Last result is clipped');
    ids.push(...rows.map(x=>x.dataset.recordId));
    if(next.disabled)break;
    next.click();
   }
   check(ids.length===expected&&new Set(ids).size===expected,'Pagination loses or repeats records');
   for(let i=0;i<400&&!prev.disabled;i++)prev.click();
   const input=document.getElementById('wb-search');input.value='SCRO_NO_RESULTS_9031';input.dispatchEvent(new Event('input',{bubbles:true}));
   check(!document.querySelector('#wb-tbody [data-record-id]')&&prev.disabled&&next.disabled,'Empty pagination boundary failed');
   input.value='';input.dispatchEvent(new Event('input',{bubbles:true}));
   check(prev.disabled,'Filter reset does not return to first page');
   const density=document.getElementById('wb-density');density.value='comfortable';density.dispatchEvent(new Event('change',{bubbles:true}));
   check(wrap.scrollHeight<=wrap.clientHeight+2,'Comfortable density overflows');
   density.value='compact';density.dispatchEvent(new Event('change',{bubbles:true}));
   const blobs=[],create=URL.createObjectURL,click=HTMLAnchorElement.prototype.click;
   URL.createObjectURL=b=>{blobs.push(b);return create(b);};
   HTMLAnchorElement.prototype.click=function(){if(!this.download)click.call(this);};
   document.getElementById('wb-export').click();
   if(blobs.length){const csv=await blobs[0].text();check(csv.split('\r\n').length-1===expected,'CSV exports only current page');}
   else check(false,'Workbench CSV missing');
   URL.createObjectURL=create;HTMLAnchorElement.prototype.click=click;
  }
  dispatch('wb-search',fixtureRecord,'input');
  dispatch('wb-to','2026-11-10','change');
  const month=monthFilter();
  const metadataButton=document.getElementById('wb-query-metadata');
  check(monthOptionsReady()&&metadataButton,'Workbench month filter or metadata export missing');
  if(month){
   month.value=fixtureMonth;
   month.dispatchEvent(new Event('change',{bubbles:true}));
  }
  const row=()=>document.querySelector('[data-record-id="'+fixtureRecord+'"]');
  for(let i=0;i<60&&(!row()||metadataButton?.disabled);i++)await new Promise(resolve=>setTimeout(resolve,50));
  const fixtureRow=row();
  check(new URL(location.href).searchParams.get('firstSeenMonth')===fixtureMonth,'Month filter did not update the URL');
  check(fixtureRow?.querySelector('.wb-date-cell')?.textContent===utcDay,'Workbench date filter or display differs from UTC');
  if(metadataButton){
   const blobs=[],create=URL.createObjectURL,click=HTMLAnchorElement.prototype.click;
   URL.createObjectURL=blob=>{blobs.push(blob);return create(blob);};
   HTMLAnchorElement.prototype.click=function(){if(!this.download)click.call(this);};
   try{
    metadataButton.click();
    for(let i=0;i<60&&!blobs.length;i++)await new Promise(resolve=>setTimeout(resolve,50));
    check(blobs.length===1,'Query metadata export missing');
    if(blobs.length){
     const metadata=JSON.parse(await blobs[0].text());
     check(metadata.filters?.q===fixtureRecord&&metadata.filters?.firstSeenMonth===fixtureMonth&&
      metadata.matched_records===1&&metadata.coverage==='requested_scope_complete'&&
      metadata.shards?.length>0&&metadata.build?.git_revision,'Query metadata lacks filters or provenance');
    }
   }finally{URL.createObjectURL=create;HTMLAnchorElement.prototype.click=click;}
  }
  fixtureRow?.click();
  const detail=[...document.querySelectorAll('#wb-detail a')].map(a=>new URL(a.href))
   .find(url=>url.origin===location.origin&&url.pathname.endsWith('/record.html'));
  const detailBack=new URLSearchParams(detail?.searchParams.get('back')||'');
  check(detail?.searchParams.get('id')===fixtureRecord&&detailBack.get('q')===fixtureRecord&&
   detailBack.get('to')==='2026-11-10'&&detailBack.get('firstSeenMonth')===fixtureMonth,
   'Workbench record link lost the search context');
  dispatch('wb-to','2026-11-09','change');
  check(!document.querySelector('[data-record-id="'+fixtureRecord+'"]'),'Workbench included a record after the UTC cutoff');
  const collectionTime=document.getElementById('wb-updated-utc');
  check(collectionTime?.tagName==='TIME'&&!collectionTime.hidden&&collectionTime.textContent.endsWith(' UTC'),
   'Collection timestamp lacks a visible UTC time');
 }
 if(page==='policy'){
  check(document.body.textContent.includes('2027-12-14')&&document.body.textContent.includes('2029-07-26'),'Policy dates absent');
  const presets=[...document.querySelectorAll('main a')].filter(a=>isReader(a.href)).map(a=>new URL(a.href).searchParams.get('topics'));
  check(presets.includes('forced-labour')&&presets.includes('policy'),'Policy Workbench presets missing');
 }
 check(document.documentElement.scrollWidth<=innerWidth+3,'Horizontal document overflow');
 const report={page,language:document.documentElement.lang,width:innerWidth,
  path:initial.pathname,params:Object.fromEntries(initial.searchParams),errors};
 const out=document.createElement('pre');out.id='portal-test-report';out.textContent=JSON.stringify(report);document.body.append(out);
})();
'''
def run():
 if not CHROME:raise SystemExit('FAIL: Chrome is required for migration acceptance; no browser detected')
 if not (ROOT/'_site/index.html').exists():raise SystemExit('Build _site first')
 qa=ROOT/'_qa';qa.mkdir(exist_ok=True)
 with tempfile.TemporaryDirectory() as tmp:
  root=Path(tmp);prefix='supply-chain-rights-observatory';site=root/prefix;shutil.copytree(ROOT/'_site',site)
  records=json.loads((site/'data/record-index.json').read_text())['records']
  overlay=json.loads((site/'data/relevance-index.json').read_text())['records']
  rid=next(key for key in records if overlay[key]['included'])
  shard=site/'data/archive'/records[rid]['file']
  archive=json.loads(shard.read_text(encoding='utf-8'))
  next(r for r in archive['records'] if r['record_id']==rid)['published_at']='2026-11-11T03:39:16+08:00'
  shard.write_text(json.dumps(archive,ensure_ascii=False),encoding='utf-8')
  probe=PROBE.replace('__UTC_TEST_RECORD_ID__',rid).replace('__UTC_TEST_FIRST_SEEN_MONTH__',records[rid]['month'])
  (site/'portal-test-probe.js').write_text(probe,encoding='utf-8')
  # Verify all three availability states on the isolated browser fixture.
  snapshot=site/'data/latest.json';fixture=json.loads(snapshot.read_text(encoding='utf-8'))
  for item in fixture['items']:
   if (item.get('record_id') or item.get('id'))==rid:item['published_at']='2026-11-11T03:39:16+08:00'
  for feed,failures in zip(fixture['sources'][:3], (0,1,3)):
   feed.update(status='failed' if failures else 'ok',consecutive_failures=failures)
  snapshot.write_text(json.dumps(fixture,ensure_ascii=False),encoding='utf-8')
  for p in site.rglob('*.html'):
   s=p.read_text(encoding='utf-8').replace('</body>',f'<script defer src="/{prefix}/portal-test-probe.js"></script></body>');p.write_text(s,encoding='utf-8')
  class Handler(SimpleHTTPRequestHandler):
   def log_message(self,*args):pass
  server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(root)));thread=Thread(target=server.serve_forever,daemon=True);thread.start()
  base=f'http://127.0.0.1:{server.server_port}/{prefix}/'
  paths=['','sources/','policy/','research/','methodology/','record.html?id='+rid,'workbench/']
  cases=[(p,lang,1440) for lang in ('en','zh','de','es') for p in paths]
  cases += [(p,'de',w) for w in (500,820,1600) for p in ('','sources/','workbench/')]
  cases += [(p,'es',390) for p in ('','sources/','workbench/')]
  legacy_filters={'q':'NO_MATCH_9031','month':records[rid]['month'],'topic':'forced-labour',
                  'kind':'academic','from':'2026-01-01','to':'2026-12-31'}
  legacy_params=urlencode({**legacy_filters,'relevance':'high','unrelated':'ignored'})
  redirects=[('archive/?'+legacy_params,'zh',1280),('?'+legacy_params+'&lang=de#archive-explorer','de',1280)]
  cases += redirects
  cases += [('?lang=de#'+old,'de',1280) for old in ('sources','lenses','method')]
  back=urlencode({**legacy_filters,'tag':'sample','relevance':'high'})
  cases += [('record.html?'+urlencode({'id':rid,'back':back}),'es',1280)]
  reports=[]
  try:
   for i,(path,lang,width) in enumerate(cases):
    url=base+path
    if '#' not in url:url+=('&' if '?' in url else '?')+'lang='+lang
    args=[CHROME,'--headless=new','--no-sandbox','--disable-gpu','--disable-dev-shm-usage',
          '--window-size='+str(width)+',1000','--force-device-scale-factor=1',
          '--virtual-time-budget=10000','--user-data-dir='+str(root/('browser-'+str(i))),'--dump-dom']
    if i<8:args+=['--screenshot='+str(qa/('portal-'+str(i)+'.png'))]
    r=subprocess.run(args+[url],capture_output=True,text=True,timeout=60,check=True)
    m=re.search(r'<pre id="portal-test-report">([^<]+)</pre>',r.stdout)
    if not m:raise AssertionError('Browser probe absent for '+url)
    report=json.loads(html.unescape(m.group(1)));reports.append(report)
    if (path,lang,width) in redirects:
     expected={**legacy_filters,'firstSeenMonth':legacy_filters['month'],'topics':legacy_filters['topic'],'lang':lang}
     del expected['month'],expected['topic']
     if report['path']!=f'/{prefix}/workbench/' or any(report['params'].get(key)!=val for key,val in expected.items()):
      report['errors'].append('Legacy URL lost its Workbench route or query parameters')
     if {'month','topic','relevance','unrelated'}&set(report['params']):
      report['errors'].append('Legacy URL kept unsupported parameters')
    print('PASS' if not report['errors'] else 'FAIL',path,lang,width,report,flush=True)
    if report['errors']:raise AssertionError(report)
  finally:
   (qa/'portal-test-results.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf-8')
   server.shutdown();thread.join(timeout=3)
 print('PASS',len(reports),'generated-page browser cases. Not a formal WCAG or penetration-test certification.')
if __name__=='__main__':run()
