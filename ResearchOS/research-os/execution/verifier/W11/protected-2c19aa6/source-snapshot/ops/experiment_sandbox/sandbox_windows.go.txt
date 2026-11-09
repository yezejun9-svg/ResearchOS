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
}
type Receipt struct {
	Executable   string   `json:"executable"`
	Args         []string `json:"argv"`
	Directory    string   `json:"cwd"`
	Profile      string   `json:"profile"`
	PID          uint32   `json:"pid"`
	SID          string   `json:"appcontainer_sid"`
	Capabilities []string `json:"capabilities"`
	ExitCode     int      `json:"exit_code"`
	Stopped      bool     `json:"children_stopped"`
	TimedOut     bool     `json:"timed_out"`
	Started      string   `json:"started_at"`
	Finished     string   `json:"finished_at"`
	Stdout       []byte   `json:"stdout"`
	Stderr       []byte   `json:"stderr"`
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
func Run(ctx context.Context, c Command) (r Receipt, err error) {
	if c.Timeout <= 0 || c.Timeout > 5*time.Minute {
		return r, errors.New("bounded timeout 0..5m required")
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
	defer userenv.NewProc("DeleteAppContainerProfile").Call(uintptr(unsafe.Pointer(utf(name))))
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
	defer os.RemoveAll(staging)
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
		if r.Stopped {
			if x := copyTree(context.Background(), c.OutputDirectory, originalOutput); x != nil && err == nil {
				err = x
			}
		}
	}()
	job, e := windows.CreateJobObject(nil, nil)
	if e != nil {
		return r, e
	}
	defer windows.CloseHandle(job)
	limit := windows.JOBOBJECT_EXTENDED_LIMIT_INFORMATION{}
	limit.BasicLimitInformation.LimitFlags = windows.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE | windows.JOB_OBJECT_LIMIT_ACTIVE_PROCESS | windows.JOB_OBJECT_LIMIT_PROCESS_MEMORY
	limit.BasicLimitInformation.ActiveProcessLimit = 1
	limit.ProcessMemoryLimit = 256 * 1024 * 1024
	if _, e = windows.SetInformationJobObject(job, windows.JobObjectExtendedLimitInformation, uintptr(unsafe.Pointer(&limit)), uint32(unsafe.Sizeof(limit))); e != nil {
		return r, e
	}
	stdin, e := os.Open(os.DevNull)
	if e != nil {
		return r, e
	}
	defer stdin.Close()
	stdout, e := os.CreateTemp("", "researchos-w10-out-")
	if e != nil {
		return r, e
	}
	defer os.Remove(stdout.Name())
	defer stdout.Close()
	stderr, e := os.CreateTemp("", "researchos-w10-err-")
	if e != nil {
		return r, e
	}
	defer os.Remove(stderr.Name())
	defer stderr.Close()
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
	env := utf16.Encode([]rune("SystemRoot=" + os.Getenv("SystemRoot") + "\x00TEMP=" + c.OutputDirectory + "\x00TMP=" + c.OutputDirectory + "\x00USERPROFILE=" + c.OutputDirectory + "\x00LOCALAPPDATA=" + c.OutputDirectory + "\x00APPDATA=" + c.OutputDirectory + "\x00\x00"))
	var pi windows.ProcessInformation
	r.Started = time.Now().UTC().Format(time.RFC3339Nano)
	if e = windows.CreateProcess(utf(c.Executable), line, nil, nil, true, windows.EXTENDED_STARTUPINFO_PRESENT|windows.CREATE_NO_WINDOW|windows.CREATE_UNICODE_ENVIRONMENT, &env[0], utf(c.OutputDirectory), &si.StartupInfo, &pi); e != nil {
		return r, fmt.Errorf("CreateProcess: %w", e)
	}
	defer windows.CloseHandle(pi.Process)
	windows.CloseHandle(pi.Thread)
	r.PID = pi.ProcessId
	deadline := time.Now().Add(c.Timeout)
	for {
		state, x := windows.WaitForSingleObject(pi.Process, 20)
		if x != nil {
			return r, x
		}
		if state == windows.WAIT_OBJECT_0 {
			break
		}
		if ctx.Err() != nil || time.Now().After(deadline) {
			r.TimedOut = true
			if e = windows.TerminateJobObject(job, 124); e != nil {
				return r, e
			}
			windows.WaitForSingleObject(pi.Process, 5000)
			break
		}
	}
	var code uint32
	if e = windows.GetExitCodeProcess(pi.Process, &code); e != nil {
		return r, e
	}
	r.ExitCode = int(code)
	r.Finished = time.Now().UTC().Format(time.RFC3339Nano)
	var accounting struct {
		User, Kernel, PeriodUser, PeriodKernel              int64
		Faults, TotalProcesses, ActiveProcesses, Terminated uint32
	}
	if e = windows.QueryInformationJobObject(job, windows.JobObjectBasicAccountingInformation, uintptr(unsafe.Pointer(&accounting)), uint32(unsafe.Sizeof(accounting)), nil); e != nil {
		return r, e
	}
	for n := 0; n < 50 && accounting.ActiveProcesses != 0; n++ {
		time.Sleep(10 * time.Millisecond)
		if e = windows.QueryInformationJobObject(job, windows.JobObjectBasicAccountingInformation, uintptr(unsafe.Pointer(&accounting)), uint32(unsafe.Sizeof(accounting)), nil); e != nil {
			return r, e
		}
	}
	r.Stopped = accounting.ActiveProcesses == 0
	r.Stdout, e = os.ReadFile(stdout.Name())
	if e != nil {
		return r, e
	}
	r.Stderr, e = os.ReadFile(stderr.Name())
	return r, e
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
