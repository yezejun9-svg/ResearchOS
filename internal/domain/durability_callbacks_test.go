package domain

import (
	"context"
	"researchos.local/research-os/adapters/sources"
	"testing"
	"time"
)

func TestW12DuplicateCallbacks(t *testing.T) {
	f, _, cursor := sourceProject(t)
	resourceHTTP(f)
	f.switchPrincipal("resource-source-fixture", []string{"SOURCE_ADAPTER"})
	config, current, e := f.s.sourceConfig(context.Background(), f.token, f.project, Str(cursor, "id"))
	if e != nil {
		t.Fatal(e)
	}
	from := time.Now().UTC().Add(-2 * time.Hour).Truncate(time.Second)
	to := from.Add(time.Hour)
	page := sources.Page{Items: []sources.Item{{SourceID: Str(cursor, "source_id"), CanonicalURL: "https://github.com/paperclipai/paperclip/releases/tag/v1", UpstreamID: "fixture-release-v1", UpstreamRevision: "v1", PublishedAt: from.Add(time.Minute), Body: []byte("durable fixture source item"), MediaType: "text/plain", Locator: "release.body"}}, RawResponse: []byte(`[{"id":"fixture-release-v1"}]`), RawMediaType: "application/json", Complete: true, HTTPStatus: 200, FetchedAt: time.Now().UTC(), RequestURLs: []string{"https://api.github.com/repos/paperclipai/paperclip/releases"}, FinalURLs: []string{"https://api.github.com/repos/paperclipai/paperclip/releases"}}
	captured, e := f.s.captureSourcePage(context.Background(), f.token, f.project, current, config, from, to, 20, sourceFixtureAdapter{page})
	if e != nil {
		t.Fatal(e)
	}
	duplicateRejected := 0
	for range 2 {
		if _, e = f.s.captureSourcePage(context.Background(), f.token, f.project, current, config, from, to, 20, sourceFixtureAdapter{page}); e != nil {
			duplicateRejected++
		}
	}
	advance := Object{"opaque_cursor": nil, "covered_until": to.Format(time.RFC3339Nano), "last_success_at": Now(), "retry_after": nil, "pending_window_from": nil, "pending_window_to": nil, "last_cycle_id": nil}
	advanced := f.expect(200, "PUT", f.path("/source-cursors/"+Str(cursor, "id")), ID(), testTag(cursor), advance)
	staleAdvance := MergeCopy(advance, Object{"covered_until": from.Format(time.RFC3339Nano)})
	regress, _, _ := f.request("PUT", f.path("/source-cursors/"+Str(cursor, "id")), ID(), testTag(advanced), staleAdvance)
	evidenceCount := countKind(t, f.db, "Evidence")
	resourceSnapshot(f, "source-replay-after.json")
	o := orchestrationSetup(t)
	g := o.f
	resourceHTTP(g)
	r := o.claim(o.task("experiment-callback-fixture", Empty(), Empty()))
	artifact := o.report(r, []byte(`{"result":"verified"}`))
	codes := []int{200}
	g.token, _ = g.s.IssueCredential(context.Background(), r.executor, time.Minute)
	for range 2 {
		code, _, _ := g.request("POST", g.path("/runs/"+Str(r.run, "id")+"/report"), ID(), testTag(r.run), r.report([]any{artifact["id"]}, 0))
		codes = append(codes, code)
	}
	request := o.acceptance(r, artifact)
	key := ID()
	tag := testTag(r.task)
	acceptanceCodes := []int{}
	var acceptance Object
	for range 3 {
		code, reply, _ := g.request("POST", g.path("/acceptances"), key, tag, request)
		acceptanceCodes = append(acceptanceCodes, code)
		acceptance = reply
	}
	var acceptances int
	g.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='AcceptanceReceipt' AND json_extract(body,'$.subject_ref.id')=?", r.task["id"]).Scan(&acceptances)
	milestones := countKind(t, g.db, "MilestoneRelease")
	resourcesAssert(t, "C11-03", []any{1, 2, 409, true, 1, 0, []int{200, 409, 409}, []int{201, 201, 201}}, []any{evidenceCount, duplicateRejected, regress, advanced["covered_until"] == advance["covered_until"], acceptances, milestones, codes, acceptanceCodes}, Object{"adapter_mode": "FIXTURE_NOT_LIVE", "source_snapshot": captured.RawArtifact, "cursor_before": cursor, "cursor_after": advanced, "acceptance": acceptance, "callback_boundary": "official reportRun and AcceptanceService; local experiment output fixture"})
	resourceSnapshot(g, "callback-replay-after.json")
}
