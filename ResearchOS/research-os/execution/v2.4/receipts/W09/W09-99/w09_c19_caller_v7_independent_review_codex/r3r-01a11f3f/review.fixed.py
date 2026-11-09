import sys
sys.dont_write_bytecode=True
import ast,copy,hashlib,json,types
from pathlib import Path
N=Path(__file__).resolve().parent
R=Path("D:/作品集/ResearchOS/research-os")
W=R/"execution/v2.4/receipts/W09/W09-99"
C=W/"w09_c19_caller_v7_source_codex/w09c19r3-1a11f30"
S=W/"w09_c19_caller_source_revision_codex/w09c19r2-1a11f08"
V=W/"w09_evidence_v7_fragment_source_codex/fragv7-1a11f30"
Q=W/"w09_c19_caller_r2_independent_review_codex/w09c19r2r-20261009-source-review"
F=W/"v7_fragment_independent_review_codex/v7r-01a11f3f"
GP=R/"execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes()
 return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def verify(ref):
 actual=pin(ref["path"])
 assert actual["sha256"]==ref["sha256"].removeprefix("sha256:") and actual["bytes"]==ref["bytes"],ref["path"]
 return actual
def save(name,obj):
 with (N/name).open("x",encoding="utf-8",newline="\n") as f:f.write(json.dumps(obj,ensure_ascii=False,indent=2)+"\n")
checks=[]
def check(name,ok,detail=None):
 checks.append(dict(name=name,passed=bool(ok),detail=detail))
 if not ok:raise AssertionError(name)
h=verify(dict(path=str(C/"HDF.json"),sha256="1ad85d20080d9ad8c0fb5cd4220a04646f3d1a6d2f04296713dbe1b24520e0f3",bytes=7985))
m=verify(dict(path=str(C/"MF.json"),sha256="991592e7cccb49947dabc63cbeb0d76c656ae73568d1f7da97c3e3ecc87f04a1",bytes=9297))
H=json.loads(Path(h["path"]).read_bytes());M=json.loads(Path(m["path"]).read_bytes())
refs=[h,m]+[verify(v) for v in M["members"]]
for filename in ("source-input-pins.original.json","choice-input-pins.original.json"):
 refs += [verify(v) for v in json.loads((C/filename).read_bytes())]
choice=json.loads((C/"source.integration.choice.json").read_bytes())
refs += [verify(v) for v in list(choice["sources"].values())+choice["base_driver_refs"]+choice["review_refs"]+choice["original_input_refs"]]
refs += [pin(S/"source.integration.choice.json"),pin(S/"root-calling-contract.json"),pin(GP),pin(__file__),pin(sys.executable)]
refs=list({v["path"].casefold():v for v in refs}.values())
canonical={str((R/"execution/v2.4"/(name+".json")).resolve()).casefold() for name in ("checkpoint","path_ownership","step_state","commands")}
check("no_current_canonical_read_guard_inputs",not any(v["path"].casefold() in canonical for v in refs))
check("guard_accepted_exact_hash",pin(GP)["sha256"]=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85")
gm=types.ModuleType("r3_independent_actual_source_guard");gm.__file__=str(GP);sys.modules[gm.__name__]=gm
exec(compile(GP.read_bytes(),str(GP),"exec"),gm.__dict__)
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
try:
 guard.acquire(refs)
 def raw(p):return guard.get_buffer(str(Path(p).resolve()))
 def obj(p):return json.loads(raw(p))
 oldchoice=obj(S/"source.integration.choice.json");contract=obj(C/"root-calling-contract.json");oldcontract=obj(S/"root-calling-contract.json")
 check("candidate_HDF_manifest_pin",H["manifest_ref"]==m)
 check("r2_source_HDF_pin",pin(S/"HDF.json")["sha256"]=="bfb479d0c441c0eeec03858ee41f1d12150e50c8b7b2cee563c16025525e58f2")
 check("r2_source_MF_pin",pin(S/"MF.json")["sha256"]=="455553ae51eb98c6ead665c7f9dfde0d9e6b5e765418d760f335d5f8845b0ab8")
 check("r2_non_author_HDF_pin",pin(Q/"HDF.json")["sha256"]=="e1e6bad4357aa045b90e86e7e3d07ce3f3d02bcadbe0ac110b721dcb43119ee5")
 check("r2_non_author_MF_pin",pin(Q/"MF.json")["sha256"]=="8759a702db34490765433cfcd62f888dfce8e1647ef4c58321a68b7459428194")
 check("r2_non_author_gate",obj(Q/"HDF.json")["status"]=="SOURCE_ACCEPTED_PENDING_ROOT_SCOPE_REGISTRATION_VECTOR_AND_ACTUAL")
 check("v7_non_author_HDF_pin",pin(F/"HDF.json")["sha256"]=="dc5eaea8d4b7c8a74db392b9a4782af7075e657d607c42a79ce1e61b8e979ef6")
 check("v7_non_author_MF_pin",pin(F/"MF.json")["sha256"]=="0b30564210352839b4bb435e6086b74828e06b9172d7b802817329e043eb6f0f")
 replacements=[
 ("w09c19-1a11f08","w09c19v7-1a11f30"),
 ("w09c19-isolation-1a11f08","w09c19v7-isolation-1a11f30"),
 ("w09c19-producer-1a11f08","w09c19v7-producer-1a11f30"),
 ("w09c19-isolation-env-1a11f08","w09c19v7-isolation-env-1a11f30"),
 ("w09c19-producer-env-1a11f08","w09c19v7-producer-env-1a11f30")]
 proof=obj(C/"caller-complete-inverse.json");inverse_results=[]
 for name in ("prepare_w09_c19.actual_owned.py","run_w09_c19.actual_owned.py"):
  prior=raw(S/name);new=raw(C/name)
  forward=prior.decode("utf-8")
  for old,newpath in replacements:forward=forward.replace(old,newpath)
  check(name+"_independent_full_byte_forward",forward.encode()==new)
  inverse=new.decode("utf-8")
  for old,newpath in reversed(replacements):inverse=inverse.replace(newpath,old)
  check(name+"_independent_full_byte_inverse",inverse.encode()==prior)
  ot=ast.parse(prior);nt=ast.parse(new)
  check(name+"_whole_module_AST_inverse",ast.dump(ast.parse(inverse),include_attributes=False)==ast.dump(ot,include_attributes=False))
  of={x.name:x for x in ot.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))}
  nf={x.name:x for x in nt.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))}
  check(name+"_exact_function_set",set(of)==set(nf))
  for fname,node in of.items():check(name+"_unchanged_function_AST_"+fname,ast.dump(node,include_attributes=False)==ast.dump(nf[fname],include_attributes=False))
  for old,newpath in replacements:check(name+"_old_path_absent_"+old,old not in new.decode())
  cp=next(v for v in proof["callers"] if Path(v["candidate_ref"]["path"]).name==name)
  check(name+"_author_whole_opcode_inverse_and_forward","".join(l for op in cp["opcodes"] for l in op["old_lines"]).encode()==prior and "".join(l for op in cp["opcodes"] for l in op["new_lines"]).encode()==new)
  inverse_results.append(dict(name=name,old_ref=pin(S/name),new_ref=pin(C/name),all_other_bytes_unchanged=True,all_functions_AST_unchanged=True))
 expectedpaths={}
 for key,value in oldchoice["fixed_paths"].items():
  for old,newpath in replacements:value=value.replace(old,newpath)
  expectedpaths[key]=value
 check("exact_independent_five_future_paths",choice["fixed_paths"]==expectedpaths and len(expectedpaths)==5 and len(set(expectedpaths.values()))==5)
 for key,p in expectedpaths.items():check("future_path_absent_"+key,not Path(p).exists())
 closure="ops/ci/w09_evidence_closure.py";v7=pin(V/"w09_evidence_closure.v7.proposed.py")
 check("v7_exact_source",v7["sha256"]=="1cc37f4fec48d2e2bae39db3c1f8d1da9fdfe6bd788a44396ea0a8b877be6777" and v7["bytes"]==42716)
 check("exact_six_same_order",list(choice["sources"])==list(oldchoice["sources"]) and len(choice["sources"])==6)
 for path,ref in oldchoice["sources"].items():
  check("Source_pin_"+path,choice["sources"][path]==(v7 if path==closure else ref))
 binding=obj(C/"v7-independent-review.binding.json")
 check("v7_binding_exact_two_receipts",binding["handoff_ref"]==pin(F/"HDF.json") and binding["manifest_ref"]==pin(F/"MF.json"))
 check("v7_binding_matches_actual_source",obj(F/"HDF.json")["candidate_ref"]==v7)
 check("v7_binding_status_source_only",binding["status"]==obj(F/"HDF.json")["status"]=="SOURCE_ACCEPTED_PENDING_NEW_PRODUCER_AND_MODE_DECISIONS" and obj(F/"HDF.json")["formal_acceptance"] is False)
 expectedchoice=copy.deepcopy(oldchoice)
 expectedchoice["sources"][closure]=v7
 expectedchoice["fixed_paths"]=expectedpaths
 expectedchoice["base_driver_refs"]=[pin(S/name) for name in ("prepare_w09_c19.actual_owned.py","run_w09_c19.actual_owned.py")]
 expectedchoice["review_refs"] += [pin(Q/"HDF.json"),pin(Q/"MF.json"),pin(F/"HDF.json"),pin(F/"MF.json")]
 expectedchoice["original_input_refs"]=[v7 if v==oldchoice["sources"][closure] else v for v in oldchoice["original_input_refs"]]
 expectedchoice["original_input_refs"] += [pin(S/"HDF.json"),pin(S/"MF.json"),pin(S/"source.integration.choice.json"),pin(V/"HDF.json"),pin(V/"MF.json"),pin(V/"source-contract.json"),pin(C/"v7-independent-review.binding.json")]
 historical=obj(V/"HDF.json")["canonical_refs_unchanged"]
 expectedchoice["provenance_original"]=dict(canonical_refs=historical,checkpoint_ref=historical[0],checkpoint_revision=365,ownership_revision=169,purpose="HISTORICAL_SOURCE_PREPARATION_ONLY_NOT_ACTUAL_BINDING")
 expectedchoice["r3_provenance"]=dict(base_source_handoff_ref=pin(S/"HDF.json"),base_source_manifest_ref=pin(S/"MF.json"),v7_source_handoff_ref=pin(V/"HDF.json"),v7_source_manifest_ref=pin(V/"MF.json"),v7_independent_review_status=binding["status"],old_v6_closure_ref=oldchoice["sources"][closure],r2_historical_canonical_provenance=oldchoice["provenance_original"],replaced_only_one_of_six_source_refs=True,no_Main_source_adoption=True,new_native_run_required=True,old_v6_native_packet_not_reused=True,actual_Git_Go_SQL_API_model_consumer=False)
 check("independent_entire_choice_expected_semantics",expectedchoice==choice)
 check("independent_entire_choice_expected_bytes",(json.dumps(expectedchoice,ensure_ascii=False,indent=2)+"\n").encode()==raw(C/"source.integration.choice.json"))
 expectedkeys={"sources","base_driver_refs","review_refs","original_input_refs","fixed_paths","provenance_original","r3_provenance"}
 actualkeys={k for k in set(choice)|set(oldchoice) if choice.get(k)!=oldchoice.get(k)}
 check("choice_exact_allowlisted_delta_keys",actualkeys==expectedkeys)
 delta=obj(C/"choice-complete-inverse.json")
 inverse=copy.deepcopy(choice)
 for d in delta["semantic_deltas"]:
  if d["old_present"]:inverse[d["key"]]=d["old"]
  else:del inverse[d["key"]]
 check("author_choice_semantic_inverse",inverse==oldchoice)
 check("author_choice_full_old_new_byte_reconstruction","".join(l for op in delta["opcodes"] for l in op["old_lines"]).encode()==raw(S/"source.integration.choice.json") and "".join(l for op in delta["opcodes"] for l in op["new_lines"]).encode()==raw(C/"source.integration.choice.json"))
 check("no_canonical_static_ref_in_effective_choice",not any(str(Path(v["path"]).resolve()).casefold() in canonical for v in choice["original_input_refs"]+choice["base_driver_refs"]+choice["review_refs"]+list(choice["sources"].values())))
 check("new_selected_order_preserved",choice["selected_tests"]==oldchoice["selected_tests"]==["TestW09C19ChainInvalidation","TestW09C19ExplicitOriginAndUnknown"])
 for key in ("exact_six_targets","expected_native_ids","expected_formal_ids","canonical_input_binding","native_producer_runs","formal_consumers","main_adopted","execution_grant"):
  check("preserved_choice_"+key,choice[key]==oldchoice[key])
 prep=raw(C/"prepare_w09_c19.actual_owned.py").decode();producer=raw(C/"run_w09_c19.actual_owned.py").decode()
 check("prepare_explicit_six_args",len(contract["preparation_argv"])==13 and contract["prepare_parameter_count"]==6 and "len(sys.argv)==7" in prep)
 check("producer_explicit_ten_args",len(contract["producer_caller_argv"])==17 and contract["producer_parameter_count"]==10 and "len(sys.argv)==11" in producer)
 check("contract_exact_new_choice_pin",contract["producer_caller_argv"][7:9]==[pin(C/"source.integration.choice.json")["sha256"],str(pin(C/"source.integration.choice.json")["bytes"])])
 check("contract_exact_new_script_paths",Path(contract["preparation_argv"][6])==C/"prepare_w09_c19.actual_owned.py" and Path(contract["producer_caller_argv"][6])==C/"run_w09_c19.actual_owned.py")
 check("same_vector_explicit_no_hardcoded_future_revision",contract["canonical_input_binding"]==oldcontract["canonical_input_binding"] and contract["same_vector_in_both_invocations"] is True and contract["expected_future_checkpoint"] is None)
 check("contract_isolated_Python_flags",all(x[1:6]==["-I","-S","-B","-X","utf8"] for x in (contract["preparation_argv"],contract["producer_caller_argv"])))
 check("vector_binding_before_output_creation",prep.index("vector_ref,canonical_refs=bind_canonical_input_vector(")<prep.index("assert not O.exists();O.mkdir") and producer.index("assert isolation[\"canonical_input_vector_ref\"]==vector_ref")<producer.index("assert not O.exists();O.mkdir"))
 check("prepare_ready_and_producer_both_same_vector","canonical_input_vector_ref=vector_ref" in prep and 'assert isolation["canonical_input_vector_ref"]==vector_ref' in producer)
 check("historical_checkpoint_not_loaded_by_callers","provenance_original" not in prep and "provenance_original" not in producer and "365" not in prep and "365" not in producer)
 check("ready_fixed_new_namespace","w09c19v7-isolation-1a11f30" in producer and 'str(ISO/"isolation.ready.json")' in producer and 'Path(isolation["worktree_root"]).resolve()==T' in producer)
 check("new_native_packet_only","assert not base.exists()" in producer and "len(created)==1" in producer and 'packet_dir.parent==base' in producer)
 check("raw_archived_before_success_check",producer.index('archive=O/"native-packet"')<producer.index('assert result["actual_exit"]==0 and not result["timed_out"] and report["status"]==\"PASS\"'))
 check("producer_formal_delta_remains_zero",'report["formal_case_accepted_delta"]==0' in producer and 'formal_acceptance=False' in producer)
 check("no_automatic_consumer","run_c19_consumers" not in producer and "dispatch.py" not in producer and contract["actual_formal_consumer_executed"] is False)
 retrieval=ast.parse(raw(Path(choice["sources"]["ops/ci/retrieval.py"]["path"])))
 source_node=next(x for x in retrieval.body if isinstance(x,ast.Assign) and any(isinstance(y,ast.Name) and y.id=="SOURCES" for y in x.targets))
 roster=ast.literal_eval(source_node.value)
 check("Source21_roster_exact_count_and_closure",len(roster)==21 and closure in roster)
 check("future_source_hashes_computed_from_new_worktree",b'"source_sha256": {name: digest(ROOT / name) for name in SOURCES}' in raw(Path(choice["sources"]["ops/ci/retrieval.py"]["path"])))
 check("new_v7_modes_explicit_required",contract["closure_source_change_requires_new_producer_Source21"] is True and contract["old_v6_packet_immutable"] is True and contract["v7_independent_review_refs"]==[pin(F/"HDF.json"),pin(F/"MF.json")])
 ctr=obj(C/"source-controls.json");prior=obj(C/"pre-v7-review.original.source-controls.json")
 retained=[v for v in prior["checks"] if v["name"] not in {"choice_exact_call_pin","choice_full_semantic_inverse","choice_full_byte_inverse"}]
 check("author_controls_prior131_retained128_plus_new13",prior["count"]==131 and len(retained)==128 and ctr["count"]==141 and ctr["retained_prebinding_check_count"]==128 and ctr["new_or_repeated_affected_check_count"]==13 and ctr["checks"][:128]==retained and len(ctr["checks"][128:])==13)
 check("author_controls_all141_PASS",all(v["passed"] is True for v in ctr["checks"]))
 check("author_controls_retained_exact_provenance",ctr["retained_prebinding_controls_ref"]==pin(C/"pre-v7-review.original.source-controls.json"))
 g=obj(C/"preparation-source-guard.cleanup.json")
 check("author_actual_guard_closed",g["closed"] and not g["errors"] and g["retained_handles_count"]==0 and all(v["closed"] and v["verified"] and v["final_path_match"] for v in g["entries"]))
 failure=obj(C/"failure-origins.json")
 check("original_failures_exact_two_once",failure["ordinals"]==[933,934] and failure["new_original_failures"]==H["new_original_failures"])
 for ordinal,sha,size,pyexit in [(933,"3a9d761bde3a869557406fe73aa7f093237c9e4610041cca89dd8e9adc5cb39d",1115,None),(934,"2d48eee15da96fbb4f3e47c1c233538684916c4aea616a1d66b5fcc81b319c81",1259,1)]:
  p=C/f"failure-origin.{ordinal}.original-tool-io.json";f=obj(p)
  check("failure_original_"+str(ordinal),pin(p)["sha256"]==sha and pin(p)["bytes"]==size and f["ordinal"]==ordinal and f["result"]["exit_code"]==1 and f["qualification"]["python_exit"]==pyexit and f["qualification"]["native_exit"] is None and f["qualification"]["model_exit"] is None)
 for ref in refs:check("final_input_pin_"+ref["path"],pin(ref["path"])==ref)
 for key,p in expectedpaths.items():check("postcheck_future_path_absent_"+key,not Path(p).exists())
 save("checks.json",dict(all_passed=all(v["passed"] for v in checks),count=len(checks),checks=checks))
 save("input-pins.json",refs)
 save("independent-inverse.json",dict(callers=inverse_results,choice_expected_semantics_and_bytes=True,choice_allowed_delta_keys=sorted(expectedkeys),Source21=roster,future_paths=expectedpaths,historical_canonical_live_not_read_or_held=True))
 save("result.json",dict(status="SOURCE_ACCEPTED_PENDING_ROOT_SCOPE_FRESH_VECTOR_AND_ACTUAL",source_resource_gate="PASS_CONDITIONAL_ON_ROOT_SCOPE_AND_EXPLICIT_SAME_VECTOR",actual_resource_gate="NOT_RUN",checks=len(checks),input_count=len(refs),candidate_HDF=h,candidate_MF=m,prepare_ref=H["prepare_ref"],producer_ref=H["producer_caller_ref"],choice_ref=H["choice_ref"],calling_contract_ref=H["calling_contract_ref"],five_future_paths_absent=True,current_canonical_read_or_held=False,author_controls_retained=128,author_controls_new_or_repeated=13,original_failures_preserved=[933,934],new_failures=[],all_other_r2_caller_bytes_and_AST_unchanged=True,source21_closure_only_changed=True,new_producer_packet_and_ModeDecision_required=True,actual_source_guard_held=True,actual_Git_Go_SQL_Native_API_model_consumer=False,formal_acceptance=False,execution_grant=False,STOP_FINAL=True))
 print(json.dumps(dict(status="SOURCE_ACCEPTED_PENDING_ROOT_SCOPE_FRESH_VECTOR_AND_ACTUAL",checks=len(checks),inputs=len(refs),actual_source_guard_held=True,current_canonical_read_or_held=False,future_paths_absent=True,new_failures=[])),flush=True)
finally:
 cleanup=guard.close();save("source-guard.fixed.cleanup.json",cleanup)
 assert cleanup["closed"] and not cleanup["errors"] and cleanup["retained_handles_count"]==0
