import pathlib,json,hashlib
P=pathlib.Path;N=P(__file__).resolve().parent;B=N.parent.parent
A=B/'integration_codex/history20-five-parent-sparse-target-root-h20v-1a11ebe6616'
I=B/'integration_codex/history20-five-parent-sparse-isolation-root-h20v-1a11ebe6616'
C=B/'integration_codex/history20-five-parent-sparse-root-source-h20v-1a11ebe661670a1a49d0ea22092604a'
def pin(p):
 p=P(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(p):return json.loads(P(p).read_bytes())
def save(n,v):
 with (N/n).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
 return pin(N/n)
c=read(N/'checks.json');g=read(N/'sourceguard.final.json')
assert c['passed']==25791 and c['failed']==0 and c['input_count']==5005 and g['closed'] and not g['errors'] and g['retained_handles_count']==0
mf=save('MF.json',dict(schema='researchos.independent-failed-actual-review-manifest.v1',members=[pin(p) for p in sorted(N.iterdir()) if p.is_file()]))
hf=save('HDF.json',dict(schema='researchos.h20-failed-actual-independent-review.v1',status='FAILED_ACTUAL_CLOSURE_VERIFIED_FIXTURE_ROOT_CAUSE_CONFIRMED',isolation_ref=pin(I/'isolation.ready.json'),failed_actual_ref=pin(A/'validation.closed.json'),failure_origin_ref=pin(C/'postseal-failure-origin.914.json'),original_failure_ordinal=914,original_validation_outer_exit=1,original_validation_python_exit=1,official_test2json_primary_exit=1,individual_descendant_test_binary_exit=None,actual_compile_exit=0,owned_jobs_closed=10,actual_guards_closed=7,exact_test_terminals=9,actual_PASS=8,actual_FAIL=1,actual_SKIP=0,public_upgrade_success_observed=False,matching_correct_key_or_wrong_key_crypto_observed=False,targeted_drift_guard_coverage_qualified=False,generic_migration_callback_reachability_observed=False,manifest_ref=mf,report_ref=pin(N/'report.md'),checks_ref=pin(N/'checks.json'),review_guard_ref=pin(N/'sourceguard.final.json'),checks_passed=25791,input_count=5005,reviewer_Git_Go_SQL_native_model_executed=False,canonical_CP364_unchanged=True,post_validation_Git_status_observed=False,new_failure_ordinals=[],formal_acceptance=False,overall20_to24='OPEN',guard_released=True,STOP=True,FINAL=True))
print(json.dumps(dict(HDF=hf,MF=mf)))

