from pathlib import Path
import hashlib,json
ROOT=Path("D:/作品集/ResearchOS/research-os")
PACK=ROOT/"execution/v2.4/receipts/W05/W05-99/f08_driver18_execution_preparation_codex/d8a13bae58b341d8b28c0092527df4fc"
OWN=ROOT/"execution/v2.4/receipts/W05/W05-99/f08_driver18_execution_independent_source_review_codex/86a653e6772140f1b85f472613ef6d81"
def ref(p):
 raw=p.read_bytes()
 return {"path":p.as_posix(),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def save(n,d):
 p=OWN/n
 if p.exists():raise RuntimeError("new-only file exists")
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
manifest=json.loads((PACK/"manifest.json").read_bytes())
need_count=len(manifest["members"])
if need_count!=34:raise RuntimeError("author manifest membership changed")
expected=[{"role":"author_manifest","ref":ref(PACK/"manifest.json")}]
for i,r in enumerate(manifest["members"]):expected.append({"role":"author_member_"+str(i).zfill(2),"ref":r})
scope=json.loads((PACK/"scope.UNBOUND.proposed.json").read_bytes())
for k in ["utility_ref","owned_helper_ref","debug_helper_ref"]:expected.append({"role":k,"ref":scope[k]})
fixed=json.loads((PACK/"fixed-inputs.json").read_bytes())
for k,r in fixed.items():
 if isinstance(r,dict) and set(r)=={"path","sha256","bytes"}:expected.append({"role":"fixed_"+k,"ref":r})
records=[]
seen={}
for x in expected:
 p=Path(x["ref"]["path"]);a=ref(p)
 if a["sha256"]!=x["ref"]["sha256"] or a["bytes"]!=x["ref"]["bytes"]:raise RuntimeError("public expected ref mismatch")
 key=str(p.resolve()).casefold()
 if key in seen:
  seen[key]["roles"].append(x["role"]);continue
 i=len(records);raw=p.read_bytes();copy=OWN/"source-snapshots"/(str(i).zfill(2)+"-"+p.name)
 if copy.exists():raise RuntimeError("snapshot exists")
 copy.parent.mkdir(parents=True,exist_ok=True);copy.write_bytes(raw)
 if hashlib.sha256(raw).hexdigest()!=a["sha256"]:raise RuntimeError("read race")
 row={"roles":[x["role"]],"expected":x["ref"],"actual":a,"copy":ref(copy)}
 records.append(row);seen[key]=row
save("inputs.before.json",records)
save("packet-verification.json",{"author_manifest":ref(PACK/"manifest.json"),"actual_listed_rehashed":34,"author_self_plus":35,"unique_selected_ref_count":len(records),"full1899_files_rehashed":False,"reused_sealed_source_resource_review":fixed["non_author_handoff_ref"],"actual_target_execution":False})
print(json.dumps({"listed_members_rehashed":34,"unique_selected_refs":len(records),"native_target_execution":0,"own_namespace":OWN.as_posix()},ensure_ascii=False))
