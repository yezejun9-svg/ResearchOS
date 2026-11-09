import pathlib,json,hashlib
B=pathlib.Path(__file__).parent
S=pathlib.Path(json.loads((B/'PHASE2-exact-snapshot-verification.json').read_text(encoding='utf-8'))['snapshot'])
raw=(S/'internal/domain/qualification_failure_maintenance_windows_test.go').read_text(encoding='utf-8')
a=raw.index('func TestHistoricalQualificationPlannedWriterFiveVersions(');z=raw.index('\nfunc TestHistoricalQualificationRecoveryClassificationNineTables(',a)
body=raw[a:z].replace('TestHistoricalQualificationPlannedWriterFiveVersions','TestIndependentC57SQLCutsAndWriterReservation')
injected='''
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
'''
body=body.replace('\t// A collision after upload insertion',injected+'\n\t// A collision after upload insertion')
body=body.replace('\tclassification, e := ClassifyHistoricalQualification(ctx, writerDB, plan, planFileSHA256)', '\tindAfter:=independentC57ExactCensus(t,writerDB,"committed")\n\tindependentC57Compare(t,indBefore,indAfter,true)\n\tclassification, e := ClassifyHistoricalQualification(ctx, writerDB, plan, planFileSHA256)')
body=body.rstrip()[:-1]+'\tindependentC57Compare(t,indAfter,independentC57ExactCensus(t,writerDB,"replay"),false)\n}\n'
old=(S/'internal/domain/independent_c57_census_windows_test.go').read_text(encoding='utf-8')
header=old[:old.index('// Independently read every application table')]
helper=old[old.index('func independentC57Census('):old.index('\nfunc independentC57Compare(')]
helper=helper.replace('independentC57Census','independentC57ExactCensus').replace('"quote("+q+")"','"CASE WHEN typeof("+q+")=\'real\' THEN printf(\'%!.26g\',"+q+") ELSE hex(CAST("+q+" AS BLOB)) END"')
dest=S/'internal/domain/independent_c57_sqlcuts_windows_test.go';assert not dest.exists();dest.write_text(header+helper+body,encoding='utf-8')
job=json.loads((B/'PHASE2-jobs/114-independent-native-hold.json').read_text(encoding='utf-8'))
job['tag']='116-independent-sql-cuts';job['argv'][-1]='^TestIndependentC57SQLCutsAndWriterReservation$'
job['supplementary_files'].append({'path':str(dest.relative_to(S)).replace('\\','/'),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
(B/'PHASE2-jobs/116-independent-sql-cuts.json').write_text(json.dumps(job,indent=2),encoding='utf-8')
print(json.dumps(job['supplementary_files'],indent=2))
