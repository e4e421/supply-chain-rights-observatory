import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';

const source = readFileSync(new URL('../docs/relevance-client.js', import.meta.url), 'utf8');
const first = {record_id: 'a'.repeat(18)};
const second = {record_id: 'b'.repeat(18)};
const excluded = {record_id: 'c'.repeat(18)};

async function client(publication, detail) {
  const window = {};
  runInNewContext(source, {
    window, URL, AbortController, setTimeout, clearTimeout,
    document: {currentScript: {src: 'https://example.org/relevance-client.js'}},
    fetch: async url => {
      const value = url.pathname.endsWith('/publication-index.json') ? publication : detail;
      return {ok: Boolean(value), text: async () => JSON.stringify(value)};
    }
  });
  await window.SCRO_RELEVANCE.ready;
  return window.SCRO_RELEVANCE;
}

test('publication exclusions and aliases work when relevance details fail', async () => {
  const model = await client({schema_version: 1, excluded: [excluded.record_id], aliases: {[second.record_id]: first.record_id}}, null);
  assert.equal(model.included(first), true);
  assert.equal(model.included(excluded), false);
  assert.equal(model.distinct([second, first])[0], first);
  assert.equal(model.distinct([second])[0], second);
});

test('missing publication rules pause public results while archived details remain available', async () => {
  const model = await client(null, {schema_version: 1, topics: {}, records: {}});
  assert.equal(model.failed, true);
  assert.equal(model.included(first), false);
  assert.equal(model.apply(first), first);
});
