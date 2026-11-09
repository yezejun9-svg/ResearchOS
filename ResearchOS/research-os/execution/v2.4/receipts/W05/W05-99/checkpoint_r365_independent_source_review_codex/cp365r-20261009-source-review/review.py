import sys
sys.dont_write_bytecode=True
import ast,copy,difflib,hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent;R=Path("D:/作品集/ResearchOS/research-os")
B=R/"execution/v2.4/receipts/W05/W05-99";C=B/"checkpoint_r365_source_preparation_codex/cp365-1a11f08"
checks=[];inputs={}
def ck(label,value):checks.append(dict(label=label,passed=bool(value)))
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def verify(ref):
 expected=dict(path=str(Path(ref["path"]).resolve()),sha256=ref["sha256"].removeprefix("sha256:"),bytes=ref["bytes"])
 actual=pin(ref["path"]);ck("pin:"+expected["path"],actual==expected);inputs[expected["path"]]=expected;return expected
def read(p):return json.loads(Path(p).read_bytes())
def save(name,obj):
 with (N/name).open("x",encoding="utf-8",newline="\n") as f:f.write(json.dumps(obj,ensure_ascii=False,indent=2)+"\n")
def fixed(p,sha,size):return verify(dict(path=str(p),sha256=sha,bytes=size))
fixed(C/"HDF.json","36889c3632ee890ada707b1cd46cacc8d657506c144f7f8d8075b7b2b40ee957",4506)
fixed(C/"MF.json","a54d76a1a26bd38d49bc153a2a7c18f591b6335c5daf4e715f848fbcdada40d5",6035)
h=read(C/"HDF.json")
for ref in read(h["manifest_ref"]["path"])["members"]:verify(ref)
facts=read(h["facts_ref"]["path"]);fr=verify(h["facts_ref"]);writerref=verify(h["writer_ref"])
old=[Path(v["path"]).read_bytes() for v in facts["canonical_refs"]]
for ref in facts["canonical_refs"]:verify(ref)
c0,o0=map(json.loads,old[:2])
ck("before-CP364-OW168-900",c0["revision"]==364 and o0["revision"]==168 and len(c0["failure_counters"])==900)
ck("facts-counter-contract",(facts["registered_before"],facts["registered_after"],facts["highest_observed_ordinal"],facts["next_failure_ordinal"])==(900,923,925,926))
pending=facts["diagnostics"];ck("exact-903-through-925",[x["ordinal"] for x in pending]==list(range(903,926)))
factpins=read(C/"facts-inputs.original-pins.json");ck("261-finite-inputs",len(factpins)==261)
for ref in factpins:verify(ref)
for entry in facts["reviews"]:
 verify(entry["handoff_ref"]);verify(entry["manifest_ref"])
 members=read(entry["manifest_ref"]["path"])["members"]
 for ref in (members.values() if isinstance(members,dict) else members):verify(ref)
for ref in facts["actual_refs"]+facts["qualification_refs"]:verify(ref)
origins={x["ordinal"]:read(verify(x["origin_ref"])["path"]) for x in pending}
ds={x["ordinal"]:x for x in pending}
for x in pending:
 ck("qualified-single-origin:"+str(x["ordinal"]),x["exit_qualification"]["functions_numeric_exit"] is None and x["exit_qualification"]["one_original_invocation"] is True and x["exit_qualification"]["automatic_retry"] is False)
o=origins[921]
ck("921-observed-shell1-functionsNULL",o["tool_return"]["exit_code"]==o["origin"]["command_exit_code"]==ds[921]["actual_outer_exit"]==1 and o["origin"]["functions_numeric_exit"] is ds[921]["exit_qualification"]["functions_numeric_exit"] is None and ds[921]["actual_python_exit"] is ds[921]["actual_native_exit"] is None)
ck("922-observed-shell0-error-not-success",origins[922]["command_exit_code"]==ds[922]["actual_outer_exit"]==0 and origins[922]["atomic_read_failed"] is True and origins[922]["later_same_command_ownership_read_succeeded"] is True and ds[922]["actual_native_exit"] is None)
ck("924-nativeNULL-original-immutable",origins[924]["qualification"]["product_native_exit"] is ds[924]["actual_native_exit"] is None and origins[924]["qualification"]["outer_shell_exit"]==ds[924]["actual_outer_exit"]==1 and ds[924]["actual_python_exit"]==1)
supp=read(verify(ds[924]["exit_qualification"]["independent_native_exit_supplement_ref"])["path"])
ck("924-independent-exit1-is-supplement",supp["primary_native_exit"]==supp["outer_controller_child_exit"]==1 and supp["Native_case_accepted"] is False and ds[924]["exit_qualification"]["original_native_null_preserved"])
ck("925-nonnative-review-diagnostic",origins[925]["actual_product_native_exit"] is ds[925]["actual_native_exit"] is None and origins[925]["actual_outer_shell_exit"]==ds[925]["actual_outer_exit"]==1 and origins[925]["actual_python_exit"]==ds[925]["actual_python_exit"]==1)
ck("914-primary-scope-not-descendant",ds[914]["actual_native_exit"]==1 and ds[914]["exit_qualification"]["native_exit_scope"]=="test2json primary" and ds[914]["exit_qualification"]["descendant_test_binary_exit"] is None)
scope=facts["w09_scope_registration"];scoperef=verify(scope["scope_ref"]);scopeobj=read(scoperef["path"])
ck("scope-root-exact",scoperef["sha256"]=="17b5ebc80477f6ed9012eb751758a8ef9724956cd5f999ee3dd65f37cfa100f7" and scoperef["bytes"]==4891 and scopeobj["executor"]==scopeobj["issued_by"]=="codex:/root")
ck("scope-no-formal-or-main-grant",scopeobj["formal_consumer_execution_authorized_by_this_scope"] is False and scopeobj["main_adoption_authorized_by_this_scope"] is False and scopeobj["formal_acceptance"] is False)
ck("scope-owner-and-worker-ref",scope["owner_subtask"]["scope_ref"]==scope["worker"]["scope_ref"]==scoperef)
ck("scope-sixpaths-five-roots",scope["owner_subtask"]["source_paths"]==scopeobj["permitted_candidate_source_paths"] and scope["owner_subtask"]["fixed_write_roots"]==scopeobj["fixed_write_roots"] and len(scope["owner_subtask"]["source_paths"])==6 and len(scopeobj["fixed_write_roots"])==5)
for key in ("source_handoff_ref","source_manifest_ref","independent_source_review_ref","independent_source_manifest_ref"):
 a=verify(scope["owner_subtask"][key]);b=verify(scopeobj[key]);ck("scope-reused-ref:"+key,a==b)
proof=read(h["writer_inverse_ref"]["path"]);base=Path(verify(proof["base_ref"])["path"]).read_bytes();raw=Path(writerref["path"]).read_bytes()
ops=proof["opcodes"];a=base.decode().splitlines(keepends=True);b=raw.decode().splitlines(keepends=True)
ck("full-writer-old-inverse","".join(x for op in ops for x in op["old_lines"]).encode()==base)
ck("full-writer-new-forward","".join(x for op in ops for x in op["new_lines"]).encode()==raw)
ck("independent-diff-exact",list(difflib.SequenceMatcher(a=a,b=b,autojunk=False).get_opcodes())==[(op["op"],op["old_start"],op["old_end"],op["new_start"],op["new_end"]) for op in ops])
tree=ast.parse(raw);basetree=ast.parse(base);dump=lambda x:ast.dump(x,include_attributes=False)
newf={x.name:x for x in tree.body if isinstance(x,ast.FunctionDef)};oldf={x.name:x for x in basetree.body if isinstance(x,ast.FunctionDef)}
for name in ("pin","verify","save","module","raw_failure_array"):ck("existing-helper-AST:"+name,dump(newf[name])==dump(oldf[name]))
newtry=next(x for x in tree.body if isinstance(x,ast.Try));oldtry=next(x for x in basetree.body if isinstance(x,ast.Try))
ck("same-transaction-call",dump(newtry.body[0])==dump(oldtry.body[0]))
ck("same-finally-guard-close",[dump(x) for x in newtry.finalbody]==[dump(x) for x in oldtry.finalbody])
ck("guard-before-transaction",raw.index(b"guard.acquire(refs)")<raw.index(b"transaction=tm.update_pair"))
ck("canonical-pair-excluded-readguard",b'if ref["path"].casefold() in pairs:continue' in raw)
tp=B/"mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/canonical_transactions.py";gp=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
ck("same-accepted-transaction-source",verify(pin(tp))["sha256"]=="094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9")
ck("same-accepted-guard-source",verify(pin(gp))["sha256"]=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85")
tps=tp.read_text(encoding="utf-8")
ck("pair-exclusive-compare-journal-no-auto-inverse",all(s in tps for s in ('0x80000000|0x40000000,0,None,3','if [pin_raw(p,b) for p,b in zip(PATHS,before)]!=expected_refs','journal/"intent.json"','journal/"failed.partial.json"','"automatic_inverse":False','for handle in reversed(handles):')))
# Only these two inspected functions execute on deepcopy clones. verify is a preverified map, no IO.
class FakeNow:
 def isoformat(self):return "INDEPENDENT_SOURCE_ONLY_TIMESTAMP"
class FakeDatetime:
 @staticmethod
 def now(_):return FakeNow()
def refonly(ref):
 k=str(Path(ref["path"]).resolve());assert k in inputs
 expected=inputs[k];assert expected["sha256"]==ref["sha256"].removeprefix("sha256:") and expected["bytes"]==ref["bytes"]
 return dict(expected)
env=dict(copy=copy,json=json,hashlib=hashlib,verify=refonly,facts=facts,fr=fr,pending=pending,before=copy.deepcopy(c0),before_ownership=copy.deepcopy(o0),old=old,datetime=FakeDatetime,timezone=type("Z",(),{"utc":None}))
selected=[newf["transform"],newf["raw_failure_array"]]
ck("transform-no-command-or-write-call",not any(isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and x.func.attr in ("write_bytes","write_text","open","run","Popen","update_pair","acquire","close") for x in ast.walk(selected[0])))
exec(compile(ast.Module(body=selected,type_ignores=[]),"<independent-pure-transform-only>","exec"),env)
c,o=env["transform"](copy.deepcopy(c0),copy.deepcopy(o0))
encode=lambda v:(json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode()
ck("CP365-OW169",c["revision"]==365 and c["expected_previous_revision"]==364 and o["revision"]==169)
ck("old900-full-semantic",c["failure_counters"][:900]==c0["failure_counters"])
ck("23-new-records-exact-ordinals",len(c["failure_counters"])==923 and [x["original_payload"]["observed_ordinal"] for x in c["failure_counters"][900:]]==list(range(903,926)))
newkeys=[x["origin_key"] for x in c["failure_counters"][900:]]
ck("new-origin-unique",len(set(newkeys))==23 and not(set(newkeys)&{x.get("origin_key") for x in c0["failure_counters"]}))
for p,x in zip(pending,c["failure_counters"][900:]):
 pay=x["original_payload"]
 ck("record-payload-exact:"+str(p["ordinal"]),pay["actual_outer_exit"]==p["actual_outer_exit"] and pay["actual_python_exit"]==p["actual_python_exit"] and pay["actual_native_exit"]==p["actual_native_exit"] and pay["exit_qualification"]==p["exit_qualification"] and pay["origin_selector"]==p["origin_selector"] and x["counted_once"] and not x["counter_reset"] and not x["automatic_retry"])
oldarr=env["raw_failure_array"](old[0]);newarr=env["raw_failure_array"](encode(c))
ck("old900-raw-prefix",newarr.startswith(oldarr.rstrip()[:-1].rstrip()+","))
allowed=("expected_previous_revision","revision","updated_at","updated_by","note","workers","work_in_progress","failure_counters")
inverse=copy.deepcopy(c)
for k in allowed:inverse[k]=copy.deepcopy(c0[k])
ck("full-CP-byte-inverse",encode(inverse)==old[0])
inverse=copy.deepcopy(o);del inverse["card_path_bindings"]["W09-99"]["subtasks"]["c19_fixture_producer"]
for k in ("revision","updated_at","updated_by"):inverse[k]=o0[k]
ck("full-OW-byte-inverse",encode(inverse)==old[1])
ck("old-workers-byte-semantic-preserved",c["workers"][:-1]==c0["workers"] and c["workers"][-1]==scope["worker"])
ck("unique-new-C19-root-worker",len([x for x in c["workers"] if x.get("step_id")=="W09-99" and x.get("slice_id")=="C19_FIXTURE_PRODUCER"])==1 and c["workers"][-1]["owner"]=="codex:/root")
ck("active-W05-W09",c["work_in_progress"]["construction_active_parents"]==["W05","W09"])
rec=c["work_in_progress"]["mu_sdk_r365_actor_reconciliation"]
ck("old-actor-fields-historical-exact",rec["previous_actor_fields"]=={k:c0["work_in_progress"][k] for k in rec["previous_actor_fields"]})
ck("stale-source-actors-cleared",c["work_in_progress"]["configuration_handler_writer"] is None and c["work_in_progress"]["desktop_http_exact15_source_writer"] is None and not c["work_in_progress"]["mu_sdk_source_authors_active"] and not c["work_in_progress"]["mu_sdk_source_readonly_reviewers_active"] and rec["independent_reviewers_count_as_construction"] is False)
wipkeys=set(facts["work_in_progress"])|{"r365_registered_failure_count","r365_highest_observed_diagnostic_ordinal_at_cutoff","r365_next_failure_ordinal_at_cutoff","mu_sdk_r365_facts_ref","later_diagnostics_observed_after_cutoff","root_next_failure_ordinal_live","construction_active_parents"}
ck("unrelated-wip-all-preserved",all(c["work_in_progress"][k]==v for k,v in c0["work_in_progress"].items() if k not in wipkeys))
ck("formal-counters-not-upgraded",c["work_in_progress"]["mu_sdk_r365"]["current_formal_accepted"]==0 and c["work_in_progress"]["mu_sdk_r365"]["required_formal"]==42 and c["work_in_progress"]["mu_sdk_r365"]["original_trial_provider_requests"] is None and c["work_in_progress"]["mu_sdk_r365"]["financial_closed"] is False)
for label,mutate in [
 ("CP-revision",lambda x,y:x.update(revision=363)),("OW-revision",lambda x,y:y.update(revision=167)),
 ("duplicate-owner",lambda x,y:y["card_path_bindings"]["W09-99"]["subtasks"].update(c19_fixture_producer={})),
 ("duplicate-worker",lambda x,y:x["workers"].append(copy.deepcopy(scope["worker"]))),
 ("changed-old-failure",lambda x,y:x["failure_counters"][0].update(independent_mutation=True)),
 ("wrong-active-parent",lambda x,y:x["work_in_progress"].update(construction_active_parents=["W04"]))]:
 x,y=copy.deepcopy(c0),copy.deepcopy(o0);mutate(x,y)
 try:env["transform"](x,y)
 except AssertionError:ck("reject:"+label,True)
 else:ck("reject:"+label,False)
env["pending"]=[copy.deepcopy(pending[0]),copy.deepcopy(pending[0])]+copy.deepcopy(pending[2:])
try:env["transform"](copy.deepcopy(c0),copy.deepcopy(o0))
except AssertionError:ck("reject:duplicate-origin",True)
else:ck("reject:duplicate-origin",False)
ck("canonical-SS-CM-all-four-unchanged",[Path(x["path"]).read_bytes() for x in facts["canonical_refs"]]==old)
# Reuse accepted outcome packets, do not reopen nested TEMP resources.
reviews={x["scope"]:read(x["handoff_ref"]["path"]) for x in facts["reviews"]}
ck("C12-remains-failed",reviews["C12_FAILED_NATIVE_TERMINAL_CLOSURE_ONLY"]["status"]=="FAILED_ACTUAL_CLOSURE_CONFIRMED_NATIVE_CASE_NOT_ACCEPTED")
ck("archive-component-only",reviews["PUBLIC61_ARCHIVE_COMPONENT_ONLY"]["status"]=="FULL_TEMP_PIN_CLOSURE_ACCEPTED_ARCHIVE_COMPONENT_ONLY")
ck("H20-component-only",reviews["H20R2_A20_TO_PLAIN21_COMPONENT_ONLY"]["status"]=="COMPONENT_VALIDATION_ACCEPTED_A20_TO_PLAIN21_ONLY")
ck("W09-only-source",reviews["W09R2_CALLER_SOURCE_573_PASS_NO_ACTUAL"]["status"]=="SOURCE_ACCEPTED_PENDING_ROOT_SCOPE_REGISTRATION_VECTOR_AND_ACTUAL")
controls=read(h["source_controls_ref"]["path"]);ck("author1889-pure-controls",controls["count"]==len(controls["checks"])==1889 and all(x["passed"] for x in controls["checks"]) and controls["writer_main_executed"] is False and controls["canonical_transaction_imported"] is False)
for ref in inputs.values():ck("post-pin:"+ref["path"],pin(ref["path"])==ref)
save("input-pins.json",list(inputs.values()))
save("checks.json",dict(count=len(checks),passed=sum(x["passed"] for x in checks),checks=checks))
save("pure-transform-proof.json",dict(old900_semantic=True,old900_raw_prefix=True,new_ordinals=list(range(903,926)),registered_after=923,high=925,next=926,CP_full_inverse=True,OW_full_inverse=True,SS_CM_unchanged=True,synthetic_timestamp_only=True,future_CP_sha256_not_runtime=hashlib.sha256(encode(c)).hexdigest(),future_OW_sha256_not_runtime=hashlib.sha256(encode(o)).hexdigest(),actual_writer_executed=False,transaction_imported=False,OS_API_or_SourceReadGuard_executed=False))
save("result.json",dict(status="CP365_OW169_SOURCE_GATE_ACCEPTED_PENDING_ROOT_ACTUAL" if all(x["passed"] for x in checks) else "REQUEST_CHANGES",checks=len(checks),inputs=len(inputs),failures=[x for x in checks if not x["passed"]],authority="ADMIN_SOURCE_CONSISTENCY_ONLY",canonical_before_refs=facts["canonical_refs"],actual_writer_executed=False,new_failures=[]))
assert all(x["passed"] for x in checks),[x for x in checks if not x["passed"]]
print(json.dumps(dict(status="CP365_OW169_SOURCE_GATE_ACCEPTED_PENDING_ROOT_ACTUAL",checks=len(checks),inputs=len(inputs),actual_writer_executed=False)))

