"""Run against the official Firebase Auth and Firestore emulators only."""
import json
import os
import uuid
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from case_store import Firestore,encode
from case_model import public_cases

def main():
    os.environ["FIREBASE_PROJECT_ID"]="demo-scro"
    if os.environ.get("FIRESTORE_EMULATOR_HOST") not in ("127.0.0.1:8088","localhost:8088"):
        raise ValueError("Start the demo Firestore emulator on loopback port 8088")
    if os.environ.get("FIREBASE_AUTH_EMULATOR_HOST") not in ("127.0.0.1:9097","localhost:9097"):
        raise ValueError("Start the demo Auth emulator on loopback port 9097")
    db=Firestore()
    def user(role=None):
        email=uuid.uuid4().hex+"@example.test"
        req=Request("http://127.0.0.1:9097/identitytoolkit.googleapis.com/v1/accounts:signUp?key=demo",
                    data=json.dumps({"email":email,"password":uuid.uuid4().hex,"returnSecureToken":True}).encode(),
                    headers={"Content-Type":"application/json"})
        with urlopen(req,timeout=8) as r: auth=json.load(r)
        if role:db.put("members",auth["localId"],{"role":role})
        return auth
    def call(auth,path,method,body=None,denied=False):
        token=auth.get("idToken") if auth else None
        req=Request("http://127.0.0.1:8088/v1/"+db.path+path,method=method,
                    data=json.dumps(body).encode() if body is not None else None,
                    headers={"Content-Type":"application/json",**({"Authorization":"Bearer "+token} if token else {})})
        try:
            with urlopen(req,timeout=8) as r: result=json.load(r)
        except HTTPError as err:
            if denied and err.code in (401,403):return
            raise
        if denied:raise AssertionError("Unexpected admission: "+path)
        return result
    outsider,researcher,editor=user(),user("researcher"),user("editor")
    cid="case-"+uuid.uuid4().hex
    case=json.loads((Path(__file__).resolve().parents[1]/"cases/pilot.json").read_text())[0]
    case["id"]=cid;payload=json.dumps(case,ensure_ascii=False)
    draft={"payload":payload,"note":"private-only","owner":"team","updatedBy":researcher["localId"]}
    fields=lambda row:{k:encode(v) for k,v in row.items()}
    call(researcher,"/caseDrafts/"+cid,"PATCH",{"fields":fields(draft)})
    call(None,"/caseDrafts/"+cid,"GET",denied=True);call(outsider,"/caseDrafts/"+cid,"GET",denied=True)
    call(researcher,"/members/"+researcher["localId"],"PATCH",{"fields":fields({"role":"editor"})},denied=True)
    call(editor,"/caseDrafts/"+cid,"GET")
    db.immutable("researchRecords",{cid:{"kind":"discovery","title":"sample","url":"https://example.test/item"}})
    call(outsider,"/researchRecords/"+cid,"GET",denied=True);call(researcher,"/researchRecords/"+cid,"GET")
    def writes(auth,state,value):
        ver=uuid.uuid4().hex;name=db.path+"/casePublications/"+cid
        obj=fields({"payload":value,"state":state,"reviewer":auth["localId"],"version":ver})
        return [{"update":{"name":name,"fields":obj}},{"update":{"name":name+"/versions/"+ver,"fields":obj},"currentDocument":{"exists":False}}]
    call(researcher,":commit","POST",{"writes":writes(researcher,"approved",payload)},denied=True)
    call(editor,":commit","POST",{"writes":writes(editor,"approved","incorrect draft")},denied=True)
    approval=writes(editor,"approved",payload)
    call(editor,":commit","POST",{"writes":approval[:1]},denied=True)
    call(editor,":commit","POST",{"writes":approval})
    call(None,"/casePublications/"+cid,"GET",denied=True)
    doc=db.get("casePublications",cid)
    result=public_cases([],[(cid,{"state":doc["state"],"public":json.loads(doc["payload"])})])
    assert result==[case] and "private-only" not in str(result)
    call(editor,":commit","POST",{"writes":writes(editor,"withdrawn","")})
    assert db.get("casePublications",cid)["state"]=="withdrawn"
    print("PASS anonymous, nonmember, researcher, editor, approval history, withdrawal and immutable import")
if __name__=="__main__":main()
