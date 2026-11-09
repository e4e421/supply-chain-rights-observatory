import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {webcrypto} from 'node:crypto';

const source=fs.readFileSync('docs/workbench/review-store.js','utf8');
const A='a'.repeat(18),B='b'.repeat(18),C='c'.repeat(18);
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
test('drafts stay after new tab; only a matching published decision clears its own draft',()=>{
 const a=draft('a'),b=draft('b');
 const {store,localStorage}=harness();
 store.saveDraft(A,a);const first=store.makeHandoff(()=>true);
 store.saveDraft(B,b);
 const clone=harness({
  'scro.review.drafts.v1':localStorage.getItem('scro.review.drafts.v1'),
  'scro.review.queue.v2':localStorage.getItem('scro.review.queue.v2')
 }).store;
 assert.equal(clone.draftEntries().length,2);
 assert.equal(clone.active(A)?.id,first.id);
 const review=Object.fromEntries(['content_fingerprint','relevance','topics','publisher_confirmed','canonical_url','note']
  .map(k=>[k,a[k]]));
 const index={records:{[A]:{review_state:'current',review:{...review,issue:15}}}};
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
