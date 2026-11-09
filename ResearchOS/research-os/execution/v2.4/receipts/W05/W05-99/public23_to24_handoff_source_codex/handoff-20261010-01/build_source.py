from pathlib import Path
import json,hashlib,types,difflib
N=Path(__file__).parent;R=N.parents[6]
B=R/'execution/v2.4/receipts/W05/W05-99'
Q=B/'prepared_abandonment_schema_upgrade_revision_codex/6b0cb88050554e688314092dbebc6ba6'
G=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
def pin(p):
 raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,v,raw=False):
 p=N/name;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(v if raw else (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(p)
assert G.is_file()
graw=G.read_bytes();assert hashlib.sha256(graw).hexdigest()=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
module=types.ModuleType('source_guard');exec(compile(graw,str(G),'exec'),module.__dict__)
hdf=json.loads((Q/'HDF.json').read_bytes())
refs=[{k:r[k] for k in ('path','sha256','bytes')} for r in hdf['source_refs'].values()]
refs += [pin(p) for p in (G,Q/'HDF.json',Q/'MF.json',Q/'CONTRACT.md',R/'ops/backup/main.go',R/'internal/domain/backup_upgrade.go',R/'internal/domain/backup_recovery.go',R/'internal/domain/backup_configuration_upgrade.go',N/'handoff_prelude.go.txt',N/'build_source.py')]
guard=module.SourceReadGuard();guard.acquire(refs)
try:
 def get(p):return guard.get_buffer(str(p)).decode('utf-8').replace('\r\n','\n')
 save('source-inputs.json',dict(schema='researchos.public23-to24-handoff-source-inputs.v1',inputs=refs))
 base=get(Q/'candidate-root/internal/domain/backup_prepared_abandonment_upgrade.go')
 start=base.index('func upgradePreparedAbandonmentLocal(')
 end=base.index('\nfunc preparedUpgradeConcreteVerifier',start)
 body=base[start:end]
 edits=[]
 def rep(text,old,new):
  assert text.count(old)==1, ('expected one source span',old[:100],text.count(old))
  edits.append(dict(old=old,new=new))
  return text.replace(old,new,1)
 body=rep(body,'func upgradePreparedAbandonmentLocal(ctx context.Context, opt LocalUpgradeOptions, verifier upgradeVerifier)', 'func upgradePreparedAbandonmentBackup(ctx context.Context, handoff PreparedBackupHandoffOptions, verifier upgradeVerifier)')
 body=rep(body,'    report = RestoreReport{Started: Now(), Status: "FAILED"}','    opt := handoff.Upgrade\n    report = RestoreReport{Started: Now(), Status: "FAILED"}')
 body=rep(body,'upgradePaths(&opt)','preparedHandoffPaths(&opt, &handoff)')
 body=body.replace('preparedUpgradeProgramHashes(opt, false)','preparedUpgradeProgramHashes(opt, true)')
 assert 'preparedUpgradeProgramHashes(opt, false)' not in body
 body=rep(body,'    contracts, err := LoadContracts', '    binding, err := preparedHandoffCheck(opt, handoff)\n    if err != nil { return report, err }\n    contracts, err := LoadContracts')
 body=rep(body,'    defer clear(key)','    defer clear(key)\n    if err = preparedHandoffVerifyBackup(opt, key, binding); err != nil { return report, err }')
 body=rep(body,'    if err != nil || schema != schemas.Source23 { return report, fmt.Errorf("PREPARED_UPGRADE_SOURCE_SCHEMA") }',
 '''    if err != nil { return report, err }
    sourceSchema, targetSchema := schema, schemas.Original24
    if schema == schemas.Restored23 {
        targetSchema = schemas.Restored24
    } else if schema != schemas.Source23 {
        return report, fmt.Errorf("PREPARED_UPGRADE_SOURCE_SCHEMA")
    }''')
 body=body.replace('SourceSchema: schemas.Source23, TargetSchema: schemas.Original24','SourceSchema: sourceSchema, TargetSchema: targetSchema')
 body=body.replace('"source_schema_hash": schemas.Source23, "original_target_schema_hash": schemas.Original24','"source_schema_hash": sourceSchema, "original_target_schema_hash": targetSchema')
 body=body.replace('currentSchema != schemas.Source23','currentSchema != sourceSchema')
 body=rep(body,'Schema: "researchos.prepared-abandonment-schema-rehearsal.v1"','Schema: "researchos.prepared-abandonment-public-backup-rehearsal.v1"')
 body=rep(body,'"SAME_HOST_PREPARED_ABANDONMENT_SCHEMA_REHEARSAL"','"SAME_HOST_PUBLIC23_TO24_BACKUP_HANDOFF"')
 body=rep(body,'    receipt.BackupPurpose = purpose','''    purpose["source_provenance"] = "EXTERNALLY_REVIEWED_OBSERVATION_INPUT_NOT_JSON_AUTHORITY"
    purpose["handoff_binding_sha256"] = handoff.BindingSHA256
    purpose["producer_observation"] = binding.ProducerObservation
    purpose["producer_stdout"] = binding.ProducerStdout
    purpose["existing_public_backup_consumed"] = true
    purpose["old_program_executed_by_target"] = false
    receipt.BackupPurpose = purpose''')
 body=rep(body,'''    policy := &backupPolicy{format: localUpgradeFormat, databaseName: "researchos.sqlite", purpose: purpose,
        validate: guard.refresh, allowProtected: guard.artifact}''',
 '''    // Retain ordinary public backup MAC/portable/queue/protected-artifact gates.
    // This private flag only permits fixed same-host preservation and late DDL.
    policy := &backupPolicy{format: "RESEARCHOS_BACKUP_V1", databaseName: "researchos.sqlite",
        validate: guard.refresh, publicPreparedAbandonmentHandoff: true}''')
 body=rep(body,'        return ctx.Err()','''        currentBinding, err := preparedHandoffCheck(opt, handoff)
        if err != nil || Hash(currentBinding) != Hash(binding) { return fmt.Errorf("PREPARED_HANDOFF_INPUT_CHANGED") }
        if err = preparedHandoffVerifyBackup(opt, key, binding); err != nil { return err }
        return ctx.Err()''')
 body=rep(body,'''    if _, err = (&Service{DB: db, Contracts: contracts}).createBackupPolicy(ctx, opt.Snapshot, key, policy); err != nil { return report, err }
''','')
 body=rep(body,'    // No skipRecovery and no migration callback in generic RestoreOptions.','''    // Consume the already-observed old-program output. Never recreate it.
    // The beforeRecovery hook rejects stale/mixed snapshots before late DDL.
    // No skipRecovery and no migration callback in generic RestoreOptions.''')
 body=rep(body,'"ISOLATED_REHEARSAL_COMPLETE_ORIGINAL_UNCHANGED"','"ISOLATED_PUBLIC_BACKUP_HANDOFF_COMPLETE_ORIGINAL_UNCHANGED"')
 body=body.replace('preparedUpgradeReceiptName','preparedPublicHandoffReceiptName')
 body=rep(body,'    report.Recovery["prepared_abandonment_rehearsal_receipt"]','    report.Recovery["prepared_abandonment_public_backup_handoff_receipt"]')
 body=rep(body,'    report.Recovery["prepared_abandonment_public_backup_handoff_receipt"] = Object',
 '''    report.Recovery["local_upgrade"] = purpose
    report.Recovery["source_provenance_authority"] = "EXTERNAL_INDEPENDENT_REVIEW_REQUIRED"
    report.Recovery["prepared_abandonment_public_backup_handoff_receipt"] = Object''')
 # Copy the prior schema24 candidate without changing existing native apply or
 # fixtures. Only backup.go below changes; CLI and handoff files are additions.
 for rel,ref in hdf['source_refs'].items():
  if rel=='candidate-root/internal/domain/backup.go':continue
  save(rel,guard.get_buffer(ref['path']),True)
 prelude=get(N/'handoff_prelude.go.txt')
 save('candidate-root/internal/domain/backup_prepared_abandonment_handoff.go',(prelude+body).encode(),True)
 backup=get(Q/'candidate-root/internal/domain/backup.go')
 bedits=[]
 def brep(old,new):
  nonlocal_dummy=None
  global backup
  assert backup.count(old)==1, ('backup span count',old[:90],backup.count(old))
  backup=backup.replace(old,new,1);bedits.append(dict(old=old,new=new))
 brep('\tpreservePreparedAbandonmentUpgradeWorkspaces func(*sql.DB) error','\tpreservePreparedAbandonmentUpgradeWorkspaces func(*sql.DB) error\n\tpublicPreparedAbandonmentHandoff bool')
 brep('func backupFormat(policy *backupPolicy) string {','''// Ordinary public validation remains mandatory for the fixed handoff policy.
func backupOrdinaryPublicPolicy(policy *backupPolicy) bool {
    return policy == nil || policy.publicPreparedAbandonmentHandoff
}

func backupFormat(policy *backupPolicy) string {''')
 brep('(policy == nil && files["portable.json"] == nil)','(backupOrdinaryPublicPolicy(policy) && files["portable.json"] == nil)')
 brep('if policy != nil && files["portable.json"] != nil {','if !backupOrdinaryPublicPolicy(policy) && files["portable.json"] != nil {')
 brep('if policy == nil {\n\t\tif e = backupWorkspaceRestorePaths','if backupOrdinaryPublicPolicy(policy) {\n\t\tif e = backupWorkspaceRestorePaths')
 brep('if policy == nil {\n\t\tqueue, err := backupQueueState','if backupOrdinaryPublicPolicy(policy) {\n\t\tqueue, err := backupQueueState')
 brep('''\t\tif !ok || policy.format != localUpgradeFormat || plan["id"] != PreparedAbandonmentSchemaUpgradePlan {
\t\t\treturn r, fmt.Errorf("RESTORE_PREPARED_ABANDONMENT_WORKSPACE_POLICY_MISMATCH")
\t\t}''','''        fixedLocal := ok && policy.format == localUpgradeFormat && plan["id"] == PreparedAbandonmentSchemaUpgradePlan
        fixedPublic := policy.publicPreparedAbandonmentHandoff && policy.format == "RESEARCHOS_BACKUP_V1" &&
            len(policy.purpose) == 0 && policy.allowProtected == nil
        if !fixedLocal && !fixedPublic {
            return r, fmt.Errorf("RESTORE_PREPARED_ABANDONMENT_WORKSPACE_POLICY_MISMATCH")
        }''')
 save('candidate-root/internal/domain/backup.go',backup.encode(),True)
 cli=get(R/'ops/backup/main.go');cedits=[]
 def crep(old,new):
  global cli
  assert cli.count(old)==1, ('CLI span count',old[:100],cli.count(old))
  cli=cli.replace(old,new,1);cedits.append(dict(old=old,new=new))
 crep('keygen|create|export|restore|upgrade-local [flags]','keygen|create|export|restore|upgrade-local|upgrade-prepared-backup [flags]')
 crep('\tif e := f.Parse(os.Args[2:]); e != nil {','''    handoffBinding := f.String("handoff-binding", "", "upgrade-prepared-backup: externally reviewed and pinned producer binding")
    handoffSHA256 := f.String("handoff-binding-sha256", "", "upgrade-prepared-backup: expected sha256: digest of binding")
\tif e := f.Parse(os.Args[2:]); e != nil {''')
 crep('command != "upgrade-local" {','command != "upgrade-local" && command != "upgrade-prepared-backup" {')
 crep('\tif command == "upgrade-local" {','''    if command == "upgrade-prepared-backup" {
        r, e := domain.UpgradePreparedAbandonmentBackup(context.Background(), domain.PreparedBackupHandoffOptions{
            Upgrade: domain.LocalUpgradeOptions{
                Source: *source, Snapshot: *backup, Destination: *out, KeyFile: *keyfile,
                SourceRoot: *sourceRoot, TargetRoot: *root, SourceProgram: *sourceProgram,
                TargetProgram: *targetProgram, Plan: *plan,
            },
            BindingFile: *handoffBinding, BindingSHA256: *handoffSHA256,
        })
        if e != nil { return e }
        return json.NewEncoder(os.Stdout).Encode(r)
    }
\tif command == "upgrade-local" {''')
 save('candidate-root/ops/backup/main.go',cli.encode(),True)
 # Byte preservation is evaluated with original newline bytes as well.
 preserved=[]
 for rel,ref in hdf['source_refs'].items():
  if rel!='candidate-root/internal/domain/backup.go':
   assert pin(N/rel)['sha256']==ref['sha256'];preserved.append(rel)
 def inverse(s,changes):
  for e in reversed(changes):
   assert s.count(e['new'])==1
   s=s.replace(e['new'],e['old'],1)
  return s
 assert inverse(backup,bedits)==get(Q/'candidate-root/internal/domain/backup.go')
 assert inverse(cli,cedits)==get(R/'ops/backup/main.go')
 assert 'createBackupPolicy(' not in body and 'preparedUpgradeProgramHashes(opt, false)' not in body
 assert body.count('preparedUpgradeProgramHashes(opt, true)')==2
 assert 'allowProtected:' not in body
 assert 'SourceSchema: sourceSchema, TargetSchema: targetSchema' in body
 assert 'preparedUpgradeRehearseDDL(ctx, restored, sqls[23], baseline, schemas.Restored23, schemas.Restored24)' in body
 for needle in ['policy.beforeRecovery = checkSnapshot','policy.afterRecovery = func','Hash(rows) != Hash(original)','preparedHandoffVerifyBackup(opt, key, binding)','acquirePreparedUpgradeRootLease','receipt.RollbackVerified, receipt.ExistingRowsUnchanged, receipt.NewProofTableEmpty = true, true, true']:
  assert needle in body
 # No original-apply filename can be emitted by the new function.
 assert 'preparedUpgradeReceiptName' not in prelude+body
 patches=[]
 for path,old,new in [('internal/domain/backup.go',get(Q/'candidate-root/internal/domain/backup.go'),backup),('ops/backup/main.go',get(R/'ops/backup/main.go'),cli)]:
  patches.append(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+path,tofile='b/'+path)))
 save('integration.patch',''.join(patches).encode(),True)
 save('source-controls.json',dict(schema='researchos.public23-to24-source-controls.v1',
  status='SOURCE_TEXT_AND_BYTE_CONTROLS_PASSED_NO_GO_EXECUTION',preserved_candidate_files=preserved,
  backup_patch_inverse_exact=True,cli_patch_inverse_exact=True,new_target_bound_calls=2,
  no_old_program_execution=True,no_backup_recreation=True,ordinary_integrity_mac_queue_portable_gates_preserved=True,
  original_entry_native_apply_and_tests_byte_unchanged=True,
  accepted_source_schema_forms=['fixed Source23','fixed Restored23'],raw_ddl_and_two_phase_rehearsal_reused=True,
  Go_SQL_Native_calls=0,formal=False))
 save('transforms.json',dict(backup_go=bedits,cli_go=cedits,new_coordinator_initial_transforms=edits,
  additional_global_replacements_documented=True))
finally:
 close=guard.close()
 save('source-guard.json',close)
assert not close['errors'] and close['retained_handles_count']==0
for ref in refs:assert pin(Path(ref['path']))==ref
print(json.dumps(dict(status='SOURCE_BUILT',candidate_files=len(list((N/'candidate-root').rglob('*.*'))),guard_closed=close['retained_handles_count']==0,source_controls_ref=pin(N/'source-controls.json')),ensure_ascii=False))

