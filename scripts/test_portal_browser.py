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
  const q=document.getElementById('source-search');q.value='NO_MATCH_9031';q.dispatchEvent(new Event('input',{bubbles:true}));
  check(document.getElementById('source-count').textContent.startsWith('0 /'),'Source filter failed');
  q.value='';q.dispatchEvent(new Event('input',{bubbles:true}));
 }
 if(page==='record')check(document.getElementById('record-content').textContent.includes(new URL(location.href).searchParams.get('id')||'UNEXPECTED'),'Stable record link failed');
 if(page==='workbench'){
  check(document.querySelectorAll('[data-record-id]').length>0,'Workbench records absent');
  const rail=document.querySelector('.wb-filters').getBoundingClientRect();
  for(const id of ['wb-from','wb-to']){const r=document.getElementById(id).getBoundingClientRect();check(r.left>=rail.left-2&&r.right<=rail.right+2,'Date control overflow');}
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
