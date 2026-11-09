import sys
sys.dont_write_bytecode=True
import json,hashlib
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os"); B=R/"execution/v2.4/receipts/W05/W05-99"; O=Path(__file__).resolve().parent
def pin(p):
 p=Path(p).resolve(); raw=p.read_bytes(); return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(n,v):
 with (O/n).open("xb") as f:f.write((json.dumps(v,ensure_ascii=True,indent=2)+"\n").encode())
 return pin(O/n)
def obj(p):return json.loads(Path(p).read_bytes())
cp=pin(R/"execution/v2.4/checkpoint.json")
assert (cp["sha256"],cp["bytes"])==("9e67531bd3b1f0fbd9bc5e239b3a240a39f668db2d367714a399ba4fd8bfeb25",4223052)
old=obj(cp["path"]); assert old["revision"]==363 and len(old["failure_counters"])==893
sparse=B/"sparse_checkout_independent_review_codex/r2-1791516205000-84568553"
nh=B/"root_native_concrete_helpers_independent_review_codex/nhr-20261009-source-review"
entries=obj(nh/"original-tool-io.json"); assert isinstance(entries,list)
nhfail={v["ordinal"]:v for v in entries if v.get("ordinal") in (897,898)}
assert set(nhfail)=={897,898}
origins={}
origins[896]=pin(sparse/"failure-896-original-tool-io.json")
for n in (897,898):
 v=nhfail[n]
 assert v["tool"]=="history.search_contents" and v.get("python_exit") is None and v.get("native_exit") is None
 origins[n]=save("failure-origin."+str(n)+".json",dict(schema="researchos.original-reviewer-tool-schema-failure.v1",ordinal=n,actual_outer_exit=None,actual_python_exit=None,actual_native_exit=None,original_tool_io=v,whole_original_io_ref=pin(nh/"original-tool-io.json"),counter_reset=False,attempt_count=1))
cl=B/"native_retained_cleanup_context_revision_codex/cl-1a11e7f5205729390aaee9f47b28ce6"
h20=B/"historical20_upgrade_source_codex/h20-1a11ebe661670a1a49d0ea22092604a"
for n,p in ((899,cl),(900,h20),(901,h20)):origins[n]=pin(p/("failure-origin."+str(n)+".json"))
origins[902]=pin(O/"failure-origin.902.json")
exitqual={896:(1,1,None),897:(None,None,None),898:(None,None,None),899:(1,1,None),900:(1,None,None),901:(0,None,None),902:(1,None,None)}
descs={896:"Sparse review mechanical KeyError on prior aggregate guard schema; no product execution",897:"history.search_contents rejected unexpected arguments before execution",898:"history.search_contents second original rejected unexpected arguments before execution",899:"Cleanup Source author expected84 assertion count but observed90 before candidate write",900:"H20 author read guessed absent T9/cmd; rg2 inferred only, no actual rg marker",901:"H20 author read guessed absent domain/project.go; rg2 inferred only, no actual rg marker",902:"Root read guessed absent RESUME.md; actual handoff ref identifies RESUME.r363.original.json; no Python/native ran"}
diagnostics=[]
for n in range(896,903):
 oe,pe,ne=exitqual[n]
 diagnostics.append(dict(ordinal=n,origin_ref=origins[n],actual_outer_exit=oe,actual_python_exit=pe,actual_native_exit=ne,inferred_rg_exit=2 if n in (900,901) else None,description=descs[n]))
review_specs=[
("CP363_CANONICAL_CONSISTENCY_ACCEPTED_NO_PRODUCT_AUTHORITY","checkpoint_r363_independent_review_codex/cp363-5be86210"),
("T11_TWO_PARENT_ACTUAL_COMPONENT_ACCEPTED_NO_FORMAL_AUTHORITY","attach_fixture_t11_actual_independent_review_codex/t11actual-69bd7fde"),
("N12_ACTUAL_C12_SOURCE_COMPONENT_ACCEPTED_NO_NATIVE_AUTHORITY","native_n12actual_c12source_independent_review_codex/ac-20261009-review"),
("CL_SOURCE_ACCEPTED_PENDING_LIVE_NATIVE_CLEANUP","native_retained_cleanup_context_independent_review_codex/clr-20261009-source-review"),
("CTL4_N12_SOURCE_ACCEPTED_PENDING_ROOT_ACTUAL","native_ctl4_n12_independent_review_codex/cn-20261009-source-review"),
("NH1_SOURCE_ACCEPTED_PENDING_ROOT_ACTUAL","root_native_concrete_helpers_independent_review_codex/nhr1r-20261009-source-review"),
("SPARSE_R2_SOURCE_ACCEPTED_LATER_ACTUAL_T11","sparse_checkout_independent_review_codex/r2-1791516205000-84568553/retry-schema")]
reviews=[]
for scope,rel in review_specs: reviews.append(dict(scope=scope,handoff_ref=pin(B/rel/"HDF.json"),manifest_ref=pin(B/rel/"MF.json")))
t11=B/"integration_codex/attach-fixture-two-parent-sparse-target-root-1791516205000"
t11s=B/"integration_codex/attach-fixture-two-parent-sparse-root-source-1791516205000/revision-exact-paths"
n12=B/"integration_codex/native-cleanup-compile-source-root-1791516889000"
c12=B/"integration_codex/native-cleanup-controller-source-root-1791517434000"
nh1=B/"root_native_concrete_phase_helpers_revision_codex/nhr1-1a11e7f5205729390aaee9f47b28ce6"
ctl4=B/"native_controller_retained_window_revision_codex/ctl4-1a11e7f5205729390aaee9f47b28ce6"
actual_refs=[pin(t11/"validation.closed.json"),pin(t11s/"postseal-root-actual-original-io.json"),pin(n12/"validation.closed.json"),pin(n12/"postseal-root-actual-original-io.json")]
for p in (h20,c12,nh1,ctl4,cl):
 actual_refs += [pin(p/"HDF.json"),pin(p/"MF.json")]
facts=dict(schema="researchos.root-cp364-component-actuals-source-ready.v1",formal_acceptance=False,diagnostics=diagnostics,reviews=reviews,actual_refs=actual_refs,registered_before=893,registered_after=900,highest_observed_ordinal=902,next_failure_ordinal=903,
work_in_progress=dict(mu_sdk_r364=dict(
checkpoint363_independently_accepted=True,
attach_T11=dict(status="FIVE_TERMINAL_PASS_COMPONENT_ONLY",parent_count=2,leaf_count=3,pass_count=5,fail_count=0,skip_count=0,other52_parents_not_run=True,other132_declared_not_scope=True,current_source_count=58,actual_closed_ref=pin(t11/"validation.closed.json"),independent_review_ref=reviews[1]["handoff_ref"],main_adopted=False,formal_acceptance=False),
N12=dict(status="FOUR_PROGRAMS_TAGGED_TEST_AND35_UNITS_PASS_COMPONENT_ONLY",parent_count=3,leaf_count=32,pass_count=35,fail_count=0,skip_count=0,source_count=43,compile_packages=364,build_input_count=3793,whole_product_count=599,embed_count=38,live_native_cases=0,actual_closed_ref=pin(n12/"validation.closed.json"),independent_review_ref=reviews[2]["handoff_ref"],live_four_minute_cleanup_qualified=False),
native_cleanup_CTL4_NH1=dict(source_accepted=True,live_native_four_minute_retention="NOT_RUN",CTL4_inner_seconds=1560,Go_global_seconds=1500,main_seconds=1200,cleanup_seconds=240,grant_seconds=240,S10_observed_outer_seconds=1440,new_C12_outer_required_seconds=1800,NHR001_barehex_inspection_Source_fixed=True),
C12=dict(source_preparer_accepted=True,prepared_config_actual="NOT_RUN",final_prelaunch_review="PENDING",fresh_case_id="t12cl149d6f49321",config_builder_source_handoff_ref=pin(c12/"HDF.json"),source_review_ref=reviews[2]["handoff_ref"],root_manual_phase_calls="PENDING_SOURCE_AND_FINAL_REVIEW",new_trial=False),
history20=dict(candidate_handoff_ref=pin(h20/"HDF.json"),candidate_manifest_ref=pin(h20/"MF.json"),source="SEALED_PENDING_NONAUTHOR_REVIEW",production_explicit_A20_to_plain21_candidate=True,Go_SQL_actual="NOT_RUN",full20_to24_chain="OPEN",genuine_historical_owner_programs="OPEN",historical_B_session_installation="OPEN",owner_credential_product_flow="OPEN",Main_adopted=False),
native_T10=dict(status="FAILED_NATURAL_EXIT1_CLOSED_FIXTURE_LOST",grant_signed_once=True,grant_published=False,wholeSQL_after=False,specific_fixture_release=False,TTL_refreshed=False),
original_trial_business="OPEN",original_trial_provider_requests=None,financial_closed=False,historical_accepted_parents=6,current_formal_accepted=0,required_parents=22,required_formal=42,counter_reset=False)),
checkpoint_note="CP364 preserves all893 old failure records and registers896..902 exactly once. T11 two parents/three leaves5PASS and N12 three parents/32 leaves35PASS independently accepted as components only; Main and formal acceptance unchanged. Cleanup+CTL4+NH1 Sources accepted, C12 config Source accepted but config actual/prelaunch/live Native pending. Old S10 actual outer1440 seconds is corrected in new C12 Source to required1800, never edits old evidence. H20 explicit20to21 candidate sealed pending source review/GoSQL; full20to24/genuine historical release and Owner flow/session installation OPEN. T10 lost fixture not recreated; original paid trial/business/financial OPEN and provider requests unknown.",
next_action="Prepare reviewed C12 config against CP364; freeze and independently review fresh Root manual serve/API/perphase request Sources before one fresh native positive case. Independently review and actually compile/test H20 explicit A20to21 candidate; preserve all historical templates and genuine fixture gaps. Continue 22parents/42formal gates without resets.")
fr=save("checkpoint.execution.facts.json",facts)
base=O.parent/"checkpoint-r363-native-grant-expired-fixture-lost-attach-source-ready/checkpoint_native_fixture_lost.atomic.py"
source=base.read_text(encoding="utf-8")
changes=[
("researchos.root-cp363-grant-expired-fixture-lost-source-ready.v1","researchos.root-cp364-component-actuals-source-ready.v1"),
('("84c970d86ab96b78a7621595839005f68a440fc9a540d3b619500c7cbed2669b",4195882)','("9e67531bd3b1f0fbd9bc5e239b3a240a39f668db2d367714a399ba4fd8bfeb25",4223052)'),
('==362','==363'),('==873','==893'),('range(876,896)','range(896,903)'),
('==893 and c["failure_counters"][:873]','==900 and c["failure_counters"][:893]'),
('expected_previous_revision=362,revision=363','expected_previous_revision=363,revision=364'),
('r363_registered_failure_count=893,r363_highest_observed_diagnostic_ordinal_at_cutoff=895,r363_next_failure_ordinal_at_cutoff=896,mu_sdk_r363_facts_ref=fr,later_diagnostics_observed_after_cutoff=[896,897,898],root_next_failure_ordinal_live=899','r364_registered_failure_count=900,r364_highest_observed_diagnostic_ordinal_at_cutoff=902,r364_next_failure_ordinal_at_cutoff=903,mu_sdk_r364_facts_ref=fr,later_diagnostics_observed_after_cutoff=[],root_next_failure_ordinal_live=903'),
('["revision"]==363\nfinally:','["revision"]==364\nfinally:'),
('old873_failure_records_semantic_equal','old893_failure_records_semantic_equal'),('old873_raw_array_prefix_preserved','old893_raw_array_prefix_preserved'),
('registered_failures=893,highest_observed_diagnostic_ordinal_at_cutoff=895,later_diagnostics_pending=[896,897,898],live_next_failure_ordinal=899','registered_failures=900,highest_observed_diagnostic_ordinal_at_cutoff=902,later_diagnostics_pending=[],live_next_failure_ordinal=903'),
('RESUME.r363.original.json','RESUME.r364.original.json'),('researchos.root-resume-grant-expired-fixture-lost-source-ready.v1','researchos.root-resume-component-actuals-source-ready.v1'),
('checkpoint_revision=363','checkpoint_revision=364'),
('registered_failures=893,highest_registered_ordinal=895,next_failure_ordinal_at_cutoff=896,later_diagnostics_pending=[896,897,898],live_next_failure_ordinal=899','registered_failures=900,highest_registered_ordinal=902,next_failure_ordinal_at_cutoff=903,later_diagnostics_pending=[],live_next_failure_ordinal=903'),
('T11_actual_tests="NOT_RUN"','T11_actual_tests="FIVE_TERMINAL_PASS_COMPONENT_ONLY",N12_actual_tests="35_TERMINAL_PASS_COMPONENT_ONLY",C12_prepared_actual="NOT_RUN",H20_Source="SEALED_PENDING_NONAUTHOR_REVIEW"'),
('T11_sparse_source="WAIT_FINAL_INDEPENDENT_PINS_THEN_ROOT_ACTUAL"','T11_sparse_source="ACTUAL_INDEPENDENTLY_ACCEPTED_COMPONENT_ONLY"'),
('CHECKPOINT_SAVED_T10_FAILED_FIXTURE_LOST_T11_SPARSE_SOURCE_READY_PENDING_ACTUAL','CHECKPOINT_SAVED_T11_N12_COMPONENT_ACTUALS_C12_H20_SOURCE_READY'),
('registered_failures=893,highest_registered_ordinal=895','registered_failures=900,highest_registered_ordinal=902')]
import re
applied=[]
for a,b in changes:
 count=source.count(a); assert count>0,(a,count)
 positions=[m.start() for m in re.finditer(re.escape(a),source)]
 source=source.replace(a,b); applied.append(dict(before=a,after=b,count=count,positions=positions))
# Reversibility is checked in reverse order; derived code parses without executing.
inverse=source
for c in reversed(applied):
 a,b=c["before"],c["after"]
 for i,p in reversed(list(enumerate(c["positions"]))):
  q=p+i*(len(b)-len(a)); assert inverse[q:q+len(b)]==b
  inverse=inverse[:q]+a+inverse[q+len(b):]
assert inverse==base.read_text(encoding="utf-8")
import ast
ast.parse(source)
with (O/"checkpoint_component_actuals.atomic.py").open("xb") as f:f.write(source.encode())
save("writer-source-provenance.json",dict(base_ref=pin(base),changes=applied,whole_inverse_equal=True,new_ref=pin(O/"checkpoint_component_actuals.atomic.py"),native_SQL=False))
print(json.dumps(dict(facts_ref=fr,writer_ref=pin(O/"checkpoint_component_actuals.atomic.py"),diagnostics=7,registered_after=900)))

