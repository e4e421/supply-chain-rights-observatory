"""Regression for unused space below paged results after resizing.

Real Chrome HTTP/CSP pages are tested through its local debugging pipe with the
Python standard library. Actual paint frames are awaited: --virtual-time-budget
can advance timers without delivering ResizeObserver/animation-frame callbacks.
No browser dependencies, production probes or external services are added.
"""
from __future__ import annotations
import json
import os
import select
import shutil
import subprocess
import tempfile
import time
import unittest
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

ROOT=Path(__file__).resolve().parents[1]
CHROME=next((shutil.which(n) for n in (
    'google-chrome','chromium','chromium-browser','google-chrome-stable'
) if shutil.which(n)),None)
PROBE=r'''
(async()=>{
 const errors=[];
 window.addEventListener('error',e=>errors.push(e.message));
 const wait=ms=>new Promise(resolve=>setTimeout(resolve,ms));
 const settle=async()=>{for(let i=0;i<4;i++)await new Promise(resolve=>requestAnimationFrame(resolve));};
 for(let i=0;i<80&&!document.querySelector('#wb-tbody [data-record-id]');i++)await wait(75);
 if(document.fonts?.ready)await document.fonts.ready;
 await settle();
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
 columns.open=true;await settle();measure('expanded sidebar');
 columns.open=false;await settle();
 const density=document.getElementById('wb-density');
 density.value='comfortable';density.dispatchEvent(new Event('change',{bubbles:true}));
 await settle();measure('comfortable');
 density.value='compact';density.dispatchEvent(new Event('change',{bubbles:true}));
 await settle();
 // CSS zoom tests coordinate conversion; it is not native browser zoom certification.
 for(const zoom of [.8,1.25,1]){
  document.body.style.zoom=zoom;window.dispatchEvent(new Event('resize'));
  await settle();measure('css-zoom-'+zoom);
 }
 const before=document.querySelector('.wb-results').getBoundingClientRect().height;
 await settle();await settle();
 check(Math.abs(before-document.querySelector('.wb-results').getBoundingClientRect().height)<=1,'height oscillation');
 return {width:innerWidth,height:innerHeight,errors,snapshots};
})()
'''

class ChromePipe:
    """Small request/response CDP client over local pipes, without a network port."""
    def __init__(self,chrome,profile):
        self.process=subprocess.Popen([
            'bash','-c','exec 3<&0 4>&1; exec "$@" >/dev/null','--',chrome,
            '--headless=new','--no-sandbox','--disable-gpu','--disable-dev-shm-usage',
            '--no-first-run','--remote-debugging-pipe','--user-data-dir='+str(profile)
        ],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
        self.sequence=0
        self.buffer=b''
        self.session=None
        target=self.call('Target.createTarget',{'url':'about:blank'})['targetId']
        self.session=self.call('Target.attachToTarget',{'targetId':target,'flatten':True})['sessionId']
        self.call('Page.enable')
        self.call('Runtime.enable')

    def call(self,method,params=None,timeout=35):
        self.sequence+=1
        ident=self.sequence
        message={'id':ident,'method':method,'params':params or {}}
        if self.session:
            message['sessionId']=self.session
        self.process.stdin.write(json.dumps(message).encode()+b'\0')
        self.process.stdin.flush()
        end=time.monotonic()+timeout
        while time.monotonic()<end:
            if b'\0' in self.buffer:
                frame,self.buffer=self.buffer.split(b'\0',1)
                if not frame:
                    continue
                response=json.loads(frame)
                if response.get('id')!=ident:
                    continue
                if 'error' in response:
                    raise RuntimeError(response['error'])
                return response.get('result',{})
            remaining=max(0,min(1,end-time.monotonic()))
            if select.select([self.process.stdout],[],[],remaining)[0]:
                chunk=os.read(self.process.stdout.fileno(),65536)
                if not chunk:
                    raise RuntimeError('Chrome debug pipe closed')
                self.buffer+=chunk
        raise TimeoutError(method)

    def evaluate(self,expression):
        result=self.call('Runtime.evaluate',{
            'expression':expression,'awaitPromise':True,'returnByValue':True
        })
        if 'exceptionDetails' in result:
            raise RuntimeError(result['exceptionDetails'])
        return result.get('result',{}).get('value')

    def close(self):
        self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=5)
        self.process.stdin.close()
        self.process.stdout.close()

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

    @unittest.skipUnless(CHROME,'Chrome not installed: real-browser row-height audit skipped')
    def test_browser_shared_row_geometry(self):
        class Handler(SimpleHTTPRequestHandler):
            def log_message(self,*args):
                pass
        server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(ROOT/'docs')))
        thread=Thread(target=server.serve_forever,daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as profile:
                browser=ChromePipe(CHROME,profile)
                try:
                    for language in ('en','zh','de'):
                        for width,height in ((1920,900),(1600,700),(1280,720),(1000,900),(820,900),(390,844)):
                            with self.subTest(language=language,width=width,height=height):
                                browser.call('Emulation.setDeviceMetricsOverride',{
                                    'width':width,'height':height,'deviceScaleFactor':1,'mobile':False
                                })
                                url=f'http://127.0.0.1:{server.server_port}/workbench/?lang={language}&qa_width={width}'
                                browser.call('Page.navigate',{'url':url})
                                ready=False
                                for _ in range(150):
                                    try:
                                        ready=browser.evaluate('document.readyState==="complete" && location.href==='+json.dumps(url))
                                    except RuntimeError:
                                        ready=False
                                    if ready:
                                        break
                                    time.sleep(.02)
                                self.assertTrue(ready,'Workbench HTTP page did not finish loading')
                                report=browser.evaluate(PROBE)
                                self.assertEqual(report['errors'],[],report)
                                print('PASS shared row layout',language,width,height,flush=True)
                finally:
                    browser.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)

if __name__=='__main__':
    unittest.main()
