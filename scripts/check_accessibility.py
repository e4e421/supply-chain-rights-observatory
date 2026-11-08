#!/usr/bin/env python3
"""Static accessibility and contrast regression checks, not WCAG certification."""
from __future__ import annotations
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/"docs/index.html").read_text(encoding="utf-8")
CSS=(ROOT/"docs/styles.css").read_text(encoding="utf-8")
DETAIL=(ROOT/"docs/record.html").read_text(encoding="utf-8")
class Scan(HTMLParser):
    def __init__(self):
        super().__init__();self.inputs=[];self.labels=[];self.links=[];self.headings=[];self.lang=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=="html":self.lang=a.get("lang")
        if tag in ("input","select"):self.inputs.append(a)
        if tag=="label":self.labels.append(a)
        if tag=="a":self.links.append(a)
        if tag in ("h1","h2","h3"):self.headings.append(tag)
def lum(h):
    rgb=[int(h[k:k+2],16)/255 for k in (1,3,5)]
    rgb=[x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in rgb]
    return 0.2126*rgb[0]+0.7152*rgb[1]+0.0722*rgb[2]
def ratio(a,b):
    l,h=sorted((lum(a),lum(b)))
    return (h+.05)/(l+.05)
def audit():
    v=Scan();v.feed(HTML)
    assert v.lang=="en"
    assert v.headings and v.headings[0]=="h1"
    assert "skip-link" in HTML and "href=\"#signals\"" in HTML
    labelled={x.get("for") for x in v.labels if x.get("for")}
    labels_by_wrap=("search-wrap" in HTML)
    for field in v.inputs:
        if field.get("type")=="hidden":continue
        assert field.get("id") in labelled or field.get("aria-label") or (labels_by_wrap and field.get("id")=="search"), field
    for link in v.links:
        if link.get("target")=="_blank":assert "noopener" in link.get("rel","")
    assert ":focus-visible" in CSS and ":focus-within" in CSS
    assert "prefers-reduced-motion" in CSS
    assert 'lang="auto"' not in HTML+DETAIL
    known_pairs=[
        ("#40564e","#ffffff",4.5),
        ("#354e43","#ffffff",4.5),
        ("#36594a","#ffffff",4.5),
        ("#153d33","#ffffff",4.5),
        ("#697772","#ffffff",4.5)
    ]
    for fg,bg,target in known_pairs:
        actual=ratio(fg,bg)
        assert actual>=target,(fg,bg,actual)
    assert "color:#40564e" in CSS
    print("PASS: labelled controls, landmarks, skip link, language, external links, keyboard focus and sampled text contrast.")
    print("WARNING: WCAG AA remains unverified without real assistive-technology and responsive-browser testing.")
if __name__=="__main__":audit()
