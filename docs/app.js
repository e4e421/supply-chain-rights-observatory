/* Static, read-only viewer. All third-party strings are inserted using textContent. */
(() => {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const topicNames = { policy:'法規與治理', 'forced-labour':'強迫勞動', 'working-conditions':'勞動條件', 'worker-voice':'勞工發聲與補救', network:'供應網絡', research:'學術研究', other:'其他相關資訊' };
  let items = [];
  let visibleCount = 15;
  const safeURL = (value) => {
    try { const url = new URL(value); return url.protocol === 'https:' && !url.username && !url.password ? url.href : null; }
    catch { return null; }
  };
  const readableDate = (iso) => {
    if (!iso) return '未提供日期';
    const date = new Date(iso);
    return Number.isNaN(date.getTime()) ? '未提供日期' : new Intl.DateTimeFormat('zh-TW', {timeZone:'Asia/Taipei',year:'numeric',month:'2-digit',day:'2-digit'}).format(date);
  };
  const readableTime = (iso) => {
    if (!iso) return '尚未成功更新';
    const date = new Date(iso);
    return Number.isNaN(date.getTime()) ? '尚未成功更新' : new Intl.DateTimeFormat('zh-TW', {timeZone:'Asia/Taipei',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false}).format(date);
  };
  const text = (tag, value, className) => { const el = document.createElement(tag); if(className) el.className = className; el.textContent = value ?? ''; return el; };
  const dateAgeDays = (iso) => { const d = Date.parse(iso || ''); return Number.isFinite(d) ? (Date.now() - d)/86400000 : Infinity; };
  function renderMetrics(data) {
    $('metric-total').textContent = String(items.length);
    $('metric-recent').textContent = String(items.filter(x => dateAgeDays(x.published_at) >= 0 && dateAgeDays(x.published_at) <= 30).length);
    $('metric-updated').textContent = readableTime(data.last_successful_collection);
    $('metric-updated').classList.add('compact');
    const successful = (data.sources || []).filter(x => x.status === 'ok').length;
    const total = (data.sources || []).length;
    const stale = dateAgeDays(data.last_successful_collection) > 2;
    const failed = data.status === 'failed' || data.status === 'not_started';
    const status = $('metric-status');
    status.classList.toggle('is-good', !stale && !failed && data.status === 'ok');
    status.classList.toggle('is-bad', stale || failed);
    status.textContent = failed ? '未完成更新' : stale ? '資料逾時' : data.status === 'partial' ? '部分來源異常' : '正常運作';
    $('metric-coverage').textContent = `${successful} / ${total} 個自動來源成功`; 
    const alert = $('data-alert');
    if (failed || stale || data.status === 'partial') {
      alert.classList.add('visible');
      alert.classList.toggle('error', failed || stale);
      alert.textContent = failed ? '目前尚無已驗證的成功擷取紀錄，請查看 GitHub Actions 執行狀態。' : stale ? '超過 48 小時沒有成功更新。資訊可能過時，請查看來源網站與 GitHub Actions。' : '部分資料來源本次更新失敗，已保留既有線索；請注意資料涵蓋不完整。';
    } else { alert.classList.remove('visible'); }
  }
  function signalCard(item) {
    const article = text('article', '', 'signal-item');
    const metadata = text('div', '', 'signal-meta');
    const group = (item.topics || []).find(x => topicNames[x]) || 'other';
    metadata.append(text('span', topicNames[group], 'topic-tag'), text('span', item.evidence_status || '未確認', 'type-tag'), text('span', readableDate(item.published_at)));
    article.append(metadata);
    const url = safeURL(item.url);
    const title = text(url ? 'a' : 'strong', item.title || '未命名情報', 'signal-title');
    if (url) { title.href = url; title.target = '_blank'; title.rel = 'noopener noreferrer'; }
    article.append(title);
    article.append(text('p', item.description || '請點選原始連結查證背景、證據及適用情境。', 'signal-desc'));
    const foot = text('div', '', 'signal-foot');
    foot.append(text('span', `來源：${item.source || '未知'}`));
    foot.append(text('span', `類型：${item.kind === 'academic' ? '學術書目' : '發現線索'}`));
    if (item.doi) foot.append(text('span', `DOI：${item.doi}`));
    article.append(foot);
    return article;
  }
  function filteredItems() {
    const query = $('search').value.trim().toLocaleLowerCase();
    const topic = $('topic').value;
    const days = $('period').value === 'all' ? Infinity : Number($('period').value);
    return items.filter(item => {
      if (topic !== 'all' && !(item.topics || []).includes(topic)) return false;
      if (dateAgeDays(item.published_at) > days) return false;
      if (query && ![item.title,item.source,item.description,(item.topics || []).map(x=>topicNames[x]).join(' ')].join(' ').toLocaleLowerCase().includes(query)) return false;
      return true;
    });
  }
  function renderSignals() {
    const list = $('signal-list'); list.replaceChildren();
    const found = filteredItems();
    $('results-count').textContent = `符合條件 ${found.length} 筆 · 以發布日期排序`;
    if (!found.length) {
      const empty = text('div', '', 'empty-state');
      empty.append(text('strong', items.length ? '沒有符合條件的情報' : '尚無已擷取的研究情報'), text('p', items.length ? '請調整關鍵字、時間範圍或研究議題。' : '首次執行 GitHub Actions 後，才會顯示經過處理的公開資料。'));
      list.append(empty);
    } else { found.slice(0,visibleCount).forEach(item => list.append(signalCard(item))); }
    $('show-more').hidden = visibleCount >= found.length;
  }
  const safeCSV = (value) => {
    let v = String(value ?? '').replace(/[\u0000-\u001f\u007f]/g, ' ');
    if (/^\s*[=+@\-\t\r]/.test(v)) v = "'" + v;
    return '"' + v.replace(/"/g,'""') + '"';
  };
  function exportCSV() {
    const columns = ['title','published_at','source','kind','evidence_status','topics','url','doi'];
    const rows = [columns, ...filteredItems().map(row => columns.map(key => key === 'topics' ? (row.topics || []).join('; ') : row[key] ?? ''))];
    const output = '\ufeff' + rows.map(row => row.map(safeCSV).join(',')).join('\r\n');
    const blob = new Blob([output], {type:'text/csv;charset=utf-8'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'supply-chain-rights-signals.csv'; document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url),1000);
  }
  async function loadJSON(path) {
    const response = await fetch(path, {cache:'no-store', credentials:'omit'});
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }
  async function load() {
    try {
      const [data, references] = await Promise.all([loadJSON('./data/latest.json'),loadJSON('./data/references.json')]);
      if (data.schema_version !== 1 || !Array.isArray(data.items) || !Array.isArray(data.sources)) throw new Error('資料格式不符合預期');
      items = data.items.filter(item => item && typeof item.title === 'string' && typeof item.url === 'string').slice(0,1000);
      items.sort((a,b)=>Date.parse(b.published_at || '')-Date.parse(a.published_at || ''));
      renderMetrics(data); renderSignals();
      if (Array.isArray(references)) references.forEach(ref => {
        if (!safeURL(ref.url)) return;
        const card = text('article', '', 'source-card');
        const header = text('div','', 'source-card-header');
        header.append(text('span',ref.category || 'REFERENCE'),text('small',ref.mode || '人工參考'));
        card.append(header, text('h3',ref.name || ''),text('p',ref.use || ''));
        const a = text('a','前往原始網站 ↗');a.href=safeURL(ref.url);a.target='_blank';a.rel='noopener noreferrer';card.append(a);
        $('source-list').append(card);
      });
    } catch (err) {
      $('metric-status').textContent='讀取失敗';$('metric-status').classList.add('is-bad');
      $('data-alert').className='data-alert visible error';$('data-alert').textContent = '公開資料讀取失敗。請檢查 GitHub Pages 部署與 JSON 檔案。';
      $('results-count').textContent='尚無可顯示資料';
      $('signal-list').replaceChildren(text('div','無法載入情報資料，請稍後重新整理。','empty-state'));
    }
  }
  ['search','topic','period'].forEach(id => $(id).addEventListener(id==='search'?'input':'change',()=> {visibleCount=15;renderSignals();}));
  $('show-more').addEventListener('click',()=>{ visibleCount += 15;renderSignals(); });
  $('download-csv').addEventListener('click',exportCSV);
  load();
})();
