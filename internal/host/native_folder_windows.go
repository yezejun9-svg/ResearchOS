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
	bifEditBox                  = 0x0010
	bifValidate                 = 0x0020
	bffmInitialized             = 1
	bffmValidateFailedW         = 4
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
	user32FolderMessage    = windows.NewLazySystemDLL("user32.dll").NewProc("MessageBoxW")
	nativeFolderEffects    = nativeFolderUIEffects{
		setSelection: func(hwnd, suggested uintptr) {
			user32Send.Call(hwnd, bffmSetSelectionW, 1, suggested)
		},
		show: func(hwnd uintptr) { user32ShowFolder.Call(hwnd, 1) }, // SW_SHOWNORMAL.
		visible: func(hwnd uintptr) bool {
			visible, _, _ := user32FolderVisible.Call(hwnd)
			return visible != 0
		},
		foreground:  func(hwnd uintptr) { user32ForegroundFolder.Call(hwnd) },
		warnInvalid: warnNativeFolderInvalidPath,
	}
	nativeFolderCallback = syscall.NewCallback(func(hwnd uintptr, message uint32, parameter, suggested uintptr) uintptr {
		return handleNativeFolderBrowseMessage(hwnd, message, parameter, suggested, nativeFolderEffects)
	})
)

// nativeFolderUIEffects keeps the synchronous, owning-thread UI calls together.
// Tests can observe these effects without opening a dialog or changing the wire API.
type nativeFolderUIEffects struct {
	setSelection func(hwnd, suggested uintptr)
	show         func(hwnd uintptr)
	visible      func(hwnd uintptr) bool
	foreground   func(hwnd uintptr)
	warnInvalid  func(hwnd uintptr)
}

func handleNativeFolderBrowseMessage(hwnd uintptr, message uint32, _ uintptr, suggested uintptr, ui nativeFolderUIEffects) uintptr {
	switch message {
	case bffmValidateFailedW:
		// SHBrowseForFolderW supplies an unbounded UTF-16 path pointer here.
		// Do not read or retain it: a fixed warning is enough, and only a
		// subsequently confirmed Shell PIDL may become a selected path.
		ui.warnInvalid(hwnd)
		return 1 // Keep the chooser open after invalid input.
	case bffmInitialized:
		if suggested != 0 {
			ui.setSelection(hwnd, suggested)
		}
		// A background Core starts with STARTF_USESHOWWINDOW/SW_HIDE. Windows
		// may apply that startup state to the first ShowWindow call. Show only
		// this Shell-owned chooser, then repeat if the startup state hid it.
		// All calls finish on its owning thread; no deferred HWND survives it.
		ui.show(hwnd)
		if !ui.visible(hwnd) {
			ui.show(hwnd)
		}
		// Foreground activation is best-effort under Windows focus rules.
		ui.foreground(hwnd)
	}
	return 0
}

func warnNativeFolderInvalidPath(hwnd uintptr) {
	// These fixed strings cannot contain embedded NULs. Never echo invalid input.
	text, _ := windows.UTF16PtrFromString("文件夹路径无效或不存在。请输入已有的文件夹路径后重试。")
	title, _ := windows.UTF16PtrFromString("ResearchOS")
	user32FolderMessage.Call(hwnd, uintptr(unsafe.Pointer(text)), uintptr(unsafe.Pointer(title)), 0x30) // MB_OK | MB_ICONWARNING.
	runtime.KeepAlive(text)
	runtime.KeepAlive(title)
}

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
		flags: bifReturnOnlyFileSystemDirs | bifEditBox | bifValidate, callback: nativeFolderCallback,
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
