import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const context={window:{}};
vm.runInNewContext(fs.readFileSync('docs/query.js','utf8'),context);
const match=context.window.SCRO_QUERY.matches;
test('Search words default to AND',()=>{
 assert.equal(match('Worker rights in supplier networks','worker supplier'),true);
 assert.equal(match('Worker rights in supplier networks','worker automobile'),false);
});
test('OR alternative phrases are safe',()=>{
 assert.equal(match('EU forced labour regulation','"forced labour" OR "trade union"'),true);
 assert.equal(match('Collective bargaining for workers','"forced labour" OR "collective bargaining"'),true);
 assert.equal(match('Unrelated energy article','"forced labour" OR "trade union"'),false);
});
test('User input is text, not executable code',()=>{
 assert.equal(match('supply chain','supply.*chain'),false);
 assert.equal(match('supply chain','=alert(1)'),false);
});
