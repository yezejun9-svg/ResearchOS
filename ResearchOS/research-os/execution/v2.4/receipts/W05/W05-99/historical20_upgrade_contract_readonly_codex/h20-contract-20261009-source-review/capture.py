import pathlib,json,hashlib
N=pathlib.Path(__file__).resolve().parent
R=N.parents[6];B=N.parents[1]
T=R/'.local/worktrees/codex-w0599-current-attach-q5-leg2-1791509207371'
H=B/'historical20_resource_route_readonly_codex/current_target_actual_review_01'
K=R.parent/'ResearchOS_Implementation_Package_v2.4'
def pin(p):
 b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def js(n,obj):
 with (N/n).open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=True,indent=2);f.write('\n')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
paths=[]
current=["internal/domain/backup_upgrade.go","internal/domain/backup_upgrade_final.go","internal/domain/backup_migration.go","internal/domain/backup_queue_upgrade.go","internal/domain/backup_configuration_upgrade.go","internal/domain/backup_prepared_abandonment_upgrade.go","internal/domain/backup.go","internal/domain/backup_recovery.go","internal/domain/client_session_fence.go","internal/domain/store.go","internal/domain/legacy_migration_fixture_test.go","internal/domain/testdata/pretranscript-3225a31f.sql","migrations/sqlite/0021_research_pending_windows.sql","migrations/sqlite/0022_client_command_queue.sql","migrations/sqlite/0023_host_model_configuration.sql","migrations/sqlite/0024_prepared_run_abandonment.sql","migrations/sqlite/next_v24_sessions.sql","internal/recoveryauthority/migration.go","internal/recoveryauthority/migration_windows.go","ops/supervisor/recovery_root/main_windows.go","apps/control/prepared_recovery_windows.go","apps/control/main.go","ops/backup/main.go","ops/backup/README.md"]
paths += [T/x for x in current]
paths += [K/x for x in ['PACKAGE_MANIFEST.json','18_EXISTING_REPOSITORY_MIGRATION.md','07_OPERATIONS_AND_EVOLUTION.md','06_ACCEPTANCE_TESTS.md','contracts/acceptance.json','contracts/delivery.contract.json']]
paths += [H/x for x in ['HDF.json','MF.json','postseal.json','report.md','historical-source.pins.json','current-source.pins.json','resource-inventory.json','expanded-module-resource-presence.json','go-dependency-resource-presence.json']]
hist=load(H/'historical-source.pins.json')
wanted={'apps/control/main.go','apps/cli/main.go','ops/backup/main.go','internal/domain/store.go','internal/domain/backup_migration.go','internal/domain/client_session_fence.go','internal/domain/backup.go','internal/domain/v24_sessions.go','migrations/sqlite/next_v24_sessions.sql','go.mod','go.sum','execution/toolchains/locked.json'}
wanted.update(x['tree_entry']['path'] for x in hist if x['tree_entry']['path'].startswith('migrations/sqlite/00'))
historicalChecks=[]
for x in hist:
 if x['tree_entry']['path'] not in wanted:continue
 p=pathlib.Path(x['source_copy']['path']);raw=p.read_bytes()
 actual=pin(p);expected=x['source_copy'];ok=actual['sha256']==expected['sha256'] and actual['bytes']==expected['bytes']
 blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
 historicalChecks.append(dict(path=x['tree_entry']['path'],sha256=actual['sha256'],bytes=len(raw),blob=blob,expected_blob=x['tree_entry']['oid'],passed=ok and blob==x['tree_entry']['oid']))
 paths.append(p)
capsuleMF=load(H/'MF.json')
# The resource capsule's own HDF/manifest pins, and all selected source copies,
# are verified without invoking Git or accessing any original data-root secrets.
capsuleChecks=[]
memberValues=capsuleMF['members'].values() if isinstance(capsuleMF['members'],dict) else capsuleMF['members']
byPath={str(pathlib.Path(x['path']).resolve()).casefold():x for x in memberValues}
for p in paths:
 ref=byPath.get(str(p.resolve()).casefold())
 if ref:
  a=pin(p);capsuleChecks.append(dict(path=str(p),passed=a['sha256']==ref['sha256'] and a['bytes']==ref['bytes']))
refs=list({str(p.resolve()).casefold():pin(p) for p in paths}.values())
js('guard.initial.json',refs)
for i,ref in enumerate(refs):
 p=pathlib.Path(ref['path']);d=N/'inputs'/str(i).zfill(3)/p.name;d.parent.mkdir(parents=True,exist_ok=True)
 with d.open('xb') as f:f.write(p.read_bytes())
# Source anchors are location evidence only; SQL and product code are not executed.
anchors={}
patterns=['func UpgradeLocal','func upgradeLocal','func CheckMigrationSafety','func upgradeQueueTemplate','func upgradeQueueRelease','func upgradeRecoveryInvariantForTarget','func EnsureClientSessionFence','func installClientSessionFence','func restoreBackupPolicy','func (s *Service) backupFence','func legacyTranscriptFixtureDatabase','const MigrationPurpose','const MigrationPlanID','const MigrationArgument','func runPreparedRecoveryMaintenance','func runPreparedSchemaMaintenance','CREATE TABLE research_pending_windows','## 4. 数据与凭据迁移','## 6. 退出与交付','### 6.1','### 6.2','## 7. 发布布局','### A12']
for p in [T/x for x in current]+[K/x for x in ['18_EXISTING_REPOSITORY_MIGRATION.md','07_OPERATIONS_AND_EVOLUTION.md','06_ACCEPTANCE_TESTS.md']]:
 found=[]
 for i,line in enumerate(p.read_text(encoding='utf-8').splitlines(),1):
  for pattern in patterns:
   if pattern in line:found.append(dict(line=i,text=line))
 if found:anchors[str(p)]=found
js('source-anchors.json',anchors)
js('historical-blob-checks.json',historicalChecks)
js('resource-capsule-checks.json',capsuleChecks)
final=[pin(pathlib.Path(ref['path'])) for ref in refs]
js('guard.final.json',dict(unchanged=refs==final,before=refs,after=final))
result=dict(status='READONLY_RESEARCH_CAPTURED',inputs=len(refs),historical_files=len(historicalChecks),historical_blobs_ok=all(x['passed'] for x in historicalChecks),selected_capsule_refs_ok=all(x['passed'] for x in capsuleChecks),all_inputs_unchanged=refs==final,actual_Git_Go_SQL_native_model=False,private_keys_read=False)
js('capture-result.json',result);print(json.dumps(result))
assert result['historical_blobs_ok'] and result['selected_capsule_refs_ok'] and result['all_inputs_unchanged']

