//go:build windows

package supervisor

import (
	"context"
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
	image   *ownedImageFile
	path    string
	created int64
	sid     string
	sha     string
	volume  uint32
	index   uint64
}

type ownedImageAnchor struct {
	handle   windows.Handle
	volume   uint32
	index    uint64
	security string
}

type ownedImageFile struct {
	file      *os.File
	ancestors []ownedImageAnchor
	final     ownedImageAnchor
	sha       string
}

func (im *ownedImageFile) Close() {
	if im == nil {
		return
	}
	if im.file != nil {
		_ = im.file.Close()
		im.file = nil
	}
	for i := len(im.ancestors) - 1; i >= 0; i-- {
		_ = windows.CloseHandle(im.ancestors[i].handle)
	}
	im.ancestors = nil
}

func (p *ownedNativeProcess) close() {
	if p.image != nil {
		p.image.Close()
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
	if !filepath.IsAbs(path) || filepath.Clean(path) != path || len(filepath.VolumeName(path)) != 2 || strings.Contains(path[2:], ":") || !strings.EqualFold(filepath.Ext(path), ".exe") {
		return "", errors.New("canonical executable path required")
	}
	return path, nil
}

func observeOwnedImageAnchor(h windows.Handle, directory bool) (ownedImageAnchor, windows.ByHandleFileInformation, error) {
	var info windows.ByHandleFileInformation
	if err := windows.GetFileInformationByHandle(h, &info); err != nil {
		return ownedImageAnchor{}, info, err
	}
	if info.FileAttributes&windows.FILE_ATTRIBUTE_REPARSE_POINT != 0 || (info.FileAttributes&windows.FILE_ATTRIBUTE_DIRECTORY != 0) != directory || info.VolumeSerialNumber == 0 || uint64(info.FileIndexHigh)<<32|uint64(info.FileIndexLow) == 0 || (!directory && info.NumberOfLinks != 1) {
		return ownedImageAnchor{}, info, errors.New("image ancestor reparse/alias/native identity rejected")
	}
	sd, err := windows.GetSecurityInfo(h, windows.SE_FILE_OBJECT, windows.OWNER_SECURITY_INFORMATION|windows.DACL_SECURITY_INFORMATION)
	if err != nil || sd == nil || !sd.IsValid() {
		return ownedImageAnchor{}, info, errors.New("image native security descriptor unavailable")
	}
	owner, _, err := sd.Owner()
	if err != nil || owner == nil || !owner.IsValid() {
		return ownedImageAnchor{}, info, errors.New("image ancestor owner unavailable")
	}
	acl, _, err := sd.DACL()
	if err != nil || acl == nil || acl.AceCount == 0 {
		return ownedImageAnchor{}, info, errors.New("image ancestor DACL unavailable")
	}
	security := sd.String()
	if security == "" {
		return ownedImageAnchor{}, info, errors.New("image ancestor owner/DACL serialization unavailable")
	}
	return ownedImageAnchor{handle: h, volume: info.VolumeSerialNumber, index: uint64(info.FileIndexHigh)<<32 | uint64(info.FileIndexLow), security: security}, info, nil
}

func ownedNativeImage(path string) (_ *ownedImageFile, err error) {
	image := &ownedImageFile{}
	defer func() {
		if err != nil {
			image.Close()
		}
	}()
	volume := filepath.VolumeName(path)
	current := volume + string(filepath.Separator)
	parts := strings.Split(strings.TrimPrefix(path[len(volume):], string(filepath.Separator)), string(filepath.Separator))
	paths := []string{current}
	for _, part := range parts {
		if part == "" || part == "." || part == ".." {
			return nil, errors.New("noncanonical image path component")
		}
		current = filepath.Join(current, part)
		paths = append(paths, current)
	}
	for i, name := range paths {
		last := i == len(paths)-1
		wide, e := windows.UTF16PtrFromString(name)
		if e != nil {
			return nil, e
		}
		access := uint32(windows.FILE_READ_ATTRIBUTES | windows.READ_CONTROL)
		share := uint32(windows.FILE_SHARE_READ | windows.FILE_SHARE_WRITE)
		if last {
			access = windows.GENERIC_READ | windows.READ_CONTROL
			share = windows.FILE_SHARE_READ
		}
		h, e := windows.CreateFile(wide, access, share, nil, windows.OPEN_EXISTING, windows.FILE_FLAG_OPEN_REPARSE_POINT|windows.FILE_FLAG_BACKUP_SEMANTICS, 0)
		if e != nil {
			return nil, e
		}
		anchor, info, e := observeOwnedImageAnchor(h, !last)
		if e != nil {
			_ = windows.CloseHandle(h)
			return nil, e
		}
		if last {
			if info.FileSizeHigh != 0 || info.FileSizeLow == 0 || info.FileSizeLow > 256<<20 {
				_ = windows.CloseHandle(h)
				return nil, errors.New("bounded image size required")
			}
			image.final = anchor
			image.file = os.NewFile(uintptr(h), name)
			hash := sha256.New()
			var n int64
			n, err = io.Copy(hash, io.LimitReader(image.file, 256<<20+1))
			if err != nil {
				return nil, err
			}
			var after windows.ByHandleFileInformation
			if err = windows.GetFileInformationByHandle(h, &after); err != nil {
				return nil, err
			}
			if n != int64(info.FileSizeLow) || info.VolumeSerialNumber != after.VolumeSerialNumber || info.FileIndexHigh != after.FileIndexHigh || info.FileIndexLow != after.FileIndexLow || info.FileSizeLow != after.FileSizeLow || info.LastWriteTime != after.LastWriteTime {
				return nil, errors.New("image changed during retained read")
			}
			image.sha = hex.EncodeToString(hash.Sum(nil))
		} else {
			image.ancestors = append(image.ancestors, anchor)
		}
	}
	return image, nil
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
	p.image, err = ownedNativeImage(p.path)
	if err == nil {
		p.sha, p.volume, p.index = p.image.sha, p.image.final.volume, p.image.final.index
	}
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

func verifyOwnedImageFile(image *ownedImageFile, volume uint32, index uint64) error {
	if image == nil || image.file == nil || image.final.volume != volume || image.final.index != index {
		return errors.New("retained image identity absent")
	}
	for _, original := range image.ancestors {
		current, _, err := observeOwnedImageAnchor(original.handle, true)
		if err != nil || current.volume != original.volume || current.index != original.index || current.security != original.security {
			return errors.New("retained image ancestor identity/ACL changed")
		}
	}
	current, _, err := observeOwnedImageAnchor(windows.Handle(image.file.Fd()), false)
	if err != nil || current.volume != image.final.volume || current.index != image.final.index || current.security != image.final.security {
		return errors.New("retained image file identity/ACL changed")
	}
	return nil
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
	// Every path component remains open without delete sharing. The final image
	// also denies write sharing; identity and security are rechecked by handle.
	if err = verifyOwnedImageFile(h.core.image, h.identity.ImageVolume, h.identity.ImageIndex); err != nil {
		return err
	}
	parentPID, err := windows.GetProcessId(h.parent.handle)
	if err != nil || parentPID != h.identity.ParentPID {
		return errors.New("retained parent PID changed")
	}
	if err = windows.GetProcessTimes(h.parent.handle, &created, &exited, &kernel, &user); err != nil || created.Nanoseconds() != h.identity.ParentCreatedNS {
		return errors.New("retained parent creation changed")
	}
	parentStatus, err := h.nativeParentWait()
	if err != nil || parentStatus != uint32(windows.WAIT_TIMEOUT) {
		return errors.New("retained parent no longer live")
	}
	if err = verifyOwnedImageFile(h.parent.image, h.identity.ParentImageVolume, h.identity.ParentImageIndex); err != nil {
		return err
	}
	return nil
}

func (h *OwnedCoreRetainedHandle) nativeParentWait() (uint32, error) {
	return windows.WaitForSingleObject(h.parent.handle, 0)
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
	return h.TerminateOnceAndWaitUntil(timeout, time.Now().Add(time.Hour), time.Now().Add(time.Hour))
}

// TerminateOnceAndWaitUntil applies both the invocation monotonic deadline and
// the grant's wall expiry at the last native boundary, after pre-signal waits.
// A failed deadline check returns with zero TerminateProcess calls; the caller's
// already-durable intent remains consumed.
func (h *OwnedCoreRetainedHandle) TerminateOnceAndWaitUntil(timeout time.Duration, invocationDeadline, wallExpiry time.Time) (OwnedCoreNativeExit, error) {
	return h.TerminateOnceAndWaitUntilContext(context.Background(), timeout, invocationDeadline, wallExpiry)
}

func (h *OwnedCoreRetainedHandle) TerminateOnceAndWaitUntilContext(ctx context.Context, timeout time.Duration, invocationDeadline, wallExpiry time.Time) (OwnedCoreNativeExit, error) {
	var out OwnedCoreNativeExit
	if ctx == nil {
		return out, errors.New("caller context required")
	}
	if timeout <= 0 || timeout > 30*time.Second {
		return out, errors.New("bounded native wait required")
	}
	if earlier, ok := ctx.Deadline(); ok && earlier.Before(invocationDeadline) {
		invocationDeadline = earlier
	}
	if err := ctx.Err(); err != nil {
		return out, fmt.Errorf("caller unavailable before native signal: %w", err)
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
	if err := ctx.Err(); err != nil {
		return out, fmt.Errorf("caller unavailable before native signal: %w", err)
	}
	if now := time.Now(); !now.Before(invocationDeadline) || !now.Before(wallExpiry) {
		return out, errors.New("invocation or grant expired before native signal")
	}
	if err := ctx.Err(); err != nil {
		return out, fmt.Errorf("caller unavailable before native signal: %w", err)
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
