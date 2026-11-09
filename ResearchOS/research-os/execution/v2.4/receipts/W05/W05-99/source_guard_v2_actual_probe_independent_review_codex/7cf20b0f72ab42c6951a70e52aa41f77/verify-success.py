import ast,hashlib,json,pathlib
O=pathlib.Path(__file__).resolve().parent
R=pathlib.Path(r"D:\作品集\ResearchOS\research-os")
P=R/"execution/v2.4/receipts/W05/W05-99/integration_codex/source-guard-v2-windows-probe-v3-2c915e750ee94356ae32b713bd3d1242"
rows=[]
def ref(p,b=None):
 b=p.read_bytes() if b is None else b
 return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def read(p,expected=None):
 p=pathlib.Path(p);b=p.read_bytes();a=ref(p,b)
 if expected is not None:assert a["sha256"]==expected["sha256"] and a["bytes"]==expected["bytes"],str(p)
 snap=O/(a["sha256"]+".raw")
 if not snap.exists():snap.write_bytes(b)
 rows.append({"source_ref":a,"snapshot_ref":ref(snap,b)})
 return b
def rr(r):return read(r["path"],r)
def obj(b):return json.loads(b)
def write(n,x):p=O/n;p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");return ref(p)
invref={"path":str(P/"probe.invocation.json"),"sha256":"1a728c51a8459140f9ef7fc761828a408a6fc47656ae31f095a81803f3a6a221","bytes":2355}
closedref={"path":str(P/"probe.closed.json"),"sha256":"b473f1c5b3950dba2142b23a59ffd933746fffd2e0d9d33124cf20e796bb18f7","bytes":1285}
inv=obj(rr(invref));closed=obj(rr(closedref))
assert closed["invocation_ref"]==invref
proof=obj(rr(closed["proof_ref"]));cleanup=obj(rr(closed["guard_cleanup_ref"]))
intent=obj(read(P/"probe.intent.json"));inputdoc=obj(read(P/"probe.input.json"))
journalraw=read(P/"control-events.actual.jsonl");journal=[json.loads(line) for line in journalraw.splitlines()]
childraw=rr(intent["child_source_ref"]);parentraw=read(P/"launch_guard_probe.actual_owned.py")
helperraw=rr(intent["helper_ref"]);guardraw=rr(intent["guard_ref"]);review=obj(rr(intent["review_ref"]))
rr(inputdoc["python_ref"])
assert inputdoc["guard_ref"]==intent["guard_ref"]==proof["source_ref"]==review["source_ref"]
assert inputdoc["review_ref"]==intent["review_ref"]==proof["review_ref"]
assert review["decision"]=="PASS_SOURCE_ONLY" and review["reviewer"]=="codex:/root/w05_merge_review"
assert review["source_ref"]["sha256"]=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"
stdout=rr(inv["stdout_ref"]);stderr=rr(inv["stderr_ref"]);stdrecords=[json.loads(line) for line in stdout.splitlines()]
assert stderr==b"" and len(stdrecords)==1
assert stdrecords[0]["proof_ref"]==closed["proof_ref"]
assert stdrecords[0]["actual_pid"]==proof["actual_pid"]==inv["result"]["owned_child_pid"]==41408
assert proof["cleanup_ref"]==closed["guard_cleanup_ref"]
assert inv["actual_native_exit"]==inv["result"]["actual_exit"]==0 and inv["exception"] is None
assert inv["result"]["error"] is None and inv["result"]["timed_out"] is False and inv["result"]["resumed"] is True
jc=inv["result"]["job_cleanup"]
assert jc["errors"]==[] and jc["active_processes_last_observed"]==0
assert all(jc[k] is True for k in ("unnamed_exclusive_job","kill_on_job_close_configured","assigned_before_resume","primary_exit_confirmed","job_idle_confirmed","handles_closed"))
assert type(inv["result"]["creation_time_100ns"]) is int and inv["result"]["creation_time_100ns"]>0
assert inv["result"]["elapsed_seconds"]<intent["wall_seconds"]==30
expected_names=["replace_allowed_before_guard","read_allowed_while_held","write_denied_while_held","delete_denied_while_held","replace_denied_while_held","protected_inputs_unchanged","write_allowed_after_close","replace_allowed_after_guard_close","actual_probe_pid_is_job_member"]
events=proof["events"];assert [e["name"] for e in events]==expected_names
assert all(e["pass"] is True for e in events)
assert events[0]["actual_win32_succeeded"] is True and events[7]["actual_win32_succeeded"] is True
assert events[2]["actual_win32_succeeded"] is False and events[2]["observed_winerror"]==32
assert events[3]["actual_win32_succeeded"] is False and events[3]["observed_winerror"]==32
assert events[4]["actual_win32_succeeded"] is False and events[4]["observed_winerror"]==5
assert journal==events[2:5]
assert cleanup["attempted"] is True and cleanup["verification"]=="PASSED" and cleanup["share_mode"]=="FILE_SHARE_READ_ONLY"
assert cleanup["closed"] is True and cleanup["retained_handles_count"]==0 and cleanup["failure"] is None and cleanup["errors"]==[]
assert len(cleanup["entries"])==3 and all(e["closed"] and e["verified"] and e["final_path_match"] for e in cleanup["entries"])
entryrefs=[{k:e[k] for k in ("path","sha256","bytes")} for e in cleanup["entries"]]
assert entryrefs==events[5]["source_refs"] and entryrefs[2]==inputdoc["python_ref"]
assert len({r["path"] for r in entryrefs})==3
assert all(pathlib.Path(r["path"]).parent==pathlib.Path(inputdoc["fixture_directory"]) for r in entryrefs[:2])
assert intent["argv"]==[inputdoc["python_ref"]["path"],"-I","-S","-X","utf8",intent["child_source_ref"]["path"],str(P/"probe.input.json")]
assert intent["cwd"]==str(R)
assert set(intent["public_environment"])=={"SystemRoot","WINDIR","PATH","USERPROFILE","LOCALAPPDATA","APPDATA","TEMP","TMP"}
assert len(intent["frozen_main_and_canonical_refs"])==9
assert {r["path"] for r in intent["frozen_main_and_canonical_refs"]}==set(inv["frozen_inputs_unchanged"])
assert all(v is True for v in inv["frozen_inputs_unchanged"].values())
# Current observations are separate from the historical before/after raw-byte comparison.
frozen_current=[]
for historical in intent["frozen_main_and_canonical_refs"]:
 p=pathlib.Path(historical["path"]);now=ref(p)
 frozen_current.append({"probe_intent_ref":historical,"current_ref":now,"current_equals_probe_time":now==historical})
# The actual producer is read and parsed only. It is never imported or executed.
childtree=ast.parse(childraw.decode());parenttree=ast.parse(parentraw.decode());helpertree=ast.parse(helperraw.decode())
def function(tree,name):return next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
replace_ast=function(childtree,"raw_replace")
replace_calls=[n for n in ast.walk(replace_ast) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="move"]
assert len(replace_calls)==1
assert ast.unparse(replace_calls[0])=="move(str(replacement), str(a), 1)"
top_replace_calls=[n.lineno for n in childtree.body if isinstance(n,ast.Assign) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=="raw_replace"]
assert len(top_replace_calls)==2
run_owned=function(helpertree,"run_owned")
assign_calls=[n for n in ast.walk(run_owned) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="assign"]
resume_calls=[n for n in ast.walk(run_owned) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="resume"]
assert assign_calls and resume_calls and min(n.lineno for n in assign_calls)<min(n.lineno for n in resume_calls)
audit={"schema":"researchos.source-guard-actual-probe-independent-audit.v1","status":"SUCCESS_RECORDS_VERIFIED_PENDING_OUTER_IO_AND_OLD_FAILURE_BINDING","invocation_ref":invref,"closed_ref":closedref,"producer_ref":intent["child_source_ref"],"launcher_ref":ref(P/"launch_guard_probe.actual_owned.py"),"helper_ref":intent["helper_ref"],"guard_source_ref":intent["guard_ref"],"guard_source_review_ref":intent["review_ref"],"actual_pid":41408,"outer_tool_exit":"PENDING_ORIGINAL_ROOT_TOOL_IO","child_native_exit":0,"child_stdout_pid_proof_ref_matches":True,"actual_cleanup_confirmed":True,"raw_control_journal_matches_proof":True,"actual_winerrors":{"write":32,"delete":32,"replacement":5},"replacement_control_same_paths_before_held_after":True,"same_raw_replace_function_before_after_lines":top_replace_calls,"python_binary_handle_held_and_verified":True,"python_binary_mutation_probe":False,"any_job_alone_not_used_as_exact_job_proof":True,"exact_owned_child_basis":["Pinned parent calls pinned run_owned helper","Pinned helper assigns the newly created child to its explicit unnamed Job before resume","Returned owned_child_pid equals child os.getpid stdout and proof","Same helper returns actual primary exit and Job active-processes zero, all handles closed"],"helper_assign_resume_lines":{"assign":[n.lineno for n in assign_calls],"resume":[n.lineno for n in resume_calls]},"frozen_nine_probe_before_after_byte_comparison_pass":True,"current_frozen_observations":frozen_current,"scope_limits":["Only three held file handles on two private source fixtures plus current pinned Python binary.","Write/delete/replace negatives target the private Chinese filename; no mutation attempt against Python binary or production files.","Replacement WinError5 accepted with same-path before/after success; it is not reported as WinError32.","No whole Controller, trusted Host, runtime qualification or formal acceptance.","Immutable fixture refs describe held-time bytes; after-close write/replace intentionally change one fixture, so they are not asserted to match its current mutable contents."],"reviewer_actual_native_WinAPI_calls":0,"reviewer_provider_calls":0,"reviewer_SQL_calls":0,"reviewer_Main_canonical_writes":0,"candidate_module_imports":0,"rows":rows}
write("success-audit.json",audit)
print(json.dumps({k:v for k,v in audit.items() if k not in ("rows","current_frozen_observations")},ensure_ascii=False,indent=2))
print("INPUT_RECORDS",len(rows))
print("CURRENT_FROZEN_DIFFS",[r["probe_intent_ref"]["path"] for r in frozen_current if not r["current_equals_probe_time"]])

