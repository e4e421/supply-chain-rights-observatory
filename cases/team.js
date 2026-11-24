'use strict';
(() => {
  const $ = id => document.getElementById(id);
  let config, token='', uid='', role='', version=null, publication=null, active='', paged=[], next='', finished=false, checked='';
  let templates=new Map(), generation=0, selection=0, pageGeneration=0;
  const note = txt => { $('status').textContent=txt; };
  const bind = (id,evt,fn) => $(id).addEventListener(evt, e => {
    if(evt==='submit')e.preventDefault();
    Promise.resolve().then(()=>fn(e)).catch(err=>note(err.message));
  });
  const root=()=> 'projects/'+config.project+'/databases/(default)/documents';
  async function api(endpoint,method='GET',body,missing=false) {
    const response=await fetch('https://firestore.googleapis.com/v1/'+root()+endpoint,{
      method,cache:'no-store',credentials:'omit',headers:{Authorization:'Bearer '+token,'Content-Type':'application/json'},
      ...(body===undefined?{}:{body:JSON.stringify(body)})});
    if(missing && response.status===404)return null;
    if(!response.ok)throw Error(response.status===401?'登入已過期，請重新登入。':response.status===403?'此帳號沒有這項權限。':response.status===409||response.status===412?'版本已變更，請重新選取案件後比對。':'讀寫失敗（HTTP '+response.status+'），請保留草稿並重新載入版本。');
    return response.json();
  }
  const fields = row=>Object.fromEntries(Object.entries(row).map(([k,v])=>[k,{stringValue:v}]));
  const data = doc=>Object.fromEntries(Object.entries(doc?.fields||{}).map(([k,v])=>[k,v.stringValue??v.integerValue??v.booleanValue??'']));
  const precondition = doc=>doc ? {updateTime:doc.updateTime}:{exists:false};
  const blank=()=>({id:'',title:{en:'',zh:''},place:'TW',rights_holders:{en:'',zh:''},focus:{en:'',zh:''},follow_up_on:null,follow_up:{en:'',zh:''},gap:'response',source_checked_on:new Date().toISOString().slice(0,10),sources:[],timeline:[]});
  function fill(row, draft) {
    $('case-id').value=row.id; $('case-id').readOnly=Boolean(active);
    $('title-zh').value=row.title.zh;$('title-en').value=row.title.en;
    $('gap').value=row.gap;$('due').value=row.follow_up_on||'';
    $('owner').value=draft.owner||'';$('note').value=draft.note||'';
    $('payload').value=JSON.stringify(row,null,2);$('review').textContent='';checked='';$('approve').disabled=true;
  }
  function getPublic(){
    const row=JSON.parse($('payload').value);
    row.id=$('case-id').value;row.title={en:$('title-en').value,zh:$('title-zh').value};
    row.gap=$('gap').value;row.follow_up_on=$('due').value||null;
    return row;
  }
  function required(row) {
    if(!/^[a-z][a-z0-9-]{1,70}$/.test(row.id)||!row.sources?.length||!row.timeline?.length)throw Error('請填寫有效 ID，並加入至少一項來源及進展。');
    for(const k of ['title','focus','rights_holders','follow_up'])if(!row[k]?.en?.trim()||!row[k]?.zh?.trim())throw Error('請在完整公開草稿填妥中英欄位 '+k);
  }
  async function openCase(id) {
    const n=++selection;active=id;version=null;publication=null;$('draft').inert=true;
    try {
      let draft={},row=templates.get(id)||blank();
      if(id){
        const [d,p]=await Promise.all([api('/caseDrafts/'+id,'GET',undefined,true),api('/casePublications/'+id,'GET',undefined,true)]);
        if(n!==selection)return;
        version=d;publication=p;draft=data(d);const previous=data(p);
        row=draft.payload?JSON.parse(draft.payload):previous.state==='approved'?JSON.parse(previous.payload):row;
      }
      if(n===selection)fill(row,draft);
    } finally {if(n===selection)$('draft').inert=false;}
  }
  function addOption(id,label) {
    if(![...$('case-select').options].some(o=>o.value===id))$('case-select').add(new Option(label,id));
  }
  async function start(){
    const result=await fetch('config.json',{cache:'no-store'});config=await result.json();
    if(!config.project||!config.apiKey){note('正式 Firebase 專案尚未連接。公開案件與來源可正常瀏覽。');return;}
    $('login').hidden=false;note('請使用已獲授權的研究帳號登入。');
  }
  bind('login','submit',async(e)=>{
    const f=e.target;
    const result=await fetch('https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key='+encodeURIComponent(config.apiKey),{
      method:'POST',credentials:'omit',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:f.email.value,password:f.password.value,returnSecureToken:true})});
    f.password.value='';if(!result.ok)throw Error('帳號或密碼未獲接受。');
    const auth=await result.json();token=auth.idToken;uid=auth.localId;
    try {
      role=data(await api('/members/'+encodeURIComponent(uid))).role;
      if(!['researcher','editor'].includes(role))throw Error('此帳號尚未獲研究權限。');
      const publicData=await (await fetch('../data/cases.json',{cache:'no-store'})).json();
      templates=new Map(publicData.cases.map(c=>[c.id,c]));$('case-select').replaceChildren();
      for(const c of templates.values())addOption(c.id,c.title.zh);
      let cursor='';
      do{const page=await api('/caseDrafts?pageSize=100'+(cursor?'&pageToken='+encodeURIComponent(cursor):''));
        for(const d of page.documents||[]){const row=JSON.parse(data(d).payload);addOption(row.id,row.title.zh||row.id);}cursor=page.nextPageToken||'';}while(cursor);
      $('login').hidden=true;$('desk').hidden=false;$('editor').hidden=role!=='editor';
      await openCase($('case-select').value);await resetPool();note('已登入 · '+role);
    } catch(err){token='';uid='';role='';$('desk').hidden=true;$('login').hidden=false;throw err;}
  });
  bind('logout','click',()=>{generation++;selection++;token='';uid='';role='';location.reload();});
  bind('case-select','change',()=>openCase($('case-select').value));
  bind('new-case','click',()=>{ $('case-select').selectedIndex=-1;return openCase(''); });
  bind('append','click',()=>{
    const row=getPublic();const url=new URL($('source-url').value);
    if(url.protocol!=='https:'||url.username||url.password)throw Error('來源需要公開 HTTPS 網址。');
    const publisher=$('publisher').value.trim(),actor=$('actor').value.trim(),en=$('entry-en').value.trim(),zh=$('entry-zh').value.trim();
    if(!publisher||!actor||!en||!zh)throw Error('請填妥來源、行動者及中英進展。');
    let src=row.sources.find(s=>s.url===url.href);
    if(!src){src={id:'src-'+crypto.randomUUID(),publisher,url:url.href,published_on:$('source-date').value||null,record_id:null,feed_published_at:null,first_seen_at:new Date().toISOString()};row.sources.push(src);}
    row.timeline.push({on:$('entry-date').value||null,actor,kind:$('kind').value,source:src.id,text:{en,zh}});
    $('payload').value=JSON.stringify(row,null,2);$('entry').open=false;
    for(const field of ['actor','entry-en','entry-zh','entry-date','source-date','source-url','publisher'])$(field).value='';
    note('進展已加入，請儲存草稿。');
  });
  bind('draft','submit',async()=>{
    const row=getPublic();required(row);const id=row.id,n=selection;
    const update={name:root()+'/caseDrafts/'+id,fields:fields({payload:JSON.stringify(row),note:$('note').value,owner:$('owner').value,updatedBy:uid})};
    await api(':commit','POST',{writes:[{update,currentDocument:precondition(version)}]});
    if(n!==selection)return;addOption(id,row.title.zh);$('case-select').value=id;await openCase(id);note('私有草稿已儲存。');
  });
  bind('preview','click',()=>{
    const candidate=JSON.stringify(getPublic());if(candidate!==data(version).payload)throw Error('請先儲存並重讀目前草稿。');
    checked=candidate;$('review').textContent=JSON.stringify(JSON.parse(checked),null,2);$('approve').disabled=false;
  });
  async function decide(state){
    if(!active)throw Error('請先選取案件。');
    const id=active, initial=selection, payload=state==='approved'?JSON.stringify(getPublic()):'';
    if(state==='approved'&&(!checked||checked!==payload||payload!==data(version).payload))throw Error('請重新核對公開草稿。');
    if(state==='withdrawn'&&!confirm('撤回 '+id+' 的公開版本？下次發布時生效。'))return;
    const v=crypto.randomUUID(), path=root()+'/casePublications/'+id;
    const values=fields({state,payload,reviewer:uid,version:v});
    await api(':commit','POST',{writes:[
      {update:{name:path,fields:values},currentDocument:precondition(publication)},
      {update:{name:path+'/versions/'+v,fields:values},currentDocument:{exists:false}}
    ]});
    if(initial===selection){await openCase(id);note('審核決定已記錄，等待下一次成功發布。');}
  }
  bind('approve','click',()=>decide('approved'));bind('withdraw','click',()=>decide('withdrawn'));
  function showRows(){
    const query=$('find').value.trim().toLowerCase();$('rows').replaceChildren();
    const filtered=paged.filter(row=>JSON.stringify(row).toLowerCase().includes(query));
    for(const row of filtered){const li=document.createElement('li'),d=document.createElement('details'),s=document.createElement('summary'),pre=document.createElement('pre');
      s.textContent=row.title||row.case_id||row.id;pre.className='notes';pre.textContent=JSON.stringify(row,null,2);d.append(s,pre);
      if($('pool').value==='caseSuggestions' && row.proposal?.disposition==='new_development'){
        for(const point of row.proposal.points){
          const source=(row.sources||[]).find(x=>x.id===point.source_id);
          if(!source)continue;
          const button=document.createElement('button');button.type='button';button.textContent='帶入待核草稿 · '+point.actor;
          button.addEventListener('click',async()=>{
            try{
              if(active!==row.proposal.case_id)throw Error('請先選取對應案件 '+row.proposal.case_id+'，再帶入建議。');
              $('actor').value=point.actor;$('kind').value=point.kind;$('entry-date').value=point.date||'';
              $('source-url').value=source.url;$('publisher').value='';$('source-date').value='';
              $('entry-en').value=point.summary_en;$('entry-zh').value=point.summary_zh;$('entry').open=true;
              $('publisher').focus();note('請核對引文、填入發布者，再加入草稿。');
            }catch(err){note(err.message);}
          });d.append(button);
        }
      }
      li.append(d);$('rows').append(li);}
    $('loaded').textContent='已載入 '+paged.length+' 筆，符合 '+filtered.length+' 筆。';
    $('more').disabled=finished;
  }
  async function loadPage(){
    if(finished)return;
    const gen=generation,view=++pageGeneration,pool=$('pool').value;$('more').disabled=true;
    try {
      const page=await api('/'+pool+'?pageSize=50'+(next?'&pageToken='+encodeURIComponent(next):''));
      if(gen!==generation||view!==pageGeneration||pool!==$('pool').value)return;
      const docs=(page.documents||[]).map(d=>{const x=data(d);return {id:d.name.split('/').pop(),...(x.payload?JSON.parse(x.payload):x)};});
      paged.push(...docs);next=page.nextPageToken||'';finished=!next;showRows();
    } finally {if(gen===generation&&view===pageGeneration)$('more').disabled=finished;}
  }
  function resetPool(){generation++;paged=[];next='';finished=false;showRows();return loadPage();}
  bind('more','click',loadPage);bind('pool','change',resetPool);bind('find','input',showRows);
  start().catch(()=>note('無法讀取後台設定，請稍後重試。'));
})();
