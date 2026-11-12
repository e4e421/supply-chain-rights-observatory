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
function readDrafts(){
  const all=safeJSON(DRAFTS,{});
  return all&&typeof all==='object'&&!Array.isArray(all)?all:{};
}
function readQueue(){
  const saved=safeJSON(QUEUE,{});
  return {
    schema_version:2,
    selected:Array.isArray(saved?.selected)?saved.selected.filter(x=>ID.test(x)).slice(0,300):[],
    batches:Array.isArray(saved?.batches)?saved.batches.filter(b=>b&&typeof b==='object'
      &&typeof b.id==='string'&&STATES.has(b.status)&&Array.isArray(b.ids)).slice(-40):[]
  };
}
let drafts=readDrafts(),state=readQueue();
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
  const tagChange=drafts[rid]?._tagChange;
  drafts[rid]=clone(tagChange?{...decision,_tagChange:tagChange}:decision);
  // Saving an item never automatically selects every previous draft.
  state.selected=[rid];
  const success=persist();changes();return success;
}
function hasDecision(d){return typeof d?.relevance==='string';}
function saveTags(rid,change,title){
  if(!ID.test(rid)||latestActive(rid))return false;
  if(change){
    drafts[rid]={...drafts[rid],_title:title,_tagChange:clone(change)};
    state.selected=[rid];
  }else if(hasDecision(drafts[rid])){
    delete drafts[rid]._tagChange;
  }else{
    delete drafts[rid];
    state.selected=state.selected.filter(id=>id!==rid);
  }
  const success=persist();changes();return success;
}
function removeDraft(rid){
  if(latestActive(rid))return false;
  delete drafts[rid];state.selected=state.selected.filter(x=>x!==rid);
  const ok=persist();changes();return ok;
}
function draftStatus(rid,d,index){
  if(!validDraft(rid,d))return 'unavailable';
  const record=index?.records?.[rid],fingerprint=record?.analysis?.content_fingerprint;
  const decision=hasDecision(d),tagChange=d._tagChange;
  const tagDigest=index?.record_tags?.[rid]?.digest||index?.empty_tag_digest;
  if(typeof fingerprint!=='string'||!fingerprint||(!decision&&!tagChange)
    ||(decision&&(typeof record.review_digest!=='string'||!record.review_digest))
    ||(tagChange&&(typeof tagDigest!=='string'||!tagDigest)))
    return 'unavailable';
  const outdatedReview=decision&&(d.content_fingerprint!==fingerprint||d.expected_review_digest!==record.review_digest);
  const outdatedTags=tagChange&&(tagChange.content_fingerprint!==fingerprint||tagChange.expected_tag_digest!==tagDigest);
  return outdatedReview||outdatedTags?'outdated':'current';
}
function applyDraftCleanup(removed,deselected){
  const selected=state.selected.filter(rid=>!deselected.has(rid));
  const selectionChanged=selected.length!==state.selected.length;
  if(!removed.size&&!selectionChanged)return {removed:0,persisted:true};
  // A storage event from another tab can still be queued after a confirmation.
  if(JSON.stringify(readDrafts())!==JSON.stringify(drafts)||JSON.stringify(readQueue())!==JSON.stringify(state))
    return {removed:0,persisted:false};
  const remaining={...drafts};
  for(const rid of removed)delete remaining[rid];
  let selectionSaved=false;
  try{
    if(selectionChanged){
      localStorage.setItem(QUEUE,JSON.stringify({...state,selected}));
      selectionSaved=true;
    }
    if(removed.size)localStorage.setItem(DRAFTS,JSON.stringify(remaining));
  }catch(_){
    if(selectionSaved){
      try{localStorage.setItem(QUEUE,JSON.stringify(state));}catch(_){}
    }
    return {removed:0,persisted:false};
  }
  drafts=remaining;state.selected=selected;
  changes();
  return {removed:removed.size,persisted:true};
}
function removeStaleDrafts(ids=[],index){
  const removed=new Set();
  for(const rid of ids){
    if(typeof rid==='string'&&!latestActive(rid)&&draftStatus(rid,drafts[rid],index)==='outdated')
      removed.add(rid);
  }
  return applyDraftCleanup(removed,removed);
}
function reconcileStaleDrafts(index){
  const removed=new Set(),deselected=new Set();
  for(const [rid,d] of availableEntries()){
    if(draftStatus(rid,d,index)!=='outdated')continue;
    deselected.add(rid);
    const record=index.records[rid],tagChange=d._tagChange;
    const reviewPublished=!hasDecision(d)||(record.review_state==='current'&&record.review
      &&matches(d,record.review)&&d.content_fingerprint===record.analysis.content_fingerprint);
    const publishedTagEntry=index.record_tags?.[rid];
    const publishedTags=publishedTagEntry===undefined&&index.record_tags&&index.empty_tag_digest
      ?[]:publishedTagEntry?.tags;
    const tagsPublished=!tagChange||(tagChange.content_fingerprint===record.analysis.content_fingerprint
      &&Array.isArray(tagChange.tags)&&Array.isArray(publishedTags)&&sameTags(tagChange.tags,publishedTags));
    if(reviewPublished&&tagsPublished)removed.add(rid);
  }
  return applyDraftCleanup(removed,deselected);
}
function publicationFields(d){
  const cleaned={};
  for(const field of FIELDS)cleaned[field]=d[field]===undefined?null:clone(d[field]);
  return cleaned;
}
function payload(items){
  const decisions=items.filter(([,d])=>hasDecision(d)).map(([record_id,d])=>({record_id,...publicationFields(d)}));
  const tagChanges=items.filter(([,d])=>d._tagChange).map(([record_id,d])=>({record_id,...clone(d._tagChange)}));
  return {schema_version:1,decisions,...(tagChanges.length?{tag_changes:tagChanges}:{})};
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
    decisions:data.decisions,tagChanges:data.tag_changes||[],url:url.href,body,issue_number:null,issue_url:null
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
  // Expected prior review digest is a concurrency guard, not a published decision field.
  return FIELDS.filter(k=>k!=='expected_review_digest').every(k=>
    JSON.stringify(a?.[k]??null)===JSON.stringify(b?.[k]??null));
}
function refreshPublished(index){
  if(!index?.records)return false;
  let modified=false;
  for(const batch of state.batches){
    if(!['handoff','submitted','needs_attention'].includes(batch.status))continue;
    if(!Number.isInteger(batch.issue_number)||batch.issue_number<1)continue;
    const tagChanges=batch.tagChanges||[];
    const published=batch.decisions.every(d=>{
      const indexed=index.records[d.record_id];
      const reviewed=indexed?.review_state==='current'?indexed.review:null;
      return reviewed&&matches(d,reviewed)&&reviewed.issue===batch.issue_number;
    })&&tagChanges.every(d=>{
      const tagged=index.record_tags?.[d.record_id];
      return tagged?.issue===batch.issue_number&&sameTags(tagged.tags,d.tags);
    });
    if(published){
      batch.status='published';batch.published_at=new Date().toISOString();modified=true;
      for(const d of batch.decisions){
        // Never discard more recent edits which differ from the submitted snapshot.
        if(matches(d,drafts[d.record_id])){
          for(const field of FIELDS)delete drafts[d.record_id][field];
        }
      }
      for(const d of tagChanges){
        const saved=drafts[d.record_id]?._tagChange;
        if(saved?.expected_tag_digest===d.expected_tag_digest&&sameTags(saved.tags,d.tags))delete drafts[d.record_id]._tagChange;
      }
      for(const rid of batch.ids){
        if(!hasDecision(drafts[rid])&&!drafts[rid]?._tagChange)delete drafts[rid];
        state.selected=state.selected.filter(x=>x!==rid);
      }
    }
  }
  if(modified){persist();changes();}
  return modified;
}
function sameTags(a,b){return JSON.stringify([...a].sort())===JSON.stringify([...b].sort());}
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
  if(!b||b.status!=='handoff')return false;
  b.status='cancelled';
  const result=persist();changes();return result;
}
function batches(){return state.batches.map(clone).reverse();}
function onChange(fn){listeners.add(fn);return()=>listeners.delete(fn);}
window.addEventListener('storage',e=>{
  if(e.key!==DRAFTS&&e.key!==QUEUE)return;
  drafts=readDrafts();state=readQueue();
  changes();
});
window.SCRO_REVIEW_STORE=Object.freeze({
  draftEntries,availableEntries,selectedEntries,selectedIds:()=>[...state.selected],
  getDraft:rid=>drafts[rid]||null,active:latestActive,hasDecision,saveDraft,saveTags,removeDraft,
  draftStatus,removeStaleDrafts,reconcileStaleDrafts,
  setSelected,selectOnly,payload,makeHandoff,batches,refreshPublished,
  refreshFromGitHub,cancelHandoff,onChange,publicationFields
});
})();
