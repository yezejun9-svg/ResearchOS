//go:build windows

package runtime

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"researchos.local/research-os/internal/qualificationprobe"
	"slices"
	"strings"
	"testing"
	"time"

	"golang.org/x/sys/windows"
)

func TestQualificationCaptureBoundsAndExclusiveReceipt(t *testing.T) {
	for _, size := range []int{19, qualificationStreamCap + 1} {
		r, w, err := os.Pipe()
		if err != nil {
			t.Fatal(err)
		}
		out := make(chan qualificationStream, 1)
		partial := filepath.Join(t.TempDir(), "stream.partial")
		go boundedQualificationStream(r, out, partial)
		payload := bytes.Repeat([]byte{'x'}, size)
		written := make(chan error, 1)
		go func() { _, e := w.Write(payload); written <- e; _ = w.Close() }()
		stream := <-out
		if err = <-written; err != nil && size <= qualificationStreamCap {
			t.Fatal(err)
		}
		rawPartial, err := os.ReadFile(partial)
		if err != nil || !bytes.Equal(rawPartial, payload[:min(size, qualificationPrefixCap)]) {
			t.Fatal("durable partial prefix missing", err, len(rawPartial))
		}
		if size < qualificationStreamCap && (!stream.drained || stream.overflow || stream.hash == "") {
			t.Fatal("complete stream lost", stream)
		}
		if size > qualificationStreamCap && (!stream.overflow || len(stream.prefix) != qualificationPrefixCap || stream.hash != "") {
			t.Fatal("overflow claimed full hash", stream.overflow, len(stream.prefix), stream.hash)
		}
	}
	path := filepath.Join(t.TempDir(), "capture.json")
	context := qualificationReceiptContext{TaskID: "task", RunID: "run", Epoch: "1", SourceBindingHash: "sha256:source", NativeHash: "sha256:native", HelperHash: "sha256:helper", HostBuildHash: "sha256:build", TemplateHash: "sha256:template", Nonce: "researchos-readonly-fixed", ExpectedCases: []string{"source_read"}, FindingCodes: []string{"QUALIFICATION_INCOMPLETE"}}
	firstCapture := qualificationCapture{JobZero: true, Exited: true, StreamsDrained: true, CleanupComplete: true, JobLimitsVerified: true, JobProcessLimit: 16, JobMemoryLimit: 2048 << 20, Stdout: qualificationStream{prefix: []byte("out"), hash: "sha256:out"}, Stderr: qualificationStream{prefix: []byte("err"), hash: "sha256:err"}}
	if err := persistQualificationCapture(path, firstCapture, "QUALIFICATION_INCOMPLETE", context); err != nil {
		t.Fatal(err)
	}
	first, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	var fields map[string]json.RawMessage
	if err := json.Unmarshal(first, &fields); err != nil {
		t.Fatal(err)
	}
	for _, key := range []string{"stdout_prefix", "stderr_prefix", "stdout_hash", "stderr_hash", "job_process_limit", "job_memory_limit", "job_limits_verified", "context"} {
		if len(fields[key]) == 0 {
			t.Fatal("terminal receipt omitted", key)
		}
	}
	var bound qualificationReceiptContext
	if err := json.Unmarshal(fields["context"], &bound); err != nil || bound.TaskID != "task" || bound.SourceBindingHash != "sha256:source" || bound.NativeHash != "sha256:native" || bound.TemplateHash != "sha256:template" {
		t.Fatal("terminal receipt lost identity", bound, err)
	}
	if err = persistQualificationCapture(path, qualificationCapture{}, "PASS"); !errors.Is(err, os.ErrExist) {
		t.Fatal("exclusive receipt replaced", err)
	}
	second, _ := os.ReadFile(path)
	if !bytes.Equal(first, second) {
		t.Fatal("partial evidence overwritten")
	}
}
func TestQualificationStreamPersistenceErrorCannotQualify(t *testing.T) {
	requiredFlags := uint32(windows.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE | windows.JOB_OBJECT_LIMIT_ACTIVE_PROCESS | windows.JOB_OBJECT_LIMIT_JOB_MEMORY)
	c := qualificationCapture{PID: 42, JobZero: true, Exited: true, StreamsDrained: true, CleanupComplete: true, JobLimitsVerified: true, JobLimitFlags: requiredFlags, JobProcessLimit: qualificationProcessLimit, JobMemoryLimit: uint64(qualificationJobMemory), Stdout: qualificationStream{drained: true, err: errors.New("synthetic final sync failure")}, Stderr: qualificationStream{drained: true}}
	if reason := qualificationCaptureReason(c); reason == "" {
		t.Fatal("final stream persistence error qualified")
	}
}

type failingQualificationPartial struct{ syncErr, closeErr error }

func (f failingQualificationPartial) Sync() error  { return f.syncErr }
func (f failingQualificationPartial) Close() error { return f.closeErr }
func TestQualificationFinalSyncAndCloseErrorsRevokeHash(t *testing.T) {
	for name, partial := range map[string]failingQualificationPartial{
		"sync":  {syncErr: errors.New("synthetic final sync failure")},
		"close": {closeErr: errors.New("synthetic final close failure")},
	} {
		t.Run(name, func(t *testing.T) {
			stream := qualificationStream{raw: []byte("complete transcript"), drained: true}
			finishQualificationStream(&stream, partial, []byte{1, 2, 3})
			if stream.err == nil || stream.hash != "" || !bytes.Equal(stream.prefix, stream.raw) {
				t.Fatal("failed durable partial claimed complete hash", stream)
			}
		})
	}
}
func TestQualificationJobLimitsBeforeAnyChild(t *testing.T) {
	job, limits, err := qualificationJob("researchos-qualification-fake-" + time.Now().Format("150405.000000000"))
	if err != nil {
		t.Fatal(err)
	}
	flags := uint32(windows.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE | windows.JOB_OBJECT_LIMIT_ACTIVE_PROCESS | windows.JOB_OBJECT_LIMIT_JOB_MEMORY)
	if limits.Processes != qualificationProcessLimit || limits.Memory != uint64(qualificationJobMemory) || limits.Flags != flags {
		t.Fatal("queried Job limits missing", limits)
	}
	defer closeJob(job)
	ids, err := jobPIDs(job)
	if err != nil || len(ids) != 0 {
		t.Fatal("empty limited job unverified", ids, err)
	}
}

// The supervised Go fixture launches only its own test binary in the new Job.
// It never invokes Native, auth, sandbox setup, or a model.
func TestQualificationFakeChild(t *testing.T) {
	switch os.Getenv("RESEARCHOS_QUALIFICATION_FAKE_CHILD") {
	case "small":
		os.Stdout.Write([]byte("synthetic partial diagnostic\n"))
		return
	case "overflow":
		os.Stdout.Write(bytes.Repeat([]byte{'x'}, qualificationStreamCap+8192))
		return
	default:
		return
	}
}
func qualificationFakeCollectorInputs(t *testing.T, mode string) (string, []string, []string, string, string, string, qualificationReceiptContext) {
	t.Helper()
	root := t.TempDir()
	source, working, denied := filepath.Join(root, "S"), filepath.Join(root, "QW"), filepath.Join(root, "D")
	for _, dir := range []string{source, working, denied, filepath.Join(root, "receipts")} {
		if err := os.Mkdir(dir, 0700); err != nil {
			t.Fatal(err)
		}
	}
	helper := filepath.Join(source, "qualification-helper.exe")
	if err := os.WriteFile(helper, []byte("inert helper fixture"), 0600); err != nil {
		t.Fatal(err)
	}
	exe, err := os.Executable()
	if err != nil {
		t.Fatal(err)
	}
	exe, err = filepath.Abs(exe)
	if err != nil {
		t.Fatal(err)
	}
	nativeHash, err := fileDigest(exe)
	if err != nil {
		t.Fatal(err)
	}
	helperHash, err := fileDigest(helper)
	if err != nil {
		t.Fatal(err)
	}
	nonce := "researchos-readonly-0123456789abcdef0123456789abcdef"
	plan := qualificationprobe.Plan{Schema: qualificationprobe.Schema, Source: source, Working: working, Denied: denied, Nonce: nonce, Port: 18888, Cases: qualificationprobe.FixedCases()}
	encoded, err := qualificationprobe.Encode(plan)
	if err != nil {
		t.Fatal(err)
	}
	args, err := qualificationArguments(nonce, source, working, helper, encoded)
	if err != nil {
		t.Fatal(err)
	}
	env := append(Environment(""), "RESEARCHOS_QUALIFICATION_FAKE_CHILD="+mode)
	run, epoch := "run-"+mode+"-"+time.Now().Format("150405.000000000"), "1"
	base := filepath.Join(root, "receipts", strings.TrimPrefix(Hash([]byte(run+"/"+epoch)), "sha256:")+".json")
	receipt := qualificationReceiptContext{TaskID: "task-" + mode, RunID: run, Epoch: epoch, SourceBindingHash: Hash([]byte("inert source binding")), Source: source, Working: working, Denied: denied,
		NativeHash: nativeHash, HelperHash: helperHash, HostBuildHash: Hash([]byte("inert Host build")), TemplateHash: CodexRPCPolicyIdentity(nativeHash).RequestedConfigSHA256,
		EnvironmentHash: Hash(mustJSON(env)), NormalHome: os.Getenv("USERPROFILE"), HostBoot: "0123456789abcdef0123456789abcdef", RenderedArgvHash: Hash(mustJSON(args)), RenderedArgv: append([]string(nil), args...),
		PlanHash: Hash([]byte(encoded)), PlanEncoded: encoded, Nonce: nonce, LoopbackPort: plan.Port, ExpectedCases: qualificationprobe.FixedCases(), PreControlsComplete: true}
	return exe, args, env, working, qualificationJobName(run, epoch, nonce), base, receipt
}

func TestQualificationCollectorOwnedFakeChild(t *testing.T) {
	for _, mode := range []string{"small", "overflow"} {
		t.Run(mode, func(t *testing.T) {
			exe, args, env, cwd, jobName, base, receipt := qualificationFakeCollectorInputs(t, mode)
			ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
			defer cancel()
			capture := collectQualificationWithHooks(ctx, exe, args, env, cwd, jobName, base, receipt, qualificationCollectorHooks{
				launch: func(job windows.Handle, original Command, childEnv []string, stdin, stdout, stderr *os.File) (*process, error) {
					if original.Executable != exe || !slices.Equal(original.Args, args) {
						t.Fatal("collector lost original ordered argv")
					}
					return launch(job, Command{Executable: exe, Args: []string{"-test.run=^TestQualificationFakeChild$"}, Directory: original.Directory}, childEnv, stdin, stdout, stderr)
				},
			})
			if capture.PID == 0 || !capture.JobZero || !capture.Exited {
				t.Fatal("owned fake child cleanup not proved", capture.PID, capture.JobZero, capture.Exited, capture.Err)
			}
			if capture.PrelaunchIntentPath != base+".prelaunch.json" || !qualificationSHA(capture.PrelaunchIntentSHA256) {
				t.Fatal("owned child launched without durable intent", capture.PrelaunchIntentPath, capture.PrelaunchIntentSHA256)
			}
			if mode == "small" && (!capture.StreamsDrained || capture.LimitExceeded || capture.Stdout.hash == "") {
				t.Fatal("small fake stream incomplete", capture)
			}
			if mode == "overflow" && (!capture.LimitExceeded || qualificationCaptureReason(capture) == "") {
				t.Fatal("overflow fake child qualified", capture)
			}
			if err := persistQualificationCapture(base, capture, "QUALIFICATION_INCOMPLETE", receipt); err != nil {
				t.Fatal("final intent linkage", err)
			}
			var final struct {
				PrelaunchIntentSHA256 string `json:"prelaunch_intent_sha256"`
				PrelaunchIntentPath   string `json:"prelaunch_intent_path"`
			}
			raw, err := os.ReadFile(base)
			if err != nil || json.Unmarshal(raw, &final) != nil || final.PrelaunchIntentSHA256 != capture.PrelaunchIntentSHA256 || final.PrelaunchIntentPath != capture.PrelaunchIntentPath {
				t.Fatal("final capture did not link intent", err)
			}
		})
	}
}

type qualificationFaultWriter struct {
	file              *os.File
	short             bool
	syncErr, closeErr error
	order             *[]string
}

func (w *qualificationFaultWriter) Write(raw []byte) (int, error) {
	if w.order != nil {
		*w.order = append(*w.order, "write")
	}
	if w.short {
		return w.file.Write(raw[:min(7, len(raw))])
	}
	return w.file.Write(raw)
}
func (w *qualificationFaultWriter) Sync() error {
	if w.order != nil {
		*w.order = append(*w.order, "sync")
	}
	if err := w.file.Sync(); err != nil {
		return err
	}
	return w.syncErr
}
func (w *qualificationFaultWriter) Close() error {
	if w.order != nil {
		*w.order = append(*w.order, "close")
	}
	return errors.Join(w.file.Close(), w.closeErr)
}

func TestQualificationPrelaunchIntentProvenanceAndMutation(t *testing.T) {
	exe, args, env, cwd, jobName, base, receipt := qualificationFakeCollectorInputs(t, "record")
	flags := uint32(windows.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE | windows.JOB_OBJECT_LIMIT_ACTIVE_PROCESS | windows.JOB_OBJECT_LIMIT_JOB_MEMORY)
	limits := qualificationJobLimits{Flags: flags, Processes: qualificationProcessLimit, Memory: uint64(qualificationJobMemory)}
	record, err := qualificationIntentRecord(exe, args, env, cwd, jobName, base, receipt, limits)
	if err != nil || record.Phase != "PREPARED_INTENT_ONLY" || record.Context.HostBuildHash != receipt.HostBuildHash || record.Context.SourceBindingHash != receipt.SourceBindingHash || !slices.Equal(record.Context.RenderedArgv, args) {
		t.Fatal("typed provenance rejected", record, err)
	}
	path := base + ".prelaunch.json"
	digest, err := persistQualificationPrelaunchIntent(context.Background(), path, record, qualificationCollectorHooks{})
	if err != nil {
		t.Fatal(err)
	}
	raw, err := os.ReadFile(path)
	if err != nil || Hash(raw) != digest || bytes.Contains(raw, []byte("RESEARCHOS_QUALIFICATION_FAKE_CHILD")) || bytes.Contains(raw, []byte("user_request")) {
		t.Fatal("intent leaked raw env/prompt or lost digest", err)
	}
	var decoded qualificationPrelaunchIntent
	if err = json.Unmarshal(raw, &decoded); err != nil || decoded.Schema != "researchos.native-qualification-prelaunch.v1" || decoded.Context.TaskID != receipt.TaskID || decoded.Context.RunID != receipt.RunID || decoded.Context.Epoch != receipt.Epoch || decoded.Context.NativeHash != receipt.NativeHash || decoded.Context.HelperHash != receipt.HelperHash || decoded.Context.TemplateHash != receipt.TemplateHash || decoded.Context.HostBoot != receipt.HostBoot || decoded.Context.Nonce != receipt.Nonce || decoded.Context.LoopbackPort != receipt.LoopbackPort || decoded.Context.PlanHash != receipt.PlanHash || decoded.JobLimitFlags != flags {
		t.Fatal("intent roundtrip lost provenance", decoded, err)
	}
	if _, err = persistQualificationPrelaunchIntent(context.Background(), path, record, qualificationCollectorHooks{}); !errors.Is(err, os.ErrExist) {
		t.Fatal("existing intent overwritten", err)
	}
	second, _ := os.ReadFile(path)
	if !bytes.Equal(raw, second) {
		t.Fatal("existing intent bytes changed")
	}
	mutations := []struct {
		name   string
		change func(*qualificationReceiptContext)
	}{
		{"task", func(r *qualificationReceiptContext) { r.TaskID = "" }},
		{"source binding", func(r *qualificationReceiptContext) { r.SourceBindingHash = Hash([]byte("changed")) }},
		{"source", func(r *qualificationReceiptContext) { r.Source += "-changed" }},
		{"native", func(r *qualificationReceiptContext) { r.NativeHash = Hash([]byte("changed")) }},
		{"helper", func(r *qualificationReceiptContext) { r.HelperHash = Hash([]byte("changed")) }},
		{"Host build", func(r *qualificationReceiptContext) { r.HostBuildHash = "invalid" }},
		{"template", func(r *qualificationReceiptContext) { r.TemplateHash = Hash([]byte("changed")) }},
		{"environment", func(r *qualificationReceiptContext) { r.EnvironmentHash = Hash([]byte("changed")) }},
		{"Host boot", func(r *qualificationReceiptContext) { r.HostBoot = "changed" }},
		{"nonce", func(r *qualificationReceiptContext) { r.Nonce = "changed" }},
		{"port", func(r *qualificationReceiptContext) { r.LoopbackPort++ }},
		{"plan", func(r *qualificationReceiptContext) { r.PlanHash = Hash([]byte("changed")) }},
		{"argv order", func(r *qualificationReceiptContext) {
			r.RenderedArgv[0], r.RenderedArgv[1] = r.RenderedArgv[1], r.RenderedArgv[0]
		}},
	}
	for _, tc := range mutations {
		t.Run(tc.name, func(t *testing.T) {
			changed := receipt
			changed.RenderedArgv = slices.Clone(receipt.RenderedArgv)
			tc.change(&changed)
			if _, err := qualificationIntentRecord(exe, args, env, cwd, jobName, base, changed, limits); err == nil {
				t.Fatal("mutated provenance accepted")
			}
		})
	}
}

func TestQualificationPrelaunchFaultsNeverLaunch(t *testing.T) {
	for _, mode := range []string{"existing", "short", "sync", "close", "readback", "oversize", "marshal", "cancel"} {
		t.Run(mode, func(t *testing.T) {
			exe, args, env, cwd, jobName, base, receipt := qualificationFakeCollectorInputs(t, mode)
			path := base + ".prelaunch.json"
			if mode == "existing" {
				if err := os.WriteFile(path, []byte("existing consumed intent"), 0600); err != nil {
					t.Fatal(err)
				}
			}
			ctx, cancel := context.WithCancel(context.Background())
			defer cancel()
			called := 0
			hooks := qualificationCollectorHooks{launch: func(windows.Handle, Command, []string, *os.File, *os.File, *os.File) (*process, error) {
				called++
				return nil, errors.New("launch spy must not run")
			}}
			if mode == "short" || mode == "sync" || mode == "close" {
				hooks.openIntent = func(name string) (qualificationIntentWriter, error) {
					f, err := os.OpenFile(name, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
					if err != nil {
						return nil, err
					}
					return &qualificationFaultWriter{file: f, short: mode == "short", syncErr: func() error {
						if mode == "sync" {
							return errors.New("synthetic sync fault")
						}
						return nil
					}(), closeErr: func() error {
						if mode == "close" {
							return errors.New("synthetic close fault")
						}
						return nil
					}()}, nil
				}
			}
			if mode == "readback" {
				hooks.readIntent = func(string) ([]byte, error) { return []byte("changed readback"), nil }
			}
			if mode == "oversize" {
				hooks.marshalIntent = func(qualificationPrelaunchIntent) ([]byte, error) {
					return bytes.Repeat([]byte{'x'}, qualificationIntentMaxBytes+1), nil
				}
			}
			if mode == "marshal" {
				hooks.marshalIntent = func(qualificationPrelaunchIntent) ([]byte, error) { return nil, errors.New("synthetic marshal fault") }
			}
			if mode == "cancel" {
				hooks.afterIntentReady = cancel
			}
			capture := collectQualificationWithHooks(ctx, exe, args, env, cwd, jobName, base, receipt, hooks)
			if called != 0 || capture.PID != 0 || capture.Err == nil {
				t.Fatal("prelaunch fault called launch or fabricated PID", mode, called, capture.PID, capture.Err)
			}
			raw, err := os.ReadFile(path)
			if mode == "existing" {
				if err != nil || string(raw) != "existing consumed intent" {
					t.Fatal("existing evidence overwritten", err, string(raw))
				}
			}
			if mode == "short" || mode == "sync" || mode == "close" || mode == "readback" || mode == "cancel" {
				if err != nil || len(raw) == 0 {
					t.Fatal("partial/complete failed intent discarded", mode, err)
				}
			}
			if mode == "oversize" || mode == "marshal" {
				if !errors.Is(err, os.ErrNotExist) {
					t.Fatal("invalid intent unexpectedly opened", mode, err)
				}
			}
		})
	}
}

func TestQualificationPrelaunchQueriedJobDurableBeforeLaunch(t *testing.T) {
	exe, args, env, cwd, jobName, base, receipt := qualificationFakeCollectorInputs(t, "ordering")
	var order []string
	hooks := qualificationCollectorHooks{
		afterJobQueried: func(job windows.Handle, limits qualificationJobLimits) {
			ids, err := jobPIDs(job)
			if err != nil || len(ids) != 0 || limits.Processes != qualificationProcessLimit || limits.Memory != uint64(qualificationJobMemory) {
				t.Fatal("Job not queried and empty before intent", ids, limits, err)
			}
			order = append(order, "job-queried")
		},
		openIntent: func(name string) (qualificationIntentWriter, error) {
			order = append(order, "open-exclusive")
			f, err := os.OpenFile(name, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
			if err != nil {
				return nil, err
			}
			return &qualificationFaultWriter{file: f, order: &order}, nil
		},
		readIntent: func(name string) ([]byte, error) { order = append(order, "readback"); return os.ReadFile(name) },
		launch: func(windows.Handle, Command, []string, *os.File, *os.File, *os.File) (*process, error) {
			order = append(order, "launch-spy")
			return nil, errors.New("inert launch spy")
		},
	}
	capture := collectQualificationWithHooks(context.Background(), exe, args, env, cwd, jobName, base, receipt, hooks)
	want := []string{"job-queried", "open-exclusive", "write", "sync", "close", "readback", "launch-spy"}
	if !slices.Equal(order, want) || capture.PID != 0 || capture.Err == nil || !qualificationSHA(capture.PrelaunchIntentSHA256) {
		t.Fatal("same-Job durable order violated", order, capture.PID, capture.Err)
	}
	if err := persistQualificationCapture(base, qualificationCapture{PID: 42}, "PASS", receipt); err == nil {
		t.Fatal("final-only receipt accepted without intent")
	}
	if err := verifyQualificationFinalIntent(base, capture, receipt); err != nil {
		t.Fatal("valid intent link rejected", err)
	}
	path := base + ".prelaunch.json"
	if err := os.WriteFile(path, []byte("tampered"), 0600); err != nil {
		t.Fatal(err)
	}
	if err := verifyQualificationFinalIntent(base, capture, receipt); err == nil {
		t.Fatal("altered intent still verified")
	}
}
