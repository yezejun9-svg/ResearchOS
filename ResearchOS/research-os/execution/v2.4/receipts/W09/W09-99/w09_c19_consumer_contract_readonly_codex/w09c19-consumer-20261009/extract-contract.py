import ast,hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent;R=Path("D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W09/W09-99"
C=B/"w09_c19_caller_source_revision_codex/w09c19r2-1a11f08"
checks=[];inputs={}
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def ck(k,v):checks.append(dict(label=k,passed=bool(v)))
def verify(ref):
 p=pin(ref["path"]);ck("pin:"+p["path"],p==dict(path=str(Path(ref["path"]).resolve()),sha256=ref["sha256"],bytes=ref["bytes"]));inputs[p["path"]]=p;return p
def read(p):return json.loads(Path(p).read_bytes())
def save(name,obj):
 with (N/name).open("x",encoding="utf-8",newline="\n") as f:f.write(json.dumps(obj,ensure_ascii=False,indent=2)+"\n")
verify(dict(path=str(C/"HDF.json"),sha256="bfb479d0c441c0eeec03858ee41f1d12150e50c8b7b2cee563c16025525e58f2",bytes=6265))
h=read(C/"HDF.json")
for key in ("manifest_ref","choice_ref","prepare_ref","producer_caller_ref","calling_contract_ref","scope_proposal_ref"):verify(h[key])
choice=read(h["choice_ref"]["path"]);contract=read(h["calling_contract_ref"]["path"])
paths={}
for relative in ("ops/ci/retrieval.py","ops/ci/w09_formal_router.py","ops/ci/w09_evidence_closure.py"):
 ref=verify(choice["sources"][relative]);paths[relative]=Path(ref["path"])
nextref=verify(choice["original_input_refs"][0]);nexttask=read(nextref["path"])
r2review=B/"w09_c19_caller_r2_independent_review_codex/w09c19r2r-20261009-source-review"
verify(dict(path=str(r2review/"HDF.json"),sha256="e1e6bad4357aa045b90e86e7e3d07ce3f3d02bcadbe0ac110b721dcb43119ee5",bytes=4450))
rh=read(r2review/"HDF.json");verify(rh["manifest_ref"])
for p in (R/"execution/command_dispatcher/dispatch.py",R/"execution/toolchains/locked.json",R/"execution/v2.4/commands.json"):verify(pin(p))
texts={k:p.read_text(encoding="utf-8") for k,p in paths.items()}
trees={k:ast.parse(v) for k,v in texts.items()}
def literal(tree,name):
 return next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(a,ast.Name) and a.id==name for a in n.targets))
source_roster=literal(trees["ops/ci/retrieval.py"],"SOURCES")
router=trees["ops/ci/w09_formal_router.py"]
formal=literal(router,"FORMAL");native=literal(router,"NATIVE");selected=literal(router,"SELECTED")
routes=[("test.research.fixture","W09","","C19"),("test.retrieval","W09","","C19")]
ck("same-native-five-two-routes",all(native[x]==("C19-01","C19-02","C19-03","C19-04","C19-05") for x in routes))
ck("same-formal-three-two-routes",all(formal[x]==("C19-01","C19-02","C19-03") for x in routes))
ck("21-production-sources",len(source_roster)==21 and len(set(source_roster))==21)
ck("canonical-not-producer-sourcehash-roster",not any(x.startswith("execution/v2.4/") for x in source_roster))
ck("router-cwd-root","ROOT = Path.cwd().resolve()" in texts["ops/ci/w09_formal_router.py"])
ck("sibling-module-import","from w09_evidence_closure import" in texts["ops/ci/w09_formal_router.py"])
ck("consumer-no-canonical-registry-read",all(s not in texts["ops/ci/w09_formal_router.py"]+texts["ops/ci/w09_evidence_closure.py"] for s in ("checkpoint.json","commands.json","canonical-input-vector")))
ck("consumer-mode-per-route",'decision.get("route") == list(route)' in texts["ops/ci/w09_evidence_closure.py"])
ck("consumer-source-and-absolute-owned-binding",'"CURRENT_SOURCE_CLOSURE_MISMATCH"' in texts["ops/ci/w09_evidence_closure.py"] and '"path": str(group[0]["path"])' in texts["ops/ci/w09_evidence_closure.py"])
ck("fixture-temp-check","Path(tempfile.gettempdir())" in texts["ops/ci/w09_evidence_closure.py"])
ck("nexttask-formal-route-order",[a[2] for a in nexttask["formal_commands_after_binding"]]==[x[0] for x in routes])
registry=read(R/"execution/v2.4/commands.json")
entries={key:registry["commands"][key] for key in (x[0] for x in routes)}
save("registry-observed.json",dict(ref=pin(R/"execution/v2.4/commands.json"),revision=registry["revision"],entries=entries,observation_only=True))
sixenv=["RESEARCHOS_W09_NATIVE_REPORT_REF","RESEARCHOS_W09_NATIVE_REPORT_SHA256","RESEARCHOS_W09_TOOL_RUN_REF","RESEARCHOS_W09_TOOL_RUN_SHA256","RESEARCHOS_W09_MODE_DECISION_REF","RESEARCHOS_W09_MODE_DECISION_SHA256"]
ck("current-C19-registry-unbound",all("C19" not in entry.get("selectors",{}).get("case_id",[]) for entry in entries.values()))
ck("current-evidence-env-not-forwarded",all(not any(name in entry["allowed_env"] for name in sixenv) for entry in entries.values()))
T=Path(choice["fixed_paths"]["candidate"]);python=read(R/"execution/toolchains/locked.json")["tools"]["python"]["path"]
env={"RESEARCHOS_TASK_ID":"W09","RESEARCHOS_CHECK_ID":"","RESEARCHOS_CASE_ID":"C19","RESEARCHOS_W09_NATIVE_REPORT_REF":"EXACT_ORIGINAL_REPORT_RELATIVE_TO_CANDIDATE","RESEARCHOS_W09_NATIVE_REPORT_SHA256":"EXACT_ORIGINAL_REPORT_SHA256","RESEARCHOS_W09_TOOL_RUN_REF":"EXACT_ORIGINAL_TOOL_RUN_RELATIVE_TO_CANDIDATE","RESEARCHOS_W09_TOOL_RUN_SHA256":"EXACT_ORIGINAL_TOOL_RUN_SHA256","RESEARCHOS_W09_MODE_DECISION_REF":"ROUTE_SPECIFIC_POSTRUN_DECISION_RELATIVE_TO_CANDIDATE","RESEARCHOS_W09_MODE_DECISION_SHA256":"ROUTE_SPECIFIC_POSTRUN_DECISION_SHA256","TEMP":str(Path(choice["fixed_paths"]["producer_environment"])/"temp"),"TMP":str(Path(choice["fixed_paths"]["producer_environment"])/"temp")}
ck("selected-native-order-preserved",choice["selected_tests"]==["TestW09C19ChainInvalidation","TestW09C19ExplicitOriginAndUnknown"] and all(sorted(selected[x])==sorted(choice["selected_tests"]) for x in routes))
out=dict(schema="researchos.w09-c19-postproducer-consumer-contract.v1",status="READ_ONLY_CODE_DERIVED_CONTRACT_NOT_EXECUTION_GRANT",source_refs={k:pin(p) for k,p in paths.items()},calling_contract_ref=h["calling_contract_ref"],prior_sequence_ref=nextref,consumer_root=str(T),consumer_steps=[dict(order=i+1,route=list(route),cwd=str(T),component_argv=[python,"-B","-X","utf8",str(T/"ops/ci/w09_formal_router.py"),route[0]],environment=dict(env),expected_exit=0,expected_status="PASS",expected_assertion_ids=list(formal[route]),expected_assertions=3,expected_native_assertion_ids=list(native[route]),expected_formal_acceptance="PENDING_INDEPENDENT_VERIFIER") for i,route in enumerate(routes)],same_report_tool_run_and_independent_review=True,distinct_mode_decision_per_route=True,source_roster=source_roster,source_roster_count=21,selected_native_order=choice["selected_tests"],formal_dispatcher_argv_after_registration=nexttask["formal_commands_after_binding"],registry_current_ref=pin(R/"execution/v2.4/commands.json"),formal_consumers="NOT_RUN_REGISTRY_UNBOUND",formal_case_accepted_delta=0,actual_execution=False)
save("consumer-contract.json",out)
save("mode-receipt-required-fields.json",dict(template_only=True,not_a_qualified_decision=True,decision=dict(schema="researchos.w09-mode-decision.v2",required_fields=["route","mode","run_id","report_ref","report_sha256","stdout_sha256","source_sha256","go_executable","producer_id","reviewer_id","reviewer_role","decision","input_origin","independent_review_ref"],required_values=dict(mode="FIXTURE",reviewer_role="INDEPENDENT_NON_AUTHOR",decision="QUALIFIED_ONLY_AFTER_REAL_INDEPENDENT_REVIEW",input_origin="OWNED_TEMP_DIR"),route="exact respective tuple",independent_review_ref="typed relative path/sha256/bytes outside producer run subtree; byte-exact reviewer-authored receipt"),review=dict(schema="researchos.w09-independent-mode-review.v1",required_fields=["actor_id","actor_role","producer_id","run_id","report_sha256","source_sha256","go_executable","run_os","run_os_release","decision"],required_values=dict(actor_role="INDEPENDENT_NON_AUTHOR",decision="QUALIFIED_ONLY_AFTER_REAL_INDEPENDENT_REVIEW"),actor_rule="actor_id == decision.reviewer_id != producer_id")))
for ref in inputs.values():ck("post-pin:"+ref["path"],pin(ref["path"])==ref)
save("input-pins.json",list(inputs.values()))
save("checks.json",dict(count=len(checks),checks=checks,all_passed=all(x["passed"] for x in checks),runtime_executed=False))
assert all(x["passed"] for x in checks),[x for x in checks if not x["passed"]]
print(json.dumps(dict(status=out["status"],checks=len(checks),inputs=len(inputs),source_roster_count=21,actual_execution=False)))

