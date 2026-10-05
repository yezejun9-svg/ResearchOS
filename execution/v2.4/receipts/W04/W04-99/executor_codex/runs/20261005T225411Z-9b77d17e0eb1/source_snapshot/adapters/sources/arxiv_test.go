package sources

import (
	"bytes"
	"context"
	"fmt"
	"net/http"
	"testing"
	"time"
)

func validFixturePDF() []byte {
	var b bytes.Buffer
	b.WriteString("%PDF-1.4\n")
	offsets := []int{0}
	for _, object := range []string{
		"<< /Type /Catalog /Pages 2 0 R >>",
		"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
		"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << >> >>",
		"<< /Length 0 >>\nstream\n\nendstream",
	} {
		offsets = append(offsets, b.Len())
		fmt.Fprintf(&b, "%d 0 obj\n%s\nendobj\n", len(offsets)-1, object)
	}
	b.WriteByte('%')
	b.Write(bytes.Repeat([]byte("x"), 800))
	b.WriteByte('\n')
	xref := b.Len()
	fmt.Fprint(&b, "xref\n0 5\n0000000000 65535 f \n")
	for _, off := range offsets[1:] {
		fmt.Fprintf(&b, "%010d 00000 n \n", off)
	}
	fmt.Fprintf(&b, "trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n", xref)
	return b.Bytes()
}

func TestW07ArxivFullPDFAndVersion(t *testing.T) {
	pdf := validFixturePDF()
	server := sourceFixtureServer(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
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
	a := &Arxiv{Client: server.Client(), APIURL: server.URL + "/api/query", PDFBaseURL: server.URL + "/pdf", AllowedOrigins: []string{server.URL}, MinInterval: time.Nanosecond}
	p, e := a.Fetch(context.Background(), Query{SourceID: "paper", Text: "id:2304.03442v2", From: from, To: to, Limit: 1})
	if e != nil || p.Failure != "" || !p.Complete || len(p.Items) != 1 {
		t.Fatalf("fetch: %+v %v", p, e)
	}
	if len(p.RequestURLs) != 2 || len(p.FinalURLs) != 2 || p.FetchedAt.IsZero() {
		t.Fatal("actual metadata/PDF URL trace missing")
	}
	item := p.Items[0]
	if item.UpstreamRevision != "2304.03442v2" || item.Author != "First Author, Second Author" || !bytes.Equal(item.Body, pdf) || item.MediaType != "application/pdf" {
		t.Fatalf("item: %+v", item)
	}
}

func TestW07ArxivMetadataCannotPassForFullText(t *testing.T) {
	server := sourceFixtureServer(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/api/query" {
			fmt.Fprint(w, `<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>http://arxiv.org/abs/2304.03442v2</id><published>2023-04-07T00:00:00Z</published><updated>2023-07-01T00:00:00Z</updated><author><name>Author</name></author></entry></feed>`)
			return
		}
		w.Header().Set("Content-Type", "application/pdf")
		w.Write([]byte("%PDF-1.7\nmetadata-only prefix"))
	}))
	defer server.Close()
	from, _ := time.Parse(time.RFC3339, "2023-01-01T00:00:00Z")
	to, _ := time.Parse(time.RFC3339, "2026-09-30T00:00:00Z")
	a := &Arxiv{Client: server.Client(), APIURL: server.URL + "/api/query", PDFBaseURL: server.URL + "/pdf", AllowedOrigins: []string{server.URL}, MinInterval: time.Nanosecond}
	p, e := a.Fetch(context.Background(), Query{SourceID: "paper", Text: "id:2304.03442v2", From: from, To: to, Limit: 1})
	if e != nil || p.Failure != "INVALID_FULLTEXT" || len(p.Items) != 0 || p.Complete {
		t.Fatalf("metadata promoted: %+v %v", p, e)
	}
}

func TestW07ArxivChunkedPDFPrefixCannotPass(t *testing.T) {
	server := sourceFixtureServer(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/api/query" {
			fmt.Fprint(w, `<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>http://arxiv.org/abs/2304.03442v2</id><published>2023-04-07T00:00:00Z</published><updated>2023-07-01T00:00:00Z</updated><author><name>Author</name></author></entry></feed>`)
			return
		}
		w.Header().Set("Content-Type", "application/pdf")
		w.Write(append([]byte("%PDF-1.7\n"), bytes.Repeat([]byte("incomplete-page-stream"), 115)...))
	}))
	defer server.Close()
	from, _ := time.Parse(time.RFC3339, "2023-01-01T00:00:00Z")
	to, _ := time.Parse(time.RFC3339, "2026-09-30T00:00:00Z")
	a := &Arxiv{Client: server.Client(), APIURL: server.URL + "/api/query", PDFBaseURL: server.URL + "/pdf", AllowedOrigins: []string{server.URL}, MinInterval: time.Nanosecond}
	p, e := a.Fetch(context.Background(), Query{SourceID: "paper", Text: "id:2304.03442v2", From: from, To: to, Limit: 1})
	if e != nil || p.Failure != "INVALID_FULLTEXT" || p.Complete || len(p.Items) != 0 {
		t.Fatalf("incomplete PDF promoted: %+v %v", p, e)
	}
}

func TestW07ArxivRejectsForeignRedirectBeforeRequest(t *testing.T) {
	foreignHits := 0
	foreign := sourceFixtureServer(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { foreignHits++; w.Write(validFixturePDF()) }))
	defer foreign.Close()
	server := sourceFixtureServer(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/api/query" {
			fmt.Fprint(w, `<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>http://arxiv.org/abs/2304.03442v2</id><published>2023-04-07T00:00:00Z</published><updated>2023-07-01T00:00:00Z</updated><author><name>Author</name></author></entry></feed>`)
			return
		}
		http.Redirect(w, r, foreign.URL+"/pdf", http.StatusFound)
	}))
	defer server.Close()
	from, _ := time.Parse(time.RFC3339, "2023-01-01T00:00:00Z")
	to, _ := time.Parse(time.RFC3339, "2026-09-30T00:00:00Z")
	a := &Arxiv{Client: server.Client(), APIURL: server.URL + "/api/query", PDFBaseURL: server.URL + "/pdf", AllowedOrigins: []string{server.URL}, MinInterval: time.Nanosecond}
	p, e := a.Fetch(context.Background(), Query{SourceID: "paper", Text: "id:2304.03442v2", From: from, To: to, Limit: 1})
	if e != nil || p.Failure != "ORIGIN_DENIED" || p.Complete || foreignHits != 0 {
		t.Fatalf("foreign redirect escaped: %+v %v hits=%d", p, e, foreignHits)
	}
}

func TestW07ArxivErrorPageIsNotValidEmptyFeed(t *testing.T) {
	from, _ := time.Parse(time.RFC3339, "2023-01-01T00:00:00Z")
	to, _ := time.Parse(time.RFC3339, "2026-09-30T00:00:00Z")
	q := Query{SourceID: "paper", Text: "id:2304.03442v2", From: from, To: to, Limit: 1}
	for _, tc := range []struct {
		name, body, failure string
		complete            bool
	}{
		{"html_200", `<html><body>temporary error</body></html>`, "INVALID_RESPONSE", false},
		{"unrelated_xml", `<error>temporary error</error>`, "INVALID_RESPONSE", false},
		{"atom_without_total", `<feed xmlns="http://www.w3.org/2005/Atom"></feed>`, "INVALID_RESPONSE", false},
		{"atom_nonzero_without_entry", `<feed xmlns="http://www.w3.org/2005/Atom" xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/"><opensearch:totalResults>1</opensearch:totalResults></feed>`, "INVALID_RESPONSE", false},
		{"valid_empty", `<feed xmlns="http://www.w3.org/2005/Atom" xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/"><opensearch:totalResults>0</opensearch:totalResults></feed>`, "", true},
	} {
		t.Run(tc.name, func(t *testing.T) {
			server := sourceFixtureServer(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				if r.URL.Path != "/api/query" {
					t.Fatal("unexpected PDF request for empty/error feed")
				}
				fmt.Fprint(w, tc.body)
			}))
			defer server.Close()
			a := &Arxiv{Client: server.Client(), APIURL: server.URL + "/api/query", PDFBaseURL: server.URL + "/pdf", AllowedOrigins: []string{server.URL}, MinInterval: time.Nanosecond}
			p, e := a.Fetch(context.Background(), q)
			if e != nil || p.Failure != tc.failure || p.Complete != tc.complete || len(p.Items) != 0 {
				t.Fatalf("feed classified incorrectly: %+v %v", p, e)
			}
		})
	}
}
