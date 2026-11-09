from pathlib import Path
import json,hashlib,shutil
out=Path(__file__).resolve().parent;root=out.parent
original=root/'product-v1-native-rpc-wiring-author-20261105'
rev2=root/'product-v1-native-rpc-wiring-rev2-tests-20261105'
rev3=root/'product-v1-native-rpc-wiring-rev3-tests-20261105'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
m=read(original/'MANIFEST.json');r=read(rev3/'MANIFEST.json')
assert sha(rev3/'MANIFEST.json')=='4f9087adf2ce2262c3b3183d3c2f0a4afef8bc9ba47ccbbabcf9f2fb0b377ef8'
assert sha(original/'MANIFEST.json')==r['original_freeze_manifest_sha256']
assert sha(rev2/'MANIFEST.json')==r['rev2_manifest_sha256']
assert sha(rev3/'changes.patch')==r['patch_sha256']
def cp(src,rel):
 p=out/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,p)
pins={}
for item in m['files']:
 rel=item['path'];p=original/'source'/rel
 assert sha(p)==item['source_sha256']
 if rel==r['supersedes_test_file_only']:
  assert sha(rev2/'source'/rel)==r['baseline_test_sha256']
  p=rev3/'source'/rel;assert sha(p)==r['source_test_sha256']
 pins[rel]=sha(p);cp(p,'selected-source/'+rel)
for folder,label in [(original,'original'),(rev2,'rev2'),(rev3,'rev3')]:
 cp(folder/'MANIFEST.json',label+'/MANIFEST.json')
 cp(folder/'changes.patch',label+'/changes.patch')
cp(rev3/'FROZEN.txt','rev3/FROZEN.txt')
report={
 'schema':'researchos.independent-source-delta-review.v1',
 'decision':'APPROVED_SOURCE_DELTA_PENDING_CONTROLLED_TESTS',
 'source_head':m['base_head'],
 'selected_candidate':str(original),
 'selected_test_overlay':str(rev3),
 'candidate_manifest_sha256':sha(original/'MANIFEST.json'),
 'test_overlay_manifest_sha256':sha(rev3/'MANIFEST.json'),
 'source_sha256':pins,
 'formal_increment':0,'product_increment':0,
 'pending_blockers':['Final combined B1/B2 source-fixture approval awaits the Root-controlled Go test result and review of its exact frozen source overlay.'],
 'diagnostic_events':[{'origin_key':'native-rpc-wiring:before-model-turn-counterexamples-missing','classification':'RESOLVED_AT_TEST_SOURCE_LEVEL_EXECUTION_PENDING','detail':'Rev2 added real coordinator callback counterexamples; rev3 now adds an actual valid current sealed RuntimeProfile binding replacement after BeforeResume and accurately renames the separate readiness mutation. The previous coverage source gap is closed. This does not claim any test has passed.'}],
 'integrity':{'original_eight_frozen_source_files_verified':True,'rev2_to_rev3_test_baseline_verified':True,'rev3_test_and_patch_verified':True,'production_delta_from_original':False},
 'delta_review':[
  'Only the domain test file changes. policy_seal becomes policy_readiness, accurately describing the stale driver snapshot mutation.',
  'The new helper loads the actual Run/runtime/current profile after the channel confirms BeforeResume succeeded. It changes consent expiry to a still-future 23 hours and verifies the replacement retains canonical RPC policy identity.',
  'It authenticates the existing Owner and calls the actual sealRuntimeSetupProfile path to produce a new sealed Artifact. It asserts the new reference differs, updates the current runtime_bindings profile_ref/profile_hash, then verifies currentRuntimeBinding resolves that exact new reference without error before committing.',
  'The unchanged currentRuntimeBinding implementation checks reference hash, runtime technical hash, artifact content/effectiveness and sealed body identity; this test does not merely inject malformed bytes that any parser would reject.',
  'The original Task input and dispatch remain pinned to the prior reference. BeforeModelTurn reenters harnessGate/currentDispatchAdmission, where nativeHarnessAdmission can reject the old Task/profile mismatch before the later snapshot equality loop. The test therefore covers current valid binding replacement, without falsely claiming a specific later rejection line.',
  'The sealed_binding case inherits assertions requiring callback failure, zero accepted authorization, no marker, no model result, and no second Start after another Scan. The existing one_turn positive control establishes callback/marker/LOG eligibility for the unmodified fixture.',
  'The in-process fake uses actual coordinator callbacks and database fencing, with channel synchronization between first callback success and mutation. It never runs a Native child or writes a model prompt.'
 ],
 'remaining_coverage_limits':[
  'No independent Go test was run. Root identified combined scope 56f150e2dacf932110ca470f7702b2e41138915489b9ab3194ff7adca0096fd9 as the next controlled execution; its outcome is not inferred here.',
  'Artifact INSERT failure with rollback and retained exclusive marker is present in test source. A distinct tx.Commit failure and partial journal write/fsync failure are not implemented tests; corresponding fail-closed behavior is supported only by static inspection.',
  'These domain fixtures do not prove B1 OS capture pipe behavior, private live permit implementation, actual Job cleanup, Native qualification or effective filesystem grants. Final combined source and runtime evidence remain separate.',
  'Production remains unqualified for a model prompt. PREPARATION_READY/public can_submit only authorize preparation; verification stays UNVERIFIED and enforcement_verified=false.'
 ],
 'execution':{'go_tests':0,'native_cli':0,'app':0,'model':0,'product_source_writes':0,'D_writes':0}
}
(out/'review-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
files=sorted(p.relative_to(out).as_posix() for p in out.rglob('*') if p.is_file() and p.name not in ['archive-file-list.json','SHA256SUMS.json'])
(out/'SHA256SUMS.json').write_text(json.dumps({rel:sha(out/rel) for rel in files},indent=2)+'\n',encoding='utf-8')
(out/'archive-file-list.json').write_text(json.dumps({'root':str(out),'files':files+['SHA256SUMS.json']},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'report_sha256':sha(out/'review-report.json'),'archive_sha256':sha(out/'archive-file-list.json'),'archive_files':len(files)+1},indent=2))
