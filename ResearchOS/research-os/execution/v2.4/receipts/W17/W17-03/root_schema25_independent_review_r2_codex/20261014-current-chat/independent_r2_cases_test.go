package domain

import (
 "database/sql"
 "testing"
 "fmt"
)

func reviewCheckpointHash(t *testing.T,db *sql.DB) string {
 var hash string
 if err:=db.QueryRow(`SELECT checkpoint_hash FROM runtime_pause_intents`).Scan(&hash);err!=nil {t.Fatal(err)}
 return hash
}

func reviewWitness(t *testing.T,db *sql.DB) {
 rows,err:=configurationBackupRows(db,`SELECT * FROM runtime_pause_intents`)
 if err!=nil||len(rows)!=1 {t.Fatal(rows,err)}
 var count int
 if err:=db.QueryRow(`SELECT count(*) FROM runtime_pause_receipts`).Scan(&count);err!=nil {t.Fatal(err)}
 var prev any
 if count>0 {var hash string; if err:=db.QueryRow(`SELECT body_hash FROM runtime_pause_receipts WHERE sequence=?`,count).Scan(&hash);err!=nil{t.Fatal(err)};prev=hash}
 intent:=rows[0]
 body:=Object{"project":"p","pause_id":"pause","kind":"STATE_TRANSITION","sequence":count+1,"state":intent["state"],"revision":intent["revision"],"intent_hash":Hash(intent)}
 pauseStorageExec(t,db,`INSERT INTO runtime_pause_receipts(receipt_id,project,pause_id,sequence,kind,body,body_hash,previous_receipt_hash,created_at) VALUES(?,'p','pause',?,'STATE_TRANSITION',?,?,?,'now')`,fmt.Sprintf("review-witness-%d",count+1),count+1,string(Bytes(body)),Hash(body),prev)
}

func TestIndependentR2CancelRequestedRejected(t *testing.T) {
 db,oldUse,newUse:=reviewPauseValid(t)
 pauseStorageExec(t,db,`UPDATE domain_objects SET body=json_set(body,'$.status','CANCEL_REQUESTED') WHERE kind='Run'`)
 if err:=reviewActivate(t,db,oldUse,newUse,"actor");err==nil {t.Fatal("CANCEL_REQUESTED successor accepted")}
}

func TestIndependentR2MissingActivationActorRejected(t *testing.T) {
 db,oldUse,newUse:=reviewPauseValid(t)
 if err:=reviewActivate(t,db,oldUse,newUse,"nonexistent-actor");err!=nil {t.Fatal(err)}
 // Keep carry actor equal to activation so the missing principal itself is tested.
 pauseStorageExec(t,db,`UPDATE resource_checkpoint_carries SET body=json_set(body,'$.actor','nonexistent-actor')`)
 if err:=validateBackupPause(db);err==nil {t.Fatal("missing actor accepted")}
}

func TestIndependentR2CarryMutationsRejected(t *testing.T) {
 for _,field:=range []string{"actor","artifact_ref.id","artifact_ref.content_hash","new_upload_key","reason","from_use_receipt_hash","from_epoch","to_epoch"} {
  t.Run(field,func(t *testing.T){
   db,oldUse,newUse:=reviewPauseValid(t)
   if err:=reviewActivate(t,db,oldUse,newUse,"actor");err!=nil{t.Fatal(err)}
   if err:=validateBackupPause(db);err!=nil{t.Fatal("positive control",err)}
   pauseStorageExec(t,db,`UPDATE resource_checkpoint_carries SET body=json_set(body,?,'incorrect')`,"$."+field)
   if err:=validateBackupPause(db);err==nil{t.Fatal("bad carry accepted",field)}
  })
 }
}

func TestIndependentR2NoReceiptHistoryRejected(t *testing.T) {
 db,_,_:=reviewPauseValid(t)
 configurationBackupMutation(t,db,`DELETE FROM runtime_pause_receipts`)
 if err:=validateBackupPause(db);err==nil{t.Fatal("no receipts accepted")}
}

func TestIndependentR2CompleteHistoryAndLaterCancellation(t *testing.T) {
 db,oldUse,newUse:=reviewPauseValid(t)
 if err:=reviewActivate(t,db,oldUse,newUse,"actor");err!=nil{t.Fatal(err)}
 pauseStorageExec(t,db,`UPDATE runtime_pause_intents SET state='RESUMED',revision=revision+1`)
 reviewWitness(t,db)
 if err:=validateBackupPause(db);err!=nil{t.Fatal("resumed history",err)}
 pauseStorageExec(t,db,`UPDATE domain_objects SET body=json_set(body,'$.status','CANCEL_REQUESTED','$.executor_principal_id','new-current-executor') WHERE kind='Run'`)
 if err:=validateBackupPause(db);err!=nil{t.Fatal("later cancellation or executor evolution destroyed historical proof",err)}
 pauseStorageExec(t,db,`UPDATE runtime_pause_intents SET state='CANCELLED',revision=revision+1`)
 reviewWitness(t,db)
 if err:=validateBackupPause(db);err!=nil{t.Fatal("cancelled history",err)}
 var witnesses int
 if err:=db.QueryRow(`SELECT count(*) FROM runtime_pause_receipts`).Scan(&witnesses);err!=nil||witnesses!=6 {t.Fatal("full six-revision witness history expected",witnesses,err)}
}
