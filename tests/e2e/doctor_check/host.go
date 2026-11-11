package main

import (
	"encoding/json"
	"net"
	"net/http"
	"strings"
	"sync"
)

type host struct {
	url, mode, token, redirect string
	server                     *http.Server
	mu                         sync.Mutex
	requests                   []request
}

func newHost(address, mode, token, redirect string) (*host, error) {
	listener, err := net.Listen("tcp", address)
	if err != nil {
		return nil, err
	}
	h := &host{url: "http://" + listener.Addr().String(), mode: mode, token: token, redirect: redirect}
	h.server = &http.Server{Handler: http.HandlerFunc(h.handle)}
	go h.server.Serve(listener)
	return h, nil
}

func (h *host) close() { _ = h.server.Close() }
func (h *host) snapshot() []request {
	h.mu.Lock()
	defer h.mu.Unlock()
	return append([]request{}, h.requests...)
}

func (h *host) handle(w http.ResponseWriter, r *http.Request) {
	var env object
	if r.Method == http.MethodPost {
		_ = json.NewDecoder(http.MaxBytesReader(w, r.Body, 64<<10)).Decode(&env)
	}
	correct := r.Header.Get("Authorization") == "Bearer "+h.token
	h.mu.Lock()
	h.requests = append(h.requests, request{Path: r.URL.Path, Method: str(env["method"]), CorrectCredential: correct})
	h.mu.Unlock()
	w.Header().Set("Content-Type", "application/json")
	if h.mode == "redirect" {
		http.Redirect(w, r, h.redirect+r.URL.Path, http.StatusTemporaryRedirect)
		return
	}
	if r.URL.Path == "/healthz" {
		if h.mode == "unhealthy" {
			w.WriteHeader(503)
			_ = json.NewEncoder(w).Encode(object{"state": "NOT_READY"})
			return
		}
		body := object{"state": "READY"}
		if h.mode == "echo_secret" {
			body["untrusted_echo"] = h.token
			body["inference"] = "VERIFIED"
			body["tool"] = "VERIFIED"
		}
		_ = json.NewEncoder(w).Encode(body)
		return
	}
	if r.URL.Path != "/v2/command" || r.Method != http.MethodPost {
		w.WriteHeader(404)
		_ = json.NewEncoder(w).Encode(object{"error": "NOT_FOUND"})
		return
	}
	if !correct || h.mode == "auth_denied" {
		w.WriteHeader(401)
		_ = json.NewEncoder(w).Encode(reply(env, "REJECTED", nil, "UNAUTHENTICATED"))
		return
	}
	if env["protocol_version"] != "researchos-client/2" || strings.TrimSpace(str(env["command_id"])) == "" || strings.TrimSpace(str(env["client_id"])) == "" {
		w.WriteHeader(400)
		_ = json.NewEncoder(w).Encode(reply(env, "REJECTED", nil, "INVALID_REQUEST"))
		return
	}
	if env["method"] != "host.status" {
		_ = json.NewEncoder(w).Encode(reply(env, "NOT_IMPLEMENTED", nil, "NOT_IMPLEMENTED"))
		return
	}
	if h.mode == "malformed_auth" {
		_ = json.NewEncoder(w).Encode(object{"status": "COMPLETED", "result": object{"authenticated_principal_ref": "principal:fixture"}})
		return
	}
	result := object{
		"host_instance_id": "host-012345abcdef", "core_build_id": "oracle-fixture-build", "protocol_versions": []string{"researchos-client/2"}, "host_state": "READY",
		"client_id": env["client_id"], "authenticated_principal_ref": "principal:fixture-authenticated", "config_revision": 0,
		"model_configurations": []any{}, "credentials": []any{}, "workspaces": []any{}, "supported_methods": []string{"host.status"}, "operating_mode": "LOCAL_USER_HOST",
	}
	response := reply(env, "COMPLETED", result, "")
	if h.mode == "wrong_command" {
		response["command_id"] = "not-the-requested-command"
	}
	_ = json.NewEncoder(w).Encode(response)
}

func reply(env object, status string, result any, code string) object {
	var errorCode, detail any
	if code != "" {
		errorCode = code
		detail = object{"message": "fixture refusal", "retryable": false, "recovery_action": "FIX_REQUEST", "details": object{}}
	}
	return object{"protocol_version": "researchos-client/2", "command_id": env["command_id"], "method": env["method"], "status": status, "session_id": nil, "revision": nil, "result": result, "error_code": errorCode, "error": detail}
}
