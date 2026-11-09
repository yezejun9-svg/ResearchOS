from pathlib import Path
import json,hashlib,ast
R=Path("D:/作品集/ResearchOS/research-os");P=R/"execution/v2.4/receipts/W05/W05-99";N=P/"cli43_root_binding_preparation_codex/629d2cb794ab4ae4a04a1db9d8a3f8ef";O=Path(__file__).parent
checks=[];inputs={}
def pin(p):
 p=Path(p);p=p if p.is_absolute() else R/p;b=p.read_bytes();x={"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)};inputs[str(p)]=x;return x
def ck(k,v,d=None):checks.append({"name":k,"passed":bool(v),"details":d})
def verify(r,k):
 a=pin(r["path"]);ck(k,a["sha256"]==r["sha256"] and a["bytes"]==r["bytes"],{"expected":r,"actual":a})
def read(p):pin(p);return json.loads(Path(p).read_bytes())
def walk(x,k):
 if isinstance(x,dict):
  if {"path","sha256","bytes"}<=x.keys() and isinstance(x["path"],str):verify(x,k)
  else:
   for a,b in x.items():walk(b,k+"/"+a)
 elif isinstance(x,list):
  for i,b in enumerate(x):walk(b,k+"/"+str(i))
for name,h in [("handoff.json","8c4060c06c35a43266d2cc1c2bd7687521eb34cdc87108406b4194b642d33cb9"),("manifest.json","6d9e179f7f4d92c336ed161b4c628bdf7cd8a3011c72b07ec1cbde70c6328b5e")]:ck("Root_pin."+name,pin(N/name)["sha256"]==h)
m=read(N/"manifest.json");ck("manifest_count",len(m["entries"])==m["count"]==20)
for i,x in enumerate(m["entries"]):verify(x,"manifest."+str(i))
for name in ["handoff.json","input-refs.json","scope.v3.proposed.json","gate-v3-inverse-audit.json"]:walk(read(N/name),name)
old=P/"cli43_fresh_compiler_preparation_revision_codex/bb395255ecb14df6820b2e20631c9c39";m2=read(old/"manifest.complete.json")
ck("old_manifest25",len(m2["entries"])==25)
for i,x in enumerate(m2["entries"]):verify(x,"old_member."+str(i))
j=read(N/"gate-v3-inverse-audit.json");b=Path(j["new_ref"]["path"]).read_bytes()
for i,e in reversed(list(enumerate(j["edits"]))):
 x=e["new"].encode();ck("inverse_unique."+str(i),b.count(x)==1,b.count(x));b=b.replace(x,e["old"].encode(),1)
ck("gate_four_substitutions_exact_inverse",len(j["edits"])==4 and b==Path(j["original_ref"]["path"]).read_bytes())
for x in m["entries"]:
 p=Path(x["path"])
 if p.suffix==".py":ast.parse(p.read_bytes(),filename=str(p));ck("AST_ONLY."+p.name,True)
s=read(N/"scope.v3.proposed.json");orig=read(old/"scope.proposed.json")
for k in ["runner_ref","launcher_ref","instrumentation_ref","instrumented_source_ref","instrumentation_helper_ref","ordered_cases","limits"]:ck("unchanged_request3."+k,s[k]==orig[k])
ck("review_path_no_hash_cycle",s.get("controller_review_path") is None and "controller_review_ref" not in s)
b=read(N/"binding.proposed.json");ck("binding_unbound",b["preparation_only"] is True and b["execution_authorized"] is False)
for k in ["before","after","origin_cut_ref","runtime_resources_ref","compiler_resources_ref","controller_review_ref","controller_review_path","current43_authority_ref"]:ck("future_null."+k,b[k] is None)
for x in list(inputs.values()):verify(x,"after."+x["path"])
a={"schema":"researchos.cli43-root-binding-independent-static-audit.v1","checks":checks,"check_count":len(checks),"failed_count":sum(not x["passed"] for x in checks),"inputs":list(inputs.values()),"input_count":len(inputs),"target_imports":0,"native_Git_Go_SQL_HTTP_MODEL_DLL_calls":0,"source_canonical_mutations":0,"actual_cases":0,"full_current_resource_catalog_rehash":False}
(O/"audit.json").write_bytes((json.dumps(a,ensure_ascii=False,indent=2)+"\n").encode())
print(json.dumps({"output":str(O),"checks":len(checks),"failed":a["failed_count"],"inputs":len(inputs)},ensure_ascii=False))
