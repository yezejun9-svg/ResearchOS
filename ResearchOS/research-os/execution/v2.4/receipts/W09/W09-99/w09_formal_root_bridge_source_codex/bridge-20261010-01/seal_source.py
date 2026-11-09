"""Seal Source author artifacts only; never runs bridge stages or Main."""
import ast,hashlib,json,os,sys,types
from pathlib import Path
N=Path(__file__).resolve().parent
R=Path(r"D:\作品集\ResearchOS\research-os")
def sha(raw):return hashlib.sha256(raw).hexdigest()
def pin(path):
 p=Path(path);b=p.read_bytes();return {"path":str(p),"sha256":sha(b),"bytes":len(b)}
def write(path,value,raw=False):
 with Path(path).open("xb") as f:
  f.write(value if raw else (json.dumps(value,ensure_ascii=False,indent=2)+"\n").encode());f.flush();os.fsync(f.fileno())
 return pin(path)
def loadmodule(p,name):
 m=types.ModuleType(name);m.__file__=str(p);sys.modules[name]=m;exec(compile(p.read_bytes(),str(p),"exec"),m.__dict__);return m
bridge=loadmodule(N/"w09_root_bridge.source.py","bridge_author_pin_inventory_only")
refs=[{"path":str(R/path),"sha256":v[0],"bytes":v[1]} for path,v in bridge.TRUSTED.items()]
base=R/"execution/v2.4/receipts/W09/W09-99/w09_formal_consumer_readiness_readonly_codex/readiness-20261010-01"
for name,digest,size in [
 ("existing-Main-consumer-contract.json","1287416b88912497b641eca24f6558f98e5efa4250e1ed8ec5ba4339d4b0de25",23111),
 ("readiness.json","7ea20abbb03fe01b1b2035d1142b88cc6beedf643ffa9422f285c872ac0fffd4",20589),
 ("existing-Main-interface-excerpts.json","f733b543245285d7340d11f48e58c9bcd9d7917de3391f7698af82ff3b18dccf",103308)]:
 refs.append({"path":str(base/name),"sha256":digest,"bytes":size})
refs.extend(pin(N/name) for name in ("w09_root_bridge.source.py","source_controls.py","source_controls.corrected.py","source_controls.final_delta.py"))
for ref in refs:
 if pin(ref["path"])!=ref:raise ValueError("AUTHOR_INPUT_PIN_CHANGED:"+ref["path"])
guard_ref=next(r for r in refs if Path(r["path"]).name=="source_read_guard.py")
guardmod=loadmodule(Path(guard_ref["path"]),"bridge_author_read_guard")
guard=guardmod.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
copies=[]
try:
 guard.acquire(refs)
 (N/"inputs").mkdir()
 for index,ref in enumerate(refs):
  raw=guard.get_buffer(ref["path"])
  copyref=write(N/"inputs"/(str(index)+"-"+Path(ref["path"]).name),raw,True)
  copies.append({"original_ref":ref,"copy_ref":copyref})
finally:
 closed=guard.close()
 write(N/"author-source-guard.closed.json",closed)
 if not closed["closed"] or closed["retained_handles_count"] or closed["errors"]:raise ValueError("AUTHOR_GUARD_CLOSE")
write(N/"source-inputs.json",{"input_refs":refs,"copies":copies})
audit=Path(r"C:\Users\yqyyds\.codex\sessions\2026\10\09\rollout-2026-10-09T08-25-26-01a11e0c-eef6-7363-a5b1-da61d6ae7f4c.jsonl")
targets={"719b19":(1123,1,None),"5aac93":(1124,0,None),"782209":(1127,1,1),"47b00a":(1129,0,None),
         "c46acd":(None,0,0),"3cf036":(None,0,0)}
captures=[]
(N/"original-tool-captures").mkdir()
with audit.open("rb") as f:
 prefix=os.fstat(f.fileno()).st_size
 header=f.readline();hd=json.loads(header)
 if hd["payload"].get("agent_path")!="/root/attach_restore_independent_review":raise ValueError("AUTHOR_SESSION_MISMATCH")
 calls={};found=set()
 while f.tell()<prefix:
  offset=f.tell();raw=f.readline()
  if not raw or f.tell()>prefix:break
  value=json.loads(raw);p=value.get("payload",{})
  if not isinstance(p,dict):continue
  kind=p.get("type");cid=p.get("call_id")
  if kind in ("function_call","custom_tool_call") and cid:calls[cid]=(offset,raw)
  if kind not in ("function_call_output","custom_tool_call_output") or cid not in calls:continue
  for chunk,(ordinal,outer,python) in targets.items():
   if chunk in found or chunk.encode() not in raw:continue
   co,cr=calls[cid]
   out=write(N/"original-tool-captures"/(chunk+".jsonl"),header+cr+raw,True)
   captures.append({"chunk_id":chunk,"original_ordinal":ordinal,"original_capture_ref":out,
      "source_audit_path":str(audit),"source_session_id":hd["payload"]["id"],
      "source_prefix_size_observed":prefix,"source_line_offsets":[0,co,offset],
      "source_line_bytes":[len(header),len(cr),len(raw)],"original_line_sha256":[sha(header),sha(cr),sha(raw)],
      "actual_outer_exit":outer,"actual_Python_exit":python,"actual_native_exit":None,"actual_dispatcher_exit":None,
      "actual_Go_exit":None,"actual_SQL_exit":None,"component_exit_without_marker":None})
   found.add(chunk)
 if found!=set(targets):raise ValueError("MISSING_ORIGINAL_TOOL_CAPTURE:"+str(set(targets)-found))
write(N/"original-tool-captures.json",{"schema":"researchos.w09-bridge-author-original-captures.v1",
 "captures":captures,"mechanical_original_ordinals":[1123,1124,1127,1129],"counter_reset":False})
for ref in refs:
 if pin(ref["path"])!=ref:raise ValueError("AUTHOR_SOURCE_DRIFT")
final=json.loads((N/"final-delta-controls.json").read_bytes())
if final["subject"]!=pin(N/"w09_root_bridge.source.py"):raise ValueError("FINAL_SOURCE_CONTROL_PIN")
source={
 "schema":"researchos.w09-formal-root-bridge-source-handoff.v1","source_author":"codex:/root/attach_restore_independent_review",
 "status":"SOURCE_IMPLEMENTED_PENDING_INDEPENDENT_SOURCE_REVIEW","source_ref":pin(N/"w09_root_bridge.source.py"),
 "call_contract_ref":pin(N/"ROOT_CALL_CONTRACT.md"),"source_inputs_ref":pin(N/"source-inputs.json"),
 "finite_controls_ref":pin(N/"source-controls.json"),"final_delta_controls_ref":pin(N/"final-delta-controls.json"),
 "original_tool_captures_ref":pin(N/"original-tool-captures.json"),"source_guard_close_ref":pin(N/"author-source-guard.closed.json"),
 "stages":list(bridge.STAGES),"Main_modules_executed":False,"runtime_stages_executed":[],
 "Native_Go_SQL_model_dispatcher_TP_verify_owner_derive_calls":0,
 "canonical_Main_product_paths_written":[],"execution_grant":False,"formal_acceptance":False,"parent_acceptance":False,
 "Root_only_next":"Independent Source review before any runtime stage. G02/A06 qualifications must be genuine successful closed Native evidence; no producer retry in this bridge.",
 "publication_boundary":"Root must publish reviewed exact roles/original/capture/index bytes before publish-registration. Bridge never silently overwrites these fixed files.",
 "controls_limit":"21 pure/static author controls passed at an earlier source pin; six final-delta-only controls at final pin. No runtime stage or Main verifier was exercised.",
 "mechanical_failures":[1123,1124,1127,1129]}
write(N/"HDF.json",source)
members=[pin(p) for p in sorted(N.rglob("*")) if p.is_file() and p.name not in {"MF.json","postseal-tool-io.json"}]
write(N/"MF.json",{"schema":"researchos.source-manifest.v1","members":members,"self_excluded":True,
                  "postseal_tool_io_separately_pinned":True})
print(json.dumps({"HDF":pin(N/"HDF.json"),"MF":pin(N/"MF.json"),"source_ref":source["source_ref"],
                  "members":len(members),"author_inputs":len(refs),"guard_closed":closed["closed"]},ensure_ascii=False))

