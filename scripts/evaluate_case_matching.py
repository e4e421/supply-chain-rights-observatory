"""Measure the local shortlist on authored routing examples; no network or model calls."""
from pathlib import Path
import json
from case_assist import shortlist
ROOT=Path(__file__).resolve().parents[1]
def evaluate():
    cases=json.loads((ROOT/"cases/pilot.json").read_text())
    examples=json.loads((ROOT/"tests/case_matching_examples.json").read_text())
    counts={"examples":len(examples),"match_examples":0,"top1_correct":0,"unrelated_examples":0,"correct_abstentions":0}
    for row in examples:
        options=shortlist(cases,[{"url":"https://fixture.example/item","excerpt":row["excerpt"]}])
        candidate=options[0]["id"] if options else None
        if row["expected"]:
            counts["match_examples"]+=1
            counts["top1_correct"]+=int(candidate==row["expected"])
        else:
            counts["unrelated_examples"]+=1
            counts["correct_abstentions"]+=int(candidate is None)
    return counts
if __name__=="__main__":print(json.dumps(evaluate()))
