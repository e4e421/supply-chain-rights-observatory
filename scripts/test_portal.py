#!/usr/bin/env python3
"""Validate the deployed output, not just the legacy source pages. Offline and fail-closed."""
import json,re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse,unquote
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'_site'
class Scan(HTMLParser):
 def __init__(self):super().__init__();self.ids=set();self.urls=[];self.headings=[];self.lang=None;self.errors=[];self.keys=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='html':self.lang=a.get('lang')
  if 'id' in a:
   if a['id'] in self.ids:self.errors.append('duplicate ID '+a['id'])
   self.ids.add(a['id'])
  if tag in ('h1','h2','h3'):self.headings.append(tag)
  for k in ('href','src'):
   if k in a:self.urls.append(a[k])
  if tag=='script' and a.get('src','').startswith(('http:','https:','//')):self.errors.append('external runtime script')
  if tag=='a' and a.get('target')=='_blank' and 'noopener' not in a.get('rel',''):self.errors.append('unsafe new window')
  if any(re.fullmatch(r'on(click|load|error|change)',x) for x in a):self.errors.append('inline JS handler')
  if 'data-pk' in a:self.keys.append(a['data-pk'])
def run():
 old=json.loads(re.search(r'const dictionaries = (\{[^\n]+\});',(OUT/'i18n.js').read_text()).group(1))
 new=json.loads((OUT/'portal-translations.json').read_text());keys=set(old)|set(new)
 paths=['index.html','archive/index.html','sources/index.html','policy/index.html','research/index.html','methodology/index.html','record.html','workbench/index.html','workbench/edit/index.html']
 for rel in paths:
  p=OUT/rel;raw=p.read_text(encoding='utf-8');s=Scan();s.feed(raw)
  assert s.lang=='en' and s.headings[0]=='h1',(rel,s.headings)
  assert not s.errors,(rel,s.errors)
  assert 'Content-Security-Policy' in raw and 'language-select' in s.ids,rel
  assert '<option value="es" lang="es">Español</option>' in raw,rel
  assert all(k in keys for k in s.keys),(rel,sorted(set(s.keys)-keys))
  for u in s.urls:
   uri=urlparse(u)
   if uri.scheme or uri.netloc:continue
   target=(p.parent/unquote(uri.path)).resolve() if uri.path else p.resolve()
   assert target.is_relative_to(OUT.resolve()),(rel,u)
   if uri.path.endswith('/'):target=target/'index.html'
   assert target.exists(),(rel,u)
  print('PASS output links, headings, labels and translation keys:',rel)
 for k,v in new.items():
  assert not re.search('[\u3400-\u9fff]',k),k
  assert all(v.get(code) for code in ('zh','de','es')),k
 script=(OUT/'portal.js').read_text()
 assert not any(x in script for x in ['.innerHTML','eval(','new Function(','document.write('])
 index=json.loads((OUT/'data/record-index.json').read_text());cat=json.loads((OUT/'data/archive/catalog.json').read_text())
 assert len(index['records'])==cat['total_records']
 for rid,location in index['records'].items():
  assert re.fullmatch('[a-f0-9]{18}',rid)
  assert re.fullmatch(r'\d{4}-\d{2}-\d{4}\.json',location['file'])
 assert (OUT/'data/latest.json').read_bytes()==(ROOT/'docs/data/latest.json').read_bytes()
 assert (OUT/'data/references.json').read_bytes()==(ROOT/'docs/data/references.json').read_bytes()
 plain=(OUT/'workbench/index.html').read_text()
 editor=(OUT/'workbench/edit/index.html').read_text()
 assert 'src="./review-panel.js"' not in plain and 'src="./review-store.js"' not in plain
 assert 'src="../review-panel.js"' in editor and 'src="../review-store.js"' in editor
 assert 'src="../../relevance-client.js"' in editor
 assert 'href="../workbench.css"' in editor
 assert 'connect-src ' in editor and 'https://api.github.com' in editor
 assert 'https://api.github.com' not in plain
 assert 'data-page="workbench-editor"' in editor
 assert 'data-page="workbench"' in plain
 print('PASS workbench reader and editor separation and safe nested assets')
 print('PASS complete record locator, canonical data unchanged and safe rendering')
if __name__=='__main__':run()
