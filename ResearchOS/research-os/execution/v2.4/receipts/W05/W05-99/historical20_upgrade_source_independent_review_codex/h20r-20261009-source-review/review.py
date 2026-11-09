import json, hashlib, pathlib, difflib
N=pathlib.Path(__file__).resolve().parent
B=N.parent.parent
C=B/'historical20_upgrade_source_codex/h20-1a11ebe661670a1a49d0ea22092604a'
T=pathlib.Path('D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-current-attach-q5-leg2-1791509207371')
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def pin(p):
 p=pathlib.Path(p); raw=p.read_bytes()
 return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def write(name,obj):
 p=N/name
 with p.open('x',encoding='utf-8',newline='\n') as f: f.write(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
 return pin(p)
checks=[]; inputs={}
def check(name,ok): checks.append({'name':name,'pass':bool(ok)})
def verify(ref):
 actual=pin(ref['path']); check('pin:'+str(ref['path']), actual['sha256']==ref['sha256'].removeprefix('sha256:') and actual['bytes']==ref['bytes']); inputs[actual['path']]=actual
roots=[
(C/'HDF.json','f3e1a18b047e1d36370efdd489145725655fe119faa69eb98a157776c6376493',4438),
(C/'MF.json','2be232566a2f59acad0d968439ab836e5cd05618740c3fd3b7f8bfafbed40958',5565),
(B/'historical20_upgrade_contract_readonly_codex/h20-contract-20261009-source-review/HDF.json','e4ff0bfad192bd56806055c2eaf765723bade00f3e7b3c9c0992536481cd10da',2164),
(B/'historical20_resource_route_readonly_codex/current_target_actual_review_01/HDF.json','a046899ff4d1d46f0e0b2441bc2c54bd336d70756eb97afd4e567086effdee9f',4771)]
for p,h,s in roots: verify({'path':str(p),'sha256':h,'bytes':s})
for ref in read(C/'MF.json')['members']: verify(ref)
baseline=read(C/'input-pins.json')
check('source-input-count-66',len(baseline)==66)
for ref in baseline: verify(ref)
def refs(v):
 if isinstance(v,dict):
  if all(k in v for k in ['path','sha256','bytes']): verify(v)
  else:
   for x in v.values(): refs(x)
 elif isinstance(v,list):
  for x in v: refs(x)
refs(read(C/'guard.final.json'))
for p,_,_ in roots[2:]: refs(read(p))
H=read(C/'HDF.json')
check('manifest-members-17',len(read(C/'MF.json')['members'])==17)
check('candidate-count-5',len(H['candidate_files'])==5)
diffs={}
for rel in ['internal/domain/backup.go','internal/domain/backup_upgrade.go','ops/backup/main.go']:
 old=(T/rel).read_text(encoding='utf-8'); new=(C/'candidate-root'/rel).read_text(encoding='utf-8')
 diffs[rel]=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='baseline/'+rel,tofile='candidate/'+rel))
 if rel.endswith('backup_upgrade.go'):
  addition='\tif opt.Plan == History20SchemaUpgradePlan {\n\t\treturn upgradeHistory20Local(ctx, opt, verifier)\n\t}\n'
  check('existing-upgrade-dispatch-only',new.count(addition)==1 and new.replace(addition,'',1)==old)
 elif rel.endswith('backup.go'):
  field='\tpreserveHistory20UpgradeWorkspaces          func(*sql.DB) error\n'
  branch='\tif policy != nil && policy.preserveHistory20UpgradeWorkspaces != nil {\n\t\tplan, ok := policy.purpose["plan"].(Object)\n\t\tif !ok || policy.format != localUpgradeFormat || plan["id"] != History20SchemaUpgradePlan {\n\t\t\treturn r, fmt.Errorf("RESTORE_HISTORY20_WORKSPACE_POLICY_MISMATCH")\n\t\t}\n\t\te = policy.preserveHistory20UpgradeWorkspaces(db)\n\t} else if policy != nil && policy.preserveQueueUpgradeWorkspaces != nil {'
  check('existing-backup-policy-only',new.count(field)==1 and new.count(branch)==1 and new.replace(field,'',1).replace(branch,'\tif policy != nil && policy.preserveQueueUpgradeWorkspaces != nil {',1)==old)
 else:
  expected=old.replace('upgrade: exact schema13 release root','upgrade: exact source release root for the selected fixed plan').replace('schema13-to20-research-runtime-v1 (exact releases only)','schema13-to20-research-runtime-v1 or schema20-to21-research-pending-windows-v1 (exact releases only)')
  check('cli-help-only',new==expected)
write('source-diffs.json',diffs)
new=(C/'candidate-root/internal/domain/backup_history20_upgrade.go').read_text(encoding='utf-8')
test=(C/'candidate-root/internal/domain/backup_history20_upgrade_test.go').read_text(encoding='utf-8')
check('five-test-parents',test.count('\nfunc TestHistory20')==5)
check('same-transaction-DDL-ledger',new.index('tx.ExecContext(ctx, string(raw))') < new.index('INSERT INTO schema_migrations(version) VALUES(21)') < new.index('return tx.Commit()'))
check('rollback-deferred','defer tx.Rollback()' in new)
check('public-dispatch-is-fixed-plan','const History20SchemaUpgradePlan = "schema20-to21-research-pending-windows-v1"' in new)
check('no-current-domain-constructor','New(' not in new)
check('no-session-installer-call','installClientSessionFence(' not in new)
check('pure20-and-pure21-release-counts','count != 20 && count != 21' in new)
check('pre-and-post-recovery-gates','filepath.Dir(databasePath), false' in new and 'opt.Destination, true' in new)
check('full-chain-explicitly-open','SESSION_INSTALLATION_AND_21_TO24_NOT_IMPLEMENTED_BY_THIS_PLAN' in new)
# Expected defect observation; this is not a failed tool/check execution.
check('H20R-001-reproduced-statically','wrong[0] ^= 1' in test and 'RestoreBackup(context.Background(),opt.Snapshot' in test and 'if err == nil { t.Fatal("encrypted snapshot accepted wrong key") }' in test)
finding={'id':'H20R-001','priority':'P2','file':str(C/'candidate-root/internal/domain/backup_history20_upgrade_test.go'),'start':76,'end':78,'title':'Wrong-key assertion is masked by the backup-format rejection','evidence':'UpgradeLocal writes localUpgradeFormat. RestoreBackup forwards policy=nil. readBackupPolicy rejects m.Format != backupFormat(nil) before evaluating HMAC. A correct key would fail identically.','required_change':'Read the same snapshot with an exact matching local-upgrade policy: first require correct-key read success and expected files, then change only the key and require authentication rejection. Do not count a format/purpose failure as key rejection.'}
write('findings.json',[finding])
write('input-pins.json',list(inputs.values()))
write('checks.json',{'kind':'static-source-and-byte-verification-only','checks':checks,'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'inputs':len(inputs),'Go_SQL_native_executed':False})
after=[pin(p) for p in inputs]
unchanged=all(a==inputs[a['path']] for a in after)
write('guard.final.json',{'status':'RELEASED','source_inputs':list(inputs.values()),'all_inputs_unchanged':unchanged,'production_Main_canonical_candidate_written':False,'own_namespace_only':True})
if not all(x['pass'] for x in checks) or not unchanged:
 print(json.dumps({'status':'REVIEW_MECHANICAL_CHECK_FAILED','checks':checks,'unchanged':unchanged},ensure_ascii=False))
 raise SystemExit(1)
report="""# H20 independent Source review

Verdict: REQUEST_CHANGES. One P2 test-coverage defect (H20R-001); no production-path blocking defect identified by this Source review. This is not compilation, Go/SQLite/native execution or acceptance of historical20-to24.

## Required correction

The wrong-key assertion at backup_history20_upgrade_test.go:76-78 uses generic RestoreBackup on a snapshot created by the local-upgrade policy. Generic RestoreBackup supplies policy=nil (baseline backup.go:561-562). readBackupPolicy checks m.Format != backupFormat(policy) first in its short-circuit OR (backup.go:504-505). localUpgradeFormat is incompatible with the generic format. Therefore both the correct and incorrect key are rejected before the HMAC is evaluated. The test passes without testing key authentication.

Use the matching local-upgrade policy to authenticate the sealed snapshot. Establish a positive control with the original key and verify expected files, then vary only the key and require authentication rejection. Do not change the production format guard to make this test pass. Root should not execute or accept the present candidate as complete wrong-key coverage.

## Source findings

The public UpgradeLocal dispatch targets a separate fixed 20-to21 handler. The release checks pin numbered 1..20 / 1..21 SQL and contracts. The historical A shape is compared with a template built from exactly the numbered base; the B additive-session shape is rejected. The new handler does not call the current domain constructor or an additive session installer. EnsureClientSessionFence returns without writes when client_sessions is absent, and fenceRestoredClientQueues returns for version below22.

The handler retains the existing exclusive-source-open, full encrypted backup, isolated restore and final publish framework. It validates snapshot row identity and workspace identity under the exact new plan policy, checks recovery before migration, and rechecks target schema, permitted row changes, original source rows, releases and program hashes before publication. Active Runs, effect history, credentials, retrieval roots and barriers have explicit constraints. 0021 DDL executes before INSERT version21 in the same transaction with deferred rollback. No ledger-only shortcut was found.

The three existing-file changes are independently reversed byte-for-byte at the text level: one dispatch branch, one new plan-specific workspace callback/branch, and CLI help. All 66 author-pinned baseline files and original contract/resource pins were rehashed. Existing 21/22/23 plans, templates and SQL are unchanged. Candidate final new-handler hash is cf8187c56564a38a1aa1357ae7f11ef45890d9f992f7500b768890679c683778/19212; the construction intermediate is not treated as the sealed candidate.

Five test parents and four release/source rejection subcases are present as Source. The ledger-insertion trigger test exercises the actual migration function and asserts rollback if run. The generic restore-cancellation test is source coverage for staged failure; it would be stronger to assert callback reachability and errors.Is(context.Canceled), but no concrete failure of that case was established here. Active-Run, effect, workspace and protected-service runtime cases remain gaps explicitly disclosed by the author. No Go parser/compiler/runtime claim is made.

## Authority and acceptance boundaries

Local OS administration and a recovery key are not Product Owner authentication. ProvisionPrincipal and IssueCredential in the tests create public synthetic fixtures; placeholder program bytes are not historical executable provenance. Program hashes prove stable bytes only. Qualified historical/target executable, real Owner flow, explicit legal additive-session transition, exact21-to22 compatibility, subsequent22-to24 validation and single-writer cutover remain OPEN. Pure21 is an isolated candidate; the existing startup guard remains unchanged.

## Audit and handoff

This review wrote only its new review namespace. No Git, Go, SQLite, native product, private-key, paid-model, Main or canonical operation was run. Original read I/O is preserved. One original PowerShell invocation emitted two nonterminating nonexistent-path errors (HANDOFF.json and MANIFEST.json); Root assigned one ordinal903. Outer exit0, Python/native NULL. It is not counted twice. Author failures900/901 are preserved upstream and unchanged. All source guard pins were rechecked and released. STOP/FINAL after handoff.
"""
with (N/'report.md').open('x',encoding='utf-8',newline='\n') as f: f.write(report)
members=[pin(p) for p in sorted(N.iterdir()) if p.is_file() and p.name not in {'MF.json','HDF.json'}]
m=write('MF.json',{'schema':'researchos.independent-source-review-manifest.v1','scope':'SOURCE_ONLY','members':members})
h=write('HDF.json',{'schema':'researchos.h20-independent-source-review.v1','status':'REQUEST_CHANGES','finding_ids':['H20R-001'],'overall20_to24':'OPEN','review_actor':'codex:/root/attach_fixture_source_review','candidate_handoff':pin(C/'HDF.json'),'candidate_manifest':pin(C/'MF.json'),'manifest_ref':m,'report_ref':pin(N/'report.md'),'findings_ref':pin(N/'findings.json'),'checks_ref':pin(N/'checks.json'),'guard_ref':pin(N/'guard.final.json'),'passed_checks':len(checks),'input_count':len(inputs),'native_SQL_Go_executed':False,'new_failure_ordinals':[903],'guard_released':True,'STOP':True,'FINAL':True})
print(json.dumps({'HDF':h,'MF':m,'checks':len(checks),'inputs':len(inputs),'verdict':'REQUEST_CHANGES'},ensure_ascii=False))

