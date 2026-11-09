import json,hashlib,os
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");O=Path(__file__).parent
N=R/("execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r339-"+O.name)
checks=[];seen={}
def ck(n,v):checks.append({"name":n,"pass":bool(v)})
def path(v):
 v=Path(v);return v if v.is_absolute() else R/v
def read(p):
 p=path(p);raw=p.read_bytes();seen[str(p)]={"path":str(p),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)};return raw
def jd(p):return json.loads(read(p))
def pin(r):
 raw=read(r["path"]);ck("pin:"+r["path"],len(raw)==r["bytes"] and hashlib.sha256(raw).hexdigest()==r["sha256"])
def scan(x):
 if isinstance(x,dict):
  if set(x)=={"path","sha256","bytes"}:pin(x)
  else:
   for v in x.values():scan(v)
 elif isinstance(x,list):
  for v in x:scan(v)
q=jd(N/"root-construction.parameters.desktop58.json");ri=jd(N/"root-inputs.desktop58.pre-review.json");a=jd(N/"root-construction.audit.json")
ck("exact sealed q",seen[str(N/"root-construction.parameters.desktop58.json")]["sha256"]=="83b0581d664cda925b3aa2f6106c8cd6abcda7c75d8a844796fa47a914264767")
ck("exact sealed Root inputs",seen[str(N/"root-inputs.desktop58.pre-review.json")]["sha256"]=="95fe8b69e8fc6aafe744ca5167d51316c36e8f292b669994f3c9d39fb7328855")
scan(q);scan(ri)
ck("literal Root transition",q["before"]==ri["before"]==[338,166,635] and q["after"]==ri["after"]==[339,167,645])
ck("fixed budgets",[q[k] for k in ("inner_seconds","outer_seconds","builder_seconds","controller_evidence_reserve_seconds","launcher_evidence_reserve_seconds")]==[7200,7500,1800,60,60])
ck("639/22138/1303/23874 source capture counts",[a[k] for k in ("source_files","compiler_files","runtime_files","resource_union_files")]==[639,22138,1303,23874])
delta=jd(q["conhost_resource_delta_ref"]["path"]);rt=jd(ri["runtime_resources_ref"]["path"]);rm={r["path"]:r for r in rt["files"]}
for x in delta["additions_to_catalog_and_runtime"]:ck("conhost resource declared:"+x["path"],rm.get(x["path"])==x)
ck("only conhost image added",len(q["static_image_refs"])==17 and delta["static_images_add"]==q["static_image_refs"][-1:])
roots=[v for k,v in q["allocation"].items() if k.startswith("new_")]
ck("all5 fresh leaves absent",len(roots)==5 and all(not os.path.lexists(path(x)) for x in roots))
c=jd(ri["canonical_before_ref"]["path"])
for x in c["entries"]:ck("actual canonical equal:"+x["canonical_path"],read(x["canonical_path"])==read(x["ref"]["path"]))
cp=jd(R/"execution/v2.4/checkpoint.json");ow=jd(R/"execution/v2.4/path_ownership.json")
ck("actual tuple",[cp["revision"],ow["revision"],len(cp["failure_counters"])]==[338,166,635])
lease=ow["card_path_bindings"]["W13-03"]["subtasks"]["desktop58_finite_validation"]
ck("b4d lease closed no grant",lease["run_uuid"]=="b4d53db07f1e4ab8b9c0b37e291a6da5" and lease["state"]=="FAILED_EXECUTION_CLOSED_QUALIFICATION_WITHHELD" and lease["execution_grant"] is False)
cut=jd(ri["origin_cut_ref"]["path"]);ck("fixed10 cut",len(cut["origins"])==10 and len(q["pending_origin_refs"])==10 and cut["before"]==q["before"] and cut["after"]==q["after"])
for row,orig in zip(cut["origins"],q["pending_origin_refs"]):ck("opaque origin:"+orig["sha256"],row["evidence_ref"]==orig and row["original_payload"]==jd(orig["path"]))
out={"schema":"researchos.literal-pre-scope-readonly-check.v1","reviewer":"codex:/root/w05_merge_review","checks":checks,"failed":[c for c in checks if not c["pass"]],"input_refs":list(seen.values()),"final_scope_review":False,"grant":False,"candidate_executed":False}
with (O/"literal-precheck.json").open("xb") as f:f.write((json.dumps(out,ensure_ascii=False,indent=2)+"\n").encode())
print(json.dumps({"checks":len(checks),"failed":out["failed"],"final_scope_review":False},ensure_ascii=False))

