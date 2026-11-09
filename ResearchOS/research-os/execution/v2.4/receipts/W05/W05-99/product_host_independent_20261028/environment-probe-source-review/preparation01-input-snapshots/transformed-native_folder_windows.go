//go:build windows

package main

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
	shell32Browse          = windows.NewLazySystemDLL("shell32.dll").NewProc("SHBrowseForFolderW")
	shell32Path            = windows.NewLazySystemDLL("shell32.dll").NewProc("SHGetPathFromIDListEx")
	ole32Free              = windows.NewLazySystemDLL("ole32.dll").NewProc("CoTaskMemFree")
	ole32Initialize        = windows.NewLazySystemDLL("ole32.dll").NewProc("CoInitializeEx")
	ole32Uninitialize      = windows.NewLazySystemDLL("ole32.dll").NewProc("CoUninitialize")
	user32Send             = windows.NewLazySystemDLL("user32.dll").NewProc("SendMessageW")
	user32ShowFolder       = windows.NewLazySystemDLL("user32.dll").NewProc("ShowWindow")
	user32FolderVisible    = windows.NewLazySystemDLL("user32.dll").NewProc("IsWindowVisible")
	user32ForegroundFolder = windows.NewLazySystemDLL("user32.dll").NewProc("SetForegroundWindow")
	nativeFolderCallback   = syscall.NewCallback(func(hwnd uintptr, message uint32, _ uintptr, suggested uintptr) uintptr {
		if message != bffmInitialized {
			return 0
		}
		if suggested != 0 {
			user32Send.Call(hwnd, bffmSetSelectionW, 1, suggested)
		}
		// A background Core starts with STARTF_USESHOWWINDOW/SW_HIDE. Windows
		// may apply that startup state to the first ShowWindow call. Show only
		// this Shell-owned chooser, then repeat if the startup state hid it.
		// All calls finish on its owning thread; no deferred HWND survives it.
		user32ShowFolder.Call(hwnd, 1) // SW_SHOWNORMAL, never SW_SHOWDEFAULT.
		if visible, _, _ := user32FolderVisible.Call(hwnd); visible == 0 {
			user32ShowFolder.Call(hwnd, 1)
		}
		// Foreground activation is best-effort under Windows focus rules.
		user32ForegroundFolder.Call(hwnd)
		return 0
	})
)

// chooseNativeFolderWindows is called only after the pipe ACL and peer SID
// checks. A client-supplied path merely preselects the dialog; the returned
// path always comes from the folder the local user confirmed in the Shell UI.
func chooseNativeFolderWindows(initial string) (string, error) {
	runtime.LockOSThread()
	defer runtime.UnlockOSThread()
	// Both S_OK and S_FALSE own one COM initialization reference. An
	// incompatible apartment (or any other failure) must not enter Shell UI.
	hr, _, _ := ole32Initialize.Call(0, 2) // COINIT_APARTMENTTHREADED
	if int32(hr) < 0 {
		return "", fmt.Errorf("%w: folder chooser COM STA initialization failed (HRESULT 0x%08x)", ErrFrameShape, uint32(hr))
	}
	defer ole32Uninitialize.Call()
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
	var display [260]uint16
	info := browseInfoW{displayName: &display[0], title: title,
		flags: bifReturnOnlyFileSystemDirs, callback: nativeFolderCallback,
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
