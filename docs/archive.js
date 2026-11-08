/* Monthly public JSON archive explorer: all rendering is plain text. */
(() => {
'use strict';
const $=id=>document.getElementById(id),i18n=window.SCRO_I18N||{t:x=>x,onChange:()=>{}},t=x=>i18n.t(x);
let catalog=null,records=[],month='',visible=30,loading=false,failed=false;
const el=(tag,value,cls)=>{const n=document.createElement(tag);if(cls)n.className=cls;n.textContent=value==null?'':String(value);return n};
const safe=x=>{try{const u=new URL(x);return u.protocol==='https:'&&!u.username&&!u.password?u.href:null}catch{return null}};
function dateText(iso){const d=new Date(iso||'');return Number.isNaN(d.getTime())?t('Date unavailable'):new Intl.DateTimeFormat(({en:'en-GB',zh:'zh-TW',de:'de-DE'})[i18n.language]||'en-GB',{year:'numeric',month:'2-digit',day:'2-digit',timeZone:'UTC'}).format(d)}
function selected(){
 const q=$('archive-search').value.trim().toLowerCase(),topic=$('archive-topic').value,from=$('archive-from').value,to=$('archive-to').value;
 const selectedTopics=[...document.querySelectorAll('#archive-multi-topic input:checked')].map(x=>x.value);
 return records.filter(r=>{
  const requested=[...(topic==='all'?[]:[topic]),...selectedTopics];
  if(requested.length&&!requested.some(x=>(r.topics||[]).includes(x)))return false;
  if(from&&String(r.published_at||'').slice(0,10)<from)return false;
  if(to&&String(r.published_at||'').slice(0,10)>to)return false;
  const searchable=[r.title,r.publisher_hint,r.source,r.source_id,r.record_id,r.doi].join(' ').toLowerCase();
  return !q || (window.SCRO_QUERY ? window.SCRO_QUERY.matches(searchable,q) : searchable.includes(q));
 });
}
function render(){
 const list=$('archive-results');list.replaceChildren();const found=selected();
 $('archive-count').textContent=loading?t('Loading archive…'):failed?t('Archive is temporarily unavailable'):String(found.length)+' '+t('matching public records')+' · '+(month||'—')+' · '+t('not verified incidents');
 if(loading||failed||!found.length)list.append(el('p',loading?t('Loading archive…'):failed?t('Archive is temporarily unavailable'):t('No matching records in the selected month.'),'archive-notice'));
 else for(const item of found.slice(0,visible)){
   const card=el('article','','archive-item');
   const a=el('a',item.title||t('Untitled record'),'archive-record-title');
   a.href='./record.html?month='+encodeURIComponent(month)+'&id='+encodeURIComponent(item.record_id);
   const meta=el('p',dateText(item.published_at)+' · '+(item.publisher_hint||t('Publisher not verified'))+' · '+item.record_id,'archive-record-meta');
   card.append(a,meta,el('small',t('Unverified discovery / bibliographic lead'),'archive-evidence'));list.append(card);
 }
 $('archive-show-more').hidden=visible>=found.length||loading||failed;
}
async function fetchJSON(path){const r=await fetch(path,{cache:'no-store',credentials:'omit'});if(!r.ok)throw Error('HTTP '+r.status);return r.json()}
async function changeMonth(value){
 if(!/^\d{4}-\d{2}$/.test(value))return;
 month=value;loading=true;failed=false;records=[];visible=30;render();
 try{
  const m=(catalog.months||[]).find(x=>x.month===value);
  if(!m||!Array.isArray(m.files)||m.records>25000)throw Error('Unsupported month');
  const shards=await Promise.all(m.files.map(f=>{
   if(!/^\d{4}-\d{2}-\d{4}\.json$/.test(f.file))throw Error('Invalid filename');
   return fetchJSON('./data/archive/'+f.file);
  }));
  records=shards.flatMap(x=>x.records||[]);
  if(records.length!==m.records)throw Error('Invalid record count');
  records=records.filter(r=>r&&/^[0-9a-f]{18}$/.test(r.record_id)&&typeof r.title==='string');
 }catch(_){failed=true;}
 finally{loading=false;render()}
}
function safeCSV(value){let s=String(value==null?'':Array.isArray(value)?value.join('; '):value).replace(/[\u0000-\u001f\u007f]/g,' ');if(/^\s*[=+\-@]/.test(s))s="'"+s;return '"'+s.replace(/"/g,'""')+'"'}
function exportCSV(){
 const columns=['record_id','title','published_at','first_seen','source','publisher_hint','source_id','kind','evidence_status','topics','url','doi'];
 const csv=[columns,...selected().map(x=>columns.map(k=>x[k]??''))].map(row=>row.map(safeCSV).join(',')).join('\r\n');
 const url=URL.createObjectURL(new Blob(['\ufeff'+csv],{type:'text/csv;charset=utf-8'}));
 const link=document.createElement('a');link.href=url;link.download='observatory-'+month+'-selection.csv';document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),500);
}
async function init(){
 try{
  catalog=await fetchJSON('./data/archive/catalog.json');
  if(catalog.schema_version!==1||!Array.isArray(catalog.months))throw Error('Invalid catalog');
  const select=$('archive-month');select.replaceChildren();
  for(const m of catalog.months){
   if(!/^\d{4}-\d{2}$/.test(m.month))continue;
   const option=document.createElement('option');option.value=m.month;option.textContent=m.month+' ('+m.records+')';select.append(option);
  }
  if(catalog.months.length)await changeMonth(catalog.months[0].month);
  else $('archive-count').textContent=t('Archive has no records yet.');
 }catch(_){failed=true;render()}
}
$('archive-month').addEventListener('change',e=>changeMonth(e.target.value));
for(const id of ['archive-search','archive-topic','archive-from','archive-to']) $(id).addEventListener(id==='archive-search'?'input':'change',()=>{visible=30;render()});
document.querySelectorAll('#archive-multi-topic input').forEach(x=>x.addEventListener('change',()=>{visible=30;render()}));
$('archive-show-more').addEventListener('click',()=>{visible+=30;render()});
$('archive-export').addEventListener('click',exportCSV);
i18n.onChange(()=>render());
init();
})();