package domain

import (
	"context"
	"researchos.local/research-os/adapters/sources"
	"testing"
	"time"
)

func TestW07HealthRealCyclePartialProgressAndIndependentSources(t *testing.T) {
	r := researchSetup(t, true)
	r.start(t, time.Now().UTC().Add(-time.Minute).Truncate(time.Second))
	from, to, _ := parseCycleWindow(Str(r.cycle, "window_from"), Str(r.cycle, "window_to"))
	if _, e := r.f.s.CaptureSourcePage(context.Background(), r.source, r.f.project, Str(r.cursor(t, "X"), "id"), from, to, 20, "", ""); e == nil {
		t.Fatal("missing browser did not report resource gap")
	}
	for _, kind := range []string{"GITHUB", "PAPER"} {
		config, cursor, e := r.f.s.sourceConfig(context.Background(), r.source, r.f.project, Str(r.cursor(t, kind), "id"))
		if e != nil {
			t.Fatal(e)
		}
		endpoint := map[string]string{"GITHUB": "https://github.com/researchos/research/releases/tag/v1", "PAPER": "https://arxiv.org/abs/2609.12345"}[kind]
		page := sources.Page{FetchedAt: time.Now().UTC(), Failure: "page_timeout", RequestURLs: []string{endpoint}, FinalURLs: []string{endpoint}, RawResponse: []byte("complete prefix before timeout " + kind), RawMediaType: "text/plain", Items: []sources.Item{{SourceID: r.ids[kind], CanonicalURL: endpoint, UpstreamID: "v1", PublishedAt: to.Add(-time.Minute), Body: []byte("substantive original " + kind + " body"), MediaType: "text/plain", Locator: "body"}}}
		got, e := r.f.s.captureSourcePage(context.Background(), r.source, r.f.project, cursor, config, from, to, 20, sourceFixtureAdapter{page})
		if e != nil || len(got.Evidence) != 1 {
			t.Fatal(kind, got, e)
		}
	}
	r.checkpoint(t, Empty(), Empty())
	r.f.token = r.scheduler
	status, _, _ := r.f.request("POST", r.f.path("/research-cycles/"+Str(r.cycle, "id")+"/close"), ID(), testTag(r.cycle), Object{"requested_status": "COMPLETE", "outcome_summary": "incomplete sources cannot complete"})
	if status != 422 {
		t.Fatal("false complete", status)
	}
	r.close(t, "PARTIAL")
	if r.cycle["status"] != "PARTIAL" {
		t.Fatal(r.cycle)
	}
	for _, v := range Arr(r.cycle, "source_coverage") {
		c := v.(map[string]any)
		if c["source_id"] == r.ids["X"] && c["status"] != "NOT_CONFIGURED" {
			t.Fatal(c)
		}
	}
	emitH07Snapshot(t, r.f, "cycle_partial", Object{"required_sources": []any{"GITHUB", "PAPER", "X"}}, Object{"cycle": r.cycle})
}
