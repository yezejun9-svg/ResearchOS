import hashlib,json
from pathlib import Path
p=Path(__file__).resolve().parent
def ref(x):
 b=x.read_bytes();return {"path":str(x),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def new(n,v):
 with (p/n).open("x",encoding="utf-8",newline="\n") as f:json.dump(v,f,ensure_ascii=True,indent=2)
members={x.name:ref(x) for x in sorted(p.iterdir()) if x.is_file()}
new("MF.json",{"members":members})
new("HDF.json",{"schema":"researchos.source-read-failure-handoff.v1","failure_ordinal":805,"formal":False,
 "status":"SEALED_DISTINCT_READ_FAILURE","manifest_ref":ref(p/"MF.json"),
 "failure_origin_ref":ref(p/"failure-origin.805.json"),"original_io_ref":ref(p/"original-tool-io.json"),
 "actualOuter":1,"actualPython":None,"native":None,"private_reads":False,"native_or_sql_run":False})
print(json.dumps({"HDF":ref(p/"HDF.json"),"MF":ref(p/"MF.json"),"origin":ref(p/"failure-origin.805.json")},ensure_ascii=True))

