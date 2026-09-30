package domain

import (
	"bytes"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"testing"
)

func resourceEvidence(t *testing.T, name string, value any) {
	t.Helper()
	if dir := os.Getenv("W12_EVIDENCE_DIR"); dir != "" {
		dir = filepath.Join(dir, strings.ReplaceAll(t.Name(), "/", "_"))
		if e := os.MkdirAll(dir, 0700); e != nil {
			t.Fatal(e)
		}
		if e := os.WriteFile(filepath.Join(dir, name), Bytes(value), 0600); e != nil {
			t.Fatal(e)
		}
	}
}
func resourceRedact(v any) any {
	switch o := v.(type) {
	case map[string]any:
		r := Object{}
		for k, v := range o {
			if k == "lease_token" || k == "token" {
				r[k] = "[REDACTED]"
			} else {
				r[k] = resourceRedact(v)
			}
		}
		return r
	case []any:
		a := Empty()
		for _, v := range o {
			a = append(a, resourceRedact(v))
		}
		return a
	}
	return v
}

// Existing fixture request helpers traverse a real loopback HTTP server here.
// The wire content hashes are retained; bearer/lease secrets are redacted.
func resourceHTTP(f *fixture) {
	f.t.Helper()
	evidenceName := "http-" + ID() + ".json"
	var mu sync.Mutex
	events := Empty()
	handler := f.s.Handler()
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		raw, e := io.ReadAll(r.Body)
		if e != nil {
			http.Error(w, e.Error(), 500)
			return
		}
		r.Body = io.NopCloser(bytes.NewReader(raw))
		record := httptest.NewRecorder()
		handler.ServeHTTP(record, r)
		body, _ := Decode(raw)
		reply, _ := Decode(record.Body.Bytes())
		entry := Object{"method": r.Method, "path": r.URL.RequestURI(), "request": resourceRedact(body), "request_sha256": Digest(raw), "if_match": r.Header.Get("If-Match"), "idempotency_key": r.Header.Get("Idempotency-Key"), "status": record.Code, "response": resourceRedact(reply), "response_sha256": Digest(record.Body.Bytes()), "etag": record.Header().Get("ETag")}
		mu.Lock()
		events = append(events, entry)
		mu.Unlock()
		for k, v := range record.Header() {
			w.Header()[k] = v
		}
		w.WriteHeader(record.Code)
		w.Write(record.Body.Bytes())
	}))
	f.t.Cleanup(func() {
		server.Close()
		mu.Lock()
		defer mu.Unlock()
		resourceEvidence(f.t, evidenceName, Object{"transport": "REAL_LOOPBACK_HTTP", "base_url": server.URL, "exchanges": events})
	})
	f.h = http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		req, e := http.NewRequest(r.Method, server.URL+r.URL.RequestURI(), r.Body)
		if e != nil {
			http.Error(w, e.Error(), 500)
			return
		}
		req.Header = r.Header.Clone()
		response, e := server.Client().Do(req)
		if e != nil {
			w.WriteHeader(502)
			w.Write(Bytes(Object{"transport_error": e.Error()}))
			return
		}
		defer response.Body.Close()
		for k, v := range response.Header {
			w.Header()[k] = v
		}
		w.WriteHeader(response.StatusCode)
		io.Copy(w, response.Body)
	})
}
func resourceSnapshot(f *fixture, name string) {
	f.t.Helper()
	rows, e := f.db.Query("SELECT kind,body FROM domain_objects ORDER BY kind,id")
	if e != nil {
		f.t.Fatal(e)
	}
	out := Empty()
	for rows.Next() {
		var kind, raw string
		if e = rows.Scan(&kind, &raw); e != nil {
			f.t.Fatal(e)
		}
		o, e := Decode([]byte(raw))
		if e != nil {
			f.t.Fatal(e)
		}
		out = append(out, Object{"kind": kind, "body": resourceRedact(o)})
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		f.t.Fatal(e)
	}
	resourceEvidence(f.t, name, out)
}
