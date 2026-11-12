import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {webcrypto} from 'node:crypto';

const source=fs.readFileSync('docs/workbench/review-store.js','utf8');
const A='a'.repeat(18),B='b'.repeat(18),C='c'.repeat(18);
const D='1'.repeat(18),E='2'.repeat(18),F='3'.repeat(18);
const DRAFTS='scro.review.drafts.v1',QUEUE='scro.review.queue.v2';
function draft(name){
 return {content_fingerprint:'f'.repeat(64),expected_review_digest:'d'.repeat(64),
  relevance:'include',topics:null,publisher_confirmed:false,canonical_url:null,
  note:name,_title:name,_savedAt:'2026-11-09T10:00:00Z'};
}
function harness(seed={},fetchImpl=()=>Promise.reject(Error('no network'))){
 const data=new Map(Object.entries(seed));
 const localStorage={
  getItem:key=>data.get(key)??null,
  setItem:(key,val)=>data.set(key,String(val)),
  removeItem:key=>data.delete(key)
 };
 const window={addEventListener(){}};
 const context={window,localStorage,URL,crypto:webcrypto,Uint8Array,fetch:fetchImpl,
  AbortController,setTimeout,clearTimeout};
 vm.runInNewContext(source,context,{filename:'review-store.js'});
 return {store:window.SCRO_REVIEW_STORE,data,localStorage};
}
test('old drafts remain untouched and selecting the second does not submit the first',()=>{
 const {store}=harness({'scro.review.drafts.v1':JSON.stringify({[A]:draft('old')})});
 assert.equal(store.draftEntries().length,1);
 assert.deepEqual([...store.selectedIds()],[]);
 assert.equal(store.saveDraft(A,draft('first')),true);
 assert.deepEqual([...store.selectedIds()],[A]);
 assert.equal(store.saveDraft(B,draft('second')),true);
 assert.deepEqual([...store.selectedIds()],[B]);
 const first=store.makeHandoff(()=>true);
 assert.deepEqual([...first.ids],[B]);
 assert.deepEqual([...first.decisions.map(x=>x.record_id)],[B]);
 assert.equal('note' in first.decisions[0],true);
 assert.equal('_title' in first.decisions[0],false);
 assert.equal(store.active(B).status,'handoff');
 assert.equal(store.getDraft(A)?.note,'first');
 assert.equal(store.getDraft(B)?.note,'second');
 assert.equal(store.selectedEntries().length,0);
 assert.throws(()=>store.makeHandoff(()=>true),/No selected/);
 assert.equal(store.setSelected(A,true),true);
 const second=store.makeHandoff(()=>true);
 assert.deepEqual([...second.ids],[A]);
 assert.equal(store.batches().length,2);
 assert.equal(store.cancelHandoff(second.id),true);
 assert.equal(store.cancelHandoff(second.id),false);
 assert.equal(store.getDraft(A)?.note,'first');
});
test('tag-only handoffs preserve other reviews and clear only after the matching Issue deploys',async()=>{
 let issue;
 const {store}=harness({},async()=>({ok:true,json:async()=>[issue]}));
 const change={content_fingerprint:'f'.repeat(64),expected_tag_digest:'d'.repeat(64),tags:['iphone','工廠事故']};
 store.saveDraft(B,draft('existing review'));
 store.saveTags(A,change,'tagged record');
 const batch=store.makeHandoff(()=>true);
 assert.deepEqual([...batch.ids],[A]);
 assert.equal(batch.decisions.length,0);
 assert.equal(batch.tagChanges[0].record_id,A);
 assert.equal(store.getDraft(B).note,'existing review');
 issue={number:16,state:'closed',title:'[Publish Workbench review]',
  user:{login:'e4e421'},body:batch.body,html_url:'https://github.com/example/issues/16'};
 const index={records:{},record_tags:{[A]:{tags:['工廠事故','iphone'],issue:16}}};
 assert.equal(store.refreshPublished(index),false);
 await store.refreshFromGitHub(index);
 assert.equal(store.refreshPublished(index),true);
 assert.equal(store.getDraft(A),null);
 assert.equal(store.getDraft(B).note,'existing review');
 store.saveTags(B,change,'tagged record');
 store.saveDraft(B,draft('updated review'));
 const mixed=store.payload(store.selectedEntries());
 assert.equal(mixed.decisions.length,1);
 assert.equal(mixed.tag_changes.length,1);
 store.saveTags(B,null,'tagged record');
 assert.equal(store.getDraft(B).note,'updated review');
});
test('drafts stay after new tab; only a matching *confirmed Issue* and published decision clears its own draft',async()=>{
 const a=draft('a'),b=draft('b');
 const {store,localStorage}=harness();
 store.saveDraft(A,a);const first=store.makeHandoff(()=>true);
 store.saveDraft(B,b);
 const issue={number:15,state:'open',title:'[Publish Workbench review]',
  user:{login:'e4e421'},body:first.body,
  html_url:'https://github.com/e4e421/supply-chain-rights-observatory/issues/15'};
 const clone=harness({
  'scro.review.drafts.v1':localStorage.getItem('scro.review.drafts.v1'),
  'scro.review.queue.v2':localStorage.getItem('scro.review.queue.v2')
 },async()=>({ok:true,json:async()=>[issue]})).store;
 assert.equal(clone.draftEntries().length,2);
 assert.equal(clone.active(A)?.id,first.id);
 const review=Object.fromEntries(['content_fingerprint','relevance','topics','publisher_confirmed','canonical_url','note']
  .map(k=>[k,a[k]]));
 const index={records:{[A]:{review_state:'current',review:{...review,issue:15}}}};
 // Matching public fields are insufficient proof until the submitted GitHub Issue is verified.
 assert.equal(clone.refreshPublished(index),false);
 assert.equal(clone.getDraft(A)?.note,'a');
 const result=await clone.refreshFromGitHub(index);
 assert.equal(result.matched,1);
 assert.equal(clone.refreshPublished(index),true);
 assert.equal(clone.getDraft(A),null);
 assert.equal(clone.getDraft(B)?.note,'b');
 assert.equal(clone.batches()[0].status,'published');
});
test('GitHub Issue match is checked by owner, title and exact payload before marking Submitted',async()=>{
 let issue;
 const {store}=harness({},async()=>{
  return {ok:true,json:async()=>issue?[issue]:[]};
 });
 store.saveDraft(A,draft('a'));
 const batch=store.makeHandoff(()=>true);
 issue={
  number:123,html_url:'https://github.com/example/issue/123',state:'open',
  title:'[Publish Workbench review]',user:{login:'outsider'},body:batch.body
 };
 let result=await store.refreshFromGitHub({records:{}});
 assert.equal(result.matched,0);
 assert.equal(store.batches()[0].status,'handoff');
 issue.user.login='e4e421';
 issue.body='not the submitted payload';
 result=await store.refreshFromGitHub({records:{}});
 assert.equal(result.matched,0);
 issue.body=batch.body;
 result=await store.refreshFromGitHub({records:{}});
 assert.equal(result.matched,1);
 assert.equal(store.batches()[0].status,'submitted');
 assert.equal(store.cancelHandoff(batch.id),false);
 assert.ok(store.getDraft(A));
});
test('outdated or ambiguous handoffs do not silently publish or erase drafts',()=>{
 const {store}=harness();
 store.saveDraft(C,draft('c'));
 assert.throws(()=>store.makeHandoff(()=>false),/Outdated/);
 assert.equal(store.batches().length,0);
 assert.equal(store.getDraft(C)?.note,'c');
 store.makeHandoff(()=>true);
 const mismatched={records:{[C]:{review_state:'current',review:{note:'different'}}}};
 assert.equal(store.refreshPublished(mismatched),false);
 assert.equal(store.batches()[0].status,'handoff');
 assert.ok(store.getDraft(C));
});

function indexed(published,digest='e'.repeat(64)){
 return {analysis:{content_fingerprint:published.content_fingerprint},
  review_state:'current',review_digest:digest,review:published};
}
test('bulk removal rechecks explicit draft IDs and keeps current, unavailable and handed-off drafts',()=>{
 const {store,localStorage}=harness();
 const active=draft('handoff'),current=draft('current'),stale=draft('stale');
 store.saveDraft(C,active);
 const batch=store.makeHandoff(()=>true);
 store.saveDraft(A,stale);
 store.saveDraft(B,current);
 store.saveDraft(D,draft('outside index'));
 store.saveDraft(E,draft('outdated but not confirmed for removal'));
 store.setSelected(A,true);
 store.setSelected(B,true);
 store.setSelected(D,true);
 const index={records:{[A]:indexed(stale),[B]:indexed(current,current.expected_review_digest),
  [C]:indexed(active),[E]:indexed(draft('published changes'))}};
 assert.equal(store.draftStatus(A,store.getDraft(A),null),'unavailable');
 assert.equal(store.draftStatus(D,store.getDraft(D),index),'unavailable');
 assert.equal(store.draftStatus(A,store.getDraft(A),index),'outdated');
 assert.equal(store.draftStatus(B,store.getDraft(B),index),'current');
 assert.equal(store.removeStaleDrafts([A],null).removed,0);
 let notifications=0;
 store.onChange(()=>{notifications++;});
 const result=store.removeStaleDrafts([A,A,B,C,D,'invalid'],index);
 assert.equal(result.removed,1);
 assert.equal(result.persisted,true);
 assert.equal(notifications,1);
 assert.equal(store.getDraft(A),null);
 assert.equal(store.getDraft(B).note,'current');
 assert.equal(store.getDraft(C).note,'handoff');
 assert.equal(store.getDraft(D).note,'outside index');
 assert.equal(store.getDraft(E).note,'outdated but not confirmed for removal');
 assert.deepEqual([...store.selectedIds()],[E,B,D]);
 assert.equal(store.active(C).id,batch.id);
 assert.equal(JSON.parse(localStorage.getItem(DRAFTS))[A],undefined);
});
test('automatic reconciliation clears matching stale edits and deselects unique stale edits',()=>{
 const {store,localStorage}=harness();
 const a=draft('already published'),b=draft('unpublished note'),c=draft('handoff');
 const e=draft('current draft'),f=draft('unpublished tag edit');
 const tagChange={content_fingerprint:a.content_fingerprint,expected_tag_digest:'d'.repeat(64),tags:['iphone','工廠事故']};
 store.saveDraft(C,c);
 const batch=store.makeHandoff(()=>true);
 store.saveDraft(A,a);store.saveTags(A,tagChange,'mixed');
 store.saveDraft(B,b);
 store.saveDraft(D,draft('outside index'));
 store.saveDraft(E,e);
 store.saveDraft(F,f);store.saveTags(F,{...tagChange,tags:['new']},'different tags');
 for(const rid of [A,B,D,E])store.setSelected(rid,true);
 const index={records:{[A]:indexed(a),[B]:indexed(draft('different note')),[C]:indexed(c),
  [E]:indexed(e,e.expected_review_digest),[F]:indexed(f)},
  record_tags:{[A]:{tags:['工廠事故','iphone'],digest:'e'.repeat(64)},
   [F]:{tags:['iphone'],digest:'e'.repeat(64)}},empty_tag_digest:'0'.repeat(64)};
 let notifications=0;
 store.onChange(()=>{notifications++;});
 const result=store.reconcileStaleDrafts(index);
 assert.equal(result.removed,1);
 assert.equal(result.persisted,true);
 assert.equal(notifications,1);
 assert.equal(store.getDraft(A),null);
 assert.equal(store.getDraft(B).note,'unpublished note');
 assert.equal(store.getDraft(F)._tagChange.tags[0],'new');
 assert.equal(store.active(C).id,batch.id);
 assert.deepEqual([...store.selectedIds()],[D,E]);
 assert.deepEqual(JSON.parse(localStorage.getItem(QUEUE)).selected,[D,E]);
 assert.equal(store.reconcileStaleDrafts(index).removed,0);
 assert.equal(notifications,1);
});
test('cleanup preserves drafts and selection when a storage write fails',()=>{
 const {store,localStorage}=harness();
 const a=draft('already published');
 store.saveDraft(A,a);
 const oldDrafts=localStorage.getItem(DRAFTS),oldQueue=localStorage.getItem(QUEUE);
 const setItem=localStorage.setItem;
 localStorage.setItem=(key,value)=>{
  if(key===DRAFTS)throw Error('storage blocked');
  setItem(key,value);
 };
 let notifications=0;
 store.onChange(()=>{notifications++;});
 const result=store.reconcileStaleDrafts({records:{[A]:indexed(a)}});
 assert.equal(result.removed,0);
 assert.equal(result.persisted,false);
 assert.equal(store.getDraft(A).note,a.note);
 assert.deepEqual([...store.selectedIds()],[A]);
 assert.equal(localStorage.getItem(DRAFTS),oldDrafts);
 assert.equal(localStorage.getItem(QUEUE),oldQueue);
 assert.equal(notifications,0);
});
test('cleanup preserves newer drafts and handoffs from another tab before its storage event',()=>{
 const {store,localStorage}=harness();
 const a=draft('already published');
 store.saveDraft(A,a);
 const secondTab=harness({[DRAFTS]:localStorage.getItem(DRAFTS),[QUEUE]:localStorage.getItem(QUEUE)}).store;
 const newerDraft=draft('new edit');
 secondTab.saveDraft(A,newerDraft);
 const newerBatch=secondTab.makeHandoff(()=>true);
 localStorage.setItem(DRAFTS,JSON.stringify({[A]:newerDraft}));
 localStorage.setItem(QUEUE,JSON.stringify({schema_version:2,selected:[],batches:[newerBatch]}));
 const result=store.removeStaleDrafts([A],{records:{[A]:indexed(a)}});
 assert.equal(result.removed,0);
 assert.equal(JSON.parse(localStorage.getItem(DRAFTS))[A].note,newerDraft.note);
 assert.equal(JSON.parse(localStorage.getItem(QUEUE)).batches[0].id,newerBatch.id);
});
