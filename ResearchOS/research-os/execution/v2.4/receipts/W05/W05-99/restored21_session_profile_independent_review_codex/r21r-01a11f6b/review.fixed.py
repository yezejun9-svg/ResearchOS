import sys
sys.dont_write_bytecode=True
import hashlib,json,re,types
from pathlib import Path
N=Path(__file__).resolve().parent
R=Path("D:/作品集/ResearchOS/research-os");W=R/"execution/v2.4/receipts/W05/W05-99"
C=W/"restored21_session_profile_source_codex/r21s-1a11f5e"
GP=W/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
forbidden={str((R/"execution/v2.4"/(n+".json")).resolve()).casefold() for n in ("checkpoint","path_ownership","step_state","commands")}
def pin(p):
 p=Path(p).resolve();assert str(p).casefold() not in forbidden
 b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def verify(v):
 p=pin(v["path"]);assert (p["sha256"],p["bytes"])==(v["sha256"].removeprefix("sha256:"),v["bytes"]);return p
def save(n,v):
 with (N/n).open("x",encoding="utf-8",newline="\n") as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+"\n")
checks=[]
def ck(n,v):
 checks.append(dict(name=n,passed=bool(v)))
 if not v:raise AssertionError(n)
h=verify(dict(path=str(C/"HDF.json"),sha256="e4fafc6053105cc776d344f8d618b14c3514ecfb44913b80effbb1499d459d91",bytes=3641))
m=verify(dict(path=str(C/"MF.json"),sha256="c91eb027dc761b3b12589a084d17526645d68f11e39e0ba50f511d378ac46c5d",bytes=8463))
H=json.loads((C/"HDF.json").read_bytes());M=json.loads((C/"MF.json").read_bytes());inputs=json.loads((C/"input-pins.before.json").read_bytes())
refs=[h,m]+[verify(v) for v in M["members"]]+[verify(v) for v in inputs]+[pin(GP),pin(__file__),pin(sys.executable)]
refs=list({v["path"].casefold():v for v in refs}.values())
ck("guard_exact",pin(GP)["sha256"]=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85")
gm=types.ModuleType("r21_source_guard");gm.__file__=str(GP);sys.modules[gm.__name__]=gm
exec(compile(GP.read_bytes(),str(GP),"exec"),gm.__dict__)
g=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
try:
 g.acquire(refs)
 def raw(p):return g.get_buffer(str(Path(p).resolve()))
 def txt(p):return raw(p).decode().replace("\r\n","\n")
 def obj(p):return json.loads(raw(p))
 S=C/"source-root";prod=txt(S/"internal/domain/backup_restored21_upgrade.go");test=txt(S/"internal/domain/backup_restored21_upgrade_test.go")
 backup=txt(S/"internal/domain/backup.go");dispatch=txt(S/"internal/domain/backup_upgrade.go")
 contract=obj(C/"profile-contract.json")
 A=next(Path(v["path"]) for v in inputs if v["path"].endswith("a21-contract-084378e0\\contract.json"))
 a21=obj(A);queuepath=Path(a21["source_refs"]["queue21to22"]["path"]);queue=txt(queuepath)
 fence=txt(a21["source_refs"]["session_fence"]["path"])
 ck("source_HDF_manifest",H["manifest_ref"]==m)
 ck("author_count_is_static70_actual0",H["source_check_count"]==70 and H["actual_test_count"]==0 and H["Go_parser_compiler_formatter_executed"] is False)
 ck("author70_controls_all_pass",len(obj(C/"source-controls.json")["checks"])==70 and all(c["passed"] for c in obj(C/"source-controls.json")["checks"]))
 inverse=obj(C/"whole-file-inverse.final.json")
 ck("five_source_files",len(inverse["files"])==5)
 for f in inverse["files"]:
  old=b"" if f["original_was_absent"] else raw(f["original_ref"]["path"]);new=raw(f["candidate_ref"]["path"])
  ck("whole_inverse_"+f["target"],"".join(z for op in f["opcodes"] for z in op["old_lines"]).encode()==old)
  ck("whole_forward_"+f["target"],"".join(z for op in f["opcodes"] for z in op["new_lines"]).encode()==new)
  ck("exact_pin_"+f["target"],pin(f["candidate_ref"]["path"])==f["candidate_ref"])
 by={f["target"]:f for f in inverse["files"]}
 rel="internal/domain/backup_upgrade.go";old=raw(by[rel]["original_ref"]["path"]).decode()
 nl="\r\n" if "\r\n" in old else "\n";anchor="func upgradeLocal(ctx context.Context, opt LocalUpgradeOptions, verifier upgradeVerifier) (RestoreReport, error) {"
 expected=old.replace(anchor,anchor+nl+"\tif opt.Plan == Restored21SessionUpgradePlan {"+nl+"\t\treturn upgradeRestored21Local(ctx, opt, verifier)"+nl+"\t}")
 ck("dispatch_exact_only_inserted_new_plan",expected.encode()==raw(S/rel))
 rel="ops/backup/main.go";old=raw(by[rel]["original_ref"]["path"])
 expected=old.replace(b"schema20-to21-research-pending-windows-v1 (exact releases only)",b"schema20-to21-research-pending-windows-v1 or restored21-session-to22-client-command-queue-v1 (exact releases only)")
 ck("CLI_entire_bytes_only_help",expected==raw(S/rel))
 rel="internal/domain/backup.go";old=raw(by[rel]["original_ref"]["path"]).decode();nl="\r\n" if "\r\n" in old else "\n"
 priorline=next(l for l in old.splitlines(keepends=True) if l.startswith("\tpreserveHistory20UpgradeWorkspaces"))
 expected=old.replace(priorline,priorline+"\tpreserveRestored21UpgradeWorkspaces func(*sql.DB) error"+nl)
 anchor="\tif policy != nil && policy.preserveHistory20UpgradeWorkspaces != nil {"
 replacement="""\tif policy != nil && policy.preserveRestored21UpgradeWorkspaces != nil {
        plan, ok := policy.purpose["plan"].(Object)
        if !ok || policy.format != localUpgradeFormat || plan["id"] != Restored21SessionUpgradePlan {
            return r, fmt.Errorf("RESTORE_RESTORED21_WORKSPACE_POLICY_MISMATCH")
        }
        e = policy.preserveRestored21UpgradeWorkspaces(db)
    } else if policy != nil && policy.preserveHistory20UpgradeWorkspaces != nil {""".replace("\n",nl)
 expected=expected.replace(anchor,replacement)
 ck("private_policy_entire_bytes_only_new_field_branch",expected.encode()==raw(S/rel))
 co_old=queue[queue.index("func upgradeQueueLocal("):queue.index("func (g *upgradeQueueProtection) refresh(")]
 co_new=prod[prod.index("func upgradeRestored21Local("):]
 substitutions=[
 ("func upgradeQueueLocal(","func upgradeRestored21Local("),
 ("expectedSourceSchema, expectedTargetSchema, e := upgradeQueueTemplate(ctx, sqls, contracts)","expectedSourceSchema, expectedSessionSchema, expectedTargetSchema, e := upgradeRestored21Template(ctx, sqls, contracts)"),
 ("policy.preserveQueueUpgradeWorkspaces =","policy.preserveRestored21UpgradeWorkspaces ="),
 ("upgradeQueueRecoveryInvariant(original, rows, opt.Destination)","upgradeRestored21RecoveryInvariant(original, rows, opt.Destination)"),
 ('"source_path_hash": Hash(opt.Source), "target_path_hash": Hash(opt.Destination)}','"source_path_hash": Hash(opt.Source), "target_path_hash": Hash(opt.Destination),\n        "session_schema_hash": expectedSessionSchema, "session_sql_hash": Digest(sqls[22]),\n        "origin_qualification": "RESTORED21_SCHEMA_PROFILE_ONLY_RELEASE_PROGRAM_PROVENANCE_SEPARATE"}'),
 ("svc := &Service{DB: db, Contracts: contracts}","var sessionEvidence Object\n    svc := &Service{DB: db, Contracts: contracts}"),
 ("return restoreBackupPolicy(ctx, opt.Snapshot, opt.Destination, RestoreOptions{","result, restoreErr := restoreBackupPolicy(ctx, opt.Snapshot, opt.Destination, RestoreOptions{"),
 ("return upgradeQueueMigration(ctx, target, sqls[21], sqls[22])","var installErr error\n            sessionEvidence, installErr = upgradeRestored21Sessions(ctx,target,sqls[22],expectedSourceSchema,expectedSessionSchema)\n            if installErr != nil { return installErr }\n            return upgradeQueueMigration(ctx, target, sqls[21], sqls[22])"),
 ("}, policy)\n}",'}, policy)\n    if result.Recovery != nil { result.Recovery["restored21_session_initialization"] = sessionEvidence }\n    return result, restoreErr\n}')]
 expected=co_old;back=co_new
 for a,b in substitutions:ck("single_coordinator_change_"+a[:55],expected.count(a)==1);expected=expected.replace(a,b)
 for a,b in reversed(substitutions):back=back.replace(b,a)
 ck("coordinator_independent_entire_forward",expected==co_new)
 ck("coordinator_independent_entire_inverse",back==co_old)
 ck("new_prefix_exact_source",prod[:prod.index("func upgradeRestored21Local(")]==txt(C/"profile-prefix.go.txt"))
 ck("old_profiles_SQL_not_overlaid",not (S/"internal/domain/backup_queue_upgrade.go").exists() and not (S/"internal/domain/backup_history20_upgrade.go").exists() and not list(S.rglob("*.sql")))
 session=prod[prod.index("func upgradeRestored21Sessions("):prod.index("func upgradeRestored21RecoveryInvariant(")]
 template=prod[prod.index("func upgradeRestored21Template("):prod.index("func upgradeRestored21Sessions(")]
 recovery=prod[prod.index("func upgradeRestored21RecoveryInvariant("):prod.index("func upgradeRestored21Local(")]
 def ordered(name,text,parts):
  positions=[];cursor=0
  for p in parts:pos=text.index(p,cursor);positions.append(pos);cursor=pos+len(p)
  ck(name,positions==sorted(positions) and len(set(positions))==len(positions))
 ordered("profile_build_order",template,["sqls[:20]",".backupFence(ctx)","upgradeHistory20Migration(ctx,db,sqls[20])","source,err:=backupSchema(db)","db.ExecContext(ctx,string(sqls[22]))","installClientSessionFence(ctx,db,false)","session,err:=backupSchema(db)","upgradeQueueMigration(ctx,db,sqls[21],sqls[22])","target,err:=backupSchema(db)"])
 ordered("session_transaction_sequence",session,["Digest(additive)!=upgradeQueueSessionHash","db.BeginTx(ctx,nil)","defer tx.Rollback()","upgradeRestored21Schema(tx)","before,err:=upgradeQueueRows(tx)","tx.ExecContext(ctx,string(additive))","installClientSessionFence(ctx,tx,false)","after,err:=upgradeQueueRows(tx)","!reflect.DeepEqual(rows,current)","schema!=sessionSchema","PRAGMA integrity_check","PRAGMA foreign_key_check","tx.Commit()"])
 for token in ['len(sqls)!=23','Digest(sqls[20])!=upgradeHistory20SQLHash','Digest(sqls[21])!=upgradeQueueSQLHash','Digest(sqls[22])!=upgradeQueueSessionHash']:
  ck("exact_template_pin_"+token,token in template)
 for token in ['SELECT type,name,tbl_name,coalesce(sql,\'\') FROM sqlite_master ORDER BY type,name','UPGRADE_SESSION_UNEXPECTED_TABLE','len(sessions)!=0','numbered_ledger_unchanged','old_typed_rows_unchanged','restored_barriers_refreshed']:
  ck("new_profile_invariant_"+token,token in prod)
 ck("session_no_numbered_ledger_mutation","INSERT INTO schema_migrations" not in session and "UPDATE schema_migrations" not in session and "DELETE " not in session)
 ck("no_current_New_or_DROP_production",not re.search(r"\bNew\s*\(|\bDROP\b",prod))
 ck("recovery_exact_empty_session_projection",'before["client_sessions"]' in recovery and 'len(sessions)!=0' in recovery and 'if table!="client_sessions"{projected[table]=rows}' in recovery and 'return upgradeQueueRecoveryInvariant(before,projected,destination)' in recovery)
 ck("public_entry_unchanged_real_verifier",'func UpgradeLocal' in dispatch and 'provider: &protectedstore.FrozenProvider{}' in dispatch and 'protectedstore.QueryFrozenService("aggregate")' in dispatch)
 for token in ["upgradePaths(&opt)","upgradeQueueRelease(opt.SourceRoot, 21)","upgradeQueueRelease(opt.TargetRoot, 22)","upgradeOpenExclusive(ctx, opt.Source)","defer db.Close()","guard.refresh(db)","guard.refresh(restored)","upgradeQueueWorkspaceIdentity(db, opt)","UPGRADE_SOURCE_DRIFT","UPGRADE_RELEASE_CHANGED","UPGRADE_PROGRAM_CHANGED","defer clear(key)","createBackupPolicy(ctx, opt.Snapshot, key, policy)"]:
  ck("coordinator_retains_"+token,token in co_new)
 restore=backup[backup.index("func restoreBackupPolicy("):]
 ordered("failure_validation_before_publication",restore,["defer backupDiscard(stage)","policy.beforeRecovery(db)","svc.backupFence(ctx)","opt.Migration(ctx, db)","backupIntegrityPolicy(db, policy)","policy.afterRecovery(db)","db.Close()","backupWrite(filepath.Join(stage, \"restore-report.json\"), Bytes(r))","os.Rename(stage, destination)"])
 ck("migration_failure_discards_candidate_retains_snapshot","MIGRATION_FAILED: isolated copy discarded; stable backup retained:" in restore)
 ck("fence_false_does_not_refresh_barriers","if restored {" in fence and 'ON CONFLICT(project,run) DO UPDATE SET restored_at=excluded.restored_at' in fence and "installClientSessionFence(ctx,tx,false)" in session)
 ck("A21_prohibitions_preserved",a21["existing_public_qualified_A21_session_install_entry"] is False and a21["formal_acceptance"] is False and "existing_H20R1_and_queue_templates_unchanged" in a21["recommended_new_Source_boundary"])
 names=re.findall(r"^func (TestRestored21\w+)\(t \*testing.T\)",test,re.M)
 ck("nine_unique_parents",len(names)==len(set(names))==9)
 ck("four_drift_leaves", '[]string{"foreign","partial-session","session-addon","missing-restore-trigger"}' in test)
 ck("planned13_actual0",obj(C/"test-roster.json")["planned_test2json_unique_runs"]==13 and H["actual_test_count"]==0)
 ck("fixture_uses_H20_public_then_plain21","prior,_:=history20Fixture(t)" in test and "UpgradeLocal(context.Background(),prior)" in test and 'len(before["schema_migrations"])!=21' in test and not re.search(r"\bNew\s*\(",test))
 ck("fixture_program_truthful","PUBLIC_FIXTURE_MAINTENANCE22_PROGRAM_BYTES" in test and "not a genuine historical release proof" in test)
 ck("late_helper_test_not_public_claim","not public coordinator failure evidence" in test and H["public_late_failure_control"]=="OPEN")
 ck("provenance_and_fullchain_remain_open",H["genuine21_22_release_program_qualified"] is False and H["B_branch"]=="OPEN" and H["overall20to24"]=="OPEN" and not H["formal_acceptance"])
 ck("no_report_or_contract_claims_runtime",contract["actual_execution"] is False and contract["formal_acceptance"] is False)
 # This is lexical delimiter checking, not Go parsing, type checking or compilation.
 for p in S.rglob("*.go"):
  text=txt(p);clean=re.sub(r'//[^\n]*|/\*[\s\S]*?\*/|`[^`]*`|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',"",text);stack=[];pairs={")":"(","]":"[","}":"{"};valid=True
  for ch in clean:
   if ch in "([{":stack.append(ch)
   elif ch in pairs:
    if not stack or stack.pop()!=pairs[ch]:valid=False;break
  ck("lexical_balance_only_"+p.name,valid and not stack)
 # Record the new receipt split without executing either function.
 appendline=next(i for i,l in enumerate(prod.splitlines(),1) if 'result.Recovery["restored21_session_initialization"]' in l)
 writeline=next(i for i,l in enumerate(backup.splitlines(),1) if 'backupWrite(filepath.Join(stage, "restore-report.json"), Bytes(r))' in l)
 ck("receipt_append_occurs_after_restore_returns",co_new.index('}, policy)')<co_new.index('result.Recovery["restored21_session_initialization"]'))
 finding=dict(id="R21-RECEIPT-01",priority="P2",blocking_source_gate=False,title="Session receipt absent from persisted restore report",file=pin(S/"internal/domain/backup_restored21_upgrade.go"),line=appendline,related_file=pin(S/"internal/domain/backup.go"),related_line=writeline,impact="The returned/CLI report includes session evidence, but restore-report.json written before publication lacks it; disk-only auditors cannot recover before/after session row hashes from this file.",recommendation="Attach the session evidence to the report before the existing restore-report write and publication; verify returned and persisted fields agree in the future actual qualification.",runtime_reproduced=False)
 save("findings.json",[finding])
 ck("all_exact_inputs_unchanged_while_held",all(pin(v["path"])==v for v in refs))
finally:
 cleanup=g.close();save("source-guard.cleanup.fixed.actual.json",cleanup)
ck("all_actual_guard_handles_closed",cleanup["closed"] is True and not cleanup["errors"] and cleanup["retained_handles_count"]==0)
save("checks.json",checks);save("input-pins.json",refs)
save("result.json",dict(status="SOURCE_ACCEPTED_WITH_NONBLOCKING_RECEIPT_GAP_PENDING_RUNTIME_QUALIFICATION",independent_checks=len(checks),finite_input_count=len(refs),P1_findings=0,P2_findings=1,actual_test_count=0,expected_parent_count=9,expected_leaf_count=4,Go_parser_compiler_formatter_executed=False,SQL_native_Git_API_model_executed=False,current_canonical_read_locked_written=False,formal_acceptance=False,formal_case_accepted_delta=0,actual_source_read_guard=True,all_acquired_guards_closed=True,new_original_failures=[]))
print(json.dumps(dict(status="PASS_SOURCE_WITH_P2_NONBLOCKING",checks=len(checks),inputs=len(refs),findings_ref=pin(N/"findings.json"),result_ref=pin(N/"result.json"))))

