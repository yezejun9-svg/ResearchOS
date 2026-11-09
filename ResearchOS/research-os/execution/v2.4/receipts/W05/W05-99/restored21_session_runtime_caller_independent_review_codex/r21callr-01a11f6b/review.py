import sys
sys.dont_write_bytecode=True
import ast,copy,hashlib,json,types
from pathlib import Path
N=Path(__file__).resolve().parent
R=Path("D:/作品集/ResearchOS/research-os");W=R/"execution/v2.4/receipts/W05/W05-99"
C=W/"restored21_session_runtime_caller_source_codex/r21v2caller-20261009-01"
forbidden={str((R/"execution/v2.4"/(n+".json")).resolve()).casefold() for n in ("checkpoint","path_ownership","step_state","commands")}
def pin(p):
 p=Path(p).resolve();assert str(p).casefold() not in forbidden
 b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def exact(v):
 p=pin(v["path"]);assert p["sha256"]==v["sha256"] and ("bytes" not in v or p["bytes"]==v["bytes"]),v["path"];return p
def save(n,v):
 with (N/n).open("x",encoding="utf-8",newline="\n") as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+"\n")
checks=[];counterexamples=[];findings=[]
def ck(n,v):
 checks.append(dict(name=n,passed=bool(v)))
 if not v:raise AssertionError(n)
h=exact(dict(path=str(C/"HDF.json"),sha256="b19c49a10fccdeb115ca1dad956bfa9d550df89b9dd28d7716599907e203a2a1",bytes=2659))
m=exact(dict(path=str(C/"MF.json"),sha256="d04e059361e1f16764d93d29208c8614f0dfe16db0eeb701f68ba05ebfc014a2",bytes=2861))
contract=json.loads((C/"contract.json").read_bytes());H=json.loads((C/"HDF.json").read_bytes());M=json.loads((C/"MF.json").read_bytes())
keys=("h20_actual_review_handoff","h20_actual_review_manifest","h20_actual_closed","h20_source_overlay","a21_v2_source_handoff","a21_v2_source_manifest","a21_v2_review_handoff","a21_v2_review_manifest","a21_v2_overlay","source_guard","owned_job","python","go","node","mu_bundle","test2json")
refs=[h,m]+[exact(v) for v in M["members"]]+[exact(contract[k]) for k in keys]
old=json.loads(Path(contract["h20_source_overlay"]["path"]).read_bytes())["sources"]
new=json.loads(Path(contract["a21_v2_overlay"]["path"]).read_bytes())["files"]
refs += [exact(v) for v in list(old.values())+list(new.values())]
for k in ("a21_v2_source_manifest","a21_v2_review_manifest"):
 refs += [exact(v) for v in json.loads(Path(contract[k]["path"]).read_bytes())["members"]]
refs += [pin(__file__)]
refs=list({v["path"].casefold():v for v in refs}.values())
gp=exact(contract["source_guard"]);ck("guard_source_exact",gp["sha256"]=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85")
gm=types.ModuleType("a21caller_independent_guard");gm.__file__=gp["path"];sys.modules[gm.__name__]=gm
exec(compile(Path(gp["path"]).read_bytes(),gp["path"],"exec"),gm.__dict__)
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
try:
 guard.acquire(refs)
 def raw(p):return guard.get_buffer(str(Path(p).resolve()))
 def obj(p):return json.loads(raw(p))
 def src(p):return raw(p).decode()
 prep=src(C/"prepare_root_actual.py");val=src(C/"validate_root_actual.py")
 pt=ast.parse(prep);vt=ast.parse(val)
 pm=next(n for n in pt.body if isinstance(n,ast.FunctionDef) and n.name=="main")
 vm=next(n for n in vt.body if isinstance(n,ast.FunctionDef) and n.name=="main")
 ptry=next(n for n in pm.body if isinstance(n,ast.Try));vtry=next(n for n in vm.body if isinstance(n,ast.Try))
 pdefs={n.name:n for n in ast.walk(ptry) if isinstance(n,ast.FunctionDef)}
 vdefs={n.name:n for n in ast.walk(vtry) if isinstance(n,ast.FunctionDef)}
 ck("Source_HDF_MF_binding",H["manifest_ref"]==m)
 ck("old_actual_scope_accepted",obj(contract["h20_actual_review_handoff"]["path"])["status"]=="COMPONENT_VALIDATION_ACCEPTED_A20_TO_PLAIN21_ONLY")
 ck("v2_source_scope_accepted",obj(contract["a21_v2_review_handoff"]["path"])["status"]=="SOURCE_ACCEPTED_P2_ADDRESSED_PENDING_RUNTIME_QUALIFICATION")
 ck("author40controls_not_runtime",obj(C/"source-controls.json")["count"]==40 and H["actual_test_count"]==0)
 sources=dict(old);sources.update(new)
 ck("61_plus5_three_replacements_two_additions",len(old)==61 and len(new)==5 and len(set(old)&set(new))==3 and len(set(new)-set(old))==2 and len(sources)==63)
 ck("overlay_exact_five",set(new)==set(contract["overlay_exact_paths"]))
 roster=obj(Path(contract["a21_v2_source_handoff"]["path"]).with_name("test-roster.json"));parents=roster["parent_tests"];drift="TestRestored21RejectsForeignPartialSessionAndMissingFence"
 terminals=set(parents)|{drift+"/"+x for x in roster["drift_subtests"]}
 ck("9parents4leaves13unique",len(parents)==len(set(parents))==9 and len(roster["drift_subtests"])==4 and len(terminals)==13)
 test=src(new["internal/domain/backup_restored21_upgrade_test.go"]["path"])
 ck("accepted_H20_fixture_public_call_plain21_no_New24",'history20Fixture(t)' in test and 'UpgradeLocal(context.Background(),prior)' in test and 'if len(before["schema_migrations"])!=21' in test and "New(" not in test)
 ck("disk_return_report_test_retained",'Bytes(report.Recovery),Bytes(persisted.Recovery)' in test)
 ck("program_provenance_truthful_fixture_only","PUBLIC_FIXTURE_MAINTENANCE22_PROGRAM_BYTES" in test and contract["real_21_22_release_program_provenance"]=="OPEN")
 for k in ("worktree","environment","isolation_output","validation_output"):ck("future_root_absent_"+k,not Path(contract[k]).exists())
 for k in ("isolation_output","validation_output"):ck("future_receipts_namespace_"+k,Path(contract[k]).resolve().is_relative_to(W/"integration_codex"))
 ck("fixed_worktree_namespace",Path(contract["worktree"]).resolve().is_relative_to(R/".local/worktrees"))
 ck("fixed_environment_namespace",Path(contract["environment"]).resolve().is_relative_to(R/".local"))
 ck("explicit_prepare10_validate12",len(contract["prepare_argv"])==10 and len(contract["validate_argv"])==12 and contract["prepare_argv"]==contract["validate_argv"][:10])
 ck("four_SHA_bytes_inputs_same_stages",contract["prepare_argv"][1:]==contract["validate_argv"][1:10])
 ck("isolationready_SHAbytes_explicit",contract["validate_argv"][-2:]==["ISOLATION_READY_SHA256","ISOLATION_READY_BYTES"])
 ck("prepare_HEAD_before_after",prep.count(".strip() == head")==2 and "'head-before'" in prep and "'head-after'" in prep)
 ck("validate_HEAD_only_isolationreceipt","isolated['head'] == head" in val and "rev-parse" not in val)
 for name,source in (("prepare",prep),("validate",val)):
  ck(name+"_binary_raw_handles","'xb'" in source and "helper.run_owned(" in source and "creation_flags=0x08000000" in source)
  ck(name+"_explicit_python_exit","SOURCE_PYTHON_EXIT=0" in source and "SOURCE_PYTHON_EXIT=1" in source)
  ck(name+"_unchanged_canonical_check","all(p.read_bytes() == raw for p, raw in before.items())" in source)
 ck("official_jsonl_requires13_not_zero","len(actions) == 13" in val and "started == set(actions) == terminals" in val and "events[-1]['Action'] == 'pass'" in val)
 ck("native_descendant_exit_not_fabricated","'descendant_test_binary_exit': None" in val)
 # Original Source predicate evaluated against its exact pinned 63-input inventory.
 gate=next(n for n in vm.body if isinstance(n,ast.Assert) and "name.startswith" in ast.unparse(n.test))
 gate_result=eval(compile(ast.Expression(gate.test),"<exact-source-path-predicate>","eval"),{},dict(sources=sources))
 rejected=[name for name in sources if not (name.startswith(("internal/domain/","ops/backup/")) and name.endswith(".go"))]
 ck("counterexample_exact_source_roster_rejected",gate_result is False and len(rejected)==18)
 counterexamples.append(dict(id="A21CALL-01",kind="EXACT_PINNED_SOURCE_PREDICATE",line=gate.lineno,rejected_count=len(rejected),rejected_sources=[dict(name=n,ref=exact(sources[n])) for n in rejected],predicate_result=gate_result,product_execution=False))
 findings.append(dict(id="A21CALL-01",priority="P1",file=str(C/"validate_root_actual.py"),line=gate.lineno,title="Exact accepted Source set is rejected before candidate validation",impact="18 of the pinned63 include apps/control, internal/recoveryauthority, ops/supervisor and a numbered SQL file. The all-domain-or-backup-Go assertion is false with the shipped contract, so Root validation deterministically aborts before actual build.",required_fix="Allow exactly the reviewed full composed63 paths and validate safe repository-relative paths individually; preserve necessary SQL and non-domain components. Do not drop these pins to satisfy the predicate."))
 # Replay only original event-gate AST with synthetic events; no files or native execution.
 eventloop=next(n for n in vtry.body if isinstance(n,ast.For) and isinstance(n.iter,ast.Name) and n.iter.id=="events")
 start=vtry.body.index(eventloop);suffix=[]
 for n in vtry.body[start:]:
  if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=="closed":break
  suffix.append(n)
 events=[]
 for name in sorted(terminals):events += [dict(Package="researchos.local/research-os/internal/domain",Test=name,Action="run"),dict(Package="researchos.local/research-os/internal/domain",Test=name,Action="pass")]
 events.append(dict(Package="researchos.local/research-os/internal/domain",Action="pass"))
 ns=dict(events=events,terminals=terminals,result={"actual_exit":0},started=set(),actions={})
 exec(compile(ast.Module(body=suffix,type_ignores=[]),"<in-memory-original-event-gate>","exec"),ns)
 evidence_loads=[n.lineno for n in ast.walk(vm) if isinstance(n,ast.Name) and n.id=="evidence" and isinstance(n.ctx,ast.Load)]
 ck("event_gate_passes_without_typed_evidence",len(ns["actions"])==13 and all(x=="pass" for x in ns["actions"].values()))
 ck("typed_evidence_only_initialabsence_and_env",len(evidence_loads)==2 and "evidence.exists()" in val and "str(evidence)" in val)
 counterexamples.append(dict(id="A21CALL-02",kind="PURE_AST_SYNTHETIC_13_PASS_GATE",line=eventloop.lineno,events=len(events),accepted_actions=len(ns["actions"]),typed_child_evidence_provided=False,typed_evidence_load_lines=evidence_loads,product_execution=False))
 findings.append(dict(id="A21CALL-02",priority="P1",file=str(C/"validate_root_actual.py"),line=eventloop.lineno,title="Success gate omits typed descendant process evidence and export",impact="The caller only passes an empty evidence directory via environment. It never reads, pins, inventories or exports its resulting native descendants evidence;13 valid-looking test2json results satisfy its success gate even when those artifacts are absent. PID/FILETIME precision, child argv/out/err and child closure cannot be audited from validation.closed.",required_fix="After native execution, validate and archive the bounded typed evidence corpus with exact refs and integer/decimal-string64 identity fields, bind it to this run and sources, check descendant closure and raw argv/stdout/stderr before producing success."))
 # Replay the original finally cleanup lists against fake guards only.
 class FakeGuard:
  def __init__(self,name,bad=False):self.name=name;self.bad=bad;self.called=False
  def close(self):
   self.called=True
   return dict(closed=not self.bad,errors=["synthetic_close_failure"] if self.bad else [],retained_handles_count=1 if self.bad else 0)
 cleanup_cases=[]
 for label,node,names in (("prepare",ptry,["runtime_guard","guard"]),("validate",vtry,["binary_guard","compiler_guard","candidate_guard","runtime_guard","input_guard"])):
  fake={name:FakeGuard(name,bad=i==0) for i,name in enumerate(names)};writes=[]
  space=dict(fake,save=lambda name,value:writes.append(dict(name=name,value=value)))
  raised=False
  try:exec(compile(ast.Module(body=node.finalbody,type_ignores=[]),"<in-memory-original-cleanup-loop>","exec"),space)
  except AssertionError:raised=True
  called=[name for name in names if fake[name].called];notcalled=[name for name in names if not fake[name].called]
  ck("counterexample_cleanup_shortcircuits_"+label,raised and called==[names[0]] and len(notcalled)==len(names)-1)
  cleanup_cases.append(dict(stage=label,line=node.finalbody[0].lineno,called=called,not_called=notcalled,synthetic_only=True))
 # Replay original invoke with fake file handles and fake helper to expose jobs=[] truth.
 class FakePath:
  def __init__(self,s):self.s=s
  def __truediv__(self,n):return FakePath(self.s+"/"+n)
  def open(self,*args):return self
  def __enter__(self):return self
  def __exit__(self,*args):return False
  def __str__(self):return self.s
 bad_result=dict(actual_exit=None,timed_out=False,error="synthetic_owned_job_error",job_cleanup=dict(errors=["job_handle_retained"],active_processes_last_observed=1,handles_closed=False))
 helper=types.SimpleNamespace(run_owned=lambda *a,**k:copy.deepcopy(bad_result))
 writes=[];space=dict(T=FakePath("SYNTHETIC_CANDIDATE"),O=FakePath("SYNTHETIC_OUTPUT"),helper=helper,env={},jobs=[],invocations=[],json=json,print=lambda *a,**k:None,pin=lambda p:dict(path=str(p),sha256="0"*64,bytes=0),save=lambda n,v:(writes.append(dict(name=n,value=v)) or dict(path=n,sha256="0"*64,bytes=0)))
 exec(compile(ast.Module(body=[vdefs["invoke"]],type_ignores=[]),"<in-memory-original-invoke>","exec"),space)
 raised=False
 try:space["invoke"]("synthetic",["not-executed"],1)
 except AssertionError:raised=True
 ck("counterexample_job_failure_not_in_jobs",raised and space["jobs"]==[] and all(space["jobs"]) is True)
 counterexamples.append(dict(id="A21CALL-03",kind="PURE_AST_FAKE_GUARD_AND_FAKE_JOB",cleanup_cases=cleanup_cases,failed_job_recorded_in_jobs=False,closed_all_jobs_expression=all(space["jobs"]),native_execution=False))
 findings.append(dict(id="A21CALL-03",priority="P1",file=str(C/"validate_root_actual.py"),line=vtry.finalbody[0].lineno,title="Cleanup aborts early and failed job closure can be reported true",impact="If the first guard returns a cleanup error, both finally loops assert before closing remaining guards. invoke can reject a result before appending to jobs; FAILED closed then reports all_owned_jobs_closed=all([])=true although the failing job has retained handles. Ready/PASS is also written before guard cleanup and validator does not require prepare cleanup refs.",required_fix="Attempt and record every guard cleanup despite errors; record job closure including exceptions/failures before rejecting a result, distinguish not-observed from closed, and publish stage-ready/success only after required cleanup is verified. Bind exact prepare cleanup/closed evidence into stage2."))
 # Original CP comparison accepts bool/float; no OW JSON revision validation exists.
 revisions=[]
 for label,main in (("prepare",pm),("validate",vm)):
  predicate=next(n for n in main.body if isinstance(n,ast.Assert) and "['revision']" in ast.unparse(n.test))
  for label2,payload,expected in (("bool_true",b'{"revision":true}',1),("float",b'{"revision":366.0}',366),("zero",b'{"revision":0}',0)):
   values=["0"*64,"1",str(expected)];space=dict(json=json,before={"cp":payload},CANONICAL=["cp"],values=values)
   accepted=eval(compile(ast.Expression(predicate.test),"<original-canonical-revision-predicate>","eval"),space)
   ck("counterexample_revision_"+label+"_"+label2,accepted is True)
   revisions.append(dict(stage=label,case=label2,accepted=accepted,line=predicate.lineno))
 counterexamples.append(dict(id="A21CALL-04",kind="PURE_AST_JSON_REVISION_PREDICATE",cases=revisions,ownership_revision_validation=False))
 findings.append(dict(id="A21CALL-04",priority="P2",file=str(C/"validate_root_actual.py"),line=next(n.lineno for n in vm.body if isinstance(n,ast.Assert) and "['revision']" in ast.unparse(n.test)),title="Canonical revision gate does not validate positive integer structure",impact="Both stages accept JSON true,366.0 or0 as checkpoint revision when the numeric argument compares equal; path_ownership is hash-bound but its revision structure is never validated.",required_fix="Validate current checkpoint and ownership JSON revision as positive type-int excluding bool, then compare checkpoint with the explicit revision and bind the identical four-ref vector across stages. Keep genuine Root-provided revisions dynamic."))
 fields=next(n for n in vt.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=="FIELDS")
 fieldnames=ast.literal_eval(fields.value)
 ck("inventory_covers_declared_embed_test_source_fields",all(f in fieldnames for f in ("TestGoFiles","XTestGoFiles","EmbedFiles","TestEmbedFiles","XTestEmbedFiles","CompiledGoFiles")))
 ck("inventory_omits_export_and_module_fields","Export" not in fieldnames and "Module" not in fieldnames and "'-export'" not in val)
 counterexamples.append(dict(id="A21CALL-05",kind="STATIC_COMPILER_INVENTORY_FIELD_AUDIT",captured_fields=list(fieldnames),export_file_field_captured=False,module_manifest_field_captured=False,shared_GOCACHE=True,no_runtime_claim=True))
 findings.append(dict(id="A21CALL-05",priority="P2",file=str(C/"validate_root_actual.py"),line=fields.lineno,title="Compiler inventory omits export/cache and dependency module manifests",impact="The go list call does not request-export, and FIELDS never records pkg.Export or Module.GoMod; compilation uses shared GOCACHE/GOPATH. The Source can claim source/embed inventory but not an exact frozen compiler dependency/export closure.",required_fix="Record and guard the actual module manifests and required export/cache artifacts or use a reviewed fresh isolated cache strategy, then make the inventory claim match what is held."))
 ck("original945_has_honest_null_envelope",obj(C/"original-failure.945.json")["original_chunk_id"] is None and obj(C/"original-failure.945.json")["original_exit_code"] is None)
 ck("no_original945_pin_drift",pin(C/"original-failure.945.json")["sha256"]=="4ac8ff0550fea4e430f5f6f46db3678252929420e770c8896fe76fa573da3394")
 ck("all_exact_inputs_unchanged_while_held",all(pin(v["path"])==v for v in refs))
 save("counterexamples.json",counterexamples);save("findings.json",findings)
finally:
 cleanup=guard.close();save("source-guard.cleanup.actual.json",cleanup)
ck("independent_actual_guard_closed",cleanup["closed"] is True and not cleanup["errors"] and cleanup["retained_handles_count"]==0)
save("checks.json",checks);save("input-pins.json",refs)
save("result.json",dict(status="REQUEST_CHANGES",independent_checks=len(checks),finite_exact_inputs=len(refs),P1_findings=3,P2_findings=2,strict_counterexamples=len(counterexamples),synthetic_AST_controls_only=True,actual_caller_Git_Go_compile_SQL_native_product_CLI_model=False,current_canonical_read_locked_written=False,source_author_files_modified=False,formal_acceptance=False,formal_case_accepted_delta=0,new_original_failures=[]))
print(json.dumps(dict(status="REQUEST_CHANGES",checks=len(checks),inputs=len(refs),findings_ref=pin(N/"findings.json"),counterexamples_ref=pin(N/"counterexamples.json"),result_ref=pin(N/"result.json"))))

