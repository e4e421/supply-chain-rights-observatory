/* Read-only derived relevance. Failure is disclosed, never silently labelled reviewed. */
(() => {
'use strict';
const root=new URL('./',document.currentScript.src);let data=null,failed=false;
async function fetchIndex(){const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),12000);try{
 const r=await fetch(new URL('data/relevance-index.json',root),{credentials:'omit',cache:'no-store',signal:controller.signal});
 if(!r.ok)throw Error();const s=await r.text();if(s.length>20000000)throw Error();
 const d=JSON.parse(s);if(d.schema_version!==1||!d.records||!d.topics)throw Error();data=d;failed=false;return d;
 }finally{clearTimeout(timer);}}
const ready=fetchIndex().catch(()=>{failed=true;});
const id=r=>r.record_id||r.id;
const get=r=>data?.records[typeof r==='string'?r:id(r)]||null;
const tags=r=>data?.record_tags?.[typeof r==='string'?r:id(r)]?.tags||[];
function apply(r){const d=get(r);if(!d)return r;return {...r,original_topics:r.original_topics||r.topics,topics:d.effective_topics,
 relevance_level:d.analysis.level,rule_version:d.analysis.rule_version,review_state:d.review_state,
 manual_relevance:d.review_state==='current'?d.review.relevance:'',
 publisher_confirmed:d.review_state==='current'&&d.review.publisher_confirmed,
 reviewed_canonical_url:d.review_state==='current'?d.review.canonical_url:null};}
window.SCRO_RELEVANCE=Object.freeze({ready,get,apply,tags,refresh:fetchIndex,included:r=>get(r)?.included!==false,
 get data(){return data;},get failed(){return failed;}});
})();
