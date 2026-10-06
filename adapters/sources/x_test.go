package sources

import (
	"context"
	"fmt"
	"strings"
	"testing"
	"time"
)

type fakeXRunner struct {
	calls      [][]string
	truncated  bool
	searchMode string
}

func (f *fakeXRunner) Run(_ context.Context, args ...string) ([]byte, error) {
	f.calls = append(f.calls, append([]string(nil), args...))
	joined := strings.Join(args, " ")
	if strings.Contains(joined, "browser open") || strings.Contains(joined, "session close") || strings.Contains(joined, "navigate ") {
		return []byte("ok"), nil
	}
	if strings.Contains(joined, "emptyState") {
		var searchURL string
		for _, call := range f.calls {
			if len(call) > 0 && strings.Contains(strings.Join(call, " "), "browser open") {
				searchURL = call[len(call)-1]
			}
		}
		if f.searchMode == "empty" {
			return []byte(fmt.Sprintf(`{"url":%q,"items":[],"empty":true}`, searchURL)), nil
		}
		if f.searchMode == "unrendered" {
			return []byte(fmt.Sprintf(`{"url":%q,"items":[],"empty":false}`, searchURL)), nil
		}
		return []byte(fmt.Sprintf(`{"url":%q,"items":[{"url":"https://x.com/public_author/status/2105011808327401690","published_at":"2026-09-29T19:08:18.000Z","text":"search snippet","author":"/public_author"}]}`, searchURL)), nil
	}
	return []byte(fmt.Sprintf(`{"url":"https://x.com/public_author/status/2105011808327401690","items":[{"url":"https://x.com/public_author/status/2105011808327401690","published_at":"2026-09-29T19:08:18.000Z","text":"Complete public post body","author":"/public_author","truncated":%v}]}`, f.truncated)), nil
}

func TestW07XVisibleEmptyDiffersFromUnrendered(t *testing.T) {
	from, _ := time.Parse(time.RFC3339, "2026-09-29T00:00:00Z")
	to, _ := time.Parse(time.RFC3339, "2026-09-30T00:00:00Z")
	q := Query{SourceID: "x", Text: "paperclip agents", From: from, To: to, Limit: 1}
	empty, e := (XBrowser{Runner: &fakeXRunner{searchMode: "empty"}, BrowserID: "existing-authorized-browser"}).Fetch(context.Background(), q)
	if e != nil || empty.Failure != "" || !empty.VisibleEmpty || empty.Complete || len(empty.Items) != 0 || len(empty.RawResponse) == 0 {
		t.Fatalf("valid visible empty misclassified: %+v %v", empty, e)
	}
	unrendered, e := (XBrowser{Runner: &fakeXRunner{searchMode: "unrendered"}, BrowserID: "existing-authorized-browser"}).Fetch(context.Background(), q)
	if e != nil || unrendered.Failure != "UNAVAILABLE" || unrendered.VisibleEmpty || unrendered.Complete {
		t.Fatalf("unrendered page misclassified: %+v %v", unrendered, e)
	}
}

func TestW07XExpandedBodyRequired(t *testing.T) {
	from, _ := time.Parse(time.RFC3339, "2026-09-29T00:00:00Z")
	to, _ := time.Parse(time.RFC3339, "2026-09-30T00:00:00Z")
	p, e := (XBrowser{Runner: &fakeXRunner{truncated: true}, BrowserID: "existing-authorized-browser"}).Fetch(context.Background(), Query{SourceID: "x", Text: "paperclip agents", From: from, To: to, Limit: 1})
	if e != nil || p.Failure != "INCOMPLETE_ITEM" || p.Complete {
		t.Fatalf("collapsed post promoted: %+v %v", p, e)
	}
}

func TestW07XOnlyPublicPostAndNoFalseComplete(t *testing.T) {
	from, _ := time.Parse(time.RFC3339, "2026-09-29T00:00:00Z")
	to, _ := time.Parse(time.RFC3339, "2026-09-30T00:00:00Z")
	runner := &fakeXRunner{}
	a := XBrowser{Runner: runner, BrowserID: "existing-authorized-browser"}
	p, e := a.Fetch(context.Background(), Query{SourceID: "x-source", Text: "paperclip agents", From: from, To: to, Limit: 1})
	if e != nil || p.Failure != "" || len(p.Items) != 1 || p.Complete || p.NextCursor != "" || p.ObservationMarker != "observed_tail:2105011808327401690" {
		t.Fatalf("public post: %+v %v", p, e)
	}
	item := p.Items[0]
	if item.Author != "public_author" || string(item.Body) != "Complete public post body" {
		t.Fatalf("public body: %+v", item)
	}
	for _, call := range runner.calls {
		joined := strings.Join(call, " ")
		if strings.Contains(joined, "network request") || strings.Contains(joined, "get html") || strings.Contains(joined, "cookie") {
			t.Fatalf("private extraction command: %q", joined)
		}
	}
}
