package domain

// W07-02: a source page that read items completely and then hit a rendering gap must seal the verified prefix and
// keep the gap visible, instead of being thrown away as though the source were unavailable.
//
// The two cases below are what the contract turns on. A page carrying Failure with nothing complete must still seal
// nothing - that is the pre-existing behaviour and it is not widened here. A page carrying Failure *with* a complete
// item must seal that item, preserve Failure and NextCursor, and stay not-complete, so the caller can persist a
// pending window and resume from the observed tail rather than re-reading or skipping the gap.

import (
	"context"
	"testing"
	"time"

	"researchos.local/research-os/adapters/sources"
)

func partialPageCapture(t *testing.T, page sources.Page) (SourceCapture, error, string) {
	t.Helper()
	ctx := context.Background()
	f, _, initial := sourceProject(t)
	actor := Principal{ID: "fixture-partial-adapter", Roles: []string{"SOURCE_ADAPTER"}, Grants: []Grant{{ProjectID: f.project}}}
	if e := f.s.ProvisionPrincipal(ctx, actor); e != nil {
		t.Fatal(e)
	}
	token, e := f.s.IssueCredential(ctx, actor.ID, time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	config, cursor, e := f.s.sourceConfig(ctx, token, f.project, Str(initial, "id"))
	if e != nil {
		t.Fatal(e)
	}
	to := time.Now().UTC().Add(-time.Second)
	from := to.Add(-time.Hour)
	page.FetchedAt = time.Now().UTC()
	sourceID := Str(config, "source_id")
	for i := range page.Items {
		page.Items[i].SourceID = sourceID
		page.Items[i].PublishedAt = to.Add(-time.Minute)
	}
	capture, e := f.s.captureSourcePage(ctx, token, f.project, cursor, config, from, to, 20, sourceFixtureAdapter{page})
	return capture, e, sourceID
}

func TestW0702PartialPageSealsItsVerifiedPrefix(t *testing.T) {
	endpoint := "https://api.github.com/repos/researchos/research/releases"
	complete := sources.Item{CanonicalURL: endpoint + "/tag/prefix-one", UpstreamID: "prefix-one",
		UpstreamRevision: "commit-one", Body: []byte("complete prefix body"),
		MediaType: "text/plain", Locator: "body"}
	page := sources.Page{RawResponse: []byte("rendered page with a gap"), RawMediaType: "application/json",
		HTTPStatus: 200, RequestURLs: []string{endpoint}, FinalURLs: []string{endpoint},
		Items: []sources.Item{complete}, NextCursor: "observed_tail:prefix-one", Failure: "INCOMPLETE_ITEM"}

	capture, e, sourceID := partialPageCapture(t, page)
	if e != nil {
		t.Fatalf("a partially rendered page discarded its verified prefix: %v", e)
	}
	if capture.Page.Failure != "INCOMPLETE_ITEM" {
		t.Fatalf("the gap stopped being recorded: %+v", capture.Page)
	}
	if capture.Page.Complete {
		t.Fatal("a page that stopped at a gap reported exhaustive coverage")
	}
	if capture.Page.NextCursor != "observed_tail:prefix-one" {
		t.Fatalf("resume cursor lost: %q", capture.Page.NextCursor)
	}
	if len(capture.Evidence) != 1 || len(capture.Page.Items) != 1 {
		t.Fatalf("evidence/items pairing broken on a partial page: evidence %d items %d", len(capture.Evidence), len(capture.Page.Items))
	}
	if capture.Page.Items[0].SourceID != sourceID {
		t.Fatalf("sealed item not bound to its configured source: %q vs %q", capture.Page.Items[0].SourceID, sourceID)
	}
	if len(capture.RawArtifact) == 0 || len(capture.Manifest) == 0 {
		t.Fatalf("partial page left raw evidence or manifest unsealed: raw %d manifest %d", len(capture.RawArtifact), len(capture.Manifest))
	}
}

func TestW0702FailedPageWithNothingCompleteStillSealsNothing(t *testing.T) {
	endpoint := "https://api.github.com/repos/researchos/research/releases"
	page := sources.Page{RawResponse: []byte("page whose only article collapsed"), RawMediaType: "application/json",
		HTTPStatus: 200, RequestURLs: []string{endpoint}, FinalURLs: []string{endpoint},
		Items: nil, NextCursor: "observed_tail:none", Failure: "INCOMPLETE_ITEM"}

	capture, e, _ := partialPageCapture(t, page)
	if len(capture.Evidence) != 0 {
		t.Fatalf("a page with nothing complete sealed %d evidence records", len(capture.Evidence))
	}
	if capture.Page.Failure != "INCOMPLETE_ITEM" {
		t.Fatalf("failure reason lost on the empty prefix: %+v", capture.Page)
	}
	if e == nil && len(capture.Manifest) > 0 {
		t.Fatal("an unusable page produced a manifest; the widened path sealed more than intended")
	}
}
