/* Research workbench for filtering, inspecting and exporting records. */
(() => {
'use strict';
const $ = id => document.getElementById(id);
const baseI18n = window.SCRO_I18N || {language:'en', t:x=>x, onChange:()=>{}};
const recordTags=window.SCRO_RECORD_TAGS;
const publishedTags=item=>window.SCRO_RELEVANCE?.tags(item)||[];
const locale = () => baseI18n.language || 'en';
const number = value => baseI18n.formatNumber?.(value)??String(value);
const wbAssetRoot=new URL('./',document.currentScript.src);
const editorMode=document.body.dataset.page==='workbench-editor';
const L = {
zh:{
"Advanced tools":"進階工具",

"You are in the Review Editor":"您正在使用審核編輯器",
"Return to the read-only view":"返回檢視頁",

"Searchable records":"可搜尋紀錄總數",
"First-seen month":"首次收錄月份（UTC）",
"All available months":"所有月份",
'Export':'匯出','Export query metadata':'匯出查詢中繼資料',
"Remove first-seen month filter":"移除首次收錄月份條件",
'Previous page':'上一頁','Next page':'下一頁','Page':'第','of':'／','Showing':'顯示','records':'筆','Results pagination':'結果分頁','Paged research results table':'分頁研究結果表格','Full text in record inspector':'完整內容請見右側紀錄詳情',
'Skip to results':'跳至搜尋結果','Visitor portal':'一般訪客首頁',
'Latest records':'最新情報','Historical records':'歷史紀錄',
'Collection status':'擷取狀態','Last successful collection':'最後成功擷取',
'Methodology':'研究方法','Dataset':'資料範圍','Latest':'最新情報','Archive month':'歷史月份','All available':'全部可取得紀錄',
'Sort by':'排序方式','Published: newest':'發布時間：最新','Published: oldest':'發布時間：最早',
'Observed: newest':'首次收錄：最新','Title: A–Z':'標題：A–Z','Publisher: A–Z':'出版者：A–Z',
'Reset':'重設','Filters':'篩選條件','Combinable criteria':'可組合條件','Published from':'發布起始日',
'Through':'截至日期','Record type':'紀錄類型','All types':'所有類型',
'Any evidence class':'所有證據分類',

'Research themes (OR)':'研究議題（擇一符合）','Visible columns':'顯示欄位','Date':'日期',
'Title':'標題','Publisher':'出版者','Topics':'主題','Type':'類型','Evidence':'證據',
'Record ID':'紀錄編號','Quick views':'快速視圖','Labour & remedy':'勞工與補救',
'EU policy & HRDD':'歐盟政策與人權盡職調查','Academic research':'學術研究',
'Research records':'研究紀錄','AND / OR / quoted phrases supported':'支援 AND、OR 與引號片語',
'Density':'顯示密度','Compact':'緊密','Comfortable':'舒適','Export CSV':'匯出 CSV',
'Show more':'顯示更多','Record inspector':'紀錄詳情','Clear selection':'清除選取',
'Select a record to inspect its provenance, dates and evidence status.':'選取紀錄後檢查來源、日期與證據狀態。',
'Workspace & sharing':'工作區與分享',
'Saved views stay in this browser. Shared links include the current search terms.':'已儲存的視圖保留在此瀏覽器。分享連結會包含目前的搜尋條件。',
'Save current view':'儲存目前視圖','Choose a saved view':'選擇已儲存視圖',
'Delete saved view':'刪除已儲存視圖','Research integrity':'研究完整性',
'Language':'語言','Search records':'搜尋紀錄',
'Select website language':'選擇網站語言','Scrollable research results table':'可捲動的研究結果表格',
'Loading public records…':'正在讀取公開紀錄…','Loading months…':'讀取月份…',
'Search titles, publishers, DOI, record IDs…':'搜尋標題、出版者、DOI、紀錄編號…',
'/ search · J/K navigate · Enter details · Esc clear':'/ 搜尋 · J/K 切換 · Enter 詳情 · Esc 清除',
'Operational (technical)':'正常（技術狀態）','Partial sources':'部分來源異常',
'Collection failed':'擷取失敗','Not started':'尚未開始','Unavailable':'無法取得',
'No results':'沒有符合的紀錄','Records shown':'筆結果',
'Some records could not be loaded. Search results may be incomplete.':'部分紀錄載入失敗，搜尋結果可能不完整。',
'Search covers part of the archive. Choose a first-seen month to narrow the search.':'目前搜尋涵蓋部分封存資料。可選擇首次收錄月份縮小查詢。',
'The review index could not be loaded.':'審核索引載入失敗。',
'Last collection':'最近擷取','Source review needed':'來源待審查',
'Licence review pending':'授權審查待處理','Curated references':'收錄參考來源',
'Editorial status':'編輯審查狀態','Reachability':'連線狀態',
'Not independently verified':'尚未獨立查證','Publisher credit is unverified.':'出版者資訊未經獨立查證。',
'Original discovery link':'原始線索連結','Open DOI':'開啟 DOI','Publication date':'發布日期',
'Monitoring query':'監測查詢','Publisher hint':'出版者線索',
'Publisher verified':'出版者已查核','No':'否','Yes':'是','Source type':'資料類型',
'Screening status':'初篩狀態','Event ID':'事件編號','Not assigned':'尚未指派',
'Topics (preliminary)':'主題（初步分類）','Source inspection':'來源查核',
'View saved':'視圖已儲存','View limit reached (12)':'已達儲存上限（12）',
'View name':'視圖名稱','Saved view removed':'已刪除儲存視圖',
'Unable to copy automatically; copy the address shown.':'無法自動複製，請複製顯示的網址。',
'Date range is reversed.':'日期範圍前後相反。',
'Data could not be loaded. Check the GitHub Pages deployment.':'資料載入失敗；請檢查 GitHub Pages 部署。',
'Source unavailable':'來源不明','No selected record':'尚未選取紀錄','No active filters':'尚無篩選條件',
'Publication title is shown in its original language.':'出版標題保留原始語言。',
},
de:{
"Advanced tools":"Erweiterte Werkzeuge",

"You are in the Review Editor":"Sie befinden sich im Review-Editor",
"Return to the read-only view":"Zurück zur Leseansicht",

"Searchable records":"Durchsuchbare Datensätze insgesamt",
"First-seen month":"Monat der Ersterfassung (UTC)",
"All available months":"Alle verfügbaren Monate",
'Export':'Exportieren','Export query metadata':'Suchmetadaten exportieren',
"Remove first-seen month filter":"Filter für den Monat der Ersterfassung entfernen",
'Previous page':'Vorherige Seite','Next page':'Nächste Seite','Page':'Seite','of':'von','Showing':'Anzeige','records':'Einträge','Results pagination':'Ergebnisseiten','Paged research results table':'Seitengesteuerte Ergebnistabelle','Full text in record inspector':'Volltext in den Datensatzdetails',
'Skip to results':'Zu den Suchergebnissen','Visitor portal':'Besucherportal',
'Latest records':'Aktuelle Meldungen','Historical records':'Historische Datensätze',
'Collection status':'Erfassungsstatus','Last successful collection':'Letzte erfolgreiche Erfassung',
'Methodology':'Methodik','Dataset':'Datenbestand',
'Latest':'Aktuell','Archive month':'Archivmonat','All available':'Alle verfügbaren',
'Sort by':'Sortieren nach','Published: newest':'Veröffentlicht: neueste','Published: oldest':'Veröffentlicht: älteste',
'Observed: newest':'Erfasst: neueste','Title: A–Z':'Titel: A–Z','Publisher: A–Z':'Herausgeber: A–Z',
'Reset':'Zurücksetzen','Filters':'Filter','Combinable criteria':'Kombinierbare Kriterien',
'Published from':'Veröffentlicht ab','Through':'Bis','Record type':'Datensatztyp',
'All types':'Alle Typen',
'Any evidence class':'Alle Evidenzkategorien',

'Research themes (OR)':'Forschungsthemen (ODER)','Visible columns':'Sichtbare Spalten','Date':'Datum',
'Title':'Titel','Publisher':'Herausgeber','Topics':'Themen','Type':'Typ','Evidence':'Evidenz',
'Record ID':'Datensatz-ID','Quick views':'Schnellansichten','Labour & remedy':'Arbeitsrechte & Abhilfe',
'EU policy & HRDD':'EU-Recht & menschenrechtliche Sorgfalt',
'Academic research':'Wissenschaftliche Forschung','Research records':'Forschungsdatensätze',
'AND / OR / quoted phrases supported':'AND, OR und exakte Phrasen in Anführungszeichen',
'Density':'Dichte','Compact':'Kompakt','Comfortable':'Komfortabel','Export CSV':'CSV exportieren',
'Show more':'Mehr anzeigen','Record inspector':'Datensatzdetails','Clear selection':'Auswahl löschen',
'Select a record to inspect its provenance, dates and evidence status.':'Datensatz auswählen, um Herkunft, Daten und Evidenzstatus zu prüfen.',
'Workspace & sharing':'Arbeitsbereich & Teilen',
'Saved views stay in this browser. Shared links include the current search terms.':'Gespeicherte Ansichten bleiben in diesem Browser. Geteilte Links enthalten die aktuellen Suchbegriffe.',
'Save current view':'Ansicht speichern','Choose a saved view':'Gespeicherte Ansicht auswählen',
'Delete saved view':'Ansicht löschen','Research integrity':'Forschungsintegrität',
'Language':'Sprache','Search records':'Datensätze suchen',
'Select website language':'Sprache auswählen','Scrollable research results table':'Scrollbare Ergebnistabelle',
'Loading public records…':'Öffentliche Datensätze werden geladen …','Loading months…':'Archivmonate werden geladen …',
'Search titles, publishers, DOI, record IDs…':'Titel, Herausgeber, DOI, Datensatz-ID suchen …',
'/ search · J/K navigate · Enter details · Esc clear':'/ Suche · J/K Navigation · Enter Details · Esc Auswahl löschen',
'Operational (technical)':'Betriebsbereit (technisch)','Partial sources':'Teilweise Quellenfehler',
'Collection failed':'Erfassung fehlgeschlagen','Not started':'Noch nicht begonnen','Unavailable':'Nicht verfügbar',
'No results':'Keine Treffer','Records shown':'Treffer',
'Some records could not be loaded. Search results may be incomplete.':'Einige Datensätze konnten nicht geladen werden. Die Suchergebnisse sind möglicherweise unvollständig.',
'Search covers part of the archive. Choose a first-seen month to narrow the search.':'Die Suche deckt einen Teil des Archivs ab. Wählen Sie einen Monat der Ersterfassung, um die Suche einzugrenzen.',
'The review index could not be loaded.':'Der Prüfindex konnte nicht geladen werden.',
'Last collection':'Letzte Erfassung','Source review needed':'Quellenprüfung erforderlich',
'Licence review pending':'Lizenzprüfung ausstehend','Curated references':'Kuratierte Referenzen',
'Editorial status':'Redaktioneller Prüfstatus','Reachability':'Erreichbarkeit',
'Not independently verified':'Nicht unabhängig überprüft','Publisher credit is unverified.':'Herausgeberangabe ist nicht geprüft.',
'Original discovery link':'Originalhinweis öffnen','Open DOI':'DOI öffnen','Publication date':'Veröffentlichungsdatum',
'Monitoring query':'Suchabfrage','Publisher hint':'Herausgeberhinweis',
'Publisher verified':'Herausgeber überprüft','No':'Nein','Yes':'Ja','Source type':'Quellentyp',
'Screening status':'Vorsortierungsstatus','Event ID':'Ereignis-ID','Not assigned':'Nicht zugewiesen',
'Topics (preliminary)':'Themen (vorläufig)','Source inspection':'Quellenprüfung',
'View saved':'Ansicht gespeichert','View limit reached (12)':'Limit erreicht (12)',
'View name':'Name der Ansicht','Saved view removed':'Ansicht gelöscht',
'Unable to copy automatically; copy the address shown.':'Automatisches Kopieren nicht möglich; angezeigte Adresse kopieren.',
'Date range is reversed.':'Datumsbereich ist umgekehrt.',
'Data could not be loaded. Check the GitHub Pages deployment.':'Daten konnten nicht geladen werden; GitHub-Pages-Bereitstellung prüfen.',
'Source unavailable':'Quelle unbekannt','No selected record':'Kein Datensatz ausgewählt',
'No active filters':'Keine aktiven Filter','Publication title is shown in its original language.':'Originaltitel bleibt in der Veröffentlichungssprache.',
},
es:{
"Other":"Otros",
"Advanced tools":"Herramientas avanzadas",

"You are in the Review Editor":"Está en el editor de revisión",
"Return to the read-only view":"Volver a la vista de solo lectura",

"Searchable records":"Total de registros consultables",
"First-seen month":"Mes de primera detección (UTC)",
"All available months":"Todos los meses disponibles",
"Export":"Exportar",
"Export query metadata":"Exportar metadatos de la consulta",
"Remove first-seen month filter":"Quitar el filtro por mes de primera detección",
"Previous page":"Página anterior",
"Next page":"Página siguiente",
"Page":"Página",
"of":"de",
"Showing":"Se muestran",
"records":"registros",
"Results pagination":"Paginación de resultados",
"Paged research results table":"Tabla paginada de resultados",
"Full text in record inspector":"Texto completo en los detalles del registro",
"Skip to results":"Ir a los resultados",
"Visitor portal":"Portal de visitantes",

"Latest records":"Registros recientes",
"Historical records":"Registros históricos",
"Collection status":"Estado de la recopilación",
"Last successful collection":"Última recopilación exitosa",

"Methodology":"Metodología",
"Dataset":"Conjunto de datos",
"Latest":"Recientes",
"Archive month":"Mes del archivo",
"All available":"Todos los disponibles",
"Sort by":"Ordenar por",
"Published: newest":"Publicación: más reciente",
"Published: oldest":"Publicación: más antigua",
"Observed: newest":"Primera detección: más reciente",
"Title: A–Z":"Título: A–Z",
"Publisher: A–Z":"Entidad editora: A–Z",
"Reset":"Restablecer",
"Filters":"Filtros",
"Combinable criteria":"Criterios combinables",
"Published from":"Publicado desde",
"Through":"Hasta",
"Record type":"Tipo de registro",
"All types":"Todos los tipos",

"Any evidence class":"Cualquier categoría de evidencia",

"Research themes (OR)":"Temas de investigación (OR)",
"Visible columns":"Columnas visibles",
"Date":"Fecha",
"Title":"Título",
"Publisher":"Entidad editora",
"Topics":"Temas",
"Type":"Tipo",
"Evidence":"Evidencia",
"Record ID":"ID del registro",
"Quick views":"Vistas rápidas",
"Labour & remedy":"Derechos laborales y reparación",
"EU policy & HRDD":"Política de la UE y diligencia debida en derechos humanos",
"Academic research":"Investigación académica",
"Research records":"Registros de investigación",
"AND / OR / quoted phrases supported":"Se admiten AND, OR y frases entre comillas",
"Density":"Densidad",
"Compact":"Compacta",
"Comfortable":"Espaciada",
"Export CSV":"Exportar CSV",
"Show more":"Mostrar más",
"Record inspector":"Detalles del registro",
"Clear selection":"Borrar la selección",
"Select a record to inspect its provenance, dates and evidence status.":"Seleccione un registro para consultar su procedencia, sus fechas y la categoría de evidencia.",
"Workspace & sharing":"Espacio de trabajo y enlaces",
"Saved views stay in this browser. Shared links include the current search terms.":"Las vistas se guardan en este navegador. Los enlaces compartidos incluyen los términos de búsqueda actuales.",
"Save current view":"Guardar vista actual",
"Choose a saved view":"Elegir una vista guardada",
"Delete saved view":"Eliminar vista guardada",

"Research integrity":"Integridad de la investigación",

"Language":"Idioma",
"Search records":"Buscar registros",
"Select website language":"Seleccionar el idioma del sitio",
"Scrollable research results table":"Tabla desplazable de resultados",
"Loading public records…":"Cargando registros públicos…",
"Loading months…":"Cargando meses…",
"Search titles, publishers, DOI, record IDs…":"Buscar por título, entidad editora, DOI o ID del registro…",
"/ search · J/K navigate · Enter details · Esc clear":"/ buscar · J/K navegar · Intro ver detalles · Esc borrar",
"Operational (technical)":"Operativo (estado técnico)",
"Partial sources":"Fallos en algunas fuentes",
"Collection failed":"Error de recopilación",
"Not started":"Pendiente de inicio",
"Unavailable":"No disponible",
"No results":"Sin resultados",
"Records shown":"registros mostrados",
"Some records could not be loaded. Search results may be incomplete.":"Algunos registros no se pudieron cargar. Los resultados pueden estar incompletos.",
"Search covers part of the archive. Choose a first-seen month to narrow the search.":"La búsqueda abarca parte del archivo. Elija un mes de primera detección para acotarla.",
"The review index could not be loaded.":"No se pudo cargar el índice de revisión.",
"Last collection":"Última recopilación",
"Source review needed":"Fuente pendiente de revisión",
"Licence review pending":"Licencia pendiente de revisión",
"Curated references":"Referencias seleccionadas",
"Editorial status":"Estado editorial",
"Reachability":"Disponibilidad del enlace",
"Not independently verified":"Pendiente de verificación independiente",
"Publisher credit is unverified.":"Entidad editora pendiente de verificación.",
"Original discovery link":"Enlace a la pista original",
"Open DOI":"Abrir DOI",
"Publication date":"Fecha de publicación",

"Monitoring query":"Consulta de seguimiento",
"Publisher hint":"Entidad editora indicada",
"Publisher verified":"Entidad editora verificada",
"No":"No",
"Yes":"Sí",
"Source type":"Tipo de fuente",
"Screening status":"Estado del filtrado",
"Event ID":"ID del evento",
"Not assigned":"Pendiente de asignación",
"Topics (preliminary)":"Temas (preliminares)",
"Source inspection":"Revisión de la fuente",
"View saved":"Vista guardada",
"View limit reached (12)":"Se ha alcanzado el límite de 12 vistas",
"View name":"Nombre de la vista",
"Saved view removed":"Vista guardada eliminada",

"Unable to copy automatically; copy the address shown.":"Error al copiar automáticamente. Copie la dirección que se muestra.",
"Date range is reversed.":"La fecha inicial es posterior a la fecha final.",
"Data could not be loaded. Check the GitHub Pages deployment.":"Error al cargar los datos. Compruebe la publicación en GitHub Pages.",
"Source unavailable":"Fuente no disponible",
"No selected record":"Seleccione un registro",
"No active filters":"Sin filtros activos",
"Publication title is shown in its original language.":"El título se muestra en el idioma de publicación.",
}};
const t = s => locale()==='en' ? s : (L[locale()] && L[locale()][s]) || baseI18n.t(s);
const text = (tag,value,className) => {const n=document.createElement(tag); if(className)n.className=className;n.textContent=value==null?'':String(value);return n;};
const TOPICS={
policy:'Policy & governance','forced-labour':'Forced labour','working-conditions':'Working conditions',
'worker-voice':'Worker voice & remedy',network:'Supply networks',research:'Academic research',other:'Other'
};
const COLS=[
 {key:'date',label:'Publication date (UTC)'},{key:'title',label:'Title'},{key:'publisher',label:'Publisher'},
 {key:'topics',label:'Topics'},{key:'kind',label:'Type'},{key:'evidence',label:'Evidence'},{key:'id',label:'Record ID'}
];
const STORAGE='scro.workbench.views.v1', MAX_FILES=24, MAX_ROWS=10000, MAX_PAGE_SIZE=40;
const EDITOR_PAGE_SIZE=10;
const archiveCache=new Map();
let live=null,catalog=null,buildInfo=null,loadedShards=[],activeRecords=[],filtered=[],loading=true,archiveError=false,
 coveragePartial=false,chosen='',firstSeenMonth='',catalogueMonth='';
let pageIndex=0,pageSize=6,pageAnchor=0,locateSelection=false,layoutFrame=0;
let selectedTags=[];
const param = new URL(location.href).searchParams;
const SAFE_SORT=['published-desc','published-asc','observed-desc','title-asc','publisher-asc'];
const SAFE_KIND=['all','discovery','academic'],SAFE_EVIDENCE=['all','unverified','bibliographic'];
const safeValue=(value,allowed,fallback)=>allowed.includes(value)?value:fallback;
function canonicalID(item){return item.record_id || item.id || '';}
const validRecordID=id=>/^[0-9a-f]{18}$/.test(id);
const validMonth=month=>/^\d{4}-(0[1-9]|1[0-2])$/.test(month);
function normalise(item,month) {return {...item,record_id:canonicalID(item),archive_month:month || (item.first_seen||'').slice(0,7)};}
function dateAge(date){const n=Date.parse(date||'');return Number.isFinite(n)?n:0;}
function dateView(date,withTime) {
 return baseI18n.formatDate?.(date,withTime)||'—';
}
function https(value) {try{const u=new URL(value);return u.protocol==='https:' && !u.username && !u.password ? u.href : null;}catch(_){return null;}}
function readControls(){
 return {
 firstSeenMonth,q:$('wb-search').value.trim().slice(0,120),
 from:$('wb-from').value,to:$('wb-to').value,kind:$('wb-kind').value,
 evidence:$('wb-evidence').value,sort:$('wb-sort').value,
 relevance:window.SCRO_REVIEW?.filterValue()||'all',
 topics:[...document.querySelectorAll('[name="wb-topic"]:checked')].map(x=>x.value),tags:[...selectedTags],
 cols:[...document.querySelectorAll('[data-column]:checked')].map(x=>x.dataset.column),
 density:$('wb-density').value,offset:pageIndex*pageSize
 };
}
function applyControls(values) {
 pageAnchor=values.scope==='latest'?0:Math.min(MAX_ROWS,Math.max(0,parseInt(values.offset,10)||0));
 pageIndex=0;
 const month=values.firstSeenMonth||(values.scope==='archive'?values.month:'');
 firstSeenMonth=validMonth(month)?month:'';
 $('wb-sort').value=safeValue(values.sort,SAFE_SORT,'published-desc');
 $('wb-kind').value=safeValue(values.kind,SAFE_KIND,'all');
 $('wb-evidence').value=safeValue(values.evidence,SAFE_EVIDENCE,'all');
 window.SCRO_REVIEW?.setFilter(values.relevance);
 $('wb-search').value=String(values.q||'').slice(0,120);
 selectedTags=recordTags.keys(Array.isArray(values.tags)?values.tags:[]);
 for(const id of ['from','to']) {
  const v=values[id]||'';$('wb-'+id).value=/^\d{4}-\d{2}-\d{2}$/.test(v)?v:'';
 }
 const chosenTopics=Array.isArray(values.topics)?values.topics:[];
 document.querySelectorAll('[name="wb-topic"]').forEach(x=>x.checked=chosenTopics.includes(x.value));
 const columns=Array.isArray(values.cols)?values.cols:COLS.filter(x=>x.key!=='id').map(x=>x.key);
 document.querySelectorAll('[data-column]').forEach(x=>x.checked=x.disabled||columns.includes(x.dataset.column));
 $('wb-density').value=values.density==='comfortable'?'comfortable':'compact';
}
function parseURL(){
 const p=new URL(location.href).searchParams;
 return {scope:p.get('scope'),month:p.get('month'),firstSeenMonth:p.get('firstSeenMonth'),q:p.get('q'),from:p.get('from'),to:p.get('to'),
 kind:p.get('kind'),evidence:p.get('evidence'),sort:p.get('sort'),
 relevance:p.get('relevance'),
 topics:(p.get('topics')||'').split(',').filter(Boolean),tags:(p.get('tag')||'').split(','),cols:p.has('cols')?p.get('cols').split(','):undefined,
 density:p.get('density'),offset:p.get('offset')};
}
const workbenchQueryKeys=['firstSeenMonth','q','from','to','kind','evidence','sort','topics','tag','cols','density','record','offset'];
function updateReaderLink(params){
 const link=$('wb-return-to-reader');
 if(!link)return;
 const destination=new URL('../',location.href);
 destination.searchParams.set('lang',locale());
 for(const key of workbenchQueryKeys){
  const value=params.get(key);
  if(value!==null)destination.searchParams.set(key,value);
 }
 if(firstSeenMonth)destination.searchParams.set('firstSeenMonth',firstSeenMonth);
 link.href=destination.href;
}
function syncURL(){
 const s=readControls(),url=new URL(location.href);
 for(const key of workbenchQueryKeys)url.searchParams.delete(key);
 url.searchParams.delete('scope');
 url.searchParams.delete('month');
 if(s.firstSeenMonth)url.searchParams.set('firstSeenMonth',s.firstSeenMonth);
 if(s.q)url.searchParams.set('q',s.q);
 for(const id of ['from','to'])if(s[id])url.searchParams.set(id,s[id]);
 if(s.kind!=='all')url.searchParams.set('kind',s.kind);
 if(s.evidence!=='all')url.searchParams.set('evidence',s.evidence);
 if(editorMode&&s.relevance!=='all')url.searchParams.set('relevance',s.relevance);
 else url.searchParams.delete('relevance');
 if(s.sort!=='published-desc')url.searchParams.set('sort',s.sort);
 if(s.topics.length)url.searchParams.set('topics',s.topics.join(','));
 if(s.tags.length)url.searchParams.set('tag',s.tags.join(','));
 if(s.cols.join(',')!==COLS.filter(x=>x.key!=='id').map(x=>x.key).join(','))url.searchParams.set('cols',s.cols.join(','));
 if(s.density!=='compact')url.searchParams.set('density',s.density);
 if(chosen)url.searchParams.set('record',chosen);
 if(pageIndex>0)url.searchParams.set('offset',String(pageIndex*pageSize));
 history.replaceState(null,'',url.pathname+url.search+url.hash);
 updateReaderLink(url.searchParams);
}
function localiseStatic(){
 updateReaderLink(new URL(location.href).searchParams);
 document.querySelectorAll('[data-l10n]').forEach(n=>{n.textContent=t(n.dataset.l10n);});
 $('wb-search').placeholder=t('Search titles, publishers, DOI, record IDs…');
 $('language-select').setAttribute('aria-label',t('Select website language'));
 document.title=t(editorMode?'Review Editor':'Research Workbench')+' | Supply Chain Rights Observatory';
 $('wb-table').parentElement.setAttribute('aria-label',t('Paged research results table'));
 populateMonths();
 render();
}
async function fetchJSON(path) {
 const response=await fetch(path,{credentials:'omit',cache:'no-store'});
 if(!response.ok)throw new Error('HTTP '+response.status);
 return response.json();
}

function populateMonths(){
 const select=$('wb-first-seen-month');
 const months=(catalog?.months||[]).map(entry=>entry.month).filter(validMonth);
 select.replaceChildren(new Option(t('All available months'),''),
  ...months.map(month=>new Option(month,month)));
}
function incompleteCoverage(){
 return archiveError||!live||coveragePartial||window.SCRO_RELEVANCE?.failed;
}
function renderStatus(){
 const review=window.SCRO_RELEVANCE;
 const complete=!loading&&!incompleteCoverage();
 let searchableTotal=null;
 if(complete){
  if(!catalogueMonth){
   const rows=activeRecords.filter(row=>review?.included(row)!==false);
   searchableTotal=(review?.distinct?.(rows)??rows).length;
  }
  else if(Number.isSafeInteger(review?.data?.total_records)){
   const excluded=Object.values(review.data.records).filter(row=>row.included===false).length;
   searchableTotal=review.data.total_records-excluded-(review.duplicateCount?.()??0);
  }
 }
 const count=$('wb-searchable-count');
 count.textContent=searchableTotal===null?'—':number(searchableTotal);
 const months=$('wb-first-seen-month');
 if(firstSeenMonth&&![...months.options].some(option=>option.value===firstSeenMonth)){
  months.add(new Option(firstSeenMonth,firstSeenMonth));
 }
 months.value=firstSeenMonth;
 months.disabled=!catalog&&!firstSeenMonth;
 $('wb-legacy-month').hidden=!firstSeenMonth;
 $('wb-legacy-month-value').textContent=firstSeenMonth;
 $('wb-data-status').textContent=!live?t('Unavailable'):live.status==='ok'?t('Operational (technical)'):
  live.status==='partial'?t('Partial sources'):live.status==='failed'?t('Collection failed'):t('Not started');
}
async function fetchMonth(month){
 if(archiveCache.has(month))return archiveCache.get(month);
 const data=(catalog?.months||[]).find(m=>m.month===month);
 if(!data || !/^\d{4}-\d{2}$/.test(month) || !Array.isArray(data.files) || data.files.length>MAX_FILES)throw new Error('Unsupported archive month');
 let all=[];
 for(const part of data.files){
  if(!/^\d{4}-\d{2}-\d{4}\.json$/.test(part.file)||!part.file.startsWith(month+'-'))throw new Error('Invalid archive filename');
  const shard=await fetchJSON(new URL('../data/archive/'+part.file,wbAssetRoot).href);
  if(!Array.isArray(shard.records) || (typeof part.records==='number'&&shard.records.length!==part.records))throw new Error('Archive integrity mismatch');
  const records=shard.records.map(x=>normalise(x,month));
  if(records.some(row=>!validRecordID(row.record_id)))throw new Error('Invalid archive record ID');
  all.push(...records);
  if(all.length>MAX_ROWS)throw new Error('Archive exceeds browser cap');
 }
 if(all.length!==data.records)throw new Error('Archive count mismatch');
 archiveCache.set(month,all);
 return all;
}
async function loadCatalogue(){
 catalogueMonth=firstSeenMonth;
 loading=true;archiveError=false;coveragePartial=false;
 activeRecords=[];loadedShards=[];
 render();
 const recent=new Map(),shards=[];
 for(const row of live?.items||[]){
  if(!row||!validRecordID(canonicalID(row))){archiveError=true;continue;}
  const record=normalise(row);
  recent.set(record.record_id,record);
 }
 const records=catalogueMonth?new Map():new Map(recent);
 try {
  if(!catalog)throw new Error('Archive catalogue unavailable');
  const months=catalogueMonth?catalog.months.filter(entry=>entry.month===catalogueMonth):catalog.months;
  let fileCount=0,rowCount=0;
  for(const month of months){
   const fragments=month.files?.length||0;
   if(fileCount+fragments>MAX_FILES||rowCount+month.records>MAX_ROWS){
    coveragePartial=true;continue;
   }
   fileCount+=fragments;rowCount+=month.records;
   try{
    for(const archived of await fetchMonth(month.month)){
     // Use recent fields with the archive's original observation date.
     const current=recent.get(archived.record_id);
     records.set(archived.record_id,current?{...current,first_seen:archived.first_seen,archive_month:archived.archive_month}:archived);
    }
    shards.push(...month.files.map(part=>part.file));
   }catch(_){archiveError=true;}
  }
 }catch(_){archiveError=true;}
 finally{
  if(catalogueMonth&&(archiveError||coveragePartial)){
   for(const [rid,row] of recent)if(row.archive_month===catalogueMonth&&!records.has(rid))records.set(rid,row);
  }
  activeRecords=[...records.values()];loadedShards=shards;loading=false;
  if(firstSeenMonth!==catalogueMonth)await loadCatalogue();
  else render();
 }
}
function selectedRecords(){
 const c=readControls();
 const from=c.from,to=c.to;
 const {query,tags}=recordTags.search(c.q);
 const requiredTags=[...new Set([...c.tags,...tags])];
 let arr=activeRecords.filter(x=>{
  if(c.firstSeenMonth&&x.archive_month!==c.firstSeenMonth)return false;
  if(requiredTags.length&&!requiredTags.every(tag=>publishedTags(x).includes(tag)))return false;
  if(c.kind!=='all'&&x.kind!==c.kind)return false;
  if(c.evidence==='unverified'&&!String(x.evidence_status).toLowerCase().includes('unverified'))return false;
  if(c.evidence==='bibliographic'&&!String(x.evidence_status).toLowerCase().includes('bibliographic'))return false;
  if(c.topics.length&&!c.topics.some(a=>(x.topics||[]).includes(a)))return false;
  if(from||to){
   const published=baseI18n.utcDateKey(x.published_at);
   if(!published||(from&&published<from)||(to&&published>to))return false;
  }
  if(query){
   const topics=x.topics||[];
   const parts=[x.title,x.publisher_hint,x.source,x.source_id,x.record_id,x.doi,x.evidence_status,x.kind,
    ...topics,...topics.map(key=>t(TOPICS[key]||key))].join(' ');
   const matches=window.SCRO_QUERY?window.SCRO_QUERY.matches(parts,query):parts.toLowerCase().includes(query.toLowerCase());
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
 return editorMode?arr:window.SCRO_RELEVANCE?.distinct?.(arr)??arr;
}
/* Viewport pagination replaces incremental rendering. Only the current page's
   rows enter the DOM. Long cells wrap to three lines; full text stays in the
   inspector and CSV exports always cover the entire filtered selection. */
function setupPagination(){
 document.body.classList.add('wb-paged');
 const stylesheet=document.createElement('link');
 stylesheet.rel='stylesheet';stylesheet.href=new URL('./pagination.css',wbAssetRoot).href;
 if(!editorMode)stylesheet.addEventListener('load',schedulePageLayout);
 document.head.append(stylesheet);
 const controls=text('nav','','wb-page-controls');
 controls.id='wb-page-controls';controls.setAttribute('aria-label',t('Results pagination'));
 const previous=text('button',t('Previous page'),'wb-action');previous.type='button';previous.id='wb-prev';
 previous.setAttribute('aria-controls','wb-tbody');
 const status=text('span','','wb-page-status');status.id='wb-page-status';
 status.setAttribute('role','status');status.setAttribute('aria-live','polite');status.setAttribute('aria-atomic','true');
 // Reuse the old more-results button rather than adding another control below.
 const next=$('wb-more');next.id='wb-next';next.hidden=false;next.textContent=t('Next page');
 next.removeAttribute('data-l10n');next.setAttribute('aria-controls','wb-tbody');
 controls.append(previous,status,next);
 document.querySelector(editorMode?'.wb-results-meta':'.wb-head-actions').append(controls);
 const count=$('wb-count');count.setAttribute('role','status');count.setAttribute('aria-live','polite');count.setAttribute('aria-atomic','true');
 if(editorMode)return;
 window.addEventListener('resize',schedulePageLayout,{passive:true});
 if(window.visualViewport)window.visualViewport.addEventListener('resize',schedulePageLayout,{passive:true});
 if('ResizeObserver' in window){
  // Observe independent geometry, never the table height that this code sets.
  // Sidebars and toolbar text can grow after fonts, locale, density or selection change.
  const dimensions=new WeakMap();
  const results=$('wb-results');
  const observer=new ResizeObserver(entries=>{
   let changed=false;
   for(const entry of entries){
    const width=Math.round(entry.contentRect.width);
    const height=entry.target===results?0:Math.round(entry.contentRect.height);
    const signature=width+':'+height;
    if(dimensions.get(entry.target)!==signature){dimensions.set(entry.target,signature);changed=true;}
   }
   if(changed)schedulePageLayout();
  });
  for(const selector of ['#wb-results','.wb-filters','.wb-inspector','.wb-results-head',
   '#wb-coverage','.wb-results-meta','.wb-pagination','.wb-header','.wb-status-strip','.wb-toolbar']){
   const node=document.querySelector(selector);if(node)observer.observe(node);
  }
 }
 if(document.fonts?.ready)document.fonts.ready.then(schedulePageLayout);
}
function schedulePageLayout(){
 if(layoutFrame)return;
 layoutFrame=requestAnimationFrame(()=>{layoutFrame=0;drawTable();showRecord();});
}
function turnPage(direction){
 const pages=Math.ceil(filtered.length/pageSize);
 const next=Math.max(0,Math.min(Math.max(0,pages-1),pageIndex+direction));
 if(loading||next===pageIndex)return;
 pageAnchor=next*pageSize;
 drawTable();showRecord();syncURL();
}
function sizeReaderPage(wrap,thead,rowHeight){
 // Use the viewport or the natural height of a sidebar sharing the grid row.
 const panel=$('wb-results'),panelBox=panel.getBoundingClientRect();
 const wrapBox=wrap.getBoundingClientRect();
 const scale=wrap.offsetWidth>0?wrapBox.width/wrap.offsetWidth:1;
 const unit=Number.isFinite(scale)&&scale>0?scale:1;
 const viewport=window.visualViewport?.height||window.innerHeight;
 const footer=(document.querySelector('.wb-pagination')?.getBoundingClientRect().height||40)/unit;
 const panelBorder=parseFloat(getComputedStyle(panel).borderBottomWidth)||0;
 const chrome=(wrapBox.top-panelBox.top)/unit+footer+panelBorder;
 const peers=[...document.querySelectorAll('.wb-filters,.wb-inspector')]
  .map(node=>node.getBoundingClientRect())
  .filter(box=>box.width>0&&Math.abs(box.top-panelBox.top)<=2);
 const peerHeight=peers.reduce((height,box)=>Math.max(height,box.height/unit),0);
 const viewportBudget=(viewport-(wrapBox.top+window.scrollY)-22)/unit-footer;
 const preferred=peers.length
  ? Math.max(230,viewportBudget,peerHeight-chrome)
  : Math.max(230,Math.min(760,viewport*.62/unit));
 const headingHeight=Math.ceil(thead.getBoundingClientRect().height/unit)||40;
 const budget=Math.min(headingHeight+MAX_PAGE_SIZE*rowHeight+22,Math.max(headingHeight+rowHeight+22,Math.ceil(preferred)));
 // Leave room for a horizontal scrollbar and keep the frame on the final page.
 wrap.style.height=budget+'px';
 return Math.max(1,Math.min(MAX_PAGE_SIZE,Math.floor((budget-headingHeight-22)/rowHeight)));
}
function drawTable(){
 const c=readControls();filtered=selectedRecords();
 renderTagFilters();
 const table=$('wb-table'),wrap=table.parentElement;
 document.body.classList.toggle('wb-comfortable',c.density==='comfortable');
 const fields=COLS.filter(col=>col.key==='title'||c.cols.includes(col.key));
 const widths={date:88,title:260,publisher:155,topics:165,kind:110,evidence:125,id:155};
 let colgroup=table.querySelector('colgroup');
 if(!colgroup){colgroup=document.createElement('colgroup');table.prepend(colgroup);}
 colgroup.replaceChildren();
 const minWidth=fields.reduce((sum,col)=>sum+widths[col.key],0);
 table.style.minWidth=minWidth+'px';
 for(const field of fields){const col=document.createElement('col');col.style.width=(100*widths[field.key]/minWidth)+'%';colgroup.append(col);}
 const thead=$('wb-thead'),tbody=$('wb-tbody');thead.replaceChildren();tbody.replaceChildren();
 const tr=document.createElement('tr');
 for(const field of fields){
  const th=document.createElement('th');th.scope='col';
  const sort={date:'published',title:'title',publisher:'publisher'}[field.key];
  if(sort){
   const ascending=c.sort.endsWith('-asc'),active=c.sort.startsWith(sort);
   const b=text('button',t(field.label)+(active?(ascending?' ↑':' ↓'):''));b.type='button';
   b.addEventListener('click',()=>{
    $('wb-sort').value=sort==='published'?(c.sort==='published-desc'?'published-asc':'published-desc'):sort+'-asc';
    changed(false);
   });th.append(b);th.setAttribute('aria-sort',active?(ascending?'ascending':'descending'):'none');
  }else th.textContent=t(field.label);
  tr.append(th);
 }
 thead.append(tr);
 const controls=$('wb-page-controls');
 controls.setAttribute('aria-label',t('Results pagination'));
 $('wb-prev').textContent=t('Previous page');$('wb-next').textContent=t('Next page');
 // Fixed-height cells prevent a page from changing shape when long titles wrap.
 const rowHeight=c.density==='comfortable'?84:68;
 table.style.setProperty('--wb-page-row-height',rowHeight+'px');
 pageSize=editorMode?EDITOR_PAGE_SIZE:sizeReaderPage(wrap,thead,rowHeight);
 if(!loading){
  if(locateSelection){const at=filtered.findIndex(x=>x.record_id===chosen);if(at>=0)pageAnchor=at;locateSelection=false;}
  pageIndex=Math.min(Math.max(0,Math.ceil(filtered.length/pageSize)-1),Math.floor(pageAnchor/pageSize));
  pageAnchor=pageIndex*pageSize;
 }
 const start=pageIndex*pageSize,end=Math.min(start+pageSize,filtered.length);
 wrap.scrollTop=0;
 for(const item of filtered.slice(start,end)){
  const row=document.createElement('tr');row.tabIndex=0;row.dataset.recordId=item.record_id;
  row.setAttribute('aria-label',item.title||'');
  if(item.record_id===chosen)row.classList.add('is-selected');
  for(const field of fields){
   const td=document.createElement('td');let value='';
   switch(field.key){
    case 'date':value=dateView(item.published_at,false);td.className='wb-date-cell';break;
    case 'title':value=item.title||'—';td.className='wb-title-cell';td.lang=item.original_language||'und';break;
    case 'publisher':value=item.publisher_hint||t('Not independently verified');break;
    case 'topics':value=(item.topics||[]).map(x=>t(TOPICS[x]||x)).join(', ');break;
    case 'kind':value=t(item.kind==='academic'?'Academic metadata':'Discovery leads');break;
    case 'evidence':value=t(item.evidence_status||'Not independently verified');break;
    case 'id':value=item.record_id;td.className='wb-id-cell';break;
   }
   const cell=text('span',value,'wb-page-cell');cell.title=value;
   td.append(cell);row.append(td);
  }
  row.addEventListener('click',()=>selectRecord(item.record_id));
  row.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();selectRecord(item.record_id);}});
  tbody.append(row);
 }
 if(!filtered.length){
  const row=document.createElement('tr'),cell=text('td',t(loading?'Loading public records…':'No results'));
  row.className='wb-page-empty';cell.colSpan=fields.length;row.append(cell);tbody.append(row);
 }
 const pages=Math.ceil(filtered.length/pageSize);
 $('wb-page-status').textContent=t('Page')+' '+number(pages?pageIndex+1:0)+' '+t('of')+' '+number(pages);
 $('wb-prev').disabled=loading||!pages||pageIndex===0;
 $('wb-next').disabled=loading||!pages||pageIndex>=pages-1;
 $('wb-count').dataset.total=String(filtered.length);
 $('wb-count').textContent=filtered.length?t('Showing')+' '+number(start+1)+'–'+number(end)+' '+t('of')+' '+number(filtered.length)+' '+t('records'):'0 '+t('Records shown');
 const terms=[];
 if(c.q)terms.push(c.q);
 if(c.firstSeenMonth)terms.push(t('First-seen month')+' '+c.firstSeenMonth);
 if(c.topics.length)terms.push(c.topics.map(k=>t(TOPICS[k]||k)).join(' OR '));
 if(c.tags.length)terms.push(c.tags.map(tag=>'#'+tag).join(' '));
 if(c.kind!=='all')terms.push(t(c.kind==='academic'?'Academic metadata':'Discovery leads'));
 if(c.evidence!=='all')terms.push(t(c.evidence==='unverified'?'Unverified discovery':'Bibliographic record'));
 if(c.from)terms.push(t('Published from (UTC)')+' '+c.from);
 if(c.to)terms.push(t('Published through (UTC)')+' '+c.to);
 const relevanceLabel=window.SCRO_REVIEW?.filterLabel();
 if(relevanceLabel)terms.push(relevanceLabel);
 $('wb-active-filters').textContent=terms.join(' · ')||t('No active filters');
 const warnings=[];
 if(!loading){
  if(archiveError||!live)warnings.push(t('Some records could not be loaded. Search results may be incomplete.'));
  if(coveragePartial)warnings.push(t('Search covers part of the archive. Choose a first-seen month to narrow the search.'));
  if(window.SCRO_RELEVANCE?.failed)warnings.push(t('The review index could not be loaded.'));
 }
 if(c.from&&c.to&&c.from>c.to)warnings.push(t('Date range is reversed.'));
 const alert=$('wb-coverage');alert.textContent=warnings.join(' · ');
 alert.classList.toggle('is-alert',warnings.length>0);
 $('wb-export').disabled=$('wb-query-metadata').disabled=loading||(!live&&!catalog);
 if(!loading)syncURL();
}

function filterTag(tag){
 if(tag&&!selectedTags.includes(tag)&&selectedTags.length<recordTags.maxTags){
  selectedTags=recordTags.keys([...selectedTags,tag]);
  changed(false);
 }
}
function renderTagFilters(){
 const select=$('wb-tag-filter'),chips=$('wb-tag-filters'),counts=new Map();
 for(const item of activeRecords){
  if(firstSeenMonth&&item.archive_month!==firstSeenMonth)continue;
  if(window.SCRO_RELEVANCE?.included(item)===false)continue;
  for(const tag of publishedTags(item))counts.set(tag,(counts.get(tag)||0)+1);
 }
 const options=[new Option(t('Choose a tag'),'')];
 for(const tag of [...counts.keys()].sort((a,b)=>a.localeCompare(b,locale()))){
  if(!selectedTags.includes(tag))options.push(new Option('#'+tag+' ('+number(counts.get(tag))+')',tag));
 }
 select.replaceChildren(...options);
 select.disabled=options.length===1||selectedTags.length>=recordTags.maxTags;
 chips.replaceChildren();
 for(const tag of selectedTags){
  const button=text('button','#'+tag+' ×','wb-tag-chip');
  button.type='button';button.setAttribute('aria-label',t('Remove tag filter')+' #'+tag);
  button.addEventListener('click',()=>{
   selectedTags=selectedTags.filter(value=>value!==tag);changed(false);
   (chips.querySelector('button')||(select.disabled?$('wb-search'):select)).focus();
  });
  chips.append(button);
 }
}
function showRecord(){
 const out=$('wb-detail');out.replaceChildren();
 const item=activeRecords.find(x=>x.record_id===chosen);
 if(!item){out.append(text('p',t('Select a record to inspect its provenance, dates and evidence status.'),'wb-empty'));return;}
 out.append(text('h3',item.title));
 const dl=document.createElement('dl');
 const fields=[
  ['Record ID',item.record_id],['Publication date (UTC)',dateView(item.published_at,true)],
  ['First observed',dateView(item.first_seen,true)],['Publisher hint',item.publisher_hint||t('Source unavailable')],
  ['Publisher verified',t(item.publisher_verified?'Yes':'No')],['Monitoring query',t(item.source||'Unknown')],
  ['Source type',t(item.kind==='academic'?'Academic metadata':'Discovery leads')],
  ['Evidence class',t(item.evidence_status||'Not independently verified')],
  ['Screening status',item.screening_status?t(({candidate_relevant:'Passed preliminary screening',excluded:'Excluded by preliminary screening'})[item.screening_status]||item.screening_status):'—'],
  ['Topics (preliminary)',(item.topics||[]).map(x=>t(TOPICS[x]||x)).join(', ')],
  ['Event ID',item.event_id||t('Not assigned')]
 ];
 if(item.doi)fields.push(['DOI',item.doi]);
 for(const [key,val] of fields){dl.append(text('dt',t(key)),text('dd',val));}
 out.append(dl);
 const tags=publishedTags(item);
 if(tags.length){
  const group=text('div','','wb-tag-chips');
  group.setAttribute('role','group');group.setAttribute('aria-label',t('Custom tags'));
  for(const tag of tags){
   const button=text('button','#'+tag,'wb-tag-chip');
   button.type='button';button.addEventListener('click',()=>{filterTag(tag);$('wb-search').focus();});
   group.append(button);
  }
  out.append(text('h4',t('Custom tags'),'wb-tags-heading'),group);
 }
 const links=text('div','','wb-detail-links');
 const url=https(item.canonical_url)||https(item.url);
 if(url){
  const link=text('a',t(item.doi?'Open DOI':'Original discovery link'));link.href=url;link.target='_blank';link.rel='noopener noreferrer';links.append(link);
 }
 const urlMonth=item.archive_month;
 if(urlMonth&&/^\d{4}-\d{2}$/.test(urlMonth)){
  const detailURL=new URL('../record.html',wbAssetRoot);
  const current=new URL(location.href).searchParams,back=new URLSearchParams();
  for(const key of workbenchQueryKeys)if(current.has(key))back.set(key,current.get(key));
  detailURL.search=new URLSearchParams({month:urlMonth,id:item.record_id,lang:locale(),back:back.toString()});
  const detail=text('a',t('Record ID'));detail.href=detailURL.href;
  links.append(detail);
 }
 out.append(links);
 out.append(text('p',t('Publication title is shown in its original language.'),'wb-empty'));
}
function selectRecord(id){
 chosen=id;
 const at=filtered.findIndex(x=>x.record_id===id);
 if(at>=0 && Math.floor(at/pageSize)!==pageIndex){pageAnchor=at;drawTable();}
 syncURL();showRecord();
 document.querySelectorAll('#wb-tbody tr').forEach(row=>row.classList.toggle('is-selected',row.dataset.recordId===id));
}
function render(){renderStatus();drawTable();showRecord();}
function changed(keepPosition=false){
 if(!keepPosition){pageAnchor=0;pageIndex=0;}
 syncURL();
 if(!loading&&firstSeenMonth!==catalogueMonth)loadCatalogue();
 else render();
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
 const suffix=incompleteCoverage()?'-PARTIAL':'';
 download(csv,'text/csv;charset=utf-8','scro-records'+suffix+'-'+new Date().toISOString().slice(0,10)+'.csv');
}
function exportQueryMetadata(){
 const {firstSeenMonth,q,from,to,kind,evidence,sort,relevance,topics,tags}=readControls();
 const data={schema_version:1,language:locale(),filters:{firstSeenMonth,q,from,to,kind,evidence,sort,relevance,topics,tags},
  coverage:incompleteCoverage()?'partial':'requested_scope_complete',loaded_records:activeRecords.length,
  matched_records:filtered.length,shards:loadedShards,build:buildInfo,exported_at:new Date().toISOString()};
 download(JSON.stringify(data,null,2)+'\n','application/json','scro-query.json');
}
function download(content,type,filename){
 const blob=new Blob([content],{type});
 const url=URL.createObjectURL(blob);
 const a=document.createElement('a');a.href=url;a.download=filename;
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
 const url=new URL(location.href);url.searchParams.set('lang',locale());
 try {await navigator.clipboard.writeText(url.href);feedback('Shareable link copied');}
 catch(_){window.prompt(t('Unable to copy automatically; copy the address shown.'),url.href);}
}
function reset(){
 applyControls({sort:'published-desc',kind:'all',evidence:'all'});
 chosen='';changed();
}
function setPreset(key){
 const base={sort:'published-desc',kind:'all',evidence:'all'};
 if(key==='labour')base.topics=['forced-labour','working-conditions','worker-voice'];
 if(key==='policy')base.topics=['policy','network'];
 if(key==='academic')base.kind='academic';
 applyControls(base);chosen='';changed();
}
async function init(){
 applyControls(parseURL());
 chosen=(param.get('record')||'').match(/^[0-9a-f]{18}$/)?.[0]||'';
 locateSelection=Boolean(chosen);
 localiseStatic();
 const [snapshot,archive,build]=await Promise.allSettled([
  fetchJSON(new URL('../data/latest.json',wbAssetRoot).href),
  fetchJSON(new URL('../data/archive/catalog.json',wbAssetRoot).href),
  fetchJSON(new URL('../data/build-info.json',wbAssetRoot).href)
 ]);
 if(snapshot.status==='fulfilled'&&Array.isArray(snapshot.value?.items))live=snapshot.value;
 window.SCRO_COLLECTION_TIME?.set(live?.last_successful_collection);
 if(archive.status==='fulfilled'&&Array.isArray(archive.value?.months))catalog=archive.value;
 if(build.status==='fulfilled'&&build.value?.schema_version===1)buildInfo=build.value;
 populateMonths();
 await loadCatalogue();
}
function bind(){
 setupPagination();
 window.SCRO_WORKBENCH=Object.freeze({
  getRecord:id=>{
   const record=activeRecords.find(x=>x.record_id===id);
   return record?{record_id:record.record_id,title:record.title}:null;
  }
 });
 window.addEventListener('scro:select-record',event=>{
  const rid=event.detail?.record_id;
  if(typeof rid!=='string'||!/^[a-f0-9]{18}$/.test(rid))return;
  if(activeRecords.some(row=>row.record_id===rid)){
   selectRecord(rid);
   document.getElementById('review-panel')?.scrollIntoView({block:'nearest'});
  }else{
   const url=new URL(location.href);
   url.searchParams.set('record',rid);
   for(const key of ['q','from','to','kind','evidence','topics','tag','relevance','offset','scope','month','firstSeenMonth'])url.searchParams.delete(key);
   location.assign(url.href);
  }
 });
 for(const id of ['wb-search','wb-sort','wb-kind','wb-evidence','wb-from','wb-to','wb-density'])
  $(id).addEventListener(id==='wb-search'?'input':'change',()=>changed(id==='wb-density'));
 $('wb-first-seen-month').addEventListener('change',event=>{
  firstSeenMonth=event.target.value;chosen='';changed();
 });
 $('wb-clear-legacy-month').addEventListener('click',()=>{
  firstSeenMonth='';changed();$('wb-search').focus();
 });
 $('wb-tag-filter').addEventListener('change',event=>{filterTag(event.target.value);});
 document.querySelectorAll('[name="wb-topic"],[data-column]').forEach(x=>x.addEventListener('change',()=>changed(Boolean(x.dataset.column))));
 $('wb-clear').addEventListener('click',reset);
 $('wb-export').addEventListener('click',exportCSV);
 $('wb-query-metadata').addEventListener('click',exportQueryMetadata);
 $('wb-prev').addEventListener('click',()=>turnPage(-1));
 $('wb-next').addEventListener('click',()=>turnPage(1));
 $('wb-deselect').addEventListener('click',()=>selectRecord(''));
 $('wb-share').addEventListener('click',share);
 $('wb-save').addEventListener('click',saveView);
 $('wb-remove-view').addEventListener('click',()=>{
  const id=$('wb-saved-list').value;if(!id)return;
  if(saveViews(views().filter(x=>x.id!==id))){populateViews();feedback('Saved view removed');}
 });
 $('wb-saved-list').addEventListener('change',()=>{
  const v=views().find(x=>x.id===$('wb-saved-list').value);
  if(v){applyControls(v.state);chosen='';changed();}
 });
 document.querySelectorAll('[data-preset]').forEach(x=>x.addEventListener('click',()=>setPreset(x.dataset.preset)));
 window.addEventListener('keydown',e=>{
  const tag=e.target?.tagName||'';
  const editing=/^(INPUT|TEXTAREA|SELECT)$/.test(tag)||e.target?.isContentEditable;
  if(e.defaultPrevented)return;
  if(e.key==='Escape'){if(chosen){selectRecord('');e.preventDefault();}return;}
  if(editing || e.ctrlKey||e.metaKey||e.altKey)return;
  if(e.key==='/'){e.preventDefault();$('wb-search').focus();return;}
  if(e.key==='j'||e.key==='k'){
   if(!filtered.length)return;e.preventDefault();
   const idx=filtered.findIndex(x=>x.record_id===chosen);
   const newIndex=e.key==='j'?Math.min(filtered.length-1,idx+1):Math.max(0,idx<0?0:idx-1);
   selectRecord(filtered[newIndex].record_id);
  }else if(e.key==='Enter'&&chosen){showRecord();$('wb-detail').scrollIntoView({block:'nearest'});}
 });
 baseI18n.onChange(localiseStatic);
 populateViews();
}
bind();init();
})();
