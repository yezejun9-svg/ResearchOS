package domain

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"strings"
	"testing"
)

func identityRefusal(t *testing.T, tx *sql.Tx, doc *SchemaDoc, raw []byte, env *Envelope) {
	t.Helper()
	if _, e := reserveClientCommandIdentity(context.Background(), tx, doc, configurationFixturePrincipal, raw, env); e != nil {
		t.Fatal(e)
	}
	response := NewTypedRejection(env, "MODEL_UNAVAILABLE", "fixture storage refusal")
	if e := configurationReceipt(tx, configurationFixturePrincipal, env, response); e != nil {
		t.Fatal(e)
	}
	if _, e := lookupClientCommandIdentity(context.Background(), tx, doc, configurationFixturePrincipal, raw, env); e != nil {
		t.Fatal(e)
	}
}

func TestClientCommandIdentityRetainedRawAndResponse(t *testing.T) {
	doc := configurationSchema(t)
	raw, env := configurationEnvelope(t, doc, "identity", 1)
	if _, e := validateClientIdentityRequest(doc, raw, env); e != nil {
		t.Fatal(e)
	}
	for _, mutation := range []string{"field", "retained", "missing", "nil_schema"} {
		t.Run(mutation, func(t *testing.T) {
			copyEnv, e := decodeClientIdentityEnvelope(doc, raw)
			if e != nil {
				t.Fatal(e)
			}
			d := doc
			switch mutation {
			case "field":
				copyEnv.ClientID = strptr("changed")
			case "retained":
				copyEnv.extra["client_id"] = Bytes("changed")
			case "missing":
				copyEnv.extra = nil
			case "nil_schema":
				d = nil
			}
			if _, e = validateClientIdentityRequest(d, raw, copyEnv); e == nil {
				t.Fatal("forged envelope accepted")
			}
		})
	}
	req, e := validateClientIdentityRequest(doc, raw, env)
	if e != nil {
		t.Fatal(e)
	}
	response := NewTypedRejection(env, "MODEL_UNAVAILABLE", "fixture")
	if _, e = decodeClientIdentityResponse(doc, req, Bytes(response)); e != nil {
		t.Fatal(e)
	}
	for _, field := range []string{"protocol_version", "command_id", "method", "session_id", "result"} {
		t.Run("response_"+field, func(t *testing.T) {
			var value Object
			if e := json.Unmarshal(Bytes(response), &value); e != nil {
				t.Fatal(e)
			}
			value[field] = "wrong"
			if _, e = decodeClientIdentityResponse(doc, req, Bytes(value)); e == nil {
				t.Fatal("foreign/corrupt response accepted")
			}
		})
	}
	if _, e = decodeClientIdentityResponse(nil, req, Bytes(response)); e == nil {
		t.Fatal("nil schema")
	}
	duplicate := strings.Replace(string(raw), `"client_id":"foundation-fixture"`, `"client_id":"foundation-fixture","client_id":"other"`, 1)
	if _, e = decodeClientIdentityEnvelope(doc, []byte(duplicate)); e == nil {
		t.Fatal("duplicate keys")
	}
}

func TestClientCommandIdentityGlobalReplayAndLegacyAmbiguity(t *testing.T) {
	db, _ := configurationDB(t, 23, true)
	doc := configurationSchema(t)
	raw, env := configurationEnvelope(t, doc, "global-identity", 1)
	tx, e := db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	identityRefusal(t, tx, doc, raw, env)
	if e = tx.Commit(); e != nil {
		t.Fatal(e)
	}
	for _, field := range []string{"project_id", "method", "session_id", "writer_epoch", "payload"} {
		t.Run(field, func(t *testing.T) {
			var changed Object
			if e := json.Unmarshal(raw, &changed); e != nil {
				t.Fatal(e)
			}
			switch field {
			case "method":
				changed[field] = "host.status"
				changed["payload"] = Object{}
			case "session_id":
				changed[field] = "other"
				changed["project_id"] = "other-project"
				changed["expected_revision"] = 1
				changed["writer_epoch"] = 1
			case "writer_epoch":
				changed[field] = 1
			case "payload":
				changed[field].(map[string]any)["model_id"] = "other"
			default:
				changed[field] = "other"
			}
			newRaw := Bytes(changed)
			newEnv, e := decodeClientIdentityEnvelope(doc, newRaw)
			if e != nil {
				t.Fatal(e)
			}
			tx, e := db.Begin()
			if e != nil {
				t.Fatal(e)
			}
			defer tx.Rollback()
			if _, e = lookupClientCommandIdentity(context.Background(), tx, doc, configurationFixturePrincipal, newRaw, newEnv); !errors.Is(e, ErrIdemConflict) {
				t.Fatalf("expected global conflict: %v", e)
			}
		})
	}
	t.Run("exact_replay", func(t *testing.T) {
		tx, e := db.Begin()
		if e != nil {
			t.Fatal(e)
		}
		defer tx.Rollback()
		response, e := reserveClientCommandIdentity(context.Background(), tx, doc, configurationFixturePrincipal, raw, env)
		if e != nil || deref(response.Status) != "REJECTED" {
			t.Fatalf("%v", e)
		}
		if _, e = lookupClientCommandIdentity(context.Background(), tx, doc, "other-principal", raw, env); e != nil {
			t.Fatal(e)
		}
	})
	for _, ambiguous := range []bool{false, true} {
		t.Run(map[bool]string{false: "legacy_link", true: "legacy_ambiguous"}[ambiguous], func(t *testing.T) {
			db, _ := configurationDB(t, 23, true)
			tx, e := db.Begin()
			if e != nil {
				t.Fatal(e)
			}
			defer tx.Rollback()
			response := NewTypedRejection(env, "MODEL_UNAVAILABLE", "legacy-original")
			if e = configurationReceipt(tx, configurationFixturePrincipal, env, response); e != nil {
				t.Fatal(e)
			}
			if _, e = tx.Exec(`INSERT INTO idempotency SELECT principal,project,'v1:host.configure',key,request_hash,status,body,headers,created_at FROM idempotency`); e != nil {
				t.Fatal(e)
			}
			if ambiguous {
				if _, e = tx.Exec(`INSERT INTO idempotency SELECT principal,'other-project',operation,key,request_hash,status,body,headers,created_at FROM idempotency WHERE operation='v2:host.configure'`); e != nil {
					t.Fatal(e)
				}
			}
			found, e := reserveClientCommandIdentity(context.Background(), tx, doc, configurationFixturePrincipal, raw, env)
			if ambiguous {
				if !errors.Is(e, ErrIdemConflict) {
					t.Fatalf("%v", e)
				}
				return
			}
			if e != nil || string(Bytes(found)) != string(Bytes(response)) {
				t.Fatalf("legacy changed %v", e)
			}
			if e = tx.Commit(); e != nil {
				t.Fatal(e)
			}
			if configurationCount(t, db, "client_command_identities") != 1 || configurationCount(t, db, "idempotency") != 2 {
				t.Fatal("wrong lazy link cardinality")
			}
		})
	}
}

func TestClientCommandIdentityDeferredReceiptAndSavepoint(t *testing.T) {
	for _, kind := range []string{"absent", "wrong_hash", "refusal_after_business_rollback"} {
		t.Run(kind, func(t *testing.T) {
			db, _ := configurationDB(t, 23, true)
			doc := configurationSchema(t)
			raw, env := configurationEnvelope(t, doc, "deferred", 1)
			tx, e := db.Begin()
			if e != nil {
				t.Fatal(e)
			}
			defer tx.Rollback()
			if _, e = reserveClientCommandIdentity(context.Background(), tx, doc, configurationFixturePrincipal, raw, env); e != nil {
				t.Fatal(e)
			}
			if kind == "refusal_after_business_rollback" {
				if _, e = tx.Exec("SAVEPOINT configure_business"); e != nil {
					t.Fatal(e)
				}
				if _, e = stageClientConfiguration(context.Background(), tx, doc, configurationFixtureOwner, configurationFixturePrincipal, raw, env); e != nil {
					t.Fatal(e)
				}
				if _, e = tx.Exec("ROLLBACK TO configure_business"); e != nil {
					t.Fatal(e)
				}
				if _, e = tx.Exec("RELEASE configure_business"); e != nil {
					t.Fatal(e)
				}
				if e = configurationReceipt(tx, configurationFixturePrincipal, env, NewTypedRejection(env, "MODEL_UNAVAILABLE", "fixture refusal")); e != nil {
					t.Fatal(e)
				}
				if e = tx.Commit(); e != nil {
					t.Fatal(e)
				}
				if configurationCount(t, db, "client_command_identities") != 1 || configurationCount(t, db, "idempotency") != 1 || configurationCount(t, db, "host_model_configurations") != 0 {
					t.Fatal("savepoint authority mismatch")
				}
				return
			}
			if kind == "wrong_hash" {
				if _, e = tx.Exec(`INSERT INTO idempotency(principal,project,operation,key,request_hash,status,body,headers,created_at) VALUES(?,'','v2:host.configure',?,?,200,'{}','{}',?)`, configurationFixturePrincipal, deref(env.CommandID), "sha256:"+strings.Repeat("0", 64), Now()); e != nil {
					t.Fatal(e)
				}
			}
			if e = tx.Commit(); e == nil {
				t.Fatal("orphan committed")
			}
			tx.Rollback()
			if configurationCount(t, db, "client_command_identities") != 0 || configurationCount(t, db, "idempotency") != 0 {
				t.Fatal("failed commit leaked")
			}
		})
	}
}

// This records the actual inherited trigger contract rather than removing it to
// invent an ACK-finalization capability. Product finalization integration is a
// separately scoped open gate; identities never own a copied response.
func TestClientCommandIdentityOriginalJournalTriggerEvidence(t *testing.T) {
	for _, version := range []int{22, 23} {
		t.Run(map[int]string{22: "baseline22", 23: "candidate23"}[version], func(t *testing.T) {
			db, _ := configurationDB(t, version, true)
			doc := configurationSchema(t)
			raw, env := configurationEnvelope(t, doc, "original-journal", 1)
			tx, e := db.Begin()
			if e != nil {
				t.Fatal(e)
			}
			defer tx.Rollback()
			if e = configurationReceipt(tx, configurationFixturePrincipal, env, NewTypedRejection(env, "MODEL_UNAVAILABLE", "original")); e != nil {
				t.Fatal(e)
			}
			var trigger string
			if e = tx.QueryRow("SELECT sql FROM sqlite_master WHERE type='trigger' AND name='idempotency_immutable'").Scan(&trigger); e != nil {
				t.Fatal(e)
			}
			t.Logf("installed_schema=%d trigger=%s", version, trigger)
			_, e = tx.Exec("UPDATE idempotency SET body=body WHERE key=?", deref(env.CommandID))
			if e == nil || !strings.Contains(e.Error(), "immutable replay") {
				t.Fatalf("unexpected installed original journal protection %v", e)
			}
			t.Logf("actual_update_error=%v", e)
			if version == 23 {
				response, e := reserveClientCommandIdentity(context.Background(), tx, doc, configurationFixturePrincipal, raw, env)
				if e != nil || response.Error.Message != "original" {
					t.Fatalf("original row changed: %v", e)
				}
			}
		})
	}
}
