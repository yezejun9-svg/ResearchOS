package sources

// W07-02: X lazy-renders post bodies, so a results page can yield one complete article and then a collapsed one.
// Before this card, the adapter returned on that gap with `return p, nil`, which skipped the post-loop cursor and
// observed-window lines: the caller got a complete item and NO way to say where reading stopped, so a partially
// rendered page could not be resumed and looked identical to an unreadable one.
//
// The behaviour pinned here is the opposite: keep the verified prefix, record the gap, and still report how far the
// window was observed.

import (
	"context"
	"fmt"
	"strings"
	"testing"
	"time"
)

type gapXRunner struct {
	collapseAt int
	searchURL  string
	navigated  string
	calls      [][]string
}

func (g *gapXRunner) candidate(index int) string {
	return fmt.Sprintf(`{"url":"https://x.com/author_%d/status/%d","published_at":"2026-09-29T19:08:%02d.000Z",`+
		`"text":"search snippet","author":"/author_%d"}`, index, 2105011808327401000+index, 10*(index+1), index)
}

func (g *gapXRunner) Run(_ context.Context, args ...string) ([]byte, error) {
	g.calls = append(g.calls, append([]string(nil), args...))
	joined := strings.Join(args, " ")
	switch {
	case strings.Contains(joined, "browser open"):
		g.searchURL = args[len(args)-1]
		return []byte("ok"), nil
	case strings.Contains(joined, "navigate "):
		g.navigated = args[len(args)-1]
		return []byte("ok"), nil
	case strings.Contains(joined, "session close"), strings.HasPrefix(joined, "wait"):
		return []byte("ok"), nil
	case strings.Contains(joined, "emptyState"):
		return []byte(`{"url":"` + g.searchURL + `","items":[` + g.candidate(0) + `,` + g.candidate(1) + `],"empty":false}`), nil
	default:
		// The detail script answers for whichever post the adapter navigated to. The designated candidate comes back
		// collapsed, which is what an unexpanded article looks like on a real page.
		index := 0
		if strings.Contains(g.navigated, "/author_1/") {
			index = 1
		}
		truncated := index == g.collapseAt
		text := "Complete public post body"
		if truncated {
			text = "Collapsed preview only"
		}
		return []byte(fmt.Sprintf(`{"url":%q,"items":[{"url":%q,"published_at":"2026-09-29T19:08:%02d.000Z",`+
			`"text":%q,"author":%q,"truncated":%v}]}`, g.navigated, g.navigated, 10*(index+1), text,
			fmt.Sprintf("/author_%d", index), truncated)), nil
	}
}

func TestW0702XGapKeepsPrefixAndResumeCursor(t *testing.T) {
	from, _ := time.Parse(time.RFC3339, "2026-09-29T00:00:00Z")
	to, _ := time.Parse(time.RFC3339, "2026-09-30T00:00:00Z")
	runner := &gapXRunner{collapseAt: 1}
	p, e := (XBrowser{Runner: runner, BrowserID: "existing-authorized-browser"}).
		Fetch(context.Background(), Query{SourceID: "x-source", Text: "paperclip agents", From: from, To: to, Limit: 5})
	if e != nil {
		t.Fatalf("a collapsed second article became a transport error: %v", e)
	}
	if p.Failure != "INCOMPLETE_ITEM" {
		t.Fatalf("the gap was not recorded: %+v", p.Failure)
	}
	if p.Complete {
		t.Fatal("a page that stopped at a gap claimed exhaustive coverage")
	}
	if len(p.Items) != 1 || string(p.Items[0].Body) != "Complete public post body" {
		t.Fatalf("the verified prefix was discarded instead of kept: %d items", len(p.Items))
	}
	if p.NextCursor != "observed_tail:2105011808327401000" {
		t.Fatalf("no resume cursor after a gap, so the window cannot be补齐: %q", p.NextCursor)
	}
	if p.ObservedFrom == nil || p.ObservedTo == nil {
		t.Fatalf("observed span missing on a partial page: %v %v", p.ObservedFrom, p.ObservedTo)
	}
	if p.RawMediaType != "application/json" || len(p.RawResponse) == 0 {
		t.Fatalf("partial page lost its raw observation: %d bytes", len(p.RawResponse))
	}
	for _, call := range runner.calls {
		if strings.Contains(strings.Join(call, " "), "cookie") {
			t.Fatal("the gap path reached for private state")
		}
	}
}

func TestW0702XGapOnFirstArticleSealsNothingButStillReports(t *testing.T) {
	from, _ := time.Parse(time.RFC3339, "2026-09-29T00:00:00Z")
	to, _ := time.Parse(time.RFC3339, "2026-09-30T00:00:00Z")
	p, e := (XBrowser{Runner: &gapXRunner{collapseAt: 0}, BrowserID: "existing-authorized-browser"}).
		Fetch(context.Background(), Query{SourceID: "x-source", Text: "paperclip agents", From: from, To: to, Limit: 5})
	if e != nil || p.Failure != "INCOMPLETE_ITEM" || len(p.Items) != 0 || p.Complete {
		t.Fatalf("an immediately collapsed page produced a usable-looking result: %+v %v", p, e)
	}
	if p.NextCursor != "" {
		t.Fatalf("a page with nothing complete invented a resume cursor: %q", p.NextCursor)
	}
}
