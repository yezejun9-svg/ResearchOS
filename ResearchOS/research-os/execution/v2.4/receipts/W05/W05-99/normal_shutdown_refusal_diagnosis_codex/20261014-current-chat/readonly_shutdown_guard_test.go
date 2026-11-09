//go:build windows
package domain
import("context";"database/sql";"net/url";"os";"path/filepath";"testing";_ "modernc.org/sqlite")
func TestReadOnlyOriginalShutdownGuard(t *testing.T){
 path:=os.Getenv("REVIEW_ORIGINAL_DATABASE");if path==""{t.Fatal("explicit original read-only database required")}
 u:=url.URL{Scheme:"file",Path:"/"+filepath.ToSlash(path),RawQuery:"mode=ro"}
 db,e:=sql.Open("sqlite",u.String());if e!=nil{t.Fatal(e)};defer db.Close();db.SetMaxOpenConns(1);db.SetMaxIdleConns(1)
 if _,e=db.Exec("PRAGMA query_only=ON");e!=nil{t.Fatal(e)}
 var ro int;if e=db.QueryRow("PRAGMA query_only").Scan(&ro);e!=nil||ro!=1{t.Fatal("read-only guard",e,ro)}
 s:=&Service{DB:db};snapshot,e:=s.RuntimeDrainSnapshot(context.Background());if e!=nil{t.Fatal(e)}
 t.Logf("READ_ONLY_DRAIN_COUNTERS active_runs=%d unresolved_effects=%d unresolved_dispatches=%d reservations=%d unresolved_commands=%d",snapshot.ActiveRuns,snapshot.UnresolvedEffects,snapshot.UnresolvedDispatches,snapshot.Reservations,snapshot.UnresolvedCommands)
 e=s.completedLocalUnknownCosts(context.Background())
 if e!=nil {t.Logf("READ_ONLY_ORIGINAL_PRODUCTION_ACCOUNTING_GUARD_REJECTS: %s",e.Error())}else{t.Log("READ_ONLY_ORIGINAL_PRODUCTION_ACCOUNTING_GUARD_PASSES")}
}
