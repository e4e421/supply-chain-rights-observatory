"""Regression for the blank area below paged results at different zoom/layout sizes.

Tests the actual static HTTP/CSP pages in Chrome when available. The probe is added
only to a temporary copy, never published, and uses no external services.
"""
from __future__ import annotations
import html
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

ROOT = Path(__file__).resolve().parents[1]
CHROME = next((shutil.which(n) for n in (
    'google-chrome', 'chromium', 'chromium-browser', 'google-chrome-stable'
) if shutil.which(n)), None)
PROBE = r'''
(async () => {
 const errors=[];
 window.addEventListener('error',e=>errors.push(e.message));
 const wait=ms=>new Promise(resolve=>setTimeout(resolve,ms));
 for(let i=0;i<80&&!document.querySelector('#wb-tbody [data-record-id]');i++)await wait(75);
 if(document.fonts?.ready)await document.fonts.ready;
 await wait(150);
 const check=(value,message)=>{if(!value)errors.push(message);};
 const snapshots=[];
 function measure(stage){
  const panel=document.getElementById('wb-results').getBoundingClientRect();
  const wrap=document.querySelector('.wb-table-wrap'),box=wrap.getBoundingClientRect();
  const rows=[...document.querySelectorAll('#wb-tbody [data-record-id]')];
  const peers=[...document.querySelectorAll('.wb-filters,.wb-inspector')]
   .map(e=>e.getBoundingClientRect()).filter(r=>Math.abs(r.top-panel.top)<=2&&r.width>0);
  const peerBottom=peers.length?Math.max(...peers.map(r=>r.bottom)):null;
  if(peerBottom!==null)check(panel.bottom>=peerBottom-3,stage+': unused area below results');
  check(wrap.scrollHeight<=wrap.clientHeight+2,stage+': inner vertical overflow');
  check(rows.length>0&&rows.length<=40,stage+': unbounded or absent rows');
  if(rows.length)check(rows.at(-1).getBoundingClientRect().bottom<=box.bottom+2,stage+': clipped row');
  check(document.documentElement.scrollWidth<=innerWidth+3,stage+': page horizontal overflow');
  snapshots.push({stage,rows:rows.length,gap:peerBottom===null?null:peerBottom-panel.bottom,height:panel.height});
 }
 measure('initial');
 const columns=document.querySelector('.wb-columns');
 columns.open=true;await wait(150);measure('expanded sidebar');
 columns.open=false;await wait(150);
 const density=document.getElementById('wb-density');
 density.value='comfortable';density.dispatchEvent(new Event('change',{bubbles:true}));
 await wait(150);measure('comfortable');
 density.value='compact';density.dispatchEvent(new Event('change',{bubbles:true}));
 await wait(150);
 // CSS zoom is an additional layout-unit regression, not a claim of native zoom testing.
 for(const zoom of [.8,1.25,1]){
  document.body.style.zoom=zoom;window.dispatchEvent(new Event('resize'));
  await wait(150);measure('css-zoom-'+zoom);
 }
 const before=document.querySelector('.wb-results').getBoundingClientRect().height;
 await wait(250);
 check(Math.abs(before-document.querySelector('.wb-results').getBoundingClientRect().height)<=1,'height oscillation');
 const report=document.createElement('pre');report.id='shared-row-test-report';
 report.textContent=JSON.stringify({width:innerWidth,height:innerHeight,errors,snapshots});
 document.body.append(report);
})();
'''

class WorkbenchRowHeightTests(unittest.TestCase):
    def test_only_same_row_sidebars_influence_page_height(self):
        source=(ROOT/'docs/workbench/workbench.js').read_text(encoding='utf-8')
        self.assertIn('Math.abs(box.top-panelBox.top)<=2',source)
        self.assertIn('peerHeight-chrome',source)
        self.assertIn('wrap.style.height=budget',source)
        self.assertIn('MAX_PAGE_SIZE',source)

    def test_observer_avoids_self_height_feedback(self):
        source=(ROOT/'docs/workbench/workbench.js').read_text(encoding='utf-8')
        self.assertIn('entry.target===results?0:',source)
        self.assertIn('dimensions.get(entry.target)!==signature',source)
        self.assertIn("'.wb-filters','.wb-inspector'",source)
        self.assertIn('requestAnimationFrame',source)

    @unittest.skipUnless(CHROME, 'Chrome not installed: real-browser row-height audit skipped')
    def test_browser_shared_row_geometry(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            site=root/'site'
            shutil.copytree(ROOT/'docs',site)
            (site/'row-height-probe.js').write_text(PROBE,encoding='utf-8')
            page=site/'workbench/index.html'
            page.write_text(page.read_text(encoding='utf-8').replace(
                '</body>','<script defer src="../row-height-probe.js"></script></body>'
            ),encoding='utf-8')
            class Handler(SimpleHTTPRequestHandler):
                def log_message(self,*args):
                    pass
            server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(site)))
            thread=Thread(target=server.serve_forever,daemon=True)
            thread.start()
            try:
                for language in ('en','zh','de'):
                    for width,height in ((1920,900),(1600,700),(1280,720),(1000,900),(820,900),(500,844)):
                        with self.subTest(language=language,width=width,height=height):
                            profile=root/f'browser-{language}-{width}'
                            url=f'http://127.0.0.1:{server.server_port}/workbench/?lang={language}'
                            result=subprocess.run([
                                CHROME,'--headless=new','--no-sandbox','--disable-gpu',
                                '--disable-dev-shm-usage','--force-device-scale-factor=1',
                                f'--window-size={width},{height}','--virtual-time-budget=10000',
                                '--user-data-dir='+str(profile),'--dump-dom',url
                            ],capture_output=True,text=True,check=True,timeout=45)
                            match=re.search(r'<pre id="shared-row-test-report">([^<]+)</pre>',result.stdout)
                            self.assertIsNotNone(match,'Browser layout probe did not run')
                            report=json.loads(html.unescape(match.group(1)))
                            self.assertEqual(report['errors'],[],report)
                            print('PASS shared row layout',language,width,height,flush=True)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)

if __name__=='__main__':
    unittest.main()
