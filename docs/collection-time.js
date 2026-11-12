/* The homepage and Workbench display the collection timestamp from latest.json. */
(() => {
'use strict';
const age = document.querySelector('[data-collection-age]');
const utcTime = document.querySelector('[data-collection-utc]');
if (!age || !utcTime) return;

const utcFormat = new Intl.DateTimeFormat('en-GB', {
  timeZone: 'UTC', year: 'numeric', month: 'long', day: 'numeric',
  hour: '2-digit', minute: '2-digit', hourCycle: 'h23'
});
const relativeFormats = new Map();
const justNow = {en: 'Just now', 'zh-Hant': '剛剛', de: 'Gerade eben', es: 'Ahora mismo'};
let collectionTime = NaN;

function ageLabel() {
  const elapsed = Date.now() - collectionTime;
  if (!Number.isFinite(elapsed) || elapsed < 0) return '—';
  const minutes = Math.floor(elapsed / 60_000);
  const hours = Math.floor(minutes / 60);
  const language = document.documentElement.lang;
  if (minutes === 0) return justNow[language] ?? justNow.en;
  if (!relativeFormats.has(language)) {
    relativeFormats.set(language, new Intl.RelativeTimeFormat(language, {numeric: 'always', style: 'long'}));
  }
  const formatter = relativeFormats.get(language);
  if (hours >= 48) return formatter.format(-Math.floor(hours / 24), 'day');
  if (hours) return formatter.format(-hours, 'hour');
  return formatter.format(-minutes, 'minute');
}

function renderAge() {
  const label = ageLabel();
  if (age.textContent !== label) age.textContent = label;
}

function set(value) {
  collectionTime = typeof value === 'string' && /(?:Z|[+-]\d{2}:\d{2})$/.test(value) ? Date.parse(value) : NaN;
  if (Number.isFinite(collectionTime)) {
    const parts = utcFormat.formatToParts(collectionTime);
    const {day, month, year, hour, minute} = Object.fromEntries(parts.map(({type, value}) => [type, value]));
    utcTime.dateTime = new Date(collectionTime).toISOString();
    utcTime.textContent = `${day} ${month} ${year}, ${hour}:${minute} UTC`;
    utcTime.hidden = false;
  } else {
    utcTime.hidden = true;
    utcTime.removeAttribute('datetime');
    utcTime.textContent = '';
  }
  renderAge();
}

const updateWhenVisible = () => { if (!document.hidden) renderAge(); };
window.setInterval(updateWhenVisible, 60_000);
document.addEventListener('visibilitychange', updateWhenVisible);
window.SCRO_I18N?.onChange(renderAge);
window.SCRO_COLLECTION_TIME = Object.freeze({set});
})();
