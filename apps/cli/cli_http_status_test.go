package main

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strconv"
	"strings"
	"sync/atomic"
	"testing"
	"time"
)

const httpStatusSentinel = "SYNTHETIC_HTTP_STATUS_BEARER_DO_NOT_PRINT"

func httpStatusContext(baseURL string) *v2Context {
	return &v2Context{baseURL: baseURL, clientID: "http-status-client", commandID: "http-status-command", credential: httpStatusSentinel}
}

func TestW05HTTPFailureClassificationAndBodyIsolation(t *testing.T) {
	for _, status := range []int{400, 401, 403, 404, 429, 500, 503, 599} {
		for _, body := range []string{"json", "plain", "oversize"} {
			t.Run(strconv.Itoa(status)+"/"+body, func(t *testing.T) {
				server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
					if r.Method != http.MethodPost || r.URL.Path != v2CommandPath || r.Header.Get("Authorization") != "Bearer "+httpStatusSentinel {
						t.Error("request identity or credential transport changed")
					}
					var env map[string]any
					if json.NewDecoder(r.Body).Decode(&env) != nil || env["command_id"] != "http-status-command" || env["method"] != "host.status" {
						t.Error("original request envelope changed")
					}
					w.WriteHeader(status)
					switch body {
					case "json":
						json.NewEncoder(w).Encode(map[string]any{"status": "COMPLETED", "result": httpStatusSentinel})
					case "plain":
						w.Write([]byte(httpStatusSentinel))
					case "oversize":
						w.Write([]byte(strings.Repeat("x", (1<<20)+1) + httpStatusSentinel))
					}
				}))
				defer server.Close()
				c := httpStatusContext(server.URL)
				reply, reason, code := v2CallContext(context.Background(), c, "host.status", map[string]any{})
				want := exitNotImplemented
				if status >= 500 {
					want = exitFailed
				}
				if code != want || reason != "HOST_HTTP_"+strconv.Itoa(status) || reply != nil || strings.Contains(reason, httpStatusSentinel) {
					t.Fatalf("classification/body isolation: code=%d reason=%q reply=%v", code, reason, reply)
				}
				if len(c.requestLog) != 1 || c.requestLog[0] != "host.status" {
					t.Fatal("request log changed")
				}
			})
		}
	}
}

func TestW05HTTPFailureDoesNotWaitForErrorBody(t *testing.T) {
	for _, status := range []int{401, 500} {
		t.Run(strconv.Itoa(status), func(t *testing.T) {
			releaseBody := make(chan struct{})
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				w.WriteHeader(status)
				w.(http.Flusher).Flush()
				<-releaseBody
				w.Write([]byte(httpStatusSentinel))
			}))
			defer server.Close()
			defer close(releaseBody)
			ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
			defer cancel()
			type outcome struct {
				reply  map[string]any
				reason string
				code   int
			}
			done := make(chan outcome, 1)
			go func() {
				r, why, code := v2CallContext(ctx, httpStatusContext(server.URL), "host.status", map[string]any{})
				done <- outcome{r, why, code}
			}()
			select {
			case got := <-done:
				want := exitNotImplemented
				if status == 500 {
					want = exitFailed
				}
				if got.code != want || got.reason != "HOST_HTTP_"+strconv.Itoa(status) || got.reply != nil {
					t.Fatal("header classification changed", got)
				}
			case <-ctx.Done():
				t.Fatal("waited for error body before classification")
			}
		})
	}
}

func TestW05HTTPRedirectNeverForwardsCredential(t *testing.T) {
	var redirected atomic.Int32
	target := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		redirected.Add(1)
		w.WriteHeader(200)
	}))
	defer target.Close()
	for _, status := range []int{302, 307} {
		t.Run(strconv.Itoa(status), func(t *testing.T) {
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				w.Header().Set("Location", target.URL)
				w.WriteHeader(status)
				w.Write([]byte(httpStatusSentinel))
			}))
			defer server.Close()
			reply, why, code := v2CallContext(context.Background(), httpStatusContext(server.URL), "host.status", map[string]any{})
			if code != exitNotImplemented || why != "HOST_HTTP_"+strconv.Itoa(status) || reply != nil || redirected.Load() != 0 {
				t.Fatal("redirect followed or classification changed")
			}
		})
	}
}

func TestW05HTTP2xxValidationRetained(t *testing.T) {
	for _, mode := range []string{"valid", "protocol", "command", "method", "session", "badjson", "oversize"} {
		t.Run(mode, func(t *testing.T) {
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				if mode == "badjson" {
					w.Write([]byte("not-json"))
					return
				}
				if mode == "oversize" {
					w.Write([]byte(strings.Repeat("x", (1<<20)+1)))
					return
				}
				reply := map[string]any{"protocol_version": clientProtocol, "command_id": "http-status-command", "method": "host.status", "status": "COMPLETED", "session_id": "http-status-session", "revision": 1, "error_code": nil, "error": nil, "result": cliProtocolHostFixture("http-status-client")}
				switch mode {
				case "protocol":
					reply["protocol_version"] = "wrong-protocol"
				case "command":
					reply["command_id"] = "wrong-command"
				case "method":
					reply["method"] = "wrong-method"
				case "session":
					reply["session_id"] = "wrong-session"
				}
				json.NewEncoder(w).Encode(reply)
			}))
			defer server.Close()
			c := httpStatusContext(server.URL)
			c.sessionID = "http-status-session"
			_, why, code := v2CallContext(context.Background(), c, "host.status", map[string]any{})
			if mode == "valid" {
				if code != exitCompleted || why != "" {
					t.Fatal("valid strict reply changed", why, code)
				}
			} else if code != exitFailed || why == "" {
				t.Fatal("malformed or foreign2xx accepted", why, code)
			}
		})
	}
}
