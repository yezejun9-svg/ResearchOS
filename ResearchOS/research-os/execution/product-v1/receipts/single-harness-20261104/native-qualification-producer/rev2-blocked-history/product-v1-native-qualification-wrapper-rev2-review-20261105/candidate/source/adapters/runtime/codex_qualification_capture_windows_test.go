//go:build windows

package runtime

import (
	"bytes"
	"context"
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
	if err := persistQualificationCapture(path, qualificationCapture{PID: 42, JobZero: true, Exited: true, StreamsDrained: true, CleanupComplete: true}, "QUALIFICATION_INCOMPLETE"); err != nil {
		t.Fatal(err)
	}
	first, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	if err = persistQualificationCapture(path, qualificationCapture{}, "PASS"); !errors.Is(err, os.ErrExist) {
		t.Fatal("exclusive receipt replaced", err)
	}
	second, _ := os.ReadFile(path)
	if !bytes.Equal(first, second) {
		t.Fatal("partial evidence overwritten")
	}
}
func TestQualificationJobLimitsBeforeAnyChild(t *testing.T) {
	job, err := qualificationJob("researchos-qualification-fake-" + time.Now().Format("150405.000000000"))
	if err != nil {
		t.Fatal(err)
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
