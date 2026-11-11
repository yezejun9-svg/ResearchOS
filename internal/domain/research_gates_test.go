package domain

import (
	"context"
	"fmt"
	"os"
	"researchos.local/research-os/adapters/sources"
	"testing"
	"time"
)

func TestW08RequiredGates(t *testing.T) {
	for _, mode := range []string{"registered", "remove", "inconclusive", "stale", "stable", "regressed"} {
		r := researchSetup(t, true)
		r.start(t, time.Now().UTC().Add(-time.Minute).Truncate(time.Second))
		for _, kind := range []string{"GITHUB", "PAPER", "X"} {
			r.capture(t, kind, false)
		}
		input := mode
		if mode == "remove" {
			input = "registered"
		}
		x := researchExperiment(t, r, input)
		r.checkpoint(t, Empty(), []any{x["id"]})
		f := r.f
		if mode == "remove" {
			status, _, _ := f.request("POST", f.path("/research-cycles/"+Str(r.cycle, "id")+"/checkpoint"), ID(), testTag(r.cycle), Object{
				"source_coverage": r.cycle["source_coverage"], "candidate_evidence_ids": Empty(), "required_experiment_ids": Empty(), "decision_ids": Empty(), "follow_up_task_ids": Empty(), "checkpoint_artifact_id": nil})
			researchAssert(t, "W08-REQUIRED-REMOVE", 422, status)
		}
		if mode == "stale" {
			f.token = r.owner
			value := f.artifact("changed research requirement", Empty())
			state := f.state()
			proposal := f.expect(201, "POST", f.path("/change-proposals"), ID(), testTag(state), changeRequest(state, Arr(x, "input_refs")[0].(map[string]any), value, "text"))
			f.apply(proposal)
		}
		f.token = r.scheduler
		status, _, _ := f.request("POST", f.path("/research-cycles/"+Str(r.cycle, "id")+"/close"), ID(), testTag(r.cycle), Object{"requested_status": "COMPLETE", "outcome_summary": "Required experiment qualification regression"})
		want := 422
		if mode == "stable" || mode == "regressed" {
			want = 200
		}
		researchAssert(t, "W08-REQUIRED-"+mode, want, status)
		if want == 422 {
			r.close(t, "PARTIAL")
		}
		if dir := os.Getenv("W08_EVIDENCE_DIR"); dir != "" {
			researchSnapshot(t, r, dir, "required-"+mode)
		}
	}
}

func TestW08CoverageGates(t *testing.T) {
	for _, mode := range []string{"fraction-gap", "multipage", "duplicate", "replay"} {
		r := researchSetup(t, true)
		r.start(t, time.Now().UTC().Add(-time.Minute).Truncate(time.Second))
		from, to, _ := parseCycleWindow(Str(r.cycle, "window_from"), Str(r.cycle, "window_to"))
		if mode == "fraction-gap" {
			from = from.Add(500 * time.Millisecond)
		}
		f := r.f
		f.token = r.source
		cur := r.cursor(t, "GITHUB")
		config, cursor, err := f.s.sourceConfig(context.Background(), r.source, f.project, Str(cur, "id"))
		if err != nil {
			t.Fatal(err)
		}
		for i := 0; i < 2; i++ {
			item := i
			if mode == "duplicate" {
				item = 0
			}
			page := sources.Page{RawResponse: []byte(fmt.Sprintf("source-page-%d", i)), RawMediaType: "text/plain", Complete: i == 1, HTTPStatus: 200, FetchedAt: time.Now().UTC(),
				RequestURLs: []string{"https://api.github.com/repos/researchos/research/releases"}, FinalURLs: []string{"https://api.github.com/repos/researchos/research/releases"},
				Items: []sources.Item{{SourceID: r.ids["GITHUB"], CanonicalURL: fmt.Sprintf("https://github.com/researchos/research/releases/tag/review-%d", item), UpstreamID: fmt.Sprintf("review-%d", item), PublishedAt: to.Add(-time.Second), Body: []byte(fmt.Sprintf("source-body-%d", item)), MediaType: "text/plain", Locator: "body"}}}
			if !page.Complete {
				page.NextCursor = "second"
			}
			if _, err = f.s.captureSourcePage(context.Background(), r.source, f.project, cursor, config, from, to, 20, sourceFixtureAdapter{page}); err != nil {
				t.Fatal(err)
			}
			if mode == "replay" && i == 0 {
				_, err = f.s.captureSourcePage(context.Background(), r.source, f.project, cursor, config, from, to, 20, sourceFixtureAdapter{page})
				researchAssert(t, "W08-SOURCE-REPLAY", true, err == nil)
				changed := page
				changed.RawResponse = []byte("different source page")
				_, err = f.s.captureSourcePage(context.Background(), r.source, f.project, cursor, config, from, to, 20, sourceFixtureAdapter{changed})
				fault, ok := err.(*Fault)
				researchAssert(t, "W08-SOURCE-PAGE-CONFLICT", true, ok && fault.Status == 409)
			}
			advance := Object{"opaque_cursor": nil, "covered_until": to.Format(time.RFC3339Nano), "last_success_at": Now(), "retry_after": nil, "pending_window_from": nil, "pending_window_to": nil, "last_cycle_id": r.cycle["id"]}
			if !page.Complete {
				advance["opaque_cursor"], advance["covered_until"], advance["pending_window_from"], advance["pending_window_to"] = "second", cursor["covered_until"], from.Format(time.RFC3339Nano), to.Format(time.RFC3339Nano)
			}
			f.expect(200, "PUT", f.path("/source-cursors/"+Str(cursor, "id")), ID(), testTag(cursor), advance)
			config, cursor, err = f.s.sourceConfig(context.Background(), r.source, f.project, Str(cur, "id"))
			if err != nil {
				t.Fatal(err)
			}
		}
		r.capture(t, "PAPER", false)
		r.capture(t, "X", false)
		r.checkpoint(t, Empty(), Empty())
		coverage := Arr(r.cycle, "source_coverage")[0].(map[string]any)
		wantStatus, wantCount := "COMPLETE", 2
		if mode == "fraction-gap" {
			wantStatus, wantCount = "PARTIAL", 0
		}
		if mode == "duplicate" {
			wantCount = 1
		}
		researchAssert(t, "W08-COVERAGE-"+mode, []any{wantStatus, wantCount}, []any{coverage["status"], coverage["record_count"]})
		if mode == "fraction-gap" {
			status, _, _ := f.request("POST", f.path("/research-cycles/"+Str(r.cycle, "id")+"/close"), ID(), testTag(r.cycle), Object{"requested_status": "COMPLETE", "outcome_summary": "Fractional coverage gap"})
			researchAssert(t, "W08-COVERAGE-NO-FALSE-COMPLETE", 422, status)
		}
		if dir := os.Getenv("W08_EVIDENCE_DIR"); dir != "" {
			researchSnapshot(t, r, dir, "coverage-"+mode)
		}
		if mode == "duplicate" {
			// Trusted fault injections are rolled back; capture/advance above use the real service.
			for _, fault := range []string{"CURRENT", "UNPROVEN", "STALE", "REVOKED", "BAD_HASH", "BAD_REVISION"} {
				tx, err := f.db.Begin()
				if err != nil {
					t.Fatal(err)
				}
				var raw string
				if err = tx.QueryRow("SELECT a.body FROM source_pages p JOIN domain_objects a ON a.project=p.project AND a.id=p.raw_artifact_id AND a.kind='Artifact' WHERE p.project=? AND p.cursor_id=? AND p.page_cursor_in=''", f.project, cur["id"]).Scan(&raw); err != nil {
					t.Fatal(err)
				}
				a, err := Decode([]byte(raw))
				if err != nil {
					t.Fatal(err)
				}
				switch fault {
				case "UNPROVEN":
					a["id"] = ID()
				case "BAD_REVISION":
					Arr(a, "input_refs")[0].(map[string]any)["revision"] = 999999
				case "BAD_HASH":
					a["content_hash"] = Digest([]byte("tampered"))
				case "STALE", "REVOKED":
					a["validity"] = fault
					if err = bump(a); err != nil {
						t.Fatal(err)
					}
					err = f.s.put(tx, "Artifact", a)
				}
				if err != nil {
					t.Fatal(err)
				}
				if fault == "UNPROVEN" || fault == "BAD_REVISION" || fault == "BAD_HASH" {
					err = f.s.effectiveInputs(tx, f.project, "Artifact", a, map[string]bool{})
				} else {
					err = f.s.effective(tx, f.project, Ref(a, "Artifact"))
				}
				tx.Rollback()
				researchAssert(t, "W08-SOURCE-GUARD-"+fault, fault == "CURRENT", err == nil)
			}
		}
	}
}
