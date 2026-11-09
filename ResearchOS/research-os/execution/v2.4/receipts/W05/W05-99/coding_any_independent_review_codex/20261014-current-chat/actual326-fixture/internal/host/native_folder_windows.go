//go:build windows

package host

import (
	"fmt"
	"runtime"
	"syscall"
	"unsafe"

	"golang.org/x/sys/windows"
)

// browseInfoW matches the Windows BROWSEINFOW layout. The selected PIDL is
// converted to a filesystem path and freed before it reaches root registration.
type browseInfoW struct {
	owner       uintptr
	root        uintptr
	displayName *uint16
	title       *uint16
	flags       uint32
	callback    uintptr
	callbackArg uintptr
	image       int32
}

const (
	bifReturnOnlyFileSystemDirs = 0x0001
	bffmInitialized             = 1
	bffmSetSelectionW           = 0x0467
)

var (
	shell32Browse = windows.NewLazySystemDLL("shell32.dll").NewProc("SHBrowseForFolderW")
	shell32Path   = windows.NewLazySystemDLL("shell32.dll").NewProc("SHGetPathFromIDListEx")
	ole32Free     = windows.NewLazySystemDLL("ole32.dll").NewProc("CoTaskMemFree")
	user32Send    = windows.NewLazySystemDLL("user32.dll").NewProc("SendMessageW")
)

// chooseNativeFolderWindows is called only after the pipe ACL and peer SID
// checks. A client-supplied path merely preselects the dialog; the returned
// path always comes from the folder the local user confirmed in the Shell UI.
func chooseNativeFolderWindows(initial string) (string, error) {
	runtime.LockOSThread()
	defer runtime.UnlockOSThread()
	title, err := windows.UTF16PtrFromString("Select a ResearchOS workspace folder")
	if err != nil {
		return "", err
	}
	var initialPath *uint16
	if initial != "" {
		initialPath, err = windows.UTF16PtrFromString(initial)
		if err != nil {
			return "", fmt.Errorf("%w: invalid suggested folder", ErrFrameShape)
		}
	}
	var callback uintptr
	if initialPath != nil {
		callback = syscall.NewCallback(func(hwnd uintptr, message uint32, _ uintptr, suggested uintptr) uintptr {
			if message == bffmInitialized && suggested != 0 {
				user32Send.Call(hwnd, bffmSetSelectionW, 1, suggested)
			}
			return 0
		})
	}
	var display [260]uint16
	info := browseInfoW{displayName: &display[0], title: title,
		flags: bifReturnOnlyFileSystemDirs, callback: callback,
		callbackArg: uintptr(unsafe.Pointer(initialPath))}
	selected, _, _ := shell32Browse.Call(uintptr(unsafe.Pointer(&info)))
	runtime.KeepAlive(initialPath)
	runtime.KeepAlive(title)
	if selected == 0 {
		return "", fmt.Errorf("%w: folder selection cancelled", ErrFrameShape)
	}
	defer ole32Free.Call(selected)
	var pathBuffer [32768]uint16
	ok, _, _ := shell32Path.Call(selected, uintptr(unsafe.Pointer(&pathBuffer[0])), uintptr(len(pathBuffer)), 0)
	if ok == 0 {
		return "", fmt.Errorf("%w: selected item is not a filesystem folder", ErrFrameShape)
	}
	chosen := windows.UTF16ToString(pathBuffer[:])
	if chosen == "" {
		return "", fmt.Errorf("%w: no filesystem folder selected", ErrFrameShape)
	}
	return chosen, nil
}
