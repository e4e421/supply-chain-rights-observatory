/* Professional research workbench. Same-origin public data only, no keys or remote services. */
(() => {
'use strict';
const $ = id => document.getElementById(id);
const baseI18n = window.SCRO_I18N || {language:'en', t:x=>x, onChange:()=>{}};
const locale = () => baseI18n.language || 'en';
const L = {
zh:{
'Skip to results':'跳至搜尋結果','Visitor portal':'一般訪客首頁','Research Workbench':'專業研究工作台',
'Public metadata · not verified incidents':'公開資料 · 非已證實事件','Latest records':'最新情報','Historical records':'歷史紀錄',
'Collection status':'擷取狀態','Last successful update (Taipei)':'最後成功更新（臺北）','Source directory':'來源目錄',
'Methodology':'研究方法','Dataset':'資料範圍','Latest':'最新情報','Archive month':'歷史月份','All available':'全部可取得紀錄',
'Sort by':'排序方式','Published: newest':'發布時間：最新','Published: oldest':'發布時間：最早',
'Observed: newest':'首次擷取：最新','Title: A–Z':'標題：A–Z','Publisher: A–Z':'出版者：A–Z',
'Reset':'重設','Filters':'篩選條件','Combinable criteria':'可組合條件','Published from':'發布起始日',
'Through':'截至日期','Record type':'紀錄類型','All types':'所有類型','Academic metadata':'學術書目',
'Discovery leads':'研究線索','Evidence class':'證據分類','Any evidence class':'所有證據分類',
'Unverified discovery':'未驗證線索','Bibliographic record':'書目記錄',
'Research themes (OR)':'研究議題（擇一符合）','Visible columns':'顯示欄位','Date':'日期',
'Title':'標題','Publisher':'出版者','Topics':'主題','Type':'類型','Evidence':'證據',
'Record ID':'紀錄編號','Quick views':'快速視圖','Labour & remedy':'勞工與補救',
'EU policy & HRDD':'歐盟政策與人權盡職調查','Academic research':'學術研究',
'Research records':'研究紀錄','AND / OR / quoted phrases supported':'支援 AND、OR 與引號片語',
'Density':'顯示密度','Compact':'緊密','Comfortable':'舒適','Export CSV':'匯出 CSV',
'Show more':'顯示更多','Record inspector':'紀錄詳情','Clear selection':'清除選取',
'Select a record to inspect its provenance, dates and evidence status.':'選取紀錄後檢查來源、日期與證據狀態。',
'Daily data checks':'每日資料查核','Loading checks…':'讀取查核資訊…',
'Workspace & sharing':'工作區與分享',
'Saved views stay in this browser. Sharing a URL shares its search terms; do not include private data.':'儲存視圖僅保留於此瀏覽器。分享網址會揭露搜尋條件，請勿輸入私密資料。',
'Save current view':'儲存目前視圖','Choose a saved view':'選擇已儲存視圖',
'Delete saved view':'刪除已儲存視圖','Copy shareable link':'複製分享連結','Research integrity':'研究完整性',
'Discovery records are not verified human-rights violations. Source reachability is not evidence of credibility.':'研究線索不等於已確認人權違規；網站可連線也不代表來源可信。',
'Methods & limitations':'方法與限制','Language':'語言','Search records':'搜尋紀錄',
'Select website language':'選擇網站語言','Scrollable research results table':'可捲動的研究結果表格',
'Loading public records…':'正在讀取公開紀錄…','Loading months…':'讀取月份…',
'Search titles, publishers, DOI, record IDs…':'搜尋標題、出版者、DOI、紀錄編號…',
'/ search · J/K navigate · Enter details · Esc clear':'/ 搜尋 · J/K 切換 · Enter 詳情 · Esc 清除',
'Operational (technical)':'正常（技術狀態）','Partial sources':'部分來源異常',
'Collection failed':'擷取失敗','Not started':'尚未開始','Unavailable':'無法取得',
'No results':'沒有符合的紀錄','No records in this scope':'此範圍沒有紀錄',
'Records shown':'筆結果','Records loaded':'筆已載入','Scope: latest snapshot':'範圍：最新快照',
'Scope: archive month':'範圍：歷史月份','Scope: combined catalogue':'範圍：合併查詢',
'All available archive shards loaded.':'已讀取所有可取得的歷史分片。',
'Partial archive scope: only recent shards loaded. Narrow the month or use the canonical archive for full analysis.':'歷史資料只載入近期分片；請縮小月份範圍，或使用原始封存檔進行完整研究。',
'Archive could not be loaded; results are not complete.':'歷史資料無法載入；結果不完整。',
'Loading historical records…':'正在讀取歷史紀錄…',
'Last collection':'最近擷取','Source review needed':'來源待審查',
'Licence review pending':'授權審查待處理','Curated references':'收錄參考來源',
'Editorial status':'編輯審查狀態','Reachability':'連線狀態',
'Not independently verified':'尚未獨立查證','Publisher credit is unverified.':'出版者資訊未經獨立查證。',
'No incident event ID has been assigned.':'尚未建立經查核的事件編號。',
'Original discovery link':'原始線索連結','Open DOI':'開啟 DOI','Publication date':'發布日期',
'First observed':'首次觀測','Monitoring query':'監測查詢','Publisher hint':'出版者線索',
'Publisher verified':'出版者已查核','No':'否','Yes':'是','Source type':'資料類型',
'Screening status':'初篩狀態','Event ID':'事件編號','Not assigned':'尚未指派',
'Topics (preliminary)':'主題（初步分類）','Source inspection':'來源查核',
'Use the original source to verify all substantive claims.':'請查閱原始資料以確認實質主張。',
'No source-health report available.':'尚無可用來源健康報告。','Sources requiring review':'待審查來源',
'Licences pending':'授權待核對','Last source probe':'最近來源連線測試',
'Reachability does not verify publication quality.':'可連線不代表內容品質已核實。',
'View saved':'視圖已儲存','View limit reached (12)':'已達儲存上限（12）',
'View name':'視圖名稱','Saved view removed':'已刪除儲存視圖',
'Shareable link copied':'分享連結已複製','Unable to copy automatically; copy the address shown.':'無法自動複製，請複製顯示的網址。',
'Date range is reversed.':'日期範圍前後相反。',
'Data could not be loaded. Check the GitHub Pages deployment.':'資料載入失敗；請檢查 GitHub Pages 部署。',
'Source unavailable':'來源不明','No selected record':'尚未選取紀錄','No active filters':'尚無篩選條件',
'Publication title is shown in its original language.':'出版標題保留原始語言。',
'All records are public discovery metadata, not a verified population of incidents.':'所有紀錄均為公開研究線索，不代表已驗證事件母體。'
},
de:{
'Skip to results':'Zu den Suchergebnissen','Visitor portal':'Besucherportal','Research Workbench':'Forschungsarbeitsplatz',
'Public metadata · not verified incidents':'Öffentliche Metadaten · keine bestätigten Vorfälle',
'Latest records':'Aktuelle Meldungen','Historical records':'Historische Datensätze',
'Collection status':'Erfassungsstatus','Last successful update (Taipei)':'Letzte Aktualisierung (Taipeh)',
'Source directory':'Quellenverzeichnis','Methodology':'Methodik','Dataset':'Datenbestand',
'Latest':'Aktuell','Archive month':'Archivmonat','All available':'Alle verfügbaren',
'Sort by':'Sortieren nach','Published: newest':'Veröffentlicht: neueste','Published: oldest':'Veröffentlicht: älteste',
'Observed: newest':'Erfasst: neueste','Title: A–Z':'Titel: A–Z','Publisher: A–Z':'Herausgeber: A–Z',
'Reset':'Zurücksetzen','Filters':'Filter','Combinable criteria':'Kombinierbare Kriterien',
'Published from':'Veröffentlicht ab','Through':'Bis','Record type':'Datensatztyp',
'All types':'Alle Typen','Academic metadata':'Wissenschaftliche Metadaten',
'Discovery leads':'Recherchehinweise','Evidence class':'Evidenzkategorie','Any evidence class':'Alle Evidenzkategorien',
'Unverified discovery':'Ungeprüfter Hinweis','Bibliographic record':'Bibliografischer Nachweis',
'Research themes (OR)':'Forschungsthemen (ODER)','Visible columns':'Sichtbare Spalten','Date':'Datum',
'Title':'Titel','Publisher':'Herausgeber','Topics':'Themen','Type':'Typ','Evidence':'Evidenz',
'Record ID':'Datensatz-ID','Quick views':'Schnellansichten','Labour & remedy':'Arbeitsrechte & Abhilfe',
'EU policy & HRDD':'EU-Recht & menschenrechtliche Sorgfalt',
'Academic research':'Wissenschaftliche Forschung','Research records':'Forschungsdatensätze',
'AND / OR / quoted phrases supported':'AND, OR und exakte Phrasen in Anführungszeichen',
'Density':'Dichte','Compact':'Kompakt','Comfortable':'Komfortabel','Export CSV':'CSV exportieren',
'Show more':'Mehr anzeigen','Record inspector':'Datensatzdetails','Clear selection':'Auswahl löschen',
'Select a record to inspect its provenance, dates and evidence status.':'Datensatz auswählen, um Herkunft, Daten und Evidenzstatus zu prüfen.',
'Daily data checks':'Tägliche Datenprüfung','Loading checks…':'Prüfstatus wird geladen …',
'Workspace & sharing':'Arbeitsbereich & Teilen',
'Saved views stay in this browser. Sharing a URL shares its search terms; do not include private data.':'Gespeicherte Ansichten bleiben in diesem Browser. Geteilte URLs enthalten Suchbegriffe; keine vertraulichen Daten eingeben.',
'Save current view':'Ansicht speichern','Choose a saved view':'Gespeicherte Ansicht auswählen',
'Delete saved view':'Ansicht löschen','Copy shareable link':'Link kopieren','Research integrity':'Forschungsintegrität',
'Discovery records are not verified human-rights violations. Source reachability is not evidence of credibility.':'Recherchehinweise sind keine bestätigten Menschenrechtsverletzungen. Erreichbarkeit ist kein Glaubwürdigkeitsnachweis.',
'Methods & limitations':'Methoden & Grenzen','Language':'Sprache','Search records':'Datensätze suchen',
'Select website language':'Sprache auswählen','Scrollable research results table':'Scrollbare Ergebnistabelle',
'Loading public records…':'Öffentliche Datensätze werden geladen …','Loading months…':'Archivmonate werden geladen …',
'Search titles, publishers, DOI, record IDs…':'Titel, Herausgeber, DOI, Datensatz-ID suchen …',
'/ search · J/K navigate · Enter details · Esc clear':'/ Suche · J/K Navigation · Enter Details · Esc Auswahl löschen',
'Operational (technical)':'Betriebsbereit (technisch)','Partial sources':'Teilweise Quellenfehler',
'Collection failed':'Erfassung fehlgeschlagen','Not started':'Noch nicht begonnen','Unavailable':'Nicht verfügbar',
'No results':'Keine Treffer','No records in this scope':'Keine Datensätze in diesem Bereich',
'Records shown':'Treffer','Records loaded':'Datensätze geladen','Scope: latest snapshot':'Bereich: aktueller Stand',
'Scope: archive month':'Bereich: Archivmonat','Scope: combined catalogue':'Bereich: Gesamtübersicht',
'All available archive shards loaded.':'Alle verfügbaren Archivteile geladen.',
'Partial archive scope: only recent shards loaded. Narrow the month or use the canonical archive for full analysis.':'Archiv nur teilweise geladen. Monat eingrenzen oder für vollständige Analysen das kanonische Archiv verwenden.',
'Archive could not be loaded; results are not complete.':'Archiv konnte nicht geladen werden; Ergebnisse sind unvollständig.',
'Loading historical records…':'Historische Datensätze werden geladen …',
'Last collection':'Letzte Erfassung','Source review needed':'Quellenprüfung erforderlich',
'Licence review pending':'Lizenzprüfung ausstehend','Curated references':'Kuratierte Referenzen',
'Editorial status':'Redaktioneller Prüfstatus','Reachability':'Erreichbarkeit',
'Not independently verified':'Nicht unabhängig überprüft','Publisher credit is unverified.':'Herausgeberangabe ist nicht geprüft.',
'No incident event ID has been assigned.':'Es wurde keine überprüfte Ereignis-ID vergeben.',
'Original discovery link':'Originalhinweis öffnen','Open DOI':'DOI öffnen','Publication date':'Veröffentlichungsdatum',
'First observed':'Erstmals erfasst','Monitoring query':'Suchabfrage','Publisher hint':'Herausgeberhinweis',
'Publisher verified':'Herausgeber überprüft','No':'Nein','Yes':'Ja','Source type':'Quellentyp',
'Screening status':'Vorsortierungsstatus','Event ID':'Ereignis-ID','Not assigned':'Nicht zugewiesen',
'Topics (preliminary)':'Themen (vorläufig)','Source inspection':'Quellenprüfung',
'Use the original source to verify all substantive claims.':'Alle inhaltlichen Aussagen anhand der Originalquelle prüfen.',
'No source-health report available.':'Kein Quellenstatusbericht verfügbar.',
'Sources requiring review':'Quellen zur Prüfung','Licences pending':'Lizenzprüfung offen',
'Last source probe':'Letzte Erreichbarkeitsprüfung',
'Reachability does not verify publication quality.':'Erreichbarkeit bestätigt nicht die Publikationsqualität.',
'View saved':'Ansicht gespeichert','View limit reached (12)':'Limit erreicht (12)',
'View name':'Name der Ansicht','Saved view removed':'Ansicht gelöscht',
'Shareable link copied':'Link kopiert','Unable to copy automatically; copy the address shown.':'Automatisches Kopieren nicht möglich; angezeigte Adresse kopieren.',
'Date range is reversed.':'Datumsbereich ist umgekehrt.',
'Data could not be loaded. Check the GitHub Pages deployment.':'Daten konnten nicht geladen werden; GitHub-Pages-Bereitstellung prüfen.',
'Source unavailable':'Quelle unbekannt','No selected record':'Kein Datensatz ausgewählt',
'No active filters':'Keine aktiven Filter','Publication title is shown in its original language.':'Originaltitel bleibt in der Veröffentlichungssprache.',
'All records are public discovery metadata, not a verified population of incidents.':'Alle Datensätze sind öffentliche Recherchemetadaten, keine verifizierte Grundgesamtheit von Vorfällen.'
}};
const t = s => locale()==='en' ? s : (L[locale()] && L[locale()][s]) || baseI18n.t(s);
const text = (tag,value,className) => {const n=document.createElement(tag); if(className)n.className=className;n.textContent=value==null?'':String(value);return n;};
const TOPICS={
policy:'Policy & governance','forced-labour':'Forced labour','working-conditions':'Working conditions',
'worker-voice':'Worker voice & remedy',network:'Supply networks',research:'Academic research',other:'Other'
};
const COLS=[
 {key:'date',label:'Date'},{key:'title',label:'Title'},{key:'publisher',label:'Publisher'},
 {key:'topics',label:'Topics'},{key:'kind',label:'Type'},{key:'evidence',label:'Evidence'},{key:'id',label:'Record ID'}
];
const STORAGE='scro.workbench.views.v1', MAX_FILES=24, MAX_ROWS=10000, PAGE=60;
let live=null,catalog=null,health=null,latest=[],archiveCache=new Map(),activeRecords=[],filtered=[],
scopeStatus='',loading=false,archiveError=false,coveragePartial=false,visible=PAGE,chosen='',runNumber=0;
const param = new URL(location.href).searchParams;
const SAFE_SCOPE=['latest','archive','all'],SAFE_SORT=['published-desc','published-asc','observed-desc','title-asc','publisher-asc'];
const SAFE_KIND=['all','discovery','academic'],SAFE_EVIDENCE=['all','unverified','bibliographic'];
const safeValue=(value,allowed,fallback)=>allowed.includes(value)?value:fallback;
function canonicalID(item){return item.record_id || item.id || '';}
function normalise(item,month) {return {...item,record_id:canonicalID(item),archive_month:month || (item.first_seen||'').slice(0,7)};}
function dateAge(date){const n=Date.parse(date||'');return Number.isFinite(n)?n:0;}
function dateView(date,withTime) {
 const value=new Date(date||'');if(!Number.isFinite(value.getTime()))return '—';
 const opts={timeZone:'Asia/Taipei',year:'numeric',month:'2-digit',day:'2-digit'};
 if(withTime){opts.hour='2-digit';opts.minute='2-digit';opts.hour12=false;}
 return new Intl.DateTimeFormat(({en:'en-GB',zh:'zh-TW',de:'de-DE'})[locale()]||'en-GB',opts).format(value);
}
function https(value) {try{const u=new URL(value);return u.protocol==='https:' && !u.username && !u.password ? u.href : null;}catch(_){return null;}}
function readControls(){
 return {
 scope:$('wb-scope').value,month:$('wb-month').value,q:$('wb-search').value.trim().slice(0,120),
 from:$('wb-from').value,to:$('wb-to').value,kind:$('wb-kind').value,
 evidence:$('wb-evidence').value,sort:$('wb-sort').value,
 topics:[...document.querySelectorAll('[name="wb-topic"]:checked')].map(x=>x.value),
 cols:[...document.querySelectorAll('[data-column]:checked')].map(x=>x.dataset.column),
 density:$('wb-density').value
 };
}
function applyControls(values) {
 $('wb-scope').value=safeValue(values.scope,SAFE_SCOPE,'latest');
 $('wb-sort').value=safeValue(values.sort,SAFE_SORT,'published-desc');
 $('wb-kind').value=safeValue(values.kind,SAFE_KIND,'all');
 $('wb-evidence').value=safeValue(values.evidence,SAFE_EVIDENCE,'all');
 $('wb-search').value=String(values.q||'').slice(0,120);
 for(const id of ['from','to']) {
  const v=values[id]||'';$('wb-'+id).value=/^\d{4}-\d{2}-\d{2}$/.test(v)?v:'';
 }
 const chosenTopics=Array.isArray(values.topics)?values.topics:[];
 document.querySelectorAll('[name="wb-topic"]').forEach(x=>x.checked=chosenTopics.includes(x.value));
 const columns=Array.isArray(values.cols)?values.cols:COLS.filter(x=>x.key!=='id').map(x=>x.key);
 document.querySelectorAll('[data-column]').forEach(x=>x.checked=x.disabled||columns.includes(x.dataset.column));
 $('wb-density').value=values.density==='comfortable'?'comfortable':'compact';
 const month=values.month||'';
 if([...$('wb-month').options].some(o=>o.value===month))$('wb-month').value=month;
}
function parseURL(){
 const p=new URL(location.href).searchParams;
 return {scope:p.get('scope'),month:p.get('month'),q:p.get('q'),from:p.get('from'),to:p.get('to'),
 kind:p.get('kind'),evidence:p.get('evidence'),sort:p.get('sort'),
 topics:(p.get('topics')||'').split(',').filter(Boolean),cols:p.has('cols')?p.get('cols').split(','):undefined,
 density:p.get('density')};
}
function syncURL(){
 const s=readControls(),url=new URL(location.href);
 for(const k of ['scope','month','q','from','to','kind','evidence','sort','topics','cols','density','record']) url.searchParams.delete(k);
 url.searchParams.set('scope',s.scope);
 if(s.scope!=='latest'&&s.month)url.searchParams.set('month',s.month);
 if(s.q)url.searchParams.set('q',s.q);
 for(const id of ['from','to'])if(s[id])url.searchParams.set(id,s[id]);
 if(s.kind!=='all')url.searchParams.set('kind',s.kind);
 if(s.evidence!=='all')url.searchParams.set('evidence',s.evidence);
 if(s.sort!=='published-desc')url.searchParams.set('sort',s.sort);
 if(s.topics.length)url.searchParams.set('topics',s.topics.join(','));
 if(s.cols.join(',')!==COLS.filter(x=>x.key!=='id').map(x=>x.key).join(','))url.searchParams.set('cols',s.cols.join(','));
 if(s.density!=='compact')url.searchParams.set('density',s.density);
 if(chosen)url.searchParams.set('record',chosen);
 history.replaceState(null,'',url.pathname+url.search+url.hash);
}
function localiseStatic(){
 document.querySelectorAll('[data-l10n]').forEach(n=>{n.textContent=t(n.dataset.l10n);});
 $('wb-search').placeholder=t('Search titles, publishers, DOI, record IDs…');
 $('language-select').setAttribute('aria-label',t('Select website language'));
 document.title=t('Research Workbench')+' | Supply Chain Rights Observatory';
 $('wb-table').parentElement.setAttribute('aria-label',t('Scrollable research results table'));
 render();
}
async function fetchJSON(path) {
 const response=await fetch(path,{credentials:'omit',cache:'no-store'});
 if(!response.ok)throw new Error('HTTP '+response.status);
 return response.json();
}
function sourceInfo(){
 if(!health){$('wb-quality').replaceChildren(text('p',t('No source-health report available.')));return;}
 const box=$('wb-quality');box.replaceChildren();
 for(const [label,value] of [
  ['Curated references',health.approved_reference_count],
  ['Sources requiring review',health.review_needed_count],
  ['Licences pending',health.licence_review_pending_count],
  ['Last source probe',dateView(health.last_probe_run,true)]
 ]) {
  const row=text('div','','wb-check-row');
  row.append(text('span',t(label)),text('strong',value??'—',Number(value)>0&&label!=='Curated references'?'wb-check-warning':''));
  box.append(row);
 }
 box.append(text('p',t('Reachability does not verify publication quality.'),'wb-empty'));
 const problem=(health.sources||[]).filter(s=>s.review_needed||s.reachability==='failed').slice(0,5);
 for(const s of problem) {
  const card=text('div','','wb-source-item');
  card.append(text('strong',s.name),text('small',(s.review_needed?t('Source review needed'):'')+' · '+(s.reachability||t('Unavailable'))));
  box.append(card);
 }
}
function renderStatus(){
 $('wb-latest-count').textContent=live?String(latest.length):'—';
 $('wb-archive-count').textContent=catalog?String(catalog.total_records):'—';
 $('wb-data-status').textContent=!live?t('Unavailable'):live.status==='ok'?t('Operational (technical)'):
  live.status==='partial'?t('Partial sources'):live.status==='failed'?t('Collection failed'):t('Not started');
 $('wb-updated').textContent=live?dateView(live.last_successful_collection,true):'—';
 sourceInfo();
}
async function fetchMonth(month){
 if(archiveCache.has(month))return archiveCache.get(month);
 const data=(catalog?.months||[]).find(m=>m.month===month);
 if(!data || !/^\d{4}-\d{2}$/.test(month) || !Array.isArray(data.files) || data.files.length>MAX_FILES)throw new Error('Unsupported archive month');
 let all=[];
 for(const part of data.files){
  if(!/^\d{4}-\d{2}-\d{4}\.json$/.test(part.file))throw new Error('Unsafe archive filename');
  const shard=await fetchJSON('../data/archive/'+part.file);
  if(!Array.isArray(shard.records) || (typeof part.records==='number'&&shard.records.length!==part.records))throw new Error('Archive integrity mismatch');
  all.push(...shard.records.map(x=>normalise(x,month)));
  if(all.length>MAX_ROWS)throw new Error('Archive exceeds browser cap');
 }
 if(all.length!==data.records)throw new Error('Archive count mismatch');
 archiveCache.set(month,all);
 return all;
}
async function prepareScope(){
 const req=++runNumber;
 loading=true;archiveError=false;coveragePartial=false;activeRecords=[];
 render();
 const s=readControls();
 try {
  let combined=s.scope==='latest'?[...latest]:[];
  if(s.scope==='archive'){
   if(!catalog?.months?.length)throw new Error('No archive months');
   const month=s.month||catalog.months[0].month;
   combined=await fetchMonth(month);
  } else if(s.scope==='all'){
   if(!catalog || !Array.isArray(catalog.months))throw new Error('Archive catalogue unavailable');
   combined=[...latest];
   let fileCount=0,rowCount=0;
   for(const month of catalog.months){
    const fragments=month.files?.length||0;
    if(fileCount+fragments>MAX_FILES||rowCount+month.records>MAX_ROWS){coveragePartial=true;break;}
    combined.push(...await fetchMonth(month.month));
    fileCount+=fragments;rowCount+=month.records;
   }
  }
  if(req!==runNumber)return;
  const map=new Map();
  for(const item of combined) {
   const id=canonicalID(item);
   if(!/^[0-9a-f]{18}$/.test(id))continue;
   // Prefer current snapshot if both current and archived observations exist.
   if(!map.has(id))map.set(id,normalise(item,item.archive_month));
  }
  activeRecords=[...map.values()];
 }catch(_) {if(req!==runNumber)return;archiveError=true;activeRecords=s.scope==='all'?[...latest]:[];}
 finally{if(req===runNumber){loading=false;render();}}
}
function selectedRecords(){
 const c=readControls();
 const from=c.from,to=c.to;
 let arr=activeRecords.filter(x=>{
  if(c.kind!=='all'&&x.kind!==c.kind)return false;
  if(c.evidence==='unverified'&&!String(x.evidence_status).toLowerCase().includes('unverified'))return false;
  if(c.evidence==='bibliographic'&&!String(x.evidence_status).toLowerCase().includes('bibliographic'))return false;
  if(c.topics.length&&!c.topics.some(a=>(x.topics||[]).includes(a)))return false;
  const published=String(x.published_at||'').slice(0,10);
  if(from&&published<from)return false;
  if(to&&published>to)return false;
  if(c.q){
   const parts=[x.title,x.publisher_hint,x.source,x.source_id,x.record_id,x.doi,x.evidence_status,x.kind,...(x.topics||[])].join(' ');
   const matches=window.SCRO_QUERY?window.SCRO_QUERY.matches(parts,c.q):parts.toLowerCase().includes(c.q.toLowerCase());
   if(!matches)return false;
  }
  return true;
 });
 const str=x=>String(x||'').toLowerCase();
 arr.sort((a,b)=>{
  if(c.sort==='title-asc')return str(a.title).localeCompare(str(b.title));
  if(c.sort==='publisher-asc')return str(a.publisher_hint).localeCompare(str(b.publisher_hint));
  const field=c.sort==='observed-desc'?'first_seen':'published_at';
  const dir=c.sort==='published-asc'?1:-1;
  return (dateAge(a[field])-dateAge(b[field]))*dir||str(a.record_id).localeCompare(str(b.record_id));
 });
 return arr;
}
function drawTable(){
 const c=readControls();
 filtered=selectedRecords();
 const wrap=$('wb-table').parentElement;
 document.body.classList.toggle('wb-comfortable',c.density==='comfortable');
 const fields=COLS.filter(col=>col.key==='title'||c.cols.includes(col.key));
 const thead=$('wb-thead'),tbody=$('wb-tbody');thead.replaceChildren();tbody.replaceChildren();
 const tr=document.createElement('tr');
 for(const field of fields){
  const th=document.createElement('th');th.scope='col';
  const key=field.key;
  const sort={date:'published',title:'title',publisher:'publisher'}[key];
  if(sort){
   const b=text('button',t(field.label)+(c.sort.startsWith(sort)?' ↓':''));b.type='button';
   b.addEventListener('click',()=>{
    const next=sort==='published'?(c.sort==='published-desc'?'published-asc':'published-desc'):sort+'-asc';
    $('wb-sort').value=next;changed(false);
   });th.append(b);
   th.setAttribute('aria-sort',c.sort.startsWith(sort)?(c.sort==='published-asc'?'ascending':'descending'):'none');
  }else th.textContent=t(field.label);
  tr.append(th);
 }
 thead.append(tr);
 const rows=filtered.slice(0,visible);
 for(const item of rows){
  const row=document.createElement('tr');row.tabIndex=0;row.dataset.recordId=item.record_id;
  row.setAttribute('aria-label',item.title||'');
  if(item.record_id===chosen)row.classList.add('is-selected');
  for(const field of fields){
   const td=document.createElement('td');let val='';
   switch(field.key){
    case 'date':val=dateView(item.published_at,false);td.className='wb-date-cell';break;
    case 'title':val=item.title||'—';td.className='wb-title-cell';td.lang=item.original_language||'und';break;
    case 'publisher':val=item.publisher_hint||t('Not independently verified');break;
    case 'topics':val=(item.topics||[]).map(x=>t(TOPICS[x]||x)).join(', ');break;
    case 'kind':val=t(item.kind==='academic'?'Academic metadata':'Discovery leads');break;
    case 'evidence':val=t(item.evidence_status||'Not independently verified');break;
    case 'id':val=item.record_id;td.className='wb-id-cell';break;
   }
   td.textContent=val;
   row.append(td);
  }
  row.addEventListener('click',()=>selectRecord(item.record_id));
  row.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();selectRecord(item.record_id);}});
  tbody.append(row);
 }
 if(!rows.length){
  const row=document.createElement('tr'),cell=text('td',t(loading?'Loading historical records…':archiveError?'Archive could not be loaded; results are not complete.':'No results'));
  cell.colSpan=fields.length;row.append(cell);tbody.append(row);
 }
 $('wb-more').hidden=visible>=filtered.length;
 $('wb-count').textContent=String(filtered.length)+' '+t('Records shown');
 const terms=[];
 if(c.q)terms.push(c.q);
 if(c.topics.length)terms.push(c.topics.map(k=>t(TOPICS[k]||k)).join(' OR '));
 if(c.kind!=='all')terms.push(t(c.kind==='academic'?'Academic metadata':'Discovery leads'));
 $('wb-active-filters').textContent=terms.join(' · ')||t('No active filters');
 let status=c.scope==='latest'?t('Scope: latest snapshot'):c.scope==='archive'?t('Scope: archive month')+': '+c.month:t('Scope: combined catalogue');
 if(loading)status+=' · '+t('Loading historical records…');
 else if(archiveError)status+=' · '+t('Archive could not be loaded; results are not complete.');
 else if(coveragePartial)status+=' · '+t('Partial archive scope: only recent shards loaded. Narrow the month or use the canonical archive for full analysis.');
 else if(c.scope==='all')status+=' · '+t('All available archive shards loaded.');
 else status+=' · '+String(activeRecords.length)+' '+t('Records loaded');
 if(c.from&&c.to&&c.from>c.to)status+=' · '+t('Date range is reversed.');
 const alert=$('wb-coverage');alert.textContent=status;
 alert.classList.toggle('is-alert',archiveError||coveragePartial||Boolean(c.from&&c.to&&c.from>c.to));
}
function showRecord(){
 const out=$('wb-detail');out.replaceChildren();
 const item=activeRecords.find(x=>x.record_id===chosen);
 if(!item){out.append(text('p',t('Select a record to inspect its provenance, dates and evidence status.'),'wb-empty'));return;}
 out.append(text('h3',item.title));
 const dl=document.createElement('dl');
 const fields=[
  ['Record ID',item.record_id],['Publication date',dateView(item.published_at,true)],
  ['First observed',dateView(item.first_seen,true)],['Publisher hint',item.publisher_hint||t('Source unavailable')],
  ['Publisher verified',t(item.publisher_verified?'Yes':'No')],['Monitoring query',item.source],
  ['Source type',t(item.kind==='academic'?'Academic metadata':'Discovery leads')],
  ['Evidence class',t(item.evidence_status||'Not independently verified')],
  ['Screening status',item.screening_status||'—'],
  ['Topics (preliminary)',(item.topics||[]).map(x=>t(TOPICS[x]||x)).join(', ')],
  ['Event ID',item.event_id||t('Not assigned')]
 ];
 if(item.doi)fields.push(['DOI',item.doi]);
 for(const [key,val] of fields){dl.append(text('dt',t(key)),text('dd',val));}
 out.append(dl);
 const links=text('div','','wb-detail-links');
 const url=https(item.canonical_url)||https(item.url);
 if(url){
  const link=text('a',t(item.doi?'Open DOI':'Original discovery link'));link.href=url;link.target='_blank';link.rel='noopener noreferrer';links.append(link);
 }
 const urlMonth=item.archive_month;
 if(urlMonth&&/^\d{4}-\d{2}$/.test(urlMonth)){
  const detail=text('a',t('Record ID'));detail.href='../record.html?month='+encodeURIComponent(urlMonth)+'&id='+encodeURIComponent(item.record_id);
  links.append(detail);
 }
 out.append(links);
 out.append(text('p',t('Publisher credit is unverified.')+' '+t('No incident event ID has been assigned.')+' '+t('Use the original source to verify all substantive claims.'),'wb-record-warning'));
 out.append(text('p',t('Publication title is shown in its original language.'),'wb-empty'));
}
function selectRecord(id,scroll=true){
 chosen=id;syncURL();showRecord();
 document.querySelectorAll('#wb-tbody tr').forEach(row=>row.classList.toggle('is-selected',row.dataset.recordId===id));
 if(scroll){const row=[...document.querySelectorAll('#wb-tbody tr')].find(x=>x.dataset.recordId===id);row?.scrollIntoView({block:'nearest'});}
}
function render(){renderStatus();drawTable();showRecord();}
function changed(reload){
 visible=PAGE;syncURL();
 if(reload)prepareScope();else render();
}
function csvCell(value) {
 let s=String(value==null?'':Array.isArray(value)?value.join('; '):value).replace(/[\u0000-\u001f\u007f]/g,' ');
 if(/^\s*[=+\-@]/.test(s))s="'"+s;
 return '"'+s.replace(/"/g,'""')+'"';
}
function exportCSV(){
 const columns=['record_id','event_id','title','published_at','first_seen','publisher_hint','publisher_verified',
 'source','source_id','kind','evidence_status','screening_status','topics','doi','url'];
 const rows=[columns,...filtered.map(r=>columns.map(k=>r[k]??''))];
 const csv='\ufeff'+rows.map(r=>r.map(csvCell).join(',')).join('\r\n');
 const blob=new Blob([csv],{type:'text/csv;charset=utf-8'});
 const url=URL.createObjectURL(blob);
 const a=document.createElement('a');a.href=url;a.download='scro-'+$('wb-scope').value+'-'+new Date().toISOString().slice(0,10)+'.csv';
 document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),750);
}
function views(){
 try{const v=JSON.parse(localStorage.getItem(STORAGE)||'[]');return Array.isArray(v)?v.slice(0,12):[];}catch(_){return [];}
}
function saveViews(v){try{localStorage.setItem(STORAGE,JSON.stringify(v));return true;}catch(_){return false;}}
function populateViews(){
 const list=$('wb-saved-list');list.replaceChildren();
 const blank=text('option',t('Choose a saved view'));blank.value='';list.append(blank);
 for(const v of views()){const op=text('option',v.name);op.value=v.id;list.append(op);}
}
function saveView(){
 const all=views();if(all.length>=12){feedback('View limit reached (12)');return;}
 const name=window.prompt(t('View name'),t('Research Workbench'));
 if(!name||!name.trim())return;
 const value={id:String(Date.now())+String(Math.floor(Math.random()*1000)),name:name.trim().slice(0,45),state:readControls()};
 if(saveViews([...all,value])){populateViews();$('wb-saved-list').value=value.id;feedback('View saved');}
}
function feedback(s){$('wb-feedback').textContent=t(s);}
async function share(){
 syncURL();
 try {await navigator.clipboard.writeText(location.href);feedback('Shareable link copied');}
 catch(_){window.prompt(t('Unable to copy automatically; copy the address shown.'),location.href);}
}
function reset(){
 applyControls({scope:'latest',sort:'published-desc',kind:'all',evidence:'all'});
 chosen='';changed(true);
}
function setPreset(key){
 const base={scope:'latest',sort:'published-desc',kind:'all',evidence:'all'};
 if(key==='labour')base.topics=['forced-labour','working-conditions','worker-voice'];
 if(key==='policy')base.topics=['policy','network'];
 if(key==='academic')base.kind='academic';
 applyControls(base);chosen='';changed(true);
}
async function init(){
 applyControls(parseURL());
 chosen=(param.get('record')||'').match(/^[0-9a-f]{18}$/)?.[0]||'';
 localiseStatic();
 try{
  const [a,b,c]=await Promise.allSettled([
   fetchJSON('../data/latest.json'),fetchJSON('../data/archive/catalog.json'),fetchJSON('../data/source-health.json')
  ]);
  if(a.status!=='fulfilled'||!Array.isArray(a.value.items))throw Error('Latest snapshot unavailable');
  live=a.value;
  latest=live.items.map(x=>normalise(x)).filter(x=>/^[0-9a-f]{18}$/.test(x.record_id));
  catalog=b.status==='fulfilled'&&Array.isArray(b.value.months)?b.value:null;
  health=c.status==='fulfilled'?c.value:null;
  const months=$('wb-month');months.replaceChildren();
  if(catalog){
   for(const m of catalog.months){
    if(!/^\d{4}-\d{2}$/.test(m.month))continue;
    const op=text('option',m.month+' ('+m.records+')');op.value=m.month;months.append(op);
   }
  }
  const month=parseURL().month;
  if(month&&[...months.options].some(o=>o.value===month))months.value=month;
  await prepareScope();
 }catch(_){
  live=null;archiveError=true;loading=false;
  $('wb-coverage').textContent=t('Data could not be loaded. Check the GitHub Pages deployment.');
  render();
 }
}
function bind(){
 for(const id of ['wb-search','wb-sort','wb-kind','wb-evidence','wb-from','wb-to','wb-density'])
  $(id).addEventListener(id==='wb-search'?'input':'change',()=>changed(false));
 $('wb-scope').addEventListener('change',()=>changed(true));
 $('wb-month').addEventListener('change',()=>changed(true));
 document.querySelectorAll('[name="wb-topic"],[data-column]').forEach(x=>x.addEventListener('change',()=>changed(false)));
 $('wb-clear').addEventListener('click',reset);
 $('wb-export').addEventListener('click',exportCSV);
 $('wb-more').addEventListener('click',()=>{visible+=PAGE;render();});
 $('wb-deselect').addEventListener('click',()=>selectRecord(''));
 $('wb-share').addEventListener('click',share);
 $('wb-save').addEventListener('click',saveView);
 $('wb-remove-view').addEventListener('click',()=>{
  const id=$('wb-saved-list').value;if(!id)return;
  if(saveViews(views().filter(x=>x.id!==id))){populateViews();feedback('Saved view removed');}
 });
 $('wb-saved-list').addEventListener('change',()=>{
  const v=views().find(x=>x.id===$('wb-saved-list').value);
  if(v){applyControls(v.state);chosen='';changed(true);}
 });
 document.querySelectorAll('[data-preset]').forEach(x=>x.addEventListener('click',()=>setPreset(x.dataset.preset)));
 window.addEventListener('keydown',e=>{
  const tag=e.target?.tagName||'';
  const editing=/^(INPUT|TEXTAREA|SELECT)$/.test(tag)||e.target?.isContentEditable;
  if(e.key==='Escape'){if(chosen){selectRecord('');e.preventDefault();}return;}
  if(editing || e.ctrlKey||e.metaKey||e.altKey)return;
  if(e.key==='/'){e.preventDefault();$('wb-search').focus();return;}
  if(e.key==='j'||e.key==='k'){
   if(!filtered.length)return;e.preventDefault();
   const idx=filtered.findIndex(x=>x.record_id===chosen);
   const newIndex=e.key==='j'?Math.min(filtered.length-1,idx+1):Math.max(0,idx<0?0:idx-1);
   if(newIndex>=visible)visible=Math.min(filtered.length,newIndex+PAGE);
   render();selectRecord(filtered[newIndex].record_id);
  }else if(e.key==='Enter'&&chosen){showRecord();$('wb-detail').scrollIntoView({block:'nearest'});}
 });
 baseI18n.onChange(localiseStatic);
 populateViews();
}
bind();init();
})();