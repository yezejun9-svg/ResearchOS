//go:build windows

package domain

import (
	"context"
	"database/sql"
	"encoding/base64"
	"os"
	"path/filepath"
	"testing"
)

func TestModelStreamCancelRequiresBothDurableSDKFacts(t *testing.T) {
	for _, first := range []string{"command.idle", "command.abort_observed"} {
		t.Run(first, func(t *testing.T) {
			db, _ := modelStreamArchivedFixture(t)
			tx, err := db.Begin()
			if err != nil {
				t.Fatal(err)
			}
			defer tx.Rollback()
			var project, generation string
			if err = tx.QueryRow(`SELECT project,generation FROM client_queue_fences`).Scan(&project, &generation); err != nil {
				t.Fatal(err)
			}
			var raw string
			if err = tx.QueryRow(`SELECT body FROM client_control_receipts WHERE kind=? LIMIT 1`, modelObservationKind).Scan(&raw); err != nil {
				t.Fatal(err)
			}
			value, err := Decode([]byte(raw))
			if err != nil {
				t.Fatal(err)
			}
			original := value["observation"].(map[string]any)["binding"].(map[string]any)
			binding := Object{}
			for _, key := range []string{"project_id", "session_id", "task_id", "run_id", "runtime_epoch", "queue_generation", "dispatch_key", "manifest_hash", "process_identity"} {
				binding[key] = original[key]
			}
			check := func(want bool) {
				t.Helper()
				ready, err := clientQueueCancelFactsReady(tx, binding)
				if err != nil || ready != want {
					t.Fatalf("cancel facts ready=%v want=%v error=%v", ready, want, err)
				}
			}
			check(false)
			payload := Merge(Merge(Object{}, binding), Object{"sdk_idle": true, "sdk_queue_empty": true, "cancelled": true})
			if err = appendClientReceipt(tx, project, generation, "", first, ID(), payload, nil); err != nil {
				t.Fatal(err)
			}
			check(false)
			second := "command.idle"
			if first == second {
				second = "command.abort_observed"
			}
			bad := Merge(Merge(Object{}, payload), Object{"sdk_queue_empty": false})
			if err = appendClientReceipt(tx, project, generation, "", second, ID(), bad, nil); err != nil {
				t.Fatal(err)
			}
			check(false)
			foreign := Merge(Merge(Object{}, payload), Object{"runtime_epoch": 999, "process_identity": Object{"pid": 1}})
			if err = appendClientReceipt(tx, project, generation, "", second, ID(), foreign, nil); err != nil {
				t.Fatal(err)
			}
			check(false)
			if err = appendClientReceipt(tx, project, generation, "", second, ID(), payload, nil); err != nil {
				t.Fatal(err)
			}
			check(true)
			if ready, err := clientQueueCancelFactsReady(tx, Merge(Merge(Object{}, binding), Object{"queue_generation": "another-generation"})); err != nil || ready {
				t.Fatal("foreign generation gained cancel authority", ready, err)
			}
		})
	}
}

// This is the closed snapshot from the first actual compiled CLI/SDK run. Its
// original failed origin is retained; replay diagnoses final proof independently
// of another network request, process, or fixture credential.
func TestModelStreamOriginalActualFinalProof(t *testing.T) {
	path := filepath.Join("..", "..", "execution", "v2.4", "receipts", "W05", "W05-99", "model_stream_executor_codex", "test-53a6e07436494837878a09393994fdce", "failed-fixture.sqlite")
	db, err := sql.Open("sqlite", path+"?mode=ro")
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	tx, err := db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback()
	var project, runID string
	if err = tx.QueryRow(`SELECT project,run_id FROM client_queue_fences`).Scan(&project, &runID); err != nil {
		t.Fatal(err)
	}
	run, err := load(tx, project, "Run", runID)
	if err != nil {
		t.Fatal(err)
	}
	streams, order, err := (&Service{}).modelStreamFinalEvidence(context.Background(), tx, project, run)
	if err != nil {
		t.Fatal(err)
	}
	if len(streams) != 3 || len(order) != 5 {
		t.Fatalf("actual SDK streams=%d ordered messages=%d", len(streams), len(order))
	}
	// Freeze from the actual two-source-bound snapshot invocation. Replaying it
	// must not renew the archived runtime's now-expiring execution permission.
	rawSnapshot, err := os.ReadFile(filepath.Join("..", "..", "execution", "v2.4", "receipts", "W05", "W05-99", "model_stream_executor_codex", "test-18872d343fdd4a5fa788669ec6516cd9", "actual-fixtures", "actual-consumption-snapshot.json"))
	if err != nil {
		t.Fatal(err)
	}
	snapshot, err := Decode(rawSnapshot)
	if err != nil {
		t.Fatal(err)
	}
	for _, value := range Arr(snapshot, "artifacts") {
		entry := value.(map[string]any)
		decoded, e := base64.StdEncoding.DecodeString(Str(entry, "bytes"))
		if e != nil {
			t.Fatal(e)
		}
		entry["bytes"] = decoded
	}
	original, err := (&Service{}).modelStreamAcceptanceSnapshot(tx, project, run)
	if err != nil {
		t.Fatal(err)
	}
	if Hash(original) != Hash(snapshot["mu_turn"].(map[string]any)["model_stream"]) || Hash(run) != Hash(snapshot["run"]) {
		t.Fatal("archived canonical snapshot changed")
	}
	if status, why := verifyMuTurn(snapshot); status != "PASS" {
		t.Fatalf("actual canonical SDK command history refused: %s %s", status, why)
	}
	for name, mutate := range map[string]func(Object){
		"remove-stream-proof": func(v Object) { delete(v["mu_turn"].(map[string]any), "model_stream") },
		"admission-not-consumption": func(v Object) {
			stream := v["mu_turn"].(map[string]any)["model_stream"].(map[string]any)
			Arr(stream, "commands")[0].(map[string]any)["state"] = "SDK_ACCEPTED"
		},
		"changed-message-id": func(v Object) {
			stream := v["mu_turn"].(map[string]any)["model_stream"].(map[string]any)
			Arr(stream, "commands")[0].(map[string]any)["message_id"] = "forged"
		},
		"consumption-order": func(v Object) {
			stream := v["mu_turn"].(map[string]any)["model_stream"].(map[string]any)
			Arr(stream, "commands")[0].(map[string]any)["sdk_position"] = 0
		},
		"missing-original-effect": func(v Object) { v["mu_turn"].(map[string]any)["effects"] = Empty() },
		"changed-raw": func(v Object) {
			effects := Arr(v["mu_turn"].(map[string]any), "effects")
			effects[len(effects)-1].(map[string]any)["receipt"].(map[string]any)["receipt_id"] = "sha256:forged"
		},
		"forged-sdk-content": func(v Object) {
			muMutateResult(v, func(result Object) {
				messages := Arr(result, "messages")
				messages[len(messages)-1].(map[string]any)["content"] = []any{Object{"type": "text", "text": "forged"}}
			})
		},
	} {
		t.Run(name, func(t *testing.T) {
			clone := muCloneSnapshot(t, snapshot)
			mutate(clone)
			if status, why := verifyMuTurn(clone); status != "FAIL" {
				t.Fatalf("forgery passed %s %s", status, why)
			}
		})
	}
}
