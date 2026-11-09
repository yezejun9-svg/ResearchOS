from pathlib import Path
import json,hashlib,re,shutil
out=Path(__file__).resolve().parent;root=out.parent
run=root/'product-v1-owned-verification-20261104/runs/product-v1-native-rpc-b2-tests-01'
wt=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-native-rpc-wiring-20261105')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
def cp(src,rel):
 p=out/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,p)
for name in ['RESULT.json','stdout.raw','stderr.raw','CONSUMED.json']:cp(run/name,'actual-test01/'+name)
result=read(run/'RESULT.json')
for row in result['raw']:assert sha(run/row['file'])==row['sha256']
assert result['scope_sha256']=='56f150e2dacf932110ca470f7702b2e41138915489b9ab3194ff7adca0096fd9'
support=['migrations/sqlite/0016_runtime_qualification.sql','internal/domain/runtime_qualification.go','internal/domain/context.go','internal/domain/client_workspace_write_authority_windows_test.go']
for rel in support:cp(wt/rel,'binding-lifecycle/'+rel)
prior=root/'product-v1-native-rpc-wiring-rev3-review-20261105/review-report.json'
assert sha(prior)=='42ed1a729c0ed74eaaabc66eb4b0033b466849c4ad32a7c76c9bf2b28d6625d5'
cp(prior,'prior-review-unmodified.json')
rev3=root/'product-v1-native-rpc-wiring-rev3-tests-20261105'
cp(rev3/'MANIFEST.json','candidate/MANIFEST.json')
cp(rev3/'source/internal/domain/runtime_harness_windows_test.go','candidate/runtime_harness_windows_test.go')
report={
 'schema':'researchos.independent-actual-fixture-correction-review.v1',
 'decision':'TEST_FIXTURE_CORRECTION_REQUIRED_NOT_PRODUCT_FAILURE_PROOF',
 'formal_increment':0,'product_increment':0,
 'supersedes_claims_in':str(prior),
 'preserved_prior_report_sha256':sha(prior),
 'candidate_test_sha256':sha(rev3/'source/internal/domain/runtime_harness_windows_test.go'),
 'support_source_sha256':{rel:sha(wt/rel) for rel in support},
 'actual':{'scope_sha256':result['scope_sha256'],'result_sha256':sha(run/'RESULT.json'),'stdout_sha256':sha(run/'stdout.raw'),'status':result['status'],'root_exit_code':result['root_exit_code'],'job_total_processes':result['job_total_processes'],'job_active_zero':result['job_active_zero'],'stop_proved':result['stop_proved'],'forced_termination_attempts':result['terminate_job_attempts']+result['terminate_original_root_attempts'],'input_drift':result['input_drift'],'errors':result['errors'],'top_level_pass':3,'top_level_fail':1,'subtest_pass':10,'subtest_fail':2,'skip':0,'consumed_no_replay':True},
 'correction':{
  'reviewer_error':'The rev3 source review asserted that its test helper replaced the current binding with a valid new profile, and prematurely marked the coverage gap closed. The reviewer read currentRuntimeBinding but missed the existing BEFORE UPDATE database trigger. That static assertion and source-level gap-closure conclusion are withdrawn. The original report is retained byte-for-byte.',
  'actual_binding_behavior':'0016_runtime_qualification.sql creates runtime_bindings_frozen BEFORE UPDATE, aborting with runtime binding immutable. The actual test failed at UPDATE with SQLite 1811 before reaching its new-current-binding validity assertion. It therefore did not exercise the intended replacement at BeforeModelTurn.',
  'scope_of_immutability':'The observed and inspected invariant is the existing UPDATE prohibition and application insert-once binding lifecycle. This report does not claim every conceivable raw SQL DELETE/REPLACE operation is prevented by that one trigger. Tests must retain the real protections and must not bypass them to manufacture a scenario.',
  'no_bypass_observed':'These results expose test assumptions and an overstrong review conclusion; they do not demonstrate that production admitted revoked authority or that a Native/model prompt was sent.'
 },
 'diagnostic_events':[
  {'origin_key':'native-rpc-b2-tests-01:immutable-binding-test-assumption','classification':'ACTUAL_FIXTURE_FAILURE_REVIEW_ASSUMPTION_CORRECTED','detail':'sealed_binding fails at UPDATE with runtime binding immutable (1811). The replacement-valid assertion is not reached. Reviewer withdraws the prior claim that this source demonstrated a valid current binding replacement; the immutable trigger remains intact.'},
  {'origin_key':'native-rpc-b2-tests-01:owner-inspection-auth','classification':'ACTUAL_FIXTURE_POSTCONDITION_AUTH_FAILURE','detail':'owner reaches the final harnessViewFixture read after its callback-failure/zero-authorization/no-marker assertions, then receives FORBIDDEN because the Host principal is still foreign. This is the expected read-authorization gate conflicting with the test inspection helper; the subtest as a whole remains failed.'}
 ],
 'recommended_counterexamples':[
  {'case':'binding_immutable','method':'In an isolated fixture transaction, attempt the forbidden UPDATE and assert the specific immutability error. Preserve the trigger. Roll back any newly sealed unused artifact, re-read the original ref/hash/technical/owner tuple and assert it is unchanged. Since authority did not change, a subsequent positive callback is acceptable and must be labeled as unchanged-authority control, not a rejection test.'},
  {'case':'profile_revoked','method':'After BeforeResume, use the established fixture lifecycle from client_workspace_write_authority_windows_test.go: clone the currently bound Artifact, mark validity REVOKED, bump its revision, persist through service.put. Leave runtime_bindings and the Task/dispatch reference untouched. Assert the new Artifact version exists and currentRuntimeBinding now rejects the old frozen reference; then release BeforeModelTurn and require error, zero authorization, no marker and no relaunch.'},
  {'case':'owner','method':'Keep the foreign Host principal while asserting BeforeModelTurn rejection, no marker and zero authorization. For the later history read, explicitly assert the expected FORBIDDEN, or restore only the test authority after those negative assertions and read history; do not weaken production authentication. Distinguish that restoration from the final-turn authorization phase.'}
 ],
 'lifecycle_explanation':[
  'ensureRuntime creates a runtime binding with INSERT. Existing repository fixtures explicitly document that a replacement profile belongs to a distinct RuntimeRegistration; it is not an UPDATE of an existing binding.',
  'currentRuntimeBinding validates the immutable reference and calls effective. effectiveGraph compares its historical referenced revision with the current Artifact revision and rejects changed revision (STALE_INPUT) before the later validity check. A new revoked Artifact version therefore supplies a meaningful current-admissibility counterexample without replacing the binding.',
  'The production BeforeModelTurn callback reaches currentRuntimeBinding through harnessGate/currentDispatchAdmission/nativeHarnessAdmission, so revocation tests the actual production path.',
  'A failure in the old sealed_binding test triggers its cleanup release of the fixture channel; do not infer zero accepted callback from this failed case. The fixture is in-process and writes no Native/model prompt.'
 ],
 'pending_blockers':['Preserve failed test01 and prior reports, implement separately frozen fixture corrections, independently inspect them, and obtain a newly scoped Root-controlled result.','Distinct Commit-call and partial journal I/O failures remain untested; previous artifact INSERT rollback coverage must not be relabeled as those cases.'],
 'review_execution':{'go_tests':0,'native_cli':0,'app':0,'model':0,'product_source_writes':0,'D_writes':0}
}
(out/'correction-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
files=sorted(p.relative_to(out).as_posix() for p in out.rglob('*') if p.is_file() and p.name not in ['archive-file-list.json','SHA256SUMS.json'])
(out/'SHA256SUMS.json').write_text(json.dumps({rel:sha(out/rel) for rel in files},indent=2)+'\n',encoding='utf-8')
(out/'archive-file-list.json').write_text(json.dumps({'root':str(out),'files':files+['SHA256SUMS.json']},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'report_sha256':sha(out/'correction-report.json'),'archive_sha256':sha(out/'archive-file-list.json'),'archive_files':len(files)+1,'result_sha256':sha(run/'RESULT.json')},indent=2))
