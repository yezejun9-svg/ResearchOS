//go:build windows

package runtime

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"testing"
	"time"
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
	firstCapture := qualificationCapture{PID: 42, JobZero: true, Exited: true, StreamsDrained: true, CleanupComplete: true, JobLimitsVerified: true, JobProcessLimit: 16, JobMemoryLimit: 2048 << 20, Stdout: qualificationStream{prefix: []byte("out"), hash: "sha256:out"}, Stderr: qualificationStream{prefix: []byte("err"), hash: "sha256:err"}}
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
	c := qualificationCapture{PID: 42, JobZero: true, Exited: true, StreamsDrained: true, CleanupComplete: true, Stdout: qualificationStream{drained: true, err: errors.New("synthetic final sync failure")}, Stderr: qualificationStream{drained: true}}
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
	if limits.Processes != qualificationProcessLimit || limits.Memory != uint64(qualificationJobMemory) || limits.Flags == 0 {
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
func TestQualificationCollectorOwnedFakeChild(t *testing.T) {
	exe, err := os.Executable()
	if err != nil {
		t.Fatal(err)
	}
	for _, mode := range []string{"small", "overflow"} {
		t.Run(mode, func(t *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
			defer cancel()
			env := append(Environment(""), "RESEARCHOS_QUALIFICATION_FAKE_CHILD="+mode)
			capture := collectQualification(ctx, exe, []string{"-test.run=^TestQualificationFakeChild$"}, env, t.TempDir(), "researchos-qualification-fake-"+mode+"-"+time.Now().Format("150405.000000000"), filepath.Join(t.TempDir(), "receipt"))
			if capture.PID == 0 || !capture.JobZero || !capture.Exited {
				t.Fatal("owned fake child cleanup not proved", capture.PID, capture.JobZero, capture.Exited, capture.Err)
			}
			if mode == "small" && (!capture.StreamsDrained || capture.LimitExceeded || capture.Stdout.hash == "") {
				t.Fatal("small fake stream incomplete", capture)
			}
			if mode == "overflow" && (!capture.LimitExceeded || qualificationCaptureReason(capture) == "") {
				t.Fatal("overflow fake child qualified", capture)
			}
		})
	}
}
