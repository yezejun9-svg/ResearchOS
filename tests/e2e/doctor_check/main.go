// doctor_check is a standard-library-only, external-binary diagnostic oracle.
// It intentionally imports no candidate CLI code or product test helpers.
package main

import (
	"bytes"
	"context"
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"net"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"
	"time"
)

type object = map[string]any

var layerNames = []string{"host", "directory", "credential", "authentication", "model_catalog", "inference", "tool"}

type assertion struct {
	ID     string   `json:"id"`
	Status string   `json:"status"`
	Reason string   `json:"reason"`
	Cases  []string `json:"cases,omitempty"`
}

type request struct {
	Path              string `json:"path"`
	Method            string `json:"method,omitempty"`
	CorrectCredential bool   `json:"correct_fixture_credential"`
}

type observation struct {
	Name       string        `json:"name"`
	Args       []string      `json:"args"`
	Exit       int           `json:"exit_code"`
	TimedOut   bool          `json:"timed_out"`
	Overflow   bool          `json:"output_overflow"`
	StdoutHash string        `json:"stdout_sha256"`
	StderrHash string        `json:"stderr_sha256"`
	Stdout     string        `json:"stdout_redacted"`
	Stderr     string        `json:"stderr_redacted"`
	Requests   []request     `json:"observed_http_requests"`
	Report     object        `json:"-"`
	ParseError string        `json:"parse_error,omitempty"`
	Leak       bool          `json:"credential_leak"`
	Duration   time.Duration `json:"duration_ns"`
}

type oracle struct {
	binary, candidate, root, token string
	rows                           []assertion
	cases                          []observation
}

func main() {
	binary := flag.String("binary", "", "actual candidate executable")
	candidate := flag.String("candidate-source", "", "candidate repository root (apps/cli must exist)")
	flag.Parse()
	if *binary == "" || *candidate == "" || flag.NArg() != 0 {
		fmt.Fprintln(os.Stderr, "usage: doctor_check --binary <researchos.exe> --candidate-source <repository-root>")
		os.Exit(2)
	}
	exit, err := run(*binary, *candidate)
	if err != nil {
		_ = json.NewEncoder(os.Stdout).Encode(object{"oracle": "researchos.doctor-oracle.v1", "status": "CHECKER_ERROR", "reason": err.Error(), "card_acceptance": "NOT_GRANTED"})
		os.Exit(2)
	}
	os.Exit(exit)
}

func run(binary, candidate string) (int, error) {
	var err error
	binary, err = filepath.Abs(binary)
	if err != nil {
		return 2, err
	}
	candidate, err = filepath.Abs(candidate)
	if err != nil {
		return 2, err
	}
	binaryHash, err := fileHash(binary)
	if err != nil {
		return 2, err
	}
	sources, err := sourceHashes(candidate)
	if err != nil {
		return 2, err
	}
	repo, err := os.Getwd()
	if err != nil {
		return 2, err
	}
	issuePath := filepath.Join(repo, "execution/v2.4/live/w1401/issue_freeze.json")
	issueHash, err := fileHash(issuePath)
	if err != nil {
		return 2, fmt.Errorf("run from oracle repository root: %w", err)
	}
	contractHash, err := fileHash(filepath.Join(repo, "tests/e2e/doctor_check/CONTRACT.md"))
	if err != nil {
		return 2, err
	}
	root, err := os.MkdirTemp("", "researchos-doctor-oracle-")
	if err != nil {
		return 2, err
	}
	defer os.RemoveAll(root)
	var nonce [24]byte
	if _, err = rand.Read(nonce[:]); err != nil {
		return 2, err
	}
	o := &oracle{binary: binary, candidate: candidate, root: root, token: "oracle-fake-" + hex.EncodeToString(nonce[:])}
	started := time.Now().UTC()
	if err = o.check(); err != nil {
		return 2, err
	}
	failed := 0
	for _, row := range o.rows {
		if row.Status == "FAIL" {
			failed++
		}
	}
	verdict, exit := "PASS_IN_DIAGNOSTIC_SCOPE", 0
	if failed > 0 {
		verdict, exit = "FAIL", 1
	}
	report := object{
		"oracle": "researchos.doctor-oracle.v1", "contract_revision": 1,
		"status": verdict, "card_acceptance": "NOT_GRANTED", "full_eight_rows_passed": false,
		"started_at": started.Format(time.RFC3339Nano), "wallclock_ms": time.Since(started).Milliseconds(),
		"binary": binary, "binary_sha256": binaryHash, "candidate_source": candidate, "candidate_cli_source_hashes": sources,
		"issue_freeze_sha256": issueHash, "oracle_contract_sha256": contractHash,
		"oracle_external_provider_calls": 0, "candidate_live_provider_calls": "NOT_MEASURED_BY_DIAGNOSTIC_ORACLE", "fixtures": "loopback HTTP and a local-interface refusal/redirect sink; no external provider endpoint supplied",
		"assertions": o.rows, "observations": o.cases, "failed_assertions": failed,
		"scope_note": "Source and binary identities are captured, not proof of build or product-agent authorship. Fixture wallclock is not LIVE cost accounting. Desktop and remaining W05-03 coverage belong to parent verifier.",
	}
	return exit, json.NewEncoder(os.Stdout).Encode(report)
}

func (o *oracle) check() error {
	missing, err := o.invoke("missing", "", "missing", false, "doctor", "--json")
	if err != nil {
		return err
	}
	closed, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		return err
	}
	staleURL := "http://" + closed.Addr().String()
	closed.Close()
	stale, err := o.invoke("stale", staleURL, "stale", true, "doctor", "--json")
	if err != nil {
		return err
	}
	var checked []observation
	checked = append(checked, missing, stale)
	for _, mode := range []string{"health_only", "auth_denied", "authenticated", "malformed_auth", "wrong_command", "echo_secret"} {
		h, err := newHost("127.0.0.1:0", mode, o.token, "")
		if err != nil {
			return err
		}
		r, callErr := o.invoke(mode, h.url, "fresh", mode != "health_only", "doctor", "--json")
		r.Requests = h.snapshot()
		h.close()
		if callErr != nil {
			return callErr
		}
		checked = append(checked, r)
	}
	byName := map[string]observation{}
	for _, c := range checked {
		byName[c.Name] = c
		o.cases = append(o.cases, c)
	}
	allShape := true
	for _, c := range checked {
		allShape = allShape && validLayers(c)
	}
	health := byName["health_only"]
	o.add("W1401-DOCTOR-JSON-HONOURS-THE-MACHINE-MODE", validLayers(health) && health.Report["command"] == "doctor" && health.Exit != 2, "--json must produce one structured diagnostic with declared layers", "health_only")
	o.add("W1401-DOCTOR-JSON-LAYER-VERDICTS-PRESENT", allShape, "all seven layers require an explicit status and nonempty reason in every supported diagnostic scenario", names(checked)...)
	independent := allShape && layer(health, "host") == "VERIFIED" && layer(health, "credential") != "VERIFIED" && layer(health, "authentication") == "NOT_CHECKED"
	for _, c := range checked {
		independent = independent && layer(c, "directory") == "NOT_CHECKED"
		for _, name := range []string{"model_catalog", "inference", "tool"} {
			independent = independent && layer(c, name) != "VERIFIED"
		}
	}
	denied, auth := byName["auth_denied"], byName["authenticated"]
	independent = independent && layer(denied, "host") == "VERIFIED" && layer(denied, "credential") == "VERIFIED" && layer(denied, "authentication") == "FAILED" && observedAuth(denied)
	independent = independent && layer(auth, "host") == "VERIFIED" && layer(auth, "credential") == "VERIFIED" && layer(auth, "authentication") == "VERIFIED" && observedAuth(auth)
	for _, c := range checked {
		if layer(c, "authentication") != "VERIFIED" {
			independent = independent && layer(c, "inference") == "NOT_CHECKED" && layer(c, "tool") == "NOT_CHECKED"
		}
	}
	o.add("W1401-DOCTOR-JSON-ONE-LAYER-CANNOT-IMPLY-ANOTHER", independent, "liveness, presence, authenticated identity, catalog, inference, tool and directory authorization are separate witnesses", names(checked)...)
	o.add("W1401-DOCTOR-JSON-STALE-DISCOVERY-IS-NOT-CHECKED", validLayers(missing) && validLayers(stale) && missing.Exit == 3 && missing.Report["reason"] == "NOT_FOUND" && stale.Exit == 1 && layer(missing, "host") != "VERIFIED" && layer(stale, "host") != "VERIFIED" && layer(missing, "inference") == "NOT_CHECKED" && layer(stale, "inference") == "NOT_CHECKED" && layer(missing, "tool") == "NOT_CHECKED" && layer(stale, "tool") == "NOT_CHECKED", "missing/stale local discovery cannot verify an inference or tool", "missing", "stale")
	malformed, wrong := byName["malformed_auth"], byName["wrong_command"]
	o.add("W1401-DOCTOR-MALFORMED-AUTH-NOT-VERIFIED", validLayers(malformed) && validLayers(wrong) && layer(malformed, "authentication") == "FAILED" && layer(wrong, "authentication") == "FAILED" && observedAuth(malformed) && observedAuth(wrong), "HTTP 200 with missing typed fields or mismatched command_id must not verify authentication", "malformed_auth", "wrong_command")
	if err = o.unknownFlags(); err != nil {
		return err
	}
	if err = o.compatibility(); err != nil {
		return err
	}
	if err = o.nonlocal(); err != nil {
		return err
	}
	private := true
	for _, c := range o.cases {
		private = private && !c.Leak && !c.Overflow && !c.TimedOut
	}
	o.add("W1401-DOCTOR-NO-CREDENTIAL-DISCLOSURE", private, "no supplied fake credential is printed, including a host response that echoes it; all invocations bounded", names(o.cases)...)
	for _, id := range []string{"W1401-PRODUCT-AGENT-DIFF-IS-NON-EMPTY-AND-REVIEWABLE", "W1401-PROVIDER-COST-AND-WALLCLOCK-RECORDED", "W1401-NO-EXECUTOR-EDITS-PRESENTED-AS-PRODUCT-WORK"} {
		o.rows = append(o.rows, assertion{ID: id, Status: "NOT_CHECKED", Reason: "Requires parent verification of actual production diff/provenance, LIVE ledger and same-session Desktop evidence; diagnostic fixture is insufficient."})
	}
	return nil
}

func (o *oracle) unknownFlags() error {
	ok := true
	var caseNames []string
	for i, args := range [][]string{{"doctor", "--json", "--oracle-unknown"}, {"doctor", "--jsno"}} {
		h, err := newHost("127.0.0.1:0", "authenticated", o.token, "")
		if err != nil {
			return err
		}
		c, e := o.invoke(fmt.Sprintf("unknown_flag_%d", i), h.url, "fresh", true, args...)
		c.Requests = h.snapshot()
		h.close()
		if e != nil {
			return e
		}
		ok = ok && c.Exit == 2 && len(c.Requests) == 0 && c.ParseError == "" && c.Report["command"] == "doctor"
		o.cases = append(o.cases, c)
		caseNames = append(caseNames, c.Name)
	}
	o.add("W1401-DOCTOR-JSON-UNKNOWN-FLAG-REFUSED", ok, "unknown flags exit 2 before any host request and produce a single JSONL refusal", caseNames...)
	return nil
}

func (o *oracle) compatibility() error {
	for _, mode := range []string{"missing", "unhealthy", "health_only"} {
		var h *host
		url := ""
		if mode != "missing" {
			var err error
			h, err = newHost("127.0.0.1:0", mode, o.token, "")
			if err != nil {
				return err
			}
			url = h.url
		}
		c, err := o.invoke("plain_"+mode, url, mode, false, "doctor")
		if h != nil {
			c.Requests = h.snapshot()
			h.close()
		}
		if err != nil {
			return err
		}
		o.cases = append(o.cases, c)
		ok := c.ParseError == "" && !c.TimedOut && !c.Overflow
		id := "W0503-DOCTOR-NOT-FOUND-REFUSES"
		switch mode {
		case "missing":
			ok = ok && c.Exit == 3 && c.Report["reason"] == "NOT_FOUND"
		case "unhealthy":
			id = "W0503-DOCTOR-DOWN-EXIT-1"
			ok = ok && c.Exit == 1 && c.Report["health"] == "DOWN" && c.Report["status"] == "REJECTED" && number(c.Report["http_code"]) == 503
		default:
			id = "W0503-DOCTOR-UP-COMPLETES"
			ok = ok && c.Exit == 0 && c.Report["health"] == "UP" && c.Report["status"] == "COMPLETED"
		}
		o.add(id, ok, "bare doctor preserves accepted W05 JSONL and exit/status behavior", c.Name)
	}
	return nil
}

func (o *oracle) nonlocal() error {
	address, err := localNonLoopback()
	if err != nil {
		return err
	}
	sink, err := newHost(net.JoinHostPort(address, "0"), "authenticated", o.token, "")
	if err != nil {
		return err
	}
	defer sink.close()
	c, err := o.invoke("nonlocal_discovery", sink.url, "fresh", true, "doctor", "--json")
	c.Requests = sink.snapshot()
	if err != nil {
		return err
	}
	o.cases = append(o.cases, c)
	o.add("W1401-DOCTOR-NONLOCAL-DISCOVERY-REFUSED", validLayers(c) && c.Exit != 0 && layer(c, "host") != "VERIFIED" && layer(c, "authentication") != "VERIFIED" && len(c.Requests) == 0, "discovery pointing to a non-loopback address is refused before any HTTP request or credential use", c.Name)
	before := len(sink.snapshot())
	redirect, err := newHost("127.0.0.1:0", "redirect", o.token, sink.url)
	if err != nil {
		return err
	}
	d, err := o.invoke("nonlocal_redirect", redirect.url, "fresh", true, "doctor", "--json")
	d.Requests = redirect.snapshot()
	redirect.close()
	if err != nil {
		return err
	}
	o.cases = append(o.cases, d)
	o.add("W1401-DOCTOR-NONLOCAL-REDIRECT-REFUSED", validLayers(d) && layer(d, "host") != "VERIFIED" && layer(d, "authentication") != "VERIFIED" && len(sink.snapshot()) == before, "a local host cannot redirect the doctor to a nonlocal sink", d.Name)
	return nil
}

func (o *oracle) add(id string, ok bool, reason string, cases ...string) {
	status := "FAIL"
	if ok {
		status = "PASS"
	}
	o.rows = append(o.rows, assertion{ID: id, Status: status, Reason: reason, Cases: cases})
}

func (o *oracle) invoke(name, url, discoveryMode string, credential bool, args ...string) (observation, error) {
	c := observation{Name: name, Args: args, Exit: -1}
	dir := filepath.Join(o.root, name)
	if err := os.MkdirAll(dir, 0700); err != nil {
		return c, err
	}
	discoveryPath := filepath.Join(dir, "discovery.json")
	if discoveryMode != "missing" {
		pid := os.Getpid()
		if discoveryMode == "stale" {
			pid = 2147483647
		}
		raw, _ := json.Marshal(object{"url": url, "pid": pid, "data_dir": dir, "started_at": time.Now().UTC().Format(time.RFC3339Nano), "host_instance_id": "host-012345abcdef"})
		if err := os.WriteFile(discoveryPath, raw, 0600); err != nil {
			return c, err
		}
	}
	configPath := filepath.Join(dir, "config.json")
	if err := os.WriteFile(configPath, []byte(`{}`), 0600); err != nil {
		return c, err
	}
	env := isolatedEnv(dir)
	env = append(env, "RESEARCHOS_CLI_DISCOVERY="+discoveryPath, "RESEARCHOS_CLI_CONFIG="+configPath, "RESEARCHOS_CLI_CLIENT_ID=doctor-oracle")
	if credential {
		env = append(env, "RESEARCHOS_CLI_CREDENTIAL="+o.token)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 8*time.Second)
	defer cancel()
	cmd := exec.CommandContext(ctx, o.binary, args...)
	cmd.Dir, cmd.Env = dir, env
	var stdout, stderr boundedBuffer
	cmd.Stdout, cmd.Stderr = &stdout, &stderr
	cmd.WaitDelay = time.Second
	start := time.Now()
	err := cmd.Run()
	c.Duration, c.TimedOut = time.Since(start), errors.Is(ctx.Err(), context.DeadlineExceeded)
	if cmd.ProcessState != nil {
		c.Exit = cmd.ProcessState.ExitCode()
	}
	if err != nil && cmd.ProcessState == nil {
		return c, fmt.Errorf("candidate failed to start: %w", err)
	}
	a, b := stdout.Bytes(), stderr.Bytes()
	c.Overflow = stdout.overflow || stderr.overflow
	c.Leak = bytes.Contains(a, []byte(o.token)) || bytes.Contains(b, []byte(o.token))
	c.StdoutHash, c.StderrHash = digest(a), digest(b)
	c.Stdout, c.Stderr = strings.ReplaceAll(string(a), o.token, "[REDACTED_FIXTURE_CREDENTIAL]"), strings.ReplaceAll(string(b), o.token, "[REDACTED_FIXTURE_CREDENTIAL]")
	c.Report, err = parseReport(a)
	if err != nil {
		c.ParseError = err.Error()
	}
	return c, nil
}

type boundedBuffer struct {
	bytes.Buffer
	overflow bool
}

func (b *boundedBuffer) Write(p []byte) (int, error) {
	n := len(p)
	remaining := (1 << 20) - b.Len()
	if len(p) > remaining {
		b.overflow = true
		p = p[:remaining]
	}
	_, _ = b.Buffer.Write(p)
	return n, nil
}

func isolatedEnv(dir string) []string {
	var env []string
	allowed := map[string]bool{"SYSTEMROOT": true, "WINDIR": true, "PATH": true, "PATHEXT": true, "COMSPEC": true, "SYSTEMDRIVE": true, "NUMBER_OF_PROCESSORS": true, "PROCESSOR_ARCHITECTURE": true}
	for _, item := range os.Environ() {
		key, _, _ := strings.Cut(item, "=")
		if allowed[strings.ToUpper(key)] {
			env = append(env, item)
		}
	}
	return append(env, "HOME="+dir, "USERPROFILE="+dir, "APPDATA="+dir, "LOCALAPPDATA="+dir, "TEMP="+dir, "TMP="+dir, "NO_COLOR=1", "TERM=dumb")
}

func parseReport(raw []byte) (object, error) {
	trimmed := bytes.TrimSpace(raw)
	if len(bytes.Split(trimmed, []byte("\n"))) != 1 {
		return nil, errors.New("stdout must be one JSONL object")
	}
	var value object
	decoder := json.NewDecoder(bytes.NewReader(trimmed))
	decoder.UseNumber()
	if err := decoder.Decode(&value); err != nil || value == nil {
		return nil, errors.New("stdout is not a JSON object")
	}
	if decoder.Decode(new(any)) != io.EOF {
		return nil, errors.New("stdout has trailing content")
	}
	return value, nil
}

func validLayers(c observation) bool {
	if c.ParseError != "" || c.TimedOut || c.Overflow || c.Report["command"] != "doctor" || strings.TrimSpace(str(c.Report["status"])) == "" || number(c.Report["exit_code"]) != c.Exit {
		return false
	}
	layers, ok := c.Report["layers"].(map[string]any)
	if !ok {
		return false
	}
	for _, name := range layerNames {
		v, ok := layers[name].(map[string]any)
		if !ok {
			return false
		}
		state := str(v["status"])
		if state != "VERIFIED" && state != "FAILED" && state != "NOT_CHECKED" {
			return false
		}
		if strings.TrimSpace(str(v["reason"])) == "" {
			return false
		}
	}
	return true
}

func layer(c observation, name string) string {
	layers, _ := c.Report["layers"].(map[string]any)
	v, _ := layers[name].(map[string]any)
	return str(v["status"])
}
func observedAuth(c observation) bool {
	for _, r := range c.Requests {
		if r.Path == "/v2/command" && r.Method == "host.status" && r.CorrectCredential {
			return true
		}
	}
	return false
}
func names(cases []observation) []string {
	result := make([]string, 0, len(cases))
	for _, c := range cases {
		result = append(result, c.Name)
	}
	return result
}
func str(v any) string { s, _ := v.(string); return s }
func number(v any) int {
	n, ok := v.(json.Number)
	if !ok {
		return -9999
	}
	i, err := n.Int64()
	if err != nil {
		return -9999
	}
	return int(i)
}
func digest(raw []byte) string { sum := sha256.Sum256(raw); return hex.EncodeToString(sum[:]) }
func fileHash(path string) (string, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return "", err
	}
	return digest(raw), nil
}

func sourceHashes(candidate string) ([]object, error) {
	root := filepath.Join(candidate, "apps", "cli")
	var paths []string
	err := filepath.WalkDir(root, func(path string, entry os.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if entry.Type()&os.ModeSymlink != 0 {
			return errors.New("candidate CLI contains a symlink; cannot attest source snapshot")
		}
		if !entry.IsDir() && strings.HasSuffix(path, ".go") {
			paths = append(paths, path)
		}
		return nil
	})
	if err != nil {
		return nil, err
	}
	if len(paths) == 0 {
		return nil, errors.New("candidate apps/cli has no Go source")
	}
	sort.Strings(paths)
	result := make([]object, 0, len(paths))
	for _, path := range paths {
		hash, err := fileHash(path)
		if err != nil {
			return nil, err
		}
		rel, _ := filepath.Rel(candidate, path)
		result = append(result, object{"path": filepath.ToSlash(rel), "sha256": hash})
	}
	return result, nil
}

func localNonLoopback() (string, error) {
	interfaces, err := net.Interfaces()
	if err != nil {
		return "", err
	}
	for _, it := range interfaces {
		if it.Flags&net.FlagUp == 0 || it.Flags&net.FlagLoopback != 0 {
			continue
		}
		addresses, err := it.Addrs()
		if err != nil {
			continue
		}
		for _, address := range addresses {
			ip, _, err := net.ParseCIDR(address.String())
			if err == nil && ip.To4() != nil && !ip.IsLoopback() && !ip.IsUnspecified() {
				return ip.String(), nil
			}
		}
	}
	return "", errors.New("nonlocal refusal fixture needs an IPv4 address of this machine; no external fallback is permitted")
}
