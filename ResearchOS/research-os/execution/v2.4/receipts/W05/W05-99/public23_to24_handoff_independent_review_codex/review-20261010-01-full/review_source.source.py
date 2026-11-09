from pathlib import Path
import difflib, hashlib, json, re, traceback, types

R = Path(r'D:/作品集/ResearchOS/research-os')
B = R/'execution/v2.4/receipts/W05/W05-99'
W = R/'execution/v2.4/receipts/W09/W09-99'
D = Path(__file__).resolve().parent
N = B/'public23_to24_handoff_source_codex/handoff-20261010-01'
support = W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
raw = support.read_bytes()
assert len(raw) == 4940 and hashlib.sha256(raw).hexdigest() == '567f53cadfab3781d6345ed1c6b04b52b85135e0843ce3c217e2f7fadf2a021a'
s = types.ModuleType('handoff_review_support');s.__file__ = str(support)
exec(compile(raw, str(support), 'exec'), s.__dict__);s.D = D
hdf_ref = s.exact_ref(N/'HDF.json', 'af98c0d9a77569cdaa0e0da407d667235364d6fb0d87f93a70304612ef144c81', 8733)
mf_ref = s.exact_ref(N/'MF.json', '299d1cbf8ba78e06d6bb762d9ec7461ecadfbfe78d242280821480aeb2f9f3b3', 11179)
assert s.pin(N/'HDF.json') == hdf_ref and s.pin(N/'MF.json') == mf_ref
hdf = json.loads((N/'HDF.json').read_bytes()); mf = json.loads((N/'MF.json').read_bytes())
assert s.pin(hdf['source_input_pins_ref']['path']) == hdf['source_input_pins_ref']
inputs = json.loads(Path(hdf['source_input_pins_ref']['path']).read_bytes())['inputs']
refs = [hdf_ref, mf_ref] + mf['members'] + inputs + [s.pin(Path(__file__)), s.pin(support)]
refs = list({ref['path']: ref for ref in refs}.values())
g = s.guard(); checks = []; evidence = {}; failure = None
def check(name, value, detail=None): checks.append({'name': name, 'passed': bool(value), 'detail': detail})
def text(path): return g.get_buffer(str(path)).decode('utf-8')
def functions(src):
    starts = list(re.finditer(r'^func (?:\([^\n]*\) )?([A-Za-z_][A-Za-z_0-9]*)\b', src, re.M))
    return {m.group(1): src[m.start():starts[i+1].start() if i+1<len(starts) else len(src)] for i,m in enumerate(starts)}
def cite(src, name):
    match = re.search(r'^func (?:\([^\n]*\) )?'+re.escape(name)+r'\b', src, re.M)
    assert match is not None
    return {'function':name, 'line':src[:match.start()].count('\n')+1}
try:
    g.acquire(refs)
    hdf = json.loads(g.get_buffer(hdf_ref['path'])); mf = json.loads(g.get_buffer(mf_ref['path']))
    targets = json.loads(g.get_buffer(hdf['integration_targets_ref']['path']))['targets']
    cr = N/'candidate-root'; domain = cr/'internal/domain'
    handoff = text(domain/'backup_prepared_abandonment_handoff.go')
    backup = text(domain/'backup.go'); cli = text(cr/'ops/backup/main.go')
    upgrade = text(domain/'backup_prepared_abandonment_upgrade.go')
    backup_base_ref = targets[0]['expected_base_ref']; cli_base_ref = targets[1]['expected_base_ref']
    base_backup = text(backup_base_ref['path']); base_cli = text(cli_base_ref['path'])
    contract = text(N/'CONTRACT.md'); template = json.loads(text(N/'binding.template.json'))
    check('published_Source_identity_and_no_author_self_authorization', hdf['actor_id'] == 'codex:/root/attach_restore_independent_review' and hdf['source_only'] is True and hdf['execution_grant'] is False and hdf['Main_adopted'] is False and hdf['formal'] is False)
    check('integration_four_exact_targets_and_no_wholesale_Main_copy', len(targets) == 4 and [t['repo_relative_path'] for t in targets] == ['internal/domain/backup.go','ops/backup/main.go','internal/domain/backup_prepared_abandonment_handoff.go','internal/domain/backup_prepared_abandonment_handoff_test.go'] and [t['operation'] for t in targets] == ['replace_exact_reviewed_base','replace_exact_reviewed_base','add_new_file','add_new_file'])
    base_root = Path(backup_base_ref['path']).parents[2]
    unchanged = []
    for ref in hdf['source_refs']:
        p = Path(ref['path']); rel = p.relative_to(cr).as_posix()
        if rel not in [t['repo_relative_path'] for t in targets]:
            base_path = base_root/rel
            ref_base = next(x for x in inputs if Path(x['path']) == base_path)
            unchanged.append({'relative_path':rel, 'candidate_ref':ref, 'base_ref':ref_base, 'equal':g.get_buffer(ref['path']) == g.get_buffer(ref_base['path'])})
    check('eleven_inherited_sources_and_original_apply_windows_authority_byte_unchanged', len(unchanged) == 11 and all(x['equal'] for x in unchanged), unchanged)
    old_functions, new_functions = functions(base_backup), functions(backup)
    changed_functions = [name for name in old_functions if old_functions[name] != new_functions.get(name)]
    # The function immediately preceding the added policy helper includes the
    # intervening struct declaration in this textual map; its body is unchanged.
    check('backup_mutations_are_confined_to_public_policy_and_restore_gates', set(changed_functions).issubset({'backupOrdinaryPublicPolicy','readBackupPolicy','restoreBackupPolicy'}) and set(new_functions)-set(old_functions) == {'backupOrdinaryPublicPolicy'}, {'changed_functions':changed_functions,'new_functions':sorted(set(new_functions)-set(old_functions))})
    check('old_native_apply_and_old_source_program_identity_rules_retained', 'preparedUpgradeProgramHashes(opt, false)' in upgrade and 'func upgradePreparedAbandonmentLocal' in upgrade and 'publicPreparedAbandonmentHandoff' not in upgrade)
    check('new_target_coordinator_distinct_programs_and_full_digest_binding', handoff.count('preparedUpgradeProgramHashes(opt, true)') == 3 and 'source == target' in handoff and 'len(value) != 71' in handoff and '!strings.HasPrefix(value, "sha256:")' in handoff and 'PREPARED_UPGRADE_MATCHING_PROGRAM_REQUIRED' in upgrade)
    check('new_binding_strict_fields_trailing_document_and_explicit_zero_exit', 'dec.DisallowUnknownFields()' in handoff and 'dec.Decode(new(any)); err != io.EOF' in handoff and 'b.ObservedBackupExit == nil || *b.ObservedBackupExit != 0' in handoff and 'b.SourceBackupOperation != "create"' in handoff)
    check('producer_existing_backup_manifest_stdout_and_observation_exact_pins', 'Digest(rawManifest) != b.BackupManifestSHA256' in handoff and 'Hash(manifest) != Hash(stdout)' in handoff and 'preparedHandoffReadRef(b.ProducerObservation)' in handoff and 'ref.Bytes > 128*1024*1024' in handoff and 'int64(len(raw)) != ref.Bytes || Digest(raw) != ref.SHA256' in handoff)
    check('public_format_exact_migration23_and_empty_purpose', 'manifest.Format != "RESEARCHOS_BACKUP_V1"' in handoff and 'len(manifest.Purpose) != 0' in handoff and 'Hash(manifest.Migrations) != Hash(upgradeVersions(23))' in handoff)
    check('ordinary_public_MAC_AEAD_cipher_file_pin_portable_queue_workspace_gates_retained', 'hmac.Equal([]byte(m.MAC), []byte(backupMAC(m, key)))' in backup and 'backupOrdinaryPublicPolicy(policy) && files["portable.json"] == nil' in backup and 'if backupOrdinaryPublicPolicy(policy) {' in backup and 'backupQueueState(db)' in backup and 'backupWorkspaceRestorePaths(files, directory, destination)' in backup and old_functions['backupCipher'] == new_functions['backupCipher'])
    check('protected_artifact_allowProtected_gate_not_enabled_by_new_policy', 'policy == nil || policy.allowProtected == nil' in backup and 'policy.allowProtected == nil' in backup and 'allowProtected:' not in handoff and 'publicPreparedAbandonmentHandoff: true' in handoff)
    check('new_existing_snapshot_fresh_destination_and_alias_overlap_checks', '&opt.Snapshot' in handoff and 'upgradePath(opt.Destination, false)' in handoff and 'upgradeInside(a, b) || upgradeInside(b, a)' in handoff and 'os.SameFile(a, b)' in handoff and '&handoff.BindingFile' in handoff)
    check('original_exclusive_database_and_root_lease_span_all_handoff_checks', 'acquirePreparedUpgradeRootLease(filepath.Dir(opt.Source))' in handoff and 'upgradeOpenExclusive(ctx, opt.Source)' in handoff and 'lease.Check()' in handoff and 'defer db.Close()' in handoff)
    check('only_exact_Source23_or_Restored23_accepted_with_corresponding_target', 'if schema == schemas.Restored23' in handoff and 'targetSchema = schemas.Restored24' in handoff and 'else if schema != schemas.Source23' in handoff and 'PREPARED_UPGRADE_SOURCE_SCHEMA' in handoff)
    check('source_rows_schema_releases_programs_and_input_backup_rechecked', 'Hash(current) != Hash(original)' in handoff and 'currentSchema != sourceSchema' in handoff and 'Hash(a) != Hash(sourceRelease)' in handoff and 'Hash(b) != Hash(targetRelease)' in handoff and 'Hash(currentBinding) != Hash(binding)' in handoff and 'preparedHandoffVerifyBackup(opt, key, binding)' in handoff)
    check('isolated_snapshot_matches_source_rows_and_workspace_before_recovery', 'policy.beforeRecovery = checkSnapshot' in handoff and 'Hash(rows) != Hash(original)' in handoff and 'Hash(identity) != Hash(workspace)' in handoff and 'policy.preservePreparedAbandonmentUpgradeWorkspaces = checkSnapshot' in handoff)
    check('DDL_callback_after_existing_recovery_fence_and_acceptance_checks', backup.index('svc.backupFence(ctx)') < backup.index('svc.backupRecomputeAcceptance()') < backup.index('policy.afterRecovery(db)') and 'policy.afterRecovery = func(restored *sql.DB)' in handoff and 'preparedUpgradeRecoveryInvariant(originalRecoveryRows, recoveryRows, opt.Destination)' in handoff and 'preparedUpgradeRehearseDDL(ctx, restored, sqls[23], baseline, schemas.Restored23, schemas.Restored24)' in handoff)
    check('fixed_SQL24_digest_rehearsal_rollback_and_commit_are_inherited', 'Digest(raw) != preparedUpgradeSQLHash' in upgrade and 'preparedUpgradeRowInvariant(before, after)' in upgrade and 'PREPARED_UPGRADE_ROLLBACK_SCHEMA' in upgrade and 'return tx.Commit()' in upgrade and 'preparedUpgradeIntegrity(ctx, tx)' in upgrade)
    check('old_program_and_existing_backup_not_executed_or_recreated', 'exec.Command' not in handoff and 'createBackup' not in handoff and 'CreateBackup' not in handoff and 'upgradePreparedAbandonmentLocal(' not in handoff and 'restoreBackupPolicy(ctx, opt.Snapshot, opt.Destination' in handoff)
    check('new_receipt_isolated_name_and_separate_from_original_apply_receipt', 'prepared-abandonment-public-backup-handoff.json' in handoff and 'researchos.prepared-abandonment-public-backup-rehearsal.v1' in handoff and 'RECORDED_PROGRAM_PINS_REQUIRE_SEPARATE_NATIVE_APPLY_AUTHORITY' in handoff and 'prepared-abandonment-rehearsal.json' not in handoff)
    check('provenance_is_not_source_json_qualification_or_execution_authority', 'EXTERNALLY_REVIEWED_OBSERVATION_INPUT_NOT_JSON_AUTHORITY' in handoff and 'EXTERNAL_INDEPENDENT_REVIEW_REQUIRED' in handoff and 'does not authenticate the asserted producer' in contract and 'nulls and is deliberately unusable' in contract)
    check('error_after_isolated_publication_preserved_without_auto_retry_cleanup', 'if err = checkSource(); err != nil { return report, err }' in handoff and 'backupDiscard(opt.Destination)' not in handoff and 'No automatic cleanup or reuse is attempted' in contract and 'use a fresh destination' in contract)
    check('new_CLI_calls_existing_domain_new_entry_and_returns_error_before_stdout', 'if command == "upgrade-prepared-backup"' in cli and 'domain.UpgradePreparedAbandonmentBackup(context.Background()' in cli and 'if e != nil { return e }' in cli and 'return json.NewEncoder(os.Stdout).Encode(r)' in cli)
    evidence = {'Source_hdf_ref':hdf_ref,'Source_mf_ref':mf_ref,'Source_contract_ref':hdf['contract_ref'],'source_refs':hdf['source_refs'],'integration_targets_ref':hdf['integration_targets_ref'],'references_held':refs,'new_coordinator_functions':[cite(handoff,n) for n in functions(handoff)],'base_upgrade_functions':[cite(upgrade,n) for n in ('preparedUpgradeProgramHashes','preparedUpgradeDDL','preparedUpgradeTemplate','preparedUpgradeRehearseDDL')], 'backup_changed_functions':changed_functions,'diff':list(difflib.unified_diff(base_backup.splitlines(),backup.splitlines(),fromfile='reviewed-base/backup.go',tofile='candidate/backup.go',lineterm=''))+list(difflib.unified_diff(base_cli.splitlines(),cli.splitlines(),fromfile='Main/ops/backup/main.go',tofile='candidate/ops/backup/main.go',lineterm='')),'new_Go_tests_executed':False,'new_product_calls':0}
except BaseException:
    failure = traceback.format_exc()
    raise
finally:
    closed = g.close()
    guard_ref = s.write('source-review-guard.closed.json', closed)
    result_ref = s.write('source-review-checks.json', {'schema':'researchos.public23-to24-independent-source-checks.v1','checks':checks,'count':len(checks),'passed':sum(c['passed'] for c in checks),'failed':sum(not c['passed'] for c in checks),'failure':failure,'evidence':evidence,'guard_ref':guard_ref,'prior_successful_controls_replayed':False,'Go_Native_SQL_TP_RootStage_model_calls':0,'formal_acceptance':False,'execution_grant':False})
assert closed['closed'] is True and closed['retained_handles_count'] == 0 and closed['errors'] == []
print(json.dumps({'result_ref':result_ref,'guard_ref':guard_ref,'count':len(checks),'passed':sum(c['passed'] for c in checks),'failed':[c for c in checks if not c['passed']],'retained_handles_count':0,'product_calls':0},ensure_ascii=False))
