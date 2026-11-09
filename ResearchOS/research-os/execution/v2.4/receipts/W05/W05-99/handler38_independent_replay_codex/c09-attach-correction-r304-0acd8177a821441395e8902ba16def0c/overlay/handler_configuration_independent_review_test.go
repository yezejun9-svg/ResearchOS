package domain

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"net/url"
	"os"
	"path/filepath"
	"reflect"
	"sort"
	"strings"
	"testing"
	"time"

	"researchos.local/research-os/internal/store"
)

// Independent, explicitly INJECTED residual-state controls. No runtime, Host,
// credential decryption, process, provider, HTTP or SDK is constructed here.
type independentC09Metadata struct {
	owner, principal string
	calls            int
}

func (m *independentC09Metadata) ConfigurationMetadata(_ context.Context, principal, provider string, ref *string) (ClientConfigurationMetadata, error) {
	m.calls++
	if principal != m.principal {
		return ClientConfigurationMetadata{}, fmt.Errorf("C09 wrong principal")
	}
	v := ClientConfigurationMetadata{OwnerHost: m.owner, Principal: principal}
	if ref != nil {
		v.Credential = &ClientCredentialMetadata{Ref: *ref, Provider: provider, Kind: "API_KEY", Status: "AVAILABLE", CheckedAt: Now()}
	}
	return v, nil
}

type independentC09State map[string][]Object

func independentC09Object(t *testing.T, o Object, key string) Object {
	t.Helper()
	v, ok := o[key].(map[string]any)
	if !ok {
		t.Fatalf("expected object %s", key)
	}
	return v
}
func independentC09Write(t *testing.T, dir, name string, value any) {
	t.Helper()
	raw, e := json.MarshalIndent(value, "", "  ")
	if e != nil {
		t.Fatal(e)
	}
	p := filepath.Join(dir, name)
	f, e := os.OpenFile(p, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if e != nil {
		t.Fatal(e)
	}
	if _, e = f.Write(append(raw, '\n')); e != nil {
		f.Close()
		t.Fatal(e)
	}
	if e = f.Close(); e != nil {
		t.Fatal(e)
	}
}
func independentC09StateRead(t *testing.T, db *sql.DB) independentC09State {
	t.Helper()
	result := independentC09State{}
	schema, e := configurationBackupRows(db, `SELECT type,name,tbl_name,rootpage,sql FROM sqlite_schema ORDER BY type,name`)
	if e != nil {
		t.Fatal(e)
	}
	result["__schema"] = schema
	for _, entry := range schema {
		if entry["type"] != "table" {
			continue
		}
		name := Str(entry, "name")
		quoted := `"` + strings.ReplaceAll(name, `"`, `""`) + `"`
		selectCols := "rowid AS __original_rowid__,*"
		if strings.Contains(strings.ToUpper(Str(entry, "sql")), "WITHOUT ROWID") {
			selectCols = "*"
		}
		rows, e := configurationBackupRows(db, "SELECT "+selectCols+" FROM "+quoted)
		if e != nil {
			t.Fatal(e)
		}
		sort.Slice(rows, func(i, j int) bool { return string(Bytes(rows[i])) < string(Bytes(rows[j])) })
		result[name] = rows
	}
	return result
}
func independentC09Exact(t *testing.T, before, after independentC09State, allowed map[string]bool) {
	t.Helper()
	if len(before) != len(after) {
		t.Fatal("table inventory changed")
	}
	for table, rows := range before {
		if !allowed[table] && !reflect.DeepEqual(rows, after[table]) {
			t.Fatalf("unexpected mutation %s", table)
		}
	}
}
func independentC09Append(t *testing.T, before, after []Object, n int) []Object {
	t.Helper()
	counts := map[string]int{}
	for _, v := range before {
		counts[string(Bytes(v))]++
	}
	added := []Object{}
	for _, v := range after {
		k := string(Bytes(v))
		if counts[k] > 0 {
			counts[k]--
		} else {
			added = append(added, v)
		}
	}
	for _, v := range counts {
		if v != 0 {
			t.Fatal("original row altered/deleted")
		}
	}
	if len(added) != n {
		t.Fatalf("added rows got %d want %d", len(added), n)
	}
	return added
}
func independentC09Session(t *testing.T, db *sql.DB, sid string) Object {
	t.Helper()
	v, e := configurationBackupRows(db, `SELECT * FROM client_sessions WHERE id=?`, sid)
	if e != nil || len(v) != 1 {
		t.Fatalf("session %v %d", e, len(v))
	}
	return v[0]
}
func independentC09Command(t *testing.T, db *sql.DB, s *ClientService, principal string, env *Envelope, dir, label string) (*Response, bool) {
	t.Helper()
	raw := Bytes(env)
	independentC09Write(t, dir, label+".request.json", Object{"raw_request_base64": base64.StdEncoding.EncodeToString(raw), "raw_sha256": Digest(raw), "raw_bytes": len(raw)})
	decoded, e := DecodeEnvelope(raw)
	if e != nil {
		t.Fatal(e)
	}
	tx, e := db.BeginTx(context.Background(), nil)
	if e != nil {
		t.Fatal(e)
	}
	defer tx.Rollback()
	r, replay, e := s.Execute(context.Background(), tx, decoded, principal)
	if e != nil {
		t.Fatal(e)
	}
	if r == nil || deref(r.CommandID) != deref(env.CommandID) || deref(r.Method) != deref(env.Method) || deref(r.SessionID) != deref(env.SessionID) {
		t.Fatal("response original identity mismatch")
	}
	var generic map[string]any
	if e = json.Unmarshal(Bytes(r), &generic); e != nil {
		t.Fatal(e)
	}
	if e = s.Doc.ValidateDef("CommandResponse", generic); e != nil {
		t.Fatal(e)
	}
	if e = ValidateResultAgainstMethod(deref(env.Method), r, s.Doc); e != nil {
		t.Fatal(e)
	}
	if e = tx.Commit(); e != nil {
		t.Fatal(e)
	}
	independentC09Write(t, dir, label+".json", Object{"raw_request_base64": base64.StdEncoding.EncodeToString(raw), "response": r, "replay": replay})
	return r, replay
}
func TestIndependentHandlerConfigurationC09(t *testing.T) {
	root := os.Getenv("RESEARCHOS_C09_ROOT")
	if root == "" {
		t.Fatal("explicit frozen C09 root required")
	}
	cases := []string{"permission-resolved-positive", "all-runs-settled-positive", "permission-open", "permission-acknowledged", "older-run-unknown-hidden-by-later-settled-run", "older-run-running-hidden-by-later-settled-run"}
	for _, name := range cases {
		if !t.Run(name, func(t *testing.T) {
			dir := filepath.Join(root, "cases", name)
			input := filepath.Join(dir, "input.sqlite")
			raw, e := os.ReadFile(input)
			if e != nil {
				t.Fatal(e)
			}
			if Digest(raw) != "sha256:16a69152e10889815d686f1d91387e3dfd4d0086d6fca6b109698b9b2b33a3d1" {
				t.Fatal("frozen fixture differs")
			}
			working := filepath.Join(dir, "actual.sqlite")
			file, e := os.OpenFile(working, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
			if e != nil {
				t.Fatal(e)
			}
			_, e = file.Write(raw)
			closeErr := file.Close()
			if e != nil || closeErr != nil {
				t.Fatalf("copy %v %v", e, closeErr)
			}
			immutableURI := url.URL{Scheme: "file", Opaque: filepath.ToSlash(working), RawQuery: "mode=ro&immutable=1"}
			reader, e := sql.Open("sqlite", immutableURI.String())
			if e != nil {
				t.Fatal(e)
			}
			reader.SetMaxOpenConns(1)
			closedInput := independentC09StateRead(t, reader)
			if e = reader.Close(); e != nil {
				t.Fatal(e)
			}
			independentC09Write(t, dir, "00.before-store-open.fullrows.json", closedInput)
			db, e := store.Open(working)
			if e != nil {
				t.Fatal(e)
			}
			defer func() {
				final := independentC09StateRead(t, db)
				independentC09Write(t, dir, "closed.fullrows.json", final)
				if _, e := db.Exec(`PRAGMA wal_checkpoint(TRUNCATE)`); e != nil {
					t.Error(e)
				}
				if e := db.Close(); e != nil {
					t.Error(e)
				}
				b, e := os.ReadFile(working)
				if e != nil {
					t.Error(e)
				} else {
					independentC09Write(t, dir, "closed.bytes.json", Object{"sha256": Digest(b), "bytes": len(b), "input_sha256": Digest(raw), "byte_equal_not_assumed": true})
				}
			}()
			before := independentC09StateRead(t, db)
			independentC09Write(t, dir, "01.after-store-open.fullrows.json", before)
			if !reflect.DeepEqual(closedInput, before) {
				t.Fatal("store.Open changed initial schema or row multiset")
			}
			rows, e := configurationBackupRows(db, `SELECT * FROM client_sessions WHERE run_id IS NOT NULL AND run_id<>''`)
			if e != nil || len(rows) != 1 {
				t.Fatalf("unique settled original session prerequisite %v count=%d", e, len(rows))
			}
			sess := rows[0]
			sid, project, client := Str(sess, "id"), Str(sess, "project_id"), Str(sess, "writer_client_id")
			config, e := configurationBackupRows(db, `SELECT * FROM host_model_configurations WHERE model_config_ref=?`, sess["model_config_ref"])
			if e != nil || len(config) != 1 {
				t.Fatal("original typed config missing", e)
			}
			owner, principal := Str(config[0], "owner_host_ref"), Str(config[0], "principal")
			contracts, e := LoadContracts("../../spec/v2.0/contracts")
			if e != nil {
				t.Fatal(e)
			}
			service := &Service{DB: db, Contracts: contracts}
			doc := configurationSchema(t)
			metadata := &independentC09Metadata{owner: owner, principal: principal}
			clientService := &ClientService{Doc: doc, Domain: service, ConfigurationAuthority: metadata, Host: ClientHostInfo{InstanceID: owner, CoreBuildID: "independent-C09-SYNTHETIC", LeaseTTL: time.Hour}}
			rev, e := Num(sess, "revision")
			if e != nil {
				t.Fatal(e)
			}
			epoch, e := Num(sess, "writer_epoch")
			if e != nil {
				t.Fatal(e)
			}
			watermark, e := Num(sess, "event_watermark")
			if e != nil || watermark < 0 {
				t.Fatalf("invalid original watermark: %v", e)
			}
			attach := &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: &client, ProjectID: &project, SessionID: &sid, ExpectedRevision: &rev, WriterEpoch: nil, Method: strptr("session.attach"), Payload: Bytes(Object{"after_sequence": watermark, "request_write_owner": true})}
			ar, replayed := independentC09Command(t, db, clientService, principal, attach, dir, "02.actual-attach")
			if replayed || deref(ar.Status) != "ACKNOWLEDGED" {
				t.Fatalf("attach prerequisite %s", Bytes(ar))
			}
			actualAttach := independentC09Session(t, db, sid)
			if actualAttach["writer_epoch"] != epoch+1 || actualAttach["revision"] != rev+2 || actualAttach["writer_client_id"] != client {
				t.Fatal("actual handoff epoch/revision/client mismatch")
			}
			attached := independentC09StateRead(t, db)
			independentC09Write(t, dir, "03.post-attach.fullrows.json", attached)
			// Actual caller-transaction takeover is ACK only. Prove its real
			// lease/journal and immutable replay; never manufacture COMPLETED.
			if ar.Revision == nil || *ar.Revision != rev+2 || ar.ErrorCode != nil || ar.Error != nil {
				t.Fatal("attach typed ACK fields")
			}
			accepted, e := time.Parse(time.RFC3339Nano, Str(ar.Result, "accepted_at"))
			if e != nil {
				t.Fatal(e)
			}
			returnedSequence, e := Num(ar.Result, "after_sequence")
			if e != nil || returnedSequence != watermark+1 || ar.Result["operation_id"] != "op-"+deref(attach.CommandID) || ar.Result["related_resource_ref"] != nil {
				t.Fatal("attach PendingResult")
			}
			independentC09Exact(t, before, attached, map[string]bool{"client_sessions": true, "outbox": true, "idempotency": true, "client_command_identities": true})
			if len(before["client_sessions"]) != len(attached["client_sessions"]) {
				t.Fatal("attach changed Session count")
			}
			for i, old := range before["client_sessions"] {
				want := Object{}
				for k, v := range old {
					want[k] = v
				}
				if old["id"] == sid {
					want["writer_epoch"] = epoch + 1
					want["revision"] = rev + 2
					want["event_watermark"] = watermark + 1
					want["lease_expires_at"] = actualAttach["lease_expires_at"]
					want["updated_at"] = actualAttach["updated_at"]
				}
				if !reflect.DeepEqual(want, attached["client_sessions"][i]) {
					t.Fatal("unexpected actual attach Session field mutation")
				}
			}
			newAttachEvent := independentC09Append(t, before["outbox"], attached["outbox"], 1)[0]
			event, e := Decode([]byte(Str(newAttachEvent, "body")))
			if e != nil {
				t.Fatal(e)
			}
			if event["kind"] != "CLIENT_HANDOFF" || event["command_id"] != deref(attach.CommandID) || event["session_id"] != sid || event["protocol_version"] != ProtocolV2 || event["core_build_id"] != clientService.Host.CoreBuildID || newAttachEvent["project"] != project {
				t.Fatal("actual handoff event identity")
			}
			eventSequence, e := Num(event, "sequence")
			if e != nil || eventSequence != returnedSequence {
				t.Fatal("handoff event sequence")
			}
			decodedEvent, e := DecodeEvent([]byte(Str(newAttachEvent, "body")))
			if e != nil {
				t.Fatal(e)
			}
			if e = ValidateEventPayload(doc, decodedEvent); e != nil {
				t.Fatal(e)
			}
			handoff := independentC09Object(t, event, "payload")
			writer := independentC09Object(t, handoff, "writer")
			previousEpoch, e := Num(handoff, "previous_epoch")
			if e != nil {
				t.Fatal(e)
			}
			newEpoch, e := Num(writer, "epoch")
			if e != nil {
				t.Fatal(e)
			}
			if handoff["previous_client_id"] != client || handoff["target_client_id"] != client || previousEpoch != epoch || writer["client_id"] != client || newEpoch != epoch+1 || handoff["effective_at"] != ar.Result["accepted_at"] || writer["expires_at"] != actualAttach["lease_expires_at"] {
				t.Fatal("actual handoff ownership facts")
			}
			lease, e := time.Parse(time.RFC3339Nano, Str(writer, "expires_at"))
			if e != nil || !lease.Equal(accepted.Add(clientService.Host.LeaseTTL)) {
				t.Fatal("actual handoff configured TTL")
			}
			attachJournal := independentC09Append(t, before["idempotency"], attached["idempotency"], 1)[0]
			attachIdentity := independentC09Append(t, before["client_command_identities"], attached["client_command_identities"], 1)[0]
			if attachJournal["key"] != deref(attach.CommandID) || attachIdentity["command_id"] != deref(attach.CommandID) || attachJournal["principal"] != principal || attachIdentity["principal"] != principal || attachJournal["project"] != project || attachIdentity["project"] != project || attachJournal["operation"] != "v2:session.attach" || attachIdentity["operation"] != "v2:session.attach" || attachIdentity["method"] != "session.attach" || attachJournal["request_hash"] != attachIdentity["request_hash"] || Str(attachJournal, "body") != string(Bytes(ar)) {
				t.Fatal("attach sole original response/identity")
			}
			attachHeader, known, e := readClientCommandEnvelope(doc, Str(attachJournal, "headers"))
			if e != nil || !known || attachHeader.hash != attachJournal["request_hash"] || !bytes.Equal(attachHeader.env.originalRaw, Bytes(attach)) {
				t.Fatal("attach private original bytes/hash")
			}
			attachMetadataCalls := metadata.calls
			attachReplay, isAttachReplay := independentC09Command(t, db, clientService, principal, attach, dir, "03a.exact-attach-replay")
			afterAttachReplay := independentC09StateRead(t, db)
			independentC09Write(t, dir, "03b.post-attach-replay.fullrows.json", afterAttachReplay)
			if !isAttachReplay || deref(attachReplay.Status) != "ACKNOWLEDGED" || !bytes.Equal(Bytes(attachReplay), Bytes(ar)) || metadata.calls != attachMetadataCalls || !reflect.DeepEqual(attached, afterAttachReplay) {
				t.Fatal("attach replay changed ACK/state/metadata")
			}
			tx, e := db.Begin()
			if e != nil {
				t.Fatal(e)
			}
			var injection Object
			e = func() error {
				defer tx.Rollback()
				creator, e := clientSessionCreationPrincipal(context.Background(), tx, project, sid)
				if e != nil || creator != principal {
					return fmt.Errorf("original creator prerequisite %s %v", creator, e)
				}
				originalTasks, e := clientService.originalSessionTasks(context.Background(), tx, principal, project, sid)
				if e != nil {
					return e
				}
				task, e := load(tx, project, "Task", Str(sess, "task_id"))
				if e != nil {
					return e
				}
				found := false
				for _, old := range originalTasks {
					if old["id"] == task["id"] {
						found = true
					}
				}
				if !found {
					return fmt.Errorf("original immutable task membership unavailable")
				}
				if !clientTurnSettled(tx, project, sid, task) {
					return fmt.Errorf("current original head not settled")
				}
				run, e := load(tx, project, "Run", Str(task, "active_run_id"))
				if e != nil {
					return e
				}
				injection = Object{"mode": "INJECTED_GUARD_CONTROL_ONLY", "case": name, "original_task_id": task["id"], "original_run_id": run["id"], "current_head_settled": true, "owner": owner, "principal": principal, "session_id": sid, "project": project}
				if strings.HasPrefix(name, "permission-") {
					p, e := clientPrincipal(context.Background(), tx, principal, project, true)
					if e != nil {
						return e
					}
					request, e := service.createResourceRequest(tx, p, project, Object{"category": "PERMISSION", "account_ref": nil, "reason_code": "SYNTHETIC_C09_" + ID(), "summary": "Explicit synthetic residual permission guard input; no tool action", "blocked_task_ids": []any{task["id"]}, "continuable_task_ids": Empty(), "completed_artifact_refs": Empty(), "requested_capability": "SYNTHETIC_C09_NO_ACTION", "estimated_cost": nil, "cost_known": false, "resume_checkpoint_ref": nil})
					if e != nil {
						return e
					}
					state := "OPEN"
					if name == "permission-resolved-positive" {
						state = "RESOLVED"
					} else if name == "permission-acknowledged" {
						state = "ACKNOWLEDGED"
					}
					if state != "OPEN" {
						request["status"] = state
						if state == "RESOLVED" {
							request["resolved_by"] = principal
						}
						if e = bump(request); e != nil {
							return e
						}
						if e = service.put(tx, "ResourceRequest", request); e != nil {
							return e
						}
					}
					effect := Object{"state": "CONFIRMED", "synthetic_control": "C09_RESIDUAL_PERMISSION_NOT_REAL_LIFECYCLE", "permission": Object{"session_id": sid, "request_id": request["id"], "task_ref": Ref(task, "Task"), "principal_id": principal}}
					if e = effectAppend(tx, project, Str(run, "id"), "SYNTHETIC_C09_"+ID(), effect); e != nil {
						return e
					}
					injection["request"] = request
					injection["effect"] = effect
				} else {
					synthetic, e := Decode(Bytes(run))
					if e != nil {
						return e
					}
					synthetic["id"] = ID()
					synthetic["revision"] = int64(1)
					synthetic["created_at"] = Now()
					synthetic["updated_at"] = synthetic["created_at"]
					synthetic["external_run_id"] = nil
					synthetic["execution_report"] = "SYNTHETIC C09 nonhead Run; not executed"
					synthetic["status"] = "SETTLED"
					synthetic["children_stopped"] = true
					synthetic["queue_empty"] = true
					synthetic["runtime_settled_at"] = Now()
					synthetic["cancel_requested_at"] = nil
					synthetic["cancel_confirmed_at"] = nil
					if name == "older-run-running-hidden-by-later-settled-run" {
						synthetic["status"] = "RUNNING"
						synthetic["runtime_settled_at"] = nil
						synthetic["ended_at"] = nil
						synthetic["children_stopped"] = false
						synthetic["queue_empty"] = false
					}
					if e = service.put(tx, "Run", synthetic); e != nil {
						return e
					}
					var wm, revision, writer int64
					if e = tx.QueryRow(`SELECT event_watermark,revision,writer_epoch FROM client_sessions WHERE id=?`, sid).Scan(&wm, &revision, &writer); e != nil {
						return e
					}
					event := &SessionEvent{ProtocolVersion: strptr(ProtocolV2), CoreBuildID: strptr(clientService.Host.CoreBuildID), EventID: strptr(ID()), SessionID: &sid, Sequence: revPtr(wm + 1), RunID: strptr(Str(synthetic, "id")), Kind: strptr("RUN_STATE"), Payload: Bytes(Object{"run_id": synthetic["id"], "status": synthetic["status"], "revision": synthetic["revision"], "cancel_requested_at": synthetic["cancel_requested_at"], "cancel_confirmed_at": synthetic["cancel_confirmed_at"], "settled_at": synthetic["runtime_settled_at"], "children_stopped": synthetic["children_stopped"], "queue_empty": synthetic["queue_empty"]})}
					if e = AppendSessionEvent(context.Background(), tx, doc, project, event, writer, revision); e != nil {
						return e
					}
					if name == "older-run-unknown-hidden-by-later-settled-run" {
						effect := Object{"state": "UNKNOWN", "synthetic_control": "C09_NONHEAD_NOT_PROVIDER_DISPATCH"}
						if e = effectAppend(tx, project, Str(synthetic, "id"), "SYNTHETIC_C09_"+ID(), effect); e != nil {
							return e
						}
						injection["effect"] = effect
					}
					injection["synthetic_run"] = synthetic
					injection["event"] = event
				}
				if !clientTurnSettled(tx, project, sid, task) {
					return fmt.Errorf("injection changed current original head settlement")
				}
				return tx.Commit()
			}()
			if e != nil {
				t.Fatal(e)
			}
			independentC09Write(t, dir, "04.injection-spec.actual.json", injection)
			pre := independentC09StateRead(t, db)
			independentC09Write(t, dir, "05.pre-command.fullrows.json", pre)
			// Every original business object/history/effect and budget row is preserved
			// through the explicitly recorded injection; new rows are never substitutes.
			for _, table := range []string{"domain_objects", "domain_versions", "resource_effects"} {
				preserved := map[string]int{}
				for _, row := range pre[table] {
					preserved[string(Bytes(row))]++
				}
				for _, row := range attached[table] {
					key := string(Bytes(row))
					if preserved[key] < 1 {
						if table == "domain_objects" && row["kind"] == "ProjectState" && strings.HasPrefix(name, "permission-") {
							var current Object
							for _, v := range pre[table] {
								if v["kind"] == row["kind"] && v["id"] == row["id"] && v["project"] == row["project"] {
									current = v
								}
							}
							if current == nil {
								t.Fatal("original project state missing")
							}
							oldBody, e := Decode([]byte(Str(row, "body")))
							if e != nil {
								t.Fatal(e)
							}
							newBody, e := Decode([]byte(Str(current, "body")))
							if e != nil {
								t.Fatal(e)
							}
							originalSequence, e := Num(oldBody, "event_sequence")
							if e != nil {
								t.Fatal(e)
							}
							maxSequence := originalSequence
							for _, v := range attached["outbox"] {
								if v["project"] == project {
									n, e := Num(v, "sequence")
									if e != nil {
										t.Fatal(e)
									}
									if n > maxSequence {
										maxSequence = n
									}
								}
							}
							oldIDs := map[string]bool{}
							for _, v := range attached["domain_objects"] {
								oldIDs[Str(v, "kind")+"/"+Str(v, "id")] = true
							}
							events := []Object{}
							for _, v := range pre["domain_objects"] {
								if v["kind"] == "EventEnvelope" && !oldIDs["EventEnvelope/"+Str(v, "id")] {
									body, e := Decode([]byte(Str(v, "body")))
									if e != nil {
										t.Fatal(e)
									}
									if body["event_type"] != "NOTIFICATION_CHANGED" || body["actor_id"] != principal {
										t.Fatal("unrelated injected producer event")
									}
									events = append(events, body)
								}
							}
							if len(events) == 0 {
								t.Fatal("project state changed without notification producer events")
							}
							sort.Slice(events, func(i, j int) bool {
								a, _ := Num(events[i], "sequence")
								b, _ := Num(events[j], "sequence")
								return a < b
							})
							oldRevision, e := Num(oldBody, "revision")
							if e != nil {
								t.Fatal(e)
							}
							for i, event := range events {
								sequence, e := Num(event, "sequence")
								if e != nil || sequence != maxSequence+int64(i)+1 {
									t.Fatal("notification event sequence")
								}
								agg := independentC09Object(t, event, "aggregate_ref")
								if agg["entity_type"] != "Notification" {
									t.Fatal("notification aggregate kind")
								}
								found := false
								for _, v := range pre["domain_objects"] {
									if v["kind"] == "Notification" && v["id"] == agg["id"] && !oldIDs["Notification/"+Str(v, "id")] {
										body, e := Decode([]byte(Str(v, "body")))
										if e != nil {
											t.Fatal(e)
										}
										if body["resource_request_id"] != independentC09Object(t, injection, "request")["id"] {
											t.Fatal("notification wrong request")
										}
										found = true
									}
								}
								if !found {
									t.Fatal("notification aggregate missing")
								}
								snapshots := 0
								for _, v := range pre["event_state_snapshots"] {
									if v["project"] == project && v["event_id"] == event["id"] {
										body, e := Decode([]byte(Str(v, "body")))
										if e != nil {
											t.Fatal(e)
										}
										n, e := Num(body, "revision")
										if e != nil || n != oldRevision+int64(i)+1 {
											t.Fatal("producer snapshot revision")
										}
										seq, e := Num(body, "event_sequence")
										if e != nil || seq != sequence {
											t.Fatal("producer snapshot sequence")
										}
										snapshots++
									}
								}
								if snapshots != 1 {
									t.Fatal("producer snapshot missing/extra")
								}
							}
							want, e := Decode(Bytes(oldBody))
							if e != nil {
								t.Fatal(e)
							}
							want["revision"] = oldRevision + int64(len(events))
							want["event_sequence"] = maxSequence + int64(len(events))
							want["updated_at"] = newBody["updated_at"]
							if _, e = time.Parse(time.RFC3339Nano, Str(want, "updated_at")); e != nil {
								t.Fatal(e)
							}
							if !bytes.Equal(Bytes(want), Bytes(newBody)) {
								t.Fatal("unexpected ProjectState field delta")
							}
							wantRow := Object{}
							for k, v := range row {
								wantRow[k] = v
							}
							wantRow["revision"] = oldRevision + int64(len(events))
							wantRow["body"] = current["body"]
							if !reflect.DeepEqual(wantRow, current) {
								t.Fatal("unexpected ProjectState SQL row delta")
							}
							continue
						}
						t.Fatalf("injection changed original %s row", table)
					}
					preserved[key]--
				}
			}
			for table, rows := range attached {
				if strings.Contains(table, "budget") || strings.Contains(table, "ledger") || table == "runtime_dispatches" {
					if !reflect.DeepEqual(rows, pre[table]) {
						t.Fatalf("injection changed original %s", table)
					}
				}
			}
			sess = independentC09Session(t, db, sid)
			rev, e = Num(sess, "revision")
			if e != nil {
				t.Fatal(e)
			}
			epoch, e = Num(sess, "writer_epoch")
			if e != nil {
				t.Fatal(e)
			}
			var head int64
			if e = db.QueryRow(`SELECT current_revision FROM host_model_config_heads WHERE owner_host_ref=? AND principal=?`, owner, principal).Scan(&head); e != nil {
				t.Fatal(e)
			}
			payload, e := Decode([]byte(Str(config[0], "canonical_config_json")))
			if e != nil {
				t.Fatal(e)
			}
			payload["config_revision"] = head + 1
			env := &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: &client, ProjectID: &project, SessionID: &sid, ExpectedRevision: &rev, WriterEpoch: &epoch, Method: strptr("host.configure"), Payload: Bytes(payload)}
			response, replayed := independentC09Command(t, db, clientService, principal, env, dir, "06.configure")
			post := independentC09StateRead(t, db)
			independentC09Write(t, dir, "07.post-command.fullrows.json", post)
			positive := name == "permission-resolved-positive" || name == "all-runs-settled-positive"
			if replayed {
				t.Fatal("first command replayed")
			}
			if positive {
				if deref(response.Status) != "COMPLETED" {
					t.Fatalf("positive refused %s", Bytes(response))
				}
			} else {
				expected := "session permission remains unresolved"
				if strings.HasPrefix(name, "older-") {
					expected = "earlier session run is not settled"
				}
				if deref(response.Status) != "REJECTED" || deref(response.ErrorCode) != "SESSION_BUSY" || response.Error == nil || response.Error.Message != expected {
					t.Fatalf("wrong causal refusal %s want %s", Bytes(response), expected)
				}
			}
			allowed := map[string]bool{"idempotency": true, "client_command_identities": true}
			if positive {
				allowed["host_model_configurations"] = true
				allowed["host_model_config_heads"] = true
				allowed["client_sessions"] = true
			}
			independentC09Exact(t, pre, post, allowed)
			newJournal := independentC09Append(t, pre["idempotency"], post["idempotency"], 1)[0]
			identity := independentC09Append(t, pre["client_command_identities"], post["client_command_identities"], 1)[0]
			if newJournal["key"] != *env.CommandID || identity["command_id"] != *env.CommandID || newJournal["request_hash"] != identity["request_hash"] || newJournal["principal"] != principal || identity["principal"] != principal {
				t.Fatal("original command identity mismatch")
			}
			header, known, e := readClientCommandEnvelope(doc, Str(newJournal, "headers"))
			if e != nil || !known || header.hash != newJournal["request_hash"] || !bytes.Equal(header.env.originalRaw, Bytes(env)) {
				t.Fatalf("original raw header mismatch %v", e)
			}
			if positive {
				if response.Revision == nil || *response.Revision != rev+1 || deref(response.SessionID) != sid || deref(response.CommandID) != deref(env.CommandID) {
					t.Fatal("typed scoped response identity/revision")
				}
				fresh := independentC09Append(t, pre["host_model_configurations"], post["host_model_configurations"], 1)[0]
				if fresh["command_id"] != *env.CommandID || fresh["model_config_ref"] != response.Result["model_config_ref"] || fresh["config_revision"] != head+1 {
					t.Fatal("next immutable config mismatch")
				}
				oldSession := pre["client_sessions"]
				newSession := post["client_sessions"]
				if len(oldSession) != len(newSession) {
					t.Fatal("session count")
				}
				for i, old := range oldSession {
					want := Object{}
					for k, v := range old {
						want[k] = v
					}
					if old["id"] == sid {
						want["model_config_ref"] = fresh["model_config_ref"]
						want["revision"] = rev + 1
						want["updated_at"] = newSession[i]["updated_at"]
						if _, e = time.Parse(time.RFC3339Nano, Str(want, "updated_at")); e != nil {
							t.Fatal(e)
						}
					}
					if !reflect.DeepEqual(want, newSession[i]) {
						t.Fatal("unexpected session field mutation")
					}
				}
				if len(pre["host_model_config_heads"]) != len(post["host_model_config_heads"]) {
					t.Fatal("head count")
				}
				for i, old := range pre["host_model_config_heads"] {
					want := Object{}
					for k, v := range old {
						want[k] = v
					}
					if old["owner_host_ref"] == owner && old["principal"] == principal {
						want["current_revision"] = head + 1
						want["default_model_config_ref"] = fresh["model_config_ref"]
					}
					if !reflect.DeepEqual(want, post["host_model_config_heads"][i]) {
						t.Fatal("head delta")
					}
				}
			}
			calls := metadata.calls
			again, isReplay := independentC09Command(t, db, clientService, principal, env, dir, "08.replay")
			replayState := independentC09StateRead(t, db)
			independentC09Write(t, dir, "09.post-replay.fullrows.json", replayState)
			if !isReplay || !bytes.Equal(Bytes(again), Bytes(response)) || metadata.calls != calls || !reflect.DeepEqual(post, replayState) {
				t.Fatal("replay repeated mutation or metadata")
			}
			independentC09Write(t, dir, "result.json", Object{"passed": true, "case": name, "positive": positive, "typed_cause": response.Error, "metadata_calls": metadata.calls, "models": 0, "HTTP": 0, "Node": 0, "worker": 0, "formal_increment": 0})
		}) {
			break
		}
	}
}
