#!/usr/bin/env python3
"""Browser layout containment regression. No external website access.

Uses temporary copies of static Pages files, with a same-origin instrumentation
script injected into those copies only. Tests responsive widths and every locale.
No changes are published to docs/ and no tracking/browser service is required.
"""
import html
import json
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

ROOT = Path(__file__).resolve().parents[1]
CHROME = next((shutil.which(x) for x in
    ("google-chrome", "chromium", "chromium-browser", "google-chrome-stable") if shutil.which(x)), None)
PROBE = r"""
window.addEventListener('load', function () {
 setTimeout(function () {
  const isWorkbench = !!document.querySelector('.wb-filters');
  const isHome = !!document.querySelector('.hero');
  const width = document.documentElement.clientWidth;
  const rect = el => el.getBoundingClientRect();
  const errors = [];
  // A vertical browser scrollbar consumes clientWidth but is not horizontal overflow.
  const actualOverflow = document.documentElement.scrollWidth - window.innerWidth;
  if (actualOverflow > 4) errors.push('document horizontal overflow: ' + actualOverflow + 'px');
  if (isWorkbench) {
    const rail = document.querySelector('.wb-filters');
    const inside = rect(rail);
    for (const el of rail.querySelectorAll('input:not([type="checkbox"]), select, button')) {
      if (el.offsetParent === null) continue;
      const r=rect(el);
      if (r.right > inside.right + 2 || r.left < inside.left - 2) {
        errors.push('filter control outside rail: '+(el.id||el.tagName)+' ['+r.left+','+r.right+'] vs '+inside.right);
      }
    }
    for (const id of ['wb-from','wb-to']) {
      const el=document.getElementById(id),parent=el.closest('.wb-field');
      const a=rect(el),b=rect(parent);
      if (a.left < b.left-2 || a.right > b.right+2) errors.push('date field overflow: '+id);
    }
    const table=document.querySelector('.wb-table-wrap');
    if(rect(table).right>width+2) errors.push('table scroller extends beyond viewport');
    const resultPanel=document.querySelector('.wb-results');
    if(rect(resultPanel).right>width+2)errors.push('result panel outside viewport');
  }
  if(isHome) {
    for(const el of document.querySelectorAll('.container,.filters,.archive-controls,.content-layout')) {
      if(el.offsetParent===null)continue;
      const r=rect(el);
      if(r.right > width + 4)errors.push('homepage container overflow: '+el.className);
    }
  }
  const report={width,innerWidth:window.innerWidth,scrollWidth:document.documentElement.scrollWidth,
    page:isWorkbench?'workbench':isHome?'home':'record',errors};
  const out=document.createElement('pre');out.id='layout-probe';
  out.textContent=JSON.stringify(report);
  document.body.append(out);
 }, 700);
});
"""
def run():
    if not CHROME:
        print("SKIPPED responsive layout test: Chrome missing")
        return
    with tempfile.TemporaryDirectory() as temp:
        target=Path(temp)/"site"
        shutil.copytree(ROOT/"docs",target)
        (target/"layout-probe.js").write_text(PROBE,encoding="utf-8")
        pages=["index.html","record.html","workbench/index.html"]
        for page in pages:
            p=target/page
            text=p.read_text(encoding="utf-8")
            assert "</body>" in text
            # Absolute path is confined to the localhost test root and allowed by the existing CSP.
            text=text.replace("</body>",'<script defer src="/layout-probe.js"></script></body>')
            p.write_text(text,encoding="utf-8")
        class Handler(SimpleHTTPRequestHandler):
            def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(target),**kwargs)
            def log_message(self,*args):pass
        server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
        worker=Thread(target=server.serve_forever,daemon=True)
        worker.start()
        try:
            port=server.server_port
            cases=[("workbench/index.html",500),("workbench/index.html",600),
                   ("workbench/index.html",820),("workbench/index.html",1000),
                   ("workbench/index.html",1250),("workbench/index.html",1450),
                   ("workbench/index.html",1600),("index.html",500),
                   ("index.html",820),("index.html",1280),
                   ("record.html",500),("record.html",820)]
            with tempfile.TemporaryDirectory() as profiles:
                for i,(page,width) in enumerate(cases):
                    uri=f"http://127.0.0.1:{port}/{page}?lang={'de' if i%3==0 else 'zh' if i%3==1 else 'en'}"
                    args=[CHROME,"--headless=new","--disable-gpu","--no-sandbox",
                          "--disable-dev-shm-usage","--disable-extensions",
                          "--window-size="+str(width)+",900","--force-device-scale-factor=1",
                          "--virtual-time-budget=6000",
                          "--user-data-dir="+profiles+"/p"+str(i),"--dump-dom",uri]
                    dom=subprocess.run(args,capture_output=True,text=True,timeout=65,check=True).stdout
                    match=re.search(r'<pre id="layout-probe">([^<]+)</pre>',dom)
                    if not match:
                        raise AssertionError("Layout probe did not run: "+page+" "+str(width))
                    report=json.loads(html.unescape(match.group(1)))
                    if report['errors']:
                        raise AssertionError(f"Layout errors {page} at requested {width}: {report}")
                    print(f"PASS layout: {page} requested={width}px actual={report['width']}px")
        finally:
            server.shutdown()
            worker.join(timeout=3)
if __name__=="__main__":run()
