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
from relevance_engine import decorate,digest,fingerprint
from propose_reviews import prepare
from publish_reviews import parse_publish_body as parse_body
COLLECTION_CLOCK_PROBE=r'''
(()=>{
 const relative=document.getElementById('wb-updated');
 const absolute=document.getElementById('wb-updated-utc');
 const language=document.documentElement.lang;
 const format=new Intl.RelativeTimeFormat(language,{numeric:'always',style:'long'});
 const collection=Date.parse('2026-11-11T17:57:00Z');
 if(relative?.textContent!==format.format(-7,'hour')||absolute?.tagName!=='TIME'||absolute.hidden||
    absolute.textContent!=='11 November 2026, 17:57 UTC'||!absolute.dateTime.endsWith('Z')||
    Date.parse(absolute.dateTime)!==collection)return false;
 const justNow={en:'Just now','zh-Hant':'剛剛',de:'Gerade eben',es:'Ahora mismo'}[language];
 const now=Date.now;
 try{
  for(const [minutes,expected] of [
   [0.5,justNow],[59,format.format(-59,'minute')],[60,format.format(-1,'hour')],
   [47*60,format.format(-47,'hour')],[48*60,format.format(-2,'day')]
  ]){
   Date.now=()=>collection+minutes*60_000;
   document.dispatchEvent(new Event('visibilitychange'));
   if(relative.textContent!==expected||absolute.textContent!=='11 November 2026, 17:57 UTC')return false;
  }
 }finally{
  Date.now=now;
  document.dispatchEvent(new Event('visibilitychange'));
 }
 return true;
})()
'''
PROBE=r'''
(async()=>{
 const check=(value,message)=>{if(!value)throw Error(message);};
 const settle=async()=>{for(let i=0;i<5;i++)await new Promise(r=>requestAnimationFrame(r));};
 check(document.body.dataset.page==='workbench-editor','Not the editor subpage');
 check(window.SCRO_REVIEW_STORE&&document.getElementById('review-panel'),'Review editor not mounted');
 const lang=document.documentElement.lang;
 const header=getComputedStyle(document.querySelector('.wb-header'));
 check(header.backgroundColor==='rgb(34, 60, 104)'&&header.borderBottomColor==='rgb(143, 184, 230)',
   'Editor header is missing its mode-specific colors');
 const notice=document.querySelector('.wb-editor-notice'),back=document.getElementById('wb-return-to-reader');
 const editorCopy={en:['You are in the Review Editor','Return to the read-only view','Continue to GitHub to submit review'],
   'zh-Hant':['您正在使用審核編輯器','返回檢視頁','前往 GitHub 提交審核'],
   de:['Sie befinden sich im Review-Editor','Zurück zur Leseansicht','Weiter zu GitHub, um die Prüfung einzureichen'],
   es:['Está en el editor de revisión','Volver a la vista de solo lectura','Continuar en GitHub para enviar la revisión']}[lang];
 check(notice?.nextElementSibling?.matches('.wb-header')&&notice.contains(back),'Editor notice missing or misplaced');
 check(notice.querySelector('strong').textContent===editorCopy[0]&&back.lastElementChild.textContent===editorCopy[1],'Editor notice not translated');
 check(!document.querySelector('.wb-editor-link, .wb-footer'),'Editor exposes its own entry link');
 check(back.getBoundingClientRect().height>=24&&getComputedStyle(back).textDecorationLine==='underline','Return link lacks size or visible affordance');
 check(document.activeElement===back&&getComputedStyle(back).outlineStyle==='solid','Return link lacks keyboard focus indication');
 check(!document.querySelector('[data-scope], #wb-scope, #wb-month, #wb-latest-count, #wb-archive-count'),
   'Removed scope controls or counters are still present');
 const total=document.getElementById('wb-searchable-count');
 const totalLabel={en:'Searchable records','zh-Hant':'可搜尋紀錄總數',
   de:'Durchsuchbare Datensätze insgesamt',es:'Total de registros consultables'}[lang];
 check(total.previousElementSibling.textContent===totalLabel&&
   Number(total.textContent.replace(/\D/g,''))===Number(document.getElementById('wb-count').dataset.total),
   'Default searchable total is inconsistent or untranslated');
 check(document.getElementById('wb-legacy-month').hidden&&!document.getElementById('wb-coverage').textContent,
   'The default search still shows a scope or coverage message');
 await settle();
 const rows=[...document.querySelectorAll('#wb-tbody [data-record-id]')];
 check(rows.length===10,'Editor does not show ten records per page');
 const first=rows[0].dataset.recordId,second=rows[1].dataset.recordId;
 check(first!==second,'Repeated record IDs in current page');
 const store=SCRO_REVIEW_STORE;
 rows[0].click();await settle();
 check(document.getElementById('rv-decision'),'Selected record lacks editing controls');
 if(lang==='es'){
  check(document.querySelector('#wb-prev').textContent==='Página anterior','Spanish pagination label missing');
  check(document.querySelector('#review-panel').getAttribute('aria-label')==='Pertinencia y revisión','Spanish editor landmark label missing');
  check(document.querySelector('#rv-save').textContent==='Guardar borrador local','Spanish draft action missing');
  check(document.querySelector('input[name="rv-topic"][value="forced-labour"]').closest('label').textContent==='Trabajo forzoso',
    'Spanish review topic missing');
 }
 const before=JSON.stringify(SCRO_RELEVANCE.get(first).review);
 const tagInput=document.getElementById('rv-tag-input');
 const typeTag=value=>{
  tagInput.value=value;tagInput.dispatchEvent(new Event('input',{bubbles:true}));
  tagInput.dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowDown',bubbles:true,cancelable:true}));
  tagInput.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true,cancelable:true}));
 };
 typeTag('#iPhone');typeTag('工廠事故');
 document.getElementById('rv-note').value='unsaved editorial note';
 document.getElementById('rv-save-tags').click();
 check(document.getElementById('rv-note').value==='unsaved editorial note','Tag save cleared unsaved review fields');
 const tagBatch=store.payload(store.selectedEntries());
 check(tagBatch.decisions.length===0&&tagBatch.tag_changes?.length===1,'Tag-only save included a review');
 check(JSON.stringify(tagBatch.tag_changes[0].tags)===JSON.stringify(['iphone','工廠事故']),'Tags were not canonical or multilingual');
 check(JSON.stringify(SCRO_RELEVANCE.get(first).review)===before&&SCRO_RELEVANCE.tags(first).length===0,'Local tag draft changed public data');
 window.dispatchEvent(new CustomEvent('scro:select-record',{detail:{record_id:second}}));
 document.getElementById('rv-tag-input').focus();
 check([...document.querySelectorAll('#rv-tag-options [role=option]')].some(option=>option.textContent.includes('#iphone')),
   'Saved tags are not reusable on another record');
 store.removeDraft(first);
 window.dispatchEvent(new CustomEvent('scro:select-record',{detail:{record_id:first}}));
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
 const wrap=document.querySelector('.wb-table-wrap'),pager=document.getElementById('wb-page-controls');
 const shortcuts=document.querySelector('.wb-pagination'),historyPanel=document.getElementById('rv-history');
 const filter=document.getElementById('rv-filter');
 const beforeElement=(a,b)=>Boolean(a.compareDocumentPosition(b)&Node.DOCUMENT_POSITION_FOLLOWING);
 const top=element=>element.getBoundingClientRect().top+scrollY;
 const bottom=element=>element.getBoundingClientRect().bottom+scrollY;
 const visibleRows=()=>[...document.querySelectorAll('#wb-tbody [data-record-id]')];
 const visibleIds=()=>visibleRows().map(row=>row.dataset.recordId).join(',');
 queue.open=false;
 await settle();
 const initialTop=top(wrap),initialPagerTop=top(pager),initialIds=visibleIds();
 queue.open=true;
 await settle();
 check(beforeElement(filter,pager)&&wrap.previousElementSibling.contains(pager),
   'Filter and pager must precede the results table');
 check(beforeElement(wrap,queue)&&beforeElement(queue,historyPanel)&&
   bottom(wrap)<=top(shortcuts)+1&&bottom(shortcuts)<=top(queue)+1&&bottom(queue)<=top(historyPanel)+1,
   'Review queue and publication history must follow the results and shortcuts');
 check(Math.abs(top(wrap)-initialTop)<=1&&Math.abs(top(pager)-initialPagerTop)<=1,
   'Expanding the queue moved the results or the pager');
 check(visibleRows().length===10&&visibleIds()===initialIds,'Expanding the queue changed the results');
 const next=document.getElementById('wb-next'),previous=document.getElementById('wb-prev');
 check(previous.disabled&&!next.disabled,'First page navigation state is incorrect');
 next.click();await settle();
 check(visibleRows().length===10&&visibleRows().every(row=>!rows.some(initial=>initial.dataset.recordId===row.dataset.recordId)),
   'Next page did not show the next ten records');
 previous.click();await settle();
 check(visibleRows()[0]?.dataset.recordId===first,'Previous page did not restore the first results');
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
 check(wrap.scrollHeight<=wrap.clientHeight+2,'Nested vertical scroll reintroduced');
 check(document.documentElement.scrollWidth<=innerWidth+3,'Horizontal viewport overflow');
 const search=document.getElementById('wb-search');search.value=second;
 search.dispatchEvent(new Event('input',{bubbles:true}));
 const reader=new URL(back.href),here=new URL(location.href);
 check(reader.pathname===new URL('../',here).pathname,'Return link did not target read-only Workbench');
 check(reader.searchParams.get('lang')===({en:'en','zh-Hant':'zh',de:'de',es:'es'})[lang]&&
   reader.searchParams.get('q')===second&&reader.searchParams.get('record')===second&&
   !reader.searchParams.has('scope'),'Return link lost research context');
 check(!reader.searchParams.has('qa')&&!reader.searchParams.has('relevance'),'Editor-only query parameters leaked');
 if(lang==='es'){
  const picker=document.getElementById('language-select');
  const choose=value=>{picker.value=value;picker.dispatchEvent(new Event('change',{bubbles:true}));};
  choose('en');choose('es');
  check(document.documentElement.lang==='es'&&localStorage.getItem('scro.language')==='es'&&search.value===second,
    'Spanish language selection was not stored or lost the search');
  let copied='';
  Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async url=>{copied=url;}}});
  const clean=new URL(location.href);clean.searchParams.delete('lang');history.replaceState(null,'',clean.href);
  document.getElementById('wb-share').click();await settle();
  const shared=new URL(copied);
  check(shared.searchParams.get('lang')==='es'&&shared.searchParams.get('q')===second,'Shared link lost Spanish or the search');
 }
 return {first,second,tagBatch,batchOne:body1,batchTwo:body2,readerPath:'workbench/'+reader.search};
})()
'''
FILTER_PROBE=r'''
(async()=>{
 const byId=id=>document.getElementById(id);
 const filter=byId('rv-filter'),active=byId('wb-active-filters');
 const labels={
  en:['All relevance levels','High relevance','Needs context','Low relevance','No current review','Published reviews · included records','Excluded records'],
  'zh-Hant':['所有相關性','高相關','待判讀','低相關','無有效審核','已發布審核 · 收錄紀錄','已排除紀錄'],
  de:['Alle Relevanzstufen','Hohe Relevanz','Kontext prüfen','Geringe Relevanz','Keine aktuelle Prüfung','Veröffentlichte Prüfungen · aufgenommene Datensätze','Ausgeschlossene Datensätze'],
  es:['Todos los niveles de pertinencia','Pertinencia alta','Requiere contexto','Pertinencia baja','Sin revisión vigente','Revisiones publicadas · registros incluidos','Registros excluidos']
 };
 const expected={
  all:[1,2,3,4,5,7,8],high:[1,2],review:[3,4],low:[5,8],
  unreviewed:[1,3,5],reviewed:[2,4,8],excluded:[6]
 };
 const check=(value,message)=>{
  if(!value)throw Error(document.documentElement.lang+' '+innerWidth+'px · '+message);
 };
 const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
 const dispatch=(element,event='change')=>element.dispatchEvent(new Event(event,{bubbles:true}));
 const change=(id,value,event)=>{const element=byId(id);element.value=value;dispatch(element,event);};
 const query=key=>new URL(location.href).searchParams.get(key);
 const assertResults=(label,ids)=>{
  const rows=[...document.querySelectorAll('#wb-tbody [data-record-id]')];
  const actual=rows.map(row=>parseInt(row.dataset.recordId,16)).sort((a,b)=>a-b);
  check(same(actual,ids)&&byId('wb-count').dataset.total===String(ids.length),
   label+' expected '+ids+' but showed '+actual+' ('+byId('wb-count').dataset.total+' total)');
  check(byId('wb-searchable-count').textContent==='7','Filter changed the deduplicated header total');
 };
 const waitForResults=async(label,ids)=>{
  for(let i=0;i<90&&byId('wb-count').dataset.total!==String(ids.length);i++)
   await new Promise(resolve=>requestAnimationFrame(resolve));
  assertResults(label,ids);
 };
 const assertOptions=()=>{
  check(!filter.disabled&&same([...filter.options].map(option=>option.value),Object.keys(expected)),
   'Relevance options unavailable or changed across languages');
  check(same([...filter.options].map(option=>option.textContent),labels[document.documentElement.lang]),
   'Relevance options are not translated');
 };
 assertOptions();
 check(filter.value==='high'&&query('relevance')==='high','Initial editor URL did not restore relevance');
 assertResults('Initial editor URL',expected.high);
 for(const [value,ids] of Object.entries(expected)){
  change('rv-filter',value);
  assertResults(value,ids);
  check(query('relevance')===(value==='all'?null:value),'Editor URL lost relevance '+value);
  if(value!=='all')check(active.textContent===filter.selectedOptions[0].textContent,'Relevance missing from active filters');
 }
 change('wb-search','#smoke fire','input');
 assertResults('Hashtag and search with excluded',expected.excluded);
 change('rv-filter','high');
 assertResults('Hashtag and search with high',expected.high);
 change('wb-kind','academic');
 assertResults('High, search, tag and type',[2]);
 change('wb-evidence','unverified');
 assertResults('Evidence excludes academic record',[]);
 change('wb-evidence','bibliographic');
 assertResults('Evidence includes academic record',[2]);
 change('wb-to','2026-11-10');
 assertResults('UTC day before publication',[]);
 change('wb-to','2026-11-11');
 change('wb-from','2026-11-11');
 assertResults('UTC publication date',[2]);
 const topic=document.querySelector('[name="wb-topic"][value="forced-labour"]');
 topic.checked=true;dispatch(topic);
 assertResults('Topic excludes policy record',[]);
 topic.checked=false;dispatch(topic);
 const locale=byId('language-select').value;
 change('language-select',locale==='es'?'en':'es');
 assertOptions();
 change('language-select',locale);
 assertOptions();
 assertResults('Language switch keeps filters',[2]);
 check(filter.value==='high'&&query('relevance')==='high'&&query('q')==='#smoke fire'&&
   active.textContent.includes(filter.selectedOptions[0].textContent),'Language switch lost filter state or summary');
 let copied='';
 Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async value=>{copied=value;}}});
 byId('wb-share').click();
 await Promise.resolve();
 const shared=new URL(copied),reader=new URL(byId('wb-return-to-reader').href);
 check(shared.searchParams.get('lang')===locale&&shared.searchParams.get('relevance')==='high'&&
   shared.searchParams.get('q')==='#smoke fire','Share link lost locale or filters');
 check(!reader.searchParams.has('relevance')&&reader.searchParams.get('q')==='#smoke fire',
   'Read-only return did not preserve compatible filters');
 const prompt=window.prompt;
 window.prompt=()=> 'Browser acceptance view';
 byId('wb-save').click();
 window.prompt=prompt;
 const saved=byId('wb-saved-list').value;
 check(saved,'Save view did not create an entry');
 byId('wb-clear').click();
 await waitForResults('Reset',expected.all);
 check(filter.value==='all'&&!query('relevance')&&!query('q'),'Reset left an active filter');
 change('wb-saved-list',saved);
 await waitForResults('Restore saved view',[2]);
 check(filter.value==='high'&&query('relevance')==='high','Saved view lost relevance');
 byId('wb-remove-view').click();
 byId('wb-clear').click();
 await waitForResults('Reset before sorting',expected.all);
 change('rv-filter','low');
 assertResults('Low across snapshot and archive',expected.low);
 change('rv-filter','all');
 change('wb-sort','observed-desc');
 assertResults('First-observation sort',expected.all);
 check(document.querySelector('#wb-tbody [data-record-id]').dataset.recordId==='000000000000000001',
   'First-observation sort used publication dates');
 return true;
})()
'''
STALE_QUEUE_PROBE=r'''
(()=>{
 const check=(value,message)=>{if(!value)throw Error(document.documentElement.lang+' · '+message);};
 const store=SCRO_REVIEW_STORE,index=SCRO_RELEVANCE;
 const id=n=>n.toString(16).padStart(18,'0');
 const [staleReview,staleTags,current,locked,unindexed]=[1,2,3,4,7].map(id);
 const queue=document.getElementById('rv-queue');
 const stale=()=>document.getElementById('rv-stale-drafts');
 const button=()=>document.getElementById('rv-clear-stale');
 const visible=()=>Boolean(button()?.getClientRects().length);
 const ids=container=>[...container.querySelectorAll('[data-review-id]')].map(row=>row.dataset.reviewId).sort();
 const main=()=>document.getElementById('rv-queue-list');
 const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
 const saveReview=rid=>{
  const record=index.get(rid);
  return store.saveDraft(rid,{
   content_fingerprint:record?.analysis.content_fingerprint||'0'.repeat(64),
   expected_review_digest:record?.review_digest||'0'.repeat(64),
   relevance:'needs_review',topics:null,publisher_confirmed:false,canonical_url:null,note:''
  });
 };
 queue.open=true;
 check(!visible(),'Bulk removal was visible without outdated drafts');
 check(saveReview(locked),'Handoff fixture could not be saved');
 const batch=store.makeHandoff((rid,d)=>rid===locked&&d.expected_review_digest===index.get(rid).review_digest);
 check(saveReview(staleReview)&&saveReview(unindexed)&&saveReview(current),'Review fixtures could not be saved');
 const tag=index.data.record_tags[staleTags];
 check(store.saveTags(staleTags,{
  content_fingerprint:index.get(staleTags).analysis.content_fingerprint,
  expected_tag_digest:tag.digest,tags:['new-tag']
 },'Fixture tag draft'),'Tag fixture could not be saved');
 store.setSelected(staleReview,true);
 index.get(staleReview).review_digest='1'.repeat(64);
 index.get(locked).review_digest='1'.repeat(64);
 tag.digest='1'.repeat(64);
 store.setSelected(current,true);
 check(same(ids(main()),[current,locked,unindexed])&&queue.querySelector('summary').textContent.endsWith('(3)'),
  'Outdated drafts remained in the main queue count');
 check(stale()&&!stale().hidden&&!stale().open,'The outdated section was not collapsed by default');
 check(same(ids(stale()),[staleReview,staleTags]),'The outdated section contains the wrong drafts');
 check(!visible(),'The bulk removal button occupies space while the section is collapsed');
 document.getElementById('rv-stale-title').click();
 check(stale().open&&visible()&&!button().disabled,'Bulk removal was unavailable in the outdated section');
 const originalConfirm=window.confirm;
 const prompts=[];
 try{
  window.confirm=message=>{prompts.push(message);return false;};
  button().click();
  check(prompts.length===1&&same(ids(stale()),[staleReview,staleTags]),
   'Cancelling bulk removal changed the queue');
  window.confirm=message=>{prompts.push(message);return true;};
  button().focus();button().click();
  check(prompts.length===2&&!store.getDraft(staleReview)&&!store.getDraft(staleTags)&&
   same(ids(main()),[current,locked,unindexed]),'Bulk removal changed the wrong drafts');
  check(same(store.selectedIds(),[current])&&store.active(locked)?.id===batch.id,
   'Current selection or active handoff was lost');
  check(index.tags(staleTags).includes('smoke'),'Bulk removal changed a published tag');
  check(!visible()&&queue.querySelector('summary').textContent.endsWith('(3)'),
   'Bulk removal visibility or queue count did not update');
  check(document.activeElement===queue.querySelector('summary'),'Bulk removal did not restore focus to the queue');
 }finally{window.confirm=originalConfirm;}
 return true;
})()
'''
PUBLICATION_STATUS_PROBE=r'''
(async()=>{
 const check=(value,message)=>{if(!value)throw Error(message);};
 const store=SCRO_REVIEW_STORE,rid='000000000000000004',record=SCRO_RELEVANCE.get(rid);
 check(store.saveDraft(rid,{...store.publicationFields(record.review),
  expected_review_digest:record.review_digest,note:'Pending fixture draft'}),'Draft setup failed');
 const batch=store.makeHandoff(()=>true);
 const draftBefore=JSON.stringify(store.getDraft(rid));
 const batchBefore=JSON.stringify(store.active(rid));
 const status=document.getElementById('rv-check-status'),feedback=document.getElementById('rv-feedback');
 const issues=document.getElementById('rv-github-issues');
 const originalFetch=window.fetch;
 let apiCalls=0,indexCalls=0,indexUnavailable=false;
 window.fetch=(input,...args)=>{
  const url=new URL(input instanceof Request?input.url:input,location.href);
  if(url.origin==='https://api.github.com'){
   apiCalls++;
   return Promise.resolve(indexUnavailable?new Response('[]'):new Response(null,{status:403}));
  }
  if(url.origin===location.origin&&url.pathname.endsWith('/data/relevance-index.json')){
   indexCalls++;
   if(indexUnavailable)return Promise.resolve(new Response(null,{status:503}));
  }
  return originalFetch(input,...args);
 };
 const refresh=async()=>{
  status.click();
  check(status.disabled,'Status check did not show a pending state');
  for(let i=0;i<200&&status.disabled;i++)await new Promise(resolve=>setTimeout(resolve,25));
  check(!status.disabled,'Status button did not become available again');
  check(JSON.stringify(store.getDraft(rid))===draftBefore&&JSON.stringify(store.active(rid))===batchBefore&&
   store.active(rid).id===batch.id,'A status lookup changed the pending handoff or draft');
 };
 try{
  await refresh();
  check(apiCalls===1&&indexCalls===1,'Publication status did not refresh both sources');
  check(feedback.textContent==='Published review status refreshed. Pending submissions could not be checked on GitHub.',
   'Partial status was not reported after GitHub returned 403');
  check(issues&&!issues.hidden&&issues.getClientRects().length&&
   new URL(issues.href).pathname==='/e4e421/supply-chain-rights-observatory/issues',
   'Direct Issues link was unavailable after GitHub returned 403');
  indexUnavailable=true;
  await refresh();
  check(apiCalls===2&&indexCalls===2&&issues.hidden&&
   feedback.textContent==='Published review data could not be loaded. Try again.',
   'The review-data error did not stay distinct from a GitHub error');
 }finally{window.fetch=originalFetch;}
 return true;
})()
'''


def install_filter_fixture(site):
    """Replace only the browser test's temporary snapshot, shard and review index."""
    data = site/'data'
    scenarios = (
        ('fire alpha', 'discovery', 'high', 'unreviewed', 'forced-labour', True),
        ('fire beta', 'academic', 'high', 'current', 'policy', True),
        ('fire gamma', 'discovery', 'review', 'stale', 'forced-labour', False),
        ('flood delta', 'discovery', 'review', 'current', 'working-conditions', True),
        ('flood epsilon', 'academic', 'low', 'unreviewed', 'research', False),
        ('fire zeta', 'discovery', 'high', 'excluded', 'forced-labour', True),
        ('unknown eta', 'discovery', None, 'unindexed', 'policy', False),
        ('flood theta', 'discovery', 'low', 'current', 'working-conditions', False),
    )
    records, sidecar, tags = [], {}, {}
    for n, (title, kind, level, state, topic, tagged) in enumerate(scenarios, 1):
        record_id = f'{n:018x}'
        record = {
            'record_id': record_id, 'title': 'Fixture '+title, 'kind': kind,
            'publisher_hint': 'Fixture Publisher', 'topics': [topic],
            'source_id': 'filter-fixture', 'url': f'https://example.org/{record_id}',
            'first_seen': {1:'2026-11-12T03:00:00Z', 8:'2026-10-31T01:00:00Z'}.get(n, '2026-11-11T01:00:00Z'),
            'published_at': {1:'2026-11-10T23:59:00Z', 8:'2026-09-29T00:00:00Z'}.get(n, '2026-11-11T00:00:00Z'),
            'evidence_status': 'Bibliographic record' if kind == 'academic' else 'Unverified discovery lead',
        }
        records.append(record)
        if tagged:
            row = {'tags': ['smoke'], 'issue': 1}
            tags[record_id] = {**row, 'digest': digest(row)}
        if state == 'unindexed':
            continue
        reviews = {}
        if state in {'current', 'stale', 'excluded'}:
            reviews[record_id] = {
                'content_fingerprint': '0'*64 if state == 'stale' else fingerprint(record),
                'relevance': 'exclude' if state in {'stale', 'excluded'} else 'needs_review' if n == 4 else 'include',
                'topics': [topic], 'publisher_confirmed': False, 'canonical_url': None,
                'note': '', 'reviewed_at': '2026-11-11T01:00:00Z', 'reviewed_by': 'fixture',
                'issue': 1, 'issue_digest': 'a'*64,
            }
        entry = decorate(record, reviews)
        entry['analysis']['level'] = level
        entry['effective_topics'] = [topic]
        sidecar[record_id] = entry

    def replace(name, **fields):
        path = data/name
        document = json.loads(path.read_text())
        document.update(fields)
        path.write_text(json.dumps(document))

    replace('latest.json', items=records[:-1], last_successful_collection='2026-11-11T17:57:00Z')
    months = []
    for month, row in (('2026-11', records[0]), ('2026-10', records[-1])):
        shard = month+'-0001.json'
        months.append({'month': month, 'records': 1, 'files': [{'file': shard, 'records': 1}]})
        (data/'archive'/shard).write_text(json.dumps({'records': [row]}))
    replace('archive/catalog.json', total_records=2, months=months)
    replace('relevance-index.json', records=sidecar, coverage='partial', tag_catalog=['smoke'], record_tags=tags)


def run():
 if not CHROME:raise SystemExit('Chrome required for review acceptance')
 if not (ROOT/'_site/data/relevance-index.json').exists():raise ValueError('Build relevance index first')
 reports=[]
 with tempfile.TemporaryDirectory() as temporary:
  root=Path(temporary);site=root/'supply-chain-rights-observatory';shutil.copytree(ROOT/'_site',site)
  index_path=site/'data/relevance-index.json'
  initial_index=json.loads(index_path.read_text())
  initial_index.update(tag_catalog=[],record_tags={})
  index_path.write_text(json.dumps(initial_index))
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
   for language in ('en','zh','de','es'):
    for width in (1920,390):
     navigate('workbench/',language,width)
     self_readonly=browser.evaluate('!document.querySelector("#review-panel, #rv-publish-batch, #rv-clear-stale, [data-scope]")&&Boolean(Number(document.getElementById("wb-searchable-count").textContent.replace(/\\D/g,"")))')
     if not self_readonly:raise AssertionError('Public Workbench editing separation or total failed')
     assert browser.evaluate('!document.querySelector(".wb-editor-notice, .wb-header .wb-editor-link")')
     assert browser.evaluate('getComputedStyle(document.querySelector(".wb-header")).backgroundColor==="rgb(16, 44, 42)"')
     editor_href=browser.evaluate('document.querySelector("footer.wb-footer .wb-editor-link")?.href')
     editor_url=f'http://127.0.0.1:{server.server_port}/supply-chain-rights-observatory/workbench/edit/'
     assert editor_href==editor_url+'?lang='+language, 'Footer link lost the editor route or current language'
     navigate(editor_href.split('/supply-chain-rights-observatory/',1)[1],language,width)
     for _ in range(2):
      browser.call('Input.dispatchKeyEvent',{'type':'rawKeyDown','key':'Tab','code':'Tab','windowsVirtualKeyCode':9})
      browser.call('Input.dispatchKeyEvent',{'type':'keyUp','key':'Tab','code':'Tab','windowsVirtualKeyCode':9})
     result=browser.evaluate(PROBE);reports.append({'language':language,'width':width,'status':'passed'})
     # Validate the browser-generated payload using the same server-side parser and guards.
     overlay=json.loads((ROOT/'data/reviews/decisions.json').read_text())
     tagged=prepare(result['tagBatch'],load_records(),{'schema_version':1,'records':overlay['records']},
                    'reviewer',1,'b'*64,'2026-11-09T00:00:00Z')
     assert tagged['records']==overlay['records']
     for body in (result['batchOne'],result['batchTwo']):
      payload=parse_body(body)
      overlay=prepare(payload,load_records(),overlay,'reviewer',1,'b'*64,'2026-11-09T00:00:00Z')
     navigate(result['readerPath'],language,width)
     assert browser.evaluate('document.getElementById("wb-search").value==='+json.dumps(result['second'])+
       '&&document.querySelector("#wb-tbody .is-selected")?.dataset.recordId==='+json.dumps(result['second']))
     print('PASS footer editor entry, ten-record pagination, contextual return and review submissions',language,width,flush=True)
     browser.evaluate('localStorage.removeItem("scro.review.drafts.v1");localStorage.removeItem("scro.review.queue.v2")')
   # Publish tags into the temporary deployment and verify the reader search.
   index=json.loads((site/'data/relevance-index.json').read_text())
   index['tag_catalog']=tagged['tag_catalog']
   index['record_tags']={key:{'tags':row['tags'],'issue':row['issue'],'digest':digest(row)}
                         for key,row in tagged['record_tags'].items()}
   (site/'data/relevance-index.json').write_text(json.dumps(index))
   navigate('workbench/?q=%23iphone')
   assert browser.evaluate('document.getElementById("wb-count").dataset.total==="1"')
   assert browser.evaluate('document.querySelector("#wb-tbody [data-record-id]")?.dataset.recordId==='+json.dumps(result['first']))
   navigate('workbench/?tag=iphone&record='+result['first'])
   assert browser.evaluate('document.querySelector("#wb-detail .wb-tag-chip")?.textContent==="#iphone"')
   assert browser.evaluate('document.querySelector("#wb-tag-filters button")?.textContent.includes("#iphone")')
   print('PASS public tags filter by hashtag, URL and inspector',flush=True)
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
   install_filter_fixture(site)
   clock_script=browser.call('Page.addScriptToEvaluateOnNewDocument',{
    'source':"Date.now=()=>Date.parse('2026-11-12T01:21:00Z');"
   })['identifier']
   browser.call('Emulation.setTimezoneOverride',{'timezoneId':'Asia/Taipei'})
   for language in ('en','zh','de','es'):
    for width in (1920,390):
     navigate('workbench/edit/?relevance=high',language,width)
     assert browser.evaluate(COLLECTION_CLOCK_PROBE), f'Editor collection clock failed for {language}, {width}px'
     assert browser.evaluate(FILTER_PROBE)
     reports.append({'language':language,'width':width,'relevance_filters':'passed'})
     print('PASS relevance options, combined filters, locale switching, shared and saved views, reset and sort',
           language,width,flush=True)
     navigate('workbench/?scope=latest&q=flood+theta',language,width)
     assert browser.evaluate(COLLECTION_CLOCK_PROBE), f'Reader collection clock failed for {language}, {width}px'
     assert browser.evaluate('document.getElementById("wb-count").dataset.total==="1"&&document.getElementById("wb-searchable-count").textContent==="7"&&document.querySelector("#wb-tbody [data-record-id]")?.dataset.recordId==="000000000000000008"&&!new URL(location.href).searchParams.has("scope")')
     navigate('workbench/edit/?scope=archive&month=2026-10&record=000000000000000008',language,width)
     assert browser.evaluate('document.getElementById("wb-count").dataset.total==="1"&&document.getElementById("wb-searchable-count").textContent==="7"&&!document.getElementById("wb-legacy-month").hidden&&document.getElementById("wb-legacy-month-value").textContent==="2026-10"&&document.querySelector("#wb-tbody .is-selected")?.dataset.recordId==="000000000000000008"&&new URL(document.getElementById("wb-return-to-reader").href).searchParams.get("firstSeenMonth")==="2026-10"')
     browser.evaluate('document.getElementById("wb-clear-legacy-month").click()')
     assert browser.evaluate('document.getElementById("wb-legacy-month").hidden&&document.getElementById("wb-count").dataset.total==="7"&&!new URL(location.href).searchParams.has("firstSeenMonth")')
     print('PASS legacy search URLs, first-observation month and stable catalogue total',language,width,flush=True)
     print('PASS localized collection age and full English UTC timestamp in both workbench modes',language,width,flush=True)
     if width==390:
      assert browser.evaluate(STALE_QUEUE_PROBE)
      browser.evaluate('localStorage.removeItem("scro.review.drafts.v1");localStorage.removeItem("scro.review.queue.v2")')
      print('PASS bulk removal of outdated drafts preserves current, unindexed and handoff drafts',language,flush=True)
   browser.call('Page.removeScriptToEvaluateOnNewDocument',{'identifier':clock_script})
   browser.call('Emulation.setTimezoneOverride',{'timezoneId':''})
   browser.evaluate(r'''(()=>{
    const rid='000000000000000004',index=SCRO_RELEVANCE,record=index.get(rid);
    const draft={...SCRO_REVIEW_STORE.publicationFields(record.review),expected_review_digest:'2'.repeat(64),
     _tagChange:{content_fingerprint:record.analysis.content_fingerprint,
      expected_tag_digest:'2'.repeat(64),tags:index.tags(rid)}};
    localStorage.setItem('scro.review.drafts.v1',JSON.stringify({[rid]:draft}));
    localStorage.setItem('scro.review.queue.v2',JSON.stringify({schema_version:2,selected:[rid],batches:[]}));
   })()''')
   navigate('workbench/edit/')
   assert browser.evaluate(r'''(()=>{
    const rid='000000000000000004';
    return !SCRO_REVIEW_STORE.getDraft(rid)&&!SCRO_REVIEW_STORE.selectedIds().includes(rid)&&
     !JSON.parse(localStorage.getItem('scro.review.drafts.v1')||'{}')[rid]&&
     !document.querySelector('[data-review-id="'+rid+'"]')&&
     SCRO_RELEVANCE.get(rid).review.relevance==='needs_review'&&SCRO_RELEVANCE.tags(rid).includes('smoke');
   })()''')
   print('PASS editor reload clears a fully published-equivalent outdated local draft',flush=True)
   assert browser.evaluate(PUBLICATION_STATUS_PROBE)
   print('PASS separate GitHub and published-review status failures preserve pending drafts',flush=True)
   missing_shard=site/'data/archive/2026-10-0001.json'
   shard=missing_shard.read_bytes()
   missing_shard.unlink()
   navigate('workbench/')
   assert browser.evaluate('document.getElementById("wb-count").dataset.total==="6"&&document.getElementById("wb-searchable-count").textContent==="—"&&document.querySelector("#wb-coverage.is-alert").textContent.includes("incomplete")')
   missing_shard.write_bytes(shard)
   (site/'data/latest.json').unlink()
   navigate('workbench/')
   assert browser.evaluate('document.getElementById("wb-count").dataset.total==="2"&&document.getElementById("wb-searchable-count").textContent==="—"&&document.querySelector("#wb-coverage.is-alert").textContent.includes("incomplete")')
   print('PASS catalogue fallback with missing archive shard or recent snapshot',flush=True)
  finally:
   browser.close();server.shutdown();server.server_close();thread.join(timeout=3)
 qa=ROOT/'_qa';qa.mkdir(exist_ok=True);(qa/'review-acceptance.json').write_text(json.dumps(reports,indent=2))
 print('PASS review UI, four-language relevance filters, handoff validation, and four-route overlay consistency')
if __name__=='__main__':run()
