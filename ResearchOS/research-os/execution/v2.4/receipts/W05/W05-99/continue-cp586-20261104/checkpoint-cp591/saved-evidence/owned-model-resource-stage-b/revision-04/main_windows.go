//go:build windows

package main

import (
	"context"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"net"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"strings"
	"time"
)

type scope struct {
	Schema             string   `json:"schema"`
	Status             string   `json:"status"`
	Owner              string   `json:"owner"`
	BaselineCheckpoint int      `json:"baseline_checkpoint"`
	PriorReviewSHA     string   `json:"prior_rejected_review_sha256"`
	StageAManifestSHA  string   `json:"stage_a_manifest_sha256"`
	ControllerSHA      string   `json:"controller_sha256"`
	SourceManifestSHA  string   `json:"source_manifest_sha256"`
	Endpoint           string   `json:"endpoint"`
	RunRoot            string   `json:"run_root"`
	NativeSeconds      int      `json:"native_seconds"`
	StartupSeconds     int      `json:"startup_seconds"`
	CleanupSeconds     int      `json:"cleanup_seconds"`
	MaxProcesses       int      `json:"max_processes"`
	GETPaths           []string `json:"get_paths"`
	InferenceLimit     int      `json:"inference_limit"`
	OldFailures        string   `json:"old_failure_disposition"`
	ChildHashPolicy    string   `json:"child_image_hash_policy"`
}

func readScope(path, pin string) (scope, error) {
	var s scope
	if !strings.EqualFold(filepath.Clean(path), filepath.Join(stageBRoot, "SCOPE.json")) {
		return s, errors.New("fixed revision-04 scope path required")
	}
	h, e := hashFile(path)
	if e != nil || h != pin || len(pin) != 64 {
		return s, errors.New("reviewed scope SHA required")
	}
	raw, e := os.ReadFile(path)
	if e != nil {
		return s, e
	}
	decoder := json.NewDecoder(strings.NewReader(string(raw)))
	decoder.DisallowUnknownFields()
	if e = decoder.Decode(&s); e != nil {
		return s, e
	}
	if s.Schema != "researchos.owned-ollama-stage-b.v2" || s.Status != "PREPARED_NOT_EXECUTED" || s.Owner != "codex:/root/runtime_readiness" || s.BaselineCheckpoint != 590 || s.PriorReviewSHA != "133d48e1dc460fc218f11c874a0128bf42ce06423cabb52440cf73fe3d812c26" || s.StageAManifestSHA != stageASHA || s.Endpoint != endpoint || !strings.EqualFold(filepath.Clean(s.RunRoot), filepath.Join(stageBRoot, "run-01")) || s.NativeSeconds != 60 || s.StartupSeconds != 30 || s.CleanupSeconds != 15 || s.MaxProcesses != 32 || strings.Join(s.GETPaths, ",") != "/api/version,/api/tags" || s.InferenceLimit != 0 || s.OldFailures != "PRESERVE_ALL_NO_REPLAY_NO_RESET" || s.ChildHashPolicy != "NOT_A_KERNEL_CLEANUP_OR_REQUEST_PREREQUISITE" {
		return s, errors.New("scope invariants differ")
	}
	exe, e := os.Executable()
	if e != nil {
		return s, e
	}
	h, e = hashFile(exe)
	if e != nil || h != s.ControllerSHA {
		return s, errors.New("controller pin differs")
	}
	manifestPath := filepath.Join(stageBRoot, "SOURCE-MANIFEST.json")
	h, e = hashFile(manifestPath)
	if e != nil || h != s.SourceManifestSHA {
		return s, errors.New("source manifest pin differs")
	}
	var m struct {
		Files []struct{ Relative, SHA256 string }
	}
	raw, e = os.ReadFile(manifestPath)
	if e != nil {
		return s, e
	}
	if e = json.Unmarshal(raw, &m); e != nil {
		return s, e
	}
	for _, f := range m.Files {
		p := filepath.Join(stageBRoot, f.Relative)
		if !under(stageBRoot, p) {
			return s, errors.New("source pin escaped")
		}
		h, e = hashFile(p)
		if e != nil || h != f.SHA256 {
			return s, errors.New("source pin differs: " + f.Relative)
		}
	}
	return s, plain(stageBRoot)
}
func metadataGET(ctx context.Context, run, path string, proof connectionProof, counts map[string]int) ([]byte, error) {
	if (path != "/api/version" && path != "/api/tags") || counts[path] != 0 {
		return nil, errors.New("GET path not allowed or consumed")
	}
	transport := &http.Transport{Proxy: nil, DisableKeepAlives: true, DialContext: proof.DialContext}
	defer transport.CloseIdleConnections()
	client := &http.Client{Transport: transport, Timeout: 5 * time.Second, CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}
	req, e := http.NewRequestWithContext(ctx, "GET", endpoint+path, nil)
	if e != nil {
		return nil, e
	}
	req.Header.Set("Accept", "application/json")
	counts[path] = 1
	response, e := client.Do(req)
	if e != nil {
		return nil, e
	}
	defer response.Body.Close()
	raw, e := io.ReadAll(io.LimitReader(response.Body, 65537))
	if e != nil {
		return nil, e
	}
	if len(raw) > 65536 || response.StatusCode != 200 {
		return nil, errors.New("metadata response bound/status mismatch")
	}
	f, e := os.OpenFile(filepath.Join(run, strings.TrimPrefix(path, "/api/")+".response.json"), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if e != nil {
		return nil, e
	}
	_, e = f.Write(raw)
	e = errors.Join(e, f.Sync(), f.Close())
	return raw, e
}
func run(s scope) (result map[string]any, finalErr error) {
	result = map[string]any{"status": "FAILED_OR_BLOCKED", "metadata_get_attempts": map[string]int{"/api/version": 0, "/api/tags": 0}, "controller_inference_requests": 0, "paid_provider_requests": 0, "old_root_writes": 0, "counter_reset": false, "resource_ready": false, "formal_increment": 0}
	if _, e := verifyAssets(); e != nil {
		return result, e
	}
	if e := os.Mkdir(s.RunRoot, 0700); e != nil {
		return result, fmt.Errorf("exclusive one-use run root: %w", e)
	}
	defer func() {
		if finalErr != nil {
			result["error"] = finalErr.Error()
		}
		result["finished_at"] = time.Now().UTC().Format(time.RFC3339Nano)
		finalErr = errors.Join(finalErr, writeNew(filepath.Join(s.RunRoot, "RESULT.json"), result))
	}()
	listener, e := net.Listen("tcp4", "127.0.0.1:43861")
	if e != nil {
		return result, fmt.Errorf("PRELAUNCH_PORT_BLOCKED: %w", e)
	}
	if e = listener.Close(); e != nil {
		return result, e
	}
	env, keys, e := childEnvironment(s.RunRoot)
	if e != nil {
		return result, e
	}
	if e = writeNew(filepath.Join(s.RunRoot, "ENV-KEYS.json"), keys); e != nil {
		return result, e
	}
	stdin, e := os.Open(os.DevNull)
	if e != nil {
		return result, e
	}
	defer stdin.Close()
	outR, outW, e := os.Pipe()
	if e != nil {
		return result, e
	}
	defer outR.Close()
	defer outW.Close()
	errR, errW, e := os.Pipe()
	if e != nil {
		return result, e
	}
	defer errR.Close()
	defer errW.Close()
	stdout, e := startLog(outR, filepath.Join(s.RunRoot, "stdout.raw"))
	if e != nil {
		return result, e
	}
	stderr, e := startLog(errR, filepath.Join(s.RunRoot, "stderr.raw"))
	if e != nil {
		return result, e
	}
	backend := &nativeKernel{exe: filepath.Join(stageARoot, "runtime", "ollama.exe"), cwd: s.RunRoot, env: env, stdio: []*os.File{stdin, outW, errW}}
	owner := startOwner(backend, ownerPolicy{Native: time.Duration(s.NativeSeconds) * time.Second, Cleanup: time.Duration(s.CleanupSeconds) * time.Second})
	defer func() {
		reason := "metadata complete"
		if finalErr != nil {
			reason = finalErr.Error()
		}
		cleanupDeadline := owner.stopOnce(reason)
		// No diagnostic joins precede the owner. Its Job is already closed before
		// this outcome is published. A stuck external diagnostic cannot postpone it.
		var terminal ownerOutcome
		select {
		case terminal = <-owner.out:
		case <-time.After(time.Until(cleanupDeadline)):
			finalErr = errors.Join(finalErr, errors.New("kernel owner terminal outcome missing at shared cleanup deadline; cleanup unproved"))
			return
		}
		result["kernel"] = terminal
		result["cleanup_proved"] = terminal.CleanupProved
		if terminal.Error != "" {
			finalErr = errors.Join(finalErr, errors.New(terminal.Error))
		}
		if !terminal.CleanupProved {
			finalErr = errors.Join(finalErr, errors.New("kernel cleanup unproved"))
		}
		drained := true
		for _, stream := range []*boundedLog{stdout, stderr} {
			remaining := time.Until(terminal.CleanupDeadline)
			if remaining <= 0 {
				drained = false
				continue
			}
			select {
			case e := <-stream.done:
				if e != nil {
					drained = false
				}
			case <-time.After(remaining):
				drained = false
			}
		}
		result["streams_drained"] = drained
		if !drained || stdout.exceeded() || stderr.exceeded() {
			finalErr = errors.Join(finalErr, errors.New("streams/log bound unproved"))
		}
		if canVerifyPostStop(terminal, drained, stdout.exceeded() || stderr.exceeded()) {
			_, e := verifyAssets()
			result["stage_a_assets_unchanged_after_stop"] = e == nil
			finalErr = errors.Join(finalErr, e)
		} else {
			result["stage_a_assets_unchanged_after_stop"] = nil
		}
		if finalErr == nil {
			result["status"] = "METADATA_VERIFIED_OWNED_JOB_CLOSED_ASSETS_UNCHANGED"
		}
	}()
	var primary processRecord
	select {
	case primary = <-owner.started:
	case e := <-owner.startError:
		return result, e
	case <-owner.done:
		return result, errors.New("owner closed before suspended identity")
	case <-time.After(time.Duration(s.NativeSeconds+s.CleanupSeconds) * time.Second):
		return result, errors.New("suspended startup outcome missing")
	}
	// Disk persistence is intentionally outside the kernel owner. While blocked
	// here, the owner still consumes its own timer and closes the private Job.
	if e = writeNew(filepath.Join(s.RunRoot, "SUSPENDED-OWNED-IDENTITY.json"), primary); e != nil {
		return result, e
	}
	ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt)
	defer cancel()
	resumeCtx, stop := context.WithTimeout(ctx, 5*time.Second)
	e = owner.request(resumeCtx, "resume", 0)
	stop()
	if e != nil {
		return result, e
	}
	deadline := time.Now().Add(time.Duration(s.StartupSeconds) * time.Second)
	for !stderr.has("vram-based default context") || !stderr.has("Ollama cloud disabled: true") {
		if stdout.exceeded() || stderr.exceeded() {
			return result, errors.New("raw log bound exceeded")
		}
		select {
		case <-owner.done:
			return result, errors.New("kernel owner stopped during startup")
		case <-ctx.Done():
			return result, ctx.Err()
		case <-time.After(25 * time.Millisecond):
		}
		if time.Now().After(deadline) {
			return result, errors.New("startup marker deadline")
		}
	}
	proof := connectionProof{dial: defaultDial, rows: establishedRows, owned: func(ctx context.Context, pid uint32) error { return owner.request(ctx, "validate", pid) }}
	counts := result["metadata_get_attempts"].(map[string]int)
	raw, e := metadataGET(ctx, s.RunRoot, "/api/version", proof, counts)
	if e != nil {
		return result, e
	}
	var version struct {
		Version string `json:"version"`
	}
	if json.Unmarshal(raw, &version) != nil || version.Version != desiredVersion {
		return result, errors.New("version metadata mismatch")
	}
	raw, e = metadataGET(ctx, s.RunRoot, "/api/tags", proof, counts)
	if e != nil {
		return result, e
	}
	var tags struct {
		Models []struct {
			Name, Digest string
			Size         int64
		}
	}
	if json.Unmarshal(raw, &tags) != nil || len(tags.Models) != 1 || tags.Models[0].Name != modelName || tags.Models[0].Digest != modelSHA || tags.Models[0].Size != 2497293803 {
		return result, errors.New("model metadata mismatch")
	}
	return result, nil
}
func main() {
	execute := flag.Bool("execute", false, "Root only after independent review")
	path := flag.String("scope", filepath.Join(stageBRoot, "SCOPE.json"), "fixed v2 scope")
	pin := flag.String("expected-scope-sha256", "", "exact independently reviewed scope digest")
	flag.Parse()
	if !*execute {
		fmt.Println("PREPARED_NOT_EXECUTED")
		return
	}
	s, e := readScope(*path, *pin)
	if e != nil {
		fmt.Fprintln(os.Stderr, "PRELAUNCH_BLOCKED:", e)
		os.Exit(2)
	}
	r, e := run(s)
	if e != nil {
		fmt.Fprintln(os.Stderr, "FAILED_OR_BLOCKED:", e)
		os.Exit(1)
	}
	b, _ := json.Marshal(map[string]any{"status": r["status"], "resource_ready": false, "controller_inference_requests": 0})
	fmt.Println(string(b))
}
