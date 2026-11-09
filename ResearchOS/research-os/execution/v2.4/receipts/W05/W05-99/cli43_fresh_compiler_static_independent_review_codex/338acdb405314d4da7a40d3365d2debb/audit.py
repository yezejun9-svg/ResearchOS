from pathlib import Path
import json,hashlib,ast,datetime
R=Path("D:/作品集/ResearchOS/research-os")
P=R/"execution/v2.4/receipts/W05/W05-99"
N=P/"cli43_fresh_compiler_preparation_revision_codex/bb395255ecb14df6820b2e20631c9c39"
B=P/"cli43_fresh_compiler_preparation_codex/7bf10c8e8cc54412ba7bb89b53f5a622"
O=Path(__file__).parent
checks=[]; inputs={}
def ref(p):
 p=Path(p);raw=p.read_bytes();v={"path":str(p),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)};inputs[str(p)]=v;return v
def ck(name,ok,details=None):checks.append({"name":name,"passed":bool(ok),"details":details})
def verify(v,label):
 p=Path(v["path"]);p=p if p.is_absolute() else R/p
 a=ref(p);ck(label,a["sha256"]==v["sha256"] and a["bytes"]==v["bytes"],{"expected":v,"actual":a})
def read(p):ref(p);return json.loads(Path(p).read_bytes())
def walk(j,where):
 if isinstance(j,dict):
  if {"path","sha256","bytes"}<=j.keys() and isinstance(j["path"],str) and isinstance(j["sha256"],str):verify(j,where)
  else:
   for k,v in j.items():walk(v,where+"/"+k)
 elif isinstance(j,list):
  for i,v in enumerate(j):walk(v,where+"/"+str(i))
for folder,name,want in [(N,"new",25),(B,"old",50)]:
 m=read(folder/"manifest.complete.json");ck(name+".member_count",len(m["entries"])==want,len(m["entries"]))
 for i,e in enumerate(m["entries"]):verify(e,name+".member."+str(i))
for name,pin in [("handoff.json","de9a9ddf9b415c47a4b6b9298c11c2971efea31f23834047f61144aac6d8031e"),("manifest.complete.json","839546346329b3ecf16ce2be3f42cae50ae05067949738988134651f9a2a6b84")]:ck("root_pin."+name,ref(N/name)["sha256"]==pin)
h=read(N/"handoff.json");scope=read(N/"scope.proposed.json")
walk(h,"handoff");walk(scope,"scope")
for name in ["current43_runner.proposed.py","launch.proposed.py","authorization_gate.proposed.py"]:
 ast.parse((N/name).read_bytes(),filename=str(N/name));ck("AST_only."+name,True)
plan=read(N/"instrumentation-plan.json")
a=(N/"cli_sessions_test.instrumented.go.txt").read_bytes();orig=(R/plan["original_path"]).read_bytes();ref(R/plan["original_path"])
ck("instrumented_hash",hashlib.sha256(a).hexdigest()==plan["instrumented_sha256"])
for i,c in reversed(list(enumerate(plan["changes"]))):
 new=c["new"].encode();old=c["old"].encode();ck("inverse_unique."+str(i),a.count(new)==1,a.count(new));a=a.replace(new,old,1)
ck("inverse_whole_original_exact",a==orig and hashlib.sha256(orig).hexdigest()==plan["original_sha256"],{"original_bytes":len(orig),"changes":len(plan["changes"])})
catalog=read(B/"public-source-catalog.proposed.json")
ck("catalog_counts",len(catalog["files"])==597 and sum(x["path"].endswith(".go") for x in catalog["files"])==557)
for e in catalog["files"]:verify(e,"current_public_source."+e["path"])
ck("scope_preparation_not_authorized",scope["preparation_only"] is True and scope["execution_authorized"] is False)
for key in ["runtime_resources_ref","compiler_resources_ref","current43_authority_ref","controller_review_ref","expected_registration","registration_metadata_paths"]:ck("future_unbound."+key,scope[key] is None)
ck("two_exact_leaves",scope["ordered_cases"]==["real-existing-open-readonly","real-existing-self-send"])
ck("outbound_unknown",scope["limits"]["unobserved_client_outbound_hard_cap"] is None)
# Re-read every observed public input to establish this static audit's no-drift boundary.
initial=list(inputs.values())
for v in initial:verify(v,"after."+v["path"])
audit={"schema":"researchos.cli43-preparation-static-input-audit.v1","reviewer":"codex:/root/w05_merge_review","created_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"checks":checks,"check_count":len(checks),"failed_count":sum(not x["passed"] for x in checks),"inputs":list(inputs.values()),"input_count":len(inputs),"target_imports":0,"target_executions":0,"product_cases":0,"Git_invocations":0,"canonical_or_source_mutations":0,"old_product_native_claims_reused":False}
(O/"audit.json").write_bytes((json.dumps(audit,ensure_ascii=False,indent=2)+"\n").encode())
print(json.dumps({"output":str(O),"checks":len(checks),"failed":audit["failed_count"],"inputs":len(inputs)},ensure_ascii=False))
