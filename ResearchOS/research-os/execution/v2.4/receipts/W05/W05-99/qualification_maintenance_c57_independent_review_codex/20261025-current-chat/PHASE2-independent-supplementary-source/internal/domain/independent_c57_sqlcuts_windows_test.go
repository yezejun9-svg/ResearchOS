//go:build windows

package domain

import (
 "context"
 "crypto/sha256"
 "database/sql"
 "encoding/hex"
 "encoding/json"
 "fmt"
 "path/filepath"
 "sort"
 "strings"
 "testing"
 rt "researchos.local/research-os/adapters/runtime"
 "researchos.local/research-os/internal/store"
)

func independentC57ExactCensus(t *testing.T, db *sql.DB, phase string) map[string][]string {
 t.Helper()
 rows,e:=db.Query(`SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name`)
 if e!=nil {t.Fatal(e)}
 names:=[]string{}
 for rows.Next(){var name string;if e=rows.Scan(&name);e!=nil{t.Fatal(e)};names=append(names,name)}
 if e=rows.Err();e!=nil{t.Fatal(e)};rows.Close()
 if len(names)!=87{t.Fatalf("independent application table count %d",len(names))}
 result:=map[string][]string{}
 for _,name:=range names{
  quoted:=`"`+strings.ReplaceAll(name,`"`,`""`)+`"`
  info,e:=db.Query("PRAGMA table_info("+quoted+")");if e!=nil{t.Fatal(e)}
  expr:=[]string{}
  for info.Next(){var cid,nn,pk int;var col,typ string;var def any;if e=info.Scan(&cid,&col,&typ,&nn,&def,&pk);e!=nil{t.Fatal(e)};q:=`"`+strings.ReplaceAll(col,`"`,`""`)+`"`;expr=append(expr,"typeof("+q+")","CASE WHEN typeof("+q+")='real' THEN printf('%!.26g',"+q+") ELSE hex(CAST("+q+" AS BLOB)) END")}
  if e=info.Err();e!=nil{t.Fatal(e)};info.Close()
  rr,e:=db.Query("SELECT "+strings.Join(expr,",")+" FROM "+quoted);if e!=nil{t.Fatal(e)}
  vals:=make([]any,len(expr));ptrs:=make([]any,len(expr));for i:=range vals{ptrs[i]=&vals[i]}
  encoded:=[]string{}
  for rr.Next(){if e=rr.Scan(ptrs...);e!=nil{t.Fatal(e)};b,e:=json.Marshal(vals);if e!=nil{t.Fatal(e)};encoded=append(encoded,string(b))}
  if e=rr.Err();e!=nil{t.Fatal(e)};rr.Close();sort.Strings(encoded);result[name]=encoded
  b,e:=json.Marshal(encoded);if e!=nil{t.Fatal(e)};h:=sha256.Sum256(b)
  t.Logf("INDEPENDENT_CENSUS phase=%s table=%s rows=%d sha256=%s",phase,name,len(encoded),hex.EncodeToString(h[:]))
 }
 return result
}
func TestIndependentC57SQLCutsAndWriterReservation(t *testing.T) {
	_, route, r, _ := qualificationFailureLoopbackFixture(t)
	ctx := context.Background()
	runID := Str(r.run, "id")
	taskID := Str(r.task, "id")
	epoch, e := Num(r.run, "lease_epoch")
	if e != nil {
		t.Fatal(e)
	}
	var seq int
	var name, database string
	if e = r.f.db.QueryRow("PRAGMA database_list").Scan(&seq, &name, &database); e != nil {
		t.Fatal(e)
	}
	root := filepath.Dir(database)
	var dispatchKey string
	if e = r.f.db.QueryRow(`SELECT dispatch_key FROM runtime_dispatches WHERE project=? AND run=? AND epoch=?`,
		r.f.project, runID, epoch).Scan(&dispatchKey); e != nil {
		t.Fatal(e)
	}
	if _, e = r.f.db.Exec(`UPDATE runtime_dispatches SET state='STARTED',worker='fixture',journal_locator=dispatch_key,
		updated_at='2026-10-25T00:00:00Z',reason='synthetic writer fixture' WHERE project=? AND run=? AND epoch=?`,
		r.f.project, runID, epoch); e != nil {
		t.Fatal(e)
	}
	database = filepath.Join(root, "researchos.sqlite")
	if _, e = r.f.db.Exec(`VACUUM INTO ?`, database); e != nil {
		t.Fatal(e)
	}
	clone, e := sql.Open("sqlite", database)
	if e != nil {
		t.Fatal(e)
	}
	if _, e = clone.Exec("PRAGMA journal_mode=WAL"); e != nil {
		t.Fatal(e)
	}
	if e = clone.Close(); e != nil {
		t.Fatal(e)
	}
	writerDB, e := store.OpenQualificationMaintenance(ctx, database)
	if e != nil {
		t.Fatal(e)
	}
	defer writerDB.Close()
	writerService := &Service{DB: writerDB, Contracts: r.f.s.Contracts}
	var versionsBefore, taskRevisionsBefore, ledgerBefore int
	if e = writerDB.QueryRow(`SELECT count(*) FROM domain_versions WHERE project=?`, r.f.project).Scan(&versionsBefore); e != nil {
		t.Fatal(e)
	}
	if e = writerDB.QueryRow(`SELECT count(*) FROM domain_versions WHERE project=? AND kind='Task' AND id=?`, r.f.project, taskID).Scan(&taskRevisionsBefore); e != nil {
		t.Fatal(e)
	}
	if e = writerDB.QueryRow(`SELECT count(*) FROM domain_objects WHERE project=? AND kind='BudgetLedgerEntry'`, r.f.project).Scan(&ledgerBefore); e != nil {
		t.Fatal(e)
	}
	beforeTx, e := writerDB.BeginTx(ctx, &sql.TxOptions{ReadOnly: true})
	if e != nil {
		t.Fatal(e)
	}
	run, e := load(beforeTx, r.f.project, "Run", runID)
	if e != nil {
		t.Fatal(e)
	}
	state, e := singleton(beforeTx, r.f.project, "ProjectState")
	if e != nil {
		t.Fatal(e)
	}
	task, e := load(beforeTx, r.f.project, "Task", taskID)
	if e != nil {
		t.Fatal(e)
	}
	dispatch, e := runtimeDispatch(beforeTx, r.f.project, runID, epoch)
	if e != nil {
		t.Fatal(e)
	}
	before, e := store.QualificationMaintenanceCensus(ctx, beforeTx)
	if e != nil {
		t.Fatal(e)
	}
	if e = beforeTx.Rollback(); e != nil {
		t.Fatal(e)
	}
	inputs := Arr(task, "input_refs")
	if len(inputs) != 1 {
		t.Fatalf("fixture profile refs %d", len(inputs))
	}
	profileRef, ok := inputs[0].(map[string]any)
	if !ok {
		t.Fatal("fixture profile ref unavailable")
	}
	subject := HistoricalQualificationSubject{ProjectID: r.f.project, TaskID: taskID, RunID: runID,
		RuntimeID: route.RuntimeID, Epoch: epoch, DispatchKey: dispatchKey}
	native := historicalQualificationNative{journal: rt.BridgeJournal{Sequence: 0, Ended: "2026-10-25T00:00:00Z"}}
	verified := verifiedHistoricalQualification{subject: subject, author: Principal{ID: r.f.owner},
		ownerRoot: r.f.owner, profileRef: Object(profileRef), run: run, task: task, state: state, dispatch: dispatch,
		observation: Object{"qualification_failure": Object{"kind": historicalMaintenanceProofKind},
			"state": "UNKNOWN", "queue_empty": false},
		modelBinding: Object{"fact_hash": Digest([]byte("synthetic-model"))}, native: native,
		source: HistoricalQualificationSource{BridgeSHA256: Digest([]byte("synthetic-bridge"))}}
	op := ID()
	boundaryHash := "1111111111111111111111111111111111111111111111111111111111111111"
	planTx, e := writerDB.BeginTx(ctx, &sql.TxOptions{ReadOnly: true})
	if e != nil {
		t.Fatal(e)
	}
	plan, e := writerService.buildHistoricalQualificationPlan(ctx, planTx, verified, op, boundaryHash, root, database, filepath.Join(root, "runtime-dispatches", dispatchKey),
		"fixture-sid", before, nil)
	rollbackErr := planTx.Rollback()
	if e != nil || rollbackErr != nil {
		t.Fatalf("plan: %v rollback: %v", e, rollbackErr)
	}
	planFileSHA256 := Digest(Bytes(plan))

 // Exact typed byte encoding also preserves embedded NUL, unlike quote(TEXT).
 indBefore:=independentC57ExactCensus(t,writerDB,"before_faults")
 tables:=[]string{"uploaded_content","domain_versions","domain_objects","domain_refs","runtime_observations","runtime_dispatches","outbox","event_state_snapshots","idempotency"}
 for i,table:=range tables{
  fault,e:=writerDB.BeginTx(ctx,nil);if e!=nil{t.Fatal(e)}
  if e=resourceWriteLock(fault);e!=nil{t.Fatal(e)}
  action:="INSERT";if table=="runtime_dispatches"{action="UPDATE"}
  trigger:=fmt.Sprintf(`CREATE TEMP TRIGGER independent_cut_%d BEFORE %s ON "%s" BEGIN SELECT RAISE(ABORT,'independent-cut'); END`,i,action,table)
  if _,e=fault.Exec(trigger);e!=nil{fault.Rollback();t.Fatal(e)}
  applyErr:=writerService.applyHistoricalQualificationTx(ctx,fault,plan,planFileSHA256)
  if applyErr==nil{fault.Rollback();t.Fatalf("cut %s not reached",table)}
  if !strings.Contains(applyErr.Error(),"independent-cut"){fault.Rollback();t.Fatalf("cut %s failed for unexpected reason: %v",table,applyErr)}
  if e=fault.Rollback();e!=nil{t.Fatal(e)}
  after:=independentC57ExactCensus(t,writerDB,"rollback_"+table)
  independentC57Compare(t,indBefore,after,false)
  t.Logf("SQL_CUT table=%s actual_writer_reached=true sqlite_abort=true rollback_returned=true all87_equal=true",table)
 }
 // A real second SQLite writer must fail while the actual reservation is held.
 second,e:=sql.Open("sqlite",database);if e!=nil{t.Fatal(e)};defer second.Close()
 if _,e=second.Exec(`PRAGMA busy_timeout=20`);e!=nil{t.Fatal(e)}
 reservation,e:=writerDB.BeginTx(ctx,nil);if e!=nil{t.Fatal(e)}
 if e=resourceWriteLock(reservation);e!=nil{t.Fatal(e)}
 _,secondErr:=second.Exec(`UPDATE auth_principals SET roles=roles WHERE id=?`,r.f.owner)
 if secondErr==nil{reservation.Rollback();t.Fatal("second writer entered held reservation")}
 if !strings.Contains(strings.ToLower(secondErr.Error()),"locked")&&!strings.Contains(strings.ToLower(secondErr.Error()),"busy"){reservation.Rollback();t.Fatalf("unexpected second writer error: %v",secondErr)}
 if e=reservation.Rollback();e!=nil{t.Fatal(e)}
 if _,e=second.Exec(`UPDATE auth_principals SET roles=roles WHERE id=?`,r.f.owner);e!=nil{t.Fatalf("writer after reservation release: %v",e)}
 t.Logf("SQL_RESERVATION second_writer_blocked=%q succeeds_after_rollback=true",secondErr.Error())
 independentC57Compare(t,indBefore,independentC57ExactCensus(t,writerDB,"after_reservation"),false)

	// A collision after upload insertion must roll the entire planned write
	// set back. This is a SQL cutpoint fixture, not a boot grant.
	faultTx, e := writerDB.BeginTx(ctx, nil)
	if e != nil {
		t.Fatal(e)
	}
	if e = resourceWriteLock(faultTx); e != nil {
		t.Fatal(e)
	}
	if _, e = faultTx.Exec(`INSERT INTO domain_versions(project,kind,id,revision,body,content_hash) VALUES(?,'Artifact',?,1,?,?)`,
		plan.Subject.ProjectID, plan.Artifact["id"], string(Bytes(plan.Artifact)), plan.Artifact["content_hash"]); e != nil {
		t.Fatal(e)
	}
	if e = writerService.applyHistoricalQualificationTx(ctx, faultTx, plan, planFileSHA256); e == nil {
		t.Fatal("version collision did not stop writer")
	}
	if e = faultTx.Rollback(); e != nil {
		t.Fatal(e)
	}
	if classified, classErr := ClassifyHistoricalQualification(ctx, writerDB, plan, planFileSHA256); classErr != nil || classified != "NOT_APPLIED" {
		t.Fatalf("fault rollback classified %s: %v", classified, classErr)
	}
	writeTx, e := writerDB.BeginTx(ctx, nil)
	if e != nil {
		t.Fatal(e)
	}
	if e = resourceWriteLock(writeTx); e != nil {
		t.Fatal(e)
	}
	if e = writerService.applyHistoricalQualificationTx(ctx, writeTx, plan, planFileSHA256); e != nil {
		_ = writeTx.Rollback()
		t.Fatal(e)
	}
	if e = writeTx.Commit(); e != nil {
		t.Fatal(e)
	}
	indAfter:=independentC57ExactCensus(t,writerDB,"committed")
	independentC57Compare(t,indBefore,indAfter,true)
	classification, e := ClassifyHistoricalQualification(ctx, writerDB, plan, planFileSHA256)
	if e != nil || classification != "APPLIED" {
		probe, probeErr := writerDB.BeginTx(ctx, &sql.TxOptions{ReadOnly: true})
		if probeErr == nil {
			full, _ := store.QualificationMaintenanceCensus(ctx, probe)
			p, _ := store.QualificationMaintenanceProtectedCensus(ctx, probe)
			sel, _ := plan.residualSelectors()
			r, _ := store.QualificationMaintenanceResidualCensus(ctx, probe, sel)
			exact, exactErr := historicalQualificationExactRows(ctx, probe, plan, planFileSHA256)
			t.Logf("writer debug full=%t schema=%t protected=%t residual=%t exact=%t exactErr=%v",
				Hash(full) == Hash(plan.BeforeCensus), full.SchemaSHA256 == plan.BeforeCensus.SchemaSHA256,
				p == plan.BeforeProtectedSHA256, r == plan.BeforeResidualSHA256, exact, exactErr)
			for _, entry := range []struct {
				kind string
				obj  Object
			}{{"Artifact", plan.Artifact}, {"ImpactLink", plan.ImpactLink},
				{"Run", plan.Run}, {"ProjectState", plan.ProjectState}, {"EventEnvelope", plan.Event}} {
				rev, _ := Num(entry.obj, "revision")
				actualRefs, _ := historicalQualificationRefs(probe, plan.Subject.ProjectID, entry.kind, Str(entry.obj, "id"), rev)
				t.Logf("writer refs %s %s rev%d: %s", entry.kind, Str(entry.obj, "id"), rev, Bytes(actualRefs))
				if entry.kind == "Run" || entry.kind == "ProjectState" {
					oldRefs, _ := historicalQualificationRefs(probe, plan.Subject.ProjectID, entry.kind, Str(entry.obj, "id"), rev-1)
					t.Logf("writer old refs %s rev%d: %s", entry.kind, rev-1, Bytes(oldRefs))
				}
			}
			_ = probe.Rollback()
		}
		t.Fatalf("writer classified %s: %v", classification, e)
	}
	var versions, markers, taskRevisions, ledger int
	if e = writerDB.QueryRow(`SELECT count(*) FROM domain_versions WHERE project=?`, r.f.project).Scan(&versions); e != nil {
		t.Fatal(e)
	}
	if e = writerDB.QueryRow(`SELECT count(*) FROM idempotency WHERE project=? AND operation='host:qualification-failure-maintenance'`, r.f.project).Scan(&markers); e != nil {
		t.Fatal(e)
	}
	if e = writerDB.QueryRow(`SELECT count(*) FROM domain_versions WHERE project=? AND kind='Task' AND id=?`, r.f.project, taskID).Scan(&taskRevisions); e != nil {
		t.Fatal(e)
	}
	if e = writerDB.QueryRow(`SELECT count(*) FROM domain_objects WHERE project=? AND kind='BudgetLedgerEntry'`, r.f.project).Scan(&ledger); e != nil {
		t.Fatal(e)
	}
	if versions != versionsBefore+5 || markers != 1 || taskRevisions != taskRevisionsBefore || ledger != ledgerBefore {
		t.Fatalf("planned five-version/marker/fence delta wrong: versions=%d/%d markers=%d task=%d/%d ledger=%d/%d",
			versionsBefore, versions, markers, taskRevisionsBefore, taskRevisions, ledgerBefore, ledger)
	}
	replayTx, e := writerDB.BeginTx(ctx, nil)
	if e != nil {
		t.Fatal(e)
	}
	if e = resourceWriteLock(replayTx); e != nil {
		t.Fatal(e)
	}
	if e = writerService.applyHistoricalQualificationTx(ctx, replayTx, plan, planFileSHA256); e == nil {
		t.Fatal("same plan replay wrote again")
	}
	if e = replayTx.Rollback(); e != nil {
		t.Fatal(e)
	}
	if classified, classErr := ClassifyHistoricalQualification(ctx, writerDB, plan, planFileSHA256); classErr != nil || classified != "APPLIED" {
		t.Fatalf("replay changed durable image: %s %v", classified, classErr)
	}
	independentC57Compare(t,indAfter,independentC57ExactCensus(t,writerDB,"replay"),false)
}
