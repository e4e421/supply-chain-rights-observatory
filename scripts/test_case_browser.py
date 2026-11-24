"""Run a real Chrome smoke against the exact pilot and public-only artifacts."""
import functools
import http.server
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tests"))
from test_workbench_row_height import CHROME,ChromePipe

def main():
    if not CHROME:raise RuntimeError("Chrome is required for the release smoke")
    for script in ("build_portal.py","build_relevance.py","build_case_release.py"):
        subprocess.run([sys.executable,str(ROOT/"scripts"/script)],cwd=ROOT,check=True)
    handler=functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT))
    server=http.server.ThreadingHTTPServer(("127.0.0.1",0),handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with tempfile.TemporaryDirectory() as profile:
            browser=ChromePipe(CHROME,profile)
            def navigate(path,test):
                target="http://127.0.0.1:"+str(server.server_port)+path
                browser.call("Page.navigate",{"url":target})
                for _ in range(80):
                    try:
                        if browser.evaluate("location.pathname==="+json.dumps(path.split("?")[0])+" && document.readyState==='complete' && Boolean("+test+")"):return
                    except RuntimeError:pass
                    time.sleep(.1)
                raise AssertionError(path+" failed "+test)
            try:
                for folder in ("_site","_release"):
                    for width in (390,1200):
                        browser.call("Emulation.setDeviceMetricsOverride",{"width":width,"height":850,"deviceScaleFactor":1,"mobile":width<500})
                        navigate("/"+folder+"/cases/?lang=zh","document.documentElement.lang==='zh-Hant' && document.querySelectorAll('article.card').length===5")
                        count=browser.evaluate("(()=>{const el=document.querySelector('#case-search');el.value='BMW';el.dispatchEvent(new Event('input'));return document.querySelectorAll('article.card:not([hidden])').length})()")
                        assert count==1,count
                        navigate("/"+folder+"/cases/sulawesi-nickel/?lang=zh","document.querySelectorAll('.timeline li').length===4")
                        assert browser.evaluate("document.body.innerText.includes('2026-12-01')")
                        assert browser.evaluate("document.documentElement.scrollWidth<=innerWidth+2")
                    routes = ["cases/", "cases/sulawesi-nickel/", "team/", "", "sources/", "workbench/", "methodology/", "policy/", "research/"]
                    if folder == "_site":
                        routes.extend(["workbench/edit/", "record.html"])
                    for route in routes:
                        navigate("/"+folder+"/"+route+"?lang=en","document.documentElement.lang==='en'")
                        if route == "team/":
                            # Expose the local form to inspect its controls without an account.
                            browser.evaluate("document.querySelectorAll('[hidden]').forEach(el=>el.hidden=false);document.querySelectorAll('details').forEach(el=>el.open=true);true")
                        mixed = browser.evaluate(r"""(() => {
                          const controls = document.querySelectorAll('nav a, button, summary, label, select option, [aria-label], [placeholder]');
                          const names = [...controls].filter(el => el.matches('option') || el.getClientRects().length).map(el => {
                            const text = el.matches('option') ? el.textContent : el.innerText;
                            return [text, el.getAttribute('aria-label'), el.getAttribute('placeholder')].filter(Boolean).join(' ');
                          });
                          return names.filter(name => /[\u3400-\u9fff]/u.test(name));
                        })()""")
                        assert not mixed, (folder,route,mixed)
                    navigate("/"+folder+"/team/?lang=en","document.querySelector('#status').textContent.includes('not connected')")
                    assert browser.evaluate("""(()=>{const picker=document.querySelector('#lang');picker.value='zh';picker.dispatchEvent(new Event('change'));return document.querySelector('#status').textContent.includes('尚未連接')})()""")
                    for route in ("workbench/", "policy/", "research/", "sources/"):
                        for lang,label in (("en","Case tracking"),("zh","案件追蹤"),("de","Fallverfolgung"),("es","Seguimiento de casos")):
                            navigate("/"+folder+"/"+route+"?lang="+lang, "document.querySelector('[data-case-nav]').textContent==="+json.dumps(label))
                    navigate("/"+folder+"/team/?lang=zh","document.querySelector('#status').textContent.includes('尚未連接')")
                    assert browser.evaluate("document.querySelector('#desk').hidden")
                print("PASS desktop/mobile pilot and private-release layouts, search, source timeline and unconfigured desk")
            finally:browser.close()
    finally:server.shutdown();server.server_close()
if __name__=="__main__":main()
