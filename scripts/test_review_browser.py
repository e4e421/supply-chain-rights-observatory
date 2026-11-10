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
from propose_reviews import prepare
from publish_reviews import parse_publish_body as parse_body
PROBE=r'''
(async()=>{
 const check=(value,message)=>{if(!value)throw Error(message);};
 const settle=async()=>{for(let i=0;i<5;i++)await new Promise(r=>requestAnimationFrame(r));};
 check(document.body.dataset.page==='workbench-editor','Not the editor subpage');
 check(window.SCRO_REVIEW_STORE&&document.getElementById('review-panel'),'Review editor not mounted');
 const lang=document.documentElement.lang;
 const notice=document.querySelector('.wb-editor-notice'),back=document.getElementById('wb-return-to-reader');
 const editorCopy={en:['You are in the Review Editor','Return to the read-only view','Continue to GitHub to submit review'],
   'zh-Hant':['您正在使用審核編輯器','返回檢視頁','前往 GitHub 提交審核'],
   de:['Sie befinden sich im Review-Editor','Zurück zur Leseansicht','Weiter zu GitHub, um die Prüfung einzureichen']}[lang];
 check(notice?.nextElementSibling?.matches('.wb-header')&&notice.contains(back),'Editor notice missing or misplaced');
 check(notice.querySelector('strong').textContent===editorCopy[0]&&back.lastElementChild.textContent===editorCopy[1],'Editor notice not translated');
 check(!document.querySelector('.wb-header .wb-editor-link'),'Duplicate editor return link');
 check(back.getBoundingClientRect().height>=24&&getComputedStyle(back).textDecorationLine==='underline','Return link lacks size or visible affordance');
 check(document.activeElement===back&&getComputedStyle(back).outlineStyle==='solid','Return link lacks keyboard focus indication');
 check(document.querySelector('[data-scope=all]').getAttribute('aria-pressed')==='true','All searchable records not default');
 check(document.getElementById('wb-scope').value==='all','Underlying scope inconsistent');
 const hint=document.getElementById('wb-scope-hint').textContent.trim();
 check(hint.length>12,'Scope explanation missing');
 check(!/^(All searchable records|Recent snapshot|First-seen month)$/.test(hint),'Scope description is only a label');
 document.querySelector('[data-scope="latest"]').click();
 check(document.getElementById('wb-scope').value==='latest','Recent snapshot toggle failed');
 check(document.querySelector('#wb-scope-hint').textContent.includes('150') ||
   document.documentElement.lang!=='en','Recent snapshot meaning not visible');
 document.querySelector('[data-scope="archive"]').click();
 check(!document.getElementById('wb-month').closest('label').hidden,'First-seen month filter hidden');
 document.querySelector('[data-scope="all"]').click();
 check(document.getElementById('wb-month').closest('label').hidden,'Unnecessary month filter still visible');
 await settle();
 const rows=[...document.querySelectorAll('#wb-tbody [data-record-id]')];
 check(rows.length>=2,'Need two visible research records');
 const first=rows[0].dataset.recordId,second=rows[1].dataset.recordId;
 check(first!==second,'Repeated record IDs in current page');
 const store=SCRO_REVIEW_STORE;
 rows[0].click();await settle();
 check(document.getElementById('rv-decision'),'Selected record lacks editing controls');
 const before=JSON.stringify(SCRO_RELEVANCE.get(first).review);
 document.getElementById('rv-decision').value='include';
 document.getElementById('rv-note').value='Public acceptance fixture only.';
 document.getElementById('rv-save').click();await settle();
 check(store.getDraft(first)?.relevance==='include','First draft not stored');
 check(store.selectedIds().includes(first),'First saved draft not selected');
 check(JSON.stringify(SCRO_RELEVANCE.get(first).review)===before,'A local draft changed published data');
 window.dispatchEvent(new CustomEvent('scro:select-record',{detail:{record_id:second}}));
 await settle();
 document.getElementById('rv-decision').value='needs_review';
 document.getElementById('rv-note').value='Second public acceptance fixture.';
 document.getElementById('rv-save').click();await settle();
 const queue=document.getElementById('rv-queue');
 check(queue.querySelectorAll('[data-review-id]').length===2,'Both drafts not visible');
 check(store.selectedIds().length===1&&store.selectedIds()[0]===second,
   'Saving second draft accidentally retained first selection');
 check(queue.querySelector('[data-review-id="'+first+'"] .rv-change'),'First draft changes not previewed');
 const send=document.getElementById('rv-publish-batch');
 const submitHint=document.getElementById(send.getAttribute('aria-describedby'));
 check(send.textContent===editorCopy[2]&&submitHint?.textContent.includes('GitHub')&&submitHint.getBoundingClientRect().height>0,
   'Submission wording or visible description missing');
 let submitted=[];const oldOpen=window.open;window.open=u=>{submitted.push(u);};
 send.click();await settle();
 check(submitted.length===1,'GitHub handoff not opened once');
 check(store.batches().length===1&&store.batches()[0].status==='handoff',
   'Handoff incorrectly labelled published');
 check(store.selectedEntries().length===0,'Submitted draft stayed selected');
 check(document.getElementById('rv-publish-batch').disabled,'Accidental re-submit possible');
 check(store.getDraft(first)&&store.getDraft(second),'Handoff erased one of the drafts');
 const u1=new URL(submitted[0]);
 check(u1.searchParams.get('title')==='[Publish Workbench review]','Wrong Issue title');
 const fence=String.fromCharCode(96).repeat(3);
 const body1=u1.searchParams.get('body');
 check(body1.startsWith('SCRO_PUBLISH_V2'),'Wrong API envelope');
 const payload1=JSON.parse(body1.split(fence+'json\n')[1].split('\n'+fence)[0]);
 check(payload1.decisions.length===1&&payload1.decisions[0].record_id===second,
   'First handoff included the previously saved, unselected first draft');
 check(!('_savedAt' in payload1.decisions[0])&&!('_title' in payload1.decisions[0]),
   'Private local display fields leaked');
 const firstCheck=queue.querySelector('[data-select-record="'+first+'"]');
 firstCheck.click();await settle();
 check(store.selectedIds().length===1&&store.selectedIds()[0]===first,'Cannot select remaining draft');
 document.getElementById('rv-publish-batch').click();await settle();
 check(submitted.length===2,'Second handoff missing');
 const body2=new URL(submitted[1]).searchParams.get('body');
 const payload2=JSON.parse(body2.split(fence+'json\n')[1].split('\n'+fence)[0]);
 check(payload2.decisions.length===1&&payload2.decisions[0].record_id===first,
   'Second handoff repeated previously submitted record');
 check(store.batches().length===2,'Two handoffs not tracked');
 check(!store.getDraft(first)===false,'Draft unexpectedly removed');
 window.open=oldOpen;
 const wrap=document.querySelector('.wb-table-wrap');
 check(wrap.scrollHeight<=wrap.clientHeight+2,'Nested vertical scroll reintroduced');
 check(document.documentElement.scrollWidth<=innerWidth+3,'Horizontal viewport overflow');
 const search=document.getElementById('wb-search');search.value=second;
 search.dispatchEvent(new Event('input',{bubbles:true}));
 const reader=new URL(back.href),here=new URL(location.href);
 check(reader.pathname===new URL('../',here).pathname,'Return link did not target read-only Workbench');
 check(reader.searchParams.get('lang')===({en:'en','zh-Hant':'zh',de:'de'})[lang]&&
   reader.searchParams.get('q')===second&&reader.searchParams.get('record')===second&&
   reader.searchParams.get('scope')==='all','Return link lost research context');
 check(!reader.searchParams.has('qa')&&!reader.searchParams.has('relevance'),'Editor-only query parameters leaked');
 return {first,second,batchOne:body1,batchTwo:body2,readerPath:'workbench/'+reader.search};
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
   url+=('&' if '?' in url else '?')+'qa='+stamp
   if 'lang=' not in url:url+='&lang='+language
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
     self_readonly=browser.evaluate('document.querySelector("#review-panel")===null&&document.getElementById("rv-publish-batch")===null&&document.querySelector("[data-scope=all]").getAttribute("aria-pressed")==="true"')
     if not self_readonly:raise AssertionError('Public Workbench exposes editing controls or wrong default scope')
     assert browser.evaluate('!document.querySelector(".wb-editor-notice")&&!!document.querySelector(".wb-editor-link")')
     navigate('workbench/edit/',language,width)
     for _ in range(2):
      browser.call('Input.dispatchKeyEvent',{'type':'rawKeyDown','key':'Tab','code':'Tab','windowsVirtualKeyCode':9})
      browser.call('Input.dispatchKeyEvent',{'type':'keyUp','key':'Tab','code':'Tab','windowsVirtualKeyCode':9})
     result=browser.evaluate(PROBE);reports.append({'language':language,'width':width,'status':'passed'})
     # Validate the browser-generated payload using the same server-side parser and guards.
     overlay=json.loads((ROOT/'data/reviews/decisions.json').read_text())
     for body in (result['batchOne'],result['batchTwo']):
      payload=parse_body(body)
      overlay=prepare(payload,load_records(),overlay,'reviewer',1,'b'*64,'2026-11-09T00:00:00Z')
     navigate(result['readerPath'],language,width)
     assert browser.evaluate('document.getElementById("wb-search").value==='+json.dumps(result['second'])+
       '&&document.querySelector("#wb-tbody .is-selected")?.dataset.recordId==='+json.dumps(result['second']))
     print('PASS editor notice, contextual return and selected review submissions',language,width,flush=True)
     browser.evaluate('localStorage.removeItem("scro.review.drafts.v1");localStorage.removeItem("scro.review.queue.v2")')
   # Controlled manual exclusion in the temporary deployment only.
   rid=result['first'];records=load_records()
   payload=parse_body(result['batchTwo']);payload['decisions'][0]['relevance']='exclude'
   empty=json.loads((ROOT/'data/reviews/decisions.json').read_text())
   prepared=prepare(payload,records,empty,'reviewer',1,'b'*64,'2026-11-09T00:00:00Z')
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
