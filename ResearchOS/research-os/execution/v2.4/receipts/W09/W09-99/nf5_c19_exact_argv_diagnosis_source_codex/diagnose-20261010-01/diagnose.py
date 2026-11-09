import ast,json,hashlib,os
from pathlib import Path
N=Path(__file__).resolve().parent
R=Path(r"D:\作品集\ResearchOS\research-os")
NF=R/"execution/v2.4/receipts/W09/W09-99/full_w09_main_native_producer_source_codex/fullw09-20261010-05"
P=NF/"actual-C19-ed65b2f6b53447c1ad208a32e48a131b/producer"
facts={}
def sha(b):return hashlib.sha256(b).hexdigest()
def get(p):
 p=Path(p);b=p.read_bytes();facts[str(p)]={"path":str(p),"sha256":sha(b),"bytes":len(b)};return b
def doc(p):return json.loads(get(p))
def pin(p):
 p=Path(p)
 if str(p) not in facts:get(p)
 return facts[str(p)]
def put(name,obj):
 p=N/name
 with p.open("xb") as f:
  f.write((json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode());f.flush();os.fsync(f.fileno())
 return pin(p)
choice=doc(NF/"source.choice.json");c=dict(choice["common"],**choice["selectors"]["C19"])
assert c["run_id"]=="ed65b2f6b53447c1ad208a32e48a131b"
packet=Path(c["output_root"]);report=doc(packet/"report.json");tool=doc(packet/"native-tool-run.json")
closed=doc(P/"validation.closed.json");invocation=doc(P/"w09-selector-main-producer.invocation.json")
get(NF/"HDF.json");get(NF/"MF.json");get(NF/"root-calling-contract.json")
runtime=get(NF/"full_w09_runtime.source.py").decode();overrides=get(NF/"runtime-overrides.source.py").decode()
producer=get(R/"ops/ci/retrieval.py").decode();router=get(R/"ops/ci/w09_formal_router.py").decode()
closure=get(R/"ops/ci/w09_evidence_closure.py").decode();profile=get(R/"execution/v2.4/formal_profile_w09.py").decode()
def assignment(src,key):
 node=next(n for n in ast.parse(src).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==key for t in n.targets))
 return node.value
tests=ast.literal_eval(assignment(producer,"TESTS"))
cases=assignment(producer,"CASES");c19cases=next(ast.literal_eval(v) for k,v in zip(cases.keys,cases.values) if ast.literal_eval(k)=="C19")
routes=ast.literal_eval(assignment(router,"SELECTED"))
formal_tests=list(routes[("test.research.fixture","W09","","C19")])
assert list(routes[("test.retrieval","W09","","C19")])==formal_tests
main_selected=[name for name in tests if name in c19cases]
main_argv=[c["tool_refs"]["go"]["path"],"test","-count=1","-json","-run",
           "^(?:"+"|".join(main_selected)+")$",*sorted({tests[t][0] for t in main_selected})]
expected=[c["tool_refs"]["go"]["path"],*c["go_test_argv_suffix"]]
formal_argv=[report["actual_invocation"][0],"test","-count=1","-json","-run",
             "^(?:"+"|".join(formal_tests)+")$",*sorted({tests[t][0] for t in formal_tests})]
assert report["actual_invocation"]==tool["actual_invocation"]==main_argv
assert expected==formal_argv and c["selected_tests"]==formal_tests==c19cases
diff=[{"index":i,"actual":a,"NF5_and_Main_formal_expected":b}
      for i,(a,b) in enumerate(zip(main_argv,expected)) if a!=b]
assert len(main_argv)==len(expected)==7 and [x["index"] for x in diff]==[5]
assert main_selected!=formal_tests and sorted(main_selected)==sorted(formal_tests)
assert report["selected_tests"]==main_selected and report["passed_tests"]==main_selected
assert report["run_id"]==tool["run_id"]==c["run_id"]
assert tool["report_sha256"]==pin(packet/"report.json")["sha256"]
assert report["exit_code"]==tool["native_exit_code"]==0 and report["status"]=="PASS"
assert closed["status"]=="FAILED_NO_AUTOMATIC_RETRY" and closed["error"]=="ValueError('EXACT_NATIVE_ARGV')"
assert closed["summary"] is None and closed["all_guards_closed"] and closed["all_owned_jobs_closed"]
assert invocation["actual_outer_exit"]==invocation["result"]["actual_exit"]==0
assert invocation["individual_child_numeric_exit"] is None
for relative in ("ops/ci/retrieval.py","ops/ci/w09_formal_router.py","ops/ci/w09_evidence_closure.py"):
 ref=next(x for x in c["source21"] if Path(x["path"])==R/relative)
 assert pin(R/relative)==ref
 assert report["version_manifest"]["source_sha256"][relative]=="sha256:"+ref["sha256"]
guards=[]
for p in sorted(P.glob("*guard.cleanup.actual.json")):
 g=doc(p);assert g["closed"] and g["retained_handles_count"]==0 and not g["errors"]
 guards.append({"ref":pin(p),"closed":True,"retained_handles_count":0,"errors":[],"entries":len(g["entries"])})
assert len(guards)==5
get(P/"launcher.closed.json");get(P/"native-packet.public-index.json")
def evidence_slice(src,name,needle):
 lines=src.splitlines();i=next(i for i,x in enumerate(lines) if needle in x)
 return {"source_ref":pin(name),"line_start":i+1,"line_end":min(len(lines),i+4),"text":"\n".join(lines[i:i+4])}
locators=[
 evidence_slice(runtime,NF/"full_w09_runtime.source.py","return dict(all_choices['common'],**all_choices['selectors'][selector])"),
 evidence_slice(runtime,NF/"full_w09_runtime.source.py","'EXACT_NATIVE_ARGV'"),
 evidence_slice(runtime,NF/"full_w09_runtime.source.py","'EXACT_SELECTED_TESTS_ASSERTIONS'"),
 evidence_slice(producer,R/"ops/ci/retrieval.py","selected = GROUPS[check] if check else list(TESTS)"),
 evidence_slice(producer,R/"ops/ci/retrieval.py",'command = [go, "test"'),
 evidence_slice(closure,R/"ops/ci/w09_evidence_closure.py",'argv = [report["actual_invocation"][0]'),
 evidence_slice(profile,R/"execution/v2.4/formal_profile_w09.py",'selected = router["SELECTED"][route]')]
proposed_selection=[name for name in c19cases if name in list(tests)]
assert proposed_selection==formal_tests
diagnosis={
 "schema":"researchos.nf5-c19-exact-argv-source-diagnosis.v1",
 "author":"codex:/root/attach_restore_independent_review","status":"SOURCE_CONTRACT_ORDER_MISMATCH_CONFIRMED",
 "run_id":c["run_id"],"selector":"C19","failure_ordinal_reserved_by_Root":1156,
 "Root_original_binding_ref":None,"Root_original_binding_status":"PENDING_ROOT_SEAL_NOT_FABRICATED",
 "Root_reported_poll":{"chunk_id":"56bb8e","outer_exit":1,"python_exit":1,"source":"Root task assignment; not yet host-verified here"},
 "actual_native_facts":{"report_ref":pin(packet/"report.json"),"tool_ref":pin(packet/"native-tool-run.json"),
 "report_status":"PASS","report_exit":0,"tool_native_exit":0,
 "formal_construction_acceptance":report["formal_construction_acceptance"],
 "tool_formal_acceptance":tool["formal_acceptance"],
 "producer_invocation_ref":pin(P/"w09-selector-main-producer.invocation.json"),
 "launcher_owned_job_exit":0,"individual_child_numeric_exit":None,
 "validation_ref":pin(P/"validation.closed.json"),"validation_status":closed["status"],"validation_error":closed["error"],
 "validation_summary":None,"native_packet_ref":closed["native_packet_ref"],"guards":guards},
 "comparison":{"actual_argv":main_argv,"NF5_expected_argv":expected,"Main_formal_expected_argv":formal_argv,
 "differences":diff,"actual_selected_tests":main_selected,"NF5_selected_tests":c["selected_tests"],
 "Main_CASES_C19_order":c19cases,"Main_router_C19_order":formal_tests,
 "same_test_set":True,"same_test_order":False,"actual_report_equals_tool_argv":True,
 "NF5_argv_predicate":False,"NF5_selected_tests_predicate_if_reached":False,
 "Main_closure_exact_argv_predicate_if_reached":False},
 "cause":"Main case-only producer starts with TESTS insertion order and filters by CASES membership. C19 TESTS order is Chain then Explicit, but CASES C19, NF5 selected_tests and formal router all specify Explicit then Chain.",
 "impact":"Producer/Go success does not close NF5 validation or Main formal mode/consumer qualification. Reordering only NF5 expected argv would leave Main closure exact-argv disagreement.",
 "minimum_consistent_repair_proposal":{
 "target":"ops/ci/retrieval.py case selector branch, future independently authorized Source revision only",
 "before":"selected = [name for name in selected if name in CASES[case]]",
 "after":"selected = [name for name in CASES[case] if name in selected]",
 "reason":"Preserve selector intersection while using explicit case-contract order; C19 then agrees with NF5 and both formal routes.",
 "not_applied":True,"requires_new_current_Source21_pins":True,
 "old_evidence_preserved":True,"old_Native_not_automatically_requalified":True,
 "follow_on":"New immutable producer Source/Scope/review must bind changed current Source21; no silent reuse, counter reset or automatic Native retry."},
 "static_comparison_only":True,"actual_Main_closure_invoked":False,
 "Native_Go_model_dispatcher_TP_calls":0,"Main_Canon_Scope_NF5_written":False,
 "execution_grant":False,"formal_acceptance":False,"parent_acceptance":False,
 "source_evidence_locators":locators}
dref=put("diagnosis.json",diagnosis)
put("comparison.json",diagnosis["comparison"])
source_refs=[v for k,v in facts.items() if not Path(k).is_relative_to(N)]
for ref in source_refs:
 b=Path(ref["path"]).read_bytes();assert sha(b)==ref["sha256"] and len(b)==ref["bytes"]
put("source-fact-pins.json",{"references":source_refs,"count":len(source_refs),"all_rechecked_unchanged":True})
put("verification.json",{"schema":"researchos.source-only-diagnostic-verification.v1",
 "original_runtime_stage_executed_by_this_task":False,"producer_modules_imported":False,"Main_closure_executed":False,
 "AST_and_immutable_document_comparison":True,"different_argv_indices":[5],"current_main_source_hashes_matched":3,
 "original_cleanup_guards_closed_zero":5,"old_successful_controls_rerun":False,
 "hypothetical_single_line_selection_result":proposed_selection,
 "hypothetical_result_is_execution_evidence":False,"scope":"Exact argv/selection mismatch only; not complete Native closure qualification",
 "source_ref_count":len(source_refs),"diagnosis_ref":dref})
print(json.dumps({"status":diagnosis["status"],"diagnosis_ref":dref,"actual_regex":main_argv[5],
 "expected_regex":expected[5],"source_refs":len(source_refs),"guard_count":len(guards),
 "Root_original1156_binding":"PENDING_ROOT_SEAL"},ensure_ascii=False))

