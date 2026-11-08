/* Read-only, privacy-preserving public research viewer. English is the canonical data language. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const i18n = window.SCRO_I18N || { t: x => String(x || ''), english: x => String(x || ''), language: 'en', onChange: () => {} };
  const t = key => i18n.t(key);
  const english = key => i18n.english(key);
  const topics = {
    'policy':'Policy & governance',
    'forced-labour':'Forced labour',
    'working-conditions':'Working conditions',
    'worker-voice':'Worker voice & remedy',
    'network':'Supply networks',
    'research':'Academic research',
    'other':'Other information'
  };
  let items = [], references = [], data = null, archiveInfo = null, sourceHealth = null, loadError = false, visibleCount = 15;
  function safeURL(value) {
    try {
      const url = new URL(value);
      return url.protocol === 'https:' && !url.username && !url.password ? url.href : null;
    } catch (_) { return null; }
  }
  function dateAgeDays(iso) {
    const timestamp = Date.parse(iso || '');
    return Number.isFinite(timestamp) ? (Date.now() - timestamp)/86400000 : Infinity;
  }
  function localDate(iso, withTime) {
    if (!iso) return t(withTime ? 'No successful update yet' : 'Date unavailable');
    const date = new Date(iso);
    if (Number.isNaN(date.getTime())) return t(withTime ? 'No successful update yet' : 'Date unavailable');
    const locale = {zh:'zh-TW',en:'en-GB',de:'de-DE'}[i18n.language] || 'en-GB';
    const opts = { timeZone:'Asia/Taipei', year:'numeric', month:'2-digit', day:'2-digit' };
    if (withTime) {opts.hour='2-digit';opts.minute='2-digit';opts.hour12=false;}
    return new Intl.DateTimeFormat(locale,opts).format(date);
  }
  function el(tag, value, className) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    node.textContent = value == null ? '' : String(value);
    return node;
  }
  function sourceLabel(value) { return t(value || 'Unknown'); }
  function renderMetrics() {
    if (!data) return;
    $('metric-total').textContent = String(items.length);
    $('metric-recent').textContent = String(items.filter(x => dateAgeDays(x.published_at) >= 0 && dateAgeDays(x.published_at) <= 30).length);
    $('metric-updated').textContent = localDate(data.last_successful_collection,true);
    $('metric-updated').classList.add('compact');
    const good = (data.sources || []).filter(x => x.status === 'ok').length;
    const total = (data.sources || []).length;
    const stale = dateAgeDays(data.last_successful_collection) > 2;
    const failed = data.status === 'failed' || data.status === 'not_started';
    const status = $('metric-status');
    status.classList.toggle('is-good',!stale && !failed && data.status === 'ok');
    status.classList.toggle('is-bad',stale || failed);
    status.textContent = failed ? t('Collection incomplete') : stale ? t('Data stale') :
      data.status === 'partial' ? t('Partial source failures') : t('Operational');
    $('metric-coverage').textContent = good + ' / ' + total + ' ' + t('automated sources successful');
    const alert = $('data-alert');
    if (failed || stale || data.status === 'partial') {
      alert.classList.add('visible');
      alert.classList.toggle('error',failed || stale);
      alert.textContent = failed ? t('No verified successful collection yet. Check GitHub Actions.') :
        stale ? t('No successful update for over 48 hours. Information may be stale; check sources and GitHub Actions.') :
        t('Some sources failed during this update. Earlier leads were kept; coverage is incomplete.');
    } else {
      alert.classList.remove('visible','error');
      alert.textContent = '';
    }
  }
  function signalCard(item) {
    const card = el('article','','signal-item');
    const metadata = el('div','','signal-meta');
    const group = (item.topics || []).find(code => Object.prototype.hasOwnProperty.call(topics,code)) || 'other';
    metadata.append(
      el('span',t(topics[group]),'topic-tag'),
      el('span',t(item.evidence_status || 'Unconfirmed'),'type-tag'),
      (() => { const time=el('time',localDate(item.published_at,false)); if (item.published_at) time.dateTime=item.published_at; return time; })()
    );
    card.append(metadata);
    const href = safeURL(item.url);
    const title = el(href ? 'a' : 'strong',item.title || 'Untitled signal','signal-title');
    if (href) {title.href=href;title.target='_blank';title.rel='noopener noreferrer';}
    title.setAttribute('lang', /^(en|de|zh-Hant|fr|es|it|nl|sv|pl|pt)$/.test(item.original_language || '') ? item.original_language : 'und');
    card.append(title);
    const desc = item.description || 'Follow the original link to verify context, evidence and applicability.';
    card.append(el('p',t(desc),'signal-desc'));
    const footer = el('div','','signal-foot');
    footer.append(
      el('span',t('Source') + ': ' + sourceLabel(item.source)),
      el('span',t('Type') + ': ' + t(item.kind === 'academic' ? 'Scholarly metadata' : 'Discovery lead'))
    );
    if(item.doi) footer.append(el('span','DOI: ' + item.doi));
    card.append(footer);
    return card;
  }
  function filteredItems() {
    const query = $('search').value.trim().toLocaleLowerCase();
    const topic = $('topic').value;
    const days = $('period').value === 'all' ? Infinity : Number($('period').value);
    return items.filter(item => {
      if (topic !== 'all' && !(item.topics || []).includes(topic)) return false;
      if (dateAgeDays(item.published_at) > days) return false;
      if (query) {
        const labels = (item.topics || []).map(code => topics[code] || 'Other information');
        const searchable = [
          item.title,english(item.source),sourceLabel(item.source),
          english(item.description),t(item.description || ''),
          ...labels,...labels.map(t), ...(item.topics || [])
        ].join(' ').toLocaleLowerCase();
        if (!searchable.includes(query)) return false;
      }
      return true;
    });
  }
  function renderSignals() {
    const list = $('signal-list');
    list.replaceChildren();
    if(loadError) {
      $('results-count').textContent = t('No data available');
      list.append(el('div',t('Could not load signals. Please refresh later.'),'empty-state'));
      return;
    }
    if (!data) {
      $('results-count').textContent=t('Loading public data…');
      list.append(el('div',t('Research data is currently loading.'),'empty-state'));
      return;
    }
    const found = filteredItems();
    $('results-count').textContent=String(found.length) + ' ' + t('records · sorted by publication date');
    if (!found.length) {
      const empty=el('div','','empty-state');
      empty.append(
        el('strong',t(items.length ? 'No matching signals' : 'No collected signals yet')),
        el('p',t(items.length ? 'Adjust your search, date range or research theme.' : 'Public records appear after the first successful GitHub Actions collection.'))
      );
      list.append(empty);
    } else {
      found.slice(0,visibleCount).forEach(item=>list.append(signalCard(item)));
    }
    $('show-more').hidden=visibleCount>=found.length;
  }
  function renderSources() {
    const list=$('source-list');list.replaceChildren();
    for (const ref of references) {
      const url=safeURL(ref.url);
      if(!url) continue;
      const card=el('article','','source-card');
      const head=el('div','','source-card-header');
      head.append(el('span',t(ref.category || 'REFERENCE')),el('small',t(ref.mode || 'Curated reference')));
      card.append(head,el('h3',ref.name || ''),el('p',t(ref.use || '')));
      const link=el('a',t('Visit original source ↗'));
      link.href=url;link.target='_blank';link.rel='noopener noreferrer';
      card.append(link);list.append(card);
    }
  }

  function renderGovernance() {
    $('archive-total').textContent = archiveInfo && Number.isInteger(archiveInfo.total_records)
      ? String(archiveInfo.total_records) : t('Pending first archive');
    $('source-approved').textContent = sourceHealth && Number.isInteger(sourceHealth.approved_reference_count)
      ? String(sourceHealth.approved_reference_count) : String(references.length || 0);
    $('source-overdue').textContent = sourceHealth && Number.isInteger(sourceHealth.review_needed_count ?? sourceHealth.review_overdue)
      ? String(sourceHealth.review_needed_count ?? sourceHealth.review_overdue) : t('Not yet reviewed');
  }
  function csvCell(value) {
    let valueString=String(value == null ? '' : value).replace(/[\u0000-\u001f\u007f]/g,' ');
    if (/^\s*[=+@\-\t\r]/.test(valueString)) valueString="'"+valueString;
    return '"' + valueString.replace(/"/g,'""') + '"';
  }
  function exportCSV() {
    // Stable English schema and original article titles across all languages.
    const columns=['title','published_at','source','source_id','kind','evidence_status','topics','url','doi'];
    const output=[columns,...filteredItems().map(item=>columns.map(key=>
      key === 'topics' ? (item.topics || []).join('; ') :
      key === 'source' ? english(item.source) :
      key === 'evidence_status' ? english(item.evidence_status) : item[key] ?? ''
    ))].map(row=>row.map(csvCell).join(',')).join('\r\n');
    const blob=new Blob(['\ufeff'+output],{type:'text/csv;charset=utf-8'});
    const url=URL.createObjectURL(blob);
    const link=document.createElement('a');
    link.href=url;link.download='supply-chain-rights-signals.csv';
    document.body.append(link);link.click();link.remove();
    setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  async function loadJSON(path) {
    const response=await fetch(path,{cache:'no-store',credentials:'omit'});
    if(!response.ok) throw new Error('HTTP '+response.status);
    return response.json();
  }
  function render() {
    if(loadError) {
      $('metric-status').textContent=t('Load failed');
      $('metric-status').classList.add('is-bad');
      $('data-alert').className='data-alert visible error';
      $('data-alert').textContent=t('Public data could not be loaded. Check the GitHub Pages deployment and JSON files.');
    } else if(data) renderMetrics();
    renderSignals();
    renderSources();
    renderGovernance();
  }
  async function load() {
    try {
      const result=await Promise.all([loadJSON('./data/latest.json'),loadJSON('./data/references.json')]);
      const current=result[0], refs=result[1];
      if (current.schema_version!==1 || !Array.isArray(current.items) || !Array.isArray(current.sources) || !Array.isArray(refs)) throw new Error('Invalid public data schema');
      data=current;references=refs;
      items=current.items.filter(item=>item && typeof item.title==='string' && typeof item.url==='string').slice(0,1000);
      items.sort((a,b)=>Date.parse(b.published_at || '')-Date.parse(a.published_at || ''));
      // Optional public governance data does not prevent the main news feed from loading.
      const extras = await Promise.allSettled([
        loadJSON('./data/archive-summary.json'),loadJSON('./data/source-health.json')
      ]);
      archiveInfo = extras[0].status === 'fulfilled' ? extras[0].value : null;
      sourceHealth = extras[1].status === 'fulfilled' ? extras[1].value : null;
    } catch (_) {loadError=true;}
    render();
  }
  for(const id of ['search','topic','period']) {
    $(id).addEventListener(id==='search' ? 'input' : 'change',()=>{visibleCount=15;renderSignals();});
  }
  $('show-more').addEventListener('click',()=>{visibleCount+=15;renderSignals();});
  $('download-csv').addEventListener('click',exportCSV);
  i18n.onChange(()=>render());
  load();
})();
