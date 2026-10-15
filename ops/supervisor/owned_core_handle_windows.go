//go:build windows

package supervisor

import (
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
	"time"
	"unsafe"

	"golang.org/x/sys/windows"
)

// OwnedCoreNativeIdentity is entirely observed from retained native handles.
// ParentProcessID comes from one Toolhelp snapshot and is then bound to its
// own retained process handle, creation time, SID and image file identity.
type OwnedCoreNativeIdentity struct {
	PID               uint32 `json:"pid"`
	CreatedNS         int64  `json:"created_ns"`
	SID               string `json:"sid"`
	ImagePath         string `json:"image_path"`
	ImageSHA256       string `json:"image_sha256"`
	ImageVolume       uint32 `json:"image_volume"`
	ImageIndex        uint64 `json:"image_index"`
	ParentPID         uint32 `json:"parent_pid"`
	ParentCreatedNS   int64  `json:"parent_created_ns"`
	ParentSID         string `json:"parent_sid"`
	ParentImagePath   string `json:"parent_image_path"`
	ParentImageSHA256 string `json:"parent_image_sha256"`
	ParentImageVolume uint32 `json:"parent_image_volume"`
	ParentImageIndex  uint64 `json:"parent_image_index"`
}

type ownedNativeProcess struct {
	handle  windows.Handle
	image   *os.File
	path    string
	created int64
	sid     string
	sha     string
	volume  uint32
	index   uint64
}

func (p *ownedNativeProcess) close() {
	if p.image != nil {
		_ = p.image.Close()
		p.image = nil
	}
	if p.handle != 0 {
		_ = windows.CloseHandle(p.handle)
		p.handle = 0
	}
}

func ownedNativePath(h windows.Handle) (string, error) {
	buf := make([]uint16, 32768)
	size := uint32(len(buf))
	if err := windows.QueryFullProcessImageName(h, 0, &buf[0], &size); err != nil {
		return "", err
	}
	path := windows.UTF16ToString(buf[:size])
	if !filepath.IsAbs(path) || filepath.Clean(path) != path || !strings.EqualFold(filepath.Ext(path), ".exe") {
		return "", errors.New("canonical executable path required")
	}
	actual, err := filepath.EvalSymlinks(path)
	if err != nil || !strings.EqualFold(actual, path) {
		return "", errors.New("executable path reparse rejected")
	}
	return path, nil
}

func ownedNativeImage(path string) (*os.File, string, uint32, uint64, error) {
	wide, err := windows.UTF16PtrFromString(path)
	if err != nil {
		return nil, "", 0, 0, err
	}
	h, err := windows.CreateFile(wide, windows.GENERIC_READ, windows.FILE_SHARE_READ, nil, windows.OPEN_EXISTING, windows.FILE_FLAG_OPEN_REPARSE_POINT, 0)
	if err != nil {
		return nil, "", 0, 0, err
	}
	f := os.NewFile(uintptr(h), path)
	var before windows.ByHandleFileInformation
	if err = windows.GetFileInformationByHandle(h, &before); err != nil {
		f.Close()
		return nil, "", 0, 0, err
	}
	if before.FileAttributes&(windows.FILE_ATTRIBUTE_REPARSE_POINT|windows.FILE_ATTRIBUTE_DIRECTORY) != 0 || before.NumberOfLinks != 1 || before.FileSizeHigh != 0 || before.FileSizeLow > 256<<20 {
		f.Close()
		return nil, "", 0, 0, errors.New("image reparse/alias/size rejected")
	}
	hash := sha256.New()
	n, err := io.Copy(hash, io.LimitReader(f, 256<<20+1))
	if err != nil {
		f.Close()
		return nil, "", 0, 0, err
	}
	var after windows.ByHandleFileInformation
	if err = windows.GetFileInformationByHandle(h, &after); err != nil {
		f.Close()
		return nil, "", 0, 0, err
	}
	if n != int64(before.FileSizeLow) || before.VolumeSerialNumber != after.VolumeSerialNumber || before.FileIndexHigh != after.FileIndexHigh || before.FileIndexLow != after.FileIndexLow || before.FileSizeLow != after.FileSizeLow || before.LastWriteTime != after.LastWriteTime {
		f.Close()
		return nil, "", 0, 0, errors.New("image changed during retained read")
	}
	return f, hex.EncodeToString(hash.Sum(nil)), before.VolumeSerialNumber, uint64(before.FileIndexHigh)<<32 | uint64(before.FileIndexLow), nil
}

func ownedNativeProcessFromHandle(h windows.Handle) (p ownedNativeProcess, err error) {
	p = ownedNativeProcess{handle: h}
	defer func() {
		if err != nil {
			p.close()
		}
	}()
	var created, exited, kernel, user windows.Filetime
	if err = windows.GetProcessTimes(h, &created, &exited, &kernel, &user); err != nil {
		return p, err
	}
	p.created = created.Nanoseconds()
	var token windows.Token
	if err = windows.OpenProcessToken(h, windows.TOKEN_QUERY, &token); err != nil {
		return p, err
	}
	tu, e := token.GetTokenUser()
	_ = token.Close()
	if e != nil || tu.User.Sid == nil || !tu.User.Sid.IsValid() {
		return p, errors.New("process SID unavailable")
	}
	p.sid = tu.User.Sid.String()
	if p.path, err = ownedNativePath(h); err != nil {
		return p, err
	}
	p.image, p.sha, p.volume, p.index, err = ownedNativeImage(p.path)
	return p, err
}

func ownedNativeParentPID(pid uint32) (uint32, error) {
	snap, err := windows.CreateToolhelp32Snapshot(windows.TH32CS_SNAPPROCESS, 0)
	if err != nil {
		return 0, err
	}
	defer windows.CloseHandle(snap)
	entry := windows.ProcessEntry32{Size: uint32(unsafe.Sizeof(windows.ProcessEntry32{}))}
	if err = windows.Process32First(snap, &entry); err != nil {
		return 0, err
	}
	for {
		if entry.ProcessID == pid {
			if entry.ParentProcessID == 0 || entry.ParentProcessID == pid {
				return 0, errors.New("invalid parent identity")
			}
			return entry.ParentProcessID, nil
		}
		err = windows.Process32Next(snap, &entry)
		if errors.Is(err, windows.ERROR_NO_MORE_FILES) {
			break
		}
		if err != nil {
			return 0, err
		}
	}
	return 0, errors.New("process absent from snapshot")
}

// OwnedCoreRetainedHandle is the sole native termination capability. The
// capability never exports its process handle. The caller must first verify
// the reviewed plan and all external proofs before opening it.
type OwnedCoreRetainedHandle struct {
	core           ownedNativeProcess
	parent         ownedNativeProcess
	identity       OwnedCoreNativeIdentity
	terminateCalls int
	closed         bool
	// Per-handle native call seams allow deterministic failure-path fixture cuts.
	// Nil always uses the Windows APIs; callers outside this package cannot set them.
	terminate func(windows.Handle, uint32) error
	wait      func(windows.Handle, uint32) (uint32, error)
}

func (h *OwnedCoreRetainedHandle) nativeWait(ms uint32) (uint32, error) {
	if h.wait != nil {
		return h.wait(h.core.handle, ms)
	}
	return windows.WaitForSingleObject(h.core.handle, ms)
}

func (h *OwnedCoreRetainedHandle) nativeTerminate(code uint32) error {
	if h.terminate != nil {
		return h.terminate(h.core.handle, code)
	}
	return windows.TerminateProcess(h.core.handle, code)
}

func ownedCoreOpen(pid uint32, access uint32) (out *OwnedCoreRetainedHandle, err error) {
	if pid == 0 {
		return nil, errors.New("zero PID")
	}
	h, err := windows.OpenProcess(access|windows.PROCESS_QUERY_LIMITED_INFORMATION|windows.SYNCHRONIZE, false, pid)
	if err != nil {
		return nil, err
	}
	out = &OwnedCoreRetainedHandle{}
	defer func() {
		if err != nil {
			out.Close()
			out = nil
		}
	}()
	out.core, err = ownedNativeProcessFromHandle(h)
	if err != nil {
		return nil, err
	}
	actualPID, e := windows.GetProcessId(out.core.handle)
	if e != nil || actualPID != pid {
		return nil, errors.New("process handle PID mismatch")
	}
	parentPID, e := ownedNativeParentPID(pid)
	if e != nil {
		return nil, e
	}
	parentH, e := windows.OpenProcess(windows.PROCESS_QUERY_LIMITED_INFORMATION|windows.SYNCHRONIZE, false, parentPID)
	if e != nil {
		return nil, e
	}
	out.parent, err = ownedNativeProcessFromHandle(parentH)
	if err != nil {
		return nil, err
	}
	actualParent, e := windows.GetProcessId(out.parent.handle)
	if e != nil || actualParent != parentPID {
		return nil, errors.New("parent handle PID mismatch")
	}
	out.identity = OwnedCoreNativeIdentity{PID: pid, CreatedNS: out.core.created, SID: out.core.sid, ImagePath: out.core.path, ImageSHA256: out.core.sha, ImageVolume: out.core.volume, ImageIndex: out.core.index, ParentPID: parentPID, ParentCreatedNS: out.parent.created, ParentSID: out.parent.sid, ParentImagePath: out.parent.path, ParentImageSHA256: out.parent.sha, ParentImageVolume: out.parent.volume, ParentImageIndex: out.parent.index}
	return out, nil
}

// ObserveOwnedCoreReadOnly cannot terminate. It is suitable for preflight.
func ObserveOwnedCoreReadOnly(pid uint32) (OwnedCoreNativeIdentity, error) {
	h, err := ownedCoreOpen(pid, 0)
	if err != nil {
		return OwnedCoreNativeIdentity{}, err
	}
	defer h.Close()
	return h.identity, nil
}

// OpenOwnedCoreRetained binds the sole termination handle to a complete exact
// native identity obtained during reviewed preflight. It cannot accept a
// partial PID-only expectation.
func OpenOwnedCoreRetained(expected OwnedCoreNativeIdentity) (*OwnedCoreRetainedHandle, error) {
	if expected.PID == 0 || expected.CreatedNS == 0 || expected.SID == "" || expected.ImageSHA256 == "" || expected.ImagePath == "" || expected.ImageIndex == 0 || expected.ParentPID == 0 || expected.ParentCreatedNS == 0 || expected.ParentSID == "" || expected.ParentImageSHA256 == "" || expected.ParentImageIndex == 0 {
		return nil, errors.New("complete reviewed native identity required")
	}
	h, err := ownedCoreOpen(expected.PID, windows.PROCESS_TERMINATE)
	if err != nil {
		return nil, err
	}
	if h.identity != expected {
		h.Close()
		return nil, errors.New("retained native identity differs from plan")
	}
	return h, nil
}

func (h *OwnedCoreRetainedHandle) Identity() OwnedCoreNativeIdentity {
	if h == nil {
		return OwnedCoreNativeIdentity{}
	}
	return h.identity
}

func (h *OwnedCoreRetainedHandle) verifyRetained() error {
	if h == nil || h.closed || h.core.handle == 0 {
		return errors.New("native handle closed")
	}
	pid, err := windows.GetProcessId(h.core.handle)
	if err != nil || pid != h.identity.PID {
		return errors.New("retained PID changed")
	}
	var created, exited, kernel, user windows.Filetime
	if err = windows.GetProcessTimes(h.core.handle, &created, &exited, &kernel, &user); err != nil || created.Nanoseconds() != h.identity.CreatedNS {
		return errors.New("retained process creation changed")
	}
	// File share mode prevents replacement while the retained image is open.
	var info windows.ByHandleFileInformation
	if err = windows.GetFileInformationByHandle(windows.Handle(h.core.image.Fd()), &info); err != nil || info.VolumeSerialNumber != h.identity.ImageVolume || uint64(info.FileIndexHigh)<<32|uint64(info.FileIndexLow) != h.identity.ImageIndex {
		return errors.New("retained image file changed")
	}
	return nil
}

// OwnedCoreNativeExit records whether the one call was made and the numeric
// exit code from the same retained handle. Unknown wait is never retried.
type OwnedCoreNativeExit struct {
	TerminateCalls int    `json:"terminate_calls"`
	ExitObserved   bool   `json:"exit_observed"`
	ExitCode       uint32 `json:"exit_code"`
	BeforeSignal   bool   `json:"before_signal"`
}

const OwnedCoreMaintenanceExitCode uint32 = 0x52534f53

func (h *OwnedCoreRetainedHandle) TerminateOnceAndWait(timeout time.Duration) (OwnedCoreNativeExit, error) {
	var out OwnedCoreNativeExit
	if timeout <= 0 || timeout > 30*time.Second {
		return out, errors.New("bounded native wait required")
	}
	if err := h.verifyRetained(); err != nil {
		return out, err
	}
	if h.terminateCalls != 0 {
		return out, errors.New("native termination already attempted")
	}
	status, err := h.nativeWait(0)
	if err != nil {
		return out, err
	}
	if status == windows.WAIT_OBJECT_0 {
		out.BeforeSignal = true
		out.ExitObserved = true
		if err = windows.GetExitCodeProcess(h.core.handle, &out.ExitCode); err != nil {
			return out, err
		}
		return out, nil
	}
	if status != uint32(windows.WAIT_TIMEOUT) {
		return out, fmt.Errorf("unexpected native wait status %d", status)
	}
	h.terminateCalls = 1
	out.TerminateCalls = 1
	if err = h.nativeTerminate(OwnedCoreMaintenanceExitCode); err != nil {
		return out, fmt.Errorf("one TerminateProcess failed: %w", err)
	}
	status, err = h.nativeWait(uint32(timeout.Milliseconds()))
	if err != nil || status != windows.WAIT_OBJECT_0 {
		return out, fmt.Errorf("native wait unknown: status=%d err=%v", status, err)
	}
	out.ExitObserved = true
	if err = windows.GetExitCodeProcess(h.core.handle, &out.ExitCode); err != nil {
		return out, err
	}
	return out, nil
}

func (h *OwnedCoreRetainedHandle) Close() {
	if h == nil || h.closed {
		return
	}
	h.closed = true
	h.core.close()
	h.parent.close()
}
