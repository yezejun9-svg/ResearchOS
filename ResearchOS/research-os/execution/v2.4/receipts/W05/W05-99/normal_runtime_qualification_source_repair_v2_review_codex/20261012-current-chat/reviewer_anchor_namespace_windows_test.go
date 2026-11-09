//go:build windows
package domain
import ("context"; "testing")
func TestReviewerManagedAnchorDoesNotPolluteClientIdempotency(t *testing.T) {
 db,_:=configurationDB(t,23,true); doc:=configurationSchema(t)
 raw,env:=configurationEnvelope(t,doc,configurationFixturePrincipal,1)
 tx,e:=db.Begin();if e!=nil{t.Fatal(e)};defer tx.Rollback()
 anchor:=Object{"schema":"researchos.managed-verifier-lineage.v1","principal":configurationFixturePrincipal,"project_id":"other-project","root":"reviewer-root","registered_by":"reviewer-owner"}
 _,e=tx.Exec(`INSERT INTO idempotency(principal,project,operation,key,request_hash,status,body,headers,created_at) VALUES(?,?,'host:managed-verifier-lineage',?,?,200,?,'{}',?)`,configurationFixturePrincipal,"other-project",configurationFixturePrincipal,Hash(anchor),Bytes(anchor),Now());if e!=nil{t.Fatal(e)}
 if r,e:=lookupClientCommandIdentity(context.Background(),tx,doc,configurationFixturePrincipal,raw,env);e!=nil||r!=nil{t.Fatalf("host anchor polluted client lookup: %v %v",r,e)}
 identityRefusal(t,tx,doc,raw,env)
 var count int;if e=tx.QueryRow(`SELECT count(*) FROM idempotency WHERE principal=? AND key=?`,configurationFixturePrincipal,configurationFixturePrincipal).Scan(&count);e!=nil||count!=2{t.Fatalf("separate namespaces lost: count=%d error=%v",count,e)}
 if _,e=tx.Exec(`UPDATE idempotency SET body=body WHERE operation='host:managed-verifier-lineage'`);e==nil{t.Fatal("anchor immutable update guard absent")}
 t.Log("same principal and command key: managed anchor retained; client request/replay isolated; original immutable update trigger enforced")
}
