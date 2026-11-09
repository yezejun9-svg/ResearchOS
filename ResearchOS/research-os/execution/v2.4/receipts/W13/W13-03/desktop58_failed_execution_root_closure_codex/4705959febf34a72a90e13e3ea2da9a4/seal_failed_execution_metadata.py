import sys, json, hashlib, stat
from pathlib import Path
from collections import Counter
sys.dont_write_bytecode = True
ROOT = Path(r"D:/作品集/ResearchOS/research-os")
OUT = ROOT / "execution/v2.4/receipts/W13/W13-03/desktop58_failed_execution_root_closure_codex/4705959febf34a72a90e13e3ea2da9a4"
UID = "72ff32d0d24a42c4a8effd849d54f882"
def safe(p):
    p = Path(p)
    if not p.is_absolute(): p = ROOT / p
    p.relative_to(ROOT)
    for x in [p] + list(p.parents):
        if x == ROOT.parent: break
        st = x.lstat()
        if stat.S_ISLNK(st.st_mode) or getattr(st, "st_file_attributes", 0) & 0x400:
            raise RuntimeError("reparse boundary rejected: " + str(x))
    if not p.is_file(): raise RuntimeError("not regular file: " + str(p))
    return p
def ref(p):
    p=safe(p); b=p.read_bytes()
    return {"path":p.relative_to(ROOT).as_posix(),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def verify(r):
    got=ref(r["path"])
    if got["sha256"] != r["sha256"] or got["bytes"] != r["bytes"]: raise RuntimeError("pin mismatch: "+r["path"])
    return got
def read(p): return json.loads(safe(p).read_bytes())
def write(name, value):
    p=OUT/name
    with p.open("xb") as f: f.write((json.dumps(value,ensure_ascii=False,indent=2)+"\n").encode("utf-8"))
    return ref(p)
payload=read(OUT/"original-tool-payload.json")
canonical=[verify(r) for r in payload["canonical_expected"]]
E=ROOT/"execution/v2.4/receipts/W13/W13-03/desktop58_finite_executor_codex"/UID
L=ROOT/"execution/v2.4/receipts/W13/W13-03/desktop58_finite_launcher_codex"/UID
C=ROOT/"execution/v2.4/receipts/W13/W13-03/desktop58_root_terminal_closure_codex/7db4b93bdea5496b98e9b3a41aed1762"
verify({"path":str(E/"result.json"),"sha256":"dad4297d05a46b33d59d1c859077e491b3a0a4efd2281b50d9597311cf462ce8","bytes":8387290})
verify({"path":str(E/"build-current58.invocation.json"),"sha256":"c8914f095d0b29bfccebf898da89f58ef9e718e4d0aa1008177ebd291346b764","bytes":8359619})
er=read(E/"result.json"); bi=read(E/"build-current58.invocation.json"); lr=read(L/"result.json"); ci=read(C/"root-launch.invocation.json")
assert er["actual_observed_HTTP_total"] == 0 and er["actual_native_top_commands"] == 3 and not er["rows"]
assert not er["source_acceptance"] and not lr["source_acceptance"]
br=bi["result"]; assert br["actual_exit"] == 3758097160
states=er["all_case_states"]; state_values=list(states.values()) if isinstance(states,dict) else states
counts=Counter(v.get("state",v.get("status","UNKNOWN")) if isinstance(v,dict) else str(v) for v in state_values)
assert len(state_values)==170
rejected=[]
dc=br.get("debug_capture",{})
def find_rejections(v):
    if isinstance(v,dict):
        if "rejection_reason" in v or "qualified_module" in v:
            if v.get("qualified_module") is False or "rejection_reason" in v:
                rejected.append({k:v.get(k) for k in ("event_code","pid","process_id","generation","creation_time_100ns","canonical_path","path","image_path","sha256","bytes","expected_pin","rejection_reason","qualified_module","diagnostic_only") if k in v})
        for k,w in v.items():
            if k not in ("events","module_events","qualified_modules","processes","captured_modules","module_facts"): find_rejections(w)
    elif isinstance(v,list) and len(v)<=64:
        for w in v: find_rejections(w)
find_rejections(dc)
closed_originals=[]
for directory in [E,L,C]:
    for p in sorted(directory.rglob("*")):
        if p.is_file(): closed_originals.append(ref(p))
export=ROOT/(".local/desktop58-export-"+UID)
export_refs=[]
if export.is_dir():
    for p in sorted(export.rglob("*")):
        if p.is_file(): export_refs.append(ref(p))
export_ref=write("failed-export-current58.tree.diagnostic-only.json",{
    "schema":"researchos.failed-export-tree.diagnostic-only.v1",
    "root":export.relative_to(ROOT).as_posix(),"exists":export.is_dir(),"files":export_refs,
    "qualification":False,"source_acceptance":False,"posthoc_resource_union":False})
pending=[verify(r) for r in payload["prior_queued_origins"]]+[verify(r) for r in payload["external_pending_origins"]]
new_origins=[]
for o in payload["origins"]:
    toolref=write("origin-"+str(o["index"])+".original-observations.json",o)
    origin=write("failure-origin-"+str(o["index"])+".json",{
        "schema":"researchos.original-tool-failure.v1","failure_index":o["index"],"actor":payload["actor"],
        "kind":o["kind"],"original_observations_ref":toolref,"fact":o["fact"],
        "automatic_retry":False,"counter_reset":False,"same_propagation_chain_counted_once":True,
        "is_native_product_failure":o["index"]==595})
    pending.append(origin); new_origins.append(origin)
report=write("report.json",{
    "schema":"researchos.desktop58.failed-execution-root-closure.v1","actor":payload["actor"],
    "decision":"FAILED_EXECUTION_CLOSED_REVIEW_PENDING","scope_uid":UID,
    "original_caller_tool_outer_exit":1,"original_caller_python_exit":1,
    "caller_invocation_original":ci,"launcher_inner_exit":lr.get("actual_native_inner_exit"),
    "launcher_outer_native_exit_original":lr.get("actual_outer_native_exit"),
    "launcher_first_error":lr.get("first_error"),"launcher_job_cleanup":lr.get("inner_result",{}).get("job_cleanup"),
    "executor_first_error":er.get("first_error"),"executor_secondary_errors":er.get("secondary_errors"),
    "builder_actual_native_exit":br["actual_exit"],"builder_error":br.get("error"),
    "builder_timed_out":br.get("timed_out"),"builder_pid":br.get("owned_child_pid"),
    "builder_creation_time_100ns":br.get("creation_time_100ns"),"builder_job_cleanup":br.get("job_cleanup"),
    "builder_debug_capture_summary":{
        "keys":list(dc) if isinstance(dc,dict) else None,
        "bounded_scalar_fields":{k:v for k,v in dc.items() if isinstance(v,(str,int,float,bool,type(None))) and len(str(v))<4096} if isinstance(dc,dict) else {},
        "rejected_load_diagnostic_facts":rejected,
        "qualification":False},
    "case_total":len(state_values),"case_state_counts":dict(counts),
    "qualified_case_count":0,"actual_case_rows":len(er["rows"]),
    "actual_observed_HTTP_total":er["actual_observed_HTTP_total"],
    "actual_native_top_commands":er["actual_native_top_commands"],
    "all_closed_original_refs":closed_originals,"failed_export_tree_ref":export_ref,
    "canonical_refs_unchanged":canonical,"canonical_tuple":[335,163,580],
    "observed_failure_count":599,"registered_failure_count":580,"pending_failure_origin_refs":pending,
    "pending_count":len(pending),"root_native_session_active":False,
    "parent_acceptance_increment":0,"formal_increment":0,"source_acceptance":False,
    "visible_installed_GUI_qualified":False,"same_scope_rerun_allowed":False,
    "next":"Independent failure-closure review; fresh static resource capture and separately reviewed new scope before native rerun",
    "metadata_tool_stdout_must_remain_bounded":True})
assert len(pending)==19
resume=write("RESUME.failed-desktop72ff.closed.json",{
    "schema":"researchos.v2.4.finite-resume.v1","project_id":"aede0678-7308-43dc-b9f2-cfe3d90cfdfb",
    "head":"e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7","canonical_tuple":[335,163,580],
    "canonical_refs":canonical,"observed_failure_count":599,"registered_failure_count":580,
    "pending_failure_origin_refs":pending,"pending_count":19,"current_card":"W05-99",
    "parent_tasks_accepted":6,"formal_cases_accepted":0,"goal_status":"active",
    "failed_scope_uid":UID,"failed_result_ref":report,"root_native_session_active":False,
    "old_scope_retry":False,"counter_reset":False,
    "next":["Review failed native closure","Fresh capture adding statically verified wldp dependency","Reconcile pending originals by canonical CAS without reinterpreting statuses","Continue W09v6 Source and whole-Go configuration Source adoption","Prepare default cap=null LIVE only after actual effective budget review"]})
entries=closed_originals+[ref(OUT/"original-tool-payload.json"),ref(__file__),export_ref,report,resume]
entries += [ref(p) for p in sorted(OUT.glob("failure-origin-*.json"))]+[ref(p) for p in sorted(OUT.glob("origin-*.original-observations.json"))]
manifest=write("manifest.json",{"schema":"researchos.immutable-manifest.v1","entries":entries,"mutable_after_seal":False})
handoff=write("handoff.json",{"schema":"researchos.source-handoff.v1","actor":payload["actor"],
    "decision":"FAILED_EXECUTION_CLOSED_REVIEW_PENDING","report_ref":report,"manifest_ref":manifest,
    "resume_ref":resume,"new_root_origin_refs":new_origins,"pending_failure_origin_refs":pending,
    "qualification":False,"parent_acceptance_increment":0,"formal_increment":0})
print(json.dumps({"report_ref":report,"manifest_ref":manifest,"handoff_ref":handoff,
                 "resume_ref":resume,"new_root_origin_refs":new_origins,"pending_origin_refs":pending,
                 "closed_files":len(closed_originals),"export_files":len(export_refs),
                 "state_counts":dict(counts),"builder_exit":br["actual_exit"]},ensure_ascii=False))

