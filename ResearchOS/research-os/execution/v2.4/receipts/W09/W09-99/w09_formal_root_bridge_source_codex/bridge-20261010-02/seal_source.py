import hashlib,json,os,sys,types
from pathlib import Path
N=Path(__file__).resolve().parent
R=Path(r"D:\作品集\ResearchOS\research-os")
B=R/"execution/v2.4/receipts/W09/W09-99"
OLD=N.parent/"bridge-20261010-01"
NF3=B/"full_w09_main_native_producer_source_codex/fullw09-20261010-03"
def sha(raw):return hashlib.sha256(raw).hexdigest()
def pin(p):
 p=Path(p);b=p.read_bytes();return {"path":str(p),"sha256":sha(b),"bytes":len(b)}
def write(path,obj,raw=False):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 with path.open("xb") as f:
  f.write(obj if raw else (json.dumps(obj,ensure_ascii=False,indent=2)+"\n").encode());f.flush();os.fsync(f.fileno())
 return pin(path)
def exact(ref):
 assert pin(ref["path"])==ref,ref["path"];return Path(ref["path"]).read_bytes()
refs=[{"path":str(OLD/"HDF.json"),"sha256":"a48c7f18f62f3ce4ccf707f54c53cafd4ac31f98f6e45f3356413d3a09f89679","bytes":3428},
 {"path":str(OLD/"MF.json"),"sha256":"26f5504a13790dbe290bf39660580cb0d183c0e2860be2eea4f20ed1b5b39f8e","bytes":10100},
 {"path":str(OLD/"w09_root_bridge.source.py"),"sha256":"7b11082d9938d1611fb74bca12945d188436501d5e905b97b0ee828939810a53","bytes":36616},
 {"path":str(OLD/"ROOT_CALL_CONTRACT.md"),"sha256":"d0a123eae6d34e5e84c782a9a5963ddc517135e3eda8d2a9a7a05f5f60501bc3","bytes":6920},
 {"path":str(NF3/"MF.json"),"sha256":"71f2c09424c3fa75153a173fa5208c3d91e510390c500826e5f258855cd0f4c3","bytes":4399},
 {"path":str(R/"internal/domain/retrieval_test.go"),"sha256":"1254f8c7524638cac6bee492fe7d4daf685722250779f86e36e97b0e7a9f1141","bytes":32352}]
for ref in refs:exact(ref)
nf3h=json.loads((NF3/"HDF.json").read_bytes())
refs.append(pin(NF3/"HDF.json"))
for key in ("calling_contract_ref","source_choice_ref","runtime_ref","overrides_ref","launcher_ref",
            "prepare_caller_ref","producer_caller_ref","compiler_blueprint_ref"):
 ref=nf3h[key];exact(ref);refs.append(ref)
bridge=types.ModuleType("bridge02_author_manifest_subject");bridge.__file__=str(N/"w09_root_bridge.source.py")
exec(compile((N/"w09_root_bridge.source.py").read_bytes(),bridge.__file__,"exec"),bridge.__dict__)
for relative,pair in bridge.TRUSTED.items():
 ref={"path":str(R/relative),"sha256":pair[0],"bytes":pair[1]};exact(ref);refs.append(ref)
refs += [pin(N/name) for name in ("w09_root_bridge.source.py","ROOT_CALL_CONTRACT.md","NF4_PREPARATION_PLAN.md","delta_controls.py")]
seen={}
for ref in refs:
 p=str(Path(ref["path"]));assert p not in seen or seen[p]["sha256"]==ref["sha256"];seen[p]=dict(ref,path=p)
refs=list(seen.values())
gr=next(r for r in refs if Path(r["path"]).name=="source_read_guard.py")
gm=types.ModuleType("bridge02_author_guard");gm.__file__=gr["path"];sys.modules[gm.__name__]=gm
exec(compile(exact(gr),gr["path"],"exec"),gm.__dict__)
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
copies=[]
try:
 guard.acquire(refs)
 for i,ref in enumerate(refs):
  copies.append({"original_ref":ref,"copy_ref":write(N/"inputs"/(str(i)+"-"+Path(ref["path"]).name),guard.get_buffer(ref["path"]),True)})
finally:
 closed=guard.close();write(N/"source-guard.closed.json",closed)
 assert closed["closed"] and closed["retained_handles_count"]==0 and not closed["errors"]
for ref in refs:exact(ref)
write(N/"source-inputs.json",{"references":refs,"copies":copies})
controls=json.loads((N/"delta-controls.json").read_bytes())
assert controls["subject"]==pin(N/"w09_root_bridge.source.py") and controls["count"]==18
hdf={"schema":"researchos.w09-formal-root-bridge-source-handoff.v2",
 "source_author":"codex:/root/attach_restore_independent_review","status":"SOURCE_PREPARED_PENDING_INDEPENDENT_REVIEW",
 "source_ref":pin(N/"w09_root_bridge.source.py"),"contract_ref":pin(N/"ROOT_CALL_CONTRACT.md"),
 "NF4_preparation_plan_ref":pin(N/"NF4_PREPARATION_PLAN.md"),"base_hdf_ref":refs[0],"base_mf_ref":refs[1],
 "inherited_base_contract_ref":refs[3],"exact_inverse_ref":pin(N/"exact-inverse.json"),
 "delta_controls_ref":pin(N/"delta-controls.json"),"source_guard_ref":pin(N/"source-guard.closed.json"),
 "source_inputs_ref":pin(N/"source-inputs.json"),"original1133_ref":pin(N/"original-1133.origin.json"),
 "actual_tool_io_ref":pin(N/"actual-tool-io.json"),
 "changes":["C19 conditional current-Source21 reuse through existing Main gates",
            "RUN_CURRENT_CM40 executes six registered routes after four actual current Native selectors",
            "Main-compatible Scope/owner command-key routes plus exact selector route_bindings"],
 "current_Main_fixture_ref":pin(R/"internal/domain/retrieval_test.go"),
 "current_required_policy":"RUN_CURRENT_CM40; old Source21 evidence remains historical",
 "NF4_implemented":False,"NF4_executed":False,"old_compiler_evidence_deleted_or_moved":False,
 "C_drive_scratch_created":False,"Main_or_Canon_written":False,
 "Main_modules_executed":False,"Native_Go_SQL_model_dispatcher_TP_calls":0,
 "finite_delta_controls":18,"old_controls_rerun":False,"all_input_guards_closed":True,
 "execution_grant":False,"formal_acceptance":False,"parent_acceptance":False,"STOP":True}
write(N/"HDF.json",hdf)
members=[pin(p) for p in sorted(N.rglob("*")) if p.is_file() and p.name not in ("MF.json","postseal-tool-io.json")]
write(N/"MF.json",{"schema":"researchos.source-manifest.v1","members":members,"member_count":len(members),
 "exclusions":["MF.json self","postseal-tool-io.json separately pinned"]})
print(json.dumps({"HDF":pin(N/"HDF.json"),"MF":pin(N/"MF.json"),"source":hdf["source_ref"],
 "contract":hdf["contract_ref"],"NF4_plan":hdf["NF4_preparation_plan_ref"],
 "members":len(members),"guarded_inputs":len(refs)},ensure_ascii=False))

