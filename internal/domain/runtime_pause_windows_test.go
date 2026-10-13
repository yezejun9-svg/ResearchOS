//go:build windows

package domain

import (
	"database/sql"
	"os"
	"path/filepath"
	"testing"
)

func TestRuntimePauseRecoveryBoundedFile(t *testing.T) {
	root := t.TempDir()
	path := filepath.Join(root, "checkpoint.sealed.json")
	raw := []byte(`{"complete":true}`)
	if err := os.WriteFile(path, raw, 0600); err != nil {
		t.Fatal(err)
	}
	got, err := readRuntimePauseFile(path, int64(len(raw)))
	if err != nil || string(got) != string(raw) {
		t.Fatal("exact read", err)
	}
	if _, err = readRuntimePauseFile(path, int64(len(raw)-1)); err == nil {
		t.Fatal("oversize accepted")
	}
	if _, err = readRuntimePauseFile(root, 100); err == nil {
		t.Fatal("directory accepted")
	}
	if err = os.WriteFile(path, nil, 0600); err != nil {
		t.Fatal(err)
	}
	if _, err = readRuntimePauseFile(path, 100); err == nil {
		t.Fatal("empty accepted")
	}
}

func TestRuntimePauseActivationNeverFallsThroughMissingProof(t *testing.T) {
	for _, scenario := range []string{"schema-missing", "activation-missing", "marker-missing", "checkpoint-witness-mismatch", "ordinary-dispatch"} {
		t.Run(scenario, func(t *testing.T) {
			version := 25
			if scenario == "schema-missing" {
				version = 24
			}
			db, _ := configurationDB(t, version, true)
			service := &Service{DB: db}
			marker := Object{"pause_id": "p", "previous_epoch": 1, "checkpoint_hash": "h"}
			dispatch := Object{"manifest": Object{"admission": Object{"sealed_pause_activation": marker}}}
			run := Object{"id": "r", "task_id": "t", "lease_epoch": 2}
			if scenario == "ordinary-dispatch" {
				dispatch = Object{"manifest": Object{"admission": Object{}}}
			}
			if scenario == "marker-missing" || scenario == "checkpoint-witness-mismatch" {
				db.Close()
				var oldUse, newUse string
				db, oldUse, newUse = pauseStorageValidHistory(t)
				service.DB = db
				if err := pauseStorageActivate(t, db, oldUse, newUse, "actor"); err != nil {
					t.Fatal(err)
				}
				dispatch = Object{"dispatch_key": "d2", "manifest_hash": "m2", "manifest": Object{"admission": Object{"qualification_ids": []any{"q"}}}}
				if scenario == "checkpoint-witness-mismatch" {
					dispatch["manifest"].(Object)["admission"].(Object)["sealed_pause_activation"] = Object{"pause_id": "pause", "previous_epoch": 1, "checkpoint_hash": pauseStorageCheckpointHash(t, db)}
				}
			}
			tx, err := db.Begin()
			if err != nil {
				t.Fatal(err)
			}
			defer tx.Rollback()
			err = service.pauseActivationGate(tx, "p", run, dispatch)
			if (err == nil) != (scenario == "ordinary-dispatch") {
				t.Fatalf("%s: %v", scenario, err)
			}
		})
	}
}

// This is a storage fixture. The host test separately proves the actual native
// stop and restore. Only an exact PREPARED activation may receive a new lease.
func TestRuntimePauseUnstartedActivationFence(t *testing.T) {
	for _, mutation := range []string{"valid", "started", "worker", "identity", "journal-locator", "journal-exists", "cancelled", "run-cancel", "run-old-epoch", "task-blocked", "queue-cancel", "queue-restore", "foreign-dispatch"} {
		t.Run(mutation, func(t *testing.T) {
			db, oldUse, newUse := pauseNativeStorageHistory(t)
			manifest := Object{"project_id": "p", "run_id": "r", "epoch": 2, "dispatch_key": "d2"}
			manifestHash := Hash(manifest)

			pauseStorageExec(t, db, `UPDATE runtime_pause_intents SET state='RESUME_PREPARED',successor_epoch=2,revision=revision+1`)
			pauseStorageExec(t, db, `INSERT INTO resource_checkpoint_carries(project,run,epoch,body) VALUES('p','r',2,?)`, string(Bytes(Object{"actor": "actor", "artifact_ref": Object{"entity_type": "Artifact", "id": "a", "content_hash": pauseStorageCheckpointHash(t, db)}, "from_use_receipt_hash": oldUse, "from_epoch": 1, "to_epoch": 2, "new_upload_key": "new-upload", "reason": "CHECKPOINT_CARRY_NOT_NEW_RESULT"})))
			pauseStorageExec(t, db, `INSERT INTO runtime_checkpoint_activations(project,run,epoch,previous_epoch,pause_id,task,session_id,generation,principal,request_key,request_hash,dispatch_key,manifest_hash,checkpoint_artifact,checkpoint_hash,checkpoint_use_receipt_hash,checkpoint_use_principal,carry_use_receipt_hash,carry_use_principal,original_input_hash,native_session_ref,sdk_session_id,queue_cut,model_calls,tool_calls,created_at) SELECT project,run,2,epoch,pause_id,task,session_id,generation,'actor','resume-command','resume-request','d2',?,checkpoint_artifact,checkpoint_hash,checkpoint_use_receipt_hash,checkpoint_use_principal,?,'other-executor',original_input_hash,native_session_ref,sdk_session_id,queue_cut,model_calls,tool_calls,'now' FROM runtime_pause_intents`, manifestHash, newUse)
			pauseStorageWitness(t, db)
			pauseStorageExec(t, db, `UPDATE domain_objects SET body='{"id":"r","status":"QUEUED","task_id":"t","lease_epoch":2,"executor_principal_id":"executor"}' WHERE kind='Run'`)
			pauseStorageExec(t, db, `UPDATE domain_objects SET body='{"id":"t","status":"RUNNING","active_run_id":"r"}' WHERE kind='Task'`)
			pauseStorageExec(t, db, `UPDATE client_queue_fences SET runtime_epoch=2,dispatch_key='d2',manifest_hash=?`, manifestHash)
			root := t.TempDir()
			switch mutation {
			case "started":
				pauseStorageExec(t, db, `UPDATE runtime_dispatches SET state='STARTED' WHERE epoch=2`)
			case "worker":
				pauseStorageExec(t, db, `UPDATE runtime_dispatches SET worker='acknowledged' WHERE epoch=2`)
			case "identity":
				pauseStorageExec(t, db, `UPDATE runtime_dispatches SET identity='{"pid":1}' WHERE epoch=2`)
			case "journal-locator":
				pauseStorageExec(t, db, `UPDATE runtime_dispatches SET journal_locator='d2' WHERE epoch=2`)
			case "journal-exists":
				if err := os.MkdirAll(filepath.Join(root, "runtime-dispatches", "d2"), 0700); err != nil {
					t.Fatal(err)
				}
			case "cancelled":
				pauseStorageExec(t, db, `UPDATE runtime_pause_intents SET state='CANCELLED',revision=revision+1`)
			case "run-cancel":
				pauseStorageExec(t, db, `UPDATE domain_objects SET body=json_set(body,'$.status','CANCEL_REQUESTED') WHERE kind='Run'`)
			case "run-old-epoch":
				pauseStorageExec(t, db, `UPDATE domain_objects SET body=json_set(body,'$.lease_epoch',1) WHERE kind='Run'`)
			case "task-blocked":
				pauseStorageExec(t, db, `UPDATE domain_objects SET body=json_set(body,'$.status','BLOCKED') WHERE kind='Task'`)
			case "queue-cancel":
				pauseStorageExec(t, db, `UPDATE client_queue_fences SET state='CANCEL_FENCED'`)
			case "queue-restore":
				pauseStorageExec(t, db, `UPDATE client_queue_fences SET restore_fenced=1`)
			case "foreign-dispatch":
				pauseStorageExec(t, db, `UPDATE client_queue_fences SET dispatch_key='foreign'`)
			}
			c := &RuntimeCoordinator{service: &Service{DB: db}, config: RuntimeCoordinatorConfig{DataRoot: root}}
			tx, err := db.Begin()
			if err != nil {
				t.Fatal(err)
			}
			defer tx.Rollback()
			a, _, err := c.unstartedPauseActivation(tx, "p", "r", 2)
			if mutation == "valid" {
				if err != nil || a == nil {
					t.Fatal("safe preparation rejected", err)
				}
			} else if a != nil {
				t.Fatal("ambiguous activation was restartable", mutation)
			}
		})
	}
}

func TestRuntimePauseCanonicalQueueCut(t *testing.T) {
	for _, mutation := range []string{"valid", "sending", "unknown", "dropped", "consumed-downgrade", "content-change", "generation-change", "hash-change", "cut-change", "omit-accepted"} {
		t.Run(mutation, func(t *testing.T) {
			db, _, _ := pauseStorageValidHistory(t)
			content := `{"text":"same queue content","attachments":[]}`
			hash := Digest([]byte(content))
			pauseStorageExec(t, db, `INSERT INTO client_command_queue(principal,project,command_id,session_id,task_id,goal_id,generation,queue_sequence,request_hash,message_id,accepted_writer_epoch,delivery,content,content_hash,state,created_at) VALUES('actor','p','c','s','t','goal','g',1,'req','msg',1,'STEER',?,?,'SDK_ACCEPTED','now')`, content, hash)
			// An append above the worker's frozen cut must remain ENQUEUED.
			pauseStorageExec(t, db, `INSERT INTO client_command_queue(principal,project,command_id,session_id,task_id,goal_id,generation,queue_sequence,request_hash,message_id,accepted_writer_epoch,delivery,content,content_hash,state,created_at) VALUES('actor','p','later','s','t','goal','g',2,'req2','later-msg',1,'FOLLOW_UP',?,?,'ENQUEUED','now')`, content, hash)
			frozen := Object{"command_id": "c", "message_id": "msg", "queue_sequence": 1, "content": content, "content_hash": hash, "delivery": "STEER"}
			details := Object{"command_id": "c", "queue_sequence": 1, "queue_generation": "g", "content_hash": hash}
			entry := Object{"message_id": "msg", "details": details, "frozen": string(Bytes(frozen)), "state": "SDK_ACCEPTED"}
			commands := []any{entry}
			cut := Object{"queue_cut": 1, "command_ledger_hash": Hash(commands)}
			switch mutation {
			case "sending":
				pauseStorageExec(t, db, `UPDATE client_command_queue SET state='SENDING' WHERE command_id='c'`)
			case "unknown":
				pauseStorageExec(t, db, `UPDATE client_command_queue SET state='UNKNOWN' WHERE command_id='c'`)
			case "dropped":
				pauseStorageExec(t, db, `UPDATE client_command_queue SET state='DROPPED' WHERE command_id='c'`)
			case "consumed-downgrade":
				pauseStorageExec(t, db, `UPDATE client_command_queue SET state='CONSUMED' WHERE command_id='c'`)
			case "content-change":
				pauseStorageExec(t, db, `UPDATE client_command_queue SET content='changed' WHERE command_id='c'`)
			case "generation-change":
				details["queue_generation"] = "foreign"
				cut["command_ledger_hash"] = Hash(commands)
			case "hash-change":
				cut["command_ledger_hash"] = "foreign"
			case "cut-change":
				cut["queue_cut"] = 2
			case "omit-accepted":
				pauseStorageExec(t, db, `UPDATE client_command_queue SET state='SDK_ACCEPTED' WHERE command_id='later'`)
			}
			tx, err := db.Begin()
			if err != nil {
				t.Fatal(err)
			}
			defer tx.Rollback()
			err = validatePauseQueue(tx, Object{"generation": "g"}, Object{"commands": commands, "queue_state": cut})
			if (err == nil) != (mutation == "valid") {
				t.Fatalf("%s: %v", mutation, err)
			}
		})
	}
}

func pauseNativeStorageHistory(t *testing.T) (*sql.DB, string, string) {
	db, _ := configurationDB(t, 25, true)
	pauseStorageExec(t, db, `INSERT INTO auth_principals(id,roles) VALUES('actor','["OWNER"]'),('executor','["EXECUTOR"]'),('other-executor','["EXECUTOR"]')`)
	pauseStorageExec(t, db, `INSERT INTO domain_objects(project,kind,id,revision,body) VALUES('p','Task','t',1,'{}'),('p','Run','r',1,'{"status":"RUNNING","task_id":"t","lease_epoch":2,"executor_principal_id":"executor"}')`)
	pauseStorageExec(t, db, `INSERT INTO client_sessions(id,project_id,revision,created_at,updated_at,task_id,run_id,writer_epoch,writer_client_id,event_watermark,upstream_session_id) VALUES('s','p',1,'now','now','t','r',1,'client',0,'native')`)
	pauseStorageExec(t, db, `INSERT INTO client_queue_fences(project,task_id,session_id,generation,state) VALUES('p','t','s','g','OPEN')`)
	pauseStorageExec(t, db, `INSERT INTO runtime_dispatches(project,run,epoch,dispatch_key,manifest,manifest_hash,state,identity,prepared_at,updated_at) VALUES('p','r',1,'d1','{}','m1','OBSERVED','{}','now','now'),('p','r',2,'d2',?,?,'PREPARED','{}','now','now')`, string(Bytes(Object{"project_id": "p", "run_id": "r", "epoch": 2, "dispatch_key": "d2"})), Hash(Object{"project_id": "p", "run_id": "r", "epoch": 2, "dispatch_key": "d2"}))
	pauseStorageExec(t, db, `INSERT INTO runtime_pause_intents(project,pause_id,task,run,epoch,session_id,generation,principal,request_key,request_hash,runtime,dispatch_key,manifest_hash,process_identity_hash,original_input_hash,state,created_at,updated_at) VALUES('p','pause','t','r',1,'s','g','actor','pause-command','request','runtime','d1','m1',?,'input','PAUSE_REQUESTED','now','now')`, Hash(Object{}))
	content := []byte(`{"session":"sdk","leaseEpoch":1}`)
	contentHash := Digest(content)
	pauseStorageExec(t, db, `INSERT INTO domain_objects(project,kind,id,revision,body) VALUES('p','Artifact','a',1,?)`, string(Bytes(Object{"kind": "CHECKPOINT", "content_hash": contentHash})))
	hashes := []string{}
	for i, principal := range []string{"executor", "other-executor"} {
		storage := []string{"old-upload", "new-upload"}[i]
		use := Object{"project_id": "p", "run_id": "r", "lease_epoch": i + 1, "principal_id": principal, "storage_key": storage, "content_hash": contentHash, "byte_size": len(content), "artifact_ref": Object{"entity_type": "Artifact", "id": "a", "content_hash": contentHash, "revision": 1}}
		use["receipt_hash"] = Receipt(use)
		hashes = append(hashes, Str(use, "receipt_hash"))
		pauseStorageExec(t, db, `INSERT INTO uploaded_content(storage_key,project,principal,bytes,content_hash,expires_at,sealed) VALUES(?,'p',?,?,?,'2099-01-01T00:00:00Z',1)`, storage, principal, content, contentHash)
		pauseStorageExec(t, db, `INSERT INTO artifact_uses(project,artifact,run,epoch,principal,storage_key,receipt_hash,body) VALUES('p','a','r',?,?,?,?,?)`, i+1, principal, storage, use["receipt_hash"], string(Bytes(use)))
	}
	pauseStorageExec(t, db, `UPDATE runtime_pause_intents SET state='CHECKPOINT_SEALED',revision=revision+1,checkpoint_sequence=1,checkpoint_artifact='a',checkpoint_use_receipt_hash=?,checkpoint_use_principal='executor',checkpoint_hash=?,checkpoint_bytes=?,native_session_ref='native',sdk_session_id='sdk',queue_cut=0,command_ledger_hash='ledger',sdk_watermarks_json='{}',model_calls=1,tool_calls=2,journal_checkpoint_hash='journal'`, hashes[0], contentHash, len(content))
	pauseStorageExec(t, db, `UPDATE runtime_pause_intents SET state='PAUSED_CONFIRMED',revision=revision+1`)
	pauseStorageWitness(t, db)
	if err := validateBackupPause(db); err != nil {
		t.Fatal("valid paused fixture", err)
	}
	return db, hashes[0], hashes[1]
}
