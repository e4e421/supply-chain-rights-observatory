/* One in-place review surface. Local drafts never masquerade as published decisions. */
(() => {
'use strict';
const R=window.SCRO_RELEVANCE,I=window.SCRO_I18N||{language:'en',onChange:()=>{}};
if(!R)return;
const D={
'Pending review changes':['待發布變更清單','Ausstehende Prüfänderungen'],
'Review all edits before publication. Drafts are stored only in this browser.':['發布前請逐筆檢查；所有草稿僅儲存於本機瀏覽器。','Änderungen vor Veröffentlichung prüfen. Entwürfe sind nur im Browser gespeichert.'],
'No saved changes yet. Select an article and choose Save local draft.':['尚無已儲存變更。請點選新聞並按「儲存本機草稿」。','Noch keine Änderungen. Datensatz auswählen und lokalen Entwurf speichern.'],
'Relevance':['相關性','Relevanz'],
'Topics':['主題標記','Themen'],
'Publisher':['出版者核對','Herausgeber'],
'Public note':['公開審核備註','Öffentliche Prüfnotiz'],
'Source URL':['原文連結','Original-URL'],
'Edit draft':['返回修改','Entwurf bearbeiten'],
'Remove draft':['移除草稿','Entwurf entfernen'],
'Remove this local draft?':['確定移除此筆本機草稿？','Diesen lokalen Entwurf entfernen?'],
'Use suggested topics':['沿用規則建議的主題','Regelvorschläge beibehalten'],
'Not confirmed':['未確認','Nicht bestätigt'],
'Confirmed':['已確認','Bestätigt'],
'No public note':['未填寫公開備註','Keine öffentliche Notiz'],
'Local draft is outdated':['草稿需要重新確認','Entwurf muss erneut geprüft werden'],
'Published review has changed. Reopen and save again.':['正式審核狀態已變動，請重新開啟並儲存草稿。','Veröffentlichte Prüfung geändert; Entwurf öffnen und erneut speichern.'],
'Too many changes for one Issue (maximum 25). Export your draft and submit smaller groups.':['超過每批 25 筆限制；請匯出備份後分批提交。','Mehr als 25 Änderungen. Entwürfe exportieren und in kleineren Gruppen einreichen.'],
'Batch too large for a prefilled GitHub link. Export JSON, then paste the content into a GitHub publication Issue.':['此批次超出 GitHub 預填網址長度；請匯出 JSON，再貼入新的 GitHub 發布 Issue。','Batch zu groß für den vorausgefüllten GitHub-Link. JSON exportieren und in ein GitHub-Issue einfügen.'],
'The complete review batch will be sent to GitHub; no changes are omitted.':['所有待發布草稿會一起送往 GitHub，不會默默漏掉任何一筆。','Der gesamte Batch wird an GitHub übermittelt; keine Änderungen werden ausgelassen.'],
'Draft removed from this browser.':['已從此瀏覽器移除草稿。','Entwurf aus diesem Browser entfernt.'],
'Record unavailable from current index':['目前索引找不到此紀錄','Datensatz im aktuellen Index nicht gefunden'],

'Relevance & review':['相關性與審核','Relevanz & Prüfung'],
'All relevance levels':['所有相關性','Alle Relevanzstufen'],
'High relevance':['高相關','Hohe Relevanz'],
'Needs context':['待判讀','Kontext prüfen'],
'Low relevance':['低相關','Geringe Relevanz'],
'Unreviewed':['尚未人工審核','Ungeprüft'],
'Published reviews':['已發布審核','Veröffentlichte Prüfungen'],
'Excluded records':['已排除紀錄','Ausgeschlossene Datensätze'],
'Export review batch':['匯出審核批次','Prüfungen exportieren'],
'Publish through GitHub':['透過 GitHub 發布','Über GitHub veröffentlichen'],
'local drafts; not published':['筆本機草稿；尚未發布','lokale Entwürfe; nicht veröffentlicht'],
'Keyword analysis unavailable; records remain visible.':['關鍵字分析未載入，原始紀錄仍保留。','Schlagwortanalyse nicht verfügbar; Originaldaten bleiben sichtbar.'],
'Select a record to review it here.':['選取新聞，即可在這裡判讀與標記。','Datensatz auswählen und hier prüfen.'],
'Title only — no full text was retrieved.':['只分析標題；未擷取全文。','Nur Titel; kein Volltext abgerufen.'],
'Title and permitted abstract':['標題與允許使用的摘要','Titel und zulässige Metadaten-Zusammenfassung'],
'Relevance is not claim verification.':['相關性不等於主張已查證。','Relevanz bestätigt keine Behauptung.'],
'Matched rules and keywords':['命中規則與關鍵字','Regeln und Schlagwörter'],
'Specific HRDD or labour policy':['特定人權盡職調查或勞動法規','Spezifische Sorgfalts- oder Arbeitsregulierung'],
'Supply chain and labour context':['供應鏈與勞工脈絡共現','Lieferketten- und Arbeitskontext'],
'Governance and rights context':['治理與權利脈絡共現','Governance- und Rechtekontext'],
'Context incomplete':['脈絡不足，需人工判讀','Kontext unvollständig'],
'Insufficient textual evidence':['文字資訊不足，不等於確定不相關','Unzureichende Textsignale'],
'Relevance decision':['研究相關性決策','Relevanzentscheidung'],
'Include':['納入','Aufnehmen'],
'Exclude':['排除','Ausschließen'],
'Review needed':['待確認','Prüfung erforderlich'],
'Confirm topic tags':['人工確認主題標記','Themen manuell bestätigen'],
'Leave unchecked to retain rule suggestions.':['未勾選時沿用規則建議。','Nicht auswählen, um Regelvorschläge zu behalten.'],
'Publisher identity confirmed':['已核對出版歸屬','Herausgeber überprüft'],
'Original HTTPS URL (required for publisher confirmation)':['原始 HTTPS 網址（確認出版者時必填）','Original-HTTPS-URL (für Herausgeberbestätigung erforderlich)'],
'Public review note (no private data)':['公開審核說明（勿填私密資料）','Öffentliche Prüfnotiz (keine privaten Daten)'],
'Save local draft':['儲存本機草稿','Lokalen Entwurf speichern'],
'Discard local draft':['捨棄本機草稿','Lokalen Entwurf verwerfen'],
'Draft saved in this browser only.':['已儲存於此瀏覽器，尚未公開發布。','Nur in diesem Browser gespeichert, nicht veröffentlicht.'],
'Browser storage blocked; export the batch before leaving.':['瀏覽器封鎖儲存，離開前請匯出批次。','Browserspeicher blockiert; vor dem Verlassen exportieren.'],
'Enter a valid public HTTPS original URL.':['請填入不含帳密的公開 HTTPS 原文網址。','Gültige öffentliche HTTPS-Originaladresse eingeben.'],
'Similar keyword patterns — not confirmed same events':['相近關鍵字文章；未認定為同一事件','Ähnliche Schlagwörter; kein bestätigtes gemeinsames Ereignis'],
'Open related record':['開啟相關紀錄','Verwandten Datensatz öffnen'],
'No sufficiently similar records.':['暫無足夠相近的紀錄。','Keine hinreichend ähnlichen Datensätze.'],
'Published decision':['已發布決策','Veröffentlichte Entscheidung'],
'Review needs renewal: source text changed.':['原始文字已改變，舊審核需重新確認。','Quelltext geändert; erneute Prüfung erforderlich.'],
'Submitting the GitHub Issue authorizes automatic publication after validation. Use public review notes only; no allegation is verified.':['提交 GitHub Issue 即授權系統驗證後自動公開審核結果。備註只能包含公開資訊，並不代表指控已證實。','Das Einreichen des GitHub-Issues autorisiert die automatische Veröffentlichung nach Prüfung. Nur öffentliche Notizen; Vorwürfe gelten nicht als verifiziert.'],
'No drafts to submit.':['目前沒有待提交草稿。','Keine Entwürfe zum Einreichen.'],
'The batch was downloaded. Paste the JSON into a GitHub publication Issue with the correct title.':['批次已下載，請以正確標題建立 GitHub 發布 Issue 並貼入 JSON。','Batch heruntergeladen. JSON in ein GitHub-Publikations-Issue mit korrektem Titel einfügen.'],
'Please refresh and re-review stale drafts before submission.':['草稿對應資料已變動，請重新整理並再次判讀。','Veraltete Entwürfe vor dem Einreichen erneut prüfen.'],
'Awaiting independently labelled validation sample':['等待研究者獨立標記驗證樣本','Unabhängig annotierte Validierung ausstehend'],
'Download unlabelled validation sample':['下載未標記驗證樣本','Unbeschriftete Validierungsstichprobe herunterladen'],
'Local draft not yet published':['本機草稿，尚未發布','Lokaler, unveröffentlichter Entwurf'],
'The first three decisions will publish automatically after the GitHub Issue is submitted and validated. Remaining drafts stay in this browser.':['提交 GitHub Issue 且驗證成功後，前三筆決策將自動公開；其餘草稿保留於此瀏覽器。','Nach Einreichen des GitHub-Issues und erfolgreicher Prüfung werden die ersten drei Entscheidungen automatisch veröffentlicht. Weitere Entwürfe bleiben lokal.']
};
const t=k=>I.language==='en'?k:(D[k]?.[I.language==='zh'?0:1]||k);
const el=(tag,value='',cls='')=>{const n=document.createElement(tag);n.textContent=value;if(cls)n.className=cls;return n;};
const KEY='scro.review.drafts.v1';let draft={},callback=()=>{},current=null,signature='',feedback='';
try{const d=JSON.parse(localStorage.getItem(KEY)||'{}');if(d&&typeof d==='object'&&!Array.isArray(d))draft=d;}catch{}
const root=el('section','','rv-panel');root.id='review-panel';root.setAttribute('aria-label','Relevance and review');
document.querySelector('.wb-source-check')?.before(root);
const tools=el('div','','rv-tools'),filter=el('select');filter.id='rv-filter';filter.setAttribute('aria-label',t('Relevance & review'));
for(const [value,label]of [['all','All relevance levels'],['high','High relevance'],['review','Needs context'],['low','Low relevance'],['unreviewed','Unreviewed'],['reviewed','Published reviews'],['excluded','Excluded records']]){const o=el('option',t(label));o.value=value;o.dataset.label=label;filter.append(o);}
const initial=new URL(location.href).searchParams.get('relevance');if([...filter.options].some(o=>o.value===initial))filter.value=initial;
const count=el('span','','rv-draft-count'),exportButton=el('button'),send=el('button');exportButton.type=send.type='button';
filter.addEventListener('change',()=>{const u=new URL(location.href);if(filter.value==='all')u.searchParams.delete('relevance');else u.searchParams.set('relevance',filter.value);history.replaceState(null,'',u.pathname+u.search+u.hash);callback();});
tools.append(filter,count);document.querySelector('.wb-results-head')?.after(tools);
const queue=el('details','','rv-queue');queue.id='rv-queue';
const summary=el('summary','','rv-queue-summary');summary.id='rv-queue-title';queue.append(summary);
const queueIntro=el('p','','rv-queue-intro'),queueList=el('ol','','rv-queue-list');
queueList.id='rv-queue-list';queueList.setAttribute('aria-label',t('Pending review changes'));
const queueActions=el('div','','rv-queue-actions');
exportButton.id='rv-export-batch';send.id='rv-publish-batch';
queueActions.append(exportButton,send);queue.append(queueIntro,queueList,queueActions);
queue.open=Object.keys(draft).length>0;
tools.after(queue);
const info=el('p','','rv-message');info.id='rv-feedback';info.setAttribute('role','status');info.setAttribute('aria-live','polite');queue.after(info);
function persist(){try{localStorage.setItem(KEY,JSON.stringify(draft));return true;}catch{return false;}}
function pending(){return Object.entries(draft).filter(([rid,d])=>/^[a-f0-9]{18}$/.test(rid)&&d&&typeof d==='object'&&!Array.isArray(d));}
const decisionLabel=value=>t(({include:'Include',exclude:'Exclude',needs_review:'Review needed'})[value]||value||'Unreviewed');
function draftCurrent(rid,d){
 const indexed=R.get(rid);
 return !!(indexed&&d.content_fingerprint===indexed.analysis.content_fingerprint
   &&d.expected_review_digest===indexed.review_digest);
}
function tagLabels(value){
 if(!Array.isArray(value))return t('Use suggested topics');
 return value.map(k=>(R.data?.topics?.[k]||{})[I.language]||(R.data?.topics?.[k]||{}).en||k).join(', ')||'—';
}
function makeChange(label,before,after){
 const p=el('p','','rv-change');
 p.append(el('span',t(label)+': ','rv-change-label'));
 if(before!==after)p.append(el('span',before,'rv-change-before'),el('span',' → ','rv-change-arrow'));
 p.append(el('strong',after,'rv-change-after'));return p;
}
function renderQueue(){
 const entries=pending();
 summary.textContent=t('Pending review changes')+' ('+entries.length+')';
 queueIntro.textContent=t('Review all edits before publication. Drafts are stored only in this browser.');
 queueList.setAttribute('aria-label',t('Pending review changes'));
 queueList.replaceChildren();
 if(!entries.length)queueList.append(el('li',t('No saved changes yet. Select an article and choose Save local draft.'),'rv-queue-empty'));
 for(const [rid,d] of entries){
  const indexed=R.get(rid),source=window.SCRO_WORKBENCH?.getRecord(rid);
  const prior=indexed?.review_state==='current'?indexed.review:null;
  const stale=!draftCurrent(rid,d),item=el('li','','rv-queue-item');
  item.dataset.reviewId=rid;
  const head=el('div','','rv-queue-item-head');
  head.append(el('strong',String(d._title||source?.title||rid).slice(0,200),'rv-queue-title'));
  const badge=el('span',stale?t('Local draft is outdated'):decisionLabel(d.relevance),'rv-queue-status'+(stale?' rv-queue-stale':''));
  head.append(badge);
  item.append(head,el('small','Record ID: '+rid,'rv-queue-id'));
  if(!indexed)item.append(el('p',t('Record unavailable from current index'),'rv-alert'));
  else{
   item.append(makeChange('Relevance',prior?decisionLabel(prior.relevance):t('Unreviewed'),decisionLabel(d.relevance)));
   item.append(makeChange('Topics',prior?tagLabels(prior.topics):t('Use suggested topics'),tagLabels(d.topics)));
   item.append(makeChange('Publisher',prior?.publisher_confirmed?t('Confirmed'):t('Not confirmed'),d.publisher_confirmed?t('Confirmed'):t('Not confirmed')));
   if(d.canonical_url)item.append(makeChange('Source URL',prior?.canonical_url||'—',d.canonical_url));
   if(d.note)item.append(makeChange('Public note',prior?.note||t('No public note'),d.note));
   if(stale)item.append(el('p',t('Published review has changed. Reopen and save again.'),'rv-alert'));
  }
  const actions=el('div','','rv-queue-item-actions');
  const edit=el('button',t('Edit draft'),'rv-action');edit.type='button';edit.dataset.editRecord=rid;
  edit.addEventListener('click',()=>{
   window.dispatchEvent(new CustomEvent('scro:select-record',{detail:{record_id:rid}}));
  });
  const remove=el('button',t('Remove draft'),'rv-action rv-action-danger');remove.type='button';remove.dataset.removeRecord=rid;
  remove.addEventListener('click',()=>{
   if(!window.confirm(t('Remove this local draft?')))return;
   delete draft[rid];persist();feedback='Draft removed from this browser.';updateTools();
   if(current&&(current.record_id||current.id)===rid)inspect(current,true);
  });
  actions.append(edit,remove);item.append(actions);queueList.append(item);
 }
 const overflow=entries.length>25;
 const stale=entries.some(([rid,d])=>!draftCurrent(rid,d));
 if(overflow)queueList.prepend(el('li',t('Too many changes for one Issue (maximum 25). Export your draft and submit smaller groups.'),'rv-alert'));
 else if(stale)queueList.prepend(el('li',t('Please refresh and re-review stale drafts before submission.'),'rv-alert'));
 send.disabled=!entries.length||overflow||stale||R.failed;
}
function updateTools(){
 for(const o of filter.options)o.textContent=t(o.dataset.label);
 filter.setAttribute('aria-label',t('Relevance & review'));
 count.textContent=pending().length+' '+t('local drafts; not published');
 exportButton.textContent=t('Export review batch');send.textContent=t('Publish through GitHub');
 exportButton.disabled=!pending().length;
 info.textContent=R.failed?t('Keyword analysis unavailable; records remain visible.'):t(feedback);
 renderQueue();
}
function download(name,data){const u=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json;charset=utf-8'}));const a=el('a');a.href=u;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),1000);}
function batch(limit=25){return {schema_version:1,decisions:pending().slice(0,limit).map(([record_id,d])=>({record_id,...d}))};}
exportButton.addEventListener('click',()=>download('scro-review-batch.json',batch()));
send.addEventListener('click',()=>{
 const entries=pending();if(!entries.length){feedback='No drafts to submit.';updateTools();return;}
 if(entries.some(([rid,d])=>!R.get(rid)||d.content_fingerprint!==R.get(rid).analysis.content_fingerprint||d.expected_review_digest!==R.get(rid).review_digest)){feedback='Please refresh and re-review stale drafts before submission.';updateTools();return;}
 const body='SCRO_PUBLISH_V2\n```json\n'+JSON.stringify(batch(3))+'\n```';
 const u=new URL('https://github.com/e4e421/supply-chain-rights-observatory/issues/new');u.searchParams.set('title','[Publish Workbench review]');u.searchParams.set('body',body);
 if(u.href.length>7500){download('scro-review-batch.json',batch(3));feedback='The batch was downloaded. Paste the JSON into a GitHub publication Issue with the correct title.';updateTools();return;}
 feedback='The first three decisions will publish automatically after the GitHub Issue is submitted and validated. Remaining drafts stay in this browser.';updateTools();window.open(u.href,'_blank','noopener,noreferrer');
});
const reason={specific_hrdd_policy:'Specific HRDD or labour policy',supply_and_labour_context:'Supply chain and labour context',governance_and_rights:'Governance and rights context',incomplete_context:'Context incomplete',insufficient_text_evidence:'Insufficient textual evidence'};
function field(label,node){const wrap=el('label','','rv-field');wrap.append(el('span',t(label)),node);return wrap;}
function inspect(item,force=false){
 current=item;const rid=item&&(item.record_id||item.id);const data=rid&&R.get(rid);
 const next=(rid||'none')+':'+I.language+':'+(data?.review_digest||'');if(!force&&next===signature)return;signature=next;
 root.replaceChildren(el('h3',t('Relevance & review')));
 if(!item){root.append(el('p',t('Select a record to review it here.')));return;}
 if(!data){root.append(el('p',t('Keyword analysis unavailable; records remain visible.')));return;}
 const a=data.analysis,labels={high:'High relevance',review:'Needs context',low:'Low relevance'};
 root.append(el('strong',t(labels[a.level]),'rv-level rv-'+a.level),el('p',t(a.scope==='title_only'?'Title only — no full text was retrieved.':'Title and permitted abstract'),'rv-small'),el('p',t('Relevance is not claim verification.'),'rv-small'));
 const why=el('details');why.append(el('summary',t('Matched rules and keywords')),el('p',t(reason[a.reason]||a.reason)));
 why.append(el('small',a.rule_version));const hits=el('ul');for(const h of a.matched.slice(0,25))hits.append(el('li',h.term+' ['+h.field+']'));why.append(hits);root.append(why);
 if(data.review_state==='current')root.append(el('p',t('Published decision')+': '+data.review.relevance+' · '+data.review.reviewed_at,'rv-small'));
 if(data.review_state==='stale')root.append(el('p',t('Review needs renewal: source text changed.'),'rv-alert'));
 if(draft[rid])root.append(el('p',t('Local draft not yet published'),'rv-alert'));
 const existing=draft[rid]||((data.review_state==='current')?data.review:{});
 const decision=el('select');decision.id='rv-decision';for(const [value,label]of [['needs_review','Review needed'],['include','Include'],['exclude','Exclude']]){const o=el('option',t(label));o.value=value;decision.append(o);}decision.value=existing.relevance||'needs_review';root.append(field('Relevance decision',decision));
 const tagBox=el('details');tagBox.append(el('summary',t('Confirm topic tags')));
 const enabled=el('input');enabled.type='checkbox';enabled.id='rv-topics-confirm';enabled.checked=Array.isArray(existing.topics);tagBox.append(field('Confirm topic tags',enabled),el('p',t('Leave unchecked to retain rule suggestions.'),'rv-small'));
 const checks=[];for(const [key,names]of Object.entries(R.data.topics)){const x=el('input');x.type='checkbox';x.value=key;x.name='rv-topic';x.checked=(existing.topics||data.effective_topics).includes(key);const label=el('label','','rv-checkbox');label.append(x,el('span',names[I.language]||names.en));tagBox.append(label);checks.push(x);}root.append(tagBox);
 const verified=el('input');verified.type='checkbox';verified.id='rv-publisher';verified.checked=existing.publisher_confirmed===true;
 const original=el('input');original.type='url';original.id='rv-original';original.maxLength=2048;original.value=existing.canonical_url||'';
 const publisher=el('details');publisher.append(el('summary',t('Publisher identity confirmed')),field('Publisher identity confirmed',verified),field('Original HTTPS URL (required for publisher confirmation)',original));root.append(publisher);
 const note=el('textarea');note.id='rv-note';note.maxLength=400;note.rows=2;note.value=existing.note||'';root.append(field('Public review note (no private data)',note));
 const save=el('button',t('Save local draft')),discard=el('button',t('Discard local draft'));save.type=discard.type='button';save.id='rv-save';discard.id='rv-discard';
 save.addEventListener('click',()=>{let url=original.value.trim()||null;
  try{if(url){const u=new URL(url);if(u.protocol!=='https:'||u.username||u.password||!u.hostname.includes('.')||u.hostname==='127.0.0.1'||u.hostname.endsWith('.local'))throw Error();}if(verified.checked&&!url)throw Error();}catch{feedback='Enter a valid public HTTPS original URL.';updateTools();return;}
  draft[rid]={content_fingerprint:a.content_fingerprint,expected_review_digest:data.review_digest,relevance:decision.value,topics:enabled.checked?checks.filter(x=>x.checked).map(x=>x.value):null,publisher_confirmed:verified.checked,canonical_url:url,note:note.value.trim()};
  feedback=persist()?'Draft saved in this browser only.':'Browser storage blocked; export the batch before leaving.';updateTools();inspect(item,true);
 });
 discard.addEventListener('click',()=>{delete draft[rid];persist();feedback='';updateTools();inspect(item,true);});
 const actions=el('div','','rv-actions');actions.append(save,discard);root.append(actions,el('p',t('Submitting the GitHub Issue authorizes automatic publication after validation. Use public review notes only; no allegation is verified.'),'rv-small'));
 const similar=el('details');similar.append(el('summary',t('Similar keyword patterns — not confirmed same events')));
 if(!data.similar?.length)similar.append(el('p',t('No sufficiently similar records.')));
 for(const match of data.similar||[]){const row=el('p');const link=el('a',t('Open related record')+' '+match.record_id);const u=new URL(location.href);u.searchParams.set('scope','all');u.searchParams.set('record',match.record_id);for(const key of ['q','from','to','topics','relevance','offset','kind','evidence'])u.searchParams.delete(key);link.href=u.href;row.append(link,el('small',' · '+match.shared_terms.join(', ')));similar.append(row);}root.append(similar);
 const sample=el('a',t('Download unlabelled validation sample'));sample.href='../data/relevance-validation-sample.json';sample.download='scro-validation-sample.json';root.append(el('p',t('Awaiting independently labelled validation sample'),'rv-small'),sample);
}
function includes(item){const d=R.get(item);if(!d)return true;const v=filter.value;
 if(v==='excluded')return !d.included;
 if(!d.included)return false;
 if(v==='unreviewed')return d.review_state!=='current';
 if(v==='reviewed')return d.review_state==='current';
 return v==='all'||d.analysis.level===v;
}
function refresh(){updateTools();inspect(current,true);}
I.onChange(refresh);updateTools();inspect(null);
window.SCRO_REVIEW=Object.freeze({connect:f=>{callback=f;},inspect,includes,refresh});
})();
