#!/usr/bin/env python3
"""Accept the generated review surface over real HTTP, without publishing test decisions."""
import functools,json,shutil,sys,tempfile,time
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from threading import Thread
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'));sys.path.insert(0,str(ROOT/'scripts'))
from test_workbench_row_height import ChromePipe,CHROME
from build_relevance import load_records
from relevance_engine import decorate,digest
from propose_reviews import prepare,parse_body
PROBE=r'''
(async()=>{
 const check=(x,m)=>{if(!x)throw Error(m);};
 const settle=async()=>{for(let i=0;i<4;i++)await new Promise(r=>requestAnimationFrame(r));};
 const rows=document.querySelectorAll('#wb-tbody [data-record-id]');check(rows.length,'No records');
 rows[0].click();await settle();
 check(document.getElementById('rv-decision'),'No integrated review form');
 const rid=rows[0].dataset.recordId;
 document.getElementById('rv-decision').value='include';document.getElementById('rv-note').value='Automated UI fixture, never submitted.';
 document.getElementById('rv-save').click();await settle();
 const draft=JSON.parse(localStorage.getItem('scro.review.drafts.v1'))[rid];
 check(draft.relevance==='include','Draft not saved');
 check(SCRO_RELEVANCE.get(rid).review_state==='unreviewed','Draft falsely published');
 let submitted='';const open=window.open;window.open=u=>{submitted=u;};
 document.querySelector('.rv-tools button:last-child').click();window.open=open;
 check(submitted.startsWith('https://github.com/e4e421/supply-chain-rights-observatory/issues/new?'),'Unsafe or absent handoff');
 const url=new URL(submitted);check(url.searchParams.get('body').startsWith('SCRO_REVIEW_V1'),'Missing batch');
 const filter=document.getElementById('rv-filter');filter.value='high';filter.dispatchEvent(new Event('change'));await settle();
 for(const row of document.querySelectorAll('#wb-tbody [data-record-id]'))check(SCRO_RELEVANCE.get(row.dataset.recordId).analysis.level==='high','Incorrect high filter');
 filter.value='all';filter.dispatchEvent(new Event('change'));await settle();
 const create=URL.createObjectURL,click=HTMLAnchorElement.prototype.click,blobs=[];
 URL.createObjectURL=b=>{blobs.push(b);return create(b);};HTMLAnchorElement.prototype.click=function(){if(!this.download)click.call(this);};
 document.getElementById('wb-export').click();URL.createObjectURL=create;HTMLAnchorElement.prototype.click=click;
 check(blobs.length===1,'CSV missing');const csv=await blobs[0].text();check(csv.includes('relevance_level')&&csv.includes('review_state'),'Review export fields missing');
 const wrap=document.querySelector('.wb-table-wrap');check(wrap.scrollHeight<=wrap.clientHeight+2,'Nested scroll restored');
 check(document.documentElement.scrollWidth<=innerWidth+3,'Page overflow');
 check(document.querySelectorAll('#wb-tbody [data-record-id]').length<=40,'Unbounded rows');
 return {rid,batch:url.searchParams.get('body'),language:document.documentElement.lang,width:innerWidth};
})()
'''
def run():
 if not CHROME:raise SystemExit('Chrome required for review acceptance')
 if not (ROOT/'_site/data/relevance-index.json').exists():raise ValueError('Build relevance index first')
 reports=[]
 with tempfile.TemporaryDirectory() as temporary:
  root=Path(temporary);site=root/'supply-chain-rights-observatory';shutil.copytree(ROOT/'_site',site)
  class Handler(SimpleHTTPRequestHandler):
   def log_message(self,*args):pass
  server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(root)));thread=Thread(target=server.serve_forever,daemon=True);thread.start()
  browser=ChromePipe(CHROME,root/'browser')
  def navigate(path,language='en',width=1600):
   browser.call('Emulation.setDeviceMetricsOverride',{'width':width,'height':1000,'deviceScaleFactor':1,'mobile':False})
   stamp=str(time.time_ns());url=f'http://127.0.0.1:{server.server_port}/supply-chain-rights-observatory/'+path
   url+=('&' if '?' in url else '?')+'lang='+language+'&qa='+stamp
   browser.call('Page.navigate',{'url':url})
   for _ in range(300):
    try:
     ready=browser.evaluate('document.readyState==="complete"&&new URL(location.href).searchParams.get("qa")==='+json.dumps(stamp)+'&&window.SCRO_RELEVANCE?.data!=null&&'+('document.querySelector("#wb-tbody [data-record-id]")!=null' if path.startswith('workbench') else 'window.__PORTAL_READY__===true'))
    except RuntimeError:ready=False
    if ready:return
    time.sleep(.03)
   raise AssertionError('Generated review page not ready: '+path)
  try:
   for language in ('en','zh','de'):
    for width in (1920,390):
     navigate('workbench/',language,width)
     result=browser.evaluate(PROBE);reports.append({'language':language,'width':width,'status':'passed'})
     # Validate the browser-generated payload using the same server-side parser and guards.
     payload=parse_body(result['batch']);overlay=json.loads((ROOT/'data/reviews/decisions.json').read_text())
     prepared=prepare(payload,load_records(),overlay,'reviewer',1,'b'*64,'2026-11-09T00:00:00Z')
     print('PASS integrated review',language,width,flush=True)
     browser.evaluate('localStorage.removeItem("scro.review.drafts.v1")')
   # Controlled manual exclusion in the temporary deployment only.
   rid=result['rid'];records=load_records();payload['decisions']=payload['decisions'][:1];payload['decisions'][0]['relevance']='exclude'
   prepared=prepare(payload,records,overlay,'reviewer',1,'b'*64,'2026-11-09T00:00:00Z')
   index=json.loads((site/'data/relevance-index.json').read_text());index['records'][rid]=decorate(records[rid],prepared['records']);(site/'data/relevance-index.json').write_text(json.dumps(index))
   for path in ('','archive/','workbench/'):
    navigate(path)
    if path=='workbench/':assert browser.evaluate('!document.querySelector(\'[data-record-id="'+rid+'"]\')')
    else:assert browser.evaluate('[...document.querySelectorAll(".portal-record-title")].every(a=>new URL(a.href).searchParams.get("id")!=='+json.dumps(rid)+')')
    print('PASS published exclusion consistency',path or 'home',flush=True)
   navigate('record.html?id='+rid)
   assert browser.evaluate('document.getElementById("record-content").textContent.includes("Excluded by editorial review")')
   print('PASS excluded original record remains accessible with warning',flush=True)
  finally:
   browser.close();server.shutdown();server.server_close();thread.join(timeout=3)
 qa=ROOT/'_qa';qa.mkdir(exist_ok=True);(qa/'review-acceptance.json').write_text(json.dumps(reports,indent=2))
 print('PASS review UI, draft/public distinction, handoff validation, and four-route overlay consistency')
if __name__=='__main__':run()
