//go:build windows

package runtime

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"io"
	"os"
	"strings"
	"time"
	"unsafe"

	"golang.org/x/sys/windows"
)

const qualificationStreamCap = 1 << 20
const qualificationPrefixCap = 64 << 10
const qualificationProcessLimit = 16
const qualificationJobMemory = uintptr(2048 << 20)

type qualificationStream struct {
	raw      []byte
	prefix   []byte
	hash     string
	drained  bool
	overflow bool
	err      error
}
type qualificationCapture struct {
	Stdout, Stderr                                   qualificationStream
	PID                                              uint32
	Created                                          int64
	JobName                                          string
	ExitCode                                         int
	Exited, JobZero, StreamsDrained, CleanupComplete bool
	TimedOut, LimitExceeded                          bool
	Err                                              error
}

func boundedQualificationStream(f *os.File, out chan<- qualificationStream, partialPath string) {
	defer f.Close()
	partial, openErr := os.OpenFile(partialPath, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if openErr != nil {
		out <- qualificationStream{err: openErr}
		return
	}
	var data bytes.Buffer
	buf := make([]byte, 8192)
	h := sha256.New()
	var result qualificationStream
	for {
		n, err := f.Read(buf)
		if n > 0 {
			if data.Len() < qualificationPrefixCap {
				keep := qualificationPrefixCap - data.Len()
				if keep > n {
					keep = n
				}
				written, writeErr := partial.Write(buf[:keep])
				if writeErr == nil && written != keep {
					writeErr = io.ErrShortWrite
				}
				if writeErr == nil {
					writeErr = partial.Sync()
				}
				if writeErr != nil {
					result.err = writeErr
					break
				}
			}
			if data.Len()+n > qualificationStreamCap {
				result.overflow = true
				space := qualificationStreamCap - data.Len()
				if space > 0 {
					data.Write(buf[:space])
				}
				break
			}
			data.Write(buf[:n])
			h.Write(buf[:n])
		}
		if err == io.EOF {
			result.drained = true
			break
		}
		if err != nil {
			result.err = err
			break
		}
	}
	result.raw = bytes.Clone(data.Bytes())
	if err := partial.Sync(); err != nil {
		result.err = errors.Join(result.err, err)
	}
	if err := partial.Close(); err != nil {
		result.err = errors.Join(result.err, err)
	}
	if len(result.raw) > qualificationPrefixCap {
		result.prefix = bytes.Clone(result.raw[:qualificationPrefixCap])
	} else {
		result.prefix = bytes.Clone(result.raw)
	}
	if result.drained && !result.overflow {
		result.hash = "sha256:" + hex.EncodeToString(h.Sum(nil))
	}
	out <- result
}

// newJob only supplies KILL_ON_JOB_CLOSE. Add and read back both hard limits
// before launch resumes its suspended original process.
func qualificationJob(name string) (windows.Handle, error) {
	job, err := newJob(name)
	if err != nil {
		return 0, err
	}
	var limits windows.JOBOBJECT_EXTENDED_LIMIT_INFORMATION
	limits.BasicLimitInformation.LimitFlags = windows.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE | windows.JOB_OBJECT_LIMIT_ACTIVE_PROCESS | windows.JOB_OBJECT_LIMIT_JOB_MEMORY
	limits.BasicLimitInformation.ActiveProcessLimit = qualificationProcessLimit
	limits.JobMemoryLimit = qualificationJobMemory
	if _, err = windows.SetInformationJobObject(job, windows.JobObjectExtendedLimitInformation, uintptr(unsafe.Pointer(&limits)), uint32(unsafe.Sizeof(limits))); err != nil {
		closeJob(job)
		return 0, err
	}
	var actual windows.JOBOBJECT_EXTENDED_LIMIT_INFORMATION
	if err = windows.QueryInformationJobObject(job, windows.JobObjectExtendedLimitInformation, uintptr(unsafe.Pointer(&actual)), uint32(unsafe.Sizeof(actual)), nil); err != nil {
		closeJob(job)
		return 0, err
	}
	flags := uint32(windows.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE | windows.JOB_OBJECT_LIMIT_ACTIVE_PROCESS | windows.JOB_OBJECT_LIMIT_JOB_MEMORY)
	if actual.BasicLimitInformation.LimitFlags&flags != flags || actual.BasicLimitInformation.ActiveProcessLimit != qualificationProcessLimit || actual.JobMemoryLimit != qualificationJobMemory {
		closeJob(job)
		return 0, errors.New("QUALIFICATION_JOB_LIMIT_UNVERIFIED")
	}
	return job, nil
}

func collectQualification(ctx context.Context, executable string, args, env []string, cwd, jobName, receiptBase string) qualificationCapture {
	var out qualificationCapture
	if ctx.Err() != nil {
		out.Err = ctx.Err()
		return out
	}
	stdinR, stdinW, err := os.Pipe()
	if err != nil {
		out.Err = err
		return out
	}
	stdoutR, stdoutW, err := os.Pipe()
	if err != nil {
		stdinR.Close()
		stdinW.Close()
		out.Err = err
		return out
	}
	stderrR, stderrW, err := os.Pipe()
	if err != nil {
		stdinR.Close()
		stdinW.Close()
		stdoutR.Close()
		stdoutW.Close()
		out.Err = err
		return out
	}
	closeAll := func() {
		for _, f := range []*os.File{stdinR, stdinW, stdoutR, stdoutW, stderrR, stderrW} {
			f.Close()
		}
	}
	job, err := qualificationJob(jobName)
	if err != nil {
		closeAll()
		out.Err = err
		return out
	}
	defer closeJob(job)
	p, err := launch(job, Command{Executable: executable, Args: args, Directory: cwd}, env, stdinR, stdoutW, stderrW)
	stdinR.Close()
	stdinW.Close()
	stdoutW.Close()
	stderrW.Close()
	if err != nil {
		stdoutR.Close()
		stderrR.Close()
		out.Err = err
		return out
	}
	defer p.close()
	out.PID, out.Created, out.JobName = p.pid, p.created, jobName
	outCh, errCh := make(chan qualificationStream, 1), make(chan qualificationStream, 1)
	go boundedQualificationStream(stdoutR, outCh, receiptBase+".stdout.partial")
	go boundedQualificationStream(stderrR, errCh, receiptBase+".stderr.partial")
	soft := time.NewTimer(35 * time.Second)
	hard := time.NewTimer(45 * time.Second)
	ticker := time.NewTicker(50 * time.Millisecond)
	defer soft.Stop()
	defer hard.Stop()
	defer ticker.Stop()
	stdoutReady, stderrReady := false, false
	ctxDone := ctx.Done()
loop:
	for !out.Exited {
		select {
		case <-ctxDone:
			out.TimedOut = true
			out.Err = ctx.Err()
			_ = killJob(job)
			ctxDone = nil
		case <-soft.C:
			out.TimedOut = true
			_ = killJob(job)
		case <-hard.C:
			out.TimedOut = true
			_ = killJob(job)
			break loop
		case stream := <-outCh:
			out.Stdout = stream
			stdoutReady = true
			if stream.overflow || stream.err != nil {
				out.LimitExceeded = stream.overflow
				_ = killJob(job)
			}
		case stream := <-errCh:
			out.Stderr = stream
			stderrReady = true
			if stream.overflow || stream.err != nil {
				out.LimitExceeded = out.LimitExceeded || stream.overflow
				_ = killJob(job)
			}
		case <-ticker.C:
			exited, code, e := p.exited()
			if e != nil {
				out.Err = e
				_ = killJob(job)
			} else if exited {
				out.Exited = true
				out.ExitCode = code
			}
		}
	}
	cleanup := time.NewTimer(5 * time.Second)
	defer cleanup.Stop()
	for {
		ids, e := jobPIDs(job)
		if e != nil {
			out.Err = errors.Join(out.Err, e)
			break
		}
		if len(ids) == 0 {
			out.JobZero = true
			break
		}
		select {
		case <-cleanup.C:
			out.Err = errors.Join(out.Err, errors.New("QUALIFICATION_CLEANUP_UNKNOWN"))
			_ = killJob(job)
			break
		case <-time.After(50 * time.Millisecond):
			continue
		}
		break
	}
	if !out.JobZero {
		_ = killJob(job)
	}
	if !out.Exited {
		exited, code, e := p.exited()
		if e == nil && exited {
			out.Exited = true
			out.ExitCode = code
		}
	}
	streamDeadline := time.NewTimer(5 * time.Second)
	defer streamDeadline.Stop()
	for !stdoutReady || !stderrReady {
		select {
		case stream := <-outCh:
			out.Stdout = stream
			stdoutReady = true
		case stream := <-errCh:
			out.Stderr = stream
			stderrReady = true
		case <-streamDeadline.C:
			out.Err = errors.Join(out.Err, errors.New("QUALIFICATION_STREAMS_UNDRAINED"))
			stdoutReady, stderrReady = true, true
		}
	}
	out.StreamsDrained = out.Stdout.drained && out.Stderr.drained && !out.Stdout.overflow && !out.Stderr.overflow
	out.LimitExceeded = out.Stdout.overflow || out.Stderr.overflow
	out.CleanupComplete = out.Exited && out.JobZero && out.StreamsDrained && out.Err == nil
	return out
}

func persistQualificationCapture(path string, c qualificationCapture, reason string) error {
	if path == "" {
		return errors.New("QUALIFICATION_RECEIPT_PATH_REQUIRED")
	}
	data := struct {
		Schema                     string `json:"schema"`
		Reason                     string `json:"reason"`
		PID                        uint32 `json:"pid"`
		Created                    int64  `json:"created"`
		Job                        string `json:"job"`
		ExitCode                   int    `json:"exit_code"`
		Exited                     bool   `json:"exited"`
		JobZero                    bool   `json:"job_zero"`
		StreamsDrained             bool   `json:"streams_drained"`
		CleanupComplete            bool   `json:"cleanup_complete"`
		TimedOut                   bool   `json:"timed_out"`
		LimitExceeded              bool   `json:"limit_exceeded"`
		StdoutPrefix, StderrPrefix []byte `json:"stdout_prefix"`
		StdoutHash, StderrHash     string `json:"stdout_hash"`
	}{"researchos.native-qualification-capture.v1", reason, c.PID, c.Created, c.JobName, c.ExitCode, c.Exited, c.JobZero, c.StreamsDrained, c.CleanupComplete, c.TimedOut, c.LimitExceeded, c.Stdout.prefix, c.Stderr.prefix, c.Stdout.hash, c.Stderr.hash}
	raw, err := json.Marshal(data)
	if err != nil {
		return err
	}
	if len(raw) > 2*qualificationPrefixCap*4/3+8192 {
		return errors.New("QUALIFICATION_RECEIPT_TOO_LARGE")
	}
	f, err := os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if err != nil {
		return err
	}
	n, e := f.Write(append(raw, '\n'))
	if e == nil && n != len(raw)+1 {
		e = io.ErrShortWrite
	}
	syncErr := f.Sync()
	closeErr := f.Close()
	return errors.Join(e, syncErr, closeErr)
}

func qualificationCaptureReason(c qualificationCapture) string {
	if c.PID == 0 {
		return "QUALIFICATION_BOOTSTRAP_BLOCKED"
	}
	if !c.JobZero || !c.CleanupComplete {
		return "QUALIFICATION_CLEANUP_UNKNOWN"
	}
	if c.TimedOut || c.LimitExceeded || !c.StreamsDrained {
		return "QUALIFICATION_INCOMPLETE"
	}
	if c.Err != nil {
		return "QUALIFICATION_BOOTSTRAP_BLOCKED"
	}
	if c.ExitCode != 0 {
		return "QUALIFICATION_INCOMPLETE"
	}
	return ""
}

func qualificationJobName(run, epoch, nonce string) string {
	return "researchos-codex-qualification-" + strings.TrimPrefix(Hash([]byte(run+"/"+epoch+"/"+nonce)), "sha256:")
}
