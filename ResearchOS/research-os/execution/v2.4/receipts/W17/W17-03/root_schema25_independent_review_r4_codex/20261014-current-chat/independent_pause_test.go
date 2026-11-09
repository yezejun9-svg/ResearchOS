package domain

import (
 "database/sql"
 "testing"
)

func reviewPauseValid(t *testing.T) (*sql.DB, string, string) {
 db,_:=configurationDB(t,25,true)
 pauseStorageExec(t,db,`INSERT INTO auth_principals(id,roles) VALUES('actor','["OWNER"]'),('executor','["EXECUTOR"]'),('other-executor','["EXECUTOR"]')`)
 pauseStorageExec(t,db,`INSERT INTO domain_objects(project,kind,id,revision,body) VALUES('p','Task','t',1,'{}'),('p','Run','r',1,'{"status":"RUNNING","task_id":"t","lease_epoch":2,"executor_principal_id":"executor"}')`)
 pauseStorageExec(t,db,`INSERT INTO client_sessions(id,project_id,revision,created_at,updated_at,task_id,run_id,writer_epoch,writer_client_id,event_watermark,upstream_session_id) VALUES('s','p',1,'now','now','t','r',1,'client',0,'native')`)
 pauseStorageExec(t,db,`INSERT INTO client_queue_fences(project,task_id,session_id,generation,state) VALUES('p','t','s','g','OPEN')`)
 pauseStorageExec(t,db,`INSERT INTO runtime_dispatches(project,run,epoch,dispatch_key,manifest,manifest_hash,state,identity,prepared_at,updated_at) VALUES('p','r',1,'d1','{}','m1','OBSERVED','{}','now','now'),('p','r',2,'d2','{}','m2','PREPARED','{}','now','now')`)
 pauseStorageExec(t,db,`INSERT INTO runtime_pause_intents(project,pause_id,task,run,epoch,session_id,generation,principal,request_key,request_hash,runtime,dispatch_key,manifest_hash,process_identity_hash,original_input_hash,state,created_at,updated_at) VALUES('p','pause','t','r',1,'s','g','actor','pause-command','request','runtime','d1','m1',?,'input','PAUSE_REQUESTED','now','now')`,Hash(Object{}))
 reviewWitness(t,db)
 content:=[]byte(`{"session":"sdk","leaseEpoch":1}`)
 contentHash:=Digest(content)
 pauseStorageExec(t,db,`INSERT INTO domain_objects(project,kind,id,revision,body) VALUES('p','Artifact','a',1,?)`,string(Bytes(Object{"kind":"CHECKPOINT","content_hash":contentHash})))
 hashes:=[]string{}
 for i,principal:=range []string{"executor","other-executor"} {
  storage:=[]string{"old-upload","new-upload"}[i]
  use:=Object{"project_id":"p","run_id":"r","lease_epoch":i+1,"principal_id":principal,"storage_key":storage,"content_hash":contentHash,"byte_size":len(content),"artifact_ref":Object{"entity_type":"Artifact","id":"a","content_hash":contentHash,"revision":1}}
  use["receipt_hash"]=Receipt(use)
  hashes=append(hashes,Str(use,"receipt_hash"))
  pauseStorageExec(t,db,`INSERT INTO uploaded_content(storage_key,project,principal,bytes,content_hash,expires_at,sealed) VALUES(?,'p',?,?,?,'2099-01-01T00:00:00Z',1)`,storage,principal,content,contentHash)
  pauseStorageExec(t,db,`INSERT INTO artifact_uses(project,artifact,run,epoch,principal,storage_key,receipt_hash,body) VALUES('p','a','r',?,?,?,?,?)`,i+1,principal,storage,use["receipt_hash"],string(Bytes(use)))
 }
 pauseStorageExec(t,db,`UPDATE runtime_pause_intents SET state='CHECKPOINT_SEALED',revision=revision+1,checkpoint_sequence=1,checkpoint_artifact='a',checkpoint_use_receipt_hash=?,checkpoint_use_principal='executor',checkpoint_hash=?,checkpoint_bytes=?,native_session_ref='native',sdk_session_id='sdk',queue_cut=0,command_ledger_hash='ledger',sdk_watermarks_json='{}',model_calls=1,tool_calls=2,journal_checkpoint_hash='journal'`,hashes[0],contentHash,len(content))
 reviewWitness(t,db)
 pauseStorageExec(t,db,`UPDATE runtime_pause_intents SET state='PAUSED_CONFIRMED',revision=revision+1`)
 reviewWitness(t,db)
 if err:=validateBackupPause(db);err!=nil {t.Fatal("valid paused fixture",err)}
 return db,hashes[0],hashes[1]
}

func reviewActivate(t *testing.T,db *sql.DB,oldUse,newUse,actor string) error {
 pauseStorageExec(t,db,`UPDATE runtime_pause_intents SET state='RESUME_PREPARED',successor_epoch=2,revision=revision+1`)
 pauseStorageExec(t,db,`INSERT INTO resource_checkpoint_carries(project,run,epoch,body) VALUES('p','r',2,?)`,string(Bytes(Object{"actor":"actor","artifact_ref":Object{"entity_type":"Artifact","id":"a","content_hash":reviewCheckpointHash(t,db)},"from_use_receipt_hash":oldUse,"from_epoch":1,"to_epoch":2,"new_upload_key":"new-upload","reason":"CHECKPOINT_CARRY_NOT_NEW_RESULT"})))
 _,err:=db.Exec(`INSERT INTO runtime_checkpoint_activations(project,run,epoch,previous_epoch,pause_id,task,session_id,generation,principal,request_key,request_hash,dispatch_key,manifest_hash,checkpoint_artifact,checkpoint_hash,checkpoint_use_receipt_hash,checkpoint_use_principal,carry_use_receipt_hash,carry_use_principal,original_input_hash,native_session_ref,sdk_session_id,queue_cut,model_calls,tool_calls,created_at)
 SELECT project,run,2,epoch,pause_id,task,session_id,generation,?,'resume-command','resume-request','d2','m2',checkpoint_artifact,checkpoint_hash,checkpoint_use_receipt_hash,checkpoint_use_principal,?,'other-executor',original_input_hash,native_session_ref,sdk_session_id,queue_cut,model_calls,tool_calls,'now' FROM runtime_pause_intents`,actor,newUse)
 if err==nil {reviewWitness(t,db)}
 return err
}


