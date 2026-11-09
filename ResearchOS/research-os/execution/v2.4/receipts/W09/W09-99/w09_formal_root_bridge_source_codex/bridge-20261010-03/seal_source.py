import hashlib,json,os,sys,types
from pathlib import Path
N=Path(__file__).resolve().parent
R=Path(r"D:\作品集\ResearchOS\research-os")
def sha(b):return hashlib.sha256(b).hexdigest()
def pin(p):
 p=Path(p);b=p.read_bytes();return {"path":str(p),"sha256":sha(b),"bytes":len(b)}
def put(name,obj):
 p=N/name
 with p.open("xb") as f:
  f.write((json.dumps(obj,ensure_ascii=False,indent=2)+"\n").encode());f.flush();os.fsync(f.fileno())
 return pin(p)
def exact(ref):
 assert pin(ref["path"])==ref,ref["path"]
 return Path(ref["path"]).read_bytes()
inputs=json.loads((N/"source-inputs.json").read_bytes())
for ref in inputs["references"]:exact(ref)
c=json.loads((N/"delta-controls.json").read_bytes())
assert c["count"]==c["passed"]==22 and c["failed"]==0
assert c["subject"]==pin(N/"w09_root_bridge.source.py")
assert c["launcher"]==pin(N/"consumer_launch.source.py")
guard0=json.loads((N/"source-guard.closed.json").read_bytes())
assert guard0["closed"] and guard0["retained_handles_count"]==0 and not guard0["errors"]
o=json.loads((N/"original-1145.origin.json").read_bytes())
assert o["original_ordinal"]==1145 and o["actual_outer_exit"]==1 and o["actual_python_exit"] is None
binding=json.loads(exact(o["actual_host_binding_ref"]))
raw=exact(binding["original_capture_ref"])
with Path(binding["source_audit_path"]).open("rb") as f:
 lines=[]
 for offset,size,digest in zip(binding["source_line_offsets"],binding["source_line_bytes"],binding["source_line_sha256"]):
  f.seek(offset);b=f.read(size);assert sha(b)==digest;lines.append(b)
 assert b"5f53f9" in lines[2] and b"bridge-20261010-02" in lines[1]
 assert raw==b"".join(lines)
assert json.loads(lines[0])["payload"]["agent_path"]=="/root/attach_restore_independent_review"
subject=types.ModuleType("bridge03_seal_subject")
subject.__file__=str(N/"w09_root_bridge.source.py")
exec(compile(exact(c["subject"]),subject.__file__,"exec"),subject.__dict__)
refs=inputs["references"]+[pin(p) for p in sorted(N.rglob("*")) if p.is_file()]
for rel,pair in subject.TRUSTED.items():
 ref={"path":str(R/rel),"sha256":pair[0],"bytes":pair[1]};exact(ref);refs.append(ref)
refs += c["actual_resource_readonly_refs"]
unique={}
for ref in refs:
 key=str(Path(ref["path"]))
 assert key not in unique or unique[key]==ref
 unique[key]=ref
refs=list(unique.values())
gr={"path":str(R/subject.GUARD),"sha256":subject.TRUSTED[subject.GUARD][0],"bytes":subject.TRUSTED[subject.GUARD][1]}
gm=types.ModuleType("bridge03_seal_guard");gm.__file__=gr["path"];sys.modules[gm.__name__]=gm
exec(compile(exact(gr),gr["path"],"exec"),gm.__dict__)
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
try:
 guard.acquire(refs)
 for ref in refs:
  b=guard.get_buffer(ref["path"]);assert sha(b)==ref["sha256"] and len(b)==ref["bytes"]
finally:
 closed=guard.close();put("seal-source-guard.closed.json",closed)
 assert closed["closed"] and closed["retained_handles_count"]==0 and not closed["errors"]
for ref in refs:exact(ref)
put("seal-source-pins.json",{"references":refs,"count":len(refs)})
h={
 "schema":"researchos.w09-formal-root-bridge-source-handoff.v3",
 "source_author":"codex:/root/attach_restore_independent_review",
 "source_author_backend":"/root/attach_restore_independent_review",
 "actual_source_thread":binding["actual_thread"],"actual_parent_thread":binding["actual_parent_thread"],
 "status":"SOURCE_PREPARED_PENDING_INDEPENDENT_REVIEW","generation":"bridge-20261010-03",
 "source_ref":c["subject"],"consumer_launcher_ref":c["launcher"],
 "contract_ref":pin(N/"ROOT_CALL_CONTRACT.md"),
 "base_hdf_ref":inputs["references"][0],"base_mf_ref":inputs["references"][1],
 "task98_review_hdf_ref":pin(N.parent.parent/"w09_formal_root_bridge_independent_review_codex/review-bridge-20261010-02/HDF.json"),
 "task98_review_mf_ref":pin(N.parent.parent/"w09_formal_root_bridge_independent_review_codex/review-bridge-20261010-02/MF.json"),
 "exact_inverse_ref":pin(N/"exact-inverse.json"),"delta_controls_ref":pin(N/"delta-controls.json"),
 "source_inputs_ref":pin(N/"source-inputs.json"),"source_guard_ref":pin(N/"source-guard.closed.json"),
 "seal_source_guard_ref":pin(N/"seal-source-guard.closed.json"),"seal_source_pins_ref":pin(N/"seal-source-pins.json"),
 "original1145_ref":pin(N/"original-1145.origin.json"),"actual_tool_io_ref":pin(N/"actual-tool-io.json"),
 "preseal_tool_io_ref":pin(N/"preseal-tool-io.json"),
 "changes":["BRIDGE-ROLE-001 fixed backend SOURCE_AUTHOR plus canonical metadata","BRIDGE-TEMP-002 fixed real physical C TEMP for every Main validation process","independently pinned same-process consumer launcher validates environment before unchanged dispatcher"],
 "fixed_bridge_TEMP_TMP":str(subject.PUBLIC_TEMP),
 "resource_readonly_refs":c["actual_resource_readonly_refs"],
 "finite_delta_controls":22,"old_18_and_24_controls_rerun":False,
 "delta_control_limits":{"scope_expression_only":True,"Main_peer_predicate_only":True,"launcher_runpy_spy_only":True,"process_cache_stub_only":True},
 "actual_bridge_stages":0,"actual_dispatcher_calls":0,"actual_Main_module_calls":0,
 "actual_Native_Go_SQL_model_TP_calls":0,"Main_Canon_Scope_written":False,
 "Native_roots_moved":False,"C_drive_files_written":False,
 "NF5_qualification":"PENDING_INDEPENDENT_REVIEW_NOT_CREATED_HERE",
 "Root_Scope_execution_grant":False,"all_source_guards_closed_zero":True,
 "execution_grant":False,"formal_acceptance":False,"parent_acceptance":False,"STOP":True}
put("HDF.json",h)
members=[pin(p) for p in sorted(N.rglob("*")) if p.is_file() and p.name not in ("MF.json","postseal-tool-io.json")]
put("MF.json",{"schema":"researchos.source-manifest.v1","members":members,"member_count":len(members),
 "exclusions":["MF.json self","postseal-tool-io.json separately pinned"]})
for ref in members:exact(ref)
print(json.dumps({"status":h["status"],"HDF":pin(N/"HDF.json"),"MF":pin(N/"MF.json"),
 "source":h["source_ref"],"launcher":h["consumer_launcher_ref"],"contract":h["contract_ref"],
 "original1145":h["original1145_ref"],"manifest_members":len(members),"seal_guarded_inputs":len(refs)},ensure_ascii=False))

