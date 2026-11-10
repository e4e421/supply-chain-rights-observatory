/* One in-place review surface. Local drafts never masquerade as published decisions. */
(() => {
'use strict';
const R=window.SCRO_RELEVANCE,I=window.SCRO_I18N||{language:'en',onChange:()=>{}};
const S=window.SCRO_REVIEW_STORE;
if(!R||!S)return;
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
'The first three decisions will publish automatically after the GitHub Issue is submitted and validated. Remaining drafts stay in this browser.':['提交 GitHub Issue 且驗證成功後，前三筆決策將自動公開；其餘草稿保留於此瀏覽器。','Nach Einreichen des GitHub-Issues und erfolgreicher Prüfung werden die ersten drei Entscheidungen automatisch veröffentlicht. Weitere Entwürfe bleiben lokal.'],
"Select for publication":["選取發布","Zur Veröffentlichung auswählen"],
"Selected for publication":["已勾選待發布","Zur Veröffentlichung ausgewählt"],
"Continue to GitHub to submit review":["前往 GitHub 提交審核","Weiter zu GitHub, um die Prüfung einzureichen"],
"A prefilled GitHub form opens in a new tab. Selected changes are published after you submit the issue and validation succeeds.":["將在新分頁開啟 GitHub 預填表單。提交 Issue 且驗證通過後，才會發布已勾選的變更。","Ein vorausgefülltes GitHub-Formular öffnet sich in einem neuen Tab. Die ausgewählten Änderungen werden nach dem Einreichen des Issues und erfolgreicher Prüfung veröffentlicht."],
"Export selected batch":["匯出選取的批次","Ausgewählten Batch exportieren"],
"No selected drafts. Select the records you want to publish.":["尚未勾選紀錄。請選取本次要發布的變更。","Keine Entwürfe ausgewählt. Gewünschte Einträge markieren."],
"You can only submit the explicitly selected records.":["只會提交您明確勾選的紀錄。","Nur ausdrücklich ausgewählte Einträge werden eingereicht."],
"Handoff pending":["等待確認 Issue 已建立","Issue-Erstellung noch unbestätigt"],
"Submitted":["已建立 Issue，等待發布","Issue eingereicht, Veröffentlichung ausstehend"],
"Published":["已發布","Veröffentlicht"],
"Needs attention":["需要處理","Handlungsbedarf"],
"Check GitHub and publication status":["查核 GitHub 與發布狀態","GitHub- und Veröffentlichungsstatus prüfen"],
"Publication history":["發布紀錄與處理狀態","Veröffentlichungsverlauf"],
"GitHub status check failed; no draft was lost.":["GitHub 狀態查核失敗；草稿未遺失。","GitHub-Statusprüfung fehlgeschlagen; kein Entwurf ging verloren."],
"Open GitHub handoff":["重新開啟 GitHub 提交頁","GitHub-Einreichung öffnen"],
"View GitHub Issue":["查看 GitHub Issue","GitHub-Issue öffnen"],
"Reset unsubmitted handoff":["重設未提交的交接","Nicht eingereichten Übergang zurücksetzen"],
"Confirm that you did not submit the GitHub Issue before resetting.":["請先確認您確實沒有在 GitHub 建立 Issue，才可重設。","Nur zurücksetzen, wenn das GitHub-Issue nicht erstellt wurde."],
"An earlier batch already includes this record. Check its publication status first.":["此紀錄已包含在先前提交批次中，請先查核狀態。","Ein früherer Batch enthält diesen Datensatz. Status zuerst prüfen."],
"Only public notes may be submitted.":["審核備註僅限公開資訊。","Nur öffentliche Prüfnotizen dürfen eingereicht werden."],
"The Issue has not been confirmed yet; this is not a published review.":["尚未確認 Issue 已建立，也未正式發布。","Die Issue-Erstellung ist noch nicht bestätigt; keine Veröffentlichung."],
"No publishing history in this browser.":["此瀏覽器尚無提交紀錄。","Kein Veröffentlichungsverlauf in diesem Browser."],
"Changes in this batch":["此批次的變更","Änderungen in diesem Batch"],
"Saved in this browser only":["僅儲存於此瀏覽器","Nur in diesem Browser gespeichert"],
"Refresh or reopen to see newly published decisions.":["請重新載入頁面，查看最新發布的決策。","Seite neu laden, um neue Veröffentlichungen zu sehen."],
"Reload current review index":["重新載入審核索引","Prüfindex neu laden"],
"Review Queue":["審核變更清單","Prüfwarteschlange"],
"Editing tools are public; only the GitHub owner may publish.":["編輯介面可公開瀏覽，只有授權的 GitHub 擁有者能正式發布。","Bearbeitung ist öffentlich sichtbar; veröffentlichen darf nur der berechtigte GitHub-Inhaber."],
"Ready to publish":["可發布的草稿","Bereit zur Veröffentlichung"],
"Draft selection is stored only in your browser.":["勾選狀態只儲存在您的瀏覽器。","Die Auswahl bleibt nur in Ihrem Browser."],
};

const t=k=>I.language==='en'?k:(D[k]?.[I.language==='zh'?0:1]||k);
const el=(tag,value='',cls='')=>{const n=document.createElement(tag);n.textContent=value;if(cls)n.className=cls;return n;};
const ASSET_ROOT=new URL('./',document.currentScript.src);
let callback=()=>{},current=null,signature='',feedback='';
const root=el('section','','rv-panel');root.id='review-panel';
root.setAttribute('aria-label','Relevance and review');
document.getElementById('wb-detail')?.after(root);

const tools=el('div','','rv-tools');
const filter=el('select');filter.id='rv-filter';filter.setAttribute('aria-label',t('Relevance & review'));
for(const [value,label] of [
 ['all','All relevance levels'],['high','High relevance'],['review','Needs context'],
 ['low','Low relevance'],['unreviewed','Unreviewed'],['reviewed','Published reviews'],
 ['excluded','Excluded records']]){
 const option=el('option',t(label));option.value=value;option.dataset.label=label;filter.append(option);
}
const initial=new URL(location.href).searchParams.get('relevance');
if([...filter.options].some(x=>x.value===initial))filter.value=initial;
filter.addEventListener('change',()=>{
 const u=new URL(location.href);
 if(filter.value==='all')u.searchParams.delete('relevance');else u.searchParams.set('relevance',filter.value);
 history.replaceState(null,'',u.pathname+u.search+u.hash);callback();
});
const count=el('span','','rv-draft-count');
tools.append(filter,count);
document.querySelector('.wb-results-head')?.after(tools);

const queue=el('details','','rv-queue');queue.id='rv-queue';queue.open=S.draftEntries().length>0;
const summary=el('summary','','rv-queue-summary');summary.id='rv-queue-title';queue.append(summary);
const introduction=el('p','','rv-queue-intro');
const queueList=el('ol','','rv-queue-list');queueList.id='rv-queue-list';
queueList.setAttribute('aria-label',t('Pending review changes'));
const queueActions=el('div','','rv-queue-actions');
const exportButton=el('button');exportButton.id='rv-export-batch';exportButton.type='button';
const send=el('button');send.id='rv-publish-batch';send.type='button';
const submitHint=el('p','','rv-submit-hint');submitHint.id='rv-submit-hint';
send.setAttribute('aria-describedby',submitHint.id);
queueActions.append(submitHint,exportButton,send);
queue.append(introduction,queueList,queueActions);
tools.after(queue);
const info=el('p','','rv-message');info.id='rv-feedback';
info.setAttribute('role','status');info.setAttribute('aria-live','polite');queue.after(info);

const history=el('section','','rv-history');history.id='rv-history';
const historyHead=el('div','','rv-history-head');
historyHead.append(el('h3',t('Publication history')));
const statusBtn=el('button',t('Check GitHub and publication status'),'rv-action');
statusBtn.id='rv-check-status';statusBtn.type='button';
historyHead.append(statusBtn);
const historyList=el('div','','rv-history-list');historyList.id='rv-history-list';
history.append(historyHead,historyList);
queue.after(history);
const decisionLabel=value=>t(({include:'Include',exclude:'Exclude',needs_review:'Review needed'})[value]||value||'Unreviewed');
function tagLabels(value){
 if(!Array.isArray(value))return t('Use suggested topics');
 return value.map(k=>(R.data?.topics?.[k]||{})[I.language]||(R.data?.topics?.[k]||{}).en||k).join(', ')||'—';
}
function makeChange(label,before,after){
 const p=el('p','','rv-change');
 p.append(el('span',t(label)+': ','rv-change-label'));
 if(before!==after)p.append(el('span',before,'rv-change-before'),el('span',' → ','rv-change-arrow'));
 p.append(el('strong',after,'rv-change-after'));
 return p;
}
function draftCurrent(rid,d){
 const indexed=R.get(rid);
 return !!(indexed&&d.content_fingerprint===indexed.analysis.content_fingerprint
    &&d.expected_review_digest===indexed.review_digest);
}
function download(name,obj){
 const url=URL.createObjectURL(new Blob([JSON.stringify(obj,null,2)],{type:'application/json;charset=utf-8'}));
 const a=el('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();
 setTimeout(()=>URL.revokeObjectURL(url),1000);
}
function renderQueue(){
 const entries=S.draftEntries(),selected=S.selectedEntries();
 summary.textContent=t('Review Queue')+' ('+entries.length+')';
 introduction.textContent=t('You can only submit the explicitly selected records.')+' '+t('Draft selection is stored only in your browser.');
 count.textContent=String(selected.length)+' / '+String(entries.length)+' '+t('Selected for publication');
 queueList.replaceChildren();
 if(!entries.length)queueList.append(el('li',t('No saved changes yet. Select an article and choose Save local draft.'),'rv-queue-empty'));
 for(const [rid,d] of entries){
  const active=S.active(rid),indexed=R.get(rid),stale=!draftCurrent(rid,d);
  const prior=indexed?.review_state==='current'?indexed.review:null;
  const li=el('li','','rv-queue-item');li.dataset.reviewId=rid;
  const top=el('div','','rv-queue-item-head');
  const check=el('input');check.type='checkbox';check.className='rv-review-select';
  check.dataset.selectRecord=rid;check.checked=S.selectedIds().includes(rid);
  check.disabled=!!active||stale;check.setAttribute('aria-label',t('Select for publication')+' '+rid);
  check.addEventListener('change',()=>S.setSelected(rid,check.checked));
  top.append(check,el('strong',String(d._title||window.SCRO_WORKBENCH?.getRecord(rid)?.title||rid).slice(0,200),'rv-queue-title'));
  top.append(el('span',active?t(({handoff:'Handoff pending',submitted:'Submitted',published:'Published',needs_attention:'Needs attention'})[active.status]||active.status):stale?t('Local draft is outdated'):decisionLabel(d.relevance),'rv-queue-status'));
  li.append(top,el('small','Record ID: '+rid,'rv-queue-id'));
  if(indexed){
    li.append(makeChange('Relevance',prior?decisionLabel(prior.relevance):t('Unreviewed'),decisionLabel(d.relevance)));
    li.append(makeChange('Topics',prior?tagLabels(prior.topics):t('Use suggested topics'),tagLabels(d.topics)));
    li.append(makeChange('Publisher',prior?.publisher_confirmed?t('Confirmed'):t('Not confirmed'),d.publisher_confirmed?t('Confirmed'):t('Not confirmed')));
    if(d.canonical_url)li.append(makeChange('Source URL',prior?.canonical_url||'—',d.canonical_url));
    if(d.note)li.append(makeChange('Public note',prior?.note||t('No public note'),d.note));
  }
  if(stale)li.append(el('p',t('Published review has changed. Reopen and save again.'),'rv-alert'));
  if(active)li.append(el('p',t('An earlier batch already includes this record. Check its publication status first.'),'rv-small'));
  const actions=el('div','','rv-queue-item-actions');
  const edit=el('button',t('Edit draft'),'rv-action');edit.type='button';edit.dataset.editRecord=rid;
  edit.disabled=!!active;edit.addEventListener('click',()=>{
   window.dispatchEvent(new CustomEvent('scro:select-record',{detail:{record_id:rid}}));
  });
  const remove=el('button',t('Remove draft'),'rv-action rv-action-danger');
  remove.type='button';remove.dataset.removeRecord=rid;remove.disabled=!!active;
  remove.addEventListener('click',()=>{
   if(!window.confirm(t('Remove this local draft?')))return;
   if(S.removeDraft(rid)){feedback='Draft removed from this browser.';refresh();}
  });
  actions.append(edit,remove);li.append(actions);queueList.append(li);
 }
 if(selected.length>25)queueList.prepend(el('li',t('Too many changes for one Issue (maximum 25). Export your draft and submit smaller groups.'),'rv-alert'));
 const staleSelected=selected.some(([id,d])=>!draftCurrent(id,d));
 exportButton.textContent=t('Export selected batch');
 send.textContent=t('Continue to GitHub to submit review');
 submitHint.textContent=t('A prefilled GitHub form opens in a new tab. Selected changes are published after you submit the issue and validation succeeds.');
 exportButton.disabled=!selected.length;
 send.disabled=!selected.length||selected.length>25||staleSelected||R.failed;
 info.textContent=R.failed?t('Keyword analysis unavailable; records remain visible.'):t(feedback);
}
function renderHistory(){
 historyHead.querySelector('h3').textContent=t('Publication history');
 statusBtn.textContent=t('Check GitHub and publication status');
 historyList.replaceChildren();
 const batches=S.batches();
 if(!batches.length)historyList.append(el('p',t('No publishing history in this browser.'),'rv-small'));
 for(const batch of batches.slice(0,25)){
  const row=el('div','','rv-history-item');row.dataset.batchId=batch.id;
  row.append(el('strong',t(({handoff:'Handoff pending',submitted:'Submitted',published:'Published',needs_attention:'Needs attention',cancelled:'Cancelled'})[batch.status]||batch.status)));
  row.append(el('small',batch.ids.length+' '+t('Changes in this batch')+' · '+(batch.created_at||'')));
  const actions=el('div','','rv-queue-item-actions');
  const link=el('a',batch.issue_url?t('View GitHub Issue'):t('Open GitHub handoff'));
  link.href=batch.issue_url||batch.url;link.target='_blank';link.rel='noopener noreferrer';actions.append(link);
  if(batch.status==='handoff'){
   const reset=el('button',t('Reset unsubmitted handoff'),'rv-action');
   reset.type='button';reset.addEventListener('click',()=>{
    if(!window.confirm(t('Confirm that you did not submit the GitHub Issue before resetting.')))return;
    S.cancelHandoff(batch.id);
   });
   actions.append(reset);
  }
  row.append(actions);historyList.append(row);
 }
}
function updateTools(){
 for(const option of filter.options)option.textContent=t(option.dataset.label);
 filter.setAttribute('aria-label',t('Relevance & review'));
 renderQueue();renderHistory();
}
exportButton.addEventListener('click',()=>{
 if(S.selectedEntries().length)download('scro-selected-review-batch.json',S.payload(S.selectedEntries()));
});
send.addEventListener('click',()=>{
 try{
  const entry=S.makeHandoff(draftCurrent);feedback='The Issue has not been confirmed yet; this is not a published review.';
  updateTools();window.open(entry.url,'_blank','noopener,noreferrer');
 }catch(e){
  feedback=e.message==='No selected drafts'?'No selected drafts. Select the records you want to publish.':
   e.message==='Outdated review draft'?'Please refresh and re-review stale drafts before submission.':
   'Batch too large for a prefilled GitHub link. Export JSON, then paste the content into a GitHub publication Issue.';
  updateTools();
 }
});
statusBtn.addEventListener('click',async()=>{
 statusBtn.disabled=true;
 try{
  const indexURL=new URL('../data/relevance-index.json',ASSET_ROOT).href;
  const response=await fetch(indexURL,{credentials:'omit',cache:'no-store'});
  if(!response.ok)throw Error('Index unavailable');
  const index=await response.json();
  await S.refreshFromGitHub(index);
  S.refreshPublished(index);
  feedback='Refresh or reopen to see newly published decisions.';
 }catch(_){feedback='GitHub status check failed; no draft was lost.';}
 finally{statusBtn.disabled=false;refresh();}
});
function field(label,node){
 const wrap=el('label','','rv-field');wrap.append(el('span',t(label)),node);return wrap;
}
const reason={specific_hrdd_policy:'Specific HRDD or labour policy',supply_and_labour_context:'Supply chain and labour context',governance_and_rights:'Governance and rights context',incomplete_context:'Context incomplete',insufficient_text_evidence:'Insufficient textual evidence'};
function inspect(item,force=false){
 current=item;const rid=item&&(item.record_id||item.id);const data=rid&&R.get(rid);
 const next=(rid||'none')+':'+I.language+':'+(data?.review_digest||'');
 if(!force&&next===signature)return;signature=next;
 root.replaceChildren(el('h3',t('Relevance & review')));
 if(!item){root.append(el('p',t('Select a record to review it here.')));return;}
 if(!data){root.append(el('p',t('Keyword analysis unavailable; records remain visible.')));return;}
 const a=data.analysis,locked=!!S.active(rid);
 root.append(el('strong',t(({high:'High relevance',review:'Needs context',low:'Low relevance'})[a.level]||a.level),'rv-level rv-'+a.level));
 root.append(el('p',t(a.scope==='title_only'?'Title only — no full text was retrieved.':'Title and permitted abstract'),'rv-small'),
   el('p',t('Relevance is not claim verification.'),'rv-small'));
 const why=el('details');why.append(el('summary',t('Matched rules and keywords')),
   el('p',t(reason[a.reason]||a.reason)),el('small',a.rule_version));
 const hits=el('ul');
 for(const h of a.matched.slice(0,25))hits.append(el('li',h.term+' ['+h.field+']'));
 why.append(hits);root.append(why);
 if(data.review_state==='current')root.append(el('p',t('Published decision')+': '+data.review.relevance+' · '+data.review.reviewed_at,'rv-small'));
 if(data.review_state==='stale')root.append(el('p',t('Review needs renewal: source text changed.'),'rv-alert'));
 if(locked)root.append(el('p',t('An earlier batch already includes this record. Check its publication status first.'),'rv-alert'));
 const existing=S.getDraft(rid)||(data.review_state==='current'?data.review:{});
 const decision=el('select');decision.id='rv-decision';
 for(const [value,label] of [['needs_review','Review needed'],['include','Include'],['exclude','Exclude']]){
  const option=el('option',t(label));option.value=value;decision.append(option);
 }
 decision.value=existing.relevance||'needs_review';root.append(field('Relevance decision',decision));
 const tags=el('details');tags.append(el('summary',t('Confirm topic tags')));
 const enabled=el('input');enabled.type='checkbox';enabled.id='rv-topics-confirm';
 enabled.checked=Array.isArray(existing.topics);
 tags.append(field('Confirm topic tags',enabled),el('p',t('Leave unchecked to retain rule suggestions.'),'rv-small'));
 const checks=[];
 for(const [key,names] of Object.entries(R.data.topics)){
  const box=el('input');box.type='checkbox';box.value=key;box.name='rv-topic';
  box.checked=(existing.topics||data.effective_topics).includes(key);
  const label=el('label','','rv-checkbox');
  label.append(box,el('span',names[I.language]||names.en));
  tags.append(label);checks.push(box);
 }
 root.append(tags);
 const confirmed=el('input');confirmed.type='checkbox';confirmed.id='rv-publisher';
 confirmed.checked=existing.publisher_confirmed===true;
 const url=el('input');url.type='url';url.id='rv-original';url.maxLength=2048;url.value=existing.canonical_url||'';
 const publisher=el('details');publisher.append(el('summary',t('Publisher identity confirmed')),
  field('Publisher identity confirmed',confirmed),
  field('Original HTTPS URL (required for publisher confirmation)',url));
 root.append(publisher);
 const note=el('textarea');note.id='rv-note';note.maxLength=400;note.rows=2;note.value=existing.note||'';
 root.append(field('Public review note (no private data)',note));
 const save=el('button',t('Save local draft'));save.type='button';save.id='rv-save';
 const discard=el('button',t('Discard local draft'));discard.type='button';discard.id='rv-discard';
 for(const input of [decision,enabled,...checks,confirmed,url,note])input.disabled=locked;
 save.disabled=discard.disabled=locked;
 save.addEventListener('click',()=>{
  let canonical=url.value.trim()||null;
  try{
   if(canonical){
    const u=new URL(canonical);
    if(u.protocol!=='https:'||u.username||u.password||!u.hostname.includes('.')||
      u.hostname==='127.0.0.1'||u.hostname.endsWith('.local'))throw Error();
   }
   if(confirmed.checked&&!canonical)throw Error();
  }catch(_){feedback='Enter a valid public HTTPS original URL.';updateTools();return;}
  const saved=S.saveDraft(rid,{
   content_fingerprint:a.content_fingerprint,expected_review_digest:data.review_digest,
   relevance:decision.value,topics:enabled.checked?checks.filter(x=>x.checked).map(x=>x.value):null,
   publisher_confirmed:confirmed.checked,canonical_url:canonical,note:note.value.trim(),
   _title:String(item.title||'').slice(0,200),_savedAt:new Date().toISOString()
  });
  feedback=saved?'Draft saved in this browser only.':'Browser storage blocked; export the batch before leaving.';
  queue.open=true;refresh();
 });
 discard.addEventListener('click',()=>{
  if(S.removeDraft(rid)){feedback='Draft removed from this browser.';refresh();}
 });
 const actions=el('div','','rv-actions');actions.append(save,discard);root.append(actions);
 root.append(el('p',t('Submitting the GitHub Issue authorizes automatic publication after validation. Use public review notes only; no allegation is verified.'),'rv-small'));
 const similar=el('details');similar.append(el('summary',t('Similar keyword patterns — not confirmed same events')));
 if(!data.similar?.length)similar.append(el('p',t('No sufficiently similar records.')));
 for(const match of data.similar||[]){
  const line=el('p'),link=el('a',t('Open related record')+' '+match.record_id);
  const u=new URL(location.href);u.searchParams.set('scope','all');u.searchParams.set('record',match.record_id);
  for(const k of ['q','from','to','topics','relevance','offset','kind','evidence'])u.searchParams.delete(k);
  link.href=u.href;line.append(link,el('small',' · '+match.shared_terms.join(', ')));similar.append(line);
 }
 root.append(similar);
 const sample=el('a',t('Download unlabelled validation sample'));
 sample.href=new URL('../data/relevance-validation-sample.json',ASSET_ROOT).href;
 sample.download='scro-validation-sample.json';
 root.append(el('p',t('Awaiting independently labelled validation sample'),'rv-small'),sample);
}
function includes(item){
 const d=R.get(item);if(!d)return true;
 const v=filter.value;
 if(v==='excluded')return !d.included;
 if(!d.included)return false;
 if(v==='unreviewed')return d.review_state!=='current';
 if(v==='reviewed')return d.review_state==='current';
 return v==='all'||d.analysis.level===v;
}
function refresh(){updateTools();inspect(current,true);}
S.onChange(refresh);
I.onChange(refresh);
R.ready.then(()=>{S.refreshPublished(R.data);refresh();});
refresh();inspect(null);
window.SCRO_REVIEW=Object.freeze({connect:f=>{callback=f;},inspect,includes,refresh});
})();
