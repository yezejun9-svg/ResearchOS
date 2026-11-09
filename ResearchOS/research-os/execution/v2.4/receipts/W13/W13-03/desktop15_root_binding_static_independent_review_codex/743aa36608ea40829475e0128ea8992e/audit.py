from pathlib import Path
import json,hashlib,ast
R=Path("D:/作品集/ResearchOS/research-os")
N=R/"execution/v2.4/receipts/W13/W13-03/desktop15_root_scope_binding_preparation_codex/f2adb6bf003a47498516d95970690096"
O=Path(__file__).parent
checks=[];inputs={}
def ref(p):
 p=Path(p);p=p if p.is_absolute() else R/p;b=p.read_bytes();v={"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)};inputs[str(p)]=v;return v
def ck(n,v,d=None):checks.append({"name":n,"passed":bool(v),"details":d})
def verify(x,n):
 a=ref(x["path"]);ck(n,a["sha256"]==x["sha256"] and a["bytes"]==x["bytes"],{"expected":x,"actual":a})
def doc(p):ref(p);return json.loads(Path(p).read_bytes())
def walk(j,n):
 if isinstance(j,dict):
  if {"path","sha256","bytes"}<=j.keys() and isinstance(j["path"],str):verify(j,n)
  else:
   for k,v in j.items():walk(v,n+"/"+k)
 elif isinstance(j,list):
  for i,v in enumerate(j):walk(v,n+"/"+str(i))
m=doc(N/"manifest.json");ck("manifest_count",m["count"]==len(m["entries"])==15)
ck("root_manifest_pin",ref(N/"manifest.json")["sha256"]=="12fd849c6b942a8f50af4b4a8227884ebe9f89f767361fc64e533e090755a96a")
ck("root_handoff_pin",ref(N/"handoff.json")["sha256"]=="ffcea340f109cdd5145a26e5adaee5eddf32d64cba78c278cd1fe30d586bf8fa")
for i,x in enumerate(m["entries"]):verify(x,"manifest."+str(i))
b=doc(N/"inputs.before.json");a=doc(N/"inputs.after.json");ck("author_fixed28_equal",a==b and len(a)==28)
for i,x in enumerate(b):verify(x,"fixed28."+str(i))
for n in ["spec.json","handoff.json","root-request.example.json","metadata-input.example.json","grant-launcher-derivation-plan.json"]:walk(doc(N/n),n)
for n in ["build-scope.py","build-metadata-templates.py","metadata-engine.template.py"]:
 ast.parse((N/n).read_bytes(),filename=str(N/n));ck("AST_ONLY."+n,True)
q=doc(N/"root-request.example.json")
for k in ["expected_before","expected_after","expected_main_branch","operation_uuid","registration_namespace","binding_output_root","canonical_before_refs","current_root_handoff_ref","current_root_manifest_ref","runtime_resources_ref","status_ref","origin_cut_ref","confirmed_pending_origins"]:ck("required_future_null."+k,q[k] is None)
ck("request_not_grant",q["authorized"] is False and q["future_root_grant"] is None)
spec=doc(N/"spec.json");closed=doc(Path(spec["closed43_review_ref"]["path"]))
for k,v in spec["existing_completed_manifest_ref_objects"].items():ck("original_dictionary."+k,closed[k]==v)
permit=doc(Path(spec["independent_source_suitability_ref"]["path"]))
ck("source_only_permit",permit["source_integration_permitted"] is True and permit["source_commit"]==spec["candidate_source"] and permit["requested_changes"]==[])
for x in list(inputs.values()):verify(x,"after."+x["path"])
result={"schema":"researchos.desktop15-binding-independent-static-audit.v1","checks":checks,"check_count":len(checks),"failed_count":sum(not x["passed"] for x in checks),"inputs":list(inputs.values()),"input_count":len(inputs),"target_imports":0,"native_Git_Go_SQL_HTTP_MODEL_calls":0,"canonical_source_writes":0,"AST_is_execution_proof":False,"future_protected6983_rehash_not_performed":True}
(O/"audit.json").write_bytes((json.dumps(result,ensure_ascii=False,indent=2)+"\n").encode())
print(json.dumps({"output":str(O),"checks":len(checks),"failed":result["failed_count"],"inputs":len(inputs)},ensure_ascii=False))
