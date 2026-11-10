#!/usr/bin/env python3
"""Real Chrome tests of the generated deployment; test-only probe is never published."""
import html,json,re,shutil,subprocess,tempfile
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from threading import Thread
ROOT=Path(__file__).resolve().parents[1]
CHROME=next((shutil.which(x) for x in ('google-chrome','chromium','chromium-browser','google-chrome-stable') if shutil.which(x)),None)
PROBE=r'''
(async()=>{
 const errors=[];window.addEventListener('error',e=>errors.push(e.message));
 for(let i=0;i<100&&!window.__PORTAL_READY__&&!window.__PORTAL_ERROR__;i++)await new Promise(r=>setTimeout(r,75));
 const page=document.body.dataset.page;
 const check=(value,message)=>{if(!value)errors.push(message);};
 check(window.__PORTAL_READY__,'Portal did not finish loading');
 check(document.documentElement.lang===({en:'en',zh:'zh-Hant',de:'de'})[new URL(location.href).searchParams.get('lang')||'en'],'Incorrect language');
 if(page==='home')check(document.querySelectorAll('.portal-record').length>0,'Homepage records absent');
 if(page==='archive'){
   const input=document.getElementById('archive-search');
   const initial=document.querySelectorAll('.portal-record').length;
   if(input.value==='NO_MATCH_9031')check(initial===0,'Zero-result URL filter failed');
   else {
     check(initial>0,'Archive records absent');
     const first=document.querySelector('.portal-record-title');
     if(first){
       const rid=new URL(first.href).searchParams.get('id');
       input.value=rid;input.dispatchEvent(new Event('input',{bubbles:true}));
       check(document.querySelectorAll('.portal-record').length===1,'Record ID filter failed');
       check(new URL(location.href).searchParams.get('q')===rid,'Query URL not synchronized');
       const picker=document.getElementById('language-select'),old=picker.value;
       picker.value=old==='de'?'zh':'de';picker.dispatchEvent(new Event('change',{bubbles:true}));
       check(input.value===rid,'Language switch lost filters');
       picker.value=old;picker.dispatchEvent(new Event('change',{bubbles:true}));
       const blobs=[],create=URL.createObjectURL,click=HTMLAnchorElement.prototype.click;
       URL.createObjectURL=b=>{blobs.push(b);return create(b);};
       HTMLAnchorElement.prototype.click=function(){if(!this.download)click.call(this);};
       document.getElementById('archive-export').click();
       document.getElementById('archive-metadata').click();
       check(blobs.length===2,'Export did not produce two files');
       if(blobs.length===2){const csv=await blobs[0].text(),metadata=JSON.parse(await blobs[1].text());
         check(csv.includes('record_id')&&csv.includes(rid),'CSV identifiers missing');
         check(metadata.matched_records===1&&metadata.filters.q===rid,'Query metadata inconsistent');}
       URL.createObjectURL=create;HTMLAnchorElement.prototype.click=click;
       input.value='';input.dispatchEvent(new Event('input',{bubbles:true}));
     }
   }
 }
 if(page==='sources'){
  check(document.querySelectorAll('#source-rows tr').length>1,'Source directory absent');
  check(document.querySelector('#source-feed-rows .is-ok'),'Successful collection feed status missing');
  check(document.querySelector('#source-feed-rows .is-retry'),'Retry status missing');
  check(document.querySelector('#source-feed-rows .is-review'),'Manual confirmation status missing');
  check(document.querySelector('#source-rows .is-ok'),'Successful reference status missing');
  check(document.querySelector('#source-rows .is-manual'),'Manual reference status missing');
  const media=[...document.querySelectorAll('#source-rows td small')].filter(n=>n.textContent.startsWith('media-'));
  const manualStatus={en:'Not checked automatically','zh-Hant':'未執行自動連線檢查',de:'Nicht automatisch geprüft'}[document.documentElement.lang];
  check(media.length===11&&media.every(n=>n.closest('tr').lastElementChild.textContent.includes(manualStatus)),
    'Approved manual media missing or mislabelled');
  const section=document.getElementById('academic-monitoring');
  const expectedTitle={en:'Academic literature monitoring','zh-Hant':'學術文獻觀察',de:'Beobachtung wissenschaftlicher Literatur'};
  check(section?.querySelector('h2')?.textContent===expectedTitle[document.documentElement.lang],'Academic monitoring section missing or untranslated');
  const hosts=id=>[...document.querySelectorAll('#'+id+' a')].map(a=>new URL(a.href).hostname).join(',');
  check(hosts('academic-automatic')==='www.crossref.org,help.openalex.org','Incorrect automated academic source list');
  check(hosts('academic-manual')==='scholar.google.com,www.litmaps.com,www.semanticscholar.org,www.webofscience.com','Incorrect external academic channel list');
  const archive=section?.querySelector('a[href*="kind=academic"]');
  check(archive&&new URL(archive.href).searchParams.get('kind')==='academic','Academic archive shortcut missing');
  const q=document.getElementById('source-search');q.value='NO_MATCH_9031';q.dispatchEvent(new Event('input',{bubbles:true}));
  check(document.getElementById('source-count').textContent.startsWith('0 /'),'Source filter failed');
  q.value='';q.dispatchEvent(new Event('input',{bubbles:true}));
 }
 if(page==='record')check(document.getElementById('record-content').textContent.includes(new URL(location.href).searchParams.get('id')||'UNEXPECTED'),'Stable record link failed');
 if(page==='workbench'){
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
 }
 if(page==='policy')check(document.body.textContent.includes('2027-12-14')&&document.body.textContent.includes('2029-07-26'),'Policy dates absent');
 check(document.documentElement.scrollWidth<=innerWidth+3,'Horizontal document overflow');
 const report={page,language:document.documentElement.lang,width:innerWidth,errors};
 const out=document.createElement('pre');out.id='portal-test-report';out.textContent=JSON.stringify(report);document.body.append(out);
})();
'''
def run():
 if not CHROME:raise SystemExit('FAIL: Chrome is required for migration acceptance; no browser detected')
 if not (ROOT/'_site/index.html').exists():raise SystemExit('Build _site first')
 qa=ROOT/'_qa';qa.mkdir(exist_ok=True)
 with tempfile.TemporaryDirectory() as tmp:
  root=Path(tmp);prefix='supply-chain-rights-observatory';site=root/prefix;shutil.copytree(ROOT/'_site',site)
  (site/'portal-test-probe.js').write_text(PROBE,encoding='utf-8')
  # Verify all three availability states on the isolated browser fixture.
  snapshot=site/'data/latest.json';fixture=json.loads(snapshot.read_text(encoding='utf-8'))
  for feed,failures in zip(fixture['sources'][:3], (0,1,3)):
   feed.update(status='failed' if failures else 'ok',consecutive_failures=failures)
  snapshot.write_text(json.dumps(fixture,ensure_ascii=False),encoding='utf-8')
  for p in site.rglob('*.html'):
   s=p.read_text(encoding='utf-8').replace('</body>',f'<script defer src="/{prefix}/portal-test-probe.js"></script></body>');p.write_text(s,encoding='utf-8')
  class Handler(SimpleHTTPRequestHandler):
   def log_message(self,*args):pass
  server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(root)));thread=Thread(target=server.serve_forever,daemon=True);thread.start()
  base=f'http://127.0.0.1:{server.server_port}/{prefix}/'
  rid=next(iter(json.loads((site/'data/record-index.json').read_text())['records']))
  paths=['','archive/','sources/','policy/','research/','methodology/','record.html?id='+rid,'workbench/']
  cases=[(p,lang,1440) for lang in ('en','zh','de') for p in paths]
  cases += [(p,'de',w) for w in (500,820,1600) for p in ('','archive/','sources/','workbench/')]
  cases += [('archive/?q=NO_MATCH_9031','en',1280)]
  cases += [('?lang=de#'+old,'de',1280) for old in ('archive-explorer','sources','lenses','method')]
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
    print('PASS' if not report['errors'] else 'FAIL',path,lang,width,report,flush=True)
    if report['errors']:raise AssertionError(report)
  finally:
   (qa/'portal-test-results.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf-8')
   server.shutdown();thread.join(timeout=3)
 print('PASS',len(reports),'generated-page browser cases. Not a formal WCAG or penetration-test certification.')
if __name__=='__main__':run()
