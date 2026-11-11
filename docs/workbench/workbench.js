/* Research workbench for filtering, inspecting and exporting records. */
(() => {
'use strict';
const $ = id => document.getElementById(id);
const baseI18n = window.SCRO_I18N || {language:'en', t:x=>x, onChange:()=>{}};
const locale = () => baseI18n.language || 'en';
const number = value => baseI18n.formatNumber?.(value)??String(value);
const wbAssetRoot=new URL('./',document.currentScript.src);
const editorMode=document.body.dataset.page==='workbench-editor';
const L = {
zh:{
"Advanced tools":"進階工具",
"Open Review Editor":"開啟研究編輯頁",
"You are in the Review Editor":"您正在使用審核編輯器",
"Return to the read-only view":"返回檢視頁",
"Review Editor":"研究編輯工作台",
"Record scope":"資料範圍",
"Select record scope":"選擇資料範圍",
"All searchable records":"全部可搜尋紀錄",
"Recent snapshot":"近期快照",
"First-seen month":"首次收錄月份",
"Recent snapshot records":"近期快照筆數",
"Permanent archive records":"歷史封存筆數",
"All searchable records combine current and archived items by ID. Partial coverage is indicated when limits are reached.":"將近期與歷史資料依識別編號去重合併；超過載入限制時會顯示部分涵蓋。",
"Recent snapshot retains up to 150 days and 240 records; it overlaps with the permanent archive.":"近期快照最多保留150天及240筆紀錄，與永久歷史封存可能重疊。",
"Archive month groups records by first observed date, not publication date.":"歷史月份依首次收錄日期分組，不是新聞發布日期。",
'Previous page':'上一頁','Next page':'下一頁','Page':'第','of':'／','Showing':'顯示','records':'筆','Results pagination':'結果分頁','Paged research results table':'分頁研究結果表格','Full text in record inspector':'完整內容請見右側紀錄詳情',
'Skip to results':'跳至搜尋結果','Visitor portal':'一般訪客首頁','Research Workbench':'專業研究工作台',
'Latest records':'最新情報','Historical records':'歷史紀錄',
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
'Workspace & sharing':'工作區與分享',
'Saved views stay in this browser. Shared links include the current search terms.':'已儲存的視圖保留在此瀏覽器。分享連結會包含目前的搜尋條件。',
'Save current view':'儲存目前視圖','Choose a saved view':'選擇已儲存視圖',
'Delete saved view':'刪除已儲存視圖','Copy shareable link':'複製分享連結','Research integrity':'研究完整性',
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
'Original discovery link':'原始線索連結','Open DOI':'開啟 DOI','Publication date':'發布日期',
'First observed':'首次觀測','Monitoring query':'監測查詢','Publisher hint':'出版者線索',
'Publisher verified':'出版者已查核','No':'否','Yes':'是','Source type':'資料類型',
'Screening status':'初篩狀態','Event ID':'事件編號','Not assigned':'尚未指派',
'Topics (preliminary)':'主題（初步分類）','Source inspection':'來源查核',
'View saved':'視圖已儲存','View limit reached (12)':'已達儲存上限（12）',
'View name':'視圖名稱','Saved view removed':'已刪除儲存視圖',
'Shareable link copied':'分享連結已複製','Unable to copy automatically; copy the address shown.':'無法自動複製，請複製顯示的網址。',
'Date range is reversed.':'日期範圍前後相反。',
'Data could not be loaded. Check the GitHub Pages deployment.':'資料載入失敗；請檢查 GitHub Pages 部署。',
'Source unavailable':'來源不明','No selected record':'尚未選取紀錄','No active filters':'尚無篩選條件',
'Publication title is shown in its original language.':'出版標題保留原始語言。',
},
de:{
"Advanced tools":"Erweiterte Werkzeuge",
"Open Review Editor":"Review-Editor öffnen",
"You are in the Review Editor":"Sie befinden sich im Review-Editor",
"Return to the read-only view":"Zurück zur Leseansicht",
"Review Editor":"Review-Editor",
"Record scope":"Datenbereich",
"Select record scope":"Datenbereich auswählen",
"All searchable records":"Alle durchsuchbaren Datensätze",
"Recent snapshot":"Aktueller Datenausschnitt",
"First-seen month":"Monat der Ersterfassung",
"Recent snapshot records":"Aktueller Datenbestand",
"Permanent archive records":"Historische Archivdatensätze",
"All searchable records combine current and archived items by ID. Partial coverage is indicated when limits are reached.":"Aktuelle und archivierte Datensätze werden anhand ihrer IDs zusammengeführt. Bei Begrenzungen wird eine unvollständige Abdeckung angezeigt.",
"Recent snapshot retains up to 150 days and 240 records; it overlaps with the permanent archive.":"Der aktuelle Datenausschnitt enthält höchstens 150 Tage und 240 Datensätze; Überschneidungen mit dem Archiv sind möglich.",
"Archive month groups records by first observed date, not publication date.":"Archivmonate beziehen sich auf die Ersterfassung, nicht auf das Veröffentlichungsdatum.",
'Previous page':'Vorherige Seite','Next page':'Nächste Seite','Page':'Seite','of':'von','Showing':'Anzeige','records':'Einträge','Results pagination':'Ergebnisseiten','Paged research results table':'Seitengesteuerte Ergebnistabelle','Full text in record inspector':'Volltext in den Datensatzdetails',
'Skip to results':'Zu den Suchergebnissen','Visitor portal':'Besucherportal','Research Workbench':'Forschungsarbeitsplatz',
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
'Workspace & sharing':'Arbeitsbereich & Teilen',
'Saved views stay in this browser. Shared links include the current search terms.':'Gespeicherte Ansichten bleiben in diesem Browser. Geteilte Links enthalten die aktuellen Suchbegriffe.',
'Save current view':'Ansicht speichern','Choose a saved view':'Gespeicherte Ansicht auswählen',
'Delete saved view':'Ansicht löschen','Copy shareable link':'Link kopieren','Research integrity':'Forschungsintegrität',
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
'Original discovery link':'Originalhinweis öffnen','Open DOI':'DOI öffnen','Publication date':'Veröffentlichungsdatum',
'First observed':'Erstmals erfasst','Monitoring query':'Suchabfrage','Publisher hint':'Herausgeberhinweis',
'Publisher verified':'Herausgeber überprüft','No':'Nein','Yes':'Ja','Source type':'Quellentyp',
'Screening status':'Vorsortierungsstatus','Event ID':'Ereignis-ID','Not assigned':'Nicht zugewiesen',
'Topics (preliminary)':'Themen (vorläufig)','Source inspection':'Quellenprüfung',
'View saved':'Ansicht gespeichert','View limit reached (12)':'Limit erreicht (12)',
'View name':'Name der Ansicht','Saved view removed':'Ansicht gelöscht',
'Shareable link copied':'Link kopiert','Unable to copy automatically; copy the address shown.':'Automatisches Kopieren nicht möglich; angezeigte Adresse kopieren.',
'Date range is reversed.':'Datumsbereich ist umgekehrt.',
'Data could not be loaded. Check the GitHub Pages deployment.':'Daten konnten nicht geladen werden; GitHub-Pages-Bereitstellung prüfen.',
'Source unavailable':'Quelle unbekannt','No selected record':'Kein Datensatz ausgewählt',
'No active filters':'Keine aktiven Filter','Publication title is shown in its original language.':'Originaltitel bleibt in der Veröffentlichungssprache.',
},
es:{
"Other":"Otros",
"Advanced tools":"Herramientas avanzadas",
"Open Review Editor":"Abrir el editor de revisión",
"You are in the Review Editor":"Está en el editor de revisión",
"Return to the read-only view":"Volver a la vista de solo lectura",
"Review Editor":"Editor de revisión",
"Record scope":"Alcance de la búsqueda",
"Select record scope":"Seleccionar el alcance de la búsqueda",
"All searchable records":"Todos los registros consultables",
"Recent snapshot":"Datos recientes",
"First-seen month":"Mes de primera detección",
"Recent snapshot records":"Registros recientes",
"Permanent archive records":"Registros del archivo permanente",
"All searchable records combine current and archived items by ID. Partial coverage is indicated when limits are reached.":"Los registros recientes y archivados se combinan por identificador. Si se alcanza el límite de carga, se indica que la cobertura es parcial.",
"Recent snapshot retains up to 150 days and 240 records; it overlaps with the permanent archive.":"La vista de datos recientes conserva hasta 150 días y 240 registros. Puede incluir registros del archivo permanente.",
"Archive month groups records by first observed date, not publication date.":"El archivo agrupa los registros por mes de primera detección. Los filtros de publicación usan la fecha de publicación.",
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
"Research Workbench":"Espacio de investigación",
"Latest records":"Registros recientes",
"Historical records":"Registros históricos",
"Collection status":"Estado de la recopilación",
"Last successful update (Taipei)":"Última actualización exitosa (Taipéi)",
"Source directory":"Directorio de fuentes",
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
"Academic metadata":"Metadatos académicos",
"Discovery leads":"Referencias para investigación",
"Evidence class":"Categoría de evidencia",
"Any evidence class":"Cualquier categoría de evidencia",
"Unverified discovery":"Referencia sin verificar",
"Bibliographic record":"Registro bibliográfico",
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
"Copy shareable link":"Copiar enlace para compartir",
"Research integrity":"Integridad de la investigación",
"Methods & limitations":"Métodos y limitaciones",
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
"No records in this scope":"Sin registros en este ámbito",
"Records shown":"registros mostrados",
"Records loaded":"registros cargados",
"Scope: latest snapshot":"Alcance: datos recientes",
"Scope: archive month":"Alcance: mes del archivo",
"Scope: combined catalogue":"Alcance: catálogo combinado",
"All available archive shards loaded.":"Se han cargado todos los segmentos disponibles del archivo.",
"Partial archive scope: only recent shards loaded. Narrow the month or use the canonical archive for full analysis.":"Cobertura parcial. Acote el mes o use el archivo JSONL para consultar el historial completo.",
"Archive could not be loaded; results are not complete.":"Error al cargar el archivo. Los resultados están incompletos.",
"Loading historical records…":"Cargando registros históricos…",
"Last collection":"Última recopilación",
"Source review needed":"Fuente pendiente de revisión",
"Licence review pending":"Licencia pendiente de revisión",
"Curated references":"Referencias seleccionadas",
"Editorial status":"Estado editorial",
"Reachability":"Disponibilidad del enlace",
"Not independently verified":"Pendiente de verificación independiente",
"Publisher credit is unverified.":"Entidad editora pendiente de verificación.",
"Original discovery link":"Enlace a la referencia original",
"Open DOI":"Abrir DOI",
"Publication date":"Fecha de publicación",
"First observed":"Primera detección",
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
"Shareable link copied":"Enlace copiado",
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
 {key:'date',label:'Date'},{key:'title',label:'Title'},{key:'publisher',label:'Publisher'},
 {key:'topics',label:'Topics'},{key:'kind',label:'Type'},{key:'evidence',label:'Evidence'},{key:'id',label:'Record ID'}
];
const STORAGE='scro.workbench.views.v1', MAX_FILES=24, MAX_ROWS=10000, MAX_PAGE_SIZE=40;
const EDITOR_PAGE_SIZE=10;
let live=null,catalog=null,latest=[],archiveCache=new Map(),activeRecords=[],filtered=[],
scopeStatus='',loading=false,archiveError=false,coveragePartial=false,chosen='',runNumber=0;
let pageIndex=0,pageSize=6,pageAnchor=0,locateSelection=false,layoutFrame=0;
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
 return new Intl.DateTimeFormat(({en:'en-GB',zh:'zh-TW',de:'de-DE',es:'es-ES'})[locale()]||'en-GB',opts).format(value);
}
function https(value) {try{const u=new URL(value);return u.protocol==='https:' && !u.username && !u.password ? u.href : null;}catch(_){return null;}}
function readControls(){
 return {
 scope:$('wb-scope').value,month:$('wb-month').value,q:$('wb-search').value.trim().slice(0,120),
 from:$('wb-from').value,to:$('wb-to').value,kind:$('wb-kind').value,
 evidence:$('wb-evidence').value,sort:$('wb-sort').value,
 topics:[...document.querySelectorAll('[name="wb-topic"]:checked')].map(x=>x.value),
 cols:[...document.querySelectorAll('[data-column]:checked')].map(x=>x.dataset.column),
 density:$('wb-density').value,offset:pageIndex*pageSize
 };
}
function applyControls(values) {
 pageAnchor=Math.min(MAX_ROWS,Math.max(0,parseInt(values.offset,10)||0));
 pageIndex=0;
 $('wb-scope').value=safeValue(values.scope,SAFE_SCOPE,'all');
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
 density:p.get('density'),offset:p.get('offset')};
}
const workbenchQueryKeys=['scope','month','q','from','to','kind','evidence','sort','topics','cols','density','record','offset'];
function updateReaderLink(params){
 const link=$('wb-return-to-reader');
 if(!link)return;
 const destination=new URL('../',location.href);
 destination.searchParams.set('lang',locale());
 for(const key of workbenchQueryKeys){
  const value=params.get(key);
  if(value!==null)destination.searchParams.set(key,value);
 }
 link.href=destination.href;
}
function syncURL(){
 const s=readControls(),url=new URL(location.href);
 for(const key of workbenchQueryKeys)url.searchParams.delete(key);
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
 if(pageIndex>0)url.searchParams.set('offset',String(pageIndex*pageSize));
 history.replaceState(null,'',url.pathname+url.search+url.hash);
 updateReaderLink(url.searchParams);
}
function updateRecordScope(){
 const value=$('wb-scope')?.value||'all';
 document.querySelectorAll('[data-scope]').forEach(button=>{
  const active=button.dataset.scope===value;
  button.setAttribute('aria-pressed',String(active));
  button.textContent=t(button.dataset.l10n||button.textContent);
 });
 const explanations={
  all:'All searchable records combine current and archived items by ID. Partial coverage is indicated when limits are reached.',
  latest:'Recent snapshot retains up to 150 days and 240 records; it overlaps with the permanent archive.',
  archive:'Archive month groups records by first observed date, not publication date.'
 };
 const label=$('wb-scope-hint');if(label)label.textContent=t(explanations[value]||explanations.all);
 const month=$('wb-month')?.closest('label');if(month)month.hidden=value!=='archive';
 const scope=document.querySelector('.wb-scope-nav');
 if(scope)scope.setAttribute('aria-label',t('Record scope'));
 const tabs=document.querySelector('.wb-scope-tabs');
 if(tabs)tabs.setAttribute('aria-label',t('Select record scope'));
}
function localiseStatic(){
 updateReaderLink(new URL(location.href).searchParams);
 document.querySelectorAll('[data-l10n]').forEach(n=>{n.textContent=t(n.dataset.l10n);});
 $('wb-search').placeholder=t('Search titles, publishers, DOI, record IDs…');
 $('language-select').setAttribute('aria-label',t('Select website language'));
 document.title=t(editorMode?'Review Editor':'Research Workbench')+' | Supply Chain Rights Observatory';
 updateRecordScope();
 $('wb-table').parentElement.setAttribute('aria-label',t('Paged research results table'));
 render();
}
async function fetchJSON(path) {
 const response=await fetch(path,{credentials:'omit',cache:'no-store'});
 if(!response.ok)throw new Error('HTTP '+response.status);
 return response.json();
}

function renderStatus(){
 updateRecordScope();
 $('wb-latest-count').textContent=live?number(latest.length):'—';
 $('wb-archive-count').textContent=catalog?number(catalog.total_records):'—';
 $('wb-data-status').textContent=!live?t('Unavailable'):live.status==='ok'?t('Operational (technical)'):
  live.status==='partial'?t('Partial sources'):live.status==='failed'?t('Collection failed'):t('Not started');
 $('wb-updated').textContent=live?dateView(live.last_successful_collection,true):'—';
}
async function fetchMonth(month){
 if(archiveCache.has(month))return archiveCache.get(month);
 const data=(catalog?.months||[]).find(m=>m.month===month);
 if(!data || !/^\d{4}-\d{2}$/.test(month) || !Array.isArray(data.files) || data.files.length>MAX_FILES)throw new Error('Unsupported archive month');
 let all=[];
 for(const part of data.files){
  if(!/^\d{4}-\d{2}-\d{4}\.json$/.test(part.file))throw new Error('Unsafe archive filename');
  const shard=await fetchJSON(new URL('../data/archive/'+part.file,wbAssetRoot).href);
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
 if(!loading && live){
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
  const row=document.createElement('tr'),cell=text('td',t(loading?'Loading historical records…':archiveError?'Archive could not be loaded; results are not complete.':'No results'));
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
 if(c.topics.length)terms.push(c.topics.map(k=>t(TOPICS[k]||k)).join(' OR '));
 if(c.kind!=='all')terms.push(t(c.kind==='academic'?'Academic metadata':'Discovery leads'));
 $('wb-active-filters').textContent=terms.join(' · ')||t('No active filters');
 let status=c.scope==='latest'?t('Scope: latest snapshot'):c.scope==='archive'?t('Scope: archive month')+': '+c.month:t('Scope: combined catalogue');
 if(loading)status+=' · '+t('Loading historical records…');
 else if(archiveError)status+=' · '+t('Archive could not be loaded; results are not complete.');
 else if(coveragePartial)status+=' · '+t('Partial archive scope: only recent shards loaded. Narrow the month or use the canonical archive for full analysis.');
 else if(c.scope==='all')status+=' · '+t('All available archive shards loaded.');
 else status+=' · '+number(activeRecords.length)+' '+t('Records loaded');
 if(c.from&&c.to&&c.from>c.to)status+=' · '+t('Date range is reversed.');
 const alert=$('wb-coverage');alert.textContent=status;
 alert.classList.toggle('is-alert',archiveError||coveragePartial||Boolean(c.from&&c.to&&c.from>c.to));
 if(live&&!loading)syncURL();
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
  const detail=text('a',t('Record ID'));detail.href=new URL('../record.html?month='+encodeURIComponent(urlMonth)+'&id='+encodeURIComponent(item.record_id),wbAssetRoot).href;
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
function changed(reload,keepPosition=false){
 if(!keepPosition){pageAnchor=0;pageIndex=0;}
 syncURL();
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
 const url=new URL(location.href);url.searchParams.set('lang',locale());
 try {await navigator.clipboard.writeText(url.href);feedback('Shareable link copied');}
 catch(_){window.prompt(t('Unable to copy automatically; copy the address shown.'),url.href);}
}
function reset(){
 applyControls({scope:'all',sort:'published-desc',kind:'all',evidence:'all'});
 chosen='';changed(true);
}
function setPreset(key){
 const base={scope:'all',sort:'published-desc',kind:'all',evidence:'all'};
 if(key==='labour')base.topics=['forced-labour','working-conditions','worker-voice'];
 if(key==='policy')base.topics=['policy','network'];
 if(key==='academic')base.kind='academic';
 applyControls(base);chosen='';changed(true);
}
async function init(){
 applyControls(parseURL());
 chosen=(param.get('record')||'').match(/^[0-9a-f]{18}$/)?.[0]||'';
 locateSelection=Boolean(chosen);
 localiseStatic();
 try{
  const [a,b]=await Promise.allSettled([
   fetchJSON(new URL('../data/latest.json',wbAssetRoot).href),
   fetchJSON(new URL('../data/archive/catalog.json',wbAssetRoot).href)
  ]);
  if(a.status!=='fulfilled'||!Array.isArray(a.value.items))throw Error('Latest snapshot unavailable');
  live=a.value;
  latest=live.items.map(x=>normalise(x)).filter(x=>/^[0-9a-f]{18}$/.test(x.record_id));
  catalog=b.status==='fulfilled'&&Array.isArray(b.value.months)?b.value:null;
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
   url.searchParams.set('scope','all');url.searchParams.set('record',rid);
   for(const key of ['q','from','to','kind','evidence','topics','relevance','offset','month'])url.searchParams.delete(key);
   location.assign(url.href);
  }
 });
 for(const id of ['wb-search','wb-sort','wb-kind','wb-evidence','wb-from','wb-to','wb-density'])
  $(id).addEventListener(id==='wb-search'?'input':'change',()=>changed(false,id==='wb-density'));
 $('wb-scope').addEventListener('change',()=>changed(true));
 document.querySelectorAll('[data-scope]').forEach(button=>button.addEventListener('click',()=>{
  if($('wb-scope').value===button.dataset.scope)return;
  $('wb-scope').value=button.dataset.scope;
  chosen='';changed(true);
 }));
 $('wb-month').addEventListener('change',()=>changed(true));
 document.querySelectorAll('[name="wb-topic"],[data-column]').forEach(x=>x.addEventListener('change',()=>changed(false,Boolean(x.dataset.column))));
 $('wb-clear').addEventListener('click',reset);
 $('wb-export').addEventListener('click',exportCSV);
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
   selectRecord(filtered[newIndex].record_id);
  }else if(e.key==='Enter'&&chosen){showRecord();$('wb-detail').scrollIntoView({block:'nearest'});}
 });
 baseI18n.onChange(localiseStatic);
 populateViews();
}
bind();init();
})();
