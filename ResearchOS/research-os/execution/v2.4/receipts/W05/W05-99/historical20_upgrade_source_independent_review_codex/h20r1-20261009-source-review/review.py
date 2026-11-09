import pathlib,json,hashlib,difflib
N=pathlib.Path(__file__).resolve().parent
B=N.parent.parent
C=B/'historical20_upgrade_source_codex/h20-r1-root-1791519270000-scoped-check'
O=B/'historical20_upgrade_source_codex/h20-1a11ebe661670a1a49d0ea22092604a'
P=N.parent/'h20r-20261009-source-review'
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def pin(p):
 p=pathlib.Path(p);r=p.read_bytes()
 return {'path':str(p),'sha256':hashlib.sha256(r).hexdigest(),'bytes':len(r)}
def write(n,o):
 with (N/n).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
 return pin(N/n)
checks=[];inputs={}
def ck(n,v):checks.append({'name':n,'pass':bool(v)})
def verify(r):
 a=pin(r['path']);ck('pin:'+a['path'],a['sha256']==r['sha256'].removeprefix('sha256:') and a['bytes']==r['bytes']);inputs[a['path']]=a
for p,h,z in [(C/'HDF.json','08d1b809b51f4d246c4b272dba3d7e1bad9c9d3090b52f3464d635a8e18e49de',4294),(C/'MF.json','c46bbdb08c3cec2c29fd04b135e466c3326ed7a7d68edd383051b3de72afe790',3777),(P/'HDF.json','6b2b486eb56f7a53c5656e8858580456dc997c26c5c3a518304fba0dcdd28fb2',2585),(P/'MF.json','ba1916769f329b8f95906c9762e68784fa932599d453e2621dcdd8a3b8a027dc',2941)]:
 verify({'path':str(p),'sha256':h,'bytes':z})
for r in read(C/'MF.json')['members']+read(P/'MF.json')['members']+read(P/'input-pins.json'):verify(r)
h=read(C/'HDF.json')
for r in h['candidate_files']:verify(r)
prov=read(C/'test-only-correction.provenance.json')
scoped=read(C/'scoped-checker-source.provenance.json')
for name in ['old_failed_source_ref','old_failed_guard_ref','new_source_ref']:verify(scoped[name])
oldchecker=pathlib.Path(scoped['old_failed_source_ref']['path']).read_text(encoding='utf-8')
newchecker=pathlib.Path(scoped['new_source_ref']['path']).read_text(encoding='utf-8')
ck('checker-fix-exact-inverse',newchecker.count(scoped['after'])==1 and newchecker.replace(scoped['after'],scoped['before'],1)==oldchecker)
ck('old-failed-guard-closed',read(scoped['old_failed_guard_ref']['path'])['closed'])
ck('new-author-guard-closed',read(C/'guard.final.json')['closed'] and read(C/'guard.final.json')['retained_handles_count']==0)
failure=read(C/'failure-origin.906.json')
ck('failure906-facts-preserved',failure['ordinal']==906 and failure['actual_outer_exit']==1 and failure['actual_python_exit']==1 and failure['actual_native_exit'] is None)
rel='internal/domain/backup_history20_upgrade_test.go'
old=(O/'candidate-root'/rel).read_bytes();new=(C/'candidate-root'/rel).read_bytes()
delta=prov['test_delta'];oldblock=delta['old_block'].encode();newblock=delta['new_block'].encode()
ck('test-full-byte-inverse',new.count(newblock)==1 and new.count(b' "encoding/json"\n')==1 and new.replace(newblock,oldblock,1).replace(b' "encoding/json"\n',b'',1)==old)
for r in ['internal/domain/backup.go','internal/domain/backup_history20_upgrade.go','internal/domain/backup_upgrade.go','ops/backup/main.go']:
 ck('production-byte-equal:'+r,(O/'candidate-root'/r).read_bytes()==(C/'candidate-root'/r).read_bytes())
baseline=read(O/'input-pins.json');ck('baseline-count66',len(baseline)==66)
for ref in baseline:verify(ref)
txt=new.decode();fn=txt.split('func TestHistory20PublicUpgradePreservesSourceAndRevokesRestoredCredentials',1)[1].split('func TestHistory20RejectsReleaseAndSourceDrift',1)[0]
ck('first-test-no-generic-restore','RestoreBackup(' not in fn)
ck('same-policy-correct-key-positive-control','verified,files,err := readBackupPolicy(opt.Snapshot,key,policy)' in fn)
ck('positive-control-before-wrong-key',fn.index('correct key rejected under matching upgrade policy') < fn.index('wrong[0] ^= 1'))
ck('same-policy-wrong-key','_,wrongFiles,err := readBackupPolicy(opt.Snapshot,wrong,policy)' in fn)
ck('specific-authentication-error','err.Error() != "BACKUP_MANIFEST_INVALID"' in fn and 'wrongFiles != nil' in fn)
ck('format-and-plan-verified','manifest.Format != localUpgradeFormat' in fn and 'plan["id"] != History20SchemaUpgradePlan' in fn)
ck('policy-purpose-matches','purpose:manifest.Purpose' in fn)
ck('positive-content-and-migration-assertions','len(files["state.sqlite"]) == 0' in fn and 'Hash(verified.Migrations) != Hash(upgradeVersions(20))' in fn and 'files["portable.json"]' in fn)
ck('json-import-used','"encoding/json"' in txt and 'json.Unmarshal(raw,&manifest)' in fn)
ck('both-keys-cleared','defer clear(key)' in fn and 'defer clear(wrong)' in fn)
ck('five-test-parents-preserved',txt.count('\nfunc TestHistory20')==5)
write('test.diff.json',{'diff':''.join(difflib.unified_diff(old.decode().splitlines(True),txt.splitlines(True),fromfile='H20/test.go',tofile='H20R1/test.go'))})
write('checks.json',{'source_only':True,'checks':checks,'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks)})
write('input-pins.json',list(inputs.values()))
unchanged=all(pin(p)==ref for p,ref in inputs.items())
write('guard.final.json',{'status':'RELEASED','all_source_pins_unchanged':unchanged,'input_count':len(inputs),'candidate_production_Main_canonical_written':False,'only_own_namespace_written':True})
if not unchanged or not all(c['pass'] for c in checks):
 print(json.dumps({'failed':[c for c in checks if not c['pass']],'unchanged':unchanged}));raise SystemExit(1)
report="""# H20R1 independent Source review

Verdict: SOURCE_ACCEPTED_PENDING_ROOT_RUNTIME. H20R-001 is resolved at Source level. This does not assert successful Go parsing, compilation, SQLite tests, native execution or formal historical20-to24 acceptance.

## Correction

The updated first test checks the snapshot's localUpgradeFormat and the exact History20 plan ID, supplies the matching manifest.Purpose policy, and requires readBackupPolicy with the correct key to succeed. That call authenticates the manifest, decrypts all listed files and validates their sizes/hashes before returning. The test also requires state.sqlite, historical migrations1..20 and no portable export. It then changes only the key and uses the same snapshot and policy; BACKUP_MANIFEST_INVALID and nil files are required.

The correct-key positive control eliminates the earlier format mismatch false positive. No production format or authentication guard was weakened. Deriving purpose from the manifest is acceptable for this generated-fixture authentication test; it is not independent authorization or provenance of a historical release.

The new encoding/json import is used. The map assertion matches JSON decoding into BackupManifest.Purpose (Object with interface-valued entries). Short declarations introduce new variables in the existing test scope; nil/error checks short-circuit safely. No obvious new Source-level compilation defect was identified. A real compiler has not been run.

## Reuse and exact scope

The original independent H20 Source review is reused. Its production findings and full-chain limitations are unchanged. Four production candidates are byte-equal to the original; the test is exactly invertible to the original after removing the encoding/json import and replacing only the original key-test block. All66 baseline Source pins and the prior review inputs were reverified. The generic cancellation test is intentionally unchanged, and five test parents remain.

Failure906 is preserved with actual outer/Python exit1 and nativeNULL. The old failed checker and its closed guard remain pinned. The subsequent checker correction has one exact inverse replacement which scopes absence checking to the first test. This review does not rerun either constructor.

## Remaining gates

Root must compile and run the scoped tests in an isolated qualified environment. Public synthetic test data and placeholder program bytes do not establish real historical Owner authentication, release qualification, native source locks or cutover readiness. Active-Run/effect/workspace/protected-service runtime coverage gaps disclosed by the original submission remain. The explicit session transition and complete20-to24 route remain OPEN.

No Go, SQL, native product, Git, private-key or model call was executed here. No current canonical guard was held; no Main, candidate or prior receipt was edited. New independent namespace only. No new mechanical failures; upstream903 and906 remain historical facts, not repeated attempts. Final source guard was reverified and released. STOP/FINAL.
"""
with (N/'report.md').open('x',encoding='utf-8',newline='\n') as f:f.write(report)
members=[pin(p) for p in sorted(N.iterdir()) if p.is_file()]
mf=write('MF.json',{'schema':'researchos.independent-source-review-manifest.v1','members':members})
hf=write('HDF.json',{'schema':'researchos.h20r1-independent-source-review.v1','status':'SOURCE_ACCEPTED_PENDING_ROOT_RUNTIME','H20R001':'RESOLVED_IN_SOURCE','candidate_handoff':pin(C/'HDF.json'),'candidate_manifest':pin(C/'MF.json'),'prior_review':pin(P/'HDF.json'),'manifest_ref':mf,'report_ref':pin(N/'report.md'),'checks_ref':pin(N/'checks.json'),'guard_ref':pin(N/'guard.final.json'),'checks_passed':len(checks),'input_count':len(inputs),'Go_SQL_native_execution':False,'overall20_to24':'OPEN','formal_acceptance':False,'new_failure_ordinals':[],'guard_released':True,'STOP':True,'FINAL':True})
print(json.dumps({'HDF':hf,'MF':mf,'checks':len(checks),'inputs':len(inputs)},ensure_ascii=False))

