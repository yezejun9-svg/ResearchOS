import pathlib,json,hashlib
B=pathlib.Path(__file__).parent
S=pathlib.Path(json.loads((B/'PHASE2-exact-snapshot-verification.json').read_text(encoding='utf-8'))['snapshot'])
p=S/'internal/domain/qualification_failure_maintenance_windows_test.go'
raw=p.read_text(encoding='utf-8')
start=raw.index('func TestHistoricalQualificationPlannedWriterFiveVersions(')
end=raw.index('\nfunc TestHistoricalQualificationRecoveryClassificationNineTables(',start)
body=raw[start:end].replace('TestHistoricalQualificationPlannedWriterFiveVersions','TestIndependentC57Writer87TableBytes')
body=body.replace('\t// A collision after upload insertion', '\tindBefore := independentC57Census(t, writerDB, "before")\n\t// A collision after upload insertion')
body=body.replace('\twriteTx, e := writerDB.BeginTx(ctx, nil)', '\tindRollback := independentC57Census(t, writerDB, "rollback")\n\tindependentC57Compare(t, indBefore, indRollback, false)\n\twriteTx, e := writerDB.BeginTx(ctx, nil)')
body=body.replace('\tclassification, e := ClassifyHistoricalQualification(ctx, writerDB, plan, planFileSHA256)', '\tindAfter := independentC57Census(t, writerDB, "committed")\n\tindependentC57Compare(t, indBefore, indAfter, true)\n\tclassification, e := ClassifyHistoricalQualification(ctx, writerDB, plan, planFileSHA256)')
body=body.rstrip()[:-1]+'\tindReplay := independentC57Census(t, writerDB, "replay_rejected")\n\tindependentC57Compare(t, indAfter, indReplay, false)\n}\n'
header='''//go:build windows

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

// Independently read every application table using SQLite storage class and
// exact SQL literal bytes; this does not call the production census helpers.
func independentC57Census(t *testing.T, db *sql.DB, phase string) map[string][]string {
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
  for info.Next(){var cid,nn,pk int;var col,typ string;var def any;if e=info.Scan(&cid,&col,&typ,&nn,&def,&pk);e!=nil{t.Fatal(e)};q:=`"`+strings.ReplaceAll(col,`"`,`""`)+`"`;expr=append(expr,"typeof("+q+")","quote("+q+")")}
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

func independentC57Compare(t *testing.T,before,after map[string][]string,commit bool){
 t.Helper()
 allow:=map[string]int{"domain_objects":3,"domain_versions":5,"domain_refs":-1,"uploaded_content":1,"runtime_observations":1,"runtime_dispatches":0,"outbox":1,"event_state_snapshots":1,"idempotency":1}
 changed:=0
 for name,b:=range before{
  a,ok:=after[name];if !ok{t.Fatalf("missing table %s",name)}
  same:=fmt.Sprint(b)==fmt.Sprint(a)
  delta,allowed:=allow[name]
  if !commit||!allowed{if !same{t.Errorf("unlicensed byte delta %s",name)};continue}
  if same{t.Errorf("planned table unchanged %s",name)}else{changed++}
  if delta>=0&&len(a)-len(b)!=delta{t.Errorf("table %s row delta %d want %d",name,len(a)-len(b),delta)}
  t.Logf("INDEPENDENT_DELTA table=%s before=%d after=%d changed=%t",name,len(b),len(a),!same)
 }
 if commit&&changed!=9{t.Errorf("changed tables %d want 9",changed)}
}

'''
dest=S/'internal/domain/independent_c57_census_windows_test.go'
assert not dest.exists()
dest.write_text(header+body,encoding='utf-8')
sha=hashlib.sha256(dest.read_bytes()).hexdigest()
job=json.loads((B/'PHASE2-jobs/096-phase2-domain-c-owned-cache.json').read_text(encoding='utf-8'))
job['tag']='103-independent-domain-census'
job['argv'][-1]='^TestIndependentC57Writer87TableBytes$'
job['supplementary_files']=[{'path':str(dest.relative_to(S)).replace('\\','/'),'sha256':sha}]
(B/'PHASE2-jobs/103-independent-domain-census.json').write_text(json.dumps(job,indent=2),encoding='utf-8')
(B/'PHASE2-independent-supplement-01.json').write_text(json.dumps({'source_test_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'supplement':job['supplementary_files'],'construction':'Copied fixture preparation and planned writer invocation from candidate; independent storage-class/SQL-literal per-table census and delta assertions added. No candidate source/test modified.'},indent=2),encoding='utf-8')
print(sha)
