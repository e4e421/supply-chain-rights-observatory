'use strict';
const choice = document.querySelector('#lang');
const current = new URL(location.href);
const language = current.searchParams.get('lang') || localStorage.getItem('scro.language') || localStorage.getItem('scro.case.lang') || (navigator.language.startsWith('zh') ? 'zh' : 'en');
function translate(lang) {
  document.documentElement.lang = lang === 'zh' ? 'zh-Hant' : 'en';
  choice.value = lang === 'zh' ? 'zh' : 'en';
  choice.setAttribute('aria-label', choice.value === 'en' ? 'Language' : '語言');
  for (const option of document.querySelectorAll('option[data-en]')) {
    option.textContent = option.dataset[choice.value];
  }
  document.dispatchEvent(new Event('case-language'));
  document.querySelectorAll('a[data-local]').forEach(a => {
    const target = new URL(a.href);
    target.searchParams.set('lang', choice.value);
    a.href = target;
  });
}
translate(language);
choice.addEventListener('change', () => {
  translate(choice.value);
  localStorage.setItem('scro.language',choice.value);
  current.searchParams.set('lang',choice.value);
  history.replaceState(null,'',current);
});
const search = document.querySelector('#case-search'), queue = document.querySelector('#case-filter');
function filterCases() {
  const query = search.value.trim().toLocaleLowerCase();
  const now = new Date(), today = now.toISOString().slice(0,10);
  const horizon = new Date(now.getTime()+7*86400000).toISOString().slice(0,10);
  const weekAgo = new Date(now.getTime()-7*86400000).toISOString().slice(0,10);
  let count = 0;
  for (const card of document.querySelectorAll('[data-gap]')) {
    const type = queue.value;
    const match = type === 'all' || type === card.dataset.gap ||
      (type === 'due' && card.dataset.due && card.dataset.due <= horizon) ||
      (type === 'recent' && card.dataset.latest >= weekAgo && card.dataset.latest <= today);
    card.hidden = !match || !(card.textContent+' '+card.dataset.search).toLocaleLowerCase().includes(query);
    if (!card.hidden) count++;
  }
  document.querySelector('#count').textContent=String(count);
}
if (search) {
  search.addEventListener('input',filterCases);
  queue.addEventListener('change',filterCases);
  filterCases();
}

const published = document.querySelector('#release-time');
if (published && /^[0-9]+$/.test(published.dataset.run)) {
  const run=published.dataset.run;
  const link=document.createElement('a');
  link.href='https://github.com/e4e421/supply-chain-rights-observatory/actions/runs/'+run;
  link.textContent='GitHub Actions';published.replaceChildren(link);
  fetch('https://api.github.com/repos/e4e421/supply-chain-rights-observatory/actions/runs/'+run+'/jobs?per_page=100',{credentials:'omit'})
    .then(response=>{if(!response.ok)throw Error();return response.json();})
    .then(result=>{
      const verified=(result.jobs||[]).flatMap(j=>j.steps||[]).find(s=>['Confirm public case release','Confirm the public release and indexes'].includes(s.name)&&s.conclusion==='success');
      if(verified?.completed_at)link.textContent=verified.completed_at;
    }).catch(()=>{ /* The run link remains available when the API is rate-limited. */ });
}

