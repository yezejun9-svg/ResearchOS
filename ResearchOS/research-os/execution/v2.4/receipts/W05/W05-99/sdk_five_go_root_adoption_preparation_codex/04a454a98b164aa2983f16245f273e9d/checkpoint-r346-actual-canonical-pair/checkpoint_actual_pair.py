import sys
sys.dont_write_bytecode=True
import ctypes,hashlib,json,os,types,uuid
from ctypes import wintypes
from pathlib import Path
from datetime import datetime,timezone
R=Path("D:/作品集/ResearchOS/research-os");O=Path(__file__).resolve().parent;B=R/"execution/v2.4/receipts/W05/W05-99"
def pin(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def save(name,obj):
 p=O/name
 with p.open("xb") as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(p)
def source(p,h,n):
 b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==h and len(b)==n
 m=types.ModuleType("root_component_"+p.stem);m.__file__=str(p);exec(compile(b,str(p),"exec"),m.__dict__);return m
cp=R/"execution/v2.4/checkpoint.json";ow=R/"execution/v2.4/path_ownership.json"
old=[p.read_bytes() for p in (cp,ow)];expected=[pin(p) for p in (cp,ow)]
assert expected[0]["sha256"]=="724880d70d4dbc34676a6f67837d7d7e9cf53a4d3d130daefa16329f34904031"
assert expected[1]["sha256"]=="48c5641956b5f22bb48f7775e46d90494bd95944027f55070e430e207a506452"
c=json.loads(old[0]);a=json.loads(old[1]);assert c["revision"]==345 and len(c["failure_counters"])==702 and a["revision"]==168
others=[R/"execution/v2.4"/(n+".json") for n in ("step_state","commands")];other_raw=[p.read_bytes() for p in others]
guard_path=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
tx_path=B/"mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/canonical_transactions.py"
assert pin(tx_path)["sha256"]=="094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9" and pin(tx_path)["bytes"]==6877
gm=source(guard_path,"e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85",11404)
guard=gm.SourceReadGuard();guard.acquire([pin(guard_path),pin(tx_path),pin(Path(__file__).resolve())])
tm=types.ModuleType("root_actual_canonical_transaction");tm.__file__=str(tx_path);exec(compile(guard.get_buffer(tx_path),str(tx_path),"exec"),tm.__dict__)
k=ctypes.WinDLL("kernel32",use_last_error=True);create=k.CreateFileW;create.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD,wintypes.DWORD,ctypes.c_void_p];create.restype=ctypes.c_void_p
close=k.CloseHandle;close.argtypes=[ctypes.c_void_p];close.restype=wintypes.BOOL
controls=[];transaction_result=None
pending=[
 (703,O.parent/"checkpoint-r345-c5-review-and-c6-active/failure-origin.703.github-read.original.json",None,None,"one GitHub page read Internal Error among three successful sibling reads"),
 (704,B/"mu_sdk_caller_readiness_readonly_codex/453985a409ac462dbbfd55489b0b9596/failure-origin.704.original-tool-io.json",1,None,"read-only rg literal wildcard path unsupported on Windows"),
 (705,B/"mu_sdk_job_observer_revision_v4_codex/cbb82ea19cf84175baf61427251b983c/failure-origin.705.json",0,None,"read-only missing review template path; actual nonterminating Get-Content error despite outer0")]
assert pin(pending[1][1])["sha256"]=="8b4ce94c58f2b38a767df4e5dfeed2305dbefeece2888231a78328c41a336018"
assert pin(pending[2][1])["sha256"]=="ac982f8e0cbfc3aeeb308f6e06b9e6c2fa0f4ccd3af4b3378e780c1901342f5b"
try:
 wrong=[dict(x) for x in expected];wrong[0]["sha256"]="0"*64
 try:
  tm.update_pair(wrong,lambda x,y:(_ for _ in ()).throw(AssertionError("stale transform reached")),O,"activate")
 except RuntimeError as e:
  assert str(e)=="canonical expected bytes changed under exclusive ownership"
  controls.append({"control":"stale expected ref rejected before transform/write","observed_error":str(e),"expected_negative":True})
 else:raise AssertionError("stale expected ref accepted")
 assert [p.read_bytes() for p in (cp,ow)]==old
 def transform(checkpoint,ownership):
  assert checkpoint["revision"]==345 and len(checkpoint["failure_counters"])==702 and ownership["revision"]==168
  for path in (cp,ow):
   for access,label in [(0x80000000,"READ"),(0x40000000,"WRITE")]:
    ctypes.set_last_error(0);h=create(str(path),access,7,None,3,0x80,None);err=ctypes.get_last_error();success=h not in (None,ctypes.c_void_p(-1).value)
    if success:assert close(h)
    controls.append({"control":"mandatory sharing denies competing open","path":str(path),"access":label,"succeeded":success,"winerror":err,"expected_negative":True})
    assert not success and err==32
  keys={e.get("origin_key") for e in checkpoint["failure_counters"]}
  for ordinal,path,outer,py,detail in pending:
   ref=pin(path);key=hashlib.sha256((ref["sha256"]+"#"+str(ordinal)).encode()).hexdigest();assert key not in keys;keys.add(key)
   checkpoint["failure_counters"].append({"origin_key":key,"evidence_ref":ref,"original_payload":{"observed_ordinal":ordinal,"immutable_origin_ref":ref,"actual_outer_exit":outer,"actual_python_exit":py,"actual_native_exit":None,"provider_requests":0,"diagnostic":detail},"counted_once":True,"counter_reset":False,"automatic_retry":False})
  assert checkpoint["failure_counters"][:702]==c["failure_counters"] and len(checkpoint["failure_counters"])==705
  checkpoint["expected_previous_revision"]=345;checkpoint["revision"]=346;checkpoint["updated_at"]=datetime.now(timezone.utc).isoformat();checkpoint["updated_by"]="codex:/root"
  w=checkpoint["work_in_progress"];w.update({"mu_sdk_observer_v4_handoff_ref":pin(B/"mu_sdk_job_observer_revision_v4_codex/cbb82ea19cf84175baf61427251b983c/handoff.json"),"mu_sdk_source_authors_active":["codex:/root/live_resource_lookup: C6 final sealing"],"mu_sdk_source_readonly_reviewers_active":[],"mu_sdk_canonical_pair_actual_component_state":"ACTUAL_EXCLUSIVE_PAIR_STALE_REF_AND_COMPETING_READ_WRITE_DENIAL_OBSERVED_PENDING_INDEPENDENT_REVIEW","r346_registered_failure_count":705,"r346_observed_failure_count":705,"mu_sdk_live_execution_grant_issued":False,"mu_sdk_actual_external_provider_requests_current_trial":0,"mu_sdk_runtime_qualification":False})
  checkpoint["note"]="Real Root metadata update through unchanged pinned canonical transaction helper; actual Windows both-file exclusive handles reject stale refs and competing READ/WRITE opens before durable pair write. OW168 byte unchanged; SS/CM unchanged. New failures703-705 appended once; old702 preserved. O4 immutable Source proposed, C6 final sealing; Main frozen,22 local passes reused,6/22 parents0/42 formal; no SDK live grant or provider."
  return checkpoint,ownership
 transaction_result=tm.update_pair(expected,transform,O,"activate")
 after=[p.read_bytes() for p in (cp,ow)]
 assert json.loads(after[0])["revision"]==346 and len(json.loads(after[0])["failure_counters"])==705 and after[1]==old[1]
 assert [p.read_bytes() for p in others]==other_raw
 for path in (cp,ow):
  ctypes.set_last_error(0);h=create(str(path),0x80000000,7,None,3,0x80,None);err=ctypes.get_last_error();assert h not in (None,ctypes.c_void_p(-1).value);assert close(h)
  controls.append({"control":"read open restored after transaction","path":str(path),"succeeded":True,"winerror":err})
finally:
 cleanup=guard.close();assert cleanup["closed"] is True and cleanup["retained_handles_count"]==0 and cleanup["errors"]==[]
 save("source_guard.cleanup.actual.json",cleanup)
proof=save("canonical_pair.actual.json",{"schema":"researchos.canonical-pair-actual-private-component.v1","actor":"codex:/root","actual_parent_pid":os.getpid(),"canonical_pair":[str(cp),str(ow)],"transaction":transaction_result,"controls":controls,"old702_failures_preserved":True,"new_failure_count":705,"source_transaction_ref":pin(tx_path),"source_guard_ref":pin(guard_path),"ownership_bytes_unchanged":True,"other_canonical_unchanged":True,"provider_requests":0,"runtime_qualification":False,"formal_acceptance":False})
closed=save("checkpoint.closed.json",{"checkpoint_ref":pin(cp),"revision":346,"ownership_revision":168,"registered_failures":705,"observed_failures":705,"proof_ref":proof,"formal_acceptance":False})
resume=save("RESUME.r346.original.json",{"schema":"researchos.root-resume-sdk-controller-host-v2","project_id":c["project_id"],"repository_root":str(R),"head":c["head"],"checkpoint_ref":pin(cp),"checkpoint_revision":346,"ownership_revision":168,"failures":705,"current_card":"W05-99","accepted_parents":6,"formal_cases_current_accepted":0,"formal_cases_required":42,"local_top_level_tests":22,"external_provider_requests_current_trial":0,"execution_grant":False,"runtime_qualification":False,"controller_state":"C6_SOURCE_SEALING_O4_PROPOSED_INDEPENDENT_REVIEW_PENDING","canonical_component_proof":proof,"next_action":"Independent C6/O4 source review; real no-provider controller/caller lifecycle; actual isolated CLI bootstrap and trusted Host prepare; one300s qualification1+ordinary2 trial.","completion_asserted":False})
print(json.dumps({"closed_ref":closed,"proof_ref":proof,"resume_ref":resume,"checkpoint_ref":pin(cp),"controls":len(controls),"failures":705,"provider_requests":0}),flush=True)

