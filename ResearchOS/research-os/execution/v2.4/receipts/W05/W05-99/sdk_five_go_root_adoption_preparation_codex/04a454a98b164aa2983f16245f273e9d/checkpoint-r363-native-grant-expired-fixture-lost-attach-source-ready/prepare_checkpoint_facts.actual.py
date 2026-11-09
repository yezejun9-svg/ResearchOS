import sys
sys.dont_write_bytecode=True
import json,hashlib,types
from pathlib import Path
from datetime import datetime,timezone
R=Path("D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(n,v):
 with (O/n).open("xb") as f:f.write((json.dumps(v,ensure_ascii=True,indent=2)+"\n").encode())
 return pin(O/n)
S=B/"integration_codex/native-broker4-positive-serve-root-1791513411000";C=B/"integration_codex/native-broker4-controller-config-root-1791513411000"
outer=json.loads((S/"serve-outer.invocation.json").read_bytes());native=json.loads((C/"controller-runtime/test.invocation.json").read_bytes())
assert outer["result"]["actual_exit"]==1 and native["result"]["actual_exit"]==1
assert not outer["result"]["timed_out"] and not native["result"]["timed_out"]
for value in (outer["result"],native["result"]):
 j=value["job_cleanup"];assert j["active_processes_last_observed"]==0 and j["primary_exit_confirmed"] and j["handles_closed"] and j["job_idle_confirmed"] and not j["errors"] and not j["termination_requested"]
closed=json.loads((C/"controller-runtime/controller.closed.json").read_bytes());assert closed["job_and_guards_closed"] and not closed["worker_still_alive"] and not closed["fixture_release_approval_exists"]
fixture=json.loads((C/"harness-facts/fixture.public.json").read_bytes());assert not Path(fixture["database"]).exists() and not Path(fixture["root"]).exists()
terminal=json.loads((S/"original-root-terminal-tool-io.json").read_bytes());assert terminal["actual_outer_exit"]==terminal["explicit_python_exit"]==1
active=pin(S/"ACTIVE.NATIVE.T10.grant-expired.original.json")
origin892=save("failure-origin.892.json",dict(schema="researchos.root-native-failed-original-execution.v1",ordinal=892,diagnostic="T10 grant signed once but expired without publication; main wait and cleanup reuse the same expired 20min context, naturally fail exit1, temporary fixture lost without wholeSQL or specificrelease",actual_outer_exit=1,actual_python_exit=1,actual_native_exit=1,original_active_tool_io_ref=active,original_terminal_tool_io_ref=pin(S/"original-root-terminal-tool-io.json"),outer_invocation_ref=pin(S/"serve-outer.invocation.json"),native_invocation_ref=pin(C/"controller-runtime/test.invocation.json"),outer_closed_ref=pin(S/"serve-outer.closed.json"),controller_closed_ref=pin(C/"controller-runtime/controller.closed.json"),native_stdout_ref=pin(C/"controller-runtime/test.stdout.raw"),native_stderr_ref=pin(C/"controller-runtime/test.stderr.raw"),controller_owner=dict(pid=outer["result"]["owned_child_pid"],creation_FILETIME_decimal=str(outer["result"]["creation_time_100ns"])),go_primary=dict(pid=native["result"]["owned_child_pid"],creation_FILETIME_decimal=str(native["result"]["creation_time_100ns"])),fixture_exists_at_review=False,fixture_SQL_after_not_observed=True,specific_fixture_release_not_completed=True,original_apply_and_replay_not_started=True,grant_signed_once=True,grant_published=False,TTL_refreshed=False,formal_acceptance=False,counter_reset=False,automatic_retry=False))
p362=B/"sdk_five_go_root_adoption_preparation_codex/04a454a98b164aa2983f16245f273e9d/checkpoint-r362-native-failed-closed-current-target-results"
af=B/"session_attach_contract_fixture_revision_codex/af-1a11e3e93437fe089b15fdf6a164840"
afr=B/"session_attach_contract_fixture_independent_review_codex/afr-20261009-attach-fixture-source-review"
cp362r=B/"checkpoint_r362_independent_review_codex/current_target_actual_review_01"
u=B/"integration_codex/python-broker4-public-units-root-1791512710000"
pre=B/"native_broker4_prelaunch_actual_independent_review_codex/824d231b423344aeacbb84cf60976311"
helper=B/"root_native_concrete_phase_helpers_revision_codex/nh-1a11e7f5205729390aaee9f47b28ce6"
h20=B/"historical20_upgrade_contract_readonly_codex/h20-contract-20261009-source-review"
sparse=B/"integration_codex/attach-fixture-two-parent-sparse-root-source-1791516205000"
loc={876:af,877:p362,878:af,879:u,880:cp362r,881:u,882:af,883:cp362r,884:cp362r,885:C,886:afr,887:afr,888:B/"historical20_resource_route_readonly_codex/current_target_actual_review_01",889:pre,890:p362,891:pre,892:O,893:helper,894:sparse,895:h20}
exits={876:(1,None,None),877:(2,2,None),878:(None,None,None),879:(1,1,None),880:(0,None,None),881:(0,None,None),882:(1,1,None),883:(1,1,None),884:(0,0,None),885:(0,None,None),886:(1,1,None),887:(1,1,None),888:(0,None,None),889:(1,1,None),890:(1,None,None),891:(0,0,None),892:(1,1,1),893:(0,None,None),894:(1,1,128),895:(0,None,None)}
desc={876:"AF read missing spec/v2.4 resource",877:"Root task_packet wrong repo tools path",878:"AF JavaScript parse rejected before tool execution",879:"Root owned helper received str streams; no child was created and no unit test executed",880:"CP362 review guessed absent RESUME.md",881:"Root read first U10 stdout/stderr that were never created",882:"AF lexer did not account for two observed gofmt semicolon differences",883:"CP362 review assumed historical origin_key field",884:"CP362 first false finding confused28 leaves with30 terminals including2 parents",885:"Root guessed API8 basename",886:"AF review guessed RequestEnvelope instead of CommandEnvelope",887:"AF review UTF8 file decoded using GBK",888:"H20 read guessed absent backup_restore.go",889:"C10 review classified Environment mapping as RawPin",890:"Root guessed I9 isolation script basename",891:"C10 review false findings on CRLF and actual enrollment-program role in one invocation",892:"Native T10 signed grant expired unpublished and expired cleanup context removed fixture; no wholeSQL/specificrelease",893:"Source helper read null.GetType twice in one PowerShell invocation",894:"T11 full worktree checkout ENOSPC Git128; original Source target not reached",895:"H20 research rg guessed absent ops/recovery_root path"}
diagnostics=[]
for n in range(876,896):
 ref=pin(loc[n]/("failure-origin."+str(n)+".json"));oe,pe,ne=exits[n]
 diagnostics.append(dict(ordinal=n,origin_ref=ref,actual_outer_exit=oe,actual_python_exit=pe,actual_native_exit=ne,description=desc[n]))
reviews=[]
for tag,path,h,m in [
 ("CP362_INDEPENDENT_CANONICAL_CONSISTENCY",cp362r,"HDF.json","MF.json"),
 ("AF_SOURCE_ACCEPTED_PENDING_ROOT_ACTUAL",afr,"HDF.json","MF.json"),
 ("T11_CALLER_SOURCE_ACCEPTED_PENDING_ROOT_ACTUAL",B/"attach_fixture_two_parent_caller_independent_review_codex/t11r-20261009-source-review","HDF.json","MF.json"),
 ("T10_PRELAUNCH_COMPONENT_ONLY",pre,"HDF.json","MF.json"),
 ("T10_FAILED_CLOSURE_FIXTURE_LOST",B/"native_broker4_actual_failure_independent_review_codex/7a3f2b80b7bd43d8907d91de469c6b2e","handoff.json","manifest.json"),
 ("HISTORY20_RESOURCE_PRODUCT_GAP",B/"historical20_resource_route_readonly_codex/current_target_actual_review_01","HDF.json","MF.json"),
 ("HISTORY20_LEGAL_ROUTE_CONTRACT_GAPS",h20,"HDF.json","MF.json")]:
 reviews.append(dict(scope=tag,handoff_ref=pin(path/h),manifest_ref=pin(path/m)))
actual_refs=[pin(S/n) for n in ("serve-outer.closed.json","serve-outer.invocation.json","original-root-terminal-tool-io.json","ACTIVE.NATIVE.T10.grant-expired.original.json")]
actual_refs += [pin(C/"controller-runtime"/n) for n in ("controller.closed.json","test.invocation.json","test.stdout.raw","test.stderr.raw","sign-release.receipt.json","publish-release.receipt.json","sign-grant.receipt.json")]
actual_refs += [pin(u/"revision-explicit-binary-handles"/n) for n in ("validation.closed.json","unit-tests.invocation.json") if (u/"revision-explicit-binary-handles"/n).is_file()]
actual_refs += [pin(u/n) for n in ("original-root-tool-io.json","failure879.exit-qualification.json")]
iso=B/"integration_codex/attach-fixture-current-two-parent-isolation-root-t11-1a11e7f5205729390aaee9f47b28ce6"
actual_refs += [pin(p) for p in iso.iterdir() if p.is_file()]
facts=save("checkpoint.execution.facts.json",dict(schema="researchos.root-cp363-grant-expired-fixture-lost-source-ready.v1",formal_acceptance=False,diagnostics=diagnostics,reviews=reviews,actual_refs=actual_refs,registered_before=873,registered_after=893,highest_observed_ordinal=895,next_failure_ordinal=896,work_in_progress=dict(mu_sdk_r363=dict(native_T10=dict(status="FAILED_NATURAL_EXIT1_JOB_GUARDS_CLOSED",go_native_exit=1,outer_python_exit=1,expired_grant_signed_once=True,grant_published=False,apply_and_replay="NOT_STARTED",fixture_lost_before_wholeSQL=True,specific_fixture_release="NOT_COMPLETED",independent_review_scope="FAILED_EXECUTION_CLOSURE_ONLY",original_io_ref=pin(S/"original-root-terminal-tool-io.json")),broker4_pure_unit_tests=dict(pass_count=17,fail_count=0,skip_count=0,actual_closed_ref=pin(u/"revision-explicit-binary-handles/validation.closed.json"),native_acceptance=False),attach_T11=dict(original_Source_independently_accepted=True,original_isolation_status="FAILED_ENOSPC_GIT128",original_source_overlay=False,tests="NOT_EXECUTED",sparse_revision_source_ref=pin(sparse/"revision-exact-paths/HDF.json"),sparse_revision="PENDING_INDEPENDENT_SOURCE_REVIEW_AND_ROOT_ACTUAL"),native_phase_helpers_source=dict(handoff_ref=pin(helper/"HDF.json"),independent_review="PENDING",actual_generated_approvals=0),history20_full_upgrade="OPEN_PRODUCT_20_TO21_AND_RELEASE_SHAPE_CHAIN_GAPS",old24_observation_fence_compatibility="BLOCKED_CORRESPONDING_BRANCH_ONLY",original_trial_business="OPEN",original_trial_provider_requests=None,financial_closed=False,historical_accepted_parents=6,current_formal_accepted=0,required_parents=22,required_formal=42,counter_reset=False)),checkpoint_note="CP363 preserves all873 old failure records and registers876..895 exactly once. Broker4 public17 units passed. NativeT10 failed naturally exit1 after unpublished expired grant; fixture deleted by reused expired cleanup ctx, no afterSQL/specificrelease or positive acceptance. T11 Source approved but fullcheckout failed ENOSPC; sparse Source revision awaits review. Historical20 product upgrade and historical/old24 compatibility branches remain open. Original trial business/financial open, provider requests unknown.22 parents/42current formal requirements unchanged.",next_action="Review sparse Root caller then create source-only detached worktree and validate exactly two changed attach parents. Fix retained cleanup context and independently review perphase approval helpers before fresh nativecase; preserve signed T10 and old failures without TTLrefresh. Implement legitimate20→21/full history route without fake ledger."))
print(json.dumps(dict(facts_ref=facts,diagnostics=20,registered_after=893)),flush=True)

