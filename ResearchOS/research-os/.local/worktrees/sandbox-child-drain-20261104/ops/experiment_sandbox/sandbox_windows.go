//go:build windows

// Package sandbox runs one bounded process in a fresh AppContainer with no capabilities.
package sandbox

import (
	"context"
	"errors"
	"fmt"
	"golang.org/x/sys/windows"
	"io"
	"os"
	"os/user"
	"path/filepath"
	"sort"
	"strings"
	"syscall"
	"time"
	"unicode/utf16"
	"unsafe"
)

type Command struct {
	Executable                      string
	Args                            []string
	InputDirectory, OutputDirectory string
	Timeout                         time.Duration
	// Zero values preserve the original single-process, 256 MiB boundary.
	ProcessLimit, MemoryMiB uint32
	// Env accepts only the offline Go keys validated by goEnvironment.
	Env map[string]string
}
type Receipt struct {
	Executable      string   `json:"executable"`
	Args            []string `json:"argv"`
	Directory       string   `json:"cwd"`
	Profile         string   `json:"profile"`
	PID             uint32   `json:"pid"`
	Created         int64    `json:"process_created_ns,string"`
	Job             string   `json:"job"`
	StreamsDrained  bool     `json:"streams_drained"`
	CleanupComplete bool     `json:"cleanup_complete"`
	OutputCopied    bool     `json:"output_copied"`
	SID             string   `json:"appcontainer_sid"`
	Capabilities    []string `json:"capabilities"`
	ExitCode        int      `json:"exit_code"`
	Stopped         bool     `json:"children_stopped"`
	JobProcesses    uint32   `json:"job_total_processes"`
	TimedOut        bool     `json:"timed_out"`
	Started         string   `json:"started_at"`
	Finished        string   `json:"finished_at"`
	Stdout          []byte   `json:"stdout"`
	Stderr          []byte   `json:"stderr"`
}

var userenv = windows.NewLazySystemDLL("userenv.dll")

func utf(s string) *uint16 { p, _ := windows.UTF16PtrFromString(s); return p }
func acl(path, sid, rights string) error {
	u, e := user.Current()
	if e != nil {
		return e
	}
	sd, e := windows.SecurityDescriptorFromString("D:P(A;OICI;FA;;;" + u.Uid + ")(A;OICI;" + rights + ";;;" + sid + ")S:(ML;OICI;NW;;;LW)")
	if e != nil {
		return e
	}
	d, _, e := sd.DACL()
	if e != nil {
		return e
	}
	s, _, e := sd.SACL()
	if e != nil {
		return e
	}
	if e = windows.SetNamedSecurityInfo(path, windows.SE_FILE_OBJECT, windows.DACL_SECURITY_INFORMATION|windows.PROTECTED_DACL_SECURITY_INFORMATION, nil, nil, d, nil); e != nil {
		return e
	}
	return windows.SetNamedSecurityInfo(path, windows.SE_FILE_OBJECT, windows.LABEL_SECURITY_INFORMATION, nil, nil, nil, s)
}

// Fresh container SIDs receive access only to these caller-owned staging roots.
// Windows platform files and the OS-created private AppContainer storage are OS grants.
func Run(ctx context.Context, c Command) (Receipt, error) {
	p, err := Start(ctx, c, StartOptions{})
	if err != nil {
		return Receipt{}, err
	}
	return p.Wait(context.Background())
}

func runSandbox(ctx context.Context, c Command, options StartOptions, process *Process) (r Receipt, err error) {
	maxTimeout := 5 * time.Minute
	if options.AllowCodingTurnTimeout {
		maxTimeout = 15 * time.Minute
	}
	if c.Timeout <= 0 || c.Timeout > maxTimeout {
		return r, fmt.Errorf("bounded timeout 0..%s required", maxTimeout)
	}
	processLimit, memoryMiB := c.ProcessLimit, c.MemoryMiB
	if processLimit == 0 {
		processLimit = 1
	}
	if memoryMiB == 0 {
		memoryMiB = 256
	}
	if processLimit > 32 || memoryMiB > 1024 {
		return r, errors.New("process limit 1..32 and memory limit 1..1024 MiB required")
	}
	if _, e := goEnvironment(c.Env, c.InputDirectory, c.OutputDirectory, nil); e != nil {
		return r, e
	}
	for _, p := range []string{c.Executable, c.InputDirectory, c.OutputDirectory} {
		if !filepath.IsAbs(p) {
			return r, errors.New("absolute owned staging paths required")
		}
		actual, e := filepath.EvalSymlinks(p)
		if e != nil || !strings.EqualFold(filepath.Clean(actual), filepath.Clean(p)) {
			return r, errors.New("reparse path rejected")
		}
	}

	for _, pair := range [][2]string{{c.InputDirectory, c.OutputDirectory}, {c.OutputDirectory, c.InputDirectory}} {
		overlap, e := filepath.Rel(pair[0], pair[1])
		if e != nil {
			return r, e
		}
		if overlap == "." || overlap != ".." && !strings.HasPrefix(overlap, ".."+string(os.PathSeparator)) {
			return r, errors.New("input and output roots must be disjoint")
		}
	}
	rel, e := filepath.Rel(c.InputDirectory, c.Executable)
	if e != nil || strings.HasPrefix(rel, "..") || strings.EqualFold(c.InputDirectory, c.OutputDirectory) {
		return r, errors.New("executable must be under distinct read-only input root")
	}
	name := fmt.Sprintf("ResearchOS.W10.%d", time.Now().UnixNano())
	var sid *windows.SID
	hr, _, _ := userenv.NewProc("CreateAppContainerProfile").Call(uintptr(unsafe.Pointer(utf(name))), uintptr(unsafe.Pointer(utf(name))), uintptr(unsafe.Pointer(utf("bounded development evaluation"))), 0, 0, uintptr(unsafe.Pointer(&sid)))
	if int32(hr) < 0 {
		return r, fmt.Errorf("CreateAppContainerProfile HRESULT 0x%x", hr)
	}
	cleanupAllowed := true // Becomes false as soon as an owned process exists.
	defer func() {
		if !cleanupAllowed {
			return
		}
		hr, _, _ := userenv.NewProc("DeleteAppContainerProfile").Call(uintptr(unsafe.Pointer(utf(name))))
		if int32(hr) < 0 {
			r.CleanupComplete = false
			err = errors.Join(err, fmt.Errorf("DeleteAppContainerProfile HRESULT 0x%x", hr))
		}
	}()
	defer windows.FreeSid(sid)
	r.SID = sid.String()
	r.Profile = name
	r.Capabilities = []string{}

	// A fresh copied tree inherits one known DACL; source ACLs and reparse points
	// never cross the boundary. AppContainer, not the copy, enforces isolation.
	staging, e := os.MkdirTemp("", "researchos-w10-staging-")
	if e != nil {
		return r, e
	}
	defer func() {
		if !cleanupAllowed {
			return
		}
		cleanupErr := os.RemoveAll(staging)
		r.CleanupComplete = cleanupErr == nil
		err = errors.Join(err, cleanupErr)
	}()
	originalInput, originalOutput := c.InputDirectory, c.OutputDirectory
	c.InputDirectory = filepath.Join(staging, "input")
	c.OutputDirectory = filepath.Join(staging, "output")
	for root, rights := range map[string]string{c.InputDirectory: "GRGX", c.OutputDirectory: "FA"} {
		if e = os.Mkdir(root, 0700); e != nil {
			return r, e
		}
		if e = acl(root, r.SID, rights); e != nil {
			return r, e
		}
	}
	// Windows redirects GetTempPath in an AppContainer beneath LOCALAPPDATA.
	// Create that exact per-profile directory after installing the output ACL;
	// descendants inherit only the current sandbox SID and low-integrity policy.
	if e = os.MkdirAll(filepath.Join(c.OutputDirectory, "Packages", strings.ToLower(name), "AC", "Temp"), 0700); e != nil {
		return r, e
	}
	setupCtx, cancelSetup := context.WithTimeout(ctx, 2*time.Minute)
	defer cancelSetup()
	if e = copyTree(setupCtx, originalInput, c.InputDirectory); e != nil {
		return r, fmt.Errorf("bounded input staging: %w", e)
	}
	replace := func(p string) string {
		for old, newPath := range map[string]string{originalInput: c.InputDirectory, originalOutput: c.OutputDirectory} {
			if strings.EqualFold(p, old) {
				return newPath
			}
			if len(p) > len(old) && strings.EqualFold(p[:len(old)+1], old+string(os.PathSeparator)) {
				return newPath + p[len(old):]
			}
		}
		return p
	}
	c.Executable = replace(c.Executable)
	c.Args = append([]string{}, c.Args...)
	for i, v := range c.Args {
		c.Args[i] = replace(v)
	}
	r.Executable, r.Args, r.Directory = c.Executable, c.Args, c.OutputDirectory
	defer func() {
		if cleanupAllowed && r.Stopped && r.StreamsDrained {
			copyCtx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
			defer cancel()
			x := copyTree(copyCtx, c.OutputDirectory, originalOutput)
			r.OutputCopied = x == nil
			if x != nil {
				cleanupAllowed = false
			}
			err = errors.Join(err, x)
		}
	}()
	r.Job = "Local\\" + name
	job, e := windows.CreateJobObject(nil, utf(r.Job))
	if e != nil {
		return r, e
	}
	closeJob := func() error {
		if job == 0 {
			return nil
		}
		owned := job
		job = 0 // Single owner; never reuse or close this numeric handle again.
		e := windows.CloseHandle(owned)
		if e != nil {
			cleanupAllowed = false
		}
		return e
	}
	defer func() { err = errors.Join(err, closeJob()) }()
	limit := windows.JOBOBJECT_EXTENDED_LIMIT_INFORMATION{}
	limit.BasicLimitInformation.LimitFlags = windows.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE | windows.JOB_OBJECT_LIMIT_ACTIVE_PROCESS | windows.JOB_OBJECT_LIMIT_PROCESS_MEMORY
	limit.BasicLimitInformation.ActiveProcessLimit = processLimit
	limit.ProcessMemoryLimit = uintptr(memoryMiB) * 1024 * 1024
	if _, e = windows.SetInformationJobObject(job, windows.JobObjectExtendedLimitInformation, uintptr(unsafe.Pointer(&limit)), uint32(unsafe.Sizeof(limit))); e != nil {
		return r, e
	}
	stdin, input, e := os.Pipe()
	if e != nil {
		return r, e
	}
	defer stdin.Close()
	process.mu.Lock()
	process.stdin = input
	process.mu.Unlock()
	defer process.CloseInput()
	if !options.Interactive {
		process.CloseInput()
	}
	stdoutReader, stdout, e := os.Pipe()
	if e != nil {
		return r, e
	}
	defer stdout.Close()
	defer stdoutReader.Close()
	stderrReader, stderr, e := os.Pipe()
	if e != nil {
		return r, e
	}
	defer stderr.Close()
	defer stderrReader.Close()
	outDone, errDone := make(chan streamResult, 1), make(chan streamResult, 1)
	streamFence := make(chan struct{})
	defer close(streamFence)
	go collectStream(stdoutReader, "stdout", options.OnStream, process.cancel, outDone, streamFence)
	go collectStream(stderrReader, "stderr", options.OnStream, process.cancel, errDone, streamFence)
	// Even a pre-Create failure closes the Job before pipe/collector cleanup.
	defer func() {
		err = errors.Join(err, closeJob())
		// On Create failure only this parent owns these write ends; release them
		// before closing readers, so no empty collector depends on its own writer.
		stdout.Close()
		stderr.Close()
		stdin.Close()
	}()
	handles := []windows.Handle{windows.Handle(stdin.Fd()), windows.Handle(stdout.Fd()), windows.Handle(stderr.Fd())}
	for _, h := range handles {
		if e = windows.SetHandleInformation(h, windows.HANDLE_FLAG_INHERIT, windows.HANDLE_FLAG_INHERIT); e != nil {
			return r, e
		}
		defer windows.SetHandleInformation(h, windows.HANDLE_FLAG_INHERIT, 0)
	}
	attrs, e := windows.NewProcThreadAttributeList(3)
	if e != nil {
		return r, e
	}
	defer attrs.Delete()
	type caps struct {
		SID             *windows.SID
		Capabilities    uintptr
		Count, Reserved uint32
	}
	capability := caps{SID: sid}
	if e = attrs.Update(0x00020009, unsafe.Pointer(&capability), unsafe.Sizeof(capability)); e != nil {
		return r, e
	}
	if e = attrs.Update(0x0002000d, unsafe.Pointer(&job), unsafe.Sizeof(job)); e != nil {
		return r, e
	}
	if e = attrs.Update(windows.PROC_THREAD_ATTRIBUTE_HANDLE_LIST, unsafe.Pointer(&handles[0]), uintptr(len(handles))*unsafe.Sizeof(handles[0])); e != nil {
		return r, e
	}
	si := windows.StartupInfoEx{ProcThreadAttributeList: attrs.List()}
	si.Cb = uint32(unsafe.Sizeof(si))
	si.Flags = windows.STARTF_USESTDHANDLES
	si.StdInput = handles[0]
	si.StdOutput = handles[1]
	si.StdErr = handles[2]
	args := []string{syscall.EscapeArg(c.Executable)}
	for _, a := range c.Args {
		args = append(args, syscall.EscapeArg(a))
	}
	line := utf(strings.Join(args, " "))
	goEnv, e := goEnvironment(c.Env, originalInput, originalOutput, replace)
	if e != nil {
		return r, e
	}
	envValues := []string{"SystemRoot=" + os.Getenv("SystemRoot"), "TEMP=" + c.OutputDirectory, "TMP=" + c.OutputDirectory, "USERPROFILE=" + c.OutputDirectory, "LOCALAPPDATA=" + c.OutputDirectory, "APPDATA=" + c.OutputDirectory}
	keys := make([]string, 0, len(goEnv))
	for k := range goEnv {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	for _, k := range keys {
		envValues = append(envValues, k+"="+goEnv[k])
	}
	env := utf16.Encode([]rune(strings.Join(envValues, "\x00") + "\x00\x00"))
	var pi windows.ProcessInformation
	r.Started = time.Now().UTC().Format(time.RFC3339Nano)
	if e = windows.CreateProcess(utf(c.Executable), line, nil, nil, true, windows.EXTENDED_STARTUPINFO_PRESENT|windows.CREATE_NO_WINDOW|windows.CREATE_UNICODE_ENVIRONMENT|windows.CREATE_SUSPENDED, &env[0], utf(c.OutputDirectory), &si.StartupInfo, &pi); e != nil {
		return r, fmt.Errorf("CreateProcess: %w", e)
	}
	cleanupAllowed = false
	defer func() {
		if e := windows.CloseHandle(pi.Process); e != nil {
			cleanupAllowed = false
			err = errors.Join(err, e)
		}
	}()
	defer func() {
		if e := windows.CloseHandle(pi.Thread); e != nil {
			cleanupAllowed = false
			err = errors.Join(err, e)
		}
	}()
	// Release parent write ends before observing natural EOF.
	stdout.Close()
	stderr.Close()
	stdin.Close()
	r.PID = pi.ProcessId
	resumed, finished := false, false
	deadline := time.Now().Add(c.Timeout)
	finish := func(cause error) {
		finished = true
		if !resumed && cause == nil {
			cause = errors.New("sandbox stopped before resume")
		}
		ops := sandboxLifecycleOps{
			now: time.Now, pause: time.Sleep,
			primary: func() (bool, error) {
				state, e := windows.WaitForSingleObject(pi.Process, 0)
				if e != nil {
					return false, e
				}
				if state != windows.WAIT_OBJECT_0 && state != windows.WAIT_TIMEOUT {
					return false, errors.New("unexpected primary wait state")
				}
				return state == windows.WAIT_OBJECT_0, nil
			},
			account: func() (uint32, uint32, error) {
				var a struct {
					User, Kernel, PeriodUser, PeriodKernel              int64
					Faults, TotalProcesses, ActiveProcesses, Terminated uint32
				}
				e := windows.QueryInformationJobObject(job, windows.JobObjectBasicAccountingInformation, uintptr(unsafe.Pointer(&a)), uint32(unsafe.Sizeof(a)), nil)
				return a.TotalProcesses, a.ActiveProcesses, e
			},
			terminate: func(code uint32) error { return windows.TerminateJobObject(job, code) },
			closeJob:  closeJob,
			exitCode: func() (uint32, error) {
				var code uint32
				e := windows.GetExitCodeProcess(pi.Process, &code)
				return code, e
			},
			closeReaders: func() error {
				var failure error
				for _, reader := range []*os.File{stdoutReader, stderrReader} {
					if e := reader.Close(); e != nil && !errors.Is(e, os.ErrClosed) {
						failure = errors.Join(failure, e)
					}
				}
				return failure
			},
		}
		life := coordinateSandboxLifecycle(ctx, deadline, cause, ops, outDone, errDone)
		r.Stopped, r.StreamsDrained, r.JobProcesses, r.TimedOut = life.stopped, life.drained, life.total, life.timedOut
		if life.codeKnown {
			r.ExitCode = int(life.code)
		}
		r.Stdout, r.Stderr = life.stdout, life.stderr
		r.Finished = time.Now().UTC().Format(time.RFC3339Nano)
		cleanupAllowed = life.resourcesQuiescent()
		err = errors.Join(err, life.err)
	}
	// All post-Create failures use the same original-handle stop path while the
	// process is still suspended; no stream/diagnostic join precedes Job close.
	defer func() {
		if !finished {
			finish(err)
		}
	}()
	var created, exited, kernel, user windows.Filetime
	if e = windows.GetProcessTimes(pi.Process, &created, &exited, &kernel, &user); e != nil {
		return r, e
	}
	r.Created = created.Nanoseconds()
	identity := Identity{PID: r.PID, Created: r.Created, Job: r.Job, SID: r.SID, Profile: r.Profile, StagingDirectory: staging}
	if options.BeforeResume != nil {
		if e = options.BeforeResume(identity); e != nil {
			return r, fmt.Errorf("beforeResume: %w", e)
		}
	}
	if ctx.Err() != nil {
		return r, ctx.Err()
	}
	if _, e = windows.ResumeThread(pi.Thread); e != nil {
		return r, e
	}
	resumed = true
	deadline = time.Now().Add(c.Timeout)
	process.ready <- nil
	finish(nil)
	return r, err
}

const sandboxChildGrace = 500 * time.Millisecond
const sandboxCleanupBudget = 5 * time.Second

// Private real production coordinator. Tests replace operations, never the
// public runner or an alleged Native outcome. The caller remains sole owner.
type sandboxLifecycleOps struct {
	now          func() time.Time
	pause        func(time.Duration)
	primary      func() (bool, error)
	account      func() (total, active uint32, err error)
	terminate    func(uint32) error
	closeJob     func() error
	exitCode     func() (uint32, error)
	closeReaders func() error
}

type sandboxLifecycleResult struct {
	stopped, drained, jobClosed, timedOut, codeKnown bool
	total, code                                      uint32
	stdout, stderr                                   []byte
	err                                              error
}

func (r sandboxLifecycleResult) resourcesQuiescent() bool {
	return r.stopped && r.drained && r.jobClosed && r.codeKnown
}

func coordinateSandboxLifecycle(ctx context.Context, deadline time.Time, initial error, ops sandboxLifecycleOps, stdout, stderr <-chan streamResult) (r sandboxLifecycleResult) {
	var primaryAt, cleanupAt time.Time
	var primarySeen, stopping bool
	var out, diagnostic *streamResult
	errorsSeen := map[string]bool{}
	failure := func(key string, err error) {
		if err != nil && !errorsSeen[key] {
			r.err = errors.Join(r.err, err)
			errorsSeen[key] = true
		}
	}
	beginCleanup := func() {
		if cleanupAt.IsZero() {
			cleanupAt = ops.now().Add(sandboxCleanupBudget)
		}
	}
	stop := func(code uint32) {
		beginCleanup()
		if !stopping {
			stopping = true
			failure("terminate", ops.terminate(code))
		}
	}
	collect := func() {
		if out == nil {
			select {
			case v := <-stdout:
				out = &v
				failure("stdout", v.err)
			default:
			}
		}
		if diagnostic == nil {
			select {
			case v := <-stderr:
				diagnostic = &v
				failure("stderr", v.err)
			default:
			}
		}
	}
	pause := func(until time.Time) {
		wait := 20 * time.Millisecond
		if left := until.Sub(ops.now()); left < wait {
			wait = left
		}
		if wait > 0 {
			ops.pause(wait)
		}
	}
	if initial != nil {
		failure("initial", initial)
		stop(125)
	}
	for {
		collect()
		if out != nil && out.err != nil || diagnostic != nil && diagnostic.err != nil {
			stop(125)
		}
		now := ops.now()
		if initial == nil && (ctx.Err() != nil || !now.Before(deadline)) {
			r.timedOut = true
			stop(124)
		}
		seen, err := ops.primary()
		if err != nil {
			failure("primary", err)
			stop(125)
		}
		if err == nil && seen && !primarySeen {
			primarySeen = true
			primaryAt = now
		}
		total, active, err := ops.account()
		if err != nil {
			failure("account", err)
			stop(125)
		} else {
			r.total = total
			if primarySeen && active == 0 {
				r.stopped = true
				beginCleanup()
				break
			}
		}
		if !stopping && primarySeen && !now.Before(primaryAt.Add(sandboxChildGrace)) {
			failure("descendants", errors.New("sandbox descendants survived primary exit grace"))
			stop(125)
		}
		if !cleanupAt.IsZero() && !now.Before(cleanupAt) {
			break
		}
		next := deadline
		if !cleanupAt.IsZero() {
			next = cleanupAt
		} else if primarySeen && primaryAt.Add(sandboxChildGrace).Before(next) {
			next = primaryAt.Add(sandboxChildGrace)
		}
		pause(next)
	}
	if primarySeen {
		code, err := ops.exitCode()
		failure("exit-code", err)
		if err == nil {
			r.code, r.codeKnown = code, true
		}
	}
	// Kernel fallback is synchronous and independent of all stream/callback
	// joins. After this point no operation uses the closed Job handle.
	closeErr := ops.closeJob()
	r.jobClosed = closeErr == nil
	failure("close-job", closeErr)
	readersClosed := false
	closeReaders := func() {
		if !readersClosed {
			readersClosed = true
			failure("close-readers", ops.closeReaders())
		}
	}
	if !r.stopped || !r.jobClosed {
		failure("stop-proof", errors.New("sandbox stop not confirmed before cleanup deadline"))
		closeReaders()
	} else {
		for {
			collect()
			if out != nil && diagnostic != nil {
				break
			}
			if !ops.now().Before(cleanupAt) {
				failure("drain", errors.New("sandbox streams or callback incomplete before cleanup deadline"))
				closeReaders()
				break
			}
			if ctx.Err() != nil || !ops.now().Before(deadline) {
				r.timedOut = true
				closeReaders()
			}
			pause(cleanupAt)
		}
	}
	if out != nil {
		r.stdout = append([]byte{}, out.bytes...)
	}
	if diagnostic != nil {
		r.stderr = append([]byte{}, diagnostic.bytes...)
	}
	r.drained = r.stopped && r.jobClosed && !readersClosed && out != nil && diagnostic != nil && out.eof && diagnostic.eof && out.err == nil && diagnostic.err == nil
	if !r.drained {
		failure("incomplete", errors.New("sandbox streams not naturally drained"))
	}
	return r
}

// goEnvironment permits only offline, deterministic Go configuration. Writable
// paths stay in the output root; GOROOT is read-only staged input. No PATH or
// host environment is inherited by the AppContainer.
func goEnvironment(values map[string]string, input, output string, remap func(string) string) (map[string]string, error) {
	result := make(map[string]string, len(values))
	within := func(root, path string) bool {
		if !filepath.IsAbs(path) {
			return false
		}
		rel, err := filepath.Rel(root, path)
		return err == nil && rel != ".." && !strings.HasPrefix(rel, ".."+string(os.PathSeparator))
	}
	for key, value := range values {
		if key != strings.ToUpper(key) || strings.ContainsAny(key+value, "=\x00") || value == "" {
			return nil, fmt.Errorf("invalid Go environment %q", key)
		}
		switch key {
		case "GOROOT":
			if !within(input, value) {
				return nil, fmt.Errorf("GOROOT must be in staged input")
			}
		case "GOPATH", "GOCACHE", "GOTMPDIR":
			if !within(output, value) {
				return nil, fmt.Errorf("%s must be in staged output", key)
			}
		case "GOTOOLCHAIN":
			if value != "local" {
				return nil, fmt.Errorf("GOTOOLCHAIN must be local")
			}
		case "GOPROXY", "GOSUMDB", "GOENV", "GOWORK":
			if value != "off" {
				return nil, fmt.Errorf("%s must be off", key)
			}
		case "CGO_ENABLED":
			if value != "0" {
				return nil, fmt.Errorf("CGO_ENABLED must be 0")
			}
		default:
			return nil, fmt.Errorf("Go environment key %q is not allowed", key)
		}
		if remap != nil && (key == "GOROOT" || key == "GOPATH" || key == "GOCACHE" || key == "GOTMPDIR") {
			value = remap(value)
		}
		result[key] = value
	}
	return result, nil
}

func copyTree(ctx context.Context, source, target string) error {
	var total int64
	return filepath.WalkDir(source, func(path string, d os.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if err = ctx.Err(); err != nil {
			return err
		}
		if d.Type()&os.ModeSymlink != 0 {
			return errors.New("reparse/symlink rejected")
		}
		rel, err := filepath.Rel(source, path)
		if err != nil {
			return err
		}
		if rel == "." {
			return nil
		}
		dest := filepath.Join(target, rel)
		if d.IsDir() {
			return os.MkdirAll(dest, 0700)
		}
		info, err := d.Info()
		if err != nil {
			return err
		}
		if !info.Mode().IsRegular() {
			return errors.New("regular files only")
		}
		total += info.Size()
		if total > 1024*1024*1024 {
			return errors.New("staging exceeds 1 GiB budget")
		}
		in, err := os.Open(path)
		if err != nil {
			return err
		}
		defer in.Close()
		out, err := os.OpenFile(dest, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
		if err != nil {
			return err
		}
		_, err = io.Copy(out, in)
		closeErr := out.Close()
		if err != nil {
			return err
		}
		return closeErr
	})
}
