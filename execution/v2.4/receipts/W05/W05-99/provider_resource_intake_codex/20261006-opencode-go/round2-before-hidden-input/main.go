//go:build windows

// Authorized resource intake through the existing host credential boundary.
// No product Task/Run, current host, historical effect or qualification is changed.
package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"

	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/host"
	"researchos.local/research-os/internal/store"
)

const baseURL = "https://opencode.ai/zen/go/v1"
const modelID = "deepseek-v4.1-flash"
const providerID = "opencode-go"

func save(dir, name string, value any) error {
	raw, err := json.MarshalIndent(value, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(filepath.Join(dir, name), append(raw, '\n'), 0600)
}

func zero(raw []byte) {
	for i := range raw {
		raw[i] = 0
	}
}

func request(ctx context.Context, client *http.Client, method, path string, body []byte, key []byte, session string) ([]byte, int, error) {
	req, err := http.NewRequestWithContext(ctx, method, baseURL+path, bytes.NewReader(body))
	if err != nil {
		return nil, 0, err
	}
	req.Header.Set("Authorization", "Bearer "+string(key))
	req.Header.Set("User-Agent", "ResearchOS/2.4 (+authorized-resource-intake)")
	req.Header.Set("x-opencode-session", session)
	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}
	resp, err := client.Do(req)
	if err != nil {
		return nil, 0, err
	}
	defer resp.Body.Close()
	// Refusal bodies are untrusted and are never persisted or printed.
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return nil, resp.StatusCode, nil
	}
	raw, err := io.ReadAll(io.LimitReader(resp.Body, 1048577))
	if err != nil {
		return nil, resp.StatusCode, err
	}
	if len(raw) > 1048576 || bytes.Contains(raw, key) {
		return nil, resp.StatusCode, fmt.Errorf("UNSAFE_OR_OVERSIZED_RESPONSE")
	}
	return raw, resp.StatusCode, nil
}

func run() error {
	if len(os.Args) != 4 {
		return fmt.Errorf("EXPECTED_REPO_PRIVATE_ROOT_RECEIPT_ROOT")
	}
	repo, private, receipt := os.Args[1], os.Args[2], os.Args[3]
	if _, err := os.Stat(private); !os.IsNotExist(err) {
		return fmt.Errorf("PRIVATE_ROOT_MUST_BE_NEW")
	}
	if err := os.MkdirAll(private, 0700); err != nil {
		return err
	}
	db, err := store.Open(filepath.Join(private, "researchos.sqlite"))
	if err != nil {
		return err
	}
	defer db.Close()
	if err := store.Bootstrap(context.Background(), db, filepath.Join(repo, "migrations/sqlite/0001_bootstrap.sql")); err != nil {
		return err
	}
	h, err := host.New(host.Config{DB: db, Dir: filepath.Join(private, "host"), ContractsDir: filepath.Join(repo, "spec/v2.0/contracts"), MigrationFile: filepath.Join(repo, "migrations/sqlite/0002_domain.sql"), SchemaDir: filepath.Join(repo, "internal/api/contracts")})
	if err != nil {
		return err
	}
	input, err := bufio.NewReader(io.LimitReader(os.Stdin, 4097)).ReadBytes('\n')
	if err != nil {
		zero(input)
		return fmt.Errorf("CREDENTIAL_INPUT_UNAVAILABLE")
	}
	defer zero(input)
	input = bytes.TrimRight(input, "\r\n")
	ref, err := h.ImportCredential(providerID, "API_KEY", string(input), "")
	if err != nil {
		return fmt.Errorf("PROTECTED_IMPORT_REFUSED")
	}
	zero(input)
	route := domain.RuntimeProviderRoute{CredentialRef: ref, CredentialRevision: ref, ModelConfig: domain.Object{"provider": providerID}}
	key, err := h.ModelCredential(context.Background(), route)
	if err != nil {
		return fmt.Errorf("PROTECTED_CREDENTIAL_RESOLUTION_REFUSED")
	}
	defer zero(key)
	session := "aede0678-7308-43dc-b9f2-cfe3d90cfdfb:opencode-go-resource-20261006"
	status := map[string]any{"schema": "researchos.authorized-provider-resource.v1", "provider_id": providerID, "base_url": baseURL, "preferred_model": modelID, "credential_ref": ref, "credential_status": h.CredentialStatus(ref), "private_host_root": private, "protected_existing_host_api": true, "plaintext_saved_in_receipts": false, "cost": nil, "formal_acceptance_delta": 0, "product_task_run_created": false, "old_unknown_retried": false, "session_header": session, "user_agent": "ResearchOS/2.4 (+authorized-resource-intake)", "at": time.Now().UTC().Format(time.RFC3339Nano)}
	if err := save(receipt, "credential-intake.json", status); err != nil {
		return err
	}
	client := &http.Client{Timeout: 45 * time.Second, CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}
	ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
	defer cancel()
	raw, httpStatus, err := request(ctx, client, "GET", "/models", nil, key, session)
	status["catalog_http_status"] = httpStatus
	if err != nil {
		status["catalog_error"] = "TRANSPORT_OR_RESPONSE_ERROR"
		_ = save(receipt, "result.json", status)
		return fmt.Errorf("CATALOG_FAILED")
	}
	if httpStatus != 200 {
		_ = save(receipt, "result.json", status)
		return fmt.Errorf("CATALOG_HTTP_%d", httpStatus)
	}
	var catalog struct {
		Data []struct {
			ID string `json:"id"`
		} `json:"data"`
	}
	if err := json.Unmarshal(raw, &catalog); err != nil {
		return fmt.Errorf("CATALOG_JSON_INVALID")
	}
	found := false
	for _, item := range catalog.Data {
		if item.ID == modelID {
			found = true
		}
	}
	status["catalog_model_count"] = len(catalog.Data)
	status["preferred_model_listed"] = found
	if err := os.WriteFile(filepath.Join(receipt, "models.response.json"), raw, 0600); err != nil {
		return err
	}
	if !found {
		_ = save(receipt, "result.json", status)
		return fmt.Errorf("PREFERRED_MODEL_NOT_LISTED")
	}
	// One bounded coding request checks actual authorized access; it is not runtime qualification.
	body, err := json.Marshal(map[string]any{"model": modelID, "max_tokens": 128, "stream": false, "messages": []map[string]string{{"role": "user", "content": "ResearchOS implements a Go URL validator for model provider configuration. Review this expression: u.Scheme == \"https\" && u.Host != \"\" && u.User == nil && u.RawQuery == \"\" && u.Fragment == \"\". Name one missing check, in one short sentence. Do not call tools."}}})
	if err != nil {
		return err
	}
	if err := os.WriteFile(filepath.Join(receipt, "probe.request.json"), body, 0600); err != nil {
		return err
	}
	probeContext, stop := context.WithTimeout(context.Background(), 60*time.Second)
	defer stop()
	probe, code, err := request(probeContext, client, "POST", "/chat/completions", body, key, session)
	status["probe_http_status"] = code
	status["actual_model_requests"] = 1
	status["automatic_retries"] = 0
	if err != nil {
		status["probe_error"] = "TRANSPORT_OR_RESPONSE_ERROR"
		_ = save(receipt, "result.json", status)
		return fmt.Errorf("PROBE_FAILED")
	}
	if code < 200 || code >= 300 {
		_ = save(receipt, "result.json", status)
		return fmt.Errorf("PROBE_HTTP_%d", code)
	}
	var answer struct {
		Model   string `json:"model"`
		Choices []struct {
			Message struct {
				Content string `json:"content"`
			} `json:"message"`
			FinishReason string `json:"finish_reason"`
		} `json:"choices"`
		Usage json.RawMessage `json:"usage"`
	}
	if err := json.Unmarshal(probe, &answer); err != nil {
		return fmt.Errorf("PROBE_JSON_INVALID")
	}
	status["actual_response_model"] = answer.Model
	status["usage"] = answer.Usage
	status["coding_response_received"] = len(answer.Choices) > 0 && strings.TrimSpace(answer.Choices[0].Message.Content) != ""
	if err := os.WriteFile(filepath.Join(receipt, "probe.response.json"), probe, 0600); err != nil {
		return err
	}
	if err := save(receipt, "result.json", status); err != nil {
		return err
	}
	if status["coding_response_received"] != true {
		return fmt.Errorf("PROBE_NO_VISIBLE_ANSWER")
	}
	fmt.Println("PROTECTED_CREDENTIAL_IMPORTED CATALOG_OK PREFERRED_MODEL_CODE_RESPONSE_RECEIVED")
	return nil
}

func main() {
	if err := run(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
