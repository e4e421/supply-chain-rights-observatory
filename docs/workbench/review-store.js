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
function saveDraftAndQueueChanges(nextDrafts,nextQueue){
  const priorDrafts=JSON.stringify(drafts),priorQueue=JSON.stringify(state);
  const updatedDrafts=JSON.stringify(nextDrafts),updatedQueue=JSON.stringify(nextQueue);
  // A storage event from another tab can still be queued after a confirmation.
  if(JSON.stringify(readDrafts())!==priorDrafts||JSON.stringify(readQueue())!==priorQueue)return false;
  let queueSaved=false;
  try{
    if(updatedQueue!==priorQueue){
      localStorage.setItem(QUEUE,updatedQueue);
      queueSaved=true;
    }
    if(updatedDrafts!==priorDrafts)localStorage.setItem(DRAFTS,updatedDrafts);
  }catch(_){
    if(queueSaved){
      try{localStorage.setItem(QUEUE,priorQueue);}catch(_){}
    }
    return false;
  }
  drafts=nextDrafts;state=nextQueue;
  changes();
  return true;
}
function applyDraftCleanup(removed,deselected){
  const selected=state.selected.filter(rid=>!deselected.has(rid));
  if(!removed.size&&selected.length===state.selected.length)return {removed:0,persisted:true};
  const remaining={...drafts};
  for(const rid of removed)delete remaining[rid];
  const persisted=saveDraftAndQueueChanges(remaining,{...state,selected});
  return {removed:persisted?removed.size:0,persisted};
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
function publishedRows(batch,index){
  if(!Array.isArray(batch.decisions)||!Array.isArray(batch.tagChanges??[]))return [];
  const reviews=batch.decisions.map(d=>{
    if(!d||!ID.test(d.record_id))return null;
    const indexed=index.records[d.record_id];
    const reviewed=indexed?.review_state==='current'?indexed.review:null;
    return reviewed&&matches(d,reviewed)?reviewed:null;
  });
  const tags=(batch.tagChanges||[]).map(d=>{
    if(!d||!ID.test(d.record_id))return null;
    const tagged=index.record_tags?.[d.record_id];
    return Array.isArray(tagged?.tags)&&Array.isArray(d.tags)&&sameTags(tagged.tags,d.tags)?tagged:null;
  });
  return [...reviews,...tags];
}
function issueLink(number){
  return 'https://github.com/e4e421/supply-chain-rights-observatory/issues/'+number;
}
function refreshPublished(index,proofs=new Map()){
  if(!index?.records)return false;
  const nextQueue=clone(state),nextDrafts=clone(drafts);
  let modified=false;
  for(const batch of nextQueue.batches){
    if(!['handoff','submitted','needs_attention'].includes(batch.status))continue;
    const proof=proofs.get(batch.id);
    const issue=batch.issue_number||(proof?.body===batch.body?proof.issue:null);
    if(!Number.isInteger(issue)||issue<1)continue;
    const tagChanges=batch.tagChanges||[];
    const rows=publishedRows(batch,index);
    const published=rows.length&&rows.every(row=>row?.issue===issue);
    if(published){
      batch.issue_number=issue;batch.issue_url=issueLink(issue);
      batch.status='published';batch.published_at=new Date().toISOString();modified=true;
      for(const d of batch.decisions){
        // Never discard more recent edits which differ from the submitted snapshot.
        const saved=nextDrafts[d.record_id];
        if(hasDecision(saved)&&matches(d,saved)&&saved.expected_review_digest===d.expected_review_digest){
          for(const field of FIELDS)delete saved[field];
        }
      }
      for(const d of tagChanges){
        const saved=nextDrafts[d.record_id]?._tagChange;
        if(Array.isArray(saved?.tags)&&saved.content_fingerprint===d.content_fingerprint
          &&saved.expected_tag_digest===d.expected_tag_digest&&sameTags(saved.tags,d.tags))delete nextDrafts[d.record_id]._tagChange;
      }
      for(const rid of batch.ids){
        if(!hasDecision(nextDrafts[rid])&&!nextDrafts[rid]?._tagChange)delete nextDrafts[rid];
        nextQueue.selected=nextQueue.selected.filter(x=>x!==rid);
      }
    }
  }
  return modified&&saveDraftAndQueueChanges(nextDrafts,nextQueue);
}
async function refreshPublishedFromIndex(index){
  if(!index?.records)return false;
  const proofs=new Map();
  if(crypto?.subtle){
    for(const batch of state.batches){
      if(batch.status!=='handoff'||batch.issue_number||typeof batch.body!=='string')continue;
      const rows=publishedRows(batch,index);
      const issue=rows[0]?.issue,digest=rows[0]?.issue_digest;
      if(!Number.isInteger(issue)||issue<1||!/^[a-f0-9]{64}$/.test(digest)||
          !rows.every(row=>row?.issue===issue&&row.issue_digest===digest))continue;
      try{
        for(const body of new Set([batch.body,normalizeBody(batch.body)])){
          const bytes=new TextEncoder().encode(JSON.stringify({body}));
          const hash=new Uint8Array(await crypto.subtle.digest('SHA-256',bytes));
          const actual=Array.from(hash,x=>x.toString(16).padStart(2,'0')).join('');
          if(actual===digest){proofs.set(batch.id,{issue,body:batch.body});break;}
        }
      }catch(_){/* An unavailable digest check leaves the handoff pending. */}
    }
  }
  return refreshPublished(index,proofs);
}
function sameTags(a,b){return JSON.stringify([...a].sort())===JSON.stringify([...b].sort());}
function normalizeBody(s){return String(s||'').trim().replace(/\r\n/g,'\n');}
function confirmIssue(b,issue){
  return issue?.title==='[Publish Workbench review]'&&issue.user?.login==='e4e421'&&!issue.pull_request
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
  await refreshPublishedFromIndex(index);
  const pending=new Map(state.batches.filter(b=>b.status==='handoff'&&!b.issue_number).map(b=>[b.id,b.body]));
  if(!pending.size)return {checked:0,matched:0,unavailable:false};
  let matchesFound=0,issues;
  const listURL='https://api.github.com/repos/e4e421/supply-chain-rights-observatory/issues?state=all&per_page=100&sort=created&direction=desc';
  try{
    issues=await request(listURL);
    if(!Array.isArray(issues))throw Error('Unexpected GitHub Issue response');
  }catch(_){
    return {checked:pending.size,matched:0,unavailable:true};
  }
  const nextQueue=clone(state);
  for(const b of nextQueue.batches){
    if(pending.get(b.id)!==b.body||!pending.has(b.id)||b.status!=='handoff'||b.issue_number)continue;
    const issue=issues.find(i=>confirmIssue(b,i));
    if(!issue)continue;
    b.status='submitted';b.issue_number=issue.number;b.issue_url=issueLink(issue.number);matchesFound++;
  }
  if(matchesFound){
    if(!saveDraftAndQueueChanges(drafts,nextQueue))return {checked:pending.size,matched:0,unavailable:false,storageUnavailable:true};
    refreshPublished(index);
  }
  return {checked:pending.size,matched:matchesFound,unavailable:false};
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
  setSelected,selectOnly,payload,makeHandoff,batches,refreshPublished,refreshPublishedFromIndex,
  refreshFromGitHub,cancelHandoff,onChange,publicationFields
});
})();
