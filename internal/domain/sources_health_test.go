package domain

import (
	"context"
	"database/sql"
	"fmt"
	"os"
	"path/filepath"
	"researchos.local/research-os/adapters/sources"
	"testing"
	"time"
)

func TestW07HealthDurableFaultsExactWindowAndReplay(t *testing.T) {
	r := researchSetup(t, true)
	r.start(t, time.Now().UTC().Add(-time.Minute).Truncate(time.Second))
	from, to, _ := parseCycleWindow(Str(r.cycle, "window_from"), Str(r.cycle, "window_to"))
	config, cursor, e := r.f.s.sourceConfig(context.Background(), r.source, r.f.project, Str(r.cursor(t, "GITHUB"), "id"))
	if e != nil {
		t.Fatal(e)
	}
	for _, tc := range []struct {
		name string
		page sources.Page
		want string
	}{{"timeout", sources.Page{Complete: true, ProviderResult: &sources.ProviderResult{ExitCode: 0, Status: "ok", DetailErrors: []string{"page_timeout"}}}, "PARTIAL"}, {"revoked", sources.Page{HTTPStatus: 401}, "UNAVAILABLE"}, {"not_configured", sources.Page{Failure: "NOT_CONFIGURED"}, "NOT_CONFIGURED"}} {
		t.Run(tc.name, func(t *testing.T) {
			tc.page.FetchedAt = time.Now().UTC()
			got, e := r.f.s.captureSourcePage(context.Background(), r.source, r.f.project, cursor, config, from, to, 20, sourceFixtureAdapter{tc.page})
			if e != nil {
				t.Fatal(e)
			}
			if got.HealthArtifact == nil || got.Manifest != nil || len(got.Evidence) != 0 || got.Health.Status != tc.want || got.Page.Complete {
				t.Fatalf("false source evidence: %+v", got)
			}
			before := countKind(t, r.f.db, "Artifact")
			replay, e := r.f.s.captureSourcePage(context.Background(), r.source, r.f.project, cursor, config, from, to, 20, sourceFixtureAdapter{tc.page})
			if e != nil || Hash(Ref(replay.HealthArtifact, "Artifact")) != Hash(Ref(got.HealthArtifact, "Artifact")) || countKind(t, r.f.db, "Artifact") != before {
				t.Fatal("health replay changed identity", e)
			}
			sourceTx(t, r.f.db, func(tx *sql.Tx) error {
				profile, _ := singleton(tx, r.f.project, "ProjectProfile")
				h, e := r.f.s.latestSourceHealth(tx, r.f.project, profile, config, cursor, from, to)
				if e != nil || h == nil || h.Status != tc.want {
					t.Fatal("durable health missing", h, e)
				}
				h, e = r.f.s.latestSourceHealth(tx, r.f.project, profile, config, cursor, from.Add(time.Second), to)
				if e != nil || h != nil {
					t.Fatal("health leaked into other window", h, e)
				}
				return nil
			})
			fmt.Println("H07_ASSERTION " + string(Bytes(Object{"id": tc.name, "mode": "INJECTED", "status": "PASS", "health_ref": Ref(got.HealthArtifact, "Artifact"), "health": got.Health})))
		})
	}
	var pages int
	if e = r.f.db.QueryRow("SELECT count(*) FROM source_pages WHERE project=?", r.f.project).Scan(&pages); e != nil || pages != 0 {
		t.Fatal("health-only failure became a source page", pages, e)
	}
}

func TestW07HealthPartialPrefixNoProviderCursorAndNoFalseComplete(t *testing.T) {
	r := researchSetup(t, true)
	r.start(t, time.Now().UTC().Add(-time.Minute).Truncate(time.Second))
	from, to, _ := parseCycleWindow(Str(r.cycle, "window_from"), Str(r.cycle, "window_to"))
	config, cursor, e := r.f.s.sourceConfig(context.Background(), r.source, r.f.project, Str(r.cursor(t, "X"), "id"))
	if e != nil {
		t.Fatal(e)
	}
	page := sources.Page{FetchedAt: time.Now().UTC(), RequestURLs: []string{"https://x.com/search"}, FinalURLs: []string{"https://x.com/search"}, RawResponse: []byte(`{"items":["full prefix"]}`), RawMediaType: "application/json", AccessScope: "VISIBLE_PUBLIC_POSTS", ObservationMarker: "observed_tail:123", Complete: true, NextCursor: "observed_tail:123", ProviderResult: &sources.ProviderResult{ExitCode: 0, Status: "ok", DetailErrors: []string{"page_timeout"}}, Items: []sources.Item{{SourceID: r.ids["X"], CanonicalURL: "https://x.com/research/status/123", UpstreamID: "123", PublishedAt: to.Add(-time.Minute), Body: []byte("full public post body"), MediaType: "text/plain", Locator: "post.text"}}}
	got, e := r.f.s.captureSourcePage(context.Background(), r.source, r.f.project, cursor, config, from, to, 20, sourceFixtureAdapter{page})
	if e != nil {
		t.Fatal(e)
	}
	if got.Health.FullReadCount != 1 || got.Health.Status != "PARTIAL" || got.Page.NextCursor != "" || got.Manifest == nil || got.HealthArtifact == nil {
		t.Fatal(got)
	}
	artifactCount := countKind(t, r.f.db, "Artifact")
	eventCount := countKind(t, r.f.db, "EventEnvelope")
	before := countKind(t, r.f.db, "Evidence")
	again, e := r.f.s.captureSourcePage(context.Background(), r.source, r.f.project, cursor, config, from, to, 20, sourceFixtureAdapter{page})
	if e != nil || Hash(Ref(again.HealthArtifact, "Artifact")) != Hash(Ref(got.HealthArtifact, "Artifact")) || again.Manifest["id"] != got.Manifest["id"] || countKind(t, r.f.db, "Artifact") != artifactCount || countKind(t, r.f.db, "EventEnvelope") != eventCount || len(again.Evidence) != 1 || again.Evidence[0]["id"] != got.Evidence[0]["id"] || countKind(t, r.f.db, "Evidence") != before {
		t.Fatal("repeated visible post inflated evidence", e)
	}
	sourceTx(t, r.f.db, func(tx *sql.Tx) error {
		profile, _ := singleton(tx, r.f.project, "ProjectProfile")
		coverage, e := r.f.s.researchCoverage(tx, r.f.project, profile, from, to)
		if e != nil {
			return e
		}
		for _, v := range coverage {
			c := v.(map[string]any)
			if c["source_id"] == r.ids["X"] {
				n, _ := Num(c, "record_count")
				if c["status"] != "PARTIAL" || n != 1 || c["gap_reason"] != "page_timeout" {
					t.Fatal(c)
				}
			}
		}
		return nil
	})
}

type staleHealthAdapter struct {
	run  func()
	page sources.Page
}

func (a staleHealthAdapter) Fetch(_ context.Context, q sources.Query) (sources.Page, error) {
	a.run()
	a.page.RequestedFrom = q.From
	a.page.RequestedTo = q.To
	return a.page, nil
}
func TestW07HealthCASAndUnconfiguredResourceDedup(t *testing.T) {
	r := researchSetup(t, true)
	r.start(t, time.Now().UTC().Add(-time.Minute).Truncate(time.Second))
	from, to, _ := parseCycleWindow(Str(r.cycle, "window_from"), Str(r.cycle, "window_to"))
	for i := 0; i < 2; i++ {
		got, e := r.f.s.CaptureSourcePage(context.Background(), r.source, r.f.project, Str(r.cursor(t, "X"), "id"), from, to, 20, "", "")
		if e == nil || got.Health.Status != "NOT_CONFIGURED" || got.HealthArtifact == nil {
			t.Fatal(got, e)
		}
	}
	var count int
	r.f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='ResourceRequest'", r.f.project).Scan(&count)
	if count != 1 {
		t.Fatal("duplicate backend requests", count)
	}
	config, cursor, _ := r.f.s.sourceConfig(context.Background(), r.source, r.f.project, Str(r.cursor(t, "GITHUB"), "id"))
	adapter := staleHealthAdapter{page: sources.Page{Failure: "page_timeout"}, run: func() {
		sourceTx(t, r.f.db, func(tx *sql.Tx) error {
			c, _ := load(tx, r.f.project, "SourceCursor", Str(cursor, "id"))
			bump(c)
			return r.f.s.put(tx, "SourceCursor", c)
		})
	}}
	got, e := r.f.s.captureSourcePage(context.Background(), r.source, r.f.project, cursor, config, from, to, 20, adapter)
	if e == nil || got.HealthArtifact != nil {
		t.Fatal("stale fetch overwrote health", e)
	}
}

func emitH07Snapshot(t *testing.T, f *fixture, id string, input, actual Object) {
	t.Helper()
	out := Object{"id": id, "measurement_mode": "INJECTED", "input": input, "actual": actual, "status": "PASS", "project_id": f.project}
	if dir := os.Getenv("W07_EVIDENCE_DIR"); dir != "" {
		if e := os.MkdirAll(dir, 0755); e != nil {
			t.Fatal(e)
		}
		path := filepath.Join(dir, id+"-"+ID()+".sqlite")
		if _, e := f.db.Exec("VACUUM INTO ?", path); e != nil {
			t.Fatal(e)
		}
		out["db_snapshot_path"] = path
		out["db_closed_or_vacuum_snapshot"] = true
	}
	fmt.Println("H07_ASSERTION " + string(Bytes(out)))
}

func TestW07HealthH07ProductionFaultMatrix(t *testing.T) {
	for _, name := range []string{"not_configured", "429", "401_or_revoked", "timeout", "empty_valid_result", "visible_empty", "index_only", "pr_open", "pr_closed_unmerged", "pr_merged"} {
		t.Run(name, func(t *testing.T) {
			r := researchSetup(t, true)
			r.start(t, time.Now().UTC().Add(-time.Minute).Truncate(time.Second))
			from, to, _ := parseCycleWindow(Str(r.cycle, "window_from"), Str(r.cycle, "window_to"))
			kind := "GITHUB"
			if name == "visible_empty" || name == "not_configured" {
				kind = "X"
			}
			config, cursor, e := r.f.s.sourceConfig(context.Background(), r.source, r.f.project, Str(r.cursor(t, kind), "id"))
			if e != nil {
				t.Fatal(e)
			}
			endpoint := "https://api.github.com/repos/researchos/research/releases"
			if kind == "X" {
				endpoint = "https://x.com/search"
			}
			p := sources.Page{FetchedAt: time.Now().UTC(), RequestURLs: []string{endpoint}, FinalURLs: []string{endpoint}, RawResponse: []byte("[]"), RawMediaType: "application/json", Complete: true, HTTPStatus: 200}
			want := "COMPLETE"
			switch name {
			case "not_configured":
				p.Failure = "NOT_CONFIGURED"
				want = "NOT_CONFIGURED"
			case "429":
				p.HTTPStatus = 429
				wait := time.Now().UTC().Add(time.Minute)
				p.RetryAfter = &wait
				want = "RATE_LIMITED"
			case "401_or_revoked":
				p.HTTPStatus = 401
				want = "UNAVAILABLE"
			case "timeout":
				p.ProviderResult = &sources.ProviderResult{ExitCode: 0, Status: "ok", DetailErrors: []string{"page_timeout"}}
				want = "PARTIAL"
			case "visible_empty":
				p.Complete = false
				p.VisibleEmpty = true
				p.AccessScope = "VISIBLE_PUBLIC_POSTS"
				p.RawResponse = Bytes(Object{"url": endpoint, "items": Empty(), "empty": true})
				want = "PARTIAL"
			case "index_only":
				p.Items = []sources.Item{{ReadLevel: "INDEX", Body: []byte("index snippet")}}
				want = "PARTIAL"
			case "pr_open", "pr_closed_unmerged", "pr_merged":
				state := map[string]string{"pr_open": "OPEN", "pr_closed_unmerged": "CLOSED", "pr_merged": "MERGED"}[name]
				p.AccessScope = "PINNED_PR_DETAIL"
				p.Items = []sources.Item{{SourceID: r.ids[kind], CanonicalURL: "https://github.com/researchos/research/pull/1", UpstreamID: "1", PublishedAt: to.Add(-time.Minute), Body: Bytes(Object{"state": state, "body": "Original PR detail fixture"}), MediaType: "application/json", ReadLevel: "BODY", PRState: state, Locator: "pull_request.body"}}
			}
			got, e := r.f.s.captureSourcePage(context.Background(), r.source, r.f.project, cursor, config, from, to, 20, sourceFixtureAdapter{p})
			if e != nil || got.Health.Status != want || got.HealthArtifact == nil {
				t.Fatal(name, got, e)
			}
			after := r.cursor(t, kind)
			if after["covered_until"] != nil {
				t.Fatal("capture advanced uncommitted window")
			}
			if name == "429" {
				never := &neverFetchSource{}
				_, e = r.f.s.captureSourcePage(context.Background(), r.source, r.f.project, after, config, from, to, 20, never)
				if e != nil || never.calls != 0 {
					t.Fatal("ignored retry deadline", e)
				}
			}
			emitH07Snapshot(t, r.f, name, Object{"page": p, "requested_from": from, "requested_to": to}, Object{"health": got.Health, "health_artifact_ref": Ref(got.HealthArtifact, "Artifact"), "cursor": after, "manifest": got.Manifest, "evidence": got.Evidence, "page_complete": got.Page.Complete})
		})
	}
}

func TestW07HealthForgedReportCannotCompleteWindow(t *testing.T) {
	r := researchSetup(t, true)
	r.start(t, time.Now().UTC().Add(-time.Minute).Truncate(time.Second))
	from, to, _ := parseCycleWindow(Str(r.cycle, "window_from"), Str(r.cycle, "window_to"))
	config, cursor, _ := r.f.s.sourceConfig(context.Background(), r.source, r.f.project, Str(r.cursor(t, "GITHUB"), "id"))
	sourceTx(t, r.f.db, func(tx *sql.Tx) error {
		actor, e := authenticate(tx, r.source)
		if e != nil {
			return e
		}
		_, e = r.f.s.sealSourceHealth(tx, actor, r.f.project, cursor, config, SourceCapture{Page: sources.Page{FetchedAt: time.Now().UTC()}, Health: sources.SourceHealth{Status: "COMPLETE", Exhaustive: true, RequestedFrom: from, RequestedTo: to}})
		if e != nil {
			return e
		}
		profile, _ := singleton(tx, r.f.project, "ProjectProfile")
		coverage, e := r.f.s.researchCoverage(tx, r.f.project, profile, from, to)
		if e != nil {
			return e
		}
		for _, v := range coverage {
			c := v.(map[string]any)
			if c["source_id"] == r.ids["GITHUB"] && c["status"] == "COMPLETE" {
				t.Fatal("standalone REPORT forged page chain")
			}
		}
		return nil
	})
}

// Caller-authored bytes and role names cannot supply the host's capture authority.
// All forgery attempts enter through the actual authenticated public HTTP routes.
func TestW07HealthPublicIngressCannotForgeCapturedSource(t *testing.T) {
	for _, role := range []string{"owner_planner", "source_adapter"} {
		t.Run(role, func(t *testing.T) {
			r := researchSetup(t, true)
			r.start(t, time.Now().UTC().Add(-time.Minute).Truncate(time.Second))
			from, to, _ := parseCycleWindow(Str(r.cycle, "window_from"), Str(r.cycle, "window_to"))
			config, cursor, err := r.f.s.sourceConfig(context.Background(), r.source, r.f.project, Str(r.cursor(t, "GITHUB"), "id"))
			if err != nil {
				t.Fatal(err)
			}
			if role == "source_adapter" {
				r.f.token = r.source
			}
			var actor Principal
			var profile Object
			sourceTx(t, r.f.db, func(tx *sql.Tx) error {
				actor, err = authenticate(tx, r.f.token)
				if err != nil {
					return err
				}
				profile, err = singleton(tx, r.f.project, "ProjectProfile")
				return err
			})
			upload := func(raw []byte, kind, evidence, media string, refs []any) Object {
				u := r.f.expect(201, "POST", r.f.path("/content"), ID(), "", raw)
				return Object{"run_id": nil, "kind": kind, "evidence_kind": evidence, "measurement_mode": "LIVE", "content_hash": u["content_hash"], "storage_key": u["storage_key"], "media_type": media, "byte_size": len(raw), "input_refs": []any{Ref(cursor, "SourceCursor"), Ref(profile, "ProjectProfile")}, "source_refs": refs, "produced_by": actor.ID, "access_class": "PROJECT"}
			}
			fakeBody := upload([]byte("Caller-authored body without any provider request."), "SOURCE_SNAPSHOT", "OBSERVED", "text/plain", Empty())
			fakeBody["input_refs"] = []any{Ref(cursor, "SourceCursor")}
			fake := r.f.expect(201, "POST", r.f.path("/artifacts"), ID(), r.f.stateTag(), fakeBody)
			refs := []any{Ref(fake, "Artifact")}
			health := sources.SourceHealth{Status: "NOT_CONFIGURED", Reason: "caller-authored false outage", RequestedFrom: from, RequestedTo: to, ActualFrom: &from, ActualTo: &to, AccessScope: "NONE"}
			doc := Object{"schema": sourceHealthSchema, "source_id": config["source_id"], "query_hash": cursor["query_hash"], "config_hash": Hash(config), "query": config["query"], "cursor_ref": Ref(cursor, "SourceCursor"), "profile_ref": Ref(profile, "ProjectProfile"), "health": health, "source_refs": refs, "fetched_at": Now(), "failed_provider_raw": nil}
			before := countKind(t, r.f.db, "Artifact")
			for _, attempt := range []string{"self_consistent", "body_trusted_flag", "producer_impersonation", "schema_trusted_flag"} {
				rawDoc := MergeCopy(doc, Object{})
				if attempt == "body_trusted_flag" {
					rawDoc["trustedSourceHealth"] = true
				}
				body := upload(Bytes(rawDoc), "REPORT", "GENERATED", "application/vnd.researchos.source-health.v1+json", refs)
				if attempt == "producer_impersonation" {
					body["produced_by"] = "host-source-health"
				}
				if attempt == "schema_trusted_flag" {
					body["trustedSourceHealth"] = true
				}
				code, response, _ := r.f.request("POST", r.f.path("/artifacts"), ID(), r.f.stateTag(), body)
				t.Logf("HEALTH_INGRESS role=%s attempt=%s status=%d response=%s provider_calls=0", role, attempt, code, Bytes(response))
				if attempt == "schema_trusted_flag" {
					if code != 400 && code != 422 {
						t.Fatalf("schema flag accepted: %d", code)
					}
				} else if code != 403 {
					t.Fatalf("public health seal accepted: %d", code)
				}
				if countKind(t, r.f.db, "Artifact") != before {
					t.Fatal("rejected report created an Artifact")
				}
				var sealed int
				if err = r.f.db.QueryRow("SELECT sealed FROM uploaded_content WHERE project=? AND storage_key=?", r.f.project, body["storage_key"]).Scan(&sealed); err != nil || sealed != 0 {
					t.Fatal("rejected upload became sealed", err)
				}
			}
			sourceTx(t, r.f.db, func(tx *sql.Tx) error {
				h, e := r.f.s.latestSourceHealth(tx, r.f.project, profile, config, cursor, from, to)
				if e != nil || h != nil {
					t.Fatal("public report affected canonical health", h, e)
				}
				captured, e := capturedSourceArtifact(tx, r.f.project, fake)
				if e != nil || captured {
					t.Fatal("public report granted captured provenance", captured, e)
				}
				var pages int
				if e = tx.QueryRow("SELECT count(*) FROM source_pages WHERE project=?", r.f.project).Scan(&pages); e != nil || pages != 0 {
					t.Fatal("forged page authority", pages, e)
				}
				coverage, e := r.f.s.researchCoverage(tx, r.f.project, profile, from, to)
				if e != nil {
					return e
				}
				for _, v := range coverage {
					c := v.(map[string]any)
					if c["source_id"] == config["source_id"] && (c["status"] == "NOT_CONFIGURED" || c["gap_reason"] == health.Reason) {
						t.Fatal("public report affected coverage", c)
					}
				}
				return nil
			})
			page := sources.Page{FetchedAt: time.Now().UTC(), Failure: "NOT_CONFIGURED"}
			genuine, err := r.f.s.captureSourcePage(context.Background(), r.source, r.f.project, cursor, config, from, to, 20, sourceFixtureAdapter{page})
			if err != nil || genuine.HealthArtifact == nil || genuine.Health.Status != "NOT_CONFIGURED" {
				t.Fatal("host capture rejected", err)
			}
			count := countKind(t, r.f.db, "Artifact")
			replay, err := r.f.s.captureSourcePage(context.Background(), r.source, r.f.project, cursor, config, from, to, 20, sourceFixtureAdapter{page})
			if err != nil || Hash(Ref(replay.HealthArtifact, "Artifact")) != Hash(Ref(genuine.HealthArtifact, "Artifact")) || countKind(t, r.f.db, "Artifact") != count {
				t.Fatal("host health replay changed", err)
			}
			var raw []byte
			if err = r.f.db.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1", r.f.project, genuine.HealthArtifact["storage_key"]).Scan(&raw); err != nil {
				t.Fatal(err)
			}
			// Even exact bytes of a genuine report cannot bypass the public guard via deduplication.
			body := upload(raw, "REPORT", "GENERATED", "application/vnd.researchos.source-health.v1+json", Empty())
			r.f.expect(403, "POST", r.f.path("/artifacts"), ID(), r.f.stateTag(), body)
			if countKind(t, r.f.db, "Artifact") != count {
				t.Fatal("public replay created report")
			}
			t.Logf("HEALTH_INGRESS role=%s host_capture=PASS host_replay=PASS provider_calls=0 health_ref=%s", role, Bytes(Ref(genuine.HealthArtifact, "Artifact")))
		})
	}
}
