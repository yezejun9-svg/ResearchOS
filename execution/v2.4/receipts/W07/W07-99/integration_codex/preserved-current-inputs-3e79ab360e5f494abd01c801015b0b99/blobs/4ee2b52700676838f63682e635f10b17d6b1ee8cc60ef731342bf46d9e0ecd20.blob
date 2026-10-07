package sources

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestW07PRDetailStatesAndIndexRejection(t *testing.T) {
	for _, tc := range []struct {
		name, state string
		merged      bool
		mergedAt    any
		want        string
	}{{"open", "open", false, nil, "OPEN"}, {"closed_unmerged", "closed", false, nil, "CLOSED"}, {"merged", "closed", true, "2026-01-02T00:00:00Z", "MERGED"}, {"contradictory", "open", true, "2026-01-02T00:00:00Z", ""}, {"missing_merge_time", "closed", true, nil, ""}} {
		t.Run(tc.name, func(t *testing.T) {
			srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				if r.URL.Path != "/repos/owner/repo/pulls/7" {
					t.Error(r.URL)
				}
				json.NewEncoder(w).Encode(map[string]any{"id": 77, "number": 7, "html_url": "https://github.com/owner/repo/pull/7", "state": tc.state, "merged": tc.merged, "merged_at": tc.mergedAt, "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-02T00:00:00Z", "body": "Original authored PR body", "user": map[string]any{"login": "owner"}, "head": map[string]any{"sha": "0123456789abcdef0123456789abcdef01234567"}, "merge_commit_sha": "1123456789abcdef0123456789abcdef01234567"})
			}))
			defer srv.Close()
			q := Query{SourceID: "source", Text: "pr:owner/repo/7", From: time.Date(2026, 1, 1, 0, 0, 0, 0, time.UTC), To: time.Date(2026, 1, 3, 0, 0, 0, 0, time.UTC), Limit: 1}
			p, e := (GitHubPR{BaseURL: srv.URL, AllowedOrigins: []string{srv.URL}}).Fetch(context.Background(), q)
			if e != nil {
				t.Fatal(e)
			}
			if tc.want == "" {
				if p.Complete || len(p.Items) > 0 || p.Failure == "" {
					t.Fatal(p)
				}
			} else if len(p.Items) != 1 || p.Items[0].PRState != tc.want || p.Items[0].ReadLevel != "BODY" {
				t.Fatal(p)
			}
		})
	}
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { w.Write([]byte(`{"items":[{"body":"index snippet"}]}`)) }))
	defer srv.Close()
	q := Query{SourceID: "source", Text: "pr:owner/repo/7", From: time.Now().Add(-time.Hour), To: time.Now(), Limit: 1}
	p, e := (GitHubPR{BaseURL: srv.URL, AllowedOrigins: []string{srv.URL}}).Fetch(context.Background(), q)
	if e != nil || p.Complete || len(p.Items) > 0 || p.Failure != "INVALID_PR_DETAIL" {
		t.Fatal(p, e)
	}
	p, e = (GitHubPR{BaseURL: srv.URL, AllowedOrigins: []string{"https://api.github.com"}}).Fetch(context.Background(), q)
	if e != nil || p.Failure != "ORIGIN_DENIED" {
		t.Fatal(p, e)
	}
}
