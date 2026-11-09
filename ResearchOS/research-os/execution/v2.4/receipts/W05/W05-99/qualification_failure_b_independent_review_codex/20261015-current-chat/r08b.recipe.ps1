$ErrorActionPreference='Stop'
$W='D:\作品集\ResearchOS\research-os\.local\worktrees\qualification-failure-b-20261015'
$T='D:\作品集\ResearchOS\research-os\.local\qualification-failure-b-independent-review-20261015'
New-Item -ItemType Directory -Force -Path "$T\gotmp","$T\gocache","$T\overlay" | Out-Null
$adapter=Get-Content -Raw "$W\adapters\runtime\qualification_failure_proof_windows_test.go"
$adapter += @'

func TestIndependentQualificationProtectedWorldWritableDirectoryRejected(t *testing.T) {
 private := t.TempDir()
 if _, err := PrivateDirectory(private); err != nil { t.Fatal(err) }
 output, err := exec.Command("icacls", private, "/grant", "*S-1-1-0:(OI)(CI)F").CombinedOutput()
 t.Logf("icacls output=%s err=%v", output, err)
 if err != nil { t.Fatal(err) }
 output, err = exec.Command("icacls", private).CombinedOutput()
 t.Logf("actual fixture DACL=%s err=%v", output, err)
 if err != nil { t.Fatal(err) }
 err = PersistQualificationRejection(private, []byte("{\"outcome\":\"NO_EFFECT\"}"))
 if err == nil { t.Fatal("protected DACL containing current SID AND Everyone full access was accepted and receipt persisted") }
}
'@
[IO.File]::WriteAllText("$T\overlay\qualification_failure_proof_windows_test.go",$adapter)
$domain=Get-Content -Raw "$W\internal\domain\runtime_qualification_failure_windows_test.go"
$domain += @'

func TestIndependentQualificationCurrentOwnerRootRevocation(t *testing.T) {
 c, route, r, calls := qualificationFailureLoopbackFixture(t)
 if err := c.RunAdmitted(context.Background(), route, r.run, r.lease); err == nil { t.Fatal("expected typed rejection") }
 if calls.Load()!=1 { t.Fatalf("loopback calls=%d", calls.Load()) }
 epoch, err := Num(r.run,"lease_epoch"); if err!=nil {t.Fatal(err)}
 tx, err:=r.f.db.Begin();if err!=nil {t.Fatal(err)}
 closure, err:=r.f.s.validatedQualificationFailureTx(tx,r.f.project,Str(r.task,"id"),Str(r.run,"id"),epoch)
 if err!=nil {tx.Rollback();t.Fatal(err)}
 if closure.seal=="" {tx.Rollback();t.Fatal("empty baseline seal")}
 var author, root string
 err=tx.QueryRow("SELECT principal,json_extract(body,'$.owner_root') FROM idempotency WHERE project=? AND operation='host:qualification-failure-closure'",r.f.project).Scan(&author,&root)
 tx.Rollback();if err!=nil {t.Fatal(err)}
 t.Logf("actual closure author=%s current owner root=%s fixture owner=%s",author,root,r.f.owner)
 if author==root {t.Fatal("test requires distinct scheduler and Owner root")}
 if err=r.f.s.RevokePrincipal(context.Background(),root);err!=nil {t.Fatal(err)}
 tx,err=r.f.db.Begin();if err!=nil {t.Fatal(err)};defer tx.Rollback()
 var revoked int
 if err=tx.QueryRow("SELECT revoked FROM auth_principals WHERE id=?",author).Scan(&revoked);err!=nil||revoked!=0 {t.Fatalf("author unexpectedly revoked: %d %v",revoked,err)}
 _,err=r.f.s.validatedQualificationFailureTx(tx,r.f.project,Str(r.task,"id"),Str(r.run,"id"),epoch)
 if err==nil {t.Fatal("private consumer accepted after actual current Owner root was revoked")}
 t.Logf("current Owner root revocation correctly rejected: %v",err)
}
'@
[IO.File]::WriteAllText("$T\overlay\runtime_qualification_failure_windows_test.go",$domain)
$replace=@{}
$replace["$W\adapters\runtime\qualification_failure_proof_windows_test.go"]="$T\overlay\qualification_failure_proof_windows_test.go"
$replace["$W\internal\domain\runtime_qualification_failure_windows_test.go"]="$T\overlay\runtime_qualification_failure_windows_test.go"
@{Replace=$replace}|ConvertTo-Json -Depth 5|Set-Content -Encoding utf8 "$T\overlay.json"
Get-FileHash "$T\overlay\*","$T\overlay.json"
