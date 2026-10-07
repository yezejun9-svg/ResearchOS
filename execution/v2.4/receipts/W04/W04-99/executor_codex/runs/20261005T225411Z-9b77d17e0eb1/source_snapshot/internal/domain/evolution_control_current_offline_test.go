//go:build windows

package domain

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"researchos.local/research-os/adapters/protectedstore"
	"researchos.local/research-os/evaluation/evolution"
	"sort"
	"strings"
	"testing"
	"time"
)

// Offline diagnostics never construct a qualified owner or invoke evaluation.
// Preserved synthetic B0 chunks are ordered by writer timestamps, and the full
// original hash from the recorded SAMPLE must match before any row analysis.
func TestControlCurrentPreservedPreparation(t *testing.T) {
	base := os.Getenv("W16_CURRENT_OFFLINE_WORK")
	if base == "" {
		t.Skip("preserved setup-only diagnostic required")
	}
	ctx := context.Background()
	base = filepath.Clean(base)
	db, err := sql.Open("sqlite", "file:"+filepath.ToSlash(filepath.Join(base, "data", "researchos.sqlite"))+"?mode=ro")
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	privateRoot := base + "-private"
	private, err := protectedstore.OpenCanary(privateRoot)
	if err != nil {
		t.Fatal(err)
	}
	defer private.Close()
	var project string
	if err = db.QueryRow("SELECT project FROM evolution_hosts").Scan(&project); err != nil {
		t.Fatal(err)
	}
	type part struct {
		blob protectedstore.Blob
		time time.Time
	}
	parts := []part{}
	entries, err := os.ReadDir(privateRoot)
	if err != nil {
		t.Fatal(err)
	}
	for _, entry := range entries {
		if !strings.HasSuffix(entry.Name(), ".json") {
			continue
		}
		raw, err := os.ReadFile(filepath.Join(privateRoot, entry.Name()))
		if err != nil {
			t.Fatal(err)
		}
		var b protectedstore.Blob
		if err = json.Unmarshal(raw, &b); err != nil {
			t.Fatal(err)
		}
		if strings.Contains(b.MediaType, "stage=B0;") {
			info, err := entry.Info()
			if err != nil {
				t.Fatal(err)
			}
			parts = append(parts, part{b, info.ModTime()})
		}
	}
	sort.Slice(parts, func(i, j int) bool { return parts[i].time.Before(parts[j].time) })
	raw := []byte{}
	for _, p := range parts {
		b, err := private.Read(ctx, p.blob)
		if err != nil {
			t.Fatal(err)
		}
		raw = append(raw, b...)
	}
	if Digest(raw) != os.Getenv("W16_CURRENT_OFFLINE_B0_HASH") {
		t.Fatal("preserved B0 order/hash did not match original SAMPLE")
	}
	b0, err := controlSnapshotMemoryDB(ctx, raw)
	if err != nil {
		t.Fatal(err)
	}
	defer b0.Close()
	before, err := controlCurrentRows(b0)
	if err != nil {
		t.Fatal(err)
	}
	tx, err := db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback()
	after, err := controlCurrentRows(tx)
	if err != nil {
		t.Fatal(err)
	}
	h, err := evolutionHost(tx, project)
	if err != nil {
		t.Fatal(err)
	}
	get := func(kind string) Object {
		t.Helper()
		var raw string
		if err := tx.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind=?", project, kind).Scan(&raw); err != nil {
			t.Fatal(err)
		}
		b, err := Decode([]byte(raw))
		if err != nil {
			t.Fatal(err)
		}
		return b
	}
	x, task, run, state := get("SystemCandidate"), get("Task"), get("Run"), get("ProjectState")
	current := h["current_control"].(map[string]any)
	frozen, present, err := evolutionHoldoutEntry(tx, project, Str(x, "id"), "HOLDOUT_FROZEN")
	if err != nil || !present {
		t.Fatal("missing holdout")
	}
	n := &controlCurrentNames{Project: project, Candidate: Str(x, "id"), Task: Str(task, "id"), Run: Str(run, "id"), Experiment: Str(x, "experiment_id"), Goal: Str(task, "goal_id"), Retention: Str(task, "no_progress_record_id"), State: Str(state, "id"), Verifier: Str(frozen, "verifier_id"), Executor: Str(run, "executor_principal_id"), Release: Str(h, "release_principal"), Plan: Hash(evolutionPlan(x)), Rows: after}
	if err = tx.QueryRow("SELECT creator FROM evolution_candidates WHERE project=? AND candidate=?", project, x["id"]).Scan(&n.Author); err != nil {
		t.Fatal(err)
	}
	a := &currentControlAuthority{id: Str(current, "session_id"), project: project, ownerID: n.Author, stableRef: x["stable_artifact_ref"].(map[string]any), candidateRef: x["candidate_artifact_ref"].(map[string]any), snapshotRef: h["snapshot_ref"].(map[string]any), provenanceRef: current["provenance_ref"].(map[string]any)}
	a.owner.StableHash = Str(a.stableRef, "content_hash")
	differences, err := controlRowDifferences(tx, before, after)
	if err != nil {
		t.Fatal(err)
	}
	indices, err := controlIndexChanges(tx, before, after, differences)
	if err != nil {
		t.Fatal(err)
	}
	groups := map[string]int{}
	for _, d := range differences {
		row := indices[d.Table].after[d.KeyHash]
		label := d.Table
		if d.Table == "domain_objects" || d.Table == "domain_versions" || d.Table == "domain_refs" {
			label += "/" + Str(row, "kind")
		}
		if d.Table == "idempotency" {
			label += "/" + Str(row, "operation")
		}
		groups[label]++
	}
	fmt.Println("W16_CURRENT_PREPARATION_DIFFERENCES " + string(Bytes(groups)))
	delta, err := a.validatePreparation(tx, before, n)
	if err != nil {
		t.Fatal(err)
	}
	counts := map[string]int{}
	for _, d := range delta {
		counts[d.Table]++
	}
	fmt.Println("W16_CURRENT_OFFLINE_PREPARATION " + string(evolution.Bytes(map[string]any{"delta_hash": Hash(delta), "counts": counts, "qualified_owner": false, "evaluation_invoked": false})))
}
