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
	JobProcessLimit                                  uint32
	JobMemoryLimit                                   uint64
	JobLimitFlags                                    uint32
	JobLimitsVerified                                bool
	ExitCode                                         int
	Exited, JobZero, StreamsDrained, CleanupComplete bool
	TimedOut, LimitExceeded                          bool
	Err                                              error
}

type qualificationSyncCloser interface {
	Sync() error
	Close() error
}

func finishQualificationStream(result *qualificationStream, partial qualificationSyncCloser, digest []byte) {
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
	if result.drained && !result.overflow && result.err == nil {
		result.hash = "sha256:" + hex.EncodeToString(digest)
	}
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
		readLimit := qualificationStreamCap - data.Len()
		if readLimit == 0 {
			result.overflow = true
			break
		}
		if readLimit > len(buf) {
			readLimit = len(buf)
		}
		n, err := f.Read(buf[:readLimit])
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
	finishQualificationStream(&result, partial, h.Sum(nil))
	out <- result
}

// newJob only supplies KILL_ON_JOB_CLOSE. Add and read back both hard limits
// before launch resumes its suspended original process.
type qualificationJobLimits struct {
	Flags, Processes uint32
	Memory           uint64
}

func qualificationJob(name string) (windows.Handle, qualificationJobLimits, error) {
	job, err := newJob(name)
	if err != nil {
		return 0, qualificationJobLimits{}, err
	}
	var limits windows.JOBOBJECT_EXTENDED_LIMIT_INFORMATION
	limits.BasicLimitInformation.LimitFlags = windows.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE | windows.JOB_OBJECT_LIMIT_ACTIVE_PROCESS | windows.JOB_OBJECT_LIMIT_JOB_MEMORY
	limits.BasicLimitInformation.ActiveProcessLimit = qualificationProcessLimit
	limits.JobMemoryLimit = qualificationJobMemory
	if _, err = windows.SetInformationJobObject(job, windows.JobObjectExtendedLimitInformation, uintptr(unsafe.Pointer(&limits)), uint32(unsafe.Sizeof(limits))); err != nil {
		closeJob(job)
		return 0, qualificationJobLimits{}, err
	}
	var actual windows.JOBOBJECT_EXTENDED_LIMIT_INFORMATION
	if err = windows.QueryInformationJobObject(job, windows.JobObjectExtendedLimitInformation, uintptr(unsafe.Pointer(&actual)), uint32(unsafe.Sizeof(actual)), nil); err != nil {
		closeJob(job)
		return 0, qualificationJobLimits{}, err
	}
	flags := uint32(windows.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE | windows.JOB_OBJECT_LIMIT_ACTIVE_PROCESS | windows.JOB_OBJECT_LIMIT_JOB_MEMORY)
	if actual.BasicLimitInformation.LimitFlags&flags != flags || actual.BasicLimitInformation.ActiveProcessLimit != qualificationProcessLimit || actual.JobMemoryLimit != qualificationJobMemory {
		closeJob(job)
		return 0, qualificationJobLimits{}, errors.New("QUALIFICATION_JOB_LIMIT_UNVERIFIED")
	}
	return job, qualificationJobLimits{Flags: actual.BasicLimitInformation.LimitFlags, Processes: actual.BasicLimitInformation.ActiveProcessLimit, Memory: uint64(actual.JobMemoryLimit)}, nil
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
	job, jobLimits, err := qualificationJob(jobName)
	if err != nil {
		closeAll()
		out.Err = err
		return out
	}
	defer closeJob(job)
	out.JobProcessLimit = jobLimits.Processes
	out.JobMemoryLimit = jobLimits.Memory
	out.JobLimitFlags = jobLimits.Flags
	out.JobLimitsVerified = true
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
	streamTimedOut := false
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
			_ = stdoutR.Close()
			_ = stderrR.Close()
			streamTimedOut = true
		}
		if streamTimedOut {
			break
		}
	}
	if streamTimedOut {
		joinDeadline := time.NewTimer(time.Second)
		defer joinDeadline.Stop()
		for !stdoutReady || !stderrReady {
			select {
			case stream := <-outCh:
				out.Stdout, stdoutReady = stream, true
			case stream := <-errCh:
				out.Stderr, stderrReady = stream, true
			case <-joinDeadline.C:
				out.Err = errors.Join(out.Err, errors.New("QUALIFICATION_STREAM_READER_UNJOINED"))
				stdoutReady, stderrReady = true, true
			}
		}
	}
	out.StreamsDrained = out.Stdout.drained && out.Stderr.drained && !out.Stdout.overflow && !out.Stderr.overflow
	out.LimitExceeded = out.Stdout.overflow || out.Stderr.overflow
	out.Err = errors.Join(out.Err, out.Stdout.err, out.Stderr.err)
	out.CleanupComplete = out.Exited && out.JobZero && out.StreamsDrained && out.Err == nil
	return out
}

type qualificationReceiptContext struct {
	TaskID               string                     `json:"task_id"`
	RunID                string                     `json:"run_id"`
	Epoch                string                     `json:"epoch"`
	SourceBindingHash    string                     `json:"source_binding_hash"`
	Source               string                     `json:"source"`
	Working              string                     `json:"working"`
	Denied               string                     `json:"denied"`
	NativeHash           string                     `json:"native_hash"`
	HelperHash           string                     `json:"helper_hash"`
	HostBuildHash        string                     `json:"host_build_hash"`
	TemplateHash         string                     `json:"template_hash"`
	EnvironmentHash      string                     `json:"environment_hash"`
	NormalHome           string                     `json:"normal_home"`
	HostBoot             string                     `json:"host_boot"`
	RenderedArgvHash     string                     `json:"rendered_argv_hash"`
	RenderedArgv         []string                   `json:"rendered_argv"`
	PlanHash             string                     `json:"plan_hash"`
	PlanEncoded          string                     `json:"plan_encoded"`
	Nonce                string                     `json:"nonce"`
	LoopbackPort         uint16                     `json:"loopback_port"`
	ExpectedCases        []string                   `json:"expected_cases"`
	CaseResults          []qualificationCaseOutcome `json:"case_results"`
	FindingCodes         []string                   `json:"finding_codes"`
	ObservedCaseBitmap   uint32                     `json:"observed_case_bitmap"`
	PreControlsComplete  bool                       `json:"pre_controls_complete"`
	PostControlsComplete bool                       `json:"post_controls_complete"`
}

type qualificationCaseOutcome struct {
	Name   string `json:"name"`
	Opened bool   `json:"opened"`
	Errno  int    `json:"errno"`
	Digest string `json:"digest"`
	Bytes  int    `json:"bytes"`
}

func persistQualificationCapture(path string, c qualificationCapture, reason string, context ...qualificationReceiptContext) error {
	if path == "" {
		return errors.New("QUALIFICATION_RECEIPT_PATH_REQUIRED")
	}
	data := struct {
		Schema            string                      `json:"schema"`
		Reason            string                      `json:"reason"`
		PID               uint32                      `json:"pid"`
		Created           int64                       `json:"created"`
		Job               string                      `json:"job"`
		ExitCode          int                         `json:"exit_code"`
		Exited            bool                        `json:"exited"`
		JobZero           bool                        `json:"job_zero"`
		StreamsDrained    bool                        `json:"streams_drained"`
		CleanupComplete   bool                        `json:"cleanup_complete"`
		TimedOut          bool                        `json:"timed_out"`
		LimitExceeded     bool                        `json:"limit_exceeded"`
		CaptureError      string                      `json:"capture_error"`
		StdoutError       string                      `json:"stdout_error"`
		StderrError       string                      `json:"stderr_error"`
		JobProcessLimit   uint32                      `json:"job_process_limit"`
		JobMemoryLimit    uint64                      `json:"job_memory_limit"`
		JobLimitFlags     uint32                      `json:"job_limit_flags"`
		JobLimitsVerified bool                        `json:"job_limits_verified"`
		Context           qualificationReceiptContext `json:"context"`
		StdoutPartial     string                      `json:"stdout_partial"`
		StderrPartial     string                      `json:"stderr_partial"`
		StdoutPrefix      []byte                      `json:"stdout_prefix"`
		StderrPrefix      []byte                      `json:"stderr_prefix"`
		StdoutHash        string                      `json:"stdout_hash"`
		StderrHash        string                      `json:"stderr_hash"`
	}{Schema: "researchos.native-qualification-capture.v1", Reason: reason, PID: c.PID, Created: c.Created, Job: c.JobName, ExitCode: c.ExitCode, Exited: c.Exited, JobZero: c.JobZero, StreamsDrained: c.StreamsDrained, CleanupComplete: c.CleanupComplete, TimedOut: c.TimedOut, LimitExceeded: c.LimitExceeded, JobProcessLimit: c.JobProcessLimit, JobMemoryLimit: c.JobMemoryLimit, JobLimitFlags: c.JobLimitFlags, JobLimitsVerified: c.JobLimitsVerified, StdoutPartial: path + ".stdout.partial", StderrPartial: path + ".stderr.partial", StdoutPrefix: c.Stdout.prefix, StderrPrefix: c.Stderr.prefix, StdoutHash: c.Stdout.hash, StderrHash: c.Stderr.hash}
	if len(context) == 1 {
		data.Context = context[0]
	} else if len(context) > 1 {
		return errors.New("QUALIFICATION_RECEIPT_CONTEXT_AMBIGUOUS")
	}
	if c.Err != nil {
		data.CaptureError = c.Err.Error()
	}
	if c.Stdout.err != nil {
		data.StdoutError = c.Stdout.err.Error()
	}
	if c.Stderr.err != nil {
		data.StderrError = c.Stderr.err.Error()
	}
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
	requiredFlags := uint32(windows.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE | windows.JOB_OBJECT_LIMIT_ACTIVE_PROCESS | windows.JOB_OBJECT_LIMIT_JOB_MEMORY)
	if !c.JobLimitsVerified || c.JobProcessLimit != qualificationProcessLimit || c.JobMemoryLimit != uint64(qualificationJobMemory) || c.JobLimitFlags&requiredFlags != requiredFlags {
		return "QUALIFICATION_BOOTSTRAP_BLOCKED"
	}
	if !c.JobZero || !c.CleanupComplete {
		return "QUALIFICATION_CLEANUP_UNKNOWN"
	}
	if c.Stdout.err != nil || c.Stderr.err != nil {
		return "QUALIFICATION_INCOMPLETE"
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
