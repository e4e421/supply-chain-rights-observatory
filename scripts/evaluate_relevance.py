#!/usr/bin/env python3
"""Compute only title-level exploratory precision and recall on an explicit tiny sample."""
import json,sys
from pathlib import Path
from research_quality import screen_title,VERSION
ROOT=Path(__file__).resolve().parents[1]
def evaluate():
    doc=json.loads((ROOT/"sources/validation/title_labels.json").read_text(encoding="utf-8"))
    labels=doc["cases"]
    tp=fp=fn=tn=0
    for case in labels:
        predicted=screen_title(case["title"])["status"]=="candidate_relevant"
        actual=case["relevant"]
        if predicted and actual:tp+=1
        elif predicted:fp+=1
        elif actual:fn+=1
        else:tn+=1
    precision=tp/(tp+fp) if tp+fp else 0
    recall=tp/(tp+fn) if tp+fn else 0
    print(f"Title-only quality screen {VERSION}: TP={tp}, FP={fp}, FN={fn}, TN={tn}, precision={precision:.3f}, recall={recall:.3f}; sample n={len(labels)}")
    print("WARNING: this tiny hand-labelled headline sample is a regression fixture, not research-grade validation.")
    return precision,recall
if __name__=="__main__":
    precision,recall=evaluate()
    if precision<0.8 or recall<0.70:sys.exit("Exploratory quality regression requires editorial review.")
