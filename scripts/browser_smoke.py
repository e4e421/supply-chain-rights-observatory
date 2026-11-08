#!/usr/bin/env python3
"""Optional real-Chrome smoke test for the static three-language site.

Requires locally installed Chrome/Chromium. Outputs explicit SKIPPED status if
the browser is absent; must not be reported as a passed accessibility audit.
"""
import json,os,shutil,subprocess,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CHROME=next((shutil.which(x) for x in ("google-chrome","chromium","chromium-browser","google-chrome-stable") if shutil.which(x)),None)
def run():
    if not CHROME:
        print("SKIPPED browser smoke: no Chrome/Chromium binary on runner")
        return
    server=subprocess.Popen(["python3","-m","http.server","8765","--bind","127.0.0.1","--directory",str(ROOT/"docs")],
                            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        time.sleep(1)
        cases=[("en","Where supply chains"),("zh","供應鏈"),("de","Wo Lieferketten")]
        with tempfile.TemporaryDirectory() as profile:
            for code,expected in cases:
                args=[CHROME,"--headless=new","--no-sandbox","--disable-dev-shm-usage","--disable-gpu",
                      "--virtual-time-budget=4000","--user-data-dir="+profile+"-"+code,
                      "--dump-dom","http://127.0.0.1:8765/index.html?lang="+code]
                got=subprocess.run(args,capture_output=True,text=True,timeout=50,check=True).stdout
                if expected not in got:raise ValueError("Language render failed: "+code)
                if 'id="archive-results"' not in got:raise ValueError("Archive explorer absent")
                print("PASS browser render:",code)
            catalog=json.loads((ROOT/"docs/data/archive/catalog.json").read_text())
            if catalog.get("months"):
                m=catalog["months"][0]
                shard=json.loads((ROOT/"docs/data/archive"/m["files"][0]["file"]).read_text())
                if shard.get("records"):
                    uid=shard["records"][0]["record_id"]
                    uri="http://127.0.0.1:8765/record.html?month="+m["month"]+"&id="+uid
                    args=[CHROME,"--headless=new","--no-sandbox","--disable-dev-shm-usage","--disable-gpu",
                          "--virtual-time-budget=4000","--user-data-dir="+profile+"-detail",
                          "--dump-dom",uri]
                    got=subprocess.run(args,capture_output=True,text=True,timeout=50,check=True).stdout
                    if uid not in got:raise ValueError("Public record detail did not render")
                    print("PASS browser record detail:",uid)
        print("WARNING: Browser smoke is not screen reader, WCAG, keyboard or penetration testing.")
    finally:
        server.terminate()
        try:server.wait(timeout=5)
        except subprocess.TimeoutExpired:server.kill()
if __name__=="__main__":run()
