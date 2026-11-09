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
                # The former status badge is now the explicit workbench entry.
                if 'class="top-tag workbench-entry"' not in got:
                    raise ValueError("Clickable workbench entry missing: "+code)
                if 'aria-label="'+({"en":"Open Research Workbench","zh":"開啟專業研究工作台","de":"Forschungsarbeitsplatz öffnen"}[code])+'"' not in got:
                    raise ValueError("Workbench entry accessible label missing: "+code)

                print("PASS browser render:",code)
            for code,expected in [("en","Research Workbench"),("zh","專業研究工作台"),("de","Forschungsarbeitsplatz")]:
                args=[CHROME,"--headless=new","--no-sandbox","--disable-dev-shm-usage","--disable-gpu",
                      "--virtual-time-budget=5500","--user-data-dir="+profile+"-workbench-"+code,
                      "--dump-dom","http://127.0.0.1:8765/workbench/?scope=latest&lang="+code]
                got=subprocess.run(args,capture_output=True,text=True,timeout=55,check=True).stdout
                if expected not in got:raise ValueError("Workbench language failed: "+code)
                if 'id="wb-tbody"' not in got:raise ValueError("Workbench table missing")
                if not __import__('re').search(r'data-record-id="[a-f0-9]{18}"',got):
                    raise ValueError("Workbench did not load live records: "+code)
                print("PASS browser workbench:",code)
            catalog=json.loads((ROOT/"docs/data/archive/catalog.json").read_text())
            if catalog.get("months"):
                m=catalog["months"][0]
                # Verify professional deep links, month scope and URL-based query state.
                checks=[
                    ("archive","/workbench/?scope=archive&month="+m["month"]+"&lang=en",'data-record-id="'),
                    ("combined","/workbench/?scope=all&lang=en","Scope: combined catalogue"),
                    ("empty-filter","/workbench/?scope=latest&q=SCRO_SENTINEL_NO_RESULT_9031&lang=en","0 Records shown")
                ]
                for label,path,needle in checks:
                    args=[CHROME,"--headless=new","--no-sandbox","--disable-dev-shm-usage","--disable-gpu",
                          "--virtual-time-budget=6000","--user-data-dir="+profile+"-workbench-"+label,
                          "--dump-dom","http://127.0.0.1:8765"+path]
                    got=subprocess.run(args,capture_output=True,text=True,timeout=55,check=True).stdout
                    if needle not in got:raise ValueError("Workbench deep link failed: "+label)
                    print("PASS browser workbench deep link:",label)
                if m.get("files"):
                    first=json.loads((ROOT/"docs/data/archive"/m["files"][0]["file"]).read_text())
                    if first.get("records"):
                        rid=first["records"][0]["record_id"]
                        uri="http://127.0.0.1:8765/workbench/?scope=archive&month="+m["month"]+"&record="+rid+"&lang=en"
                        args=[CHROME,"--headless=new","--no-sandbox","--disable-dev-shm-usage","--disable-gpu",
                              "--virtual-time-budget=6000","--user-data-dir="+profile+"-workbench-selected",
                              "--dump-dom",uri]
                        got=subprocess.run(args,capture_output=True,text=True,timeout=55,check=True).stdout
                        selected_row=__import__("re").search(r'<tr[^>]*data-record-id="'+rid+r'"[^>]*>',got)
                        if not selected_row or 'is-selected' not in selected_row.group(0):
                            raise ValueError("Workbench selected record deep link failed")
                        print("PASS browser workbench selected record:",rid)
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
