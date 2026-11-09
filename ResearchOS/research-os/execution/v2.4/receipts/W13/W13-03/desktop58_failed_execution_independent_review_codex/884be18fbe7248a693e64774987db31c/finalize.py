import json,hashlib,os,stat
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");O=Path(__file__).parent
N=R/"execution/v2.4/receipts/W13/W13-03/desktop58_failed_execution_root_closure_codex/93044794230d43ba9a169420a8cf45d1"
checks=[];readrefs=[]
def p(v):
 v=Path(v);return v if v.is_absolute() else R/v
def pin(v):
 v=p(v);b=v.read_bytes();return {"path":v.relative_to(R).as_posix(),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def jd(v):return json.loads(p(v).read_bytes())
def ck(k,v,d=None):checks.append({"name":k,"pass":bool(v),"detail":d})
def vr(r):
 f=pin(r["path"]);ck("pin:"+r["path"],f["sha256"]==r["sha256"] and f["bytes"]==r["bytes"]);readrefs.append(r);return jd(r["path"]) if str(r["path"]).endswith(".json") else None
def refs(x):
 if isinstance(x,dict):
  if {"path","sha256","bytes"}<=set(x):yield x
  else:
   for v in x.values():yield from refs(v)
 elif isinstance(x,list):
  for v in x:yield from refs(v)
def put(n,d):
 with (O/n).open("xb") as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(O/n)
r=jd(N/"report.json");s=jd(r["scope_ref"]["path"]);b=jd(r["binding_ref"]["path"]);g=jd(r["grant_ref"]["path"])
E=p(s["output_root"])
v1=jd(E/"initial.vector.json");v2=jd(E/"export-blobs-native-after.vector.json")
ck("corrected vector predicate: unchanged members with explicit revision1->2",v1["expected_members"]==v2["expected_members"] and v1["observed_members"]==v2["observed_members"] and v1["revision"]==1 and v2["revision"]==2 and v1["drift"]==v2["drift"]==[])
l2=jd(E/"ledger-add-002.json");ck("revision2 empty add permitted by actual ledger",l2["added"]==[] and l2["full_members"]==v1["expected_members"])
closed_actual=[]
for d in [p(s["output_root"]),p(s["outer_output_root"]),R/"execution/v2.4/receipts/W13/W13-03/desktop58_root_terminal_closure_codex/d8a016ddc71e440fb386a11957c098ea",p(b["new_authorization_root"]),p(b["new_grant_preflight_root"])]:
 stack=[d]
 while stack:
  parent=stack.pop()
  with os.scandir(parent) as it:entries=list(it)
  for e in entries:
   st=e.stat(follow_symlinks=False);f=Path(e.path)
   ck("closed member no reparse:"+str(f),not(stat.S_ISLNK(st.st_mode) or getattr(st,"st_file_attributes",0)&1024))
   if stat.S_ISDIR(st.st_mode):stack.append(f)
   elif stat.S_ISREG(st.st_mode):closed_actual.append(f.relative_to(R).as_posix())
ck("closed inventory actual exact108",sorted(closed_actual)==sorted(x["path"] for x in r["all_closed_original_refs"]))
ann=jd(N/"tool-observations.failed-closure.closed.original.json")
ck("sealer observed original failed and newclosed",len(ann["records"])==3 and ann["actual_failed_sealer_once_index"]==635 and ann["actual_closed_sealer_outer_exit"]==ann["actual_closed_sealer_python_exit"]==0 and ann["actual_stage_native_exit"] is None and ann["canonical_writes"]==ann["product_execution_increment"]==0)
ck("v2 terminal tool0",ann["records"][-1]["full_tool_result"].get("exit_code")==0)
src=vr(b["source_inputs_ref"]);sr=list(refs(src))
for x in sr:vr(x)
ck("639 actual current source pins",len(sr)==639)
# Live canonical compared bytewise to original grant copies at final audit time.
for x in g["canonical_copies"]:
 ck("current canonical copy exact:"+x["canonical_path"],p(x["canonical_path"]).read_bytes()==p(x["ref"]["path"]).read_bytes())
for d in [p(b["new_authorization_root"]),p(b["new_grant_preflight_root"])]:
 for name in ("admission","grant-final"):
  status=p(d/(name+".status.stdout.raw")).read_bytes()
  ck("frozen status raw:"+str(d)+name,hashlib.sha256(status).hexdigest()==b["main_git"]["status_sha256"] and len(status)==894)
  ck("frozen index empty:"+str(d)+name,len(p(d/(name+".index.stdout.raw")).read_bytes())==0)
ck("no acceptance increments",r["formal_increment"]==r["parent_acceptance_increment"]==0 and r["source_acceptance"] is False and r["same_scope_rerun_allowed"] is False)
a=jd(O/"audit.json");sp=jd(O/"supplement.json")
ck("primary all6273 pass",a["failed"]==[])
ck("only prior falsepositive preserved",len(sp["failed"])==1 and sp["failed"][0]["name"]=="initial/Git/export stable")
cor=put("final-corrections.json",{"schema":"researchos.independent-review-corrections.v1","actor":"codex:/root/w05_merge_review","checks":checks,"failed":[x for x in checks if not x["pass"]],"reads":readrefs,"original_audit_preserved":True,"predicate_correction":"Same members are compared across rev1 and rev2; revision intentionally increments for original-current-source even when added list is empty. Prior tool exit was 0; this static falsepositive is not a failure origin."})
if any(not x["pass"] for x in checks):print(json.dumps({"failed":[x for x in checks if not x["pass"]]},ensure_ascii=False));raise SystemExit(0)
review={"schema":"researchos.desktop58-failed-execution-independent-review.v1","reviewer":"codex:/root/w05_merge_review","source_author":"codex:/root","decision":"FAILED_EXECUTION_EVIDENCE_CLOSED_QUALIFICATION_WITHHELD","requested_changes":[],"scope_ref":r["scope_ref"],"grant_ref":r["grant_ref"],"report_ref":pin(N/"report.json"),"root_manifest_ref":pin(N/"manifest.json"),"root_handoff_ref":pin(N/"handoff.json"),"root_tool_annex_ref":pin(N/"tool-observations.failed-closure.closed.original.json"),"audit_ref":pin(O/"audit.json"),"supplement_ref":pin(O/"supplement.json"),"final_corrections_ref":cor,"canonical_tuple":[337,165,617],"canonical_refs":r["canonical_refs_unchanged"],"execution_status":"FAILED_CLOSED","qualification":False,"source_acceptance":False,"whole_suite_qualified":False,"visible_installed_GUI_qualified":False,"formal_increment":0,"parent_acceptance_increment":0,"same_scope_rerun_allowed":False,"facts":{"root_caller_tool_exit":1,"root_caller_explicit_python_exit":1,"caller_original_outer_native_exit":None,"launcher_native_inner_exit":1,"launcher_original_outer_native_exit":None,"builder_actual_native_exit":3758097160,"builder_exit_is_requested_termination_code":True,"builder_first_error_native_exit_original":None,"root_caller_error":None,"root_caller_secondary":[],"observed_CREATE":805,"observed_EXIT":805,"exit_event_counts":{"0":802,"3758097160":3},"explicit_handles_closed":8942,"explicit_handles_remaining":0,"job_idle":True,"capture_complete":False,"finalization_errors_preserved":r["builder_job_cleanup"]["errors"],"module_before_records":8130,"module_after_records":0,"rejected_actual_hFile":r["builder_debug_capture_summary"]["rejected_load_diagnostic_facts"],"cases_not_started":170,"qualified_cases":0,"actual_case_rows":0,"HTTP":0,"native_top_commands":3,"closed_original_files_rehashed":108,"export_regular_files_rehashed":5960,"export_reparse_witnesses_not_followed":jd(r["failed_export_tree_ref"]["path"])["reparse_witnesses_not_followed"],"current_source_pins_rehashed":639,"final_vector_members":25590,"all_vectors_saved_drift_empty":True},"cause":"Actual hFile conhost.exe was outside the frozen runtime universe; strict guard requested termination. No case began. This is a preserved rejected module diagnostic, not successful runtime admission or ordinary compiler diagnostic.","evidence_limits":["All 805 lifetimes ended and all owned handles closed, but capture/finalization remained incomplete; successful module after-hashes are absent.","Saved vectors are checked for equality and append-only ledger semantics. The historical full compiler/OS backing trees were not independently rehashed again.","The sole export junction is inspected with lstat/readlink and not followed. Export pins document failed-run artifacts only.","Source/Git status and empty index facts are the sealed owned Git observations; current Main HEAD and canonical byte copies were directly checked without a new Git process.","The caller has no asserted outer OS lifecycle qualification; original NULL fields are unchanged."],"failure_accounting":{"root_snapshot_registered":617,"root_snapshot_observed":635,"root_pending_indices":list(range(618,636)),"underlying_execution_origin_index":631,"wrapper_propagations_additional_count":0,"new_review_failures":1,"new_review_origin_refs":[pin(O/"failure-origin.afe7fb.json")],"new_review_origin_is_outside_root_snapshot":True,"counter_reset":False},"new_product_native_calls":0,"new_candidate_imports_or_execution":0,"canonical_or_source_writes":0}
rr=put("review.json",review)
put("report.json",{"decision":review["decision"],"review_ref":rr,"primary_checks":len(a["checks"]),"supplement_checks":len(sp["checks"]),"correction_checks":len(checks),"new_failures":1,"source_formal_increment":0})
print(json.dumps({"review":rr,"correction_checks":len(checks),"failed":[]},ensure_ascii=False))

