from pathlib import Path
import hashlib,json,shutil
out=Path(__file__).resolve().parent
root=out.parent
repo=Path('D:/作品集/ResearchOS/research-os')
author=root/'product-v1-native-rpc-wiring-author-20261105'
api=root/'product-v1-native-rpc-runtime-author-20261105/shared-api-v2'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((author/'MANIFEST.json').read_text(encoding='utf-8'))
assert sha(author/'MANIFEST.json')=='8588e7b60b302c5df8e88d4cadc0e2dc3bd1e94033fa18985317109a73767d22'
def cp(src,rel):
 p=out/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,p)
for name in ['MANIFEST.json','changes.patch','FROZEN.txt','README.txt']:cp(author/name,'candidate/'+name)
pins={}
worktree=repo/manifest['source_worktree']
drift=[]
for row in manifest['files']:
 rel=row['path'];pins[rel]=row['source_sha256']
 assert sha(author/'source'/rel)==row['source_sha256'],rel
 cp(author/'source'/rel,'candidate/source/'+rel)
 if sha(worktree/rel)!=row['source_sha256']:drift.append(rel)
 if row['baseline_sha256']!='ABSENT_BEFORE':
  assert sha(author/'baseline'/rel)==row['baseline_sha256'],rel
  cp(author/'baseline'/rel,'candidate/baseline/'+rel)
for rel,h in manifest['shared_api_v2'].items():
 assert sha(api/rel)==h,rel
 cp(api/rel,'shared-api-v2/'+rel)
scopepath=repo/'execution/product-v1/receipts/single-harness-20261104/native-rpc-wiring'
scope=json.loads((scopepath/'scope.json').read_text(encoding='utf-8'))
for name in ['scope.json','scope.amendment01.json']:cp(scopepath/name,'contract/'+name)
assert sha(scopepath/'scope.amendment01.json')==manifest['scope_amendment_sha256']
for rel,h in scope['contract_pins'].items():
 p=repo/rel;assert sha(p)==h;cp(p,'contract/'+p.name)
report={
 'schema':'researchos.independent-source-prereview.v1',
 'decision':'PRE_REVIEW_TEST_COVERAGE_CHANGES_REQUIRED',
 'source_head':manifest['base_head'],
 'selected_candidate':str(author),
 'candidate_manifest_sha256':sha(author/'MANIFEST.json'),
 'source_sha256':pins,
 'shared_api_sha256':manifest['shared_api_v2'],
 'formal_increment':0,'product_increment':0,
 'integrity':{'frozen_source_files_verified':8,'baseline_files_verified':6,'shared_api_files_verified':3,'worktree_drift_at_read':drift,'contract_pins_verified':True},
 'pending_blockers':[
  'Add focused domain tests that actually invoke BeforeModelTurn after BeforeResume: positive exactly once; dynamic owner/source snapshot/path/revision/seal/epoch/cancel rejection; journal/artifact/commit failure retains consumption and cannot reauthorize or relaunch.',
  'Review the final combined B1/B2 source and Root-controlled Go test evidence before final source approval. No such execution occurred or was observed by this pre-review.'
 ],
 'diagnostic_events':[
  {'origin_key':'native-rpc-wiring:before-model-turn-counterexamples-missing','classification':'REQUIRED_SOURCE_FIXTURE_COVERAGE_GAP','detail':'Current B2 frozen domain additions test only policy identity; existing fake exec never invokes BeforeModelTurn. The standalone exclusive journal test cannot establish final authorization callback behavior or DB-failure retention. Author confirmed no unarchived callback tests. This is a verification gap, not an observed permission bypass.'},
  {'origin_key':'native-rpc-wiring-prereview01:default-text-decoding','classification':'REVIEW_CAPTURE_DIAGNOSTIC_RESOLVED','detail':'Reviewer evidence-copy script first decoded the UTF-8 scope with the Windows default codec, causing JSON invalid-escape at its Chinese path. Raw bytes showed valid UTF-8 JSON; explicit UTF-8 decoding fixed capture. Earlier console contract rendering was likewise reread explicitly as UTF-8. No product write, test execution, source change or scope repair occurred.'}
 ],
 'static_observations':[
  'harnessReadiness calls shared Evaluate with canonical transport identity. PREPARATION_READY permits preparation queueing with the explanatory reason code; public verification stays UNVERIFIED and enforcement_verified=false. No new public DTO field is introduced.',
  'RPC seals use distinct V3 sandbox/command and exact transport/helper/nonce-template identifiers. The nonce permission template is researchos-readonly-${PROFILE_NONCE}. Full policy matching includes requested-config and binary hashes; dispatch admission pins current profile against original dispatch.',
  'Production Host selects NewCodexRPC with OS user-derived normal home and no qualification provider; no fallback to ordinary exec. In the shared API snapshot, ordinary production exec remains unverified and RPC stops with QUALIFICATION_REQUIRED before the Host model-turn callback when its qualifier is nil.',
  'BeforeModelTurn reopens harnessGate for current owner, runtime admission, source snapshot, lease and epoch. It checks Task RUNNING, dispatch STARTED/worker/journal locator and exact persisted PID/creation/Job identity, then checks fresh source against original driver path and revision.',
  'The private fixed native-turn-authorization.json uses exclusive creation, bounded complete write, Sync and Close. Partial files are retained. Artifact/commit errors return failure after file consumption, so repeating the callback encounters the exclusive marker. Marker bytes are an audit projection, not a qualification boolean or a recreated live permit.',
  'No changes misuse resource_effects monetary semantics or observation_hash. No new scheduler, DB schema, root write grant or helper-directory wildcard is introduced by these eight B2 files.',
  'Historical task runtime/profile identity is compared before claiming the new RPC route, preventing silent upgrades. Get/List/history reader bodies remain unchanged in the supplied patch.',
  'The host final authorization transaction is not claimed atomic against later revocation. B1 must perform its own live cancellation/protocol/one-use permit check immediately before the write.',
  'The old shared-api-v2 B1 run body pauses capture processing during qualifier/Host callbacks and unlocks before writing intent and turn; Root and B1 author were notified. B1 is being revised separately, so this old dependency snapshot is not approved as a final implementation.',
  'An initial console read rendered Chinese contract text incorrectly; it was reread explicitly as UTF-8. No source or frozen evidence was changed.'
 ],
 'execution':{'go_tests_run':0,'native_cli_invocations':0,'app_launches':0,'model_invocations':0,'D_writes':0,'source_mutations':0},
 'limits':'Static pre-review only. No B1/B2 Go test has been claimed executed; no Native effective policy, qualification, model turn or product acceptance is established.'
}
(out/'prereview-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
files=sorted(p.relative_to(out).as_posix() for p in out.rglob('*') if p.is_file() and p.name not in ['archive-file-list.json','SHA256SUMS.json'])
(out/'SHA256SUMS.json').write_text(json.dumps({rel:sha(out/rel) for rel in files},indent=2)+'\n',encoding='utf-8')
(out/'archive-file-list.json').write_text(json.dumps({'root':str(out),'files':files+['SHA256SUMS.json']},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'report_sha256':sha(out/'prereview-report.json'),'archive_sha256':sha(out/'archive-file-list.json'),'archive_files':len(files)+1,'worktree_drift_at_read':drift},indent=2))
