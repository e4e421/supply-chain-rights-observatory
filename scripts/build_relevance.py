#!/usr/bin/env python3
"""Post-build relevance sidecars. Never edits canonical archive or invents human labels."""
import hashlib,json,sys
from pathlib import Path
from relevance_engine import ROOT,analyze,decorate,digest,similarities,validate_overlay,rules
OUT=ROOT/'_site'

def load_records():
    records={}
    for file in sorted((ROOT/'docs/data/archive').glob('????-??-????.json')):
        for row in json.loads(file.read_text())['records']:records[row['record_id']]=row
    for row in json.loads((ROOT/'docs/data/latest.json').read_text())['items']:
        rid=row.get('record_id') or row.get('id')
        records[rid]={**records.get(rid,{}),**row,'record_id':rid}
    return records

def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')

def integrate_runtime():
    """Explicit fail-closed build hooks; source pages and canonical data remain unchanged."""
    patches={
      'workbench/workbench.js':[
        ("const locale = () => baseI18n.language || 'en';", "const locale = () => baseI18n.language || 'en';\nconst relevance=window.SCRO_RELEVANCE,reviewPanel=window.SCRO_REVIEW;\nreviewPanel?.connect(()=>changed(false));"),
        ("function normalise(item,month) {return {...item,record_id:canonicalID(item),archive_month:month || (item.first_seen||'').slice(0,7)};}", "function normalise(item,month) {const row={...item,record_id:canonicalID(item),archive_month:month || (item.first_seen||'').slice(0,7)};return relevance?relevance.apply(row):row;}"),
        ("let arr=activeRecords.filter(x=>{", "let arr=activeRecords.filter(x=>{\n if(reviewPanel&&!reviewPanel.includes(x))return false;\n if(!reviewPanel&&relevance&&!relevance.included(x))return false;"),
        ("function showRecord(){", "function showRecord(){\n reviewPanel?.inspect(activeRecords.find(x=>x.record_id===chosen)||null);"),
        ("t(item.publisher_verified?'Yes':'No')", "t((item.publisher_confirmed||item.publisher_verified)?'Yes':'No')"),
        ("const url=https(item.canonical_url)||https(item.url);", "const url=https(item.reviewed_canonical_url)||https(item.canonical_url)||https(item.url);"),
        ("'topics','doi','url'];", "'topics','doi','url','relevance_level','rule_version','review_state','manual_relevance'];"),
        ("async function init(){", "async function init(){\n if(relevance)await relevance.ready;\n reviewPanel?.refresh();")
      ],
      'portal.js':[
        ("const t=x=>", "const relevance=window.SCRO_RELEVANCE;\nconst t=x=>"),
        ("(live?.items||[]).slice(0,6)", "(live?.items||[]).filter(r=>!relevance||relevance.included(r)).map(r=>relevance?relevance.apply(r):r).slice(0,6)"),
        ("archiveRows.filter(r=>{", "archiveRows.filter(r=>{if(relevance&&!relevance.included(r))return false;"),
        ("archiveRows=[...records.values()];", "archiveRows=[...records.values()].map(r=>relevance?relevance.apply(r):r);"),
        ("'topics','doi','url'];const rows=", "'topics','doi','url','relevance_level','rule_version','review_state','manual_relevance'];const rows="),
        ("rec=shard.records.find(r=>r.record_id===id);", "rec=shard.records.find(r=>r.record_id===id);if(rec&&relevance)rec=relevance.apply(rec);"),
        ("const title=node('h2',rec.title);", "if(relevance&&!relevance.included(rec))root.append(node('p',t('Excluded by editorial review. The original observation is retained.'),'portal-notice'));\n const title=node('h2',rec.title);"),
        ("['Publisher credit (unverified)',rec.publisher_hint", "[rec.publisher_confirmed?'Publisher confirmed':'Publisher credit (unverified)',rec.publisher_hint"),
        ("publicLink(rec.url,'Open original discovery link')", "publicLink(rec.reviewed_canonical_url||rec.url,'Open original discovery link')"),
        ("async function start(){", "async function start(){\n if(relevance){await relevance.ready;if(relevance.failed)document.querySelector('main')?.prepend(node('p',t('Keyword review index unavailable; original records remain visible.'),'portal-notice'));}")
      ]
    }
    for relative,pairs in patches.items():
        file=OUT/relative;content=file.read_text(encoding='utf-8');marker='// SCRO_RELEVANCE_ADAPTER_V1'
        if marker in content:continue
        for old,new in pairs:
            if content.count(old)!=1:raise ValueError('Runtime anchor changed: '+relative)
            content=content.replace(old,new,1)
        file.write_text(marker+'\n'+content,encoding='utf-8')
    file=OUT/'portal-translations.json';translations=json.loads(file.read_text())
    translations.update({
      'Excluded by editorial review. The original observation is retained.':{'zh':'已由人工審核排除，原始觀測紀錄仍保留。','de':'Redaktionell ausgeschlossen. Die ursprüngliche Beobachtung bleibt erhalten.','es':'Excluido en la revisión editorial. Se conserva el registro original.'},
      'Keyword review index unavailable; original records remain visible.':{'zh':'關鍵字審核索引無法載入，原始紀錄仍可瀏覽。','de':'Prüfindex nicht verfügbar; Originaldatensätze bleiben sichtbar.','es':'Índice de revisión no disponible. Puede seguir consultando los registros originales.'},
      'Publisher confirmed':{'zh':'出版歸屬已確認','de':'Herausgeber bestätigt','es':'Entidad editora confirmada'}
    })
    write(file,translations)

def build():
    if not (OUT/'index.html').exists():raise ValueError('Run build_portal.py first')
    integrate_runtime()
    records=load_records()
    decisions=validate_overlay(json.loads((ROOT/'data/reviews/decisions.json').read_text()))['records']
    unknown=set(decisions)-set(records)
    if unknown:raise ValueError('Reviewed record absent from archive: '+','.join(sorted(unknown)))
    selected=sorted(records,key=lambda k:(records[k].get('published_at',''),k),reverse=True)[:10000]
    index={rid:decorate(records[rid],decisions) for rid in selected}
    similarities(index)
    counts={level:sum(row['analysis']['level']==level for row in index.values()) for level in ['high','review','low']}
    data={'schema_version':1,'rule_version':rules()['version'],'rule_digest':digest(rules()),'topics':rules()['topics'],
          'coverage':'complete' if len(selected)==len(records) else 'partial','indexed_records':len(index),
          'total_records':len(records),'counts':counts,'records':index}
    write(OUT/'data/relevance-index.json',data)
    # Stratified, deterministic pool. Labels remain null until the research team reviews them.
    pool={('record:'+rid):{'sample_id':'record:'+rid,'title':row['title'],'url':row['url'],
                         'kind':row['kind'],'published_at':row.get('published_at'),'human_label':None}
          for rid,row in records.items()}
    seen_publications={(row['url'],row['title']) for row in pool.values()}
    for file in sorted((ROOT/'data/candidates').glob('????-??.jsonl')):
        for line in file.read_text().splitlines():
            if not line.strip():continue
            row=json.loads(line);key='candidate:'+row['candidate_id']
            identity=(row['url'],row['title'])
            if identity in seen_publications:continue
            seen_publications.add(identity)
            pool[key]={'sample_id':key,'title':row['title'],'url':row['url'],'kind':row['kind'],
                       'published_at':row.get('published_at'),'human_label':None}
    buckets={level:[] for level in ['high','review','low']}
    for key in sorted(pool,key=lambda x:hashlib.sha256(x.encode()).hexdigest())[:5000]:
        row=pool[key];level=analyze(row)['level'];buckets[level].append(row)
    sample=[]
    while len(sample)<200 and any(buckets.values()):
        for level in buckets:
            if buckets[level] and len(sample)<200:sample.append(buckets[level].pop())
    write(OUT/'data/relevance-validation-sample.json',{'schema_version':1,'label_status':'awaiting_human_labels',
          'rule_version':rules()['version'],'available_pool':len(pool),'sample_count':len(sample),
          'target_range':[150,200],'sampling_pool_limit':5000,'metrics':None,'notes':'Keyword-derived strata for evaluation after independent annotation.','cases':sample})
    for path in OUT.rglob('*.html'):
        source=path.read_text(encoding='utf-8')
        # Root page, one-level section and nested editor all share one data index.
        depth=len(path.parent.relative_to(OUT).parts)
        prefix='./' if depth==0 else '../'*depth
        anchor=f'<script defer src="{prefix}query.js"></script>'
        if anchor not in source:continue
        addition=f'<script defer src="{prefix}relevance-client.js"></script>'
        if addition not in source:source=source.replace(anchor,anchor+addition)
        editor=path==OUT/'workbench/edit/index.html'
        if editor:
            target='<script defer src="../workbench.js"></script>'
            if source.count(target)!=1:raise ValueError('Editor workbench script anchor changed')
            additions=(
                '<script defer src="../review-store.js"></script>'
                '<script defer src="../review-panel.js"></script>'
            )
            source=source.replace(target,additions+target)
            source=source.replace('</head>','<link rel="stylesheet" href="../review-panel.css"></head>')
        elif path==OUT/'workbench/index.html':
            if '<script defer src="./review-panel.js"></script>' in source:
                raise ValueError('Read-only Workbench unexpectedly includes editing tools')
        path.write_text(source,encoding='utf-8')
    print('Relevance sidecar:',counts,'; indexed',len(index),'; human validation sample',len(sample),'of',len(pool),'; independently labelled 0')
if __name__=='__main__':build()
