"""Private Firestore REST adapter for immutable source rows and reviewed releases."""
import json
import os
import re
from urllib.error import HTTPError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from case_model import digest

def encode(value):
    if value is None: return {"nullValue": None}
    if isinstance(value,bool): return {"booleanValue": value}
    if isinstance(value,int): return {"integerValue": str(value)}
    if isinstance(value,str): return {"stringValue": value}
    raise TypeError("Firestore envelope fields must be scalar")

def unpack(doc):
    fields={}
    for key, typed in doc.get("fields",{}).items():
        typ, val=next(iter(typed.items()))
        fields[key]=int(val) if typ=="integerValue" else val
    return fields

def envelope(data):
    return {"payload":json.dumps(data,ensure_ascii=False,separators=(",",":")),"digest":digest(data)}

class Firestore:
    def __init__(self):
        project=os.environ.get("FIREBASE_PROJECT_ID","")
        if not re.fullmatch(r"[a-z][a-z0-9-]{4,28}[a-z0-9]",project):
            raise ValueError("Set FIREBASE_PROJECT_ID for the intended project")
        self.path=f"projects/{project}/databases/(default)/documents"
        emulator=os.environ.get("FIRESTORE_EMULATOR_HOST")
        if emulator:
            if not re.fullmatch(r"(localhost|127\.0\.0\.1):[0-9]{2,5}",emulator) or not project.startswith("demo-"):
                raise ValueError("Emulator must use a loopback address and demo project")
            self.origin="http://"+emulator+"/v1/"
            self.token="owner"
        else:
            self.origin="https://firestore.googleapis.com/v1/"
            self.token=os.environ.get("FIRESTORE_OAUTH_TOKEN")
            if not self.token: raise ValueError("Private Firestore requires a short-lived OAuth access token")

    def request(self, method, suffix, body=None):
        data=None if body is None else json.dumps(body,ensure_ascii=False).encode()
        req=Request(self.origin+self.path+suffix,data=data,method=method,headers={
            "Authorization":"Bearer "+self.token,"Content-Type":"application/json"})
        with urlopen(req,timeout=45) as response:
            return json.load(response)

    def all(self,collection):
        token=None
        while True:
            params={"pageSize":200}
            if token: params["pageToken"]=token
            page=self.request("GET","/"+collection+"?"+urlencode(params))
            for doc in page.get("documents",[]):
                yield doc["name"].rsplit("/",1)[-1],unpack(doc)
            token=page.get("nextPageToken")
            if not token: break

    def get(self,collection,key):
        try: doc=self.request("GET",f"/{collection}/{quote(key,safe='')}")
        except HTTPError as err:
            if err.code==404: return None
            raise
        return unpack(doc)

    def put(self,collection,key,data):
        self.request("PATCH",f"/{collection}/{quote(key,safe='')}",{"fields":{k:encode(v) for k,v in data.items()}})

    def immutable(self,collection,rows,identity=None):
        """Read back every chunk. Replaying a partially completed import is safe."""
        pending=list(rows.items())
        for start in range(0,len(pending),100):
            chunk=pending[start:start+100]
            names={self.path+"/"+collection+"/"+key:value for key,value in chunk}
            def read():
                return self.request("POST",":batchGet",{"documents":list(names)})
            existing=read()
            writes=[]
            for result in existing:
                if "found" in result:
                    doc=result["found"]
                    previous=json.loads(unpack(doc)["payload"])
                    if identity is not None and identity(previous)==identity(names[doc["name"]]):
                        names[doc["name"]]=previous
                    self.check(doc,names[doc["name"]])
                else:
                    name=result["missing"]
                    row=envelope(names[name])
                    writes.append({"update":{"name":name,"fields":{k:encode(v) for k,v in row.items()}},
                                   "currentDocument":{"exists":False}})
            if writes: self.request("POST",":commit",{"writes":writes})
            received=set()
            for item in read():
                doc=item["found"]
                self.check(doc,names[doc["name"]])
                received.add(doc["name"])
            if received!=set(names): raise ValueError("Incomplete read-back verification")
        return len(pending)

    @staticmethod
    def check(doc,expected):
        row=unpack(doc)
        if row.get("digest")!=digest(expected) or json.loads(row["payload"])!=expected:
            raise ValueError("Private archive verification mismatch")

def read_publications(db):
    for key,doc in db.all("casePublications"):
        if doc.get("state")=="withdrawn":
            yield key,{"state":"withdrawn"}
        elif doc.get("state")=="approved":
            yield key,{"state":"approved","public":json.loads(doc["payload"])}
        else:
            raise ValueError("Invalid approved document")
