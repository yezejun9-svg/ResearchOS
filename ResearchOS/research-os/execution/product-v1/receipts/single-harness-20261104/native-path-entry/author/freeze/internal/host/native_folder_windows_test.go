//go:build windows

package host

import (
	"bufio"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"runtime"
	"strings"
	"syscall"
	"testing"
	"time"
	"unsafe"

	"golang.org/x/sys/windows"
)

type nativeFolderObservation struct {
	Event      string   `json:"event"`
	PID        uint32   `json:"pid"`
	Index      int      `json:"index"`
	Initial    string   `json:"initial,omitempty"`
	Flags      uint32   `json:"startup_flags,omitempty"`
	Show       uint16   `json:"startup_show"`
	HWND       uintptr  `json:"hwnd,omitempty"`
	Class      string   `json:"class,omitempty"`
	Visible    bool     `json:"visible"`
	Rect       [4]int32 `json:"rect"`
	Foreground uintptr  `json:"foreground_hwnd,omitempty"`
	Chosen     string   `json:"chosen"`
	Error      string   `json:"error,omitempty"`
}

// This opt-in test uses only a disposable test executable and its own dialogs.
// The controller observes visibility and cancels; it never shows a window.
func TestNativeFolderHiddenProcess(t *testing.T) {
	if os.Getenv("RESEARCHOS_NATIVE_FOLDER_GUI_TEST") != "1" {
		t.Skip("requires an interactive Windows desktop and explicit native GUI opt-in")
	}
	for _, first := range []string{"empty", "suggested"} {
		t.Run(first, func(t *testing.T) { testNativeFolderHiddenProcess(t, first) })
	}
}

func testNativeFolderHiddenProcess(t *testing.T, first string) {
	t.Helper()
	exe, err := os.Executable()
	if err != nil {
		t.Fatal(err)
	}
	cmd := exec.Command(exe, "-test.run=^TestNativeFolderHiddenHelper$", "-test.v", "-test.timeout=90s")
	cmd.Env = append(os.Environ(), "RESEARCHOS_NATIVE_FOLDER_HELPER="+first, "RESEARCHOS_NATIVE_FOLDER_SUGGESTED="+t.TempDir())
	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	stdout, err := cmd.StdoutPipe()
	if err != nil {
		t.Fatal(err)
	}
	cmd.Stderr = cmd.Stdout
	stdin, err := cmd.StdinPipe()
	if err != nil {
		t.Fatal(err)
	}
	if err = cmd.Start(); err != nil {
		t.Fatal(err)
	}
	defer stdin.Close()
	scannerDone := make(chan struct{})
	defer func() {
		if cmd.ProcessState == nil {
			_ = cmd.Process.Kill()
			_ = cmd.Wait()
		}
		<-scannerDone
	}()
	events := make(chan nativeFolderObservation, 16)
	go func() {
		defer close(scannerDone)
		defer close(events)
		scanner := bufio.NewScanner(stdout)
		for scanner.Scan() {
			line := scanner.Text()
			t.Logf("helper[%d] %s", cmd.Process.Pid, line)
			if strings.HasPrefix(line, "{") {
				var event nativeFolderObservation
				if json.Unmarshal([]byte(line), &event) == nil {
					events <- event
				}
			}
		}
	}()
	next := func(want string) nativeFolderObservation {
		t.Helper()
		select {
		case event, ok := <-events:
			if !ok || event.Event != want || event.PID != uint32(cmd.Process.Pid) {
				t.Fatalf("expected own %s, got %+v (stream open %v)", want, event, ok)
			}
			return event
		case <-time.After(35 * time.Second):
			t.Fatalf("helper timed out waiting for %s", want)
		}
		return nativeFolderObservation{}
	}
	startup := next("startup")
	if startup.Flags&windows.STARTF_USESHOWWINDOW == 0 || startup.Show != windows.SW_HIDE {
		t.Fatalf("helper was not startup-hidden: %+v", startup)
	}
	user := windows.NewLazySystemDLL("user32.dll")
	enum := user.NewProc("EnumWindows")
	pidProc := user.NewProc("GetWindowThreadProcessId")
	classProc := user.NewProc("GetClassNameW")
	rectProc := user.NewProc("GetWindowRect")
	foregroundProc := user.NewProc("GetForegroundWindow")
	post := user.NewProc("PostMessageW")
	var observations []nativeFolderObservation
	callback := syscall.NewCallback(func(hwnd, _ uintptr) uintptr {
		var pid uint32
		pidProc.Call(hwnd, uintptr(unsafe.Pointer(&pid)))
		if pid != uint32(cmd.Process.Pid) {
			return 1
		}
		var class [128]uint16
		classProc.Call(hwnd, uintptr(unsafe.Pointer(&class[0])), uintptr(len(class)))
		if windows.UTF16ToString(class[:]) != "#32770" {
			return 1
		}
		obs := nativeFolderObservation{Event: "dialog", PID: pid, HWND: hwnd, Class: "#32770"}
		visible, _, _ := user32FolderVisible.Call(hwnd)
		obs.Visible = visible != 0
		rectProc.Call(hwnd, uintptr(unsafe.Pointer(&obs.Rect)))
		obs.Foreground, _, _ = foregroundProc.Call()
		observations = append(observations, obs)
		return 1
	})
	for index := 0; index < 2; index++ {
		ready := next("ready")
		if ready.Index != index {
			t.Fatalf("unexpected dialog index: %+v", ready)
		}
		if _, err = fmt.Fprintln(stdin, "open"); err != nil {
			t.Fatal(err)
		}
		var dialog nativeFolderObservation
		deadline := time.Now().Add(25 * time.Second)
		var stableSince time.Time
		for time.Now().Before(deadline) {
			observations = nil
			enum.Call(callback, 0)
			usable := len(observations) == 1 && observations[0].Visible && observations[0].Rect[2] > observations[0].Rect[0] && observations[0].Rect[3] > observations[0].Rect[1]
			if usable {
				if stableSince.IsZero() || dialog.HWND != observations[0].HWND {
					stableSince = time.Now()
				}
				dialog = observations[0]
				if time.Since(stableSince) >= 500*time.Millisecond {
					break
				}
			} else {
				stableSince = time.Time{}
			}
			time.Sleep(50 * time.Millisecond)
		}
		if stableSince.IsZero() || time.Since(stableSince) < 500*time.Millisecond {
			data, _ := json.Marshal(observations)
			t.Fatalf("own chooser did not remain visible with usable rectangle: %s", data)
		}
		dialog.Index = index
		dialog.Initial = ready.Initial
		data, _ := json.Marshal(dialog)
		t.Log(string(data))
		// Verify ownership again immediately before the sole controller mutation.
		var owner uint32
		pidProc.Call(dialog.HWND, uintptr(unsafe.Pointer(&owner)))
		if owner != uint32(cmd.Process.Pid) {
			t.Fatal("dialog ownership changed before cancellation")
		}
		if ok, _, callErr := post.Call(dialog.HWND, 0x111, 2, 0); ok == 0 {
			t.Fatalf("own dialog cancel failed: %v", callErr)
		} // WM_COMMAND/IDCANCEL
		cancelled := next("cancelled")
		if cancelled.Index != index || cancelled.Chosen != "" || !strings.Contains(cancelled.Error, "folder selection cancelled") {
			t.Fatalf("unexpected cancellation: %+v", cancelled)
		}
	}
	next("com-balanced-and-fail-closed")
	for range events {
	} // join scanner before reporting/returning from the test
	if err = cmd.Wait(); err != nil {
		t.Fatalf("hidden helper failed: %v", err)
	}
	t.Logf("helper PID %d exited normally; COM balance/failure assertions passed; chosen paths 0", cmd.Process.Pid)
}

func TestNativeFolderHiddenHelper(t *testing.T) {
	first := os.Getenv("RESEARCHOS_NATIVE_FOLDER_HELPER")
	if first == "" {
		t.Skip("subprocess helper only")
	}
	runtime.LockOSThread()
	defer runtime.UnlockOSThread()
	emit := func(event nativeFolderObservation) {
		event.PID = windows.GetCurrentProcessId()
		if err := json.NewEncoder(os.Stdout).Encode(event); err != nil {
			t.Fatal(err)
		}
	}
	var startup windows.StartupInfo
	if err := windows.GetStartupInfo(&startup); err != nil {
		t.Fatal(err)
	}
	emit(nativeFolderObservation{Event: "startup", Flags: startup.Flags, Show: startup.ShowWindow})
	paths := []string{"", os.Getenv("RESEARCHOS_NATIVE_FOLDER_SUGGESTED")}
	if first == "suggested" {
		paths[0], paths[1] = paths[1], paths[0]
	}
	reader := bufio.NewScanner(os.Stdin)
	initialize := func(mode uintptr, want uint32) {
		t.Helper()
		hr, _, _ := ole32Initialize.Call(0, mode)
		t.Logf("CoInitializeEx(%d) actual HRESULT 0x%08x; expected 0x%08x", mode, uint32(hr), want)
		if uint32(hr) != want {
			t.Fatalf("CoInitializeEx(%d) = 0x%08x, want 0x%08x", mode, uint32(hr), want)
		}
	}
	for index, initial := range paths {
		// The second chooser exercises S_FALSE with an existing STA reference.
		if index == 1 {
			initialize(2, 0)
		}
		emit(nativeFolderObservation{Event: "ready", Index: index, Initial: initial})
		if !reader.Scan() || reader.Text() != "open" {
			t.Fatal("missing controller handshake")
		}
		chosen, err := chooseNativeFolderWindows(initial)
		if chosen != "" || !errors.Is(err, ErrFrameShape) || !strings.Contains(err.Error(), "folder selection cancelled") {
			t.Fatalf("cancel returned path=%q err=%v", chosen, err)
		}
		if index == 1 {
			initialize(0, 0x80010106) // RPC_E_CHANGED_MODE: caller's STA reference survives.
			ole32Uninitialize.Call()
		}
		initialize(0, 0) // S_OK: chooser did not leak its STA reference.
		ole32Uninitialize.Call()
		emit(nativeFolderObservation{Event: "cancelled", Index: index, Chosen: chosen, Error: err.Error()})
	}
	initialize(0, 0)
	chosen, err := chooseNativeFolderWindows("")
	if chosen != "" || !errors.Is(err, ErrFrameShape) || !strings.Contains(err.Error(), "0x80010106") {
		t.Fatalf("incompatible apartment did not fail closed: %q %v", chosen, err)
	}
	initialize(0, 1) // S_FALSE: failed chooser must not uninitialize caller's MTA.
	ole32Uninitialize.Call()
	ole32Uninitialize.Call()
	initialize(2, 0)
	ole32Uninitialize.Call()
	chosen, err = chooseNativeFolderWindows("bad\x00suggestion")
	if chosen != "" || !errors.Is(err, ErrFrameShape) {
		t.Fatalf("invalid suggestion did not fail closed: %q %v", chosen, err)
	}
	initialize(0, 0) // Invalid UTF-16 input also releases the chooser's STA reference.
	ole32Uninitialize.Call()
	emit(nativeFolderObservation{Event: "com-balanced-and-fail-closed"})
}

func recordingNativeFolderUI(events *[]string, visible bool) nativeFolderUIEffects {
	return nativeFolderUIEffects{
		setSelection: func(hwnd, suggested uintptr) {
			*events = append(*events, fmt.Sprintf("select:%x:%x", hwnd, suggested))
		},
		show: func(hwnd uintptr) { *events = append(*events, fmt.Sprintf("show:%x", hwnd)) },
		visible: func(hwnd uintptr) bool {
			*events = append(*events, fmt.Sprintf("visible:%x", hwnd))
			return visible
		},
		foreground:  func(hwnd uintptr) { *events = append(*events, fmt.Sprintf("foreground:%x", hwnd)) },
		warnInvalid: func(hwnd uintptr) { *events = append(*events, fmt.Sprintf("warning:%x", hwnd)) },
	}
}

func TestNativeFolderValidationCallbackRetainsOwnedDialog(t *testing.T) {
	for _, parameter := range []uintptr{0, 1, ^uintptr(0)} {
		var events []string
		// 4 is BFFM_VALIDATEFAILEDW; neither Shell's invalid-text parameter nor
		// the suggested-path pointer is valid memory in this test.
		result := handleNativeFolderBrowseMessage(0x25, 4, parameter, ^uintptr(0), recordingNativeFolderUI(&events, false))
		if result != 1 || strings.Join(events, ",") != "warning:25" {
			t.Fatalf("invalid Unicode input must warn its owner once and retain chooser: result=%d events=%v", result, events)
		}
	}
}

func TestNativeFolderValidationIgnoresOtherMessages(t *testing.T) {
	// ANSI validation is 3, not the W chooser's message 4. Selection-change
	// and unknown notifications must not read either pointer or perform UI.
	for _, message := range []uint32{0, 2, 3, 5, 0xffffffff} {
		var events []string
		result := handleNativeFolderBrowseMessage(0x25, message, 1, ^uintptr(0), recordingNativeFolderUI(&events, false))
		if result != 0 || len(events) != 0 {
			t.Fatalf("message %d: result=%d events=%v", message, result, events)
		}
	}
}

func TestNativeFolderInitializationEffectsPreserved(t *testing.T) {
	for _, visible := range []bool{false, true} {
		for _, suggested := range []uintptr{0, 0x1234} {
			t.Run(fmt.Sprintf("visible=%v/suggested=%x", visible, suggested), func(t *testing.T) {
				var events, want []string
				if suggested != 0 {
					want = append(want, "select:25:1234")
				}
				want = append(want, "show:25", "visible:25")
				if !visible {
					want = append(want, "show:25")
				}
				want = append(want, "foreground:25")
				result := handleNativeFolderBrowseMessage(0x25, 1, ^uintptr(0), suggested, recordingNativeFolderUI(&events, visible))
				if result != 0 || strings.Join(events, ",") != strings.Join(want, ",") {
					t.Fatalf("initialization changed: result=%d events=%v want=%v", result, events, want)
				}
			})
		}
	}
}

func TestNativeFolderCancelledChoiceDoesNotGrant(t *testing.T) {
	for _, withPath := range []bool{false, true} {
		t.Run(fmt.Sprintf("error-with-path=%v", withPath), func(t *testing.T) {
			h := firstUseHost(t)
			frame := nativeFirstUseFrame(t, KindWorkspaceChooseRequest,
				map[string]any{"requested_path": nil, "requested_access": AccessReadWrite})
			picked := ""
			if withPath {
				picked = t.TempDir()
			}
			calls := 0
			reply, err := h.HandleNative(frame, true, func(initial string) (string, error) {
				calls++
				if initial != "" {
					t.Fatalf("unexpected initial path %q", initial)
				}
				return picked, fmt.Errorf("%w: folder selection cancelled", ErrFrameShape)
			})
			if calls != 1 || reply != nil || !errors.Is(err, ErrFrameShape) {
				t.Fatalf("cancel result: calls=%d reply=%s err=%v", calls, reply, err)
			}
			if len(h.Roots()) != 0 || h.selections.Outstanding() != 0 {
				t.Fatalf("cancel granted authority: roots=%d selections=%d", len(h.Roots()), h.selections.Outstanding())
			}
		})
	}
}
