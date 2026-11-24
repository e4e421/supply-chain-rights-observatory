"""Confirm the release manifest and case index served from Pages."""
import hashlib
import json
import os
import time
from pathlib import Path
from urllib.parse import urlencode
from confirm_release import read_public_file

OUT=Path(__file__).resolve().parents[1]/"_release"
def verify(expected,read):
    live=json.loads(read("data/release.json",65536))
    if live!=expected:raise ValueError("Release manifest mismatch")
    payload=read("data/cases.json",12_000_000)
    if hashlib.sha256(payload).hexdigest()!=expected["cases_sha256"]:raise ValueError("Case index mismatch")
if __name__=="__main__":
    release=json.loads((OUT/"data/release.json").read_text())
    if release["revision"]!=os.environ["GITHUB_SHA"]:raise ValueError("Wrong release revision")
    for attempt in range(6):
        try:
            q=urlencode({"release":release["revision"],"run":release["workflow_run"],"attempt":attempt})
            verify(release,lambda path,size:read_public_file(path,size,q))
            print("Confirmed public case release",release["revision"],release["case_count"]);break
        except (OSError,ValueError):
            if attempt==5:raise
            time.sleep(5)
