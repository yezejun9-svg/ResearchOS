package sources

import (
	"context"
	"crypto/sha1"
	"encoding/base64"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

func TestW07GitHubReadmePinnedPrimaryBody(t *testing.T) {
	const commit = "0123456789abcdef0123456789abcdef01234567"
	const body = "# Paperclip\nPaperclip manages AI agents for work.\n"
	blob := sha1.Sum([]byte(fmt.Sprintf("blob %d\x00%s", len(body), body)))
	requests := 0
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		requests++
		switch r.URL.Path {
		case "/repos/paperclipai/paperclip/commits":
			if r.URL.Query().Get("path") != "README.md" || r.URL.Query().Get("per_page") != "1" {
				t.Fatal("unbounded README commit lookup")
			}
			fmt.Fprintf(w, `[{"sha":%q,"commit":{"committer":{"date":"2026-09-29T12:00:00Z"}},"author":{"login":"maintainer"}}]`, commit)
		case "/repos/paperclipai/paperclip/readme":
			if r.URL.Query().Get("ref") != commit {
				t.Fatal("README body was not pinned to commit")
			}
			fmt.Fprintf(w, `{"type":"file","encoding":"base64","path":"README.md","content":%q,"size":%d,"sha":"%x"}`, base64.StdEncoding.EncodeToString([]byte(body)), len(body), blob)
		default:
			http.NotFound(w, r)
		}
	}))
	defer server.Close()
	from, _ := time.Parse(time.RFC3339, "2026-09-28T00:00:00Z")
	to, _ := time.Parse(time.RFC3339, "2026-09-30T00:00:00Z")
	a := GitHubReadme{BaseURL: server.URL, Client: server.Client(), AllowedOrigins: []string{server.URL}}
	p, err := a.Fetch(context.Background(), Query{SourceID: "readme", Text: "readme:paperclipai/paperclip", From: from, To: to, Limit: 1})
	if err != nil || p.Failure != "" || !p.Complete || len(p.Items) != 1 || requests != 2 || len(p.RequestURLs) != 2 || len(p.FinalURLs) != 2 {
		t.Fatalf("README capture incomplete: %+v %v requests=%d", p, err, requests)
	}
	item := p.Items[0]
	if string(item.Body) != body || item.UpstreamRevision != commit || item.CanonicalURL != "https://github.com/paperclipai/paperclip/blob/"+commit+"/README.md" || !strings.Contains(string(p.RawResponse), commit) {
		t.Fatalf("unpinned body: %+v", item)
	}
	bad, err := a.Fetch(context.Background(), Query{SourceID: "readme", Text: "readme:paperclipai/paperclip", From: from, To: to, Cursor: "2", Limit: 1})
	if err != ErrInvalidQuery || bad.Complete {
		t.Fatalf("README accepted unrelated cursor: %+v %v", bad, err)
	}
}
