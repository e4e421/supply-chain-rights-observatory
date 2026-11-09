#!/usr/bin/env python3
"""Fail on common accessibility / static site security regressions. Does not
replace a browser axe-core/VoiceOver/NVDA or a penetration test."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/"docs/index.html").read_text(encoding="utf-8")
JS=(ROOT/"docs/app.js").read_text(encoding="utf-8")
CSS=(ROOT/"docs/styles.css").read_text(encoding="utf-8")
I18N=(ROOT/"docs/i18n.js").read_text(encoding="utf-8")
checks={
"declared English source language":'<html lang="en">' in HTML,
"language control":'id="language-select"' in HTML,
"skip link":'class="skip-link"' in HTML,
"live result count":'id="results-count"' in HTML and 'aria-live="polite"' in HTML,
"no lang auto":"""setAttribute('lang','auto')""" not in JS,
"no innerHTML / eval":not any(x in (HTML+JS+I18N) for x in ("innerHTML","eval(","new Function(","document.write(")),
"no external runtime script":not bool(re.search(r'<script[^>]*src=["\']https?://',HTML,re.I)),
"no embedded credential pattern":not bool(re.search(r'(?:api_key|secret|token)\s*[:=]\s*["\'][A-Za-z0-9_\-]{18,}',HTML+JS,re.I)),
"focus-visible styles":":focus-visible" in CSS and ":focus-within" in CSS,
"reduced motion":'prefers-reduced-motion' in CSS,
"content security policy":'Content-Security-Policy' in HTML,
"no inline JS handlers":not bool(re.search(r'\bon(?:click|load|error|change)\s*=',HTML,re.I))
}
WORKBENCH=(ROOT/"docs/workbench/index.html").read_text(encoding="utf-8")
WB_JS=(ROOT/"docs/workbench/workbench.js").read_text(encoding="utf-8")
WB_CSS=(ROOT/"docs/workbench/workbench.css").read_text(encoding="utf-8")
checks.update({
"workbench English document":'<html lang="en">' in WORKBENCH,
"workbench independent static subpage":'href="./workbench/"' in HTML and 'src="./workbench.js"' in WORKBENCH,
"workbench local-only scripts":not bool(re.search(r"<script[^>]+src=[\x22\x27]https?://",WORKBENCH,re.I)),
"workbench CSP and focus":'Content-Security-Policy' in WORKBENCH and ':focus-visible' in CSS,
"workbench no unsafe JS HTML sinks":not any(x in (WORKBENCH+WB_JS) for x in ("innerHTML","new Function(","document.write(","eval(")),
"workbench no inline event handlers":not bool(re.search(r"\bon(?:click|load|error|change)\s*=",WORKBENCH,re.I)),
"workbench secure URLs":'https:' in WB_JS and "noopener noreferrer" in WB_JS,
"workbench keyboard and local saved views":'keydown' in WB_JS and 'localStorage' in WB_JS,
})
for label,passed in checks.items():
 print(("PASS" if passed else "FAIL")+" "+label)
if not all(checks.values()):raise SystemExit(1)
