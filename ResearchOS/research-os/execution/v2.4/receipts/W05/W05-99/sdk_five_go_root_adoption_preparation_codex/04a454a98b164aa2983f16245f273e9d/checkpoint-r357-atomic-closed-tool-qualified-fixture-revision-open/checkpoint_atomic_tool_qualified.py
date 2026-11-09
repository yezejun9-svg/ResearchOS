import sys
sys.dont_write_bytecode=True
import json,hashlib,types
from pathlib import Path
from datetime import datetime,timezone
R=Path(r"D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
def pin(path):
 path=Path(path).resolve();raw=path.read_bytes()
 return dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def verify(v):
 actual=pin(v["path"]);assert actual["sha256"]==v["sha256"].removeprefix("sha256:") and actual["bytes"]==v["bytes"]
 return actual
def save(name,value):
 with (O/name).open("xb") as f:f.write((json.dumps(value,ensure_ascii=True,indent=2)+"\n").encode("utf-8"))
 return pin(O/name)
def module(path):
 path=Path(path).resolve();m=types.ModuleType("root_cp357_"+path.stem);m.__file__=str(path)
 exec(compile(path.read_bytes(),str(path),"exec"),m.__dict__);return m
cp=R/"execution/v2.4/checkpoint.json";ow=R/"execution/v2.4/path_ownership.json"
pair=[pin(cp),pin(ow)];old=[cp.read_bytes(),ow.read_bytes()]
assert pair[0]["sha256"]=="9476bb385b95f5ed992d20b23171270d0c0525f22d2afaf5137f79ee00bc3f52"
assert pair[1]["sha256"]=="48c5641956b5f22bb48f7775e46d90494bd95944027f55070e430e207a506452"
before=json.loads(old[0]);assert before["revision"]==356 and len(before["failure_counters"])==806
assert before["project_id"]=="aede0678-7308-43dc-b9f2-cfe3d90cfdfb" and before["head"]=="adc460c2138528f163f7fdab5e8d81dde157b7fb"
others=[R/"execution/v2.4"/(n+".json") for n in ("step_state","commands")];others_before=[p.read_bytes() for p in others]
CPREVIEW=B/"checkpoint_r356_independent_review_codex/862a694ebe2f42ec8a102b6377936b95"
OBS=B/"public_observed_owned_three_independent_review_codex/3366bf0c368f4ae28efe9924c74c37d3"
WR=B/"w04_frozen_resource_independent_review_codex/05c0c29c21ff4365a2190d2bc18e4aca"
WA=B/"w04_two_case_actual_independent_review_codex/fcb649a4852c460280c3f79b7427bc26"
ATOM=B/"atomic_publication_actual_independent_review_codex/00060c91ce6e4dea8ab0cab37bae3c70"
TOOL=B/"official_test2json_resource_independent_review_codex/fd737b147f004cb4be2e57a0f85d9c4e"
Q1R=B/"typed_runtime_goal_fixture_independent_review_codex/6e7346b6ae004d219524f5049151f9fd"
Q2=B/"typed_runtime_goal_fixture_jsonl_revision_codex/3adf21aec07c4b5db6eb2fcf317f85e9"
REV=B/"native_migration_atomic_publication_revision_codex/1a11d9c912f7c13799a37e93"
CONFIG=B/"integration_codex/native-positive-controller-config-v2-root-0da7b5a0b3f84a13"
TBUILD=B/"integration_codex/official-test2json-resource-build-root-3e9129c5f7c9461e"
AA=B/"integration_codex/controller-atomic-publication-root-2e926de963bc46f2"
WACT=B/"integration_codex/w04-two-resource-repaired-cases-root-86149090aa0241f8"
expected={
 OBS:("b9933dce413d6663ef561c983a1742210d45e279496d19b59cd8050fdbf4da8b","a48212def5eeee8a51d8d07f8c8e01aadbae398081f435ab70541b3093b63540"),
 WR:("9675641fceb04ef601823ecbcca7e0d51b9aa037e9355942474c166b32a9f12f","304d068552632c229c014ce3260b45c4b3f6c62c7c3a2c6c827d14b8ad0c3b5f"),
 WA:("99611138de6a554079e74fb92582a86615790e9d0104b7e6d8b3e788bfb80be5","d14a12c55540206ca9087298a7c3a4c1e068b3f5d4dee52aa701c13513e5fe8d"),
 ATOM:("61d3224aa28d27df311b4e946e1f8432d237ef0af334e7fe42062ffcb183de84","9eb745b5a7abe640b5ec6653026635b8b0a36a40646496c6a778a15b2c700799"),
 TOOL:("680829e87f1c8f3854f7dbf17310ee2891006a5c5b5c7471023022c01da88354","b05e8744ca0b1661599329877354b0894d6044714d843f2a185c31267b551a02"),
 Q1R:("7e2b1d7818b6938d9f6815ab199f92daad171e433e8b09ba4422683c6ecc1a9c","cd320ab25ef0879d09499099f8428121fa7f8a16207d6ae6f3fd0d68acc857d4"),
 Q2:("9d0e393bedf1e647008cf9022081664ab7511ab6d341edeaa4831482bcd29340","65cd84d5c0b440f0c70acbb808c1960102bf03107e10aca1a83f0081f7035ca4")}
refs=[]
for d,(h,m) in expected.items():
 assert pin(d/"HDF.json")["sha256"]==h and pin(d/"MF.json")["sha256"]==m
 refs.extend([pin(d/"HDF.json"),pin(d/"MF.json")])
 members=json.loads((d/"MF.json").read_bytes())["members"]
 for v in (members.values() if isinstance(members,dict) else members):refs.append(verify(v))
assert json.loads((ATOM/"HDF.json").read_bytes())["decision"]=="ATOMIC_PUBLICATION_FINDING_CLOSED_COMPONENT_AND_POSITIVE_PUBLIC_CONFIG_PREPARED_ACCEPTED_STOP"
pending=[
 (809,CPREVIEW/"diagnostics-after-cp356.json",None,None,"Rejected model-private query argument before process; protected original input is restricted and not exported; public diagnostic metadata preserved."),
 (810,CPREVIEW/"diagnostics-after-cp356.json",None,None,"Windows206 long inline command rejected before process/write; full publicinput/error retained separately from809."),
 (811,B/"integration_codex/root-read-diagnostic-811-w04-file-name-b493176a/failure-origin.811.json",0,None,"Root guessed missing w04_context_test.go; subsequent Get-ChildItem succeeded so outer0; uncaptured inner rg exitNULL."),
 (812,WR/"diagnostic-812.json",1,None,"Readonly rg Windows literal internal/domain/import* OS123; no Python/product child."),
 (813,REV/"failure-origin.813.json",1,None,"Source construct inverse byte assertion due LF/CRLF mismatch; failed script preserved and new v2 corrected; Python exit inferred1 unless raw marker."),
 (814,B/"typed_runtime_goal_fixture_source_io_codex/814-b6832e-76618678c33e47ffb4e2ad9bd5e9c208/failure-origin.814.json",1,None,"Short fixedPython inline single quote stripping caused SyntaxError; Source sealed members unchanged; separate script recovery."),
 (815,Q1R/"failure-origin.815.json",1,None,"Readonly check NameError B before initialization; no Python exit marker, inferred1. Failed script reconstructed from exact patch deltas after edit and explicitly labeled, not original immutable file."),
 (816,WA/"diagnostics-816-817.json",1,None,"Readonly repetitive4337path resolution manually interrupted same session Ctrl-C; actualPythonNULL, no target rerun."),
 (817,WA/"diagnostics-816-817.json",1,None,"Independent checker asserted actual missing held inventory.GoRef; outer1/actualPythonNULL; linear corrected read preserves coverage gap.")]
refs += [pin(p) for _,p,_,_,_ in pending]
for d,names in ((CONFIG,("controller.public.config.json","controller-config.prepared.json","config-input-source-guard.cleanup.actual.json","original-tool-io.json")),
 (TBUILD,("resource-build.closed.json","selected-official-compiler-inputs.json","base-source-guard.cleanup.actual.json","selected-source-guard.cleanup.actual.json","binary-source-guard.cleanup.actual.json","original-tool-io.json")),
 (AA,("validation.closed.json","inner.closed.json","original-tool-io.json")),
 (WACT,("validation.closed.json","original-tool-io.json"))):
 refs += [pin(d/n) for n in names]
tool_actual=json.loads((TBUILD/"resource-build.closed.json").read_bytes());refs.append(verify(tool_actual["binary_ref"]))
gp=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
tp=B/"mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/canonical_transactions.py"
assert pin(gp)["sha256"]=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"
assert pin(tp)["sha256"]=="094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9"
refs += [pin(gp),pin(tp),pin(Path(__file__)),pin(sys.executable)]
refs=list({p["path"].casefold():p for p in refs}.values())
gm=module(gp);guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);guard.acquire(refs)
tm=module(tp)
def transform(c,o):
 assert c["revision"]==356 and o["revision"]==168
 keys={x.get("origin_key") for x in c["failure_counters"]}
 for n,p,outer,py,description in pending:
  r=pin(p);key=hashlib.sha256((r["sha256"]+"#"+str(n)).encode()).hexdigest()
  assert key not in keys;keys.add(key)
  c["failure_counters"].append(dict(origin_key=key,evidence_ref=r,original_payload=dict(observed_ordinal=n,immutable_origin_ref=r,actual_outer_exit=outer,actual_python_exit=py,actual_native_exit=None,diagnostic=description,private_input_exported=False if n==809 else None),counted_once=True,counter_reset=False,automatic_retry=False))
 assert c["failure_counters"][:806]==before["failure_counters"] and len(c["failure_counters"])==815
 c.update(expected_previous_revision=356,revision=357,updated_at=datetime.now(timezone.utc).isoformat(),updated_by="codex:/root")
 c["work_in_progress"].update(r357_registered_failure_count=815,r357_highest_observed_diagnostic_ordinal=817,
 mu_sdk_cp356_independent_review_ref=pin(CPREVIEW/"HDF.json"),
 mu_sdk_observed_three_actual_review_ref=pin(OBS/"HDF.json"),
 mu_sdk_atomic_publication_state="SOURCE_AND_FOUR_PUBLIC_COMPONENT_ACTUAL_INDEPENDENTLY_ACCEPTED_FINDING_CLOSED_CONTROLLER_OVERALL_AND_NATIVE_CASES_PENDING",
 mu_sdk_atomic_publication_actual_ref=pin(AA/"validation.closed.json"),mu_sdk_atomic_publication_independent_ref=pin(ATOM/"HDF.json"),
 mu_sdk_native_positive_public_controller_v2_ref=pin(CONFIG/"controller.public.config.json"),
 mu_sdk_native_positive_public_controller_v2_prepared_ref=pin(CONFIG/"controller-config.prepared.json"),
 mu_sdk_native_positive_controller_frozen_inputs=4083,
 mu_sdk_native_positive_hostile_flow_state="NOT_STARTED_PUBLIC_CONFIGURATION_V2_PREPARED_FUTURE_CHILD_CLOSURE_AND_EXACT_LAUNCH_SIGN_OWNER_CASE_RESULTS_NOT_ACCEPTED",
 mu_sdk_w04_frozen_resource_review_ref=pin(WR/"HDF.json"),mu_sdk_w04_two_observed_actual_ref=pin(WACT/"validation.closed.json"),
 mu_sdk_w04_two_observed_review_ref=pin(WA/"HDF.json"),
 mu_sdk_w04_two_state="OBSERVED_2PASS0FAIL0SKIP_AND_JOB_CLOSED_ONLY_WRAPPER_GOREF_NOT_HELD_AND_BUILTIN_TEST2JSON_CHAIN_PARTIAL_LEGACY_CHILD_PYTHON_DEPENDENCIES_PARTIAL_CURRENT_CASE_NO_LEGACY_PYTHON_NOT_FORMAL",
 mu_sdk_official_test2json_resource_ref=tool_actual["binary_ref"],mu_sdk_official_test2json_build_ref=pin(TBUILD/"resource-build.closed.json"),
 mu_sdk_official_test2json_independent_ref=pin(TOOL/"HDF.json"),
 mu_sdk_official_test2json_state="TOOL_COMPILATION_COMPONENT_ACCEPTED_102_STD_PACKAGES759_SELECTED_INPUTS_TWO_JOBS_CLOSED_BINARY_NOT_YET_EXECUTED_FUTURE_USE_REGUARD_SHARED_GOCACHE_NOT_ALL_FRESH_REBUILD",
 mu_sdk_typed_fixture_first_source_review_ref=pin(Q1R/"HDF.json"),mu_sdk_typed_fixture_jsonl_revision_handoff_ref=pin(Q2/"HDF.json"),
 mu_sdk_typed_fixture_state="FIRST_SOURCE_REJECTED_CHILD_SUBSTRING_Q2_SEALED_STATIC_REVIEW_FOUND_DIGEST_PREFIX_AND_GO127_OUTPUTTYPE_Q3_MINIMAL_SOURCE_REPAIR_ACTIVE_NO_TARGET_GO",
 mu_sdk_source_authors_active=["backup_regression_resources:Q3_minimal_typed_fixture_helper_digest_and_OutputType"],
 mu_sdk_source_readonly_reviewers_active=["typed_fixture_source_review:Q2_REQUEST_CHANGES_then_Q3","prepared_native_authority_review:canonical_and_native_scope_available"],
 mu_sdk_next_action="Root guarded single isolated positive native fixture only with concrete release/grant snapshots and Root decisions, independent typed/schema/nativeID inspection before fixture release; eight negatives separate. In parallel Q3 strict official test2json helper Source review then fresh composition and10leaf actual with full heldGo/tool references. OriginalDB/business/adoption/abandonment/history16 and fresh model trial remain separate; no original once/deadline/counter reset.")
 c["note"]="CP357 preserves806 oldfailure prefix and registers809-817once=>815registered/high817. public3 observed normal/cancel/timeout trueindieaccepted4Jobsclosed. Atomic Source+4publicactual accepted and Medium publicationrace componentCLOSED; no controlleroverall/Owner/native9 acceptance. Purepositive configv2 includes4083 actual selected input refs includingGoRef+50pyc, trueindiepreparedonly; no nativecase/signature/privatekey read. W04observed2PASS andJobclosed trueindieacceptedscopepartial: unheldGoRef+implicitbuiltin test2json chain common; legacy Pythonchild dependencies unpinned; currentcase nolegacyPython. Rootexplicit officialtest2json builtin Source102packages759selectedfiles actual2GoJobs0/closed+base101/selected760/binary1guardsclosed; independentTOOL_COMPILATIONonly, sharedcachemayreuse, notool execution. Q1typed Source changed onlytests preserved181calls/20Test/196lexicalif(190t+6fmt) but childsubstringrejected; Q2 usesstrictJSONL but staticDigestprefix/officialOutputType defects; Q3minimalrepairactive, no10leafnewactual. FULL1261PASS25FAIL4SKIP remainsFAILED/immutable; old267+24matchingunitaccepted unchanged. OriginalRunQUEUED/TaskRUNNING/PREPAREDdispatch/financialnotclosed/providerNULL/recordedEffects0/onceconsumed300sexpired untouched, no newmodeltrial. Main product/head/identity/13trackeddirty/indexempty unchanged,OW168/SS/CMunchanged. GoalACTIVE6of22historical/0of42formal; nevercompletion."
 return c,o
try:
 transaction=tm.update_pair(pair,transform,O,"activate")
 assert ow.read_bytes()==old[1] and [p.read_bytes() for p in others]==others_before
 assert json.loads(cp.read_bytes())["revision"]==357
finally:
 cleanup=guard.close();save("source_guard.cleanup.actual.json",cleanup)
 assert cleanup["closed"] and not cleanup["errors"] and cleanup["retained_handles_count"]==0
proof=save("canonical_pair.actual.json",dict(transaction=transaction,checkpoint_ref=pin(cp),ownership_ref=pin(ow),old806prefix_preserved=True,registered_failures=815,highest_observed_diagnostic_ordinal=817,formal_acceptance=False))
resume=save("RESUME.r357.original.json",dict(schema="researchos.root-resume-atomic-component-closed-tool-resource-qualified.v1",repository_root=str(R),checkpoint_ref=pin(cp),checkpoint_revision=357,ownership_revision=168,head=before["head"],project_id=before["project_id"],current_card="W05-99",historical_accepted_parents=6,current_formal_accepted=0,formal_required=42,registered_failures=815,highest_observed_diagnostic_ordinal=817,native9_executed=False,atomic_publication_component_finding_closed=True,official_test2json_ref=tool_actual["binary_ref"],positive_public_controller_config_ref=pin(CONFIG/"controller.public.config.json"),typed_fixture_Q3_source_active=True,original_trial_business_open=True,original_trial_provider_requests=None,financial_closed=False,once_consumed=True,original_clock_expired=True,counter_reset=False,completion_asserted=False,proof_ref=proof,next_action="Guarded isolated native positive concrete review; Q3 helperSource review/fresh10leaf actual; original business separate; no counters/trial reset."))
manifest=save("manifest.json",dict(members=[pin(p) for p in O.iterdir() if p.is_file()]))
handoff=save("handoff.json",dict(status="CHECKPOINT_SAVED_ATOMIC_COMPONENT_CLOSED_TOOL_QUALIFIED_NATIVE_AND_TYPED_FIXTURE_ACTUAL_OPEN",checkpoint_ref=pin(cp),resume_ref=resume,manifest_ref=manifest,formal_acceptance=False))
print(json.dumps(dict(checkpoint_ref=pin(cp),resume_ref=resume,handoff_ref=handoff,registered_failures=815,highest_observed_diagnostic_ordinal=817)),flush=True)
