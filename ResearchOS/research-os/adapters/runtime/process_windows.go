//go:build windows

package runtime

import (
	"errors"
	"fmt"
	"os"
	"os/user"
	"strings"
	"syscall"
	"unicode/utf16"
	"unsafe"

	"golang.org/x/sys/windows"
)

// PrivateDirectory applies an inheritable, protected DACL, and reads the actual descriptor back.
// os.Chmod alone does not restrict Windows access.
func PrivateDirectory(path string) (string, error) {
	u, e := user.Current()
	if e != nil {
		return "", e
	}
	sd, e := windows.SecurityDescriptorFromString("D:P(A;OICI;FA;;;" + u.Uid + ")")
	if e != nil {
		return "", e
	}
	acl, _, e := sd.DACL()
	if e != nil {
		return "", e
	}
	if e = windows.SetNamedSecurityInfo(path, windows.SE_FILE_OBJECT, windows.DACL_SECURITY_INFORMATION|windows.PROTECTED_DACL_SECURITY_INFORMATION, nil, nil, acl, nil); e != nil {
		return "", e
	}
	actual, e := windows.GetNamedSecurityInfo(path, windows.SE_FILE_OBJECT, windows.DACL_SECURITY_INFORMATION)
	if e != nil {
		return "", e
	}
	text := actual.String()
	if !strings.Contains(text, u.Uid) || !strings.Contains(text, "D:P") {
		return "", errors.New("private DACL verification failed")
	}
	return text, nil
}

type process struct {
	job, handle windows.Handle
	pid         uint32
	created     int64
}

func newJob(name string) (windows.Handle, error) {
	n, e := windows.UTF16PtrFromString(name)
	if e != nil {
		return 0, e
	}
	h, e := windows.CreateJobObject(nil, n)
	if e != nil {
		return 0, e
	}
	limits := windows.JOBOBJECT_EXTENDED_LIMIT_INFORMATION{}
	limits.BasicLimitInformation.LimitFlags = windows.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
	if _, e = windows.SetInformationJobObject(h, windows.JobObjectExtendedLimitInformation, uintptr(unsafe.Pointer(&limits)), uint32(unsafe.Sizeof(limits))); e != nil {
		windows.CloseHandle(h)
		return 0, e
	}
	return h, nil
}

// Job membership is assigned atomically at creation, before a suspended process can run.
// This also closes the worker-crash gap between CreateProcess and AssignProcessToJobObject.
func launch(job windows.Handle, c Command, env []string, stdin, stdout, stderr *os.File) (*process, error) {
	return launchWithCallback(job, c, env, stdin, stdout, stderr, nil)
}
func launchWithCallback(job windows.Handle, c Command, env []string, stdin, stdout, stderr *os.File, before func(*process) error) (*process, error) {
	handles := []windows.Handle{windows.Handle(stdin.Fd()), windows.Handle(stdout.Fd()), windows.Handle(stderr.Fd())}
	for _, h := range handles {
		if e := windows.SetHandleInformation(h, windows.HANDLE_FLAG_INHERIT, windows.HANDLE_FLAG_INHERIT); e != nil {
			return nil, e
		}
		defer windows.SetHandleInformation(h, windows.HANDLE_FLAG_INHERIT, 0)
	}
	attrs, e := windows.NewProcThreadAttributeList(2)
	if e != nil {
		return nil, e
	}
	defer attrs.Delete()
	if e = attrs.Update(windows.PROC_THREAD_ATTRIBUTE_HANDLE_LIST, unsafe.Pointer(&handles[0]), uintptr(len(handles))*unsafe.Sizeof(handles[0])); e != nil {
		return nil, e
	}
	const jobList = 0x0002000d // PROC_THREAD_ATTRIBUTE_JOB_LIST (Windows 10+)
	if e = attrs.Update(jobList, unsafe.Pointer(&job), unsafe.Sizeof(job)); e != nil {
		return nil, e
	}
	si := windows.StartupInfoEx{ProcThreadAttributeList: attrs.List()}
	si.Cb = uint32(unsafe.Sizeof(si))
	si.Flags = windows.STARTF_USESTDHANDLES
	si.StdInput = handles[0]
	si.StdOutput = handles[1]
	si.StdErr = handles[2]
	app, e := windows.UTF16PtrFromString(c.Executable)
	if e != nil {
		return nil, e
	}
	args := []string{syscall.EscapeArg(c.Executable)}
	for _, a := range c.Args {
		args = append(args, syscall.EscapeArg(a))
	}
	line, e := windows.UTF16PtrFromString(strings.Join(args, " "))
	if e != nil {
		return nil, e
	}
	cwd, e := windows.UTF16PtrFromString(c.Directory)
	if e != nil {
		return nil, e
	}
	for _, v := range env {
		if strings.ContainsRune(v, 0) {
			return nil, errors.New("NUL environment")
		}
	}
	block := utf16.Encode([]rune(strings.Join(env, "\x00") + "\x00\x00"))
	var pi windows.ProcessInformation
	if e = windows.CreateProcess(app, line, nil, nil, true, windows.EXTENDED_STARTUPINFO_PRESENT|windows.CREATE_SUSPENDED|windows.CREATE_NO_WINDOW|windows.CREATE_UNICODE_ENVIRONMENT, &block[0], cwd, &si.StartupInfo, &pi); e != nil {
		return nil, e
	}
	p := &process{job: job, handle: pi.Process, pid: pi.ProcessId}
	var created, exit, kernel, user windows.Filetime
	if e = windows.GetProcessTimes(pi.Process, &created, &exit, &kernel, &user); e == nil {
		p.created = created.Nanoseconds()
		if before != nil {
			e = before(p)
		}
		if e == nil {
			_, e = windows.ResumeThread(pi.Thread)
		}
	}
	windows.CloseHandle(pi.Thread)
	if e != nil {
		windows.TerminateJobObject(job, 137)
		windows.CloseHandle(pi.Process)
		return nil, e
	}
	return p, nil
}

func jobPIDs(job windows.Handle) ([]uint32, error) {
	// ponytail: cap a task at 4096 observed descendants; overflow fails closed and keeps UNKNOWN.
	var list struct {
		Assigned, Count uint32
		PIDs            [4096]uintptr
	}
	e := windows.QueryInformationJobObject(job, windows.JobObjectBasicProcessIdList, uintptr(unsafe.Pointer(&list)), uint32(unsafe.Sizeof(list)), nil)
	if e != nil {
		return nil, e
	}
	if list.Count > uint32(len(list.PIDs)) {
		return nil, errors.New("job process list overflow")
	}
	ids := make([]uint32, 0, list.Count)
	for _, p := range list.PIDs[:list.Count] {
		ids = append(ids, uint32(p))
	}
	return ids, nil
}
func (p *process) exited() (bool, int, error) {
	r, e := windows.WaitForSingleObject(p.handle, 0)
	if e != nil {
		return false, 0, e
	}
	if r != windows.WAIT_OBJECT_0 {
		return false, 0, nil
	}
	var code uint32
	e = windows.GetExitCodeProcess(p.handle, &code)
	return true, int(code), e
}
func (p *process) close()              { windows.CloseHandle(p.handle) }
func killJob(job windows.Handle) error { return windows.TerminateJobObject(job, 137) }
func closeJob(job windows.Handle)      { windows.CloseHandle(job) }
func atomicReplace(from, to string) error {
	a, e := windows.UTF16PtrFromString(from)
	if e != nil {
		return e
	}
	b, e := windows.UTF16PtrFromString(to)
	if e != nil {
		return e
	}
	return windows.MoveFileEx(a, b, windows.MOVEFILE_REPLACE_EXISTING|windows.MOVEFILE_WRITE_THROUGH)
}
func lockFile(path string) (*os.File, error) {
	p, e := windows.UTF16PtrFromString(path)
	if e != nil {
		return nil, e
	}
	h, e := windows.CreateFile(p, windows.GENERIC_READ|windows.GENERIC_WRITE, 0, nil, windows.OPEN_ALWAYS, windows.FILE_ATTRIBUTE_NORMAL, 0)
	if e != nil {
		return nil, e
	}
	return os.NewFile(uintptr(h), path), nil
}
func inspectIdentity(pid uint32, created int64) (bool, error) {
	h, e := windows.OpenProcess(windows.PROCESS_QUERY_LIMITED_INFORMATION|windows.SYNCHRONIZE, false, pid)
	if errors.Is(e, windows.ERROR_INVALID_PARAMETER) {
		return false, nil
	}
	if e != nil {
		return false, e
	}
	defer windows.CloseHandle(h)
	var c, x, k, u windows.Filetime
	if e = windows.GetProcessTimes(h, &c, &x, &k, &u); e != nil {
		return false, e
	}
	if c.Nanoseconds() != created {
		return false, nil
	}
	r, e := windows.WaitForSingleObject(h, 0)
	return r != windows.WAIT_OBJECT_0, e
}
func openJob(name string) (windows.Handle, error) {
	n, e := windows.UTF16PtrFromString(name)
	if e != nil {
		return 0, e
	}
	h, _, err := windows.NewLazySystemDLL("kernel32.dll").NewProc("OpenJobObjectW").Call(0x0004|0x0008, 0, uintptr(unsafe.Pointer(n)))
	if h == 0 {
		return 0, fmt.Errorf("open job: %w", err)
	}
	return windows.Handle(h), nil
}
