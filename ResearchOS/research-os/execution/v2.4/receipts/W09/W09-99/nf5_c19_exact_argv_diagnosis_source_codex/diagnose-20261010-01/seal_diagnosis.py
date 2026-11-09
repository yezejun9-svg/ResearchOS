import json,hashlib,os
from pathlib import Path
N=Path(__file__).resolve().parent
def pin(p):
 p=Path(p);b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def put(name,obj):
 with (N/name).open("xb") as f:
  f.write((json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode());f.flush();os.fsync(f.fileno())
 return pin(N/name)
d=json.loads((N/"diagnosis.json").read_bytes());refs=json.loads((N/"source-fact-pins.json").read_bytes())["references"]
for ref in refs:assert pin(ref["path"])==ref,ref["path"]
h={"schema":"researchos.nf5-c19-exact-argv-source-diagnosis-handoff.v1",
 "status":"SOURCE_CONTRACT_ORDER_MISMATCH_CONFIRMED","source_author":"codex:/root/attach_restore_independent_review",
 "diagnosis_ref":pin(N/"diagnosis.json"),"comparison_ref":pin(N/"comparison.json"),
 "verification_ref":pin(N/"verification.json"),"source_fact_pins_ref":pin(N/"source-fact-pins.json"),
 "actual_tool_io_ref":pin(N/"actual-tool-io.json"),"source_facts_verified":len(refs),
 "actual_run_id":d["run_id"],"actual_Native_exit":0,"NF5_stage_status":"FAILED_NO_AUTOMATIC_RETRY",
 "NF5_error":"EXACT_NATIVE_ARGV","original_closed_guards":5,"original_owned_job_exit":0,
 "Root_original1156_binding_ref":None,"Root_original1156_binding_status":"PENDING_ROOT_SEAL_NOT_FABRICATED",
 "observed_difference":"argv[5] test alternation order; selected_tests order also differs",
 "minimum_repair":"Future independently authorized Main producer case selection must follow CASES order; changing only NF5 expected argv does not satisfy Main closure.",
 "repair_applied":False,"Native_rerun":False,"Main_closure_executed":False,"old_controls_rerun":False,
 "Main_Canon_Scope_NF5_written":False,"Native_Go_model_dispatcher_TP_calls":0,
 "execution_grant":False,"runtime_qualification":False,"formal_acceptance":False,"parent_acceptance":False,"STOP":True}
put("HDF.json",h)
members=[pin(p) for p in sorted(N.iterdir()) if p.is_file() and p.name not in ("MF.json","postseal-tool-io.json")]
put("MF.json",{"schema":"researchos.source-manifest.v1","members":members,"member_count":len(members),
 "exclusions":["MF.json self","postseal-tool-io.json separately pinned"]})
for ref in members:assert pin(ref["path"])==ref
print(json.dumps({"HDF":pin(N/"HDF.json"),"MF":pin(N/"MF.json"),"diagnosis":h["diagnosis_ref"],
 "verification":h["verification_ref"],"members":len(members),"status":h["status"]},ensure_ascii=False))

