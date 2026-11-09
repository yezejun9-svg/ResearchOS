import hashlib,json,re
from pathlib import Path
N=Path(__file__).resolve().parent;S=N/'source-root'
def pin(p):
 p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
checks=[]
def check(n,ok):checks.append(dict(name=n,passed=bool(ok)));assert ok,n
inverse=json.loads((N/'whole-file-inverse.json').read_bytes());oldfiles={}
for item in inverse['files']:
 old=Path(item['original_ref']['path']).read_bytes();new=Path(item['candidate_ref']['path']).read_bytes();oldfiles[item['target']]=old.decode()
 check('full_old_byte_inverse_'+item['target'],''.join(x for op in item['opcodes'] for x in op['old_lines']).encode()==old)
 check('full_new_byte_forward_'+item['target'],''.join(x for op in item['opcodes'] for x in op['new_lines']).encode()==new)
 check('pinned_candidate_'+item['target'],pin(item['candidate_ref']['path'])==item['candidate_ref'])
 if not item['substitutions']:check('unchanged_source_'+item['target'],old==new)
overlay=json.loads((N/'source-overlay.json').read_bytes())
check('exact_three_changed_paths',set(overlay['changed_paths'])=={'internal/domain/backup_restored21_upgrade.go','internal/domain/backup.go','internal/domain/backup_restored21_upgrade_test.go'})
check('dispatch_and_CLI_bytes_unchanged',set(overlay['unchanged_paths'])=={'internal/domain/backup_upgrade.go','ops/backup/main.go'})
handler=(S/'internal/domain/backup_restored21_upgrade.go').read_text(encoding='utf8');backup=(S/'internal/domain/backup.go').read_text(encoding='utf8');test=(S/'internal/domain/backup_restored21_upgrade_test.go').read_text(encoding='utf8')
oldhandler=oldfiles['internal/domain/backup_restored21_upgrade.go'];oldbackup=oldfiles['internal/domain/backup.go'].replace('\r\n','\n');oldtest=oldfiles['internal/domain/backup_restored21_upgrade_test.go']
check('profile_session_SQL_recovery_functions_byte_equal',handler[:handler.index('func upgradeRestored21Local(')]==oldhandler[:oldhandler.index('func upgradeRestored21Local(')])
check('plan_purpose_original_literals_equal',handler[handler.index('\tplan := Object'):handler.index('\tpolicy := &backupPolicy')]==oldhandler[oldhandler.index('\tplan := Object'):oldhandler.index('\tpolicy := &backupPolicy')])
check('no_assignment_into_purpose',not re.search(r'policy\.purpose\[[^\n]+\]\s*=',handler))
check('sessionEvidence_in_closure_scope',handler.index('var sessionEvidence Object')<handler.index('policy.afterRecovery ='))
check('phase_value_in_dedicated_field','policy.restored21SessionEvidence = sessionEvidence' in handler)
check('no_postreturn_Recovery_patch','if result.Recovery != nil' not in handler)
hook=handler[handler.index('func upgradeRestored21PublishEvidence('):]
check('report_hook_fixed_format_and_plan',all(x in hook for x in ('policy.format != localUpgradeFormat','plan["id"] != Restored21SessionUpgradePlan','RESTORE_RESTORED21_REPORT_POLICY_MISMATCH')))
check('same_top_level_field_value_assignment','recovery["restored21_session_initialization"] = evidence' in hook and 'evidence := policy.restored21SessionEvidence' in hook)
check('dedicated_hook_called_with_original_Recovery','upgradeRestored21PublishEvidence(policy, r.Recovery)' in backup)
check('old_nil_hook_noop','if policy == nil || policy.restored21SessionEvidence == nil { return nil }' in hook)
fields='source_schema_hash session_schema_hash before_rows_hash after_rows_hash numbered_ledger_unchanged old_typed_rows_unchanged client_sessions_created_empty restore_fence_preserved restored_barriers_refreshed external_actions_dispatched'
check('all_ten_fields_exact',('upgradeQueueFields(evidence,"'+fields+'")') in hook and len(fields.split())==10)
check('typed_hash_flags_and_action_validation',all(x in hook for x in ('.(string)','len(value) != 71','value[:7] != "sha256:"',"c >= 'a' && c <= 'f'",'.(bool)','.(int)','actions != 0')))
check('only_success_writes_Recovery',hook.count('recovery["restored21_session_initialization"] = evidence')==1 and hook.index('actions != 0')<hook.index('recovery["restored21_session_initialization"] = evidence'))
check('afterRecovery_then_reportHook_then_write_then_rename',backup.index('if e = policy.afterRecovery(db)')<backup.index('if policy.restored21SessionEvidence != nil')<backup.index('backupWrite(filepath.Join(stage, "restore-report.json"), Bytes(r))')<backup.index('os.Rename(stage, destination)',backup.index('backupWrite(filepath.Join(stage, "restore-report.json"), Bytes(r))')))
def function(text,name):
 start=text.index('func '+name+'(');end=text.find('\nfunc ',start+1);return text[start:end] if end>=0 else text[start:]
for name in ('backupMAC','readBackupPolicy','backupWrite','backupNewStage'):
 check('authorization_or_publication_helper_unchanged_'+name,function(backup,name)==function(oldbackup,name))
check('full_purpose_MAC_and_exact_match_preserved','m.MAC = backupMAC(m, key)' in backup and 'Hash(m.Purpose) != Hash(policy.purpose)' in backup and 'BACKUP_PURPOSE_MISMATCH' in backup)
check('old_restore_report_write_bytes_unchanged','backupWrite(filepath.Join(stage, "restore-report.json"), Bytes(r))' in backup and 'os.Rename(stage, destination)' in backup)
check('test_reads_disk_and_compares_entire_Recovery','json.Unmarshal(persistedRaw,&persisted)' in test and 'bytes.Equal(Bytes(report.Recovery),Bytes(persisted.Recovery))' in test)
check('top_level_field_contract_preserved','report.Recovery["restored21_session_initialization"].(Object)' in test and 'report.Recovery["local_upgrade"].(Object)' not in test)
check('negative_rejections_assert_no_public_report','rejected source published restore report' in test and 'filepath.Join(opt.Destination,"restore-report.json")' in test)
check('negative_hook_and_oldplan_controls_declared',all(x in test for x in ('"wrong-plan","wrong-format","missing-field","extra-field","wrong-type","wrong-hash","nonzero-actions"','old-plan nil hook changed report','bytes.Equal(purposeBefore,Bytes(purpose))','restored21ReportHookControls(t)')))
check('test_roster_parent_names_unchanged',re.findall(r'^func (TestRestored21\w+)',test,re.M)==re.findall(r'^func (TestRestored21\w+)',oldtest,re.M))
check('nine_parents_four_leafs_source_only',len(re.findall(r'^func TestRestored21',test,re.M))==9 and '"foreign","partial-session","session-addon","missing-restore-trigger"' in test)
for v in json.loads((N/'input-pins.before.json').read_bytes()):check('unchanged_input_'+v['path'],pin(v['path'])==v)
result=dict(status='PASS_SOURCE_STATIC_ONLY',count=len(checks),checks=checks,actual_Go_parser_compile_format_SQL_native=False,actual_test_count=0,AST_statement='Old bytes reconstructed identically; no Go AST parser executed',new_original_failures=[])
assert not (N/'HDF.json').exists() and not (N/'MF.json').exists()
with (N/'source-controls.json').open('wb') as f:f.write((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps(dict(status=result['status'],checks=len(checks),controls_ref=pin(N/'source-controls.json'))))
