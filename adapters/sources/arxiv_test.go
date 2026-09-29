package sources

import (
	"bytes"
	"context"
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestW07ArxivFullPDFAndVersion(t *testing.T) {
	pdf := append([]byte("%PDF-1.7\n"), bytes.Repeat([]byte("paper full text "), 100)...)
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch r.URL.Path {
		case "/api/query":
			if r.URL.Query().Get("id_list") != "2304.03442v2" {
				t.Errorf("wrong query: %s", r.URL.RawQuery)
			}
			fmt.Fprint(w, `<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"><entry><id>http://arxiv.org/abs/2304.03442v2</id><published>2023-04-07T00:00:00Z</published><updated>2023-07-01T00:00:00Z</updated><author><name>First Author</name></author><author><name>Second Author</name></author></entry></feed>`)
		case "/pdf/2304.03442v2":
			w.Header().Set("Content-Type", "application/pdf")
			w.Write(pdf)
		default:
			http.NotFound(w, r)
		}
	}))
	defer server.Close()
	from, _ := time.Parse(time.RFC3339, "2023-01-01T00:00:00Z")
	to, _ := time.Parse(time.RFC3339, "2026-09-30T00:00:00Z")
	a := &Arxiv{Client: server.Client(), APIURL: server.URL + "/api/query", PDFBaseURL: server.URL + "/pdf", MinInterval: time.Nanosecond}
	p, e := a.Fetch(context.Background(), Query{SourceID: "paper", Text: "id:2304.03442v2", From: from, To: to, Limit: 1})
	if e != nil || p.Failure != "" || !p.Complete || len(p.Items) != 1 {
		t.Fatalf("fetch: %+v %v", p, e)
	}
	item := p.Items[0]
	if item.UpstreamRevision != "2304.03442v2" || item.Author != "First Author, Second Author" || !bytes.Equal(item.Body, pdf) || item.MediaType != "application/pdf" {
		t.Fatalf("item: %+v", item)
	}
}

func TestW07ArxivMetadataCannotPassForFullText(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/api/query" {
			fmt.Fprint(w, `<feed><entry><id>http://arxiv.org/abs/2304.03442v2</id><published>2023-04-07T00:00:00Z</published><updated>2023-07-01T00:00:00Z</updated><author><name>Author</name></author></entry></feed>`)
			return
		}
		w.Header().Set("Content-Type", "application/pdf")
		w.Write([]byte("%PDF-1.7\nmetadata-only prefix"))
	}))
	defer server.Close()
	from, _ := time.Parse(time.RFC3339, "2023-01-01T00:00:00Z")
	to, _ := time.Parse(time.RFC3339, "2026-09-30T00:00:00Z")
	a := &Arxiv{Client: server.Client(), APIURL: server.URL + "/api/query", PDFBaseURL: server.URL + "/pdf", MinInterval: time.Nanosecond}
	p, e := a.Fetch(context.Background(), Query{SourceID: "paper", Text: "id:2304.03442v2", From: from, To: to, Limit: 1})
	if e != nil || p.Failure != "INVALID_FULLTEXT" || len(p.Items) != 0 || p.Complete {
		t.Fatalf("metadata promoted: %+v %v", p, e)
	}
}
