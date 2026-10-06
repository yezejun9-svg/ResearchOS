//go:build windows

package sandbox

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"unsafe"

	"golang.org/x/sys/windows"
)

// CleanupAbandoned removes only the recorded sandbox staging after confirming
// that its exact PID/creation identity has stopped. It supplies no success or
// stream-drain evidence for the interrupted command.
func CleanupAbandoned(identity Identity) error {
	if identity.PID == 0 || identity.Created <= 0 || !strings.HasPrefix(identity.Profile, "ResearchOS.W10.") || identity.Job != "Local\\"+identity.Profile || identity.SID == "" {
		return errors.New("complete native identity required for cleanup")
	}
	h, e := windows.OpenProcess(windows.PROCESS_QUERY_LIMITED_INFORMATION|windows.SYNCHRONIZE, false, identity.PID)
	if e == nil {
		var created, exit, kernel, user windows.Filetime
		e = windows.GetProcessTimes(h, &created, &exit, &kernel, &user)
		if e == nil && created.Nanoseconds() == identity.Created {
			var state uint32
			state, e = windows.WaitForSingleObject(h, 0)
			if e == nil && state != windows.WAIT_OBJECT_0 {
				e = errors.New("sandbox still alive")
			}
		}
		windows.CloseHandle(h)
		if e != nil {
			return e
		}
	} else if !errors.Is(e, windows.ERROR_INVALID_PARAMETER) {
		return e
	}
	var derived *windows.SID
	hr, _, _ := userenv.NewProc("DeriveAppContainerSidFromAppContainerName").Call(uintptr(unsafe.Pointer(utf(identity.Profile))), uintptr(unsafe.Pointer(&derived)))
	if int32(hr) < 0 {
		return fmt.Errorf("derive sandbox SID HRESULT 0x%x", hr)
	}
	same := derived.String() == identity.SID
	windows.FreeSid(derived)
	if !same {
		return errors.New("sandbox profile SID differs from recorded identity")
	}
	root, e := filepath.Abs(os.TempDir())
	if e != nil {
		return e
	}
	target, e := filepath.Abs(identity.StagingDirectory)
	if e != nil {
		return e
	}
	relative, e := filepath.Rel(root, target)
	if e != nil || filepath.Dir(relative) != "." || !strings.HasPrefix(relative, "researchos-w10-staging-") || filepath.Clean(identity.StagingDirectory) != target {
		return errors.New("sandbox staging outside dedicated temporary root")
	}
	if _, e = os.Stat(target); e == nil {
		actual, e := filepath.EvalSymlinks(target)
		if e != nil || !strings.EqualFold(actual, target) {
			return errors.New("sandbox cleanup reparse rejected")
		}
		owned := false
		for _, name := range []string{"input", "output"} {
			sd, e := windows.GetNamedSecurityInfo(filepath.Join(target, name), windows.SE_FILE_OBJECT, windows.DACL_SECURITY_INFORMATION)
			if e == nil && strings.Contains(sd.String(), identity.SID) {
				owned = true
			}
		}
		if !owned {
			return errors.New("sandbox staging ACL no longer binds recorded SID")
		}
		if e = os.RemoveAll(target); e != nil {
			return e
		}
	} else if !os.IsNotExist(e) {
		return e
	}
	hr, _, _ = userenv.NewProc("DeleteAppContainerProfile").Call(uintptr(unsafe.Pointer(utf(identity.Profile))))
	if int32(hr) < 0 && uint32(hr) != 0x80070002 {
		return fmt.Errorf("delete sandbox profile HRESULT 0x%x", hr)
	}
	return nil
}
