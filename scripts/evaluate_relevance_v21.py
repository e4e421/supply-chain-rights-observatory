#!/usr/bin/env python3
"""Evaluate independently annotated samples, never claim synthetic labels as accuracy."""
import argparse,json
from pathlib import Path
from relevance_engine import ROOT,analyze

def evaluate(doc):
    cases=doc.get('cases',[])
    labelled=[x for x in cases if x.get('human_label') in ('relevant','irrelevant') and x.get('labelled_by')]
    if not labelled:return {'status':'awaiting_independent_annotations','labelled_count':0,'available_cases':len(cases),'precision':None,'recall':None}
    out={}
    for name,levels in [('high_priority',{'high'}),('retained_candidates',{'high','review'})]:
        tp=fp=fn=tn=0
        for c in labelled:
            predicted=analyze(c)['level'] in levels;actual=c['human_label']=='relevant'
            if predicted and actual:tp+=1
            elif predicted:fp+=1
            elif actual:fn+=1
            else:tn+=1
        out[name]={'tp':tp,'fp':fp,'fn':fn,'tn':tn,'precision':tp/(tp+fp) if tp+fp else None,'recall':tp/(tp+fn) if tp+fn else None}
    return {'status':'sample_metrics_only','labelled_count':len(labelled),'available_cases':len(cases),'results':out,
            'warning':'A stratified convenience sample is not a population-level accuracy estimate. Do not tune and evaluate on the same labels.'}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--labels',type=Path,default=ROOT/'_site/data/relevance-validation-sample.json');args=p.parse_args()
    print(json.dumps(evaluate(json.loads(args.labels.read_text())),indent=2))
