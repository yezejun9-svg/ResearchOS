package sources

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

type blockedTransport struct{}
func (blockedTransport) RoundTrip(*http.Request) (*http.Response,error) {return nil,context.DeadlineExceeded}

func TestW07GitHubReleaseBodyAndCommit(t *testing.T) {
	const sha = "0123456789abcdef0123456789abcdef01234567"
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch {
		case r.URL.Path == "/repos/paperclipai/paperclip/releases":
			if r.URL.Query().Get("page") == "1" {
				w.Header().Set("Link", `<https://api.github.com/repos/paperclipai/paperclip/releases?page=2>; rel="next"`)
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
	a := GitHubReleases{BaseURL: server.URL, Client: server.Client(), AllowedOrigins: []string{server.URL}}
	p, e := a.Fetch(context.Background(), Query{SourceID: "github-source", Text: "repo:paperclipai/paperclip", From: from, To: to, Limit: 1})
	if e != nil || p.Failure != "" || len(p.Items) != 1 || p.Complete || p.NextCursor != "2" {
		t.Fatalf("first page: %+v %v", p, e)
	}
	if len(p.RequestURLs) != 2 || len(p.FinalURLs) != 2 || p.FetchedAt.IsZero() {
		t.Fatal("actual page/commit URL trace missing")
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
	a := GitHubReleases{BaseURL: server.URL, Client: server.Client(), AllowedOrigins: []string{server.URL}}
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

func TestW07GitHubFaultsDoNotCompleteWindow(t *testing.T) {
	from, _ := time.Parse(time.RFC3339, "2026-09-28T00:00:00Z")
	to, _ := time.Parse(time.RFC3339, "2026-09-30T00:00:00Z")
	const release = `[{"id":22,"html_url":"https://github.com/owner/repo/releases/tag/v2","body":"full body","tag_name":"v2","published_at":"2026-09-29T12:00:00Z","author":{"login":"maintainer"}}]`
	for _, tc := range []struct {
		name, body, link string
		commitStatus     int
		retry            string
		failure          string
	}{
		{"short_page_with_next", release, `<https://api.github.com/next>; rel="next"`, 200, "", ""},
		{"missing_author", strings.Replace(release, `"login":"maintainer"`, `"login":""`, 1), "", 200, "", "INCOMPLETE_ITEM"},
		{"missing_body", strings.Replace(release, `"body":"full body"`, `"body":""`, 1), "", 200, "", "INCOMPLETE_ITEM"},
		{"detail_rate_limit", release, "", 429, "Wed, 30 Sep 2026 12:00:00 GMT", "RATE_LIMITED"},
		{"detail_forbidden", release, "", 403, "", "FORBIDDEN"},
		{"detail_not_found", release, "", 404, "", "NOT_FOUND"},
	} {
		t.Run(tc.name, func(t *testing.T) {
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				if strings.HasSuffix(r.URL.Path, "/releases") {
					if tc.link != "" {
						w.Header().Set("Link", tc.link)
					}
					fmt.Fprint(w, tc.body)
					return
				}
				if tc.retry != "" {
					w.Header().Set("Retry-After", tc.retry)
				}
				w.WriteHeader(tc.commitStatus)
				if tc.commitStatus == 200 {
					fmt.Fprint(w, `{"sha":"0123456789abcdef0123456789abcdef01234567"}`)
				}
			}))
			defer server.Close()
			p, e := (GitHubReleases{BaseURL: server.URL, Client: server.Client(), AllowedOrigins: []string{server.URL}}).Fetch(context.Background(), Query{SourceID: "g", Text: "repo:owner/repo", From: from, To: to, Limit: 20})
			if e != nil || p.Failure != tc.failure || p.Complete && (tc.link != "" || tc.failure != "") {
				t.Fatalf("fault promoted: %+v %v", p, e)
			}
			if tc.link != "" && p.NextCursor != "2" {
				t.Fatal("Link next ignored", p.NextCursor)
			}
			if tc.retry != "" && p.RetryAfter == nil {
				t.Fatal("Retry-After HTTP-date lost")
			}
		})
	}
}

func TestW07GitHubRejectsForeignRedirectBeforeRequest(t *testing.T) {
	foreignHits := 0
	foreign := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { foreignHits++; fmt.Fprint(w, `[]`) }))
	defer foreign.Close()
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		http.Redirect(w, r, foreign.URL+"/elsewhere", http.StatusFound)
	}))
	defer server.Close()
	from, _ := time.Parse(time.RFC3339, "2026-09-28T00:00:00Z")
	to, _ := time.Parse(time.RFC3339, "2026-09-30T00:00:00Z")
	p, e := (GitHubReleases{BaseURL: server.URL, Client: server.Client(), AllowedOrigins: []string{server.URL}}).Fetch(context.Background(), Query{SourceID: "g", Text: "repo:owner/repo", From: from, To: to, Limit: 1})
	if e != nil || p.Failure != "ORIGIN_DENIED" || p.Complete || foreignHits != 0 {
		t.Fatalf("foreign redirect escaped: %+v %v hits=%d", p, e, foreignHits)
	}
}

func TestW07GitHubEmptyAuthAndTimeoutAreDistinct(t *testing.T) {
	from,_:=time.Parse(time.RFC3339,"2026-09-28T00:00:00Z"); to,_:=time.Parse(time.RFC3339,"2026-09-30T00:00:00Z")
	q:=Query{SourceID:"g",Text:"repo:owner/repo",From:from,To:to,Limit:1}
	server:=httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter,r *http.Request) {if r.URL.Query().Get("page")=="1" {fmt.Fprint(w,"[]")}})); defer server.Close()
	a:=GitHubReleases{BaseURL:server.URL,Client:server.Client(),AllowedOrigins:[]string{server.URL}}
	p,e:=a.Fetch(context.Background(),q); if e!=nil || !p.Complete || len(p.Items)!=0 || p.Failure!="" {t.Fatalf("valid empty page classified as failure: %+v %v",p,e)}
	a.Client=&http.Client{Transport:blockedTransport{}}
	p,e=a.Fetch(context.Background(),q); if !errors.Is(e,context.DeadlineExceeded) || p.Failure!="TIMEOUT_OR_NETWORK" || p.Complete {t.Fatalf("timeout lost: %+v %v",p,e)}
	unauthorized:=httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter,r *http.Request) {w.WriteHeader(401)})); defer unauthorized.Close()
	a.BaseURL=unauthorized.URL; a.Client=unauthorized.Client(); a.AllowedOrigins=[]string{unauthorized.URL}
	p,e=a.Fetch(context.Background(),q); if e!=nil || p.Failure!="AUTH_REVOKED" || p.Complete {t.Fatalf("revoked key lost: %+v %v",p,e)}
}
