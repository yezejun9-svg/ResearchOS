package sources

import (
	"context"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

func TestW07GitHubReleaseBodyAndCommit(t *testing.T) {
	const sha = "0123456789abcdef0123456789abcdef01234567"
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch {
		case r.URL.Path == "/repos/paperclipai/paperclip/releases":
			if r.URL.Query().Get("page") == "1" {
				fmt.Fprint(w, `[ {"id":22,"html_url":"https://github.com/paperclipai/paperclip/releases/tag/v2","body":"full release body","tag_name":"v2","published_at":"2026-09-29T12:00:00Z","author":{"login":"maintainer"}} ]`)
			} else {
				fmt.Fprint(w, `[]`)
			}
		case r.URL.Path == "/repos/paperclipai/paperclip/commits/v2":
			fmt.Fprintf(w, `{"sha":%q}`, sha)
		default:
			http.NotFound(w, r)
		}
	}))
	defer server.Close()
	from, _ := time.Parse(time.RFC3339, "2026-09-28T00:00:00Z")
	to, _ := time.Parse(time.RFC3339, "2026-09-30T00:00:00Z")
	a := GitHubReleases{BaseURL: server.URL, Client: server.Client()}
	p, e := a.Fetch(context.Background(), Query{SourceID: "github-source", Text: "repo:paperclipai/paperclip", From: from, To: to, Limit: 1})
	if e != nil || p.Failure != "" || len(p.Items) != 1 || p.Complete || p.NextCursor != "2" {
		t.Fatalf("first page: %+v %v", p, e)
	}
	item := p.Items[0]
	if string(item.Body) != "full release body" || item.Author != "maintainer" || item.UpstreamRevision != sha || item.UpstreamID != "22" {
		t.Fatalf("wrong raw item: %+v", item)
	}
	p, e = a.Fetch(context.Background(), Query{SourceID: "github-source", Text: "repo:paperclipai/paperclip", From: from, To: to, Cursor: p.NextCursor, Limit: 1})
	if e != nil || !p.Complete || len(p.Items) != 0 || p.Failure != "" {
		t.Fatalf("last page: %+v %v", p, e)
	}
}

func TestW07GitHubRateLimitAndUnsafeQuery(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { w.Header().Set("Retry-After", "60"); w.WriteHeader(429) }))
	defer server.Close()
	from := time.Now().UTC().Add(-time.Hour)
	to := time.Now().UTC().Add(time.Hour)
	a := GitHubReleases{BaseURL: server.URL, Client: server.Client()}
	p, e := a.Fetch(context.Background(), Query{SourceID: "g", Text: "repo:owner/repo", From: from, To: to, Limit: 1})
	if e != nil || p.Failure != "RATE_LIMITED" || p.RetryAfter == nil || p.Complete || p.NextCursor != "" {
		t.Fatalf("rate limit: %+v %v", p, e)
	}
	_, e = a.Fetch(context.Background(), Query{SourceID: "g", Text: "repo:owner/../evil", From: from, To: to, Limit: 1})
	if e != ErrInvalidQuery {
		t.Fatalf("unsafe repository accepted: %v", e)
	}
	_, e = a.Fetch(context.Background(), Query{SourceID: "g", Text: "repo:" + strings.Repeat("a", 101) + "/repo", From: from, To: to, Limit: 1})
	if e != ErrInvalidQuery {
		t.Fatalf("oversized repository accepted: %v", e)
	}
}
