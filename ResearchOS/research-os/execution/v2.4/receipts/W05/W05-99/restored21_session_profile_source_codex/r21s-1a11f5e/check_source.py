import hashlib,json,re
from pathlib import Path
N=Path(__file__).resolve().parent;S=N/'source-root'
def pin(p):
 p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
checks=[]
def check(name,ok):checks.append(dict(name=name,passed=bool(ok)));assert ok,name
inverse=json.loads((N/'whole-file-inverse.json').read_bytes())
for f in inverse['files']:
 original=b'' if f['original_was_absent'] else Path(f['original_ref']['path']).read_bytes();candidate=Path(f['candidate_ref']['path']).read_bytes()
 check('old_inverse_'+f['target'],''.join(z for op in f['opcodes'] for z in op['old_lines']).encode()==original)
 check('candidate_forward_'+f['target'],''.join(z for op in f['opcodes'] for z in op['new_lines']).encode()==candidate)
 check('candidate_pin_'+f['target'],pin(f['candidate_ref']['path'])==f['candidate_ref'])
inputs=json.loads((N/'input-pins.before.json').read_bytes())
for v in inputs:check('unchanged_input_'+v['path'],pin(v['path'])==v)
prod=(S/'internal/domain/backup_restored21_upgrade.go').read_text(encoding='utf8');test=(S/'internal/domain/backup_restored21_upgrade_test.go').read_text(encoding='utf8')
oldqueue=next(v for v in inputs if v['path'].endswith('backup_queue_upgrade.go'));oldq=Path(oldqueue['path']).read_text(encoding='utf8')
check('old_queue_profile_not_written',not (S/'internal/domain/backup_queue_upgrade.go').exists())
check('old_history20_profile_not_written',not (S/'internal/domain/backup_history20_upgrade.go').exists())
check('no_SQL_files_written',not list(S.rglob('*.sql')))
check('no_Go_current_constructor_call',not re.search(r'\bNew\s*\(',prod))
check('no_DROP_in_production',not re.search(r'\bDROP\b',prod))
check('new_profile_fixed_plan','const Restored21SessionUpgradePlan = "restored21-session-to22-client-command-queue-v1"' in prod)
check('whole_schema_query_equal_existing','SELECT type,name,tbl_name,coalesce(sql,\'\') FROM sqlite_master ORDER BY type,name' in prod)
check('template20_restore21_order',prod.index('sqls[:20]')<prod.index('.backupFence(ctx)')<prod.index('upgradeHistory20Migration(ctx,db,sqls[20])')<prod.index('source,err:=backupSchema(db)')<prod.index('string(sqls[22])')<prod.index('session,err:=backupSchema(db)')<prod.index('upgradeQueueMigration(ctx,db,sqls[21],sqls[22])'))
session=prod[prod.index('func upgradeRestored21Sessions'):prod.index('func upgradeRestored21RecoveryInvariant')]
check('session_source_check_inside_transaction',session.index('db.BeginTx')<session.index('upgradeRestored21Schema(tx)')<session.index('tx.ExecContext(ctx,string(additive))'))
check('session_fence_false_only','installClientSessionFence(ctx,tx,false)' in session and 'installClientSessionFence(ctx,tx,true)' not in session)
check('session_old_typed_rows_including_ledger_exact','!reflect.DeepEqual(rows,current)' in session and 'table == "schema_migrations"' not in session)
check('session_new_table_only_empty','table!="client_sessions"' in session and 'len(sessions)!=0' in session)
check('session_integrity_foreign_keys_and_rollback',all(v in session for v in ('defer tx.Rollback()','PRAGMA integrity_check','PRAGMA foreign_key_check','tx.Commit()')))
check('session_no_numbered_ledger_write','INSERT INTO schema_migrations' not in session)
check('production_uses_existing_queue_migration',prod.count('upgradeQueueMigration(')==2)
check('restore_audit_separate_and_explicit_empty_session',all(v in prod for v in ('upgradeRestored21RecoveryInvariant(original, rows, opt.Destination)','upgradeQueueRecoveryInvariant(before,projected,destination)','sessionEvidence, installErr = upgradeRestored21Sessions','result.Recovery["restored21_session_initialization"] = sessionEvidence')))
check('new_owned_source_lock_preserved','defer db.Close() // The native source lock spans snapshot through publication.' in prod and 'upgradeOpenExclusive(ctx, opt.Source)' in prod)
check('all_existing_protection_and_snapshot_guards_present',all(v in prod for v in ('guard.refresh(db)','guard.refresh(restored)','upgradeQueueWorkspaceIdentity(db, opt)','UPGRADE_RELEASE_CHANGED','UPGRADE_PROGRAM_CHANGED','UPGRADE_SNAPSHOT_HISTORY_MISMATCH','UPGRADE_SOURCE_DRIFT','createBackupPolicy(ctx, opt.Snapshot, key, policy)','restoreBackupPolicy(ctx, opt.Snapshot, opt.Destination')))
dispatch=(S/'internal/domain/backup_upgrade.go').read_text(encoding='utf8');backup=(S/'internal/domain/backup.go').read_text(encoding='utf8');cli=(S/'ops/backup/main.go').read_text(encoding='utf8')
check('dispatch_exact_newplan', 'if opt.Plan == Restored21SessionUpgradePlan {\n\t\treturn upgradeRestored21Local(ctx, opt, verifier)' in dispatch)
check('private_backup_policy_fixed_newplan',all(v in backup for v in ('preserveRestored21UpgradeWorkspaces func(*sql.DB) error','plan["id"] != Restored21SessionUpgradePlan','RESTORE_RESTORED21_WORKSPACE_POLICY_MISMATCH')))
check('CLI_help_newplan_only','restored21-session-to22-client-command-queue-v1 (exact releases only)' in cli)
names=re.findall(r'^func (TestRestored21\w+)\(t \*testing.T\)',test,re.M)
check('exact_nine_source_parent_tests',len(names)==9 and len(set(names))==9)
check('fixture_accepted_H20_path_only','prior,_:=history20Fixture(t)' in test and 'UpgradeLocal(context.Background(),prior)' in test and not re.search(r'\bNew\s*\(',test))
check('fixture_not_genuine_program_claim','PUBLIC_FIXTURE_MAINTENANCE22_PROGRAM_BYTES' in test and 'not a genuine historical release proof' in test)
check('test_postDDL_rollback_exact_error','UPGRADE_RESTORED21_SESSION_SCHEMA' in test and 'sha256:wrong-target-profile' in test)
check('test_queue_ledger_failure_is_component_only','not public coordinator failure evidence' in test and 'fixture ledger failure' in test)
check('test_matching_key_negative_exact','BACKUP_MANIFEST_INVALID' in test and 'files!=nil' in test)
# Lexical balance is deliberately not Go parsing or compilation.
def tokens(text):
 return re.sub(r'//[^\n]*|/\*[\s\S]*?\*/|`[^`]*`|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'','',text)
for path in S.rglob('*.go'):
 stack=[];pairs={')':'(',']':'[','}':'{'}
 for ch in tokens(path.read_text(encoding='utf8')):
  if ch in '([{':stack.append(ch)
  elif ch in pairs:
   if not stack or stack.pop()!=pairs[ch]:raise AssertionError('lexical delimiter '+str(path))
 check('Go_lexical_delimiters_only_'+str(path.relative_to(S)),not stack)
result=dict(status='PASS_SOURCE_STATIC_ONLY',checks=checks,count=len(checks),Go_parser_compiler_formatter_executed=False,SQL_native_tests_executed=False,new_product_original_failures=[],test_parents_source_only=names)
with (N/'source-controls.json').open('xb') as f:f.write((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode())
roster=dict(status='SOURCE_DECLARATIONS_NOT_COMPILED_OR_EXECUTED',parent_tests=names,parent_count=9,drift_subtests=['foreign','partial-session','session-addon','missing-restore-trigger'],planned_test2json_unique_runs=13,genuine_release_program_provenance=False,fixture_origin='Accepted H20 public fixture construction and UpgradeLocal; no current New or ledger truncation',runtime_followup_required=['Independent Source acceptance','Root-owned isolated build and compiler/runtime inventory','Actual 9 parents and 4 drift subtests','Real maintenance21 and22 release/program qualification','Matching original backup/recovery proof','Public coordinator late-phase failure/no-publication control','Independent single-writer cutover'],overall20to24='OPEN')
with (N/'test-roster.json').open('xb') as f:f.write((json.dumps(roster,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps(dict(status=result['status'],checks=len(checks),source_parents=len(names),controls_ref=pin(N/'source-controls.json'))))
