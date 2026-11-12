/* The compact publication index controls visibility independently of relevance details. */
(() => {
'use strict';
const root = new URL('./', document.currentScript.src);
let data = null;
let visibility = null;
let failed = false;

async function readIndex(path, maximum) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 12000);
  try {
    const response = await fetch(new URL(path, root), {
      credentials: 'omit', cache: 'no-store', signal: controller.signal
    });
    if (!response.ok) throw new Error('Index unavailable');
    const source = await response.text();
    if (source.length > maximum) throw new Error('Index exceeds size limit');
    return JSON.parse(source);
  } finally {
    clearTimeout(timer);
  }
}

async function refresh() {
  const [detail, publication] = await Promise.allSettled([
    readIndex('data/relevance-index.json', 20000000),
    readIndex('data/publication-index.json', 2000000)
  ]);
  const rich = detail.status === 'fulfilled' ? detail.value : null;
  data = rich?.schema_version === 1 && rich.records && rich.topics ? rich : null;
  const value = publication.status === 'fulfilled' ? publication.value : null;
  const recordId = /^[a-f0-9]{18}$/;
  const valid = value?.schema_version === 1 && Array.isArray(value.excluded) &&
    value.excluded.every(id => recordId.test(id)) && value.aliases &&
    Object.entries(value.aliases).every(([from,to]) => recordId.test(from) && recordId.test(to) && from !== to);
  visibility = valid ? {excluded: new Set(value.excluded), aliases: value.aliases} : null;
  failed = !data || !visibility;
  if (failed) throw new Error('Publication or relevance index unavailable');
  return data;
}

const ready = refresh().catch(() => {});
const id = record => typeof record === 'string' ? record : record.record_id || record.id;
const get = record => data?.records[id(record)] || null;
const tags = record => data?.record_tags?.[id(record)]?.tags || [];
const excluded = record => visibility?.excluded.has(id(record)) || get(record)?.included === false;

function distinct(rows) {
  const unique = new Map();
  for (const row of rows) {
    const recordId = id(row);
    const primary = visibility?.aliases[recordId] ?? recordId;
    if (!unique.has(primary) || recordId === primary) unique.set(primary, row);
  }
  return [...unique.values()];
}

function duplicateCount() {
  return Object.entries(visibility?.aliases ?? {}).filter(([from,to]) =>
    get(from) && get(to) && !excluded(from) && !excluded(to)
  ).length;
}

function apply(record) {
  const detail = get(record);
  if (!detail) return record;
  const current = detail.review_state === 'current';
  return {
    ...record,
    original_topics: record.original_topics || record.topics,
    topics: detail.effective_topics,
    relevance_level: detail.analysis.level,
    rule_version: detail.analysis.rule_version,
    review_state: detail.review_state,
    manual_relevance: current ? detail.review.relevance : '',
    publisher_confirmed: current && detail.review.publisher_confirmed,
    reviewed_canonical_url: current ? detail.review.canonical_url : null
  };
}

window.SCRO_RELEVANCE = Object.freeze({
  ready, get, apply, tags, refresh, distinct, duplicateCount, excluded,
  included: record => Boolean(visibility && !excluded(record)),
  get data() { return data; },
  get failed() { return failed; }
});
})();
