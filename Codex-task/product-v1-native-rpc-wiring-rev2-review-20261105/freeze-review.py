from pathlib import Path
import json,hashlib,shutil
out=Path(__file__).resolve().parent
root=out.parent
original=root/'product-v1-native-rpc-wiring-author-20261105'
revision=root/'product-v1-native-rpc-wiring-rev2-tests-20261105'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((original/'MANIFEST.json').read_text(encoding='utf-8'))
r=json.loads((revision/'MANIFEST.json').read_text(encoding='utf-8'))
assert sha(original/'MANIFEST.json')==r['original_freeze_manifest_sha256']=='8588e7b60b302c5df8e88d4cadc0e2dc3bd1e94033fa18985317109a73767d22'
assert sha(revision/'MANIFEST.json')=='880ea955b6d9d53470ebe1ea2938b283f719f434829ed4237b5fc09605866215'
assert sha(revision/'changes.patch')==r['patch_sha256']
def cp(src,rel):
 p=out/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,p)
pins={}
for item in m['files']:
 rel=item['path'];p=original/'source'/rel
 assert sha(p)==item['source_sha256']
 if rel==r['supersedes_test_file_only']:
  assert sha(p)==r['baseline_test_sha256']
  cp(p,'prior-test/'+rel)
  p=revision/'source'/rel
  assert sha(p)==r['source_test_sha256']
 pins[rel]=sha(p)
 cp(p,'selected-source/'+rel)
for base,label in [(original,'original-freeze'),(revision,'rev2-freeze')]:
 for name in ['MANIFEST.json','changes.patch']:
  cp(base/name,label+'/'+name)
cp(revision/'FROZEN.txt','rev2-freeze/FROZEN.txt')
report={
 'schema':'researchos.independent-source-prereview.v1',
 'decision':'SOURCE_REVIEW_CONDITIONAL_PENDING_COVERAGE_AND_CONTROLLED_TESTS',
 'source_head':m['base_head'],
 'selected_candidate':str(original),
 'selected_test_overlay':str(revision),
 'candidate_manifest_sha256':sha(original/'MANIFEST.json'),
 'test_overlay_manifest_sha256':sha(revision/'MANIFEST.json'),
 'source_sha256':pins,
 'formal_increment':0,'product_increment':0,
 'pending_blockers':[
  'The case named policy_seal only mutates driver readiness PolicyIdentity. Add or separately demonstrate a current database RuntimeProfile/current binding change after BeforeResume so the existing currentDispatchAdmission sealed-snapshot comparison is exercised.',
  'Final source-fixture approval awaits Root-controlled combined B1/B2 test execution and review of the exact final source overlay. No Go test execution is evidenced by this review.'
 ],
 'diagnostic_events':[
  {'origin_key':'native-rpc-wiring:before-model-turn-counterexamples-missing','classification':'PARTIALLY_RESOLVED_TEST_SOURCE_NOT_RUN','detail':'Rev2 now invokes the actual coordinator BeforeResume and BeforeModelTurn callbacks with channel-ordered mutations, closing the former entirely untested callback path at source level. However policy_seal changes only a driver readiness snapshot, not the database sealed profile/current binding. The remaining seal-mutation coverage is required; no runtime authorization bypass has been demonstrated.'}
 ],
 'integrity':{'original_exact8_verified':True,'rev2_one_file_overlay_verified':True,'production_delta_from_original':False,'patch_hash_verified':True},
 'test_source_assessment':{
  'sequencing':'Real Submit and Scan enter runHarness. The trusted in-process driver invokes real BeforeResume, reports its result through resumed, then waits on proceed. The test mutates state only after the first callback succeeds and closes proceed to release the real BeforeModelTurn callback. Channel synchronization orders mutated driver/authority fields before the second callback. No Native process or prompt is produced by this driver.',
  'positive_and_duplicate':'one_turn requires exactly one accepted callback, one durable marker and one sealed authorization LOG. duplicate invokes the same callback again and requires os.ErrExist, then checks another Scan did not start a second run. These are Host authorization observations, not model turns.',
  'dynamic_negative_cases':{'owner':'Changes the current Host principal provider to foreign.','source_rebind':'Changes source to another existing temporary directory and increments revision.','source_revision':'Changes revision while retaining the path.','policy_seal':'Actually changes only the readiness snapshot binary identity; should be named policy_readiness.','auth_metadata':'Changes driver authentication to LOGGED_OUT.','process_identity':'Changes evidence creation identity after the persisted BeforeResume process tuple.','lease_epoch':'Changes the persisted Run lease epoch.','cancel':'Calls the public Harness Cancel path using the current Task revision and Run/epoch.'},
  'artifact_fault':'A SQLite BEFORE INSERT Artifact trigger aborts artifact creation after exclusive marker creation. Assertions require zero accepted callbacks, the marker retained, duplicate callback rejected with os.ErrExist, and no committed authorization LOG. This is artifact INSERT/transaction rollback coverage, not a Commit-call failure test.',
  'public_truthfulness':'The actual capabilities response is checked for can_submit=true while all three verification values remain UNVERIFIED and enforcement_verified=false.',
  'bounds_and_cleanup':'The test bounds arrival at BeforeResume by ten seconds and releases its channel on subsequent test failure; coordinator workers are joined before result reads. Root outer process/time bounds remain necessary for deadlock/failure containment.',
  'not_covered':'No runtime assertions yet exist because these tests have not run. This in-process fake cannot prove B1 OS pipe ordering, live private permit, prompt-write cancellation synchronization, actual process Job cleanup, real qualification, native grants, direct Commit failure, or partial file-write/fsync failure.'
 },
 'production_review':[
  'The selected production bytes are identical to original B2. Shared canonical readiness permits preparation only; public verification and enforcement stay unchanged.',
  'BeforeModelTurn uses harnessGate/currentDispatchAdmission for current owner, runtime profile, source snapshot, lease and epoch; it also checks persisted process tuple, worker/locator, RUNNING Task, and exact original driver path/revision. Static review finds these intended checks present even though the database-seal mutation case remains untested.',
  'Exclusive fixed private marker is bounded, completely written, synchronized and closed before the authorization LOG transaction commits. Marker is retained after errors and cannot deserialize into qualification or a B1 live permit. No unrelated monetary or terminal observation fields are repurposed.',
  'RPC V3 routing is distinct from historical exec; current Task runtime/profile identity is checked before claiming, and historical read paths are unchanged. Production Host uses ordinary RPC constructor without a qualifier; no model authorization is derived from PREPARATION_READY.',
  'No production authorization bypass was identified in this bounded static review. This finding does not approve the still-changing B1 implementation or actual execution.'
 ],
 'observations':['Original freeze and rev2 are preserved separately. The old policy_seal name is recorded accurately, rather than counted as a successful sealed-profile mutation test.','An explicit DB Commit failure and partial journal I/O injection remain untested; fail-closed return paths and retained marker are supported by static inspection only.'],
 'execution':{'go_tests':0,'native_cli':0,'app':0,'model':0,'product_source_writes':0,'D_writes':0}
}
(out/'review-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
files=sorted(p.relative_to(out).as_posix() for p in out.rglob('*') if p.is_file() and p.name not in ['archive-file-list.json','SHA256SUMS.json'])
(out/'SHA256SUMS.json').write_text(json.dumps({rel:sha(out/rel) for rel in files},indent=2)+'\n',encoding='utf-8')
(out/'archive-file-list.json').write_text(json.dumps({'root':str(out),'files':files+['SHA256SUMS.json']},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'report_sha256':sha(out/'review-report.json'),'archive_sha256':sha(out/'archive-file-list.json'),'archive_files':len(files)+1},indent=2))
