package domain

import (
 "context"
 "database/sql"
 "fmt"
 "os"
 "path/filepath"
 "reflect"
 "researchos.local/research-os/internal/store"
)

// This fixed maintenance plan recognizes restored schema shape. It does not
// authenticate a historical release binary or authorize single-writer cutover.
const Restored21SessionUpgradePlan = "restored21-session-to22-client-command-queue-v1"

// Same whole sqlite_master fingerprint as backupSchema, also usable inside the
// unpublished candidate's transaction. No object is excluded from the hash.
func upgradeRestored21Schema(db interface { Query(string, ...any) (*sql.Rows, error) }) (string,error) {
 rows,err:=db.Query("SELECT type,name,tbl_name,coalesce(sql,'') FROM sqlite_master ORDER BY type,name")
 if err!=nil{return "",err};defer rows.Close()
 all:=[]any{}
 for rows.Next(){var kind,name,table,sqlText string;if err=rows.Scan(&kind,&name,&table,&sqlText);err!=nil{return "",err};all=append(all,[]any{kind,name,table,sqlText})}
 return Hash(all),rows.Err()
}

// Profiles are generated from exact validated numbered SQL and the unchanged
// H20 restore order. They are schema templates, never historical fixture proof.
func upgradeRestored21Template(ctx context.Context,sqls [][]byte,contracts *Contracts)(string,string,string,error){
 if len(sqls)!=23 || Digest(sqls[20])!=upgradeHistory20SQLHash || Digest(sqls[21])!=upgradeQueueSQLHash || Digest(sqls[22])!=upgradeQueueSessionHash{return "","","",fmt.Errorf("UPGRADE_RESTORED21_TEMPLATE_INPUT")}
 stage,err:=os.MkdirTemp("",".researchos-backup-stage-");if err!=nil{return "","","",err};defer backupDiscard(stage)
 db,err:=store.Open(filepath.Join(stage,"schema.sqlite"));if err!=nil{return "","","",err};defer db.Close()
 for i,raw:=range sqls[:20]{if _,err=db.ExecContext(ctx,string(raw));err!=nil{return "","","",err};if _,err=db.ExecContext(ctx,"INSERT INTO schema_migrations(version) VALUES(?)",i+1);err!=nil{return "","","",err}}
 if _,err=(&Service{DB:db,Contracts:contracts}).backupFence(ctx);err!=nil{return "","","",err}
 if err=upgradeHistory20Migration(ctx,db,sqls[20]);err!=nil{return "","","",err}
 source,err:=backupSchema(db);if err!=nil{return "","","",err}
 // Only the disposable template installs without a precomputed target hash.
 if _,err=db.ExecContext(ctx,string(sqls[22]));err!=nil{return "","","",err}
 if err=installClientSessionFence(ctx,db,false);err!=nil{return "","","",err}
 session,err:=backupSchema(db);if err!=nil{return "","","",err}
 if err=upgradeQueueMigration(ctx,db,sqls[21],sqls[22]);err!=nil{return "","","",err}
 target,err:=backupSchema(db)
 return source,session,target,err
}

// Called only on the isolated restored candidate after its recovery phase.
// Any failed DDL, row or fingerprint check rolls this session transaction back.
func upgradeRestored21Sessions(ctx context.Context,db *sql.DB,additive []byte,sourceSchema,sessionSchema string)(Object,error){
 if Digest(additive)!=upgradeQueueSessionHash{return nil,fmt.Errorf("UPGRADE_SESSION_SCHEMA_HASH")}
 versions,err:=backupMigrations(db);if err!=nil || !reflect.DeepEqual(versions,upgradeVersions(21)){return nil,fmt.Errorf("UPGRADE_SOURCE_VERSION")}
 tx,err:=db.BeginTx(ctx,nil);if err!=nil{return nil,err};defer tx.Rollback()
 schema,err:=upgradeRestored21Schema(tx);if err!=nil || schema!=sourceSchema{return nil,fmt.Errorf("UPGRADE_RESTORED21_SOURCE_SCHEMA")}
 before,err:=upgradeQueueRows(tx);if err!=nil{return nil,err}
 if _,exists:=before["client_sessions"];exists{return nil,fmt.Errorf("UPGRADE_RESTORED21_SESSIONS_PRESENT")}
 if _,err=tx.ExecContext(ctx,string(additive));err!=nil{return nil,err}
 if err=installClientSessionFence(ctx,tx,false);err!=nil{return nil,err}
 after,err:=upgradeQueueRows(tx);if err!=nil{return nil,err}
 for table,rows:=range before{if current,ok:=after[table];!ok || !reflect.DeepEqual(rows,current){return nil,fmt.Errorf("UPGRADE_SESSION_MUTATED_HISTORY: %s",table)}}
 if sessions,ok:=after["client_sessions"];!ok || len(sessions)!=0{return nil,fmt.Errorf("UPGRADE_SESSION_NOT_EMPTY")}
 for table:=range after{if _,ok:=before[table];!ok && table!="client_sessions"{return nil,fmt.Errorf("UPGRADE_SESSION_UNEXPECTED_TABLE: %s",table)}}
 schema,err=upgradeRestored21Schema(tx);if err!=nil || schema!=sessionSchema{return nil,fmt.Errorf("UPGRADE_RESTORED21_SESSION_SCHEMA")}
 var integrity string;if err=tx.QueryRowContext(ctx,"PRAGMA integrity_check").Scan(&integrity);err!=nil || integrity!="ok"{return nil,fmt.Errorf("UPGRADE_TARGET_INTEGRITY")}
 fk,err:=tx.QueryContext(ctx,"PRAGMA foreign_key_check");if err!=nil{return nil,err};bad:=fk.Next();err=fk.Err();fk.Close();if bad || err!=nil{return nil,fmt.Errorf("UPGRADE_TARGET_REFERENCE")}
 if err=tx.Commit();err!=nil{return nil,err}
 return Object{"source_schema_hash":sourceSchema,"session_schema_hash":sessionSchema,"before_rows_hash":Hash(before),"after_rows_hash":Hash(after),"numbered_ledger_unchanged":true,"old_typed_rows_unchanged":true,"client_sessions_created_empty":true,"restore_fence_preserved":true,"restored_barriers_refreshed":false,"external_actions_dispatched":0},nil
}

// Only this new profile adds the empty session table. The existing recovery
// audit continues checking every source table, restored barrier and ledger row.
func upgradeRestored21RecoveryInvariant(before,after upgradeData,destination string)error{
 if _,exists:=before["client_sessions"];exists{return fmt.Errorf("UPGRADE_RESTORED21_SESSIONS_PRESENT")}
 sessions,ok:=after["client_sessions"];if !ok || len(sessions)!=0{return fmt.Errorf("UPGRADE_SESSION_NOT_EMPTY")}
 projected:=upgradeData{};for table,rows:=range after{if table!="client_sessions"{projected[table]=rows}}
 return upgradeQueueRecoveryInvariant(before,projected,destination)
}

func upgradeRestored21Local(ctx context.Context, opt LocalUpgradeOptions, verifier upgradeVerifier) (RestoreReport, error) {
	report := RestoreReport{Started: Now(), Status: "FAILED"}
	if e := upgradePaths(&opt); e != nil {
		return report, e
	}
	sourceRelease, _, e := upgradeQueueRelease(opt.SourceRoot, 21)
	if e != nil {
		return report, e
	}
	targetRelease, sqls, e := upgradeQueueRelease(opt.TargetRoot, 22)
	if e != nil {
		return report, e
	}
	contracts, e := LoadContracts(filepath.Join(opt.TargetRoot, "spec/v2.0/contracts"))
	if e != nil {
		return report, e
	}
	expectedSourceSchema, expectedSessionSchema, expectedTargetSchema, e := upgradeRestored21Template(ctx, sqls, contracts)
	if e != nil {
		return report, e
	}
	key, e := os.ReadFile(opt.KeyFile)
	if e != nil || len(key) != 32 {
		return report, fmt.Errorf("BACKUP_KEY_UNAVAILABLE")
	}
	defer clear(key)
	db, e := upgradeOpenExclusive(ctx, opt.Source)
	if e != nil {
		return report, e
	}
	defer db.Close() // The native source lock spans snapshot through publication.
	versions, e := backupMigrations(db)
	if e != nil || !reflect.DeepEqual(versions, upgradeVersions(21)) {
		return report, fmt.Errorf("UPGRADE_SOURCE_VERSION: require exact 1..21")
	}
	schema, e := backupSchema(db)
	if e != nil || schema != expectedSourceSchema {
		return report, fmt.Errorf("UPGRADE_SOURCE_SCHEMA")
	}
	guard := &upgradeQueueProtection{upgradeProtection: upgradeProtection{ctx: ctx, verifier: verifier}, contracts: contracts}
	if e = guard.refresh(db); e != nil {
		return report, e
	}
	// Reject any host-side protected storage before reading ordinary BLOB rows
	// for the logical inventory or creating a snapshot.
	original, e := upgradeRows(db)
	if e != nil {
		return report, e
	}
	workspaceIdentity, e := upgradeQueueWorkspaceIdentity(db, opt)
	if e != nil {
		return report, e
	}
	programHashes := Object{}
	for name, path := range map[string]string{"source": opt.SourceProgram, "target": opt.TargetProgram} {
		raw, e := os.ReadFile(path)
		if e != nil {
			return report, e
		}
		programHashes[name] = Digest(raw)
	}
	host, e := os.Hostname()
	if e != nil || host == "" {
		return report, fmt.Errorf("UPGRADE_HOST_UNAVAILABLE")
	}
	plan := Object{"id": opt.Plan, "source_versions": versions, "target_versions": upgradeVersions(22),
		"source_schema_hash": schema, "target_schema_with_restore_fence_hash": expectedTargetSchema,
		"source_release_hash": Hash(sourceRelease), "target_release_hash": Hash(targetRelease),
		"migration_sql_hash": Digest(sqls[21]), "source_database_logical_hash": Hash(original),
		"source_release_manifest": sourceRelease, "target_release_manifest": targetRelease, "operational_row_manifest_hash": guard.operationalHash,
		"workspace_identity_manifest_hash": Hash(workspaceIdentity),
		"program_hashes":                   programHashes, "host_binding_hash": Hash(host), "service_summary_hash": guard.summaryHash,
		"source_path_hash": Hash(opt.Source), "target_path_hash": Hash(opt.Destination),
        "session_schema_hash": expectedSessionSchema, "session_sql_hash": Digest(sqls[22]),
        "origin_qualification": "RESTORED21_SCHEMA_PROFILE_ONLY_RELEASE_PROGRAM_PROVENANCE_SEPARATE"}
	purpose := Object{"kind": "SAME_HOST_CONTROL_PLANE_UPGRADE", "scope": "SameHostExternalReferenceContinuityOnly",
		"plan": plan, "plan_hash": Hash(plan), "protected_reference_versions": guard.count,
		"protected_reference_digest": guard.referencesHash, "protected_payloads_included": false,
		"protected_payloads_revalidated": false, "recovery_dependency": "ORIGINAL_PROTECTED_SERVICE",
		"external_actions_dispatched": 0, "source_ownership": "SQLITE_EXCLUSIVE_UNTIL_TARGET_PUBLICATION",
		"cutover_requirement": "Keep original application and workers stopped until independent review and single-writer cutover; do not run both authorities."}
	policy := &backupPolicy{format: localUpgradeFormat, databaseName: "researchos.sqlite", purpose: purpose, validate: guard.refresh, allowProtected: guard.artifact}
	policy.preserveRestored21UpgradeWorkspaces = func(restored *sql.DB) error {
		if e := guard.refresh(restored); e != nil {
			return e
		}
		rows, e := upgradeRows(restored)
		if e != nil || Hash(rows) != Hash(original) {
			return fmt.Errorf("UPGRADE_SNAPSHOT_HISTORY_MISMATCH")
		}
		identity, e := upgradeQueueWorkspaceIdentity(restored, opt)
		if e != nil || Hash(identity) != Hash(workspaceIdentity) {
			return fmt.Errorf("UPGRADE_WORKSPACE_IDENTITY_CHANGED")
		}
		return nil
	}
	policy.beforeRecovery = func(restored *sql.DB) error {
		rows, e := upgradeRows(restored)
		if e != nil || Hash(rows) != Hash(original) {
			return fmt.Errorf("UPGRADE_SNAPSHOT_HISTORY_MISMATCH")
		}
		return nil
	}
	var sessionEvidence Object
	policy.afterRecovery = func(restored *sql.DB) error {
		identity, err := upgradeQueueWorkspaceIdentity(restored, opt)
		if err != nil || Hash(identity) != Hash(workspaceIdentity) {
			return fmt.Errorf("UPGRADE_WORKSPACE_IDENTITY_CHANGED")
		}
		currentSchema, e := backupSchema(restored)
		if e != nil || currentSchema != expectedTargetSchema {
			return fmt.Errorf("UPGRADE_TARGET_SCHEMA")
		}
		rows, e := upgradeRows(restored)
		if e != nil {
			return e
		}
		if e = upgradeRestored21RecoveryInvariant(original, rows, opt.Destination); e != nil {
			return e
		}
		sourceNow, e := upgradeRows(db)
		if e != nil || Hash(sourceNow) != Hash(original) {
			return fmt.Errorf("UPGRADE_SOURCE_DRIFT")
		}
		// Release roots and binary files must not change during the operation.
		for _, entry := range []struct {
			root string
			n    int
			hash string
		}{
			{opt.SourceRoot, 21, Hash(sourceRelease)}, {opt.TargetRoot, 22, Hash(targetRelease)},
		} {
			current, _, err := upgradeQueueRelease(entry.root, entry.n)
			if err != nil || Hash(current) != entry.hash {
				return fmt.Errorf("UPGRADE_RELEASE_CHANGED")
			}
		}
		for name, path := range map[string]string{"source": opt.SourceProgram, "target": opt.TargetProgram} {
			raw, err := os.ReadFile(path)
			if err != nil || Digest(raw) != programHashes[name] {
				return fmt.Errorf("UPGRADE_PROGRAM_CHANGED")
			}
		}
		if e := ctx.Err(); e != nil { return e }
        policy.restored21SessionEvidence = sessionEvidence
        return nil
	}
    svc := &Service{DB: db, Contracts: contracts}
	if _, e = svc.createBackupPolicy(ctx, opt.Snapshot, key, policy); e != nil {
		return report, e
	}
	result, restoreErr := restoreBackupPolicy(ctx, opt.Snapshot, opt.Destination, RestoreOptions{
		Key: key, SupportedMigrations: versions, Contracts: contracts,
		Migration: func(ctx context.Context, target *sql.DB) error {
			var installErr error
            sessionEvidence, installErr = upgradeRestored21Sessions(ctx,target,sqls[22],expectedSourceSchema,expectedSessionSchema)
            if installErr != nil { return installErr }
            return upgradeQueueMigration(ctx, target, sqls[21], sqls[22])
		},
	}, policy)
    return result, restoreErr
}


// Report-only data is separate from the authenticated backup purpose. Old plans
// leave the hook nil and never enter this fixed-profile publication branch.
func upgradeRestored21PublishEvidence(policy *backupPolicy, recovery Object) error {
 if policy == nil || policy.restored21SessionEvidence == nil { return nil }
 plan, ok := policy.purpose["plan"].(Object)
 if !ok || policy.format != localUpgradeFormat || plan["id"] != Restored21SessionUpgradePlan {
  return fmt.Errorf("RESTORE_RESTORED21_REPORT_POLICY_MISMATCH")
 }
 evidence := policy.restored21SessionEvidence
 if recovery == nil || !upgradeQueueFields(evidence,"source_schema_hash session_schema_hash before_rows_hash after_rows_hash numbered_ledger_unchanged old_typed_rows_unchanged client_sessions_created_empty restore_fence_preserved restored_barriers_refreshed external_actions_dispatched") {
  return fmt.Errorf("RESTORE_RESTORED21_REPORT_EVIDENCE_INVALID")
 }
 for _, name := range []string{"source_schema_hash","session_schema_hash","before_rows_hash","after_rows_hash"} {
  value, ok := evidence[name].(string)
  if !ok || len(value) != 71 || value[:7] != "sha256:" { return fmt.Errorf("RESTORE_RESTORED21_REPORT_EVIDENCE_INVALID") }
  for _, c := range value[7:] { if !((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f')) { return fmt.Errorf("RESTORE_RESTORED21_REPORT_EVIDENCE_INVALID") } }
 }
 for _, name := range []string{"numbered_ledger_unchanged","old_typed_rows_unchanged","client_sessions_created_empty","restore_fence_preserved"} {
  value, ok := evidence[name].(bool); if !ok || !value { return fmt.Errorf("RESTORE_RESTORED21_REPORT_EVIDENCE_INVALID") }
 }
 refreshed, ok := evidence["restored_barriers_refreshed"].(bool)
 actions, typed := evidence["external_actions_dispatched"].(int)
 if !ok || refreshed || !typed || actions != 0 { return fmt.Errorf("RESTORE_RESTORED21_REPORT_EVIDENCE_INVALID") }
 recovery["restored21_session_initialization"] = evidence
 return nil
}
