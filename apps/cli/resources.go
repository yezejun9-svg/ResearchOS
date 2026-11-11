package main

import (
	"bytes"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"time"

	"researchos.local/research-os/internal/domain"
)

func init() { commandHandlers["resources"] = runResources }

// Resource commands use the existing resource API, also consumed by the Desktop
// Resources view. Qualification, accounting and the switch transaction stay in
// the shared domain service; this client never launches a worker.
type resourceClient struct {
	base, token, principal string
	client                 http.Client
}

func (c *resourceClient) call(method, path, key, tag string, value any) (domain.Object, error) {
	var raw []byte
	contentType := "application/json"
	if b, ok := value.([]byte); ok {
		raw, contentType = b, "application/octet-stream"
	} else if value != nil {
		raw = domain.Bytes(value)
	}
	req, err := http.NewRequest(method, c.base+path, bytes.NewReader(raw))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Authorization", "Bearer "+c.token)
	req.Header.Set("Content-Type", contentType)
	if key != "" {
		req.Header.Set("Idempotency-Key", key)
	}
	if tag != "" {
		req.Header.Set("If-Match", tag)
	}
	res, err := c.client.Do(req)
	if err != nil {
		return nil, err
	}
	defer res.Body.Close()
	if id := res.Header.Get("X-ResearchOS-Principal-ID"); id != "" {
		c.principal = id
	}
	body, err := io.ReadAll(io.LimitReader(res.Body, 2<<20))
	if err != nil {
		return nil, err
	}
	out, err := domain.Decode(body)
	if err != nil {
		return nil, fmt.Errorf("invalid resource response")
	}
	if res.StatusCode < 200 || res.StatusCode >= 300 {
		return nil, fmt.Errorf("%s: %s", domain.Str(out, "code"), domain.Str(out, "message"))
	}
	return out, nil
}

func resourceTag(o domain.Object) string {
	rev, _ := domain.Num(o, "revision")
	return `"r` + strconv.FormatInt(rev, 10) + `"`
}

func (c *resourceClient) recover(base, requestID, runtimeID, reason string) (domain.Object, error) {
	request, err := c.call("GET", base+"/resource-requests/"+url.PathEscape(requestID), "", "", nil)
	if err != nil {
		return nil, err
	}
	if request["status"] != "OPEN" && request["status"] != "ACKNOWLEDGED" {
		return nil, fmt.Errorf("STATE_CONFLICT: resource request is already closed; read its current state")
	}
	replacement, err := c.call("GET", base+"/runtimes/"+url.PathEscape(runtimeID), "", "", nil)
	if err != nil {
		return nil, err
	}
	items, inputs := domain.Empty(), []any{domain.Ref(request, "ResourceRequest"), domain.Ref(replacement, "RuntimeRegistration")}
	for _, id := range domain.Arr(request, "blocked_task_ids") {
		task, err := c.call("GET", base+"/tasks/"+url.PathEscape(fmt.Sprint(id)), "", "", nil)
		if err != nil {
			return nil, err
		}
		runID := domain.Str(task, "active_run_id")
		if runID == "" {
			return nil, fmt.Errorf("RESOURCE_BLOCKED: task has no resumable run")
		}
		run, err := c.call("GET", base+"/runs/"+url.PathEscape(runID), "", "", nil)
		if err != nil {
			return nil, err
		}
		items = append(items, domain.Object{"task_ref": domain.Ref(task, "Task"), "run_ref": domain.Ref(run, "Run"), "runtime_ref": domain.Ref(replacement, "RuntimeRegistration")})
		inputs = append(inputs, domain.Ref(task, "Task"), domain.Ref(run, "Run"))
	}
	if len(items) == 0 {
		return nil, fmt.Errorf("RESOURCE_BLOCKED: no run is affected by this request")
	}
	action := domain.Object{"schema": domain.ResourceRecoverySchema, "action": "SWITCH_RUNTIME", "resource_request_ref": domain.Ref(request, "ResourceRequest"), "replacements": items}
	raw := domain.Bytes(action)
	key := "recover-" + strings.TrimPrefix(domain.Digest(raw), "sha256:")[:32]
	upload, err := c.call("POST", base+"/content", key+"-content", "", raw)
	if err != nil {
		return nil, err
	}
	state, err := c.call("GET", base+"/state", "", "", nil)
	if err != nil {
		return nil, err
	}
	if c.principal == "" {
		return nil, fmt.Errorf("UNAUTHENTICATED: host did not identify the credential owner")
	}
	artifact, err := c.call("POST", base+"/artifacts", key+"-artifact", resourceTag(state), domain.Object{
		"run_id": nil, "kind": "REPORT", "evidence_kind": "GENERATED", "measurement_mode": replacement["measurement_mode"],
		"content_hash": upload["content_hash"], "storage_key": upload["storage_key"], "media_type": domain.ResourceRecoveryMediaType, "byte_size": len(raw),
		"input_refs": inputs, "source_refs": domain.Empty(), "produced_by": c.principal, "access_class": "PROJECT"})
	if err != nil {
		return nil, err
	}
	resolved, err := c.call("POST", base+"/resource-requests/"+url.PathEscape(requestID)+"/resolve", key+"-resolve", resourceTag(request),
		domain.Object{"resolution_evidence_refs": []any{domain.Ref(artifact, "Artifact")}, "reason": reason})
	if err != nil {
		return nil, err
	}
	return domain.Object{"request": resolved, "recovery_artifact_ref": domain.Ref(artifact, "Artifact"), "effect": "QUALIFIED_RUNTIME_SWITCH_SCHEDULED", "product_acceptance": "NOT_ASSERTED"}, nil
}

func runResources(args []string) {
	if len(args) == 0 || args[0] == "--help" {
		outJSON(map[string]any{"command": "resources", "status": "COMPLETED", "usage": "resources list --project ID | resources recover REQUEST --runtime ID --reason TEXT --project ID"})
		return
	}
	d, _, err := hostDiscovery()
	if err != nil {
		fail("resources", 3, "HOST_UNAVAILABLE")
	}
	cfg, _ := readConfig()
	ctx := newV2Context("resources", args, cfg, d.URL)
	if ctx.projectID == "" {
		fail("resources", 2, "PROJECT_REQUIRED")
	}
	if ctx.credential == "" {
		fail("resources", 3, "CREDENTIAL_ABSENT")
	}
	c := &resourceClient{base: strings.TrimRight(ctx.baseURL, "/"), token: ctx.credential, client: http.Client{Timeout: 30 * time.Second}}
	base := "/v1/projects/" + url.PathEscape(ctx.projectID)
	var out domain.Object
	switch args[0] {
	case "list":
		out, err = c.call("GET", base+"/resource-requests", "", "", nil)
	case "recover":
		if len(args) < 2 || strings.HasPrefix(args[1], "--") {
			fail("resources", 2, "REQUEST_REQUIRED")
		}
		runtimeID, _ := flagValue(args, "runtime")
		reason, _ := flagValue(args, "reason")
		if runtimeID == "" || strings.TrimSpace(reason) == "" {
			fail("resources", 2, "RUNTIME_AND_REASON_REQUIRED")
		}
		out, err = c.recover(base, args[1], runtimeID, reason)
	default:
		fail("resources", 2, "UNKNOWN_RESOURCE_ACTION")
	}
	if err != nil {
		fail("resources", 3, "RESOURCE_RECOVERY_REFUSED", err.Error())
	}
	answer("resources", 0, map[string]any{"status": "COMPLETED", "result": out})
}
