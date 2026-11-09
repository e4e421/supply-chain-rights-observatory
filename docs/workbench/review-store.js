/* Browser-local drafts, explicit selection, and separately tracked GitHub handoffs.
   This is NOT authentication or a server database. No tokens are stored. */
(() => {
'use strict';
const DRAFTS='scro.review.drafts.v1';
const QUEUE='scro.review.queue.v2';
const FIELDS=['content_fingerprint','expected_review_digest','relevance','topics',
  'publisher_confirmed','canonical_url','note'];
const STATES=new Set(['handoff','submitted','published','needs_attention','cancelled']);
const ID=/^[a-f0-9]{18}$/;
function safeJSON(key,fallback){
  try {const data=JSON.parse(localStorage.getItem(key)||'null');return data===null?fallback:data;}
  catch (_) {return fallback;}
}
const all=safeJSON(DRAFTS,{});
let drafts=all&&typeof all==='object'&&!Array.isArray(all)?all:{};
const saved=safeJSON(QUEUE,{});
let state={
  schema_version:2,
  selected:Array.isArray(saved?.selected)?saved.selected.filter(x=>ID.test(x)).slice(0,300):[],
  batches:Array.isArray(saved?.batches)?saved.batches.filter(b=>b&&typeof b==='object'
   && typeof b.id==='string'&&STATES.has(b.status)&&Array.isArray(b.ids)).slice(-40):[]
};
const listeners=new Set();
const changes=()=>{
  for(const fn of listeners) try{fn();}catch(_){}
};
function persist(){
  try {
    localStorage.setItem(DRAFTS,JSON.stringify(drafts));
    localStorage.setItem(QUEUE,JSON.stringify(state));
    return true;
  }catch(_) {return false;}
}
function clone(obj){return JSON.parse(JSON.stringify(obj));}
function validDraft(rid,d){return ID.test(rid)&&d&&typeof d==='object'&&!Array.isArray(d);}
function latestActive(rid){
  return state.batches.findLast(b=>b.ids.includes(rid)
    &&(b.status==='handoff'||b.status==='submitted'||b.status==='needs_attention'))||null;
}
function draftEntries(){return Object.entries(drafts).filter(([id,d])=>validDraft(id,d));}
function availableEntries(){return draftEntries().filter(([rid])=>!latestActive(rid));}
function selectedEntries(){return availableEntries().filter(([rid])=>state.selected.includes(rid));}
function setSelected(rid,checked){
  if(!validDraft(rid,drafts[rid])||latestActive(rid))return false;
  state.selected=state.selected.filter(x=>x!==rid);
  if(checked)state.selected.push(rid);
  const saved=persist();changes();return saved;
}
function selectOnly(rid){
  if(!validDraft(rid,drafts[rid])||latestActive(rid))return false;
  state.selected=[rid];const result=persist();changes();return result;
}
function saveDraft(rid,decision){
  if(!ID.test(rid)||!decision||latestActive(rid))return false;
  drafts[rid]=clone(decision);
  // Saving an item never automatically selects every previous draft.
  state.selected=[rid];
  const success=persist();changes();return success;
}
function removeDraft(rid){
  if(latestActive(rid))return false;
  delete drafts[rid];state.selected=state.selected.filter(x=>x!==rid);
  const ok=persist();changes();return ok;
}
function publicationFields(d){
  const cleaned={};
  for(const field of FIELDS)cleaned[field]=d[field]===undefined?null:clone(d[field]);
  return cleaned;
}
function payload(items){
  return {schema_version:1,decisions:items.map(([record_id,d])=>({record_id,...publicationFields(d)}))};
}
function token(){
  if(crypto?.randomUUID)return crypto.randomUUID();
  const bits=new Uint8Array(16);crypto.getRandomValues(bits);
  return Array.from(bits,x=>x.toString(16).padStart(2,'0')).join('');
}
function makeHandoff(eligible){
  const items=selectedEntries();
  if(!items.length)throw Error('No selected drafts');
  if(items.length>25)throw Error('Review batch exceeds 25 records');
  if(!items.every(([rid,d])=>eligible(rid,d)))throw Error('Outdated review draft');
  const data=payload(items);
  const body='SCRO_PUBLISH_V2\n'+String.fromCharCode(96).repeat(3)+'json\n'
    +JSON.stringify(data)+'\n'+String.fromCharCode(96).repeat(3);
  const url=new URL('https://github.com/e4e421/supply-chain-rights-observatory/issues/new');
  url.searchParams.set('title','[Publish Workbench review]');
  url.searchParams.set('body',body);
  if(url.href.length>7500)throw Error('Review batch exceeds shareable URL length');
  const entry={
    id:token(),status:'handoff',created_at:new Date().toISOString(),ids:items.map(([rid])=>rid),
    decisions:data.decisions,url:url.href,body,issue_number:null,issue_url:null
  };
  state.batches.push(entry);
  state.batches=state.batches.slice(-40);
  state.selected=state.selected.filter(x=>!entry.ids.includes(x));
  if(!persist()){
    state.batches=state.batches.filter(x=>x.id!==entry.id);
    throw Error('Local browser storage unavailable');
  }
  changes();return clone(entry);
}
function matches(a,b){
  return FIELDS.every(k=>JSON.stringify(a?.[k]??null)===JSON.stringify(b?.[k]??null));
}
function refreshPublished(index){
  if(!index?.records)return false;
  let modified=false;
  for(const batch of state.batches){
    if(!['handoff','submitted','needs_attention'].includes(batch.status))continue;
    const published=batch.decisions.every(d=>{
      const indexed=index.records[d.record_id];
      const reviewed=indexed?.review_state==='current'?indexed.review:null;
      return reviewed&&matches(d,reviewed)&&(
        !batch.issue_number||reviewed.issue===batch.issue_number);
    });
    if(published){
      batch.status='published';batch.published_at=new Date().toISOString();modified=true;
      for(const d of batch.decisions){
        // Never discard more recent edits which differ from the submitted snapshot.
        if(matches(d,drafts[d.record_id]))delete drafts[d.record_id];
        state.selected=state.selected.filter(x=>x!==d.record_id);
      }
    }
  }
  if(modified){persist();changes();}
  return modified;
}
function normalizeBody(s){return String(s||'').trim().replace(/\r\n/g,'\n');}
function confirmIssue(b,issue){
  return issue?.title==='[Publish Workbench review]'&&issue.user?.login==='e4e421'
    &&normalizeBody(issue.body)===normalizeBody(b.body)
    &&Number.isInteger(issue.number)&&issue.number>0;
}
async function request(url){
  const abort=new AbortController(),timeout=setTimeout(()=>abort.abort(),9000);
  try{
    const r=await fetch(url,{credentials:'omit',cache:'no-store',signal:abort.signal,
      headers:{'Accept':'application/vnd.github+json'}});
    if(!r.ok)throw Error('GitHub HTTP '+r.status);
    return await r.json();
  }finally{clearTimeout(timeout);}
}
async function refreshFromGitHub(index){
  refreshPublished(index);
  const pending=state.batches.filter(b=>['handoff','submitted'].includes(b.status));
  if(!pending.length)return {checked:0,matched:0};
  let matchesFound=0,issues;
  const listURL='https://api.github.com/repos/e4e421/supply-chain-rights-observatory/issues?state=all&per_page=100&sort=created&direction=desc';
  issues=await request(listURL);
  if(!Array.isArray(issues))throw Error('Unexpected GitHub Issue response');
  for(const b of pending){
    let issue=b.issue_number?issues.find(i=>i.number===b.issue_number):null;
    if(!issue)issue=issues.find(i=>confirmIssue(b,i));
    if(!issue||!confirmIssue(b,issue))continue;
    b.status='submitted';b.issue_number=issue.number;b.issue_url=issue.html_url;matchesFound++;
    if(issue.state==='closed'){
      // A closed Issue alone is not proof that the public index deployed.
      b.status='submitted';
    }
  }
  if(matchesFound){persist();changes();}
  return {checked:pending.length,matched:matchesFound};
}
function cancelHandoff(batchId){
  const b=state.batches.find(x=>x.id===batchId);
  if(!b||!['handoff','submitted','needs_attention'].includes(b.status))return false;
  b.status='cancelled';
  const result=persist();changes();return result;
}
function batches(){return state.batches.map(clone).reverse();}
function onChange(fn){listeners.add(fn);return()=>listeners.delete(fn);}
window.addEventListener('storage',e=>{
  if(e.key!==DRAFTS&&e.key!==QUEUE)return;
  const d=safeJSON(DRAFTS,{}),q=safeJSON(QUEUE,{});
  drafts=d&&typeof d==='object'&&!Array.isArray(d)?d:{};
  state.selected=Array.isArray(q.selected)?q.selected.filter(x=>ID.test(x)):[];
  state.batches=Array.isArray(q.batches)?q.batches.filter(b=>STATES.has(b.status)):[];
  changes();
});
window.SCRO_REVIEW_STORE=Object.freeze({
  draftEntries,availableEntries,selectedEntries,selectedIds:()=>[...state.selected],
  getDraft:rid=>drafts[rid]||null,active:latestActive,saveDraft,removeDraft,
  setSelected,selectOnly,payload,makeHandoff,batches,refreshPublished,
  refreshFromGitHub,cancelHandoff,onChange,publicationFields
});
})();
