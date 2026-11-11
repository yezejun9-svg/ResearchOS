package main

import (
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync/atomic"
	"testing"
)

func TestGatewayBoundary(t *testing.T) {
	var seen http.Header
	var seenHost string
	calls := 0
	upstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		calls++
		seen = r.Header.Clone()
		seenHost = r.Host
		io.WriteString(w, "allowed")
	}))
	defer upstream.Close()
	handler, e := gateway(upstream.URL, "https://reviewed.trycloudflare.com")
	if e != nil {
		t.Fatal(e)
	}
	test := func(name, method, path string, headers map[string]string, want int) {
		t.Helper()
		t.Run(name, func(t *testing.T) {
			r := httptest.NewRequest(method, "https://reviewed.trycloudflare.com"+path, strings.NewReader(`{}`))
			r.RemoteAddr = "127.0.0.1:54321"
			r.Header.Set("X-Forwarded-Proto", "https")
			r.Header.Set("Origin", "https://reviewed.trycloudflare.com")
			r.Header.Set("Content-Type", "application/json")
			for k, v := range headers {
				if k == "Host" {
					r.Host = v
				} else if k == "RemoteAddr" {
					r.RemoteAddr = v
				} else {
					r.Header.Set(k, v)
				}
			}
			w := httptest.NewRecorder()
			handler.ServeHTTP(w, r)
			if w.Code != want {
				t.Fatalf("status %d want %d: %s", w.Code, want, w.Body.String())
			}
			if w.Header().Get("Referrer-Policy") != "no-referrer" {
				t.Fatal("missing referrer policy")
			}
		})
	}
	test("public-shell", "GET", "/pair", nil, 200)
	test("transport-info", "GET", "/remote-info", nil, 200)
	test("host-rebind", "GET", "/", map[string]string{"Host": "evil.invalid"}, 403)
	test("plaintext-forward", "GET", "/", map[string]string{"X-Forwarded-Proto": "http"}, 403)
	test("forged-forward-chain", "GET", "/", map[string]string{"X-Forwarded-Proto": "https,http"}, 403)
	test("nonloopback-connection", "GET", "/", map[string]string{"RemoteAddr": "192.0.2.10:22"}, 403)
	test("foreign-origin", "POST", "/v1/device-pairings/redeem", map[string]string{"Origin": "https://evil.invalid"}, 403)
	test("origin-null", "POST", "/v1/device-pairings/redeem", map[string]string{"Origin": "null"}, 403)
	test("origin-absent-write", "POST", "/v1/device-pairings/redeem", map[string]string{"Origin": ""}, 403)
	test("cross-site", "POST", "/v1/device-pairings/redeem", map[string]string{"Sec-Fetch-Site": "cross-site"}, 403)
	test("form-csrf", "POST", "/v1/device-pairings/redeem", map[string]string{"Content-Type": "application/x-www-form-urlencoded"}, 403)
	test("admin-denied", "POST", "/v1/device-pairings", nil, 404)
	test("global-denied", "GET", "/v1/policies/run", nil, 404)
	test("missing-auth", "GET", "/v1/projects", nil, 401)
	test("health-denied", "GET", "/healthz", nil, 404)
	test("files-denied", "GET", "/.git/config", nil, 404)
	test("SSE-explicitly-unavailable", "GET", "/v1/projects/p/events/stream", map[string]string{"Authorization": "Bearer fake"}, 404)
	before := calls
	test("valid-proof", "POST", "/v1/device-pairings/redeem", map[string]string{"Cookie": "private-cookie", "CF-Connecting-IP": "198.51.100.3", "X-Forwarded-Host": "evil.invalid"}, 200)
	if calls != before+1 || seen.Get("Cookie") != "" || seen.Get("X-Forwarded-Host") != "" || seen.Get("CF-Connecting-IP") != "" || seen.Get("X-ResearchOS-Remote-Access") != "device" || seenHost != "reviewed.trycloudflare.com" {
		t.Fatal("proxy boundary headers changed")
	}
}

func TestGatewayRejectsAmbiguousSecurityHeaders(t *testing.T) {
	var calls atomic.Int32
	upstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { calls.Add(1); io.WriteString(w, "allowed") }))
	defer upstream.Close()
	handler, err := gateway(upstream.URL, "https://reviewed.trycloudflare.com")
	if err != nil {
		t.Fatal(err)
	}
	for _, test := range []struct{ name, header, value string }{
		{"duplicate-protocol", "X-Forwarded-Proto", "http"},
		{"duplicate-origin", "Origin", "https://evil.invalid"},
		{"duplicate-fetch-site", "Sec-Fetch-Site", "cross-site"},
		{"duplicate-content-type", "Content-Type", "application/x-www-form-urlencoded"},
		{"duplicate-authorization", "Authorization", "Bearer another-identity"},
	} {
		t.Run(test.name, func(t *testing.T) {
			r := httptest.NewRequest("POST", "https://reviewed.trycloudflare.com/v1/device-pairings/redeem", strings.NewReader(`{}`))
			r.RemoteAddr = "127.0.0.1:54321"
			r.Header.Set("X-Forwarded-Proto", "https")
			r.Header.Set("Origin", "https://reviewed.trycloudflare.com")
			r.Header.Set("Sec-Fetch-Site", "same-origin")
			r.Header.Set("Content-Type", "application/json")
			r.Header.Set("Authorization", "Bearer initial-identity")
			r.Header.Add(test.header, test.value)
			before := calls.Load()
			w := httptest.NewRecorder()
			handler.ServeHTTP(w, r)
			if w.Code != 403 || calls.Load() != before {
				t.Fatalf("ambiguous %s: status=%d upstream_calls=%d", test.header, w.Code, calls.Load()-before)
			}
		})
	}
	r := httptest.NewRequest("POST", "https://reviewed.trycloudflare.com/v1/device-pairings/redeem", strings.NewReader(`{}`))
	r.RemoteAddr = "127.0.0.1:54321"
	r.Header.Set("X-Forwarded-Proto", "https")
	r.Header.Set("Origin", "https://reviewed.trycloudflare.com")
	r.Header.Set("Content-Type", "application/json; charset=utf-8")
	w := httptest.NewRecorder()
	handler.ServeHTTP(w, r)
	if w.Code != 200 || calls.Load() != 1 {
		t.Fatalf("single-header positive: status=%d upstream_calls=%d", w.Code, calls.Load())
	}
}
func TestGatewayConfigRejectsUnsafeOrigins(t *testing.T) {
	for _, origin := range []string{"http://public.invalid", "https://*.trycloudflare.com", "https://user:pass@public.invalid", "https://public.invalid/path", "https://public.invalid?secret=1"} {
		if _, e := gateway("http://127.0.0.1:8787", origin); e == nil {
			t.Fatal("unsafe origin accepted")
		}
	}
	for _, upstream := range []string{"http://0.0.0.0:8787", "http://192.0.2.1:8787", "http://localhost:8787", "http://127.0.0.1:8787/path"} {
		if _, e := gateway(upstream, "https://reviewed.trycloudflare.com"); e == nil {
			t.Fatal("unsafe upstream accepted")
		}
	}
}
