//go:build windows

package main

import (
	"encoding/binary"
	"errors"
	"fmt"
	"golang.org/x/sys/windows"
	"os"
	"sort"
	"strconv"
	"strings"
	"syscall"
	"time"
	"unsafe"
)

type heldProcess struct {
	record processRecord
	h      windows.Handle
}
type nativeKernel struct {
	exe, cwd  string
	env       []uint16
	stdio     []*os.File
	job, port windows.Handle
	pi        windows.ProcessInformation
	records   map[uint32]*heldProcess
	problems  []string
	closed    bool
}
type accounting struct {
	User, Kernel, PeriodUser, PeriodKernel int64
	Faults, Total, Active, Terminated      uint32
}

var isInJob = windows.NewLazySystemDLL("kernel32.dll").NewProc("IsProcessInJob")

func inJob(h, j windows.Handle) (bool, error) {
	var v uint32
	r, _, e := isInJob.Call(uintptr(h), uintptr(j), uintptr(unsafe.Pointer(&v)))
	if r == 0 {
		return false, e
	}
	return v != 0, nil
}
func nativeDescribe(h windows.Handle, pid uint32, job windows.Handle) (processRecord, error) {
	var r processRecord
	own, e := inJob(h, job)
	if e != nil || !own {
		return r, errors.New("process not in owned Job")
	}
	var c, x, k, u windows.Filetime
	if e = windows.GetProcessTimes(h, &c, &x, &k, &u); e != nil {
		return r, e
	}
	buf := make([]uint16, 32768)
	n := uint32(len(buf))
	if e = windows.QueryFullProcessImageName(h, 0, &buf[0], &n); e != nil {
		return r, e
	}
	return processRecord{PID: pid, CreationTicks: strconv.FormatUint(uint64(c.HighDateTime)<<32|uint64(c.LowDateTime), 10), Image: windows.UTF16ToString(buf[:n]), HandleHeld: true, InJob: true}, nil
}
func (k *nativeKernel) Create() (processRecord, error) {
	var empty processRecord
	k.records = map[uint32]*heldProcess{}
	var e error
	k.job, e = windows.CreateJobObject(nil, nil)
	if e != nil {
		return empty, e
	}
	limits := windows.JOBOBJECT_EXTENDED_LIMIT_INFORMATION{}
	limits.BasicLimitInformation.LimitFlags = windows.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE | windows.JOB_OBJECT_LIMIT_ACTIVE_PROCESS
	limits.BasicLimitInformation.ActiveProcessLimit = 32
	if _, e = windows.SetInformationJobObject(k.job, windows.JobObjectExtendedLimitInformation, uintptr(unsafe.Pointer(&limits)), uint32(unsafe.Sizeof(limits))); e != nil {
		return empty, e
	}
	k.port, e = windows.CreateIoCompletionPort(windows.InvalidHandle, 0, 0, 1)
	if e != nil {
		return empty, e
	}
	association := struct {
		Key  uintptr
		Port windows.Handle
	}{1, k.port}
	if _, e = windows.SetInformationJobObject(k.job, 7, uintptr(unsafe.Pointer(&association)), uint32(unsafe.Sizeof(association))); e != nil {
		return empty, e
	}
	handles := []windows.Handle{}
	for _, f := range k.stdio {
		h := windows.Handle(f.Fd())
		if e = windows.SetHandleInformation(h, windows.HANDLE_FLAG_INHERIT, windows.HANDLE_FLAG_INHERIT); e != nil {
			return empty, e
		}
		handles = append(handles, h)
	}
	attrs, e := windows.NewProcThreadAttributeList(2)
	if e != nil {
		return empty, e
	}
	defer attrs.Delete()
	if e = attrs.Update(windows.PROC_THREAD_ATTRIBUTE_HANDLE_LIST, unsafe.Pointer(&handles[0]), uintptr(len(handles))*unsafe.Sizeof(handles[0])); e != nil {
		return empty, e
	}
	if e = attrs.Update(0x0002000d, unsafe.Pointer(&k.job), unsafe.Sizeof(k.job)); e != nil {
		return empty, e
	}
	si := windows.StartupInfoEx{ProcThreadAttributeList: attrs.List()}
	si.Cb = uint32(unsafe.Sizeof(si))
	si.Flags = windows.STARTF_USESTDHANDLES
	si.StdInput = handles[0]
	si.StdOutput = handles[1]
	si.StdErr = handles[2]
	if e = windows.CreateProcess(utf(k.exe), utf(syscall.EscapeArg(k.exe)+" serve"), nil, nil, true, windows.EXTENDED_STARTUPINFO_PRESENT|windows.CREATE_NO_WINDOW|windows.CREATE_UNICODE_ENVIRONMENT|windows.CREATE_SUSPENDED, &k.env[0], utf(k.cwd), &si.StartupInfo, &k.pi); e != nil {
		return empty, e
	}
	for _, f := range k.stdio {
		f.Close()
	}
	r, e := nativeDescribe(k.pi.Process, k.pi.ProcessId, k.job)
	if e != nil {
		return empty, e
	}
	if !strings.EqualFold(r.Image, k.exe) {
		return empty, errors.New("created image differs")
	}
	k.records[k.pi.ProcessId] = &heldProcess{record: r, h: k.pi.Process}
	return r, nil
}
func (k *nativeKernel) Resume() error {
	if k.closed || k.pi.Thread == 0 {
		return errors.New("no owned suspended primary")
	}
	v, e := windows.ResumeThread(k.pi.Thread)
	if e != nil {
		return e
	}
	if v != 1 {
		return fmt.Errorf("unexpected suspend count %d", v)
	}
	return nil
}
func (k *nativeKernel) Poll(wait time.Duration) error {
	if k.closed {
		return errors.New("kernel backend closed")
	}
	if k.port == 0 {
		return nil
	}
	ms := uint32(wait / time.Millisecond)
	if ms < 1 {
		ms = 1
	}
	var msg uint32
	var key uintptr
	var over *windows.Overlapped
	e := windows.GetQueuedCompletionStatus(k.port, &msg, &key, &over, ms)
	if errors.Is(e, syscall.Errno(258)) {
		return nil
	}
	if e != nil {
		return e
	}
	if key != 1 {
		return errors.New("foreign completion key")
	}
	if msg != 6 {
		return nil
	}
	pid := uint32(uintptr(unsafe.Pointer(over)))
	if p := k.records[pid]; p != nil {
		p.record.NewEvent = true
		return nil
	}
	h, e := windows.OpenProcess(windows.PROCESS_QUERY_LIMITED_INFORMATION|windows.SYNCHRONIZE, false, pid)
	if e != nil {
		k.problems = append(k.problems, fmt.Sprintf("child %d handle missing: %v", pid, e))
		return nil
	}
	r, e := nativeDescribe(h, pid, k.job)
	if e != nil {
		windows.CloseHandle(h)
		k.problems = append(k.problems, e.Error())
		return nil
	}
	r.NewEvent = true
	k.records[pid] = &heldProcess{record: r, h: h}
	return nil
}
func (k *nativeKernel) ValidatePID(pid uint32) error {
	if k.closed {
		return errors.New("Job already closed")
	}
	p := k.records[pid]
	if p == nil {
		return errors.New("established socket owner has no held identity")
	}
	own, e := inJob(p.h, k.job)
	state, se := windows.WaitForSingleObject(p.h, 0)
	if e != nil || se != nil || !own || state != uint32(windows.WAIT_TIMEOUT) {
		return errors.New("established socket PID is not live in owned Job")
	}
	return nil
}
func (k *nativeKernel) State() kernelState {
	s := kernelState{Errors: append([]string{}, k.problems...)}
	if k.job == 0 {
		s.Errors = append(s.Errors, "Job never created")
		return s
	}
	var a accounting
	if e := windows.QueryInformationJobObject(k.job, windows.JobObjectBasicAccountingInformation, uintptr(unsafe.Pointer(&a)), uint32(unsafe.Sizeof(a)), nil); e != nil {
		s.Errors = append(s.Errors, e.Error())
		return s
	}
	s.Total = a.Total
	s.Active = a.Active
	s.Complete = uint32(len(k.records)) == a.Total && len(k.problems) == 0
	for _, p := range k.records {
		r := p.record
		state, e := windows.WaitForSingleObject(p.h, 0)
		r.Signaled = e == nil && state == windows.WAIT_OBJECT_0
		if e = windows.GetExitCodeProcess(p.h, &r.ExitCode); e != nil {
			s.Errors = append(s.Errors, e.Error())
		}
		s.Complete = s.Complete && r.Signaled && r.NewEvent
		s.Processes = append(s.Processes, r)
		if r.PID == k.pi.ProcessId {
			s.PrimarySignaled = r.Signaled
		}
	}
	sort.Slice(s.Processes, func(i, j int) bool { return s.Processes[i].PID < s.Processes[j].PID })
	return s
}
func (k *nativeKernel) Terminate() error {
	if k.closed {
		return errors.New("Job already closed")
	}
	if k.pi.Process != 0 {
		own, e := inJob(k.pi.Process, k.job)
		if e != nil || !own {
			_ = windows.TerminateProcess(k.pi.Process, 125)
			k.problems = append(k.problems, "atomic Job membership not proved; suspended returned primary fallback used")
		}
	}
	if k.job == 0 {
		return nil
	}
	return windows.TerminateJobObject(k.job, 125)
}
func (k *nativeKernel) Close() closeProof {
	// The last Job handle closes FIRST. No hashing, journal I/O, monitor join,
	// channel send or other diagnostic can stand in front of KILL_ON_CLOSE.
	p := closeProof{}
	if k.closed {
		p.Errors = append(p.Errors, "double backend close")
		return p
	}
	k.closed = true
	if k.job != 0 {
		e := windows.CloseHandle(k.job)
		p.JobClosed = e == nil
		if e != nil {
			p.Errors = append(p.Errors, e.Error())
		}
		k.job = 0
	}
	if k.pi.Process != 0 {
		state, e := windows.WaitForSingleObject(k.pi.Process, 0)
		p.PrimarySignaled = e == nil && state == windows.WAIT_OBJECT_0
	}
	if k.port != 0 {
		windows.CloseHandle(k.port)
		k.port = 0
	}
	seen := map[windows.Handle]bool{}
	for _, r := range k.records {
		seen[r.h] = true
		windows.CloseHandle(r.h)
	}
	if k.pi.Process != 0 && !seen[k.pi.Process] {
		windows.CloseHandle(k.pi.Process)
	}
	if k.pi.Thread != 0 {
		windows.CloseHandle(k.pi.Thread)
	}
	for _, f := range k.stdio {
		f.Close()
	}
	return p
}

var tcpTable = windows.NewLazySystemDLL("iphlpapi.dll").NewProc("GetExtendedTcpTable")

func establishedRows(t socketTuple) ([]tcpOwnerRow, error) {
	// OWNER_PID_CONNECTIONS=4; only exact server-side ESTABLISHED tuples are
	// returned. LISTENER snapshots never authorize an HTTP write.
	var size uint32
	r, _, _ := tcpTable.Call(0, uintptr(unsafe.Pointer(&size)), 0, 2, 4, 0)
	if r != 122 {
		return nil, fmt.Errorf("TCP owner sizing: %d", r)
	}
	if size < 4 || size > 16<<20 {
		return nil, errors.New("TCP owner table bound")
	}
	b := make([]byte, size)
	r, _, _ = tcpTable.Call(uintptr(unsafe.Pointer(&b[0])), uintptr(unsafe.Pointer(&size)), 0, 2, 4, 0)
	if r != 0 {
		return nil, fmt.Errorf("TCP owner query: %d", r)
	}
	n := binary.LittleEndian.Uint32(b[:4])
	if uint64(n)*24+4 > uint64(size) {
		return nil, errors.New("TCP owner table truncated")
	}
	rows := []tcpOwnerRow{}
	for i := uint32(0); i < n; i++ {
		raw := b[4+i*24 : 4+(i+1)*24]
		v := tcpOwnerRow{state: binary.LittleEndian.Uint32(raw[:4]), localPort: binary.BigEndian.Uint16(raw[8:10]), remotePort: binary.BigEndian.Uint16(raw[16:18]), pid: binary.LittleEndian.Uint32(raw[20:24])}
		copy(v.localIP[:], raw[4:8])
		copy(v.remoteIP[:], raw[12:16])
		if v.state == 5 && v.localIP == t.serverIP && v.remoteIP == t.clientIP && v.localPort == t.serverPort && v.remotePort == t.clientPort {
			rows = append(rows, v)
		}
	}
	return rows, nil
}
