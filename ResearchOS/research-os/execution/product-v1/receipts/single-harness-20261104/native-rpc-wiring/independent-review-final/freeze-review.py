from pathlib import Path
import json,hashlib,re,shutil,sys
out=Path(__file__).resolve().parent;root=out.parent
original=root/'product-v1-native-rpc-wiring-author-20261105'
rev4=root/'product-v1-native-rpc-wiring-rev4-tests-20261105'
author_final=Path(sys.argv[1])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
def cp(src,rel):
 p=out/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,p)
m=read(original/'MANIFEST.json');r=read(rev4/'MANIFEST.json')
assert sha(author_final/'MANIFEST.json')=='6e4219f609d2690043401b4ac55bf00af9fd1e6e03c0b7269655e12d465cd1fd'
fm=read(author_final/'MANIFEST.json')
assert sha(author_final/'forward.patch')==sha(author_final/'changes.patch')==fm['forward_patch_sha256']
assert sha(author_final/'inverse.patch')==fm['inverse_patch_sha256']
for row in fm['files']:
 assert sha(author_final/'source'/row['path'])==row['source_sha256']
 if row['baseline_sha256']!='ABSENT_BEFORE':assert sha(author_final/'baseline'/row['path'])==row['baseline_sha256']
for row in fm['tested_b1_sources']:
 assert sha(author_final/'tested-b1-overlay/source'/row['name'])==sha(Path(row['tested_source_ref']))==row['sha256']
assert sha(author_final/'tested-b1-overlay/overlay.json')==fm['b1_overlay_sha256']
for i,row in enumerate(fm['test_runs'],1):
 for f in row['files']:
  assert sha(author_final/'test-runs'/('test%02d'%i)/f['file'])==f['sha256']
assert sha(original/'MANIFEST.json')=='8588e7b60b302c5df8e88d4cadc0e2dc3bd1e94033fa18985317109a73767d22'
assert sha(rev4/'MANIFEST.json')=='9e7196a771ffb76b977608e5972a05a2757780cdfb0eecb2f62d4736f9ec5487'
pins={}
for item in m['files']:
 rel=item['path'];p=original/'source'/rel
 assert sha(p)==item['source_sha256']
 if rel==r['supersedes_test_file_only']:
  p=rev4/'source'/rel;assert sha(p)==r['source_test_sha256']
 pins[rel]=sha(p);cp(p,'selected-source/'+rel)
 assert sha(author_final/'source'/rel)==pins[rel],rel
assert {x['path']:x['source_sha256'] for x in fm['files']}==pins
for folder,label in [(original,'original-freeze'),(rev4,'rev4-freeze'),(author_final,'author-final')]:
 for name in ['MANIFEST.json','changes.patch']:
  cp(folder/name,label+'/'+name)
rr=root/'product-v1-owned-verification-20261104'
run=rr/'runs/product-v1-native-rpc-b2-tests-02'
scopepath=rr/'scopes/product-v1-native-rpc-b2-tests-02.json'
scope=read(scopepath);result=read(run/'RESULT.json')
assert sha(scopepath)==result['scope_sha256']=='34f4a80eba2c14de9aec53ec2f6972bf1c05cf099d880bc916e420a3898087f7'
for row in scope['inputs']:assert sha(Path(row['path']))==row['sha256'],row['path']
for rel,h in pins.items():
 rows=[x for x in scope['inputs'] if x['path'].replace('\\','/').endswith('/'+rel)]
 assert len(rows)==1 and rows[0]['sha256']==h,rel
for row in result['raw']:assert sha(run/row['file'])==row['sha256']
assert result['root_exit_code']==0 and result['stop_proved'] and result['job_active_zero']
assert not result['errors'] and not result['input_drift']
assert result['terminate_job_attempts']==result['terminate_original_root_attempts']==0
log=(run/'stdout.raw').read_text(encoding='utf-8')
passed=re.findall(r'^\s*--- PASS: (\S+)',log,re.M)
assert sum('/' not in x for x in passed)==4 and sum('/' in x for x in passed)==13
assert '--- FAIL:' not in log and '--- SKIP:' not in log
for runname in ['product-v1-native-rpc-b2-tests-01','product-v1-native-rpc-b2-tests-02']:
 for name in ['RESULT.json','stdout.raw','stderr.raw','CONSUMED.json']:cp(rr/'runs'/runname/name,'runs/'+runname+'/'+name)
cp(scopepath,'runs/test02-scope.json')
cp(root/'product-v1-native-rpc-combined-overlay02/overlay.json','runs/test02-overlay.json')
prior=root/'product-v1-native-rpc-b2-test01-correction-review-20261105/correction-report.json'
cp(prior,'prior-correction-report.json')
report={
 'schema':'researchos.independent-source-fixture-review.v1',
 'decision':'APPROVED_SOURCE_FIXTURE_ONLY',
 'approval_scope':'B2 exact eight files only; no blanket approval of B1 transport/parser, real Native qualification or model execution.',
 'source_head':m['base_head'],
 'selected_candidate':str(author_final),
 'candidate_manifest_sha256':sha(author_final/'MANIFEST.json'),
 'source_sha256':pins,
 'formal_increment':0,'product_increment':0,
 'pending_blockers':[],
 'separate_integration_gates':['B1 remains independently security-reviewed and blocked until its fixes and final source/fixture review pass. This result used the frozen B1 rev3 overlay as a compilation dependency only; it does not approve that implementation.','A final combined overlay with approved B1 is a separate integration check. Native qualification and any model run require their own authorization and evidence.'],
 'integrity':{'original_eight_file_freeze_verified':True,'rev4_test_overlay_verified':True,'author_final_all_eight_source_files_match':True,'author_final_baseline6_and_patches_and_overlay8_and_both_raw_receipt_copies_verified':True,'actual_test02_source_input_count':len(scope['inputs']),'all_test02_input_hashes_match_at_review':True,'mismatches':[]},
 'source_boundary_review':[
  'Canonical RPC PREPARATION_READY permits queueing/preparation only. Public rev2 schema remains unchanged; execution/workspace_read_scope/cancellation remain UNVERIFIED and enforcement_verified=false. Ordinary exec production readiness remains unavailable.',
  'Distinct RPC V3 policy/command/transport/helper and nonce-profile-template fields bind internal profiles. Existing task runtime/profile references are not silently upgraded or replayed. Historical reads remain independent of current execution eligibility.',
  'BeforeModelTurn reenters harnessGate/currentDispatchAdmission for owner/source/seal/lease/epoch and checks RUNNING Task, dispatch worker/locator and persisted PID/creation/Job. Fresh source snapshot, path and revision are compared against the exact binding supplied to driver Start.',
  'The fixed private native-turn-authorization.json is exclusively created, bounded, fully written, synchronized and closed. The file persists on partial or DB artifact/commit error, preventing reuse. Its audit projection is not qualification and cannot reconstruct B1 private permission to write a turn.',
  'No monetary resource_effects or terminal observation_hash is repurposed. Host production composition selects ordinary NewCodexRPC without a qualifier, with no fallback to exec and no public READY import.'
 ],
 'actual_test02':{
  'scope_sha256':result['scope_sha256'],'result_sha256':sha(run/'RESULT.json'),'stdout_sha256':sha(run/'stdout.raw'),
  'status':result['status'],'root_exit_code':0,'top_level_pass':4,'subtest_pass':13,'skip':0,
  'job_total_processes':result['job_total_processes'],'job_active_zero':True,'stop_proved':True,'force_attempts':0,'input_drift':False,
  'callback_model':'A trusted in-process fake invokes actual Submit/Scan/runHarness callbacks. Channel synchronization confirms BeforeResume success before each mutation. It creates no Native process and writes no model prompt; turns counts accepted Host callbacks only.',
  'binding_immutable_positive':'Installed BEFORE UPDATE trigger rejects the attempted profile_ref change. After rollback the original ref/hash/technical tuple is unchanged. Because authority remains valid, exactly one callback/marker/LOG is expected and observed through the passing assertions.',
  'profile_revoked_negative':'The current bound Artifact is cloned, marked REVOKED, bumped and stored as a new version. runtime_bindings is left untouched. currentRuntimeBinding rejects its old frozen reference and BeforeModelTurn rejects with zero accepted callback and no marker. This is real admissibility revocation, not replacement of an immutable binding.',
  'owner_negative':'The foreign Host principal persists through both callback completion and a denied Get. Only after workers finish and foreign Get returns an error is the original test authority restored for history inspection. Saved callback failure, zero accepted authorization and no-marker assertions still apply; restoration cannot reopen that consumed run.',
  'other_observed_cases':['one_turn','duplicate','source_rebind','source_revision','policy_readiness','auth_metadata','process_identity','lease_epoch','cancel','artifact_fault'],
  'artifact_fault':'Artifact INSERT trigger aborts the authorization LOG transaction after marker creation. The marker remains; repeated callback fails with os.ErrExist, no LOG escapes rollback, and another Scan does not start a second run.'
 },
 'diagnostic_events':[
  {'origin_key':'native-rpc-wiring:before-model-turn-counterexamples-missing','classification':'RESOLVED_B2_SOURCE_FIXTURE','detail':'Actual test02 now passes the real coordinator callback matrix, including immutable-binding control and legal profile revocation. No claim of current binding replacement remains.'},
  {'origin_key':'native-rpc-b2-tests-01:immutable-binding-test-assumption','classification':'RESOLVED_FIXTURE_WITH_PRIOR_FAILURE_PRESERVED','detail':'Test01 failure and reviewer correction remain archived. Rev4 preserves the installed immutable trigger and separates unchanged-authority positive control from Artifact-version revocation negative control. Author alias native-rpc-b2:immutable-binding-fixture refers to this same event; do not double count.'},
  {'origin_key':'native-rpc-b2-tests-01:owner-inspection-auth','classification':'RESOLVED_FIXTURE_WITH_PRIOR_FAILURE_PRESERVED','detail':'Foreign Get is explicitly denied after callback completion, then authority is restored only for history inspection. Author alias native-rpc-b2:owner-inspection-principal refers to this same event; do not double count.'}
 ],
 'coverage_limits':['A distinct tx.Commit failure and partial journal write/fsync failure are not injected by these tests; those fail-closed paths are statically inspected only.','The selected -run set covers four top-level tests, not the whole repository or all legacy Harness fixtures.','B2 in-process callback tests do not prove B1 native OS capture ordering, live permit synchronization, actual child Job lifecycle, effective filesystem permissions or qualification.','The earlier review assertion that immutable binding replacement was valid remains withdrawn; this final report relies on actual rev4/test02 behavior instead.'],
 'review_execution':{'go_test_reruns':0,'native_cli':0,'app':0,'model':0,'D_writes':0,'product_source_writes':0}
}
(out/'review-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
files=sorted(p.relative_to(out).as_posix() for p in out.rglob('*') if p.is_file() and p.name not in ['archive-file-list.json','SHA256SUMS.json'])
(out/'SHA256SUMS.json').write_text(json.dumps({rel:sha(out/rel) for rel in files},indent=2)+'\n',encoding='utf-8')
(out/'archive-file-list.json').write_text(json.dumps({'root':str(out),'files':files+['SHA256SUMS.json']},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'report_sha256':sha(out/'review-report.json'),'archive_sha256':sha(out/'archive-file-list.json'),'archive_files':len(files)+1,'candidate_manifest_sha256':sha(author_final/'MANIFEST.json')},indent=2))
