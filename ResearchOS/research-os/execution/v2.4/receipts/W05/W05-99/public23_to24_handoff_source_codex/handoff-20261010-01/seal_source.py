from pathlib import Path
import hashlib,json,types,re
N=Path(__file__).parent
def pin(p):
 b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,v):
 p=N/n
 with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(p)
sources=json.loads((N/'source-inputs.json').read_bytes())['inputs']
for ref in sources:assert pin(Path(ref['path']))==ref
G=next(Path(x['path']) for x in sources if x['path'].endswith('source_read_guard.py'))
graw=G.read_bytes();assert hashlib.sha256(graw).hexdigest()=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
m=types.ModuleType('source_guard_final');exec(compile(graw,str(G),'exec'),m.__dict__)
files=sorted(p for p in (N/'candidate-root').rglob('*') if p.is_file())
refs=[pin(p) for p in files]
guard=m.SourceReadGuard();guard.acquire(refs)
try:
 def read(p):return guard.get_buffer(str(N/'candidate-root'/p)).decode('utf-8').replace('\r\n','\n')
 new=read('internal/domain/backup_prepared_abandonment_handoff.go')
 old=read('internal/domain/backup_prepared_abandonment_upgrade.go')
 backup=read('internal/domain/backup.go')
 cli=read('ops/backup/main.go')
 tests=read('internal/domain/backup_prepared_abandonment_handoff_test.go')
 assert new.count('if Digest(rawManifest) != binding.BackupManifestSHA256 || int64(len(rawManifest)) != binding.BackupManifestBytes {')==1
 assert new.count('preparedUpgradeProgramHashes(opt, true)')==3
 assert 'preparedUpgradeProgramHashes(opt, false)' not in new
 assert old.count('preparedUpgradeProgramHashes(opt, false)')==2
 assert 'createBackupPolicy(' not in new and 'exec.Command' not in new
 assert new.count('policy.beforeRecovery = checkSnapshot')==1
 assert new.count('policy.afterRecovery = func')==1
 assert new.index('Hash(rows) != Hash(original)') < new.index('policy.afterRecovery = func')
 assert new.count('preparedUpgradeRehearseDDL(')==1
 assert 'schema == schemas.Restored23' in new and 'schema != schemas.Source23' in new
 assert 'allowProtected:' not in new
 assert 'preparedUpgradeReceiptName' not in new
 assert backup.count('backupOrdinaryPublicPolicy(policy)')==4
 assert 'policy == nil || policy.allowProtected == nil' in backup
 assert 'if m.Format != backupFormat(policy) || !hmac.Equal' in backup
 assert 'if policy != nil && Hash(m.Purpose) != Hash(policy.purpose)' in backup
 assert cli.count('domain.UpgradePreparedAbandonmentBackup(')==1
 assert cli.count('domain.UpgradeLocal(')==1
 test_names=re.findall(r'^func (Test\w+)\(',tests,re.M)
 negative_names=re.findall(r'\{"([^"]+)", func',tests)
 assert len(test_names)==3 and len(negative_names)==12
 oldref=next(r for r in sources if r['path'].endswith('candidate-root\\internal\\domain\\backup_prepared_abandonment_upgrade.go') or r['path'].endswith('candidate-root/internal/domain/backup_prepared_abandonment_upgrade.go'))
 assert pin(N/'candidate-root/internal/domain/backup_prepared_abandonment_upgrade.go')['sha256']==oldref['sha256']
 initial=json.loads((N/'source-controls.json').read_bytes())
 for name in initial['preserved_candidate_files']:
  original=next(r for r in sources if Path(r['path']).as_posix().endswith(name))
  assert pin(N/name)['sha256']==original['sha256']
 check=save('final-source-checks.json',dict(schema='researchos.public23-to24-final-source-checks.v1',
  status='SOURCE_ONLY_CHECKS_PASSED',candidate_file_count=len(files),new_Go_tests=test_names,
  new_metadata_negative_cases=negative_names,Go_tests_executed=False,Go_compiled=False,
  final_delta='Three-line final manifest digest/length reread refusal and three new Go test functions added after initial source build.',
  target_current_hash_checks=3,old_source_current_hash_checks_preserved=2,
  exact_original_candidate_files_preserved=len(initial['preserved_candidate_files']),
  no_snapshot_recreation=True,original_apply_receipt_contract_not_extended=True,
  ordinary_backup_gates_kept=True,only_fixed_source_schema_shapes=True,
  actual_Go_SQL_Native_model_Rootstage_calls=0,formal_acceptance=False))
finally:
 closure=guard.close()
close_ref=save('final-source-guard.json',closure)
assert not closure['errors'] and closure['retained_handles_count']==0
for ref in refs:assert pin(Path(ref['path']))==ref
targets=['internal/domain/backup.go','ops/backup/main.go','internal/domain/backup_prepared_abandonment_handoff.go','internal/domain/backup_prepared_abandonment_handoff_test.go']
integration=[]
for path in targets:
 base=None
 if path=='internal/domain/backup.go':
  base=next(r for r in sources if Path(r['path']).as_posix().endswith('candidate-root/'+path))
 if path=='ops/backup/main.go':
  base=next(r for r in sources if Path(r['path']).as_posix().endswith('/'+path))
 integration.append(dict(repo_relative_path=path,operation='replace_exact_reviewed_base' if base else 'add_new_file',
  expected_base_ref=base,candidate_ref=pin(N/'candidate-root'/path)))
iref=save('integration-targets.json',dict(schema='researchos.public23-to24-integration-targets.v1',targets=integration,
 base_candidate_prerequisite='prepared_abandonment_schema_upgrade_revision_codex/6b0cb88050554e688314092dbebc6ba6',
 prerequisites_require_Root_composition=True,Main_adopted=False,source_only=True))
bindings=[pin(N/'diagnostic-appendix'/('original-'+str(k)+'.binding.json')) for k in (1227,1228)]
decision=save('source-decision.json',dict(schema='researchos.public23-to24-source-author-decision.v1',
 status='SOURCE_IMPLEMENTED_PENDING_NONAUTHOR_REVIEW_AND_ROOT_RUNTIME',actor_id='codex:/root/attach_restore_independent_review',
 scope='NEW_PUBLIC_EXISTING_MAIN23_BACKUP_TO_DISTINCT_TARGET24_ISOLATED_HANDOFF',
 source_author_accepts_own_work=False,execution_grant=False,Main_adopted=False,formal=False,production_ready=False,
 original_main23_qualification='EXTERNAL_ROOT_REVIEW_REQUIRED_NOT_AUTHENTICATED_BY_BINDING_JSON',
 original_apply_authority_unchanged=True,old_successful_native_commands_rerun=False,
 author_executed_Go_SQL_Native_model_Rootstage_calls=0,source_checks_ref=check,source_guard_ref=close_ref,
 integration_targets_ref=iref,diagnostic_bindings=bindings,STOP=True))
members=[pin(p) for p in sorted(N.rglob('*')) if p.is_file() and p.name not in ('HDF.json','MF.json','postseal-tool-io.json')]
mf=save('MF.json',dict(schema='researchos.public23-to24-source-manifest.v1',members=members,
 exclusions=['HDF.json','MF.json','postseal-tool-io.json']))
hdf=save('HDF.json',dict(schema='researchos.public23-to24-source-handoff.v1',
 actor_id='codex:/root/attach_restore_independent_review',status='SOURCE_IMPLEMENTED_PENDING_NONAUTHOR_REVIEW_AND_ROOT_RUNTIME',
 manifest_ref=mf,decision_ref=decision,contract_ref=pin(N/'CONTRACT.md'),
 candidate_file_count=len(files),source_refs=refs,integration_targets_ref=iref,
 binding_template_ref=pin(N/'binding.template.json'),source_input_pins_ref=pin(N/'source-inputs.json'),
 source_checks_ref=check,source_guard_ref=close_ref,diagnostic_bindings=bindings,
 source_only=True,execution_grant=False,formal=False,Main_adopted=False,production_ready=False,
 new_Go_tests_executed=False,author_executed_Go_SQL_Native_model_Rootstage_calls=0,
 prior_successes_replayed=False,Root_unique_Main_Canon_writer=True,STOP=True))
for r in members:assert pin(Path(r['path']))==r
for r in sources:assert pin(Path(r['path']))==r
print(json.dumps(dict(status='SOURCE_SEALED_PENDING_INDEPENDENT_REVIEW',HDF_ref=hdf,MF_ref=mf,decision_ref=decision,
 entry_ref=pin(N/'candidate-root/internal/domain/backup_prepared_abandonment_handoff.go'),
 integration_targets_ref=iref,source_controls_ref=check),ensure_ascii=False))

