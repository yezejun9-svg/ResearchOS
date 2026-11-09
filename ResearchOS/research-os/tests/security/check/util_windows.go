//go:build windows

package main

import (
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"syscall"
	"unsafe"

	"golang.org/x/sys/windows"

	"researchos.local/research-os/internal/auth"
)

// foreignAccountPID finds a live process owned by a different OS account, which is how the check
// proves the peer check is an actual account comparison rather than "the pipe ACL looked right".
func foreignAccountPID() (uint32, error) {
	self, err := auth.Current()
	if err != nil {
		return 0, err
	}
	snap, err := windows.CreateToolhelp32Snapshot(windows.TH32CS_SNAPPROCESS, 0)
	if err != nil {
		return 0, err
	}
	defer windows.CloseHandle(snap)
	var entry windows.ProcessEntry32
	entry.Size = uint32(unsafe.Sizeof(entry))
	if err := windows.Process32First(snap, &entry); err != nil {
		return 0, err
	}
	tried := 0
	for {
		tried++
		pid := entry.ProcessID
		if err := windows.Process32Next(snap, &entry); err != nil {
			break
		}
		if pid == uint32(os.Getpid()) || pid <= 4 || tried > 200 {
			continue
		}
		peer, perr := auth.ProcessIdentity(pid)
		if perr != nil || peer.VID == "" {
			continue
		}
		if !self.SameUser(peer) {
			return pid, nil
		}
	}
	return 0, errors.New("no foreign-account process was inspectable on this machine")
}

// makeJunction replaces dir with an NTFS junction to target using the shell's own mklink, which
// works without elevation. Returns whether the swap actually happened so the check can disclose a
// skipped case instead of claiming it.
func makeJunction(dir, target string) (bool, string) {
	if err := os.RemoveAll(dir); err != nil {
		return false, "could not clear the directory: " + err.Error()
	}
	cmd := exec.Command("cmd", "/c", "mklink", "/J", dir, target)
	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	out, err := cmd.CombinedOutput()
	if err != nil {
		os.MkdirAll(dir, 0o755)
		return false, "mklink /J refused: " + strings.TrimSpace(string(out)) + " " + err.Error()
	}
	return true, ""
}

func removeJunction(dir string) {
	exec.Command("cmd", "/c", "rmdir", dir).Run()
	os.RemoveAll(dir)
}

// openForSecurity walks the file with a handle only (no data read) so the ACL can be inspected.
func openForSecurity(path string, directory bool) (windows.Handle, error) {
	wide, err := windows.UTF16PtrFromString(path)
	if err != nil {
		return 0, err
	}
	flags := uint32(windows.FILE_FLAG_BACKUP_SEMANTICS)
	if !directory {
		flags |= 0
	}
	h, err := windows.CreateFile(wide, windows.READ_CONTROL, windows.FILE_SHARE_READ|windows.FILE_SHARE_WRITE|windows.FILE_SHARE_DELETE,
		nil, windows.OPEN_EXISTING, flags, 0)
	if err != nil {
		return 0, err
	}
	return h, nil
}

// aclGrantsOnlyCurrentUser returns "" when the object's protected DACL contains exactly one
// ACCESS_ALLOWED ACE for the current user SID, and the reason it does not otherwise. POSIX mode
// bits mean nothing on NTFS, so this is the only honest privacy assertion.
func aclGrantsOnlyCurrentUser(path string, directory bool) string {
	h, err := openForSecurity(path, directory)
	if err != nil {
		return "cannot open " + filepath.Base(path) + ": " + err.Error()
	}
	defer windows.CloseHandle(h)
	sd, err := windows.GetSecurityInfo(h, windows.SE_FILE_OBJECT,
		windows.OWNER_SECURITY_INFORMATION|windows.DACL_SECURITY_INFORMATION)
	if err != nil || sd == nil || !sd.IsValid() {
		return "security info unavailable: " + fmt.Sprint(err)
	}
	control, _, err := sd.Control()
	if err != nil || control&windows.SE_DACL_PROTECTED == 0 {
		return "DACL is not protected (inheritance allowed)"
	}
	owner, _, err := sd.Owner()
	if err != nil || owner == nil {
		return "owner unavailable"
	}
	self := currentUserSIDString()
	if owner.String() != self {
		return "owner is " + owner.String() + ", expected the current user"
	}
	acl, _, err := sd.DACL()
	if err != nil || acl == nil {
		return "DACL unavailable"
	}
	if acl.AceCount != 1 {
		return fmt.Sprintf("DACL has %daces, expected exactly the current user", acl.AceCount)
	}
	var ace *windows.ACCESS_ALLOWED_ACE
	if err := windows.GetAce(acl, 0, &ace); err != nil || ace == nil {
		return "ACE unreadable"
	}
	if ace.Header.AceType != windows.ACCESS_ALLOWED_ACE_TYPE {
		return "ACE is not allow-type"
	}
	trustee := (*windows.SID)(unsafe.Pointer(&ace.SidStart))
	if trustee == nil || !trustee.IsValid() || trustee.String() != self {
		return "ACE trustee is not the current user"
	}
	return ""
}

func fileGrantsOnlyCurrentUser(path string) string { return aclGrantsOnlyCurrentUser(path, false) }
func dirGrantsOnlyCurrentUser(path string) string  { return aclGrantsOnlyCurrentUser(path, true) }

func currentUserSIDString() string {
	tu, err := windows.GetCurrentProcessToken().GetTokenUser()
	if err != nil || tu.User.Sid == nil {
		return ""
	}
	return tu.User.Sid.String()
}
