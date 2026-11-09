import hashlib,json,pathlib
O=pathlib.Path(__file__).resolve().parent
R=pathlib.Path(r"D:\作品集\ResearchOS\research-os")
P=R/"execution/v2.4/receipts/W05/W05-99/integration_codex/source-guard-v2-windows-probe-v3-2c915e750ee94356ae32b713bd3d1242"
a=json.loads((O/"success-audit.json").read_bytes());rows=list(a["rows"])
def ref(p,b=None):
 b=p.read_bytes() if b is None else b
 return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def read(p,expected=None):
 p=pathlib.Path(p);b=p.read_bytes();r=ref(p,b)
 if expected is not None:assert r["sha256"]==expected["sha256"] and r["bytes"]==expected["bytes"]
 snap=O/(r["sha256"]+".raw")
 if not snap.exists():snap.write_bytes(b)
 rows.append({"source_ref":r,"snapshot_ref":ref(snap,b)})
 return b
def rr(r):return read(r["path"],r)
def write(n,x):p=O/n;p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");return ref(p)
hdfref={"path":str(P/"handoff.json"),"sha256":"ddff663d514c89196e265fe7dda0ae1fdadaafd9dba7bfb51fb29521c1e0827d","bytes":4957}
h=json.loads(rr(hdfref));mf=json.loads(rr(h["manifest_ref"]))
assert mf["schema"]=="researchos.root-windows-source-guard-component-probe-manifest.v1"
for r in mf["members"]:rr(r)
rootio=json.loads(rr(h["original_root_tool_io_ref"]))
assert rootio["original_output"]["exit_code"]==0
outerlines=rootio["original_output"]["output"].splitlines()
outerrecords=[json.loads(line) for line in outerlines if line.startswith("{")]
assert len(outerrecords)==2 and outerlines.count("ACTUAL_PYTHON_EXIT=0")==1
assert outerrecords[0]["invocation_ref"]==a["invocation_ref"] and outerrecords[0]["actual_native_exit"]==0
assert outerrecords[1]["closed_ref"]==a["closed_ref"]
assert outerrecords[1]["status"]=="ACTUAL_WINDOWS_COMPONENT_PROBE_PASS"
assert "launch_guard_probe.actual_owned.py" in rootio["original_input"]["cmd"] and str(P).replace("\\","/") in rootio["original_input"]["cmd"]
old=[]
for number,key in [(696,"failed_probe_696_ref"),(698,"failed_probe_698_ref")]:
 record=json.loads(rr(h[key]))
 assert record["failure_counter"]==number
 assert record["actual_outer_exit"]==record["actual_parent_python_exit"]==record["actual_native_child_python_exit"]==1
 assert record["original_output"]["exit_code"]==1 and record["one_causal_chain"] is True
 lines=record["original_output"]["output"].splitlines()
 first=json.loads(next(line for line in lines if line.startswith("{")))
 oldinvref=first["invocation_ref"];oldinv=json.loads(rr(oldinvref))
 assert first["actual_native_exit"]==oldinv["actual_native_exit"]==oldinv["result"]["actual_exit"]==1
 olderr=rr(oldinv["stderr_ref"]).decode();rr(oldinv["stdout_ref"])
 assert "AssertionError" in olderr
 cleanup_path=pathlib.Path(oldinvref["path"]).parent/"guard.cleanup.actual.json"
 oldcleanup=json.loads(read(cleanup_path))
 assert oldcleanup["closed"] is True and oldcleanup["retained_handles_count"]==0 and oldcleanup["errors"]==[]
 assert oldinv["result"]["job_cleanup"]["errors"]==[] and oldinv["result"]["job_cleanup"]["active_processes_last_observed"]==0
 assert all(oldinv["result"]["job_cleanup"][k] is True for k in ("assigned_before_resume","primary_exit_confirmed","job_idle_confirmed","handles_closed"))
 if number==696:
  assert "PermissionError: [Errno 13]" in olderr and "write_denied_while_held" in olderr
  cause="Recorded Python stdio PermissionError13 rejects write, followed by producer expected-WinError32 assertion failure. Guard verification and cleanup pass; this run remains native/outer failure1."
  missing=["Win32 GetLastError from the stdio call"]
 else:
  assert "replace_denied_while_held" in olderr and record["actual_replace_error_value_not_persisted_in_failed_producer"] is True
  cause="Recorded assertion 'not succeeded and observed==32' failed at replacement. The saved stderr does not establish which conjunct failed; raw success flag and error value were not persisted. This run remains native/outer failure1."
  missing=["Raw replacement success flag","Raw replacement GetLastError value"]
 old.append({"failure_number":number,"origin_ref":h[key],"invocation_ref":oldinvref,"stderr_ref":oldinv["stderr_ref"],"guard_cleanup_current_ref":ref(cleanup_path),"actual_outer_exit":1,"actual_parent_python_exit":1,"actual_native_child_python_exit":1,"one_causal_chain":True,"outcome":"FAILED_ORIGINAL_PRESERVED","cause":cause,"historical_evidence_gaps":missing,"current_success_does_not_rewrite_old_result":True,"counter_recounted":False})
a["status"]="PASS_ACTUAL_PRIVATE_WINDOWS_COMPONENT_IN_SCOPE"
a["outer_tool_exit"]=0;a["root_parent_python_exit"]=0
a["root_original_io_ref"]=h["original_root_tool_io_ref"];a["source_handoff_ref"]=hdfref;a["source_manifest_ref"]=h["manifest_ref"]
a["source_package_members_verified"]=len(mf["members"]);a["old_failed_probe_results"]=old;a["rows"]=rows
a["new_reviewer_tool_failures"]=0
for row in rows:
 current=ref(pathlib.Path(row["source_ref"]["path"]))
 assert current["sha256"]==row["source_ref"]["sha256"] and current["bytes"]==row["source_ref"]["bytes"]
a["input_records"]=len(rows);a["unique_input_paths"]=len({r["source_ref"]["path"] for r in rows});a["input_drift"]=0
write("bound-audit.json",a)
print(json.dumps({"decision":a["status"],"source_package_members_verified":len(mf["members"]),"input_records":len(rows),"input_drift":0,"outer_exit":0,"parent_python_exit":0,"child_native_exit":0,"old_failures_preserved":[696,698],"new_reviewer_tool_failures":0},ensure_ascii=False,indent=2))

