$ErrorActionPreference='Stop'
$T='D:\作品集\ResearchOS\research-os\.local\qualification-failure-b-independent-review-20261015'
$W='D:\作品集\ResearchOS\research-os\.local\worktrees\qualification-failure-b-20261015'
$d=Get-Content -Raw "$T\overlay\runtime_qualification_failure_windows_test.go"
$d+=@'

func TestIndependentQualificationPrivateConsumerModelReceiptTamper(t *testing.T) {
 c, route, r, calls := qualificationFailureLoopbackFixture(t)
 if err:=c.RunAdmitted(context.Background(),route,r.run,r.lease);err==nil {t.Fatal("expected first-gate denial")}
 if calls.Load()!=1 {t.Fatal("baseline loopback count")}
 epoch,err:=Num(r.run,"lease_epoch");if err!=nil {t.Fatal(err)}
 tx,err:=r.f.db.Begin();if err!=nil {t.Fatal(err)};defer tx.Rollback()
 if _,err=r.f.s.validatedQualificationFailureTx(tx,r.f.project,Str(r.task,"id"),Str(r.run,"id"),epoch);err!=nil {t.Fatal("positive baseline",err)}
 // Corrupt an own fixture's append-only source inside a rolled-back transaction,
 // matching the author's private-consumer tamper methodology.
 rows,err:=tx.Query("SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='resource_effects'");if err!=nil {t.Fatal(err)}
 var names []string
 for rows.Next(){var n string;if err=rows.Scan(&n);err!=nil {t.Fatal(err)};names=append(names,n)}
 if err=rows.Err();err!=nil {t.Fatal(err)};rows.Close()
 for _,n:=range names {if _,err=tx.Exec("DROP TRIGGER \""+strings.ReplaceAll(n,"\"","\"\"")+"\"");err!=nil {t.Fatal(err)}}
 result,err:=tx.Exec("UPDATE resource_effects SET body=json_set(body,'$.receipt.receipt_id','sha256:forged-independent') WHERE project=? AND run=? AND json_extract(body,'$.state')='CONFIRMED'",r.f.project,r.run["id"])
 if err!=nil {t.Fatal(err)}
 changed,err:=result.RowsAffected();if err!=nil||changed!=1 {t.Fatalf("wrong tamper census %d %v",changed,err)}
 _,err=r.f.s.validatedQualificationFailureTx(tx,r.f.project,Str(r.task,"id"),Str(r.run,"id"),epoch)
 if err==nil {t.Fatal("private consumer accepted a changed confirmed MODEL receipt_id without changing sealed proof, marker, or observation")}
}
'@
[IO.File]::WriteAllText("$T\overlay\runtime_qualification_failure_windows_test_v2.go",$d)
$replace=@{}
$replace["$W\internal\domain\runtime_qualification_failure_windows_test.go"]="$T\overlay\runtime_qualification_failure_windows_test_v2.go"
@{Replace=$replace}|ConvertTo-Json|Set-Content -Encoding utf8 "$T\overlay-v2.json"
Get-FileHash "$T\overlay\runtime_qualification_failure_windows_test_v2.go"
Get-Content -Tail 12 'D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\qualification_failure_b_independent_review_codex\20261015-current-chat\r09-focused-tests.raw.txt'
