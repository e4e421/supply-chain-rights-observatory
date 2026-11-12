/* Shared research portal UI. */
(() => {
'use strict';
const ROOT=new URL('./',document.currentScript.src), PAGE=document.body.dataset.page || 'home';
const $=id=>document.getElementById(id), I=window.SCRO_I18N||{language:'en',t:x=>x,onChange:()=>{}};
let dictionary={}, redraw=()=>{};
const TOPICS={policy:'Policy & governance','forced-labour':'Forced labour','working-conditions':'Working conditions','worker-voice':'Worker voice & remedy',network:'Supply networks',research:'Academic research'};
const SEARCH_KEYS=['firstSeenMonth','q','from','to','kind','evidence','sort','topics','tag','cols','density','record','offset'];
const t=x=>I.language==='en'?String(x):(dictionary[x]?.[I.language] || I.t(String(x)));
const number=value=>I.formatNumber?.(value)??String(value);
const node=(tag,text='',cls='')=>{const n=document.createElement(tag);n.textContent=String(text??'');if(cls)n.className=cls;return n;};
const uri=(path,params={})=>{const u=new URL(path,ROOT);for(const [k,v] of Object.entries({...params,lang:I.language}))if(v!==undefined&&v!==null&&v!=='')u.searchParams.set(k,String(v));return u.href;};
const internal=(path,label,params={})=>{const a=node('a',t(label));a.href=uri(path,params);return a;};
const publicLink=(url,label)=>{try{const u=new URL(url);if(u.protocol!=='https:'||u.username||u.password)throw Error();const a=node('a',t(label));a.href=u.href;a.target='_blank';a.rel='noopener noreferrer';return a;}catch{return node('span',t('Link unavailable'));}};
function date(s,withTime=false){return I.formatDate?.(s,withTime)||t('Not available');}
async function json(path){const abort=new AbortController(),timer=setTimeout(()=>abort.abort(),15000);try{const r=await fetch(new URL(path,ROOT),{credentials:'omit',cache:'no-store',signal:abort.signal});if(!r.ok)throw Error('Resource unavailable');const text=await r.text();if(text.length>12000000)throw Error('Resource too large');return JSON.parse(text);}finally{clearTimeout(timer);}}
function feedback(s){if($('portal-feedback'))$('portal-feedback').textContent=t(s);}
function links(){for(const a of document.querySelectorAll('a[href]')){try{const u=new URL(a.getAttribute('href'),location.href);if(u.origin===ROOT.origin&&u.pathname.startsWith(ROOT.pathname)&&!u.pathname.match(/\.(md|json|jsonl|csv|cff|zip)$/i)){u.searchParams.set('lang',I.language);a.href=u.href;}}catch{}}}
function translate(){document.querySelectorAll('[data-pk]').forEach(e=>{e.textContent=t(e.dataset.pk);});document.querySelectorAll('[data-ph]').forEach(e=>e.placeholder=t(e.dataset.ph));document.title=t(document.body.dataset.pageTitle||'Research Portal')+' | Supply Chain Rights Observatory';links();redraw();}
function workbenchFilters(params){
 const filters={};
 for(const key of SEARCH_KEYS){
  const value=params.get(key);
  if(value)filters[key]=value;
 }
 const month=params.get('month'),topic=params.get('topic');
 if(!filters.firstSeenMonth&&/^\d{4}-(0[1-9]|1[0-2])$/.test(month))filters.firstSeenMonth=month;
 if(!filters.topics&&Object.hasOwn(TOPICS,topic))filters.topics=topic;
 return filters;
}
function legacy(){
 const current=new URL(location.href);
 if(PAGE==='archive'||(PAGE==='home'&&current.hash==='#archive-explorer')){
  location.replace(uri('workbench/',workbenchFilters(current.searchParams)));
  return true;
 }
 if(PAGE!=='home')return false;
 const destination={'#sources':'sources/','#lenses':'research/','#method':'methodology/'}[current.hash];
 if(!destination)return false;
 const next=new URL(destination,ROOT);
 next.search=current.search;
 if(!next.searchParams.has('lang'))next.searchParams.set('lang',I.language);
 location.replace(next.href);
 return true;
}
function updateParams(values){const u=new URL(location.href);for(const k of ['q','month','topic','kind','from','to','category','review'])u.searchParams.delete(k);for(const [k,v] of Object.entries(values))if(v&&v!=='all')u.searchParams.set(k,v);u.searchParams.set('lang',I.language);history.replaceState(null,'',u.pathname+u.search+u.hash);}
function recordCard(r){const card=node('article','','portal-record'),rid=r.record_id||r.id;
 const meta=node('div','','portal-record-meta');meta.append(node('time',date(r.published_at)),node('span',t(r.kind==='academic'?'Bibliographic record':'Unverified discovery')));card.append(meta);
 const a=internal('record.html',r.title,{id:rid});a.textContent=r.title;a.lang=r.original_language||'und';a.className='portal-record-title';card.append(a);
 const publisher=r.publisher_hint||t('Publisher not verified');card.append(node('p',publisher+' · '+rid,'portal-record-meta'));
 card.append(node('p',(r.topics||[]).map(x=>t(TOPICS[x]||x)).join(' · '),'portal-topic-line'));return card;
}
async function home(){
 const result=await Promise.allSettled([json('data/latest.json'),json('data/archive/catalog.json'),json('data/references.json')]);
 const live=result[0].status==='fulfilled'?result[0].value:null,cat=result[1].status==='fulfilled'?result[1].value:null,refs=result[2].status==='fulfilled'?result[2].value:null;
 window.SCRO_COLLECTION_TIME?.set(live?.last_successful_collection);
 redraw=()=>{const list=$('home-latest');list.replaceChildren();$('home-total').textContent=number(cat?.total_records??'—');$('home-sources').textContent=Array.isArray(refs)?number(refs.length):'—';
 const old=Date.now()-Date.parse(live?.last_successful_collection||'')>48*3600000;
 $('home-health').textContent=t(!live?'Unavailable':old?'Data stale':live.status==='ok'?'Operational (technical)':live.status==='partial'?'Partial sources':'Collection failed');
 $('home-status').textContent=!live?t('Public data could not be loaded.'):old?t('The last successful collection is over 48 hours old.'):'';
 for(const r of (live?.items||[]).slice(0,6))list.append(recordCard(r));links();};redraw();
}
function sourceAvailability(success, attempted, failures, successLabel, referenceState=null){
 const manual=['manual_only','policy_restricted'].includes(referenceState);
 const state=manual?'manual':!attempted?'unknown':success?'ok':failures>=3?'review':'retry';
 const labels={manual:referenceState==='policy_restricted'?'Site rules restrict automatic checks':'Manual link check',
   unknown:referenceState?'Awaiting first check':'No check recorded',ok:successLabel,
   review:'Manual confirmation needed',retry:'Failed · retry scheduled'};
 return node('strong',t(labels[state])+(failures>0?' ('+failures+')':''),'portal-availability is-'+state);
}
function referenceCheckDetail(check){
 const code=check.http_status,kind=check.failure_kind;
 let detail='';
 if(code===429||kind==='rate_limited')detail='Website rate limit';
 else if([401,403,405].includes(code)||kind==='access_restricted')detail='Website limits automated requests';
 else if(kind==='timeout')detail='Connection timed out';
 else if(check.reachability==='not_confirmed')detail='Connection unconfirmed';
 return [code?'HTTP '+code:'',detail?t(detail):''].filter(Boolean).join(' · ');
}
async function sources(){
 const [refsResult,healthResult,collectionResult]=await Promise.allSettled([
   json('data/references.json'),json('data/source-health.json'),json('data/latest.json')]);
 const refs=refsResult.value,health=healthResult.value,feeds=collectionResult.value?.sources;
 if(!Array.isArray(refs)){$('source-count').textContent=t('Public data could not be loaded.');return;}
 const byUrl=new Map(),legacyByName=new Map();
 for(const row of health?.sources||[]){if(row.url)byUrl.set(row.url,row);else legacyByName.set(row.name,row);}
 const categories=[...new Set(refs.map(x=>x.category))].sort();for(const k of categories){const o=node('option',t(k));o.value=k;$('source-category').append(o);}
 const p=new URL(location.href).searchParams;$('source-search').value=(p.get('q')||'').slice(0,120);if(categories.includes(p.get('category')))$('source-category').value=p.get('category');if(['needs','licence','connection'].includes(p.get('review')))$('source-review').value=p.get('review');
 redraw=()=>{
 const feedRows=$('source-feed-rows');feedRows.replaceChildren();
 for(const feed of feeds||[]){
  const row=node('tr');row.dataset.sourceId=feed.id;
  const name=node('th',t(feed.name));
  for(const [url,label] of [[feed.feed_url,'Official feed'],[feed.reuse_url,'Metadata reuse terms']]){
   if(!url)continue;
   const line=node('p');line.append(publicLink(url,label));name.append(line);
  }
  const availability=node('td');
  availability.append(sourceAvailability(feed.status==='ok',feed.last_attempt,feed.consecutive_failures,'Data retrieved'));
  row.append(name,availability,node('td',feed.status==='ok'?number(feed.items??'—'):'—'),node('td',date(feed.last_attempt,true)));
  row.firstChild.scope='row';feedRows.append(row);
 }
 if(!feeds?.length){const row=node('tr'),cell=node('td',t('No check recorded'));cell.colSpan=4;row.append(cell);feedRows.append(row);}
 const filter=$('source-review').value,cat=$('source-category').value,q=$('source-search').value.toLowerCase();$('source-rows').replaceChildren();
 for(const o of $('source-category').options)if(o.value!=='all')o.textContent=t(o.value);
 const records=refs.map(ref=>({ref,h:byUrl.get(ref.url)??legacyByName.get(ref.name)})).filter(({ref,h})=>{if(cat!=='all'&&ref.category!==cat)return false;if(q&&![ref.name,ref.category,ref.use,t(ref.use)].join(' ').toLowerCase().includes(q))return false;if(filter==='needs'&&!h?.review_needed)return false;if(filter==='licence'&&h?.licence_review_status==='approved_for_metadata'&&h.metadata_reuse_notice)return false;if(filter==='connection'&&(!h?.last_probe||['responded','manual_only','policy_restricted'].includes(h.reachability)))return false;return true;});
 $('source-count').textContent=number(records.length)+' / '+number(refs.length)+' '+t('curated sources')+(health?'':' · '+t('Source-health report unavailable; review states are unknown.'));
 for(const {ref,h} of records){const row=node('tr'),name=node('td');name.append(publicLink(ref.url,ref.name),node('p',t(ref.use)),node('small',h?.id||'—'));row.append(name,node('td',t(ref.category)));
 const editorial=node('td');editorial.append(node('strong',t(!h?'Unknown':h.review_needed?'Review needed':'Review recorded')),node('p',date(h?.last_editorial_review)),node('small',t('Next review')+': '+date(h?.review_due)));row.append(editorial);
 const use=node('td');
 if(h?.licence_review_status==='approved_for_metadata'&&h.metadata_reuse_notice){
  use.append(publicLink(h.metadata_reuse_notice,'Metadata reuse terms'));
 }else use.textContent=t('Reference link');
 row.append(use);
 const reachable=node('td');reachable.append(sourceAvailability(h?.reachability==='responded',h?.last_probe,h?.consecutive_failures,'Website reachable',h?.reachability));
 if(h?.last_probe){const detail=referenceCheckDetail(h);if(detail)reachable.append(node('p',detail));reachable.append(node('small',date(h.last_probe,true)));}
 row.append(reachable);$('source-rows').append(row);}
 if(!records.length){const row=node('tr'),td=node('td',t('No matching sources.'));td.colSpan=5;row.append(td);$('source-rows').append(row);}links();};
 for(const id of ['source-search','source-category','source-review'])$(id).addEventListener(id==='source-search'?'input':'change',()=>{updateParams({q:$('source-search').value,category:$('source-category').value,review:$('source-review').value});redraw();});redraw();
}
async function record(){
 const p=new URL(location.href).searchParams,id=p.get('id')||'';let rec=null,fail=false;
 const filters=workbenchFilters(new URLSearchParams(p.get('back')||''));
 if(!p.has('back')&&/^[a-f0-9]{18}$/.test(id))filters.record=id;
 $('record-return-to-search').href=uri('workbench/',filters);
 try{if(!/^[a-f0-9]{18}$/.test(id))throw Error();const index=await json('data/record-index.json'),where=index.records?.[id];if(!where||!/^\d{4}-\d{2}-\d{4}\.json$/.test(where.file))throw Error();const shard=await json('data/archive/'+where.file);rec=shard.records.find(r=>r.record_id===id);if(!rec)throw Error();}catch{fail=true;}
 redraw=()=>{const root=$('record-content');root.replaceChildren();if(fail){root.append(node('p',t('Record unavailable. Verify its identifier and month.')));return;}
 const title=node('h2',rec.title);title.lang='und';root.append(title,node('code',rec.record_id));
 const dl=node('dl');for(const [label,value] of [['Publication date (UTC)',date(rec.published_at)],['First observed',date(rec.first_seen,true)],['Publisher credit (unverified)',rec.publisher_hint||t('Unknown')],['Monitoring query',t(rec.source)],['Evidence class',t(rec.evidence_status)],['Topics (preliminary)',(rec.topics||[]).map(k=>t(TOPICS[k]||k)).join(', ')],['Event ID',rec.event_id||t('Not assigned')],['DOI',rec.doi]])if(value)dl.append(node('dt',t(label)),node('dd',value));root.append(dl,publicLink(rec.url,'Open original discovery link'));
 links();};redraw();
}
async function start(){
 if(legacy())return;window.addEventListener('hashchange',legacy);
 try{dictionary=await json('portal-translations.json');}catch{dictionary={};}
 $('share-query')?.addEventListener('click',async()=>{const url=new URL(location.href);url.searchParams.set('lang',I.language);try{await navigator.clipboard.writeText(url.href);feedback('Shareable link copied');}catch{window.prompt(t('Copy this link'),url.href);}});
 I.onChange(translate);translate();
 if(PAGE==='home')await home();else if(PAGE==='sources')await sources();else if(PAGE==='record')await record();
 translate();window.__PORTAL_READY__=true;
}
start().catch(()=>{feedback('Public data could not be loaded.');window.__PORTAL_ERROR__=true;});
})();
