package main

import (
	"bytes"
	"encoding/json"
	"io"
	"net/http"
	"os"
	"strings"
	"time"
)

func cliDoctor() {
	out, code := doctorReport()
	outJSON(out)
	if code != 0 {
		diag("doctor: %s", out["reason"])
		os.Exit(code)
	}
}

// Doctor reads the host's report; it never qualifies a model or renews a session.
func doctorReport() (out map[string]any, code int) {
	secret := os.Getenv("RESEARCHOS_CLI_CREDENTIAL")
	out = map[string]any{"command": "doctor", "status": "REJECTED", "product": productName,
		"version": buildVersion, "client_protocol": clientProtocol, "health": "NOT_CHECKED",
		"provider_verification": "NOT_CHECKED", "provider_network_called": false, "tool_qualification": "NOT_EVALUATED"}
	defer func() {
		out["exit_code"] = code
		for k, v := range out {
			if s, ok := v.(string); ok {
				if secret != "" {
					s = strings.ReplaceAll(s, secret, "[REDACTED]")
				}
				if len(s) > 512 {
					s = s[:512]
				}
				out[k] = s
			}
		}
	}()
	fail := func(reason string, exit int) (map[string]any, int) { out["reason"] = reason; return out, exit }
	resolved, err := resolveCLIHostDiscovery()
	file, d := resolved.path, resolved.discovery
	out["discovery_path"] = file
	if err != nil {
		out["detail"] = file
		code := 3
		if discoveryErrorCode(err) == "INVALID_LOCAL_URL" {
			code = 2
		}
		return fail(discoveryErrorCode(err), code)
	}
	out["host_url"], out["host_pid"] = d.URL, d.PID
	client := &http.Client{Timeout: 6 * time.Second, CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}
	resp, err := client.Get(strings.TrimSuffix(d.URL, "/") + "/healthz")
	out["health"] = "DOWN"
	if err != nil {
		return fail("HOST_UNREACHABLE", 1)
	}
	raw, readErr := io.ReadAll(io.LimitReader(resp.Body, 8193))
	resp.Body.Close()
	out["http_code"] = resp.StatusCode
	if resp.StatusCode == 401 || resp.StatusCode == 403 {
		return fail("HOST_AUTHORIZATION_BLOCKED", 3)
	}
	if resp.StatusCode != 200 {
		return fail("HOST_HEALTH_FAILED", 1)
	}
	var health map[string]any
	if readErr != nil || len(raw) > 8192 || json.Unmarshal(raw, &health) != nil || (health["status"] != "ready" && health["state"] != "READY") {
		return fail("INVALID_HEALTH_REPLY", 1)
	}
	out["health"] = "UP"
	// Empty configuration prevents newV2Context's first-use renewal branch.
	c := newV2Context("doctor", nil, cliConfig{}, d.URL)
	secret = c.credential
	if secret == "" {
		return fail("CREDENTIAL_ABSENT", 3)
	}
	c.baseURL = strings.TrimSuffix(c.baseURL, "/")
	envelope, refusal := v2EnvelopeFor(c, "host.status", map[string]any{})
	if refusal != "" {
		return fail("INVALID_HOST_STATUS_REQUEST", 2)
	}
	payload, err := json.Marshal(envelope)
	if err != nil {
		return fail("INVALID_HOST_STATUS_REQUEST", 2)
	}
	request, err := http.NewRequest("POST", c.baseURL+v2CommandPath, bytes.NewReader(payload))
	if err != nil {
		return fail("INVALID_HOST_STATUS_REQUEST", 2)
	}
	request.Header.Set("Content-Type", "application/json")
	request.Header.Set("Authorization", "Bearer "+c.credential)
	client.Timeout = 8 * time.Second
	response, err := client.Do(request)
	if err != nil {
		return fail("HOST_STATUS_UNREACHABLE", 1)
	}
	defer response.Body.Close()
	out["http_code"] = response.StatusCode
	// HTTP auth/resource failures remain meaningful even when a gateway emits HTML.
	if response.StatusCode == 401 || response.StatusCode == 403 || response.StatusCode == 404 {
		return fail("HOST_AUTHORIZATION_OR_RESOURCE_BLOCKED", 3)
	}
	if response.StatusCode < 200 || response.StatusCode >= 300 {
		return fail("HOST_STATUS_HTTP_FAILED", 1)
	}
	raw, err = io.ReadAll(io.LimitReader(response.Body, (1<<20)+1))
	if err != nil || len(raw) > 1<<20 {
		return fail("INVALID_HOST_STATUS_REPLY", 1)
	}
	var reply map[string]any
	if json.Unmarshal(raw, &reply) != nil {
		return fail("INVALID_HOST_STATUS_REPLY", 1)
	}
	doc, err := cliProtocolDocument()
	if err != nil || reply == nil || doc.ValidateDef("CommandResponse", reply) != nil {
		return fail("INVALID_HOST_STATUS_REPLY", 1)
	}
	if reply["protocol_version"] != clientProtocol || reply["command_id"] != c.commandID || reply["method"] != "host.status" || reply["session_id"] != nil {
		return fail("HOST_STATUS_IDENTITY_MISMATCH", 1)
	}
	if reply["status"] != "COMPLETED" {
		switch reply["error_code"] {
		case "UNAUTHENTICATED", "FORBIDDEN", "POLICY_DENIED", "NOT_FOUND", "NOT_IMPLEMENTED", "CREDENTIAL_MISSING", "CREDENTIAL_REVOKED", "LEASE_EXPIRED", "RESOURCE_BLOCKED", "MODEL_UNAVAILABLE":
			return fail("HOST_AUTHORIZATION_OR_RESOURCE_BLOCKED", 3)
		}
		return fail("HOST_STATUS_NOT_COMPLETED", 1)
	}
	r, ok := reply["result"].(map[string]any)
	if !ok || doc.ValidateDef("HostStatusResult", r) != nil || r["client_id"] != c.clientID {
		return fail("INVALID_HOST_STATUS_RESULT", 1)
	}
	protocols := r["protocol_versions"].([]any)
	if len(protocols) != 1 || protocols[0] != clientProtocol {
		return fail("UNSUPPORTED_HOST_PROTOCOL", 1)
	}
	out["host_state"], out["operating_mode"], out["config_revision"] = r["host_state"], r["operating_mode"], r["config_revision"]
	for _, key := range []string{"model_configurations", "credentials", "workspaces", "supported_methods"} {
		count := len(r[key].([]any))
		out[key+"_count"] = count
		out[key+"_reporting"] = "REPORTED_BY_HOST"
		if count == 0 {
			out[key+"_reporting"] = "NOT_REPORTED_BY_HOST"
		}
	}
	out["status"] = "COMPLETED"
	return out, 0
}
