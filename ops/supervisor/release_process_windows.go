//go:build windows

package supervisor

import (
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

	"golang.org/x/sys/windows"
)

type ProcessIdentity struct {
	PID         uint32
	CreatedNS   int64
	ImageSHA256 string
}

type ProcessDriver interface {
	Start(image, token, data string) (ProcessIdentity, error)
	Alive(ProcessIdentity) (bool, error)
	Stop(ProcessIdentity) error
}

// NativeFixtureDriver runs children under the caller's Windows identity. It
// proves actual process mechanics only; it is not an SCM service or an ACL
// boundary. Args must bind the operation token and data root in the child.
type NativeFixtureDriver struct {
	Args func(token, data string) []string
}

func exactImage(path string) (string, string, error) {
	if !filepath.IsAbs(path) || !strings.EqualFold(filepath.Ext(path), ".exe") {
		return "", "", errors.New("absolute executable required")
	}
	actual, e := filepath.EvalSymlinks(path)
	if e != nil || !strings.EqualFold(filepath.Clean(path), filepath.Clean(actual)) {
		return "", "", errors.New("executable reparse rejected")
	}
	f, e := os.Open(actual)
	if e != nil {
		return "", "", e
	}
	defer f.Close()
	info, e := f.Stat()
	if e != nil || !info.Mode().IsRegular() || info.Size() > 128*1024*1024 {
		return "", "", errors.New("bounded regular executable required")
	}
	b, e := os.ReadFile(actual)
	if e != nil {
		return "", "", e
	}
	sum := sha256.Sum256(b)
	return actual, hex.EncodeToString(sum[:]), nil
}

func processCreated(pid uint32) (int64, bool, error) {
	h, e := windows.OpenProcess(windows.PROCESS_QUERY_LIMITED_INFORMATION|windows.SYNCHRONIZE, false, pid)
	if errors.Is(e, windows.ERROR_INVALID_PARAMETER) {
		return 0, false, nil
	}
	if e != nil {
		return 0, false, e
	}
	defer windows.CloseHandle(h)
	var c, x, k, u windows.Filetime
	if e = windows.GetProcessTimes(h, &c, &x, &k, &u); e != nil {
		return 0, false, e
	}
	w, e := windows.WaitForSingleObject(h, 0)
	if e != nil {
		return 0, false, e
	}
	return c.Nanoseconds(), w != windows.WAIT_OBJECT_0, nil
}

func processImageDigest(h windows.Handle) (string, error) {
	buf := make([]uint16, 32768)
	size := uint32(len(buf))
	if e := windows.QueryFullProcessImageName(h, 0, &buf[0], &size); e != nil {
		return "", e
	}
	_, digest, e := exactImage(windows.UTF16ToString(buf[:size]))
	return digest, e
}

func (d NativeFixtureDriver) Start(image, token, data string) (ProcessIdentity, error) {
	if d.Args == nil || token == "" || !filepath.IsAbs(data) {
		return ProcessIdentity{}, errors.New("fixture args/token/data binding required")
	}
	actual, digest, e := exactImage(image)
	if e != nil {
		return ProcessIdentity{}, e
	}
	cmd := exec.Command(actual, d.Args(token, data)...)
	cmd.Dir = filepath.Dir(actual)
	cmd.SysProcAttr = &windows.SysProcAttr{CreationFlags: windows.CREATE_NEW_PROCESS_GROUP}
	if e = cmd.Start(); e != nil {
		return ProcessIdentity{}, e
	}
	go func() { _ = cmd.Wait() }()
	created, alive, e := processCreated(uint32(cmd.Process.Pid))
	if e != nil || !alive {
		_ = cmd.Process.Kill()
		return ProcessIdentity{}, fmt.Errorf("child exited before identity capture: %v", e)
	}
	return ProcessIdentity{PID: uint32(cmd.Process.Pid), CreatedNS: created, ImageSHA256: digest}, nil
}

func (d NativeFixtureDriver) Alive(p ProcessIdentity) (bool, error) {
	if p.PID == 0 || p.CreatedNS == 0 || !validDigest(p.ImageSHA256) {
		return false, errors.New("incomplete process identity")
	}
	h, e := windows.OpenProcess(windows.PROCESS_QUERY_LIMITED_INFORMATION|windows.SYNCHRONIZE, false, p.PID)
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
	created := c.Nanoseconds()
	if created != p.CreatedNS {
		return false, errors.New("PID belongs to another process")
	}
	w, e := windows.WaitForSingleObject(h, 0)
	if e != nil {
		return false, e
	}
	if w == windows.WAIT_OBJECT_0 {
		return false, nil
	}
	digest, e := processImageDigest(h)
	if e != nil || digest != p.ImageSHA256 {
		return false, errors.New("process executable changed")
	}
	return true, nil
}

func (d NativeFixtureDriver) Stop(p ProcessIdentity) error {
	alive, e := d.Alive(p)
	if e != nil {
		return e
	}
	if !alive {
		return nil
	}
	h, e := windows.OpenProcess(windows.PROCESS_TERMINATE|windows.PROCESS_QUERY_LIMITED_INFORMATION|windows.SYNCHRONIZE, false, p.PID)
	if e != nil {
		return e
	}
	defer windows.CloseHandle(h)
	var c, x, k, u windows.Filetime
	if e = windows.GetProcessTimes(h, &c, &x, &k, &u); e != nil || c.Nanoseconds() != p.CreatedNS {
		return errors.New("process identity changed before stop")
	}
	digest, e := processImageDigest(h)
	if e != nil || digest != p.ImageSHA256 {
		return errors.New("process image changed before stop")
	}
	if e = windows.TerminateProcess(h, 1); e != nil {
		return e
	}
	w, e := windows.WaitForSingleObject(h, 15000)
	if e != nil || w != windows.WAIT_OBJECT_0 {
		return fmt.Errorf("process stop not observed: wait=%d error=%v", w, e)
	}
	return nil
}
