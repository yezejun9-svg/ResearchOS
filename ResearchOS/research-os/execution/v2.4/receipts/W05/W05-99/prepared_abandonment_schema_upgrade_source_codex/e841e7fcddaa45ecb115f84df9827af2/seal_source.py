from pathlib import Path
import hashlib,json,difflib,re
own=Path(__file__).resolve().parent
base=own.parents[7]
# Resolve the repository by its exact known parent marker, never by a glob.
base=Path('D:/\u4f5c\u54c1\u96c6/ResearchOS/research-os')
def ref(path):
    path=Path(path)
    raw=path.read_bytes()
    return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(path,obj):
    path.write_text(json.dumps(obj,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
pins=json.loads((own/'base-refs.json').read_text(encoding='utf-8'))
drift=[]
for pin in pins:
    current=ref(pin['path'])
    if current!=pin: drift.append({'expected':pin,'actual':current})
assert not drift,drift
authority=base/'execution/v2.4/receipts/W05/W05-99/prepared_abandonment_native_authority_source_codex/f6373acf36474d869fa8a64f3c490864'
additional=[authority/'HDF.json',authority/'MF.json',
authority/'candidate-root/internal/recoveryauthority/migration.go',
authority/'candidate-root/internal/recoveryauthority/migration_windows.go',
authority/'candidate-root/internal/recoveryauthority/types.go',
base/'internal/domain/backup_workspace.go',
base/'internal/domain/client_configuration_test.go',
base/'internal/domain/backup_host_configuration_test.go']
seen={p['path'] for p in pins}
for path in additional:
    current=ref(path)
    if current['path'] not in seen: pins.append(current);seen.add(current['path'])
expected_authority={
'HDF.json':('2f33da54d8e91dad1651da92ecbbc6506d0520a541b730176129fafd2db0a3d2',23048),
'MF.json':('349aa6b33bd8a2616aa619607b25bea10f502e60292f734abcfc3e21a311215c',24259)}
for name,(sha,size) in expected_authority.items():
    got=ref(authority/name)
    assert got['sha256']==sha and got['bytes']==size,got
save(own/'base-refs.json',pins)
candidate=own/'candidate-root'
sources=sorted(p for p in candidate.rglob('*') if p.is_file())
assert len(sources)==10,len(sources)
texts={p.relative_to(candidate).as_posix():p.read_bytes().decode('utf-8') for p in sources if p.suffix=='.go'}
common=texts['internal/domain/backup_prepared_abandonment_upgrade.go']
native=texts['internal/domain/backup_prepared_abandonment_upgrade_windows.go']
checks=[]
def check(name,value):
    checks.append({'name':name,'passed':bool(value),'basis':'STATIC_SOURCE_TEXT_ONLY'})
check('fixed_plan_and_exact_sql_pin', 'schema23-to24-prepared-abandonment-v1' in common and 'sha256:1c606771104c3b9abaaedaadb55d8e8c16d5f91f3398fa283ec9886b935f9098' in common)
mirror=ref(candidate/'internal/domain/contracts/prepared_run_abandonment.sql')
check('embedded_sql_matches_v4',mirror['sha256']=='1c606771104c3b9abaaedaadb55d8e8c16d5f91f3398fa283ec9886b935f9098')
check('original_entry_never_calls_restore_or_backupFence','backupFence(' not in native and 'restoreBackupPolicy(' not in native)
check('original_opaque_migration_binding','token recoveryauthority.MigrationToken' in native and 'token.Begin(binding)' in native and 'token.RequirePin(' in native)
check('current_owner_rechecked_in_transaction','authenticate(tx, ownerToken)' in native and 'owner.Allowed(binding.ProjectID' in native and 'authorityRoot(tx, owner.ID)' in native)
check('complete_encrypted_payload_pins','encrypted-backup-payload:' in native and 'readBackupPolicy(opt.Snapshot, key, policy)' in native)
check('complete_fixed_release_member_pins','source-inventory:' in native and 'target-inventory:' in native)
check('single_transaction_validates_before_commit','preparedUpgradeDDL(ctx, tx' in native and native.index('preparedUpgradeDDL(ctx, tx')<native.index('if err = tx.Commit()'))
check('rollback_before_token_finish','_ = tx.Rollback(); token.Finish(commitAttempted)' in native)
check('commit_uncertainty_not_rollback_claim','COMMIT_OUTCOME_UNKNOWN' in native and 'commitAttempted = true' in native)
check('rehearsal_runs_normal_restore_before_ddl','policy.afterRecovery = func(restored *sql.DB)' in common and 'preparedUpgradeRehearseDDL(ctx, restored' in common)
check('no_generic_restore_skip_added','skipRecovery' not in texts['internal/domain/backup.go'])
check('source_only_data_root_lease','acquirePreparedUpgradeRootLease(filepath.Dir(opt.Source))' in common and 'runtimeadapter.AcquireDataRootLease(root)' in native)
check('typed_lossless_row_invariant','math.Float64bits(v)' in common and 'strconv.FormatInt(v, 10)' in common and 'PREPARED_UPGRADE_BUSINESS_ROWS_CHANGED' in common)
check('backup24_validates_fixed_schema','backupPreparedAbandonmentSchema(db)' in texts['internal/domain/backup_host_configuration.go'])
check('historical_configuration_source_not_modified',all(ref(p['path'])==p for p in pins if p['path'].endswith('backup_configuration_upgrade.go')))
check('legacy_test_keeps_exact23_fixture','root := configurationUpgradeReleaseFixture(t, 23)' in texts['internal/domain/backup_configuration_upgrade_test.go'])
check('no_main_or_input_drift',not drift)
assert all(c['passed'] for c in checks),checks
tests=[]
for name,content in texts.items():
    if name.startswith('internal/domain/backup_prepared_') and name.endswith('_test.go'):
        tests.extend(re.findall(r'^func (TestPreparedUpgrade\w+)\(',content,re.M))
assert len(tests)==13,tests
save(own/'static-evidence.json',{'schema':'researchos.prepared-schema-upgrade-static-evidence.v1','decision':'SOURCE_TEXT_CHECKS_ONLY_NOT_GO_TEST_RESULTS','checks':checks,'test_functions':tests,'go_compiler_executed':False,'gofmt_executed':False,'native_executed':False,'sql_executed_by_author':False,'provider_executed':False,'source_file_count':len(sources),'input_pin_count':len(pins),'input_drift_count':len(drift),'new_failure_ordinals':[763,764]})
diff=[]
source_refs={}
pin_map={p['path']:p for p in pins}
for p in sources:
    rel=p.relative_to(candidate).as_posix()
    main=base/rel
    old=main.read_bytes().decode('utf-8').splitlines(True) if main.is_file() else []
    new=p.read_bytes().decode('utf-8').splitlines(True)
    diff.extend(difflib.unified_diff(old,new,fromfile='Main/'+rel,tofile='candidate-root/'+rel))
    r=ref(p)
    r['base_ref']=pin_map.get(str(main))
    if rel=='internal/domain/contracts/prepared_run_abandonment.sql':
        r['byte_identical_input_ref']=next(x for x in pins if x['path'].endswith('candidate-root\\migrations\\sqlite\\0024_prepared_run_abandonment.sql'))
    source_refs['candidate-root/'+rel]=r
(own/'source.patch').write_text(''.join(diff),encoding='utf-8',newline='')
members={}
for path in sorted(own.rglob('*')):
    if path.is_file() and path.name not in ('HDF.json','MF.json'):
        members[path.relative_to(own).as_posix()]=ref(path)
manifest={'schema':'researchos.prepared-abandonment-schema-upgrade-source-manifest.v1','members':members,'member_count':len(members),'source_file_count':len(sources),'source_refs':source_refs,'base_refs':pins,'input_drift_count':0,'testing_executed':False}
save(own/'MF.json',manifest)
handoff={'schema':'researchos.prepared-abandonment-schema-upgrade-source-handoff.v1','status':'SOURCE_IMPLEMENTED_PENDING_ROOT_TESTS_AND_INDEPENDENT_REVIEW','sourceStatus':'EXECUTION_REPORTED','formal':False,'production_ready':False,'execution_authority':False,'source_root':str(candidate),'source_file_count':len(sources),'manifest_member_count':len(members),'total_file_count':len(members)+2,'manifest_ref':ref(own/'MF.json'),'source_refs':source_refs,'base_ref_count':len(pins),'input_drift_count':0,'contract_ref':ref(own/'CONTRACT.md'),'patch_ref':ref(own/'source.patch'),'static_evidence_ref':ref(own/'static-evidence.json'),'raw_tool_io_ref':ref(own/'original-tool-io.json'),'failure_origins':[ref(own/'failure-origin.763.json'),ref(own/'failure-origin.764.json')],'search_no_matches_observation_not_failure':{'operation':'pa24read2[2]','chunk':'c9ca69','outer_exit':1,'diagnostic':None},'composition_dependencies':{'prepared_v4_handoff':next(p for p in pins if p['path'].endswith('f1cd47ca0f9544bfbe94b51a80d7c492\\HDF.json')),'prepared_v4_manifest':next(p for p in pins if p['path'].endswith('f1cd47ca0f9544bfbe94b51a80d7c492\\MF.json')),'native_authority_handoff':ref(authority/'HDF.json'),'native_authority_manifest':ref(authority/'MF.json')},'actual_author_execution':{'source_constructor_outer_exit':0,'python_exit':0,'go':False,'gofmt':False,'tests':False,'native':False,'sql':False,'provider':False,'git':False,'main_edits':False,'canonical_edits':False,'production_data_root_edits':False},'implemented':['fixed23-to24 release/SQL/template gates','Windows DataRootLease plus retained SQLite exclusive rehearsal','complete matching encrypted backup and normal isolated restore','post-restore baseline and exact typed row multiset DDL+rollback validation','opaque purpose-separated native MigrationToken apply entry with current Owner recheck','signed native-held complete release and encrypted payload members','original schema-only commit and immutable intent/result receipts','exact24 normal-backup schema gate without future25 acceptance','historical23 fixture preservation','13 focused test functions, not executed'],'remaining_gates':['Root composed build and actual focused plus historical backup regressions','independent Source and actual-result review','native leaf issuer enrollment remains empty and fails closed','independently accepted matching programs/source inventory and signed migration grant','matching encrypted backup + isolated rehearsal + full native-held member pins','current already-baselined Owner credential and protected service if required','separate actual original-root migration authorization and immutable actual receipts','later abandonment is separate; no automatic retry/promotion/C7/formal advancement'],'prior_trial_accounting':{'basis':'Parent-reported preserved prior state, not re-queried by this Source author','provider_requests':None,'recorded_model_effects':0,'clock_reset':False,'old_once_replaced':False}}
save(own/'HDF.json',handoff)
assert len([p for p in own.rglob('*') if p.is_file()])==len(members)+2
print(json.dumps({'handoff':ref(own/'HDF.json'),'manifest':ref(own/'MF.json'),'source_files':len(sources),'manifest_members':len(members),'total_files':len(members)+2,'input_pins':len(pins),'input_drift':0,'static_checks':len(checks),'test_functions_not_run':len(tests),'source_refs':source_refs},ensure_ascii=True))

