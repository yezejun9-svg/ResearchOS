package domain

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"testing"

	"researchos.local/research-os/internal/store"
)

const configurationFixtureOwner = "host-012345abcdef"
const configurationFixturePrincipal = "configuration-fixture-owner"

func configurationSchema(t *testing.T) *SchemaDoc {
	t.Helper()
	raw, e := os.ReadFile("../api/contracts/client.protocol.schema.json")
	if e != nil {
		t.Fatal(e)
	}
	external, e := os.ReadFile("../api/contracts/domain.schema.json")
	if e != nil {
		t.Fatal(e)
	}
	doc, e := LoadSchemaWithExternals(raw, map[string][]byte{"domain.schema.json": external})
	if e != nil {
		t.Fatal(e)
	}
	return doc
}

// A private, credential-free SQLite fixture. It never starts a host or provider.
func configurationDB(t *testing.T, version int, additive bool) (*sql.DB, string) {
	t.Helper()
	path := filepath.Join(t.TempDir(), "fixture.sqlite")
	db, e := store.Open(path)
	if e != nil {
		t.Fatal(e)
	}
	t.Cleanup(func() { db.Close() })
	if e = store.Bootstrap(context.Background(), db, "../../migrations/sqlite/0001_bootstrap.sql"); e != nil {
		t.Fatal(e)
	}
	tx, e := db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	defer tx.Rollback()
	files, e := filepath.Glob("../../migrations/sqlite/[0-9][0-9][0-9][0-9]_*.sql")
	if e != nil {
		t.Fatal(e)
	}
	for _, p := range files {
		var n int
		if _, e = fmt.Sscanf(filepath.Base(p), "%04d_", &n); e != nil {
			t.Fatal(e)
		}
		if n < 2 || n > version {
			continue
		}
		b, e := os.ReadFile(p)
		if e != nil {
			t.Fatal(e)
		}
		if _, e = tx.Exec(string(b)); e != nil {
			t.Fatalf("%s: %v", p, e)
		}
		if _, e = tx.Exec("INSERT INTO schema_migrations(version) VALUES(?)", n); e != nil {
			t.Fatal(e)
		}
	}
	if additive {
		b, e := os.ReadFile("../../migrations/sqlite/next_v24_sessions.sql")
		if e != nil {
			t.Fatal(e)
		}
		if _, e = tx.Exec(string(b)); e != nil {
			t.Fatal(e)
		}
		if e = installClientSessionFence(context.Background(), tx, false); e != nil {
			t.Fatal(e)
		}
	}
	if version >= 2 {
		if _, e = tx.Exec(`INSERT INTO auth_principals(id,roles) VALUES(?, '["OWNER"]')`, configurationFixturePrincipal); e != nil {
			t.Fatal(e)
		}
	}
	if e = tx.Commit(); e != nil {
		t.Fatal(e)
	}
	return db, path
}

func configurationEnvelope(t *testing.T, doc *SchemaDoc, id string, revision int64) ([]byte, *Envelope) {
	t.Helper()
	raw := Bytes(Object{"protocol_version": ProtocolV2, "command_id": id, "client_id": "foundation-fixture", "project_id": nil, "session_id": nil, "expected_revision": nil, "writer_epoch": nil, "method": "host.configure", "payload": Object{"config_revision": revision, "provider_id": "fixture-provider", "base_url": "https://fixture.invalid/v1", "model_id": "fixture-model", "credential_ref": nil}})
	env, e := decodeClientIdentityEnvelope(doc, raw)
	if e != nil {
		t.Fatal(e)
	}
	return raw, env
}

func TestLocalConfigurationRequiresNoCredential(t *testing.T) {
	doc := configurationSchema(t)
	for _, tc := range []struct {
		base       string
		credential any
		valid      bool
	}{
		{"http://127.0.0.1:11434/v1", nil, true},
		{"http://[::1]:11434/v1", nil, true},
		{"http://127.0.0.1:11434/v1", "cred-fixture-api_key-1234567890-12345678-12345678", false},
		{"http://localhost:11434/v1", nil, false},
		{"http://192.168.1.1:11434/v1", nil, false},
		{"https://fixture.invalid/v1", "cred-fixture-api_key-1234567890-12345678-12345678", true},
	} {
		payload := Object{"config_revision": 1, "provider_id": "fixture-provider", "base_url": tc.base, "model_id": "fixture-model", "credential_ref": tc.credential}
		_, _, err := parseClientConfiguration(doc, Bytes(payload))
		if (err == nil) != tc.valid {
			t.Errorf("base=%q credential=%v valid=%t error=%v", tc.base, tc.credential != nil, tc.valid, err)
		}
	}
}

func configurationReceipt(tx *sql.Tx, principal string, env *Envelope, response *Response) error {
	h, e := env.ContentHash()
	if e != nil {
		return e
	}
	headers := "{}"
	var tables int
	if e = tx.QueryRow(`SELECT count(*) FROM sqlite_schema WHERE type='table' AND name='client_command_identities'`).Scan(&tables); e != nil {
		return e
	}
	if tables == 0 {
		var version int
		if e = tx.QueryRow(`SELECT max(version) FROM schema_migrations`).Scan(&version); e != nil {
			return e
		}
		if version != 22 {
			return fmt.Errorf("missing command identity table outside original schema22")
		}
	} else {
		var identities int
		if e = tx.QueryRow(`SELECT count(*) FROM client_command_identities WHERE principal=? AND command_id=?`, principal, deref(env.CommandID)).Scan(&identities); e != nil {
			return e
		}
		if identities != 0 {
			doc, err := backupConfigurationSchema()
			if err != nil {
				return err
			}
			headers, e = writeClientCommandEnvelope(doc, env)
			if e != nil {
				return e
			}
		}
	}
	_, e = tx.Exec(`INSERT INTO idempotency(principal,project,operation,key,request_hash,status,body,headers,created_at) VALUES(?,?,?,?,?,200,?,?,?)`, principal, deref(env.ProjectID), "v2:"+deref(env.Method), deref(env.CommandID), h, Bytes(response), headers, Now())
	return e
}

func configurationStage(tx *sql.Tx, doc *SchemaDoc, raw []byte, env *Envelope) (clientConfigurationRecord, error) {
	ctx := context.Background()
	var zero clientConfigurationRecord
	replay, e := reserveClientCommandIdentity(ctx, tx, doc, configurationFixturePrincipal, raw, env)
	if e != nil {
		return zero, e
	}
	if replay != nil {
		return zero, fmt.Errorf("fixture expected new command")
	}
	record, e := stageClientConfiguration(ctx, tx, doc, configurationFixtureOwner, configurationFixturePrincipal, raw, env)
	if e != nil {
		return zero, e
	}
	response := &Response{ProtocolVersion: strptr(ProtocolV2), CommandID: env.CommandID, Method: env.Method, Status: strptr("COMPLETED"), Result: clientConfigurationProjection(record)}
	if e = configurationReceipt(tx, configurationFixturePrincipal, env, response); e != nil {
		return zero, e
	}
	return readClientConfiguration(ctx, tx, doc, configurationFixtureOwner, configurationFixturePrincipal, record.Ref)
}

func configurationCommit(t *testing.T, db *sql.DB, doc *SchemaDoc, id string, revision int64) clientConfigurationRecord {
	t.Helper()
	raw, env := configurationEnvelope(t, doc, id, revision)
	tx, e := db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	defer tx.Rollback()
	record, e := configurationStage(tx, doc, raw, env)
	if e != nil {
		t.Fatal(e)
	}
	if e = tx.Commit(); e != nil {
		t.Fatal(e)
	}
	return record
}

func configurationCount(t *testing.T, db *sql.DB, table string) int {
	t.Helper()
	var n int
	if e := db.QueryRow("SELECT count(*) FROM " + table).Scan(&n); e != nil {
		t.Fatal(e)
	}
	return n
}

func configurationOldRows(t *testing.T, db *sql.DB) string {
	t.Helper()
	rows, e := db.Query(`SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT IN ('client_command_identities','host_model_configurations','host_model_config_heads') ORDER BY name`)
	if e != nil {
		t.Fatal(e)
	}
	names := []string{}
	for rows.Next() {
		var n string
		if e = rows.Scan(&n); e != nil {
			t.Fatal(e)
		}
		names = append(names, n)
	}
	if e = rows.Err(); e != nil {
		t.Fatal(e)
	}
	rows.Close()
	snapshot := map[string][]string{}
	for _, name := range names {
		query := `SELECT * FROM "` + strings.ReplaceAll(name, `"`, `""`) + `"`
		if name == "schema_migrations" {
			query += " WHERE version<=22"
		}
		r, e := db.Query(query)
		if e != nil {
			t.Fatal(e)
		}
		columns, e := r.Columns()
		if e != nil {
			t.Fatal(e)
		}
		list := []string{}
		for r.Next() {
			values := make([]any, len(columns))
			targets := make([]any, len(columns))
			for i := range values {
				targets[i] = &values[i]
			}
			if e = r.Scan(targets...); e != nil {
				t.Fatal(e)
			}
			list = append(list, string(Bytes(values)))
		}
		if e = r.Err(); e != nil {
			t.Fatal(e)
		}
		r.Close()
		sort.Strings(list)
		snapshot[name] = list
	}
	return string(Bytes(snapshot))
}

func TestClientConfigurationFreshAndNumberedMigration(t *testing.T) {
	for _, additive := range []bool{false, true} {
		t.Run(fmt.Sprintf("numbered22_additive_%t", additive), func(t *testing.T) {
			db, _ := configurationDB(t, 22, additive)
			if _, e := db.Exec(`INSERT INTO domain_objects(project,kind,id,revision,body,immutable) VALUES('fixture','Fixture','old-row',1,'{"preserved":"旧数据"}',0)`); e != nil {
				t.Fatal(e)
			}
			if _, e := db.Exec(`INSERT INTO idempotency(principal,project,operation,key,request_hash,status,body,headers,created_at) VALUES(?,'old','v1:fixture','old-key','old-hash',200,'old-raw','{}','old-time')`, configurationFixturePrincipal); e != nil {
				t.Fatal(e)
			}
			old := configurationOldRows(t, db)
			tx, e := db.Begin()
			if e != nil {
				t.Fatal(e)
			}
			defer tx.Rollback()
			b, e := os.ReadFile("../../migrations/sqlite/0023_host_model_configuration.sql")
			if e != nil {
				t.Fatal(e)
			}
			if _, e = tx.Exec(string(b)); e != nil {
				t.Fatal(e)
			}
			if _, e = tx.Exec("INSERT INTO schema_migrations(version) VALUES(23)"); e != nil {
				t.Fatal(e)
			}
			if e = tx.Commit(); e != nil {
				t.Fatal(e)
			}
			for _, table := range []string{"client_command_identities", "host_model_configurations", "host_model_config_heads"} {
				if configurationCount(t, db, table) != 0 {
					t.Fatal(table)
				}
			}
			if configurationOldRows(t, db) != old {
				t.Fatal("existing table rows changed")
			}
			var sessions int
			if e = db.QueryRow("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='client_sessions'").Scan(&sessions); e != nil {
				t.Fatal(e)
			}
			if (sessions == 1) != additive {
				t.Fatal("numbered migration installed additive schema")
			}
		})
	}
	t.Run("actual_Service_New", func(t *testing.T) {
		db, _ := configurationDB(t, 1, false)
		if _, e := New(db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql"); e != nil {
			t.Fatal(e)
		}
		var version int
		if e := db.QueryRow("SELECT max(version) FROM schema_migrations").Scan(&version); e != nil || version != 23 {
			t.Fatalf("%d %v", version, e)
		}
		if configurationCount(t, db, "client_sessions") != 0 || configurationCount(t, db, "host_model_configurations") != 0 {
			t.Fatal("fresh state")
		}
	})
}

func TestClientConfigurationConstructorRollbackAndPrebackup(t *testing.T) {
	for _, missing := range []bool{true, false} {
		t.Run(fmt.Sprintf("missing_additive_%t", missing), func(t *testing.T) {
			db, _ := configurationDB(t, 22, false)
			dir := t.TempDir()
			files, e := filepath.Glob("../../migrations/sqlite/[0-9][0-9][0-9][0-9]_*.sql")
			if e != nil {
				t.Fatal(e)
			}
			for _, p := range files {
				b, e := os.ReadFile(p)
				if e != nil {
					t.Fatal(e)
				}
				if e = os.WriteFile(filepath.Join(dir, filepath.Base(p)), b, 0600); e != nil {
					t.Fatal(e)
				}
			}
			if !missing {
				if e = os.WriteFile(filepath.Join(dir, "next_v24_sessions.sql"), []byte("THIS IS INVALID SQL;"), 0600); e != nil {
					t.Fatal(e)
				}
			}
			if _, e = New(db, "../../spec/v2.0/contracts", filepath.Join(dir, "0002_domain.sql")); e == nil {
				t.Fatal("constructor accepted unavailable additive")
			}
			var count int
			if e = db.QueryRow("SELECT count(*) FROM sqlite_master WHERE name='host_model_configurations'").Scan(&count); e != nil || count != 0 {
				t.Fatalf("SQL23 leaked from failed transaction: %d %v", count, e)
			}
			if configurationCount(t, db, "schema_migrations") != 22 {
				t.Fatal("version advanced")
			}
		})
	}
	t.Run("populated22", func(t *testing.T) {
		db, _ := configurationDB(t, 22, true)
		if _, e := db.Exec(`INSERT INTO domain_objects(project,kind,id,revision,body,immutable) VALUES('fixture','Fixture','existing',1,'{}',0)`); e != nil {
			t.Fatal(e)
		}
		_, e := New(db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql")
		if e == nil || !strings.Contains(e.Error(), "MIGRATION_PREBACKUP_REQUIRED") {
			t.Fatalf("%v", e)
		}
		if configurationCount(t, db, "schema_migrations") != 22 {
			t.Fatal("unsafe migration")
		}
	})
}

func TestClientConfigurationHistoryReplayRestartAndIsolation(t *testing.T) {
	db, path := configurationDB(t, 23, true)
	doc := configurationSchema(t)
	first := configurationCommit(t, db, doc, "configure-first", 1)
	second := configurationCommit(t, db, doc, "configure-second", 2)
	for _, table := range []string{"domain_objects", "outbox", "runtime_dispatches", "client_command_queue", "client_sessions", "auth_credentials"} {
		if configurationCount(t, db, table) != 0 {
			t.Fatal("foundation created unrelated authority " + table)
		}
	}
	if first.Ref == second.Ref || first.Payload.Revision != 1 || second.Payload.Revision != 2 {
		t.Fatal("immutable revisions")
	}
	if e := db.Close(); e != nil {
		t.Fatal(e)
	}
	reopened, e := store.Open(path)
	if e != nil {
		t.Fatal(e)
	}
	defer reopened.Close()
	tx, e := reopened.Begin()
	if e != nil {
		t.Fatal(e)
	}
	defer tx.Rollback()
	head, e := readClientConfigurationHead(context.Background(), tx, doc, configurationFixtureOwner, configurationFixturePrincipal)
	if e != nil || head.Ref != second.Ref || head.Revision != 2 {
		t.Fatalf("%+v %v", head, e)
	}
	original, e := readClientConfiguration(context.Background(), tx, doc, configurationFixtureOwner, configurationFixturePrincipal, first.Ref)
	if e != nil || original.ConfigHash != first.ConfigHash {
		t.Fatalf("history %v", e)
	}
	raw, env := configurationEnvelope(t, doc, "configure-first", 1)
	response, e := lookupClientCommandIdentity(context.Background(), tx, doc, configurationFixturePrincipal, raw, env)
	if e != nil || response.Result["model_config_ref"] != first.Ref {
		t.Fatalf("replay after head changed: %v", e)
	}
	if _, e = readClientConfiguration(context.Background(), tx, doc, "host-ffffffffffff", configurationFixturePrincipal, first.Ref); e == nil {
		t.Fatal("foreign owner")
	}
	if _, e = readClientConfiguration(context.Background(), tx, nil, configurationFixtureOwner, configurationFixturePrincipal, first.Ref); e == nil {
		t.Fatal("nil schema")
	}
	if _, e = tx.Exec(`UPDATE host_model_configurations SET config_revision=3 WHERE model_config_ref=?`, first.Ref); e == nil {
		t.Fatal("configuration mutable")
	}
	if _, e = tx.Exec(`DELETE FROM host_model_configurations WHERE model_config_ref=?`, first.Ref); e == nil {
		t.Fatal("configuration deletable")
	}
	if _, e = tx.Exec(`UPDATE host_model_config_heads SET current_revision=4 WHERE owner_host_ref=?`, configurationFixtureOwner); e == nil {
		t.Fatal("head gap")
	}
	if _, e = tx.Exec(`DELETE FROM host_model_config_heads`); e == nil {
		t.Fatal("head delete")
	}
	if _, e = tx.Exec(`UPDATE client_command_identities SET method='host.status'`); e == nil {
		t.Fatal("identity mutable")
	}
	if _, e = tx.Exec(`DELETE FROM client_command_identities`); e == nil {
		t.Fatal("identity delete")
	}
	for _, table := range []string{"client_command_identities", "host_model_configurations", "host_model_config_heads"} {
		if _, e = tx.Exec("INSERT OR REPLACE INTO " + table + " SELECT * FROM " + table); e == nil {
			t.Fatal("replace bypassed immutable " + table)
		}
	}
}

func TestClientConfigurationCorruptReadFailsClosed(t *testing.T) {
	for _, mutation := range []string{"config_hash", "scope_hash", "created_at", "scope_client", "request_hash", "config_body", "missing_receipt"} {
		t.Run(mutation, func(t *testing.T) {
			db, _ := configurationDB(t, 23, true)
			doc := configurationSchema(t)
			record := configurationCommit(t, db, doc, "original", 1)
			tx, e := db.Begin()
			if e != nil {
				t.Fatal(e)
			}
			defer tx.Rollback()
			// Deliberately corrupt only a disposable transaction after recording a valid
			// immutable row. Rollback restores both the data and its trigger.
			if _, e = tx.Exec("DROP TRIGGER host_config_no_update"); e != nil {
				t.Fatal(e)
			}
			switch mutation {
			case "config_hash", "scope_hash", "request_hash":
				_, e = tx.Exec("UPDATE host_model_configurations SET "+mutation+"=? WHERE model_config_ref=?", "sha256:"+strings.Repeat("0", 64), record.Ref)
			case "created_at":
				_, e = tx.Exec("UPDATE host_model_configurations SET created_at='not-a-time'")
			case "scope_client":
				var scope Object
				if e = json.Unmarshal(record.ScopeJSON, &scope); e != nil {
					t.Fatal(e)
				}
				scope["client_id"] = "other-client"
				b, e2 := clientConfigurationScope(&Envelope{ClientID: strptr("other-client")})
				if e2 != nil {
					t.Fatal(e2)
				}
				_, e = tx.Exec("UPDATE host_model_configurations SET operation_scope_json=?,scope_hash=?", string(b), Digest(b))
			case "config_body":
				p := record.Payload
				p.Model = "different"
				_, b, e2 := parseClientConfiguration(doc, Bytes(p))
				if e2 != nil {
					t.Fatal(e2)
				}
				_, e = tx.Exec("UPDATE host_model_configurations SET canonical_config_json=?,config_hash=?", string(b), Digest(b))
			case "missing_receipt":
				_, e = tx.Exec("DELETE FROM idempotency")
			}
			if e != nil {
				t.Fatal(e)
			}
			if _, e = readClientConfiguration(context.Background(), tx, doc, configurationFixtureOwner, configurationFixturePrincipal, record.Ref); e == nil {
				t.Fatal("corrupt linked configuration accepted")
			}
		})
	}
}

func TestClientConfigurationFaultRollbackAndCAS(t *testing.T) {
	for _, fault := range []string{"identity", "configuration", "receipt", "semantic"} {
		t.Run(fault, func(t *testing.T) {
			db, _ := configurationDB(t, 23, true)
			doc := configurationSchema(t)
			raw, env := configurationEnvelope(t, doc, "fault", 1)
			tx, e := db.Begin()
			if e != nil {
				t.Fatal(e)
			}
			if _, e = reserveClientCommandIdentity(context.Background(), tx, doc, configurationFixturePrincipal, raw, env); e != nil {
				t.Fatal(e)
			}
			if fault != "identity" {
				r, e := stageClientConfiguration(context.Background(), tx, doc, configurationFixtureOwner, configurationFixturePrincipal, raw, env)
				if e != nil {
					t.Fatal(e)
				}
				if fault != "configuration" {
					response := &Response{ProtocolVersion: strptr(ProtocolV2), CommandID: env.CommandID, Method: env.Method, Status: strptr("COMPLETED"), Result: clientConfigurationProjection(r)}
					if fault == "semantic" {
						response.Result["model_id"] = "wrong"
					}
					if e = configurationReceipt(tx, configurationFixturePrincipal, env, response); e != nil {
						t.Fatal(e)
					}
					if fault == "semantic" {
						if _, e = readClientConfiguration(context.Background(), tx, doc, configurationFixtureOwner, configurationFixturePrincipal, r.Ref); e == nil {
							t.Fatal("mismatched original result")
						}
					}
				}
			}
			if e = tx.Rollback(); e != nil {
				t.Fatal(e)
			}
			for _, table := range []string{"client_command_identities", "host_model_configurations", "host_model_config_heads", "idempotency"} {
				if configurationCount(t, db, table) != 0 {
					t.Fatal("rollback leaked " + table)
				}
			}
		})
	}
	t.Run("stale_and_gap", func(t *testing.T) {
		db, _ := configurationDB(t, 23, true)
		doc := configurationSchema(t)
		configurationCommit(t, db, doc, "first", 1)
		for _, rev := range []int64{1, 3} {
			raw, env := configurationEnvelope(t, doc, fmt.Sprint("bad", rev), rev)
			tx, e := db.Begin()
			if e != nil {
				t.Fatal(e)
			}
			_, e = configurationStage(tx, doc, raw, env)
			if e == nil || !strings.Contains(e.Error(), "CONFIG_CONFLICT") {
				t.Fatalf("%v", e)
			}
			tx.Rollback()
		}
		if configurationCount(t, db, "host_model_configurations") != 1 || configurationCount(t, db, "client_command_identities") != 1 {
			t.Fatal("failed CAS leaked writes")
		}
	})
	t.Run("separate_connections", func(t *testing.T) {
		db, path := configurationDB(t, 23, true)
		other, e := store.Open(path)
		if e != nil {
			t.Fatal(e)
		}
		defer other.Close()
		doc := configurationSchema(t)
		raws := [][]byte{}
		envs := []*Envelope{}
		for i := 0; i < 2; i++ {
			raw, env := configurationEnvelope(t, doc, fmt.Sprintf("race-%d", i), 1)
			raws = append(raws, raw)
			envs = append(envs, env)
		}
		start := make(chan struct{})
		results := make(chan error, 2)
		var wg sync.WaitGroup
		for i, conn := range []*sql.DB{db, other} {
			wg.Add(1)
			go func(i int, conn *sql.DB) {
				defer wg.Done()
				<-start
				tx, e := conn.Begin()
				if e != nil {
					results <- e
					return
				}
				defer tx.Rollback()
				_, e = configurationStage(tx, doc, raws[i], envs[i])
				if e == nil {
					e = tx.Commit()
				}
				results <- e
			}(i, conn)
		}
		close(start)
		wg.Wait()
		close(results)
		wins := 0
		for e := range results {
			if e == nil {
				wins++
			} else if !strings.Contains(e.Error(), "CONFIG_CONFLICT") && !strings.Contains(e.Error(), "locked") && !strings.Contains(e.Error(), "BUSY") {
				t.Fatalf("unexpected race error %v", e)
			}
		}
		if wins != 1 || configurationCount(t, db, "host_model_configurations") != 1 || configurationCount(t, db, "client_command_identities") != 1 {
			t.Fatalf("race winners %d", wins)
		}
	})
}

func TestClientConfigurationStrictPayloadAndUnwiredSession(t *testing.T) {
	doc := configurationSchema(t)
	base := `{"config_revision":1,"provider_id":"fixture","base_url":"https://fixture.invalid/v1","model_id":"fixture","credential_ref":null}`
	for name, raw := range map[string]string{"duplicate": strings.Replace(base, `"config_revision":1`, `"config_revision":1,"config_revision":2`, 1), "unicode": strings.Replace(base, `"fixture"`, `"\ud800"`, 1), "overflow": strings.Replace(base, `"config_revision":1`, `"config_revision":9007199254740992`, 1), "fraction": strings.Replace(base, `"config_revision":1`, `"config_revision":1.5`, 1), "zero": strings.Replace(base, `"config_revision":1`, `"config_revision":0`, 1), "unknown": strings.Replace(base, `"credential_ref":null`, `"credential_ref":null,"api_key":"forbidden"`, 1), "secretref": strings.Replace(base, `"credential_ref":null`, `"credential_ref":"raw-secret"`, 1), "userinfo": strings.Replace(base, "https://fixture.invalid/v1", "https://name:secret@fixture.invalid/v1", 1), "query": strings.Replace(base, "https://fixture.invalid/v1", "https://fixture.invalid/v1?q=x", 1), "fragment": strings.Replace(base, "https://fixture.invalid/v1", "https://fixture.invalid/v1#", 1), "http": strings.Replace(base, "https://", "http://", 1)} {
		t.Run(name, func(t *testing.T) {
			if _, _, e := parseClientConfiguration(doc, []byte(raw)); e == nil {
				t.Fatal("invalid configuration accepted")
			}
		})
	}
	valid := strings.Replace(base, `"credential_ref":null`, `"credential_ref":"cred-fixture-api_key-1000000000000-0123abcd-0123abcd"`, 1)
	if _, _, e := parseClientConfiguration(doc, []byte(valid)); e != nil {
		t.Fatal(e)
	}
	db, _ := configurationDB(t, 23, true)
	raw, env := configurationEnvelope(t, doc, "session-target", 1)
	var fields Object
	if e := json.Unmarshal(raw, &fields); e != nil {
		t.Fatal(e)
	}
	fields["session_id"] = "settled-fixture"
	fields["project_id"] = "fixture-project"
	fields["expected_revision"] = 1
	fields["writer_epoch"] = 1
	raw = Bytes(fields)
	env, e := decodeClientIdentityEnvelope(doc, raw)
	if e != nil {
		t.Fatal(e)
	}
	tx, e := db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	defer tx.Rollback()
	if _, e = stageClientConfiguration(context.Background(), tx, doc, configurationFixtureOwner, configurationFixturePrincipal, raw, env); e == nil || !strings.Contains(e.Error(), "SESSION_INTEGRATION_REQUIRED") {
		t.Fatalf("%v", e)
	}
	// Valid default scope is decoded; trusted Host authority is checked by Execute.
	hostRaw, _ := configurationEnvelope(t, doc, "public-unwired", 1)
	if _, e = DecodeEnvelope(hostRaw); e != nil {
		t.Fatalf("public default configure decode: %v", e)
	}
}

func TestClientConfigurationNoOpaqueAuthorityAndOldReleaseGuard(t *testing.T) {
	db, _ := configurationDB(t, 23, true)
	doc := configurationSchema(t)
	tx, e := db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	defer tx.Rollback()
	ref := "mc-" + strings.Repeat("1", 32)
	forged := Object{"model_config_ref": ref, "config_revision": 1, "provider_id": "fixture", "base_url": "https://fixture.invalid", "model_id": "fixture", "credential_ref": nil, "verified_at": Now(), "ready": true}
	if _, e = tx.Exec(`INSERT INTO domain_objects(project,kind,id,revision,body,immutable) VALUES('fixture','REPORT',?,1,?,0)`, ref, string(Bytes(forged))); e != nil {
		t.Fatal(e)
	}
	if _, e = readClientConfiguration(context.Background(), tx, doc, configurationFixtureOwner, configurationFixturePrincipal, ref); e != sql.ErrNoRows {
		t.Fatalf("opaque REPORT established typed authority: %v", e)
	}
	if _, _, e = upgradeQueueRelease("../..", 22); e == nil || !strings.Contains(e.Error(), "require exact 1..22") {
		t.Fatalf("old release guard widened: %v", e)
	}
}
