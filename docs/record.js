/* Month-scoped, read-only public record viewer. All third-party text is textContent. */
(() => {
'use strict';
const root=document.getElementById('record-content');
const t=x=>window.SCRO_I18N?window.SCRO_I18N.t(x):x;
const date=(value,withTime=false)=>window.SCRO_I18N?.formatDate(value,withTime)||'—';
const q=new URL(location.href).searchParams,id=q.get('id')||'',month=q.get('month')||'';
const txt=(tag,x)=>{const n=document.createElement(tag);n.textContent=x==null?'':String(x);return n};
const link=(url,label)=>{
 try{const u=new URL(url);if(u.protocol!=='https:'||u.username||u.password)return txt('span',label);
 const a=txt('a',label);a.href=u.href;a.target='_blank';a.rel='noopener noreferrer';return a
 }catch{return txt('span',label)}
};
let item=null,error=false;
function show(){
 root.replaceChildren();
 if(error||!item){root.append(txt('p',t('Record unavailable. Verify its identifier and month.')));return}
 const title=txt('h1',item.title),meta=txt('p',item.record_id+' · '+date(item.published_at));
 title.setAttribute('lang','und');
 const evidence=txt('p',t('Unverified discovery / bibliographic lead'));
 const dl=document.createElement('dl');
 const fields=[
 [t('Publication date (UTC)'),date(item.published_at)],[t('First observed'),date(item.first_seen,true)],
 [t('Monitoring query'),item.source],
 [t('Publisher credit (unverified)'),item.publisher_hint||t('Unknown')],
 [t('Evidence class'),item.evidence_status],
 [t('Topic identifiers'),(item.topics||[]).join('; ')],[t('DOI'),item.doi]
 ];
 for(const [name,value]of fields){if(!value)continue;dl.append(txt('dt',name),txt('dd',value))}
 const original=document.createElement('p');original.append(link(item.url,t('Open original discovery link')));
 root.append(title,meta,evidence,dl,original);
}
async function read(path){const r=await fetch(path,{credentials:'omit',cache:'no-store'});if(!r.ok)throw Error();return r.json()}
(async()=>{
 try{
  if(!/^[a-f0-9]{18}$/.test(id)||!/^\d{4}-\d{2}$/.test(month))throw Error();
  const catalog=await read('./data/archive/catalog.json');
  const section=(catalog.months||[]).find(x=>x.month===month);
  if(!section)throw Error();
  for(const file of section.files||[]){
    if(!/^\d{4}-\d{2}-\d{4}\.json$/.test(file.file))throw Error();
    const shard=await read('./data/archive/'+file.file);
    item=(shard.records||[]).find(x=>x.record_id===id);
    if(item)break;
  }
  if(!item)throw Error();
 }catch(_){error=true}
 show();
 window.SCRO_I18N?.onChange(()=>show());
})();
})();