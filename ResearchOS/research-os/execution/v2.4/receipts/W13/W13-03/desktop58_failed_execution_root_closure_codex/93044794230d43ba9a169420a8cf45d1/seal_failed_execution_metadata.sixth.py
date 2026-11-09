import sys,json,hashlib,stat
from pathlib import Path
from collections import Counter
sys.dont_write_bytecode=True
ROOT=Path("D:/作品集/ResearchOS/research-os")
OUT=Path(__file__).parent
EXPECTED_OUT=ROOT/"execution/v2.4/receipts/W13/W13-03/desktop58_failed_execution_root_closure_codex/93044794230d43ba9a169420a8cf45d1"
assert OUT==EXPECTED_OUT and OUT.resolve()==OUT

def safe(p):
 p=Path(p);p=p if p.is_absolute() else ROOT/p
 assert p.is_relative_to(ROOT) and p.resolve()==p
 for x in (p,*p.parents):
  if x==ROOT or x.is_relative_to(ROOT):
   st=x.lstat();assert not stat.S_ISLNK(st.st_mode) and not(getattr(st,"st_file_attributes",0)&0x400)
 assert p.is_file()
 return p

def ref(p):
 p=safe(p);raw=p.read_bytes()
 return {"path":p.relative_to(ROOT).as_posix(),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def rawref(r):
 p=safe(r["path"]);raw=p.read_bytes();assert len(raw)==r["bytes"] and hashlib.sha256(raw).hexdigest()==r["sha256"];return raw
def doc(r):return json.loads(rawref(r))
def write(name,d):
 with(OUT/name).open("xb")as f:f.write((json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode("utf-8"))
 return ref(OUT/name)
def tree(p):
 assert p.is_dir() and p.resolve()==p and not(getattr(p.lstat(),"st_file_attributes",0)&0x400)
 return [ref(x)for x in sorted(p.rglob("*"))if x.is_file()]
payload=json.loads(safe(OUT/"original-tool-payload.json").read_bytes())
assert payload["actor"]=="codex:/root" and payload["namespace_rel"]==OUT.relative_to(ROOT).as_posix()
assert payload["scope_uid"]=="b4d53db07f1e4ab8b9c0b37e291a6da5"
assert payload["canonical_tuple"]==[337,165,617] and payload["registered_failure_count"]==617
canonical=[ref(safe(x["path"])) for x in payload["canonical_expected"]]
for x in payload["canonical_expected"]:rawref(x)
scope=doc(payload["scope_ref"]);binding=doc(payload["binding_ref"]);grant=doc(payload["grant_actual"]["grant_ref"])
assert grant["scope_ref"]==payload["scope_ref"] and grant["status"]=="ROOT_REGISTERED_EXECUTION_AUTHORIZED"
for k in("grant_closed_io_ref","registration_closed_io_ref","caller_source_ref","caller_source_review_ref"):rawref(payload[k])
E=Path(binding["new_output_root"]);L=Path(binding["new_wrapper_root"]);C=ROOT/payload["caller_out_rel"]
assert E==Path(scope["output_root"]) and L==Path(scope["outer_output_root"])
er=doc(payload["executor_result_ref"]);bi=doc(payload["builder_invocation_ref"]);lr=json.loads(safe(L/"result.json").read_bytes());ci=json.loads(safe(C/"root-launch.invocation.json").read_bytes())
assert ci["actual_launcher_native_exit"]==1 and ci["caller_error"]is None and ci["secondary"]==[]
terminal=payload["root_originals"][-1]["full_tool_result"]
assert terminal["exit_code"]==1 and "ACTUAL_PYTHON_EXIT=1" in terminal["output"]
assert er["actual_observed_HTTP_total"]==0 and er["actual_native_top_commands"]==3 and er["rows"]==[] and not er["source_acceptance"] and not lr["source_acceptance"]
br=bi["result"];assert br==er["last_child_result"] and br["actual_exit"]==3758097160 and not br["timed_out"]
dc=br["debug_capture"];cleanup=br["job_cleanup"]
assert dc["complete"]is False and dc["create_process_count"]==805 and dc["exit_process_count"]==805
assert cleanup["job_idle_confirmed"] and cleanup["primary_exit_confirmed"] and cleanup["handles_closed"] and cleanup["active_processes_last_observed"]==0 and cleanup["explicit_owned_handles_remaining"]==0 and cleanup["explicit_owned_handle_close_successes"]==8942
assert lr["inner_result"]["job_cleanup"]["job_idle_confirmed"] and lr["inner_result"]["job_cleanup"]["handles_closed"]
states=er["all_case_states"];values=list(states.values())if isinstance(states,dict)else states
counts=Counter(v.get("state",v.get("status","UNKNOWN"))if isinstance(v,dict)else str(v)for v in values)
assert len(values)==170 and counts=={"NOT_STARTED":170}
rejected=dc["rejected_load_facts"];assert len(rejected)==1 and rejected[0]["qualified_module"]is False and rejected[0]["expected_pin"]is None
assert rejected[0]["path_from_actual_file_handle"].lower().endswith("windows\\system32\\conhost.exe") and rejected[0]["before"]=={"sha256":"e449bce01f275cd08f3d4e64bb73b3b43ae845a0dbdb3e6131426e66537705e5","bytes":1003520}
closed=[]
for directory in(E,L,C,Path(binding["new_authorization_root"]),Path(binding["new_grant_preflight_root"])):closed+=tree(directory)
export=Path(scope["export_root"]);export_refs=tree(export)
export_ref=write("failed-export-current58.tree.diagnostic-only.json",{"schema":"researchos.failed-export-tree.diagnostic-only.v1","root":export.relative_to(ROOT).as_posix(),"files":export_refs,"qualification":False,"posthoc_resource_union":False})
origin=write("failure-origin-631.original.json",{"schema":"researchos.original-tool-failure.v1","failure_index":631,"actor":"codex:/root","kind":"DESKTOP_SIXTH_NATIVE_BUILD_FROZEN_RUNTIME_REJECTION","input_ref":ref(OUT/"original-tool-payload.json"),"root_originals":payload["root_originals"],"actual_outer_tool_exit":1,"actual_python_exit":1,"actual_launcher_native_exit":1,"actual_builder_native_exit":br["actual_exit"],"caller_error_original":ci["caller_error"],"caller_secondary_original":ci["secondary"],"executor_first_error_original":er["first_error"],"builder_error_original":br["error"],"rejected_actual_handle_diagnostic":rejected,"same_propagation_chain_counted_once":True,"counter_reset":False,"automatic_retry":False,"formal_increment":0})
pending=payload["pending_records"]
assert [x["failure_index"]for x in pending]==list(range(618,635))
for x in pending:
 if x["failure_index"]==631:assert x["origin_ref"]is None;x["origin_ref"]=origin
 assert x["origin_ref"]is not None;rawref(x["origin_ref"])
assert len(pending)==17
report=write("report.json",{"schema":"researchos.desktop58.failed-execution-root-closure.v1","actor":"codex:/root","decision":"FAILED_EXECUTION_CLOSED_REVIEW_PENDING","scope_uid":payload["scope_uid"],"scope_ref":payload["scope_ref"],"binding_ref":payload["binding_ref"],"grant_ref":payload["grant_actual"]["grant_ref"],"root_original_tool_payload_ref":ref(OUT/"original-tool-payload.json"),"original_caller_tool_outer_exit":1,"original_caller_python_exit":1,"caller_invocation_original":ci,"launcher_inner_exit":lr["actual_native_inner_exit"],"launcher_outer_native_exit_original":lr["actual_outer_native_exit"],"launcher_first_error":lr["first_error"],"launcher_job_cleanup":lr["inner_result"]["job_cleanup"],"executor_first_error":er["first_error"],"executor_secondary_errors":er["secondary_errors"],"builder_actual_native_exit":br["actual_exit"],"builder_error":br["error"],"builder_timed_out":br["timed_out"],"builder_pid":br["owned_child_pid"],"builder_creation_time_100ns":br["creation_time_100ns"],"builder_job_cleanup":cleanup,"builder_debug_capture_summary":{"complete":False,"create_process_count":805,"exit_process_count":805,"initial_breakpoint_count":dc["initial_breakpoint_count"],"rejected_load_diagnostic_facts":rejected,"qualified_module":False},"case_total":170,"case_state_counts":dict(counts),"qualified_case_count":0,"actual_case_rows":0,"actual_observed_HTTP_total":0,"actual_native_top_commands":3,"all_closed_original_refs":closed,"failed_export_tree_ref":export_ref,"canonical_refs_unchanged":canonical,"canonical_tuple":payload["canonical_tuple"],"observed_failure_count":634,"registered_failure_count":617,"pending_failure_origin_records":pending,"pending_count":17,"root_native_session_active":False,"parent_acceptance_increment":0,"formal_increment":0,"source_acceptance":False,"visible_installed_GUI_qualified":False,"same_scope_rerun_allowed":False})
resume=write("RESUME.failed-desktop-b4d.closed.json",{"schema":"researchos.v2.4.finite-resume.v1","project_id":"aede0678-7308-43dc-b9f2-cfe3d90cfdfb","head":"e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7","canonical_tuple":payload["canonical_tuple"],"canonical_refs":canonical,"observed_failure_count":634,"registered_failure_count":617,"pending_failure_origin_records":pending,"pending_count":17,"current_card":"W05-99","parent_tasks_accepted":6,"formal_cases_accepted":0,"goal_status":"active","failed_scope_uid":payload["scope_uid"],"failed_result_ref":report,"root_native_session_active":False,"old_scope_retry":False,"counter_reset":False,"next":["Independent exact failed-execution closure review","Close only this failed lease by reviewed Root CAS preserving all failure origins","Separate fresh conhost public resource Source/PE static admission; no posthoc qualification","Continue W09 v6 adoption and formal W09 profile; SDK v3/wholeGo cap v4 Source independent review"]})
entries=closed+[ref(OUT/"original-tool-payload.json"),ref(__file__),export_ref,origin,report,resume]
manifest=write("manifest.json",{"schema":"researchos.immutable-manifest.v1","entries":entries,"mutable_after_seal":False})
handoff=write("handoff.json",{"schema":"researchos.source-handoff.v1","actor":"codex:/root","decision":"FAILED_EXECUTION_CLOSED_REVIEW_PENDING","report_ref":report,"manifest_ref":manifest,"resume_ref":resume,"new_root_origin_refs":[origin],"pending_failure_origin_records":pending,"qualification":False,"parent_acceptance_increment":0,"formal_increment":0})
print(json.dumps({"report_ref":report,"manifest_ref":manifest,"handoff_ref":handoff,"resume_ref":resume,"new_root_origin_ref":origin,"closed_files":len(closed),"export_files":len(export_refs),"state_counts":dict(counts),"builder_exit":br["actual_exit"]},ensure_ascii=False))

