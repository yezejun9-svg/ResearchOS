from pathlib import Path
import hashlib
import json

ROOT = Path(r"D:\作品集\ResearchOS\research-os\.local\worktrees\product-v1-native-path-entry-20261105")
EXPECTED = {
    "internal/host/native_folder_windows.go": "e79f977b5d7b21a6cc93034120984110816a6fdfdd9148a6a4e13dbc9f4e5433",
    "internal/host/native_folder_windows_test.go": "ed131f838beaefe76fcf0a6354b28568a98bd1de0bb97f87cc4dd4916ed87759",
}
for rel, digest in EXPECTED.items():
    path = ROOT / rel
    assert path.resolve().is_relative_to(ROOT.resolve())
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, rel

source_path = ROOT / "internal/host/native_folder_windows.go"
source = source_path.read_text(encoding="utf-8")
source = source.replace(
    "\tbifReturnOnlyFileSystemDirs = 0x0001\n\tbffmInitialized             = 1\n",
    "\tbifReturnOnlyFileSystemDirs = 0x0001\n\tbifEditBox                  = 0x0010\n\tbifValidate                 = 0x0020\n\tbffmInitialized             = 1\n\tbffmValidateFailedW         = 4\n",
    1,
)
old_start = source.index("\tnativeFolderCallback   = syscall.NewCallback(")
old_end = source.index("\n)", old_start)
source = source[:old_start] + '''\tuser32FolderMessage    = windows.NewLazySystemDLL("user32.dll").NewProc("MessageBoxW")
\tnativeFolderEffects    = nativeFolderUIEffects{
\t\tsetSelection: func(hwnd, suggested uintptr) {
\t\t\tuser32Send.Call(hwnd, bffmSetSelectionW, 1, suggested)
\t\t},
\t\tshow: func(hwnd uintptr) { user32ShowFolder.Call(hwnd, 1) }, // SW_SHOWNORMAL.
\t\tvisible: func(hwnd uintptr) bool {
\t\t\tvisible, _, _ := user32FolderVisible.Call(hwnd)
\t\t\treturn visible != 0
\t\t},
\t\tforeground:  func(hwnd uintptr) { user32ForegroundFolder.Call(hwnd) },
\t\twarnInvalid: warnNativeFolderInvalidPath,
\t}
\tnativeFolderCallback = syscall.NewCallback(func(hwnd uintptr, message uint32, parameter, suggested uintptr) uintptr {
\t\treturn handleNativeFolderBrowseMessage(hwnd, message, parameter, suggested, nativeFolderEffects)
\t})''' + source[old_end:]
marker = "// chooseNativeFolderWindows is called only after the pipe ACL and peer SID"
assert source.count(marker) == 1
helpers = '''// nativeFolderUIEffects keeps the synchronous, owning-thread UI calls together.
// Tests can observe these effects without opening a dialog or changing the wire API.
type nativeFolderUIEffects struct {
\tsetSelection func(hwnd, suggested uintptr)
\tshow         func(hwnd uintptr)
\tvisible      func(hwnd uintptr) bool
\tforeground   func(hwnd uintptr)
\twarnInvalid  func(hwnd uintptr)
}

func handleNativeFolderBrowseMessage(hwnd uintptr, message uint32, _ uintptr, suggested uintptr, ui nativeFolderUIEffects) uintptr {
\tswitch message {
\tcase bffmValidateFailedW:
\t\t// SHBrowseForFolderW supplies an unbounded UTF-16 path pointer here.
\t\t// Do not read or retain it: a fixed warning is enough, and only a
\t\t// subsequently confirmed Shell PIDL may become a selected path.
\t\tui.warnInvalid(hwnd)
\t\treturn 1 // Keep the chooser open after invalid input.
\tcase bffmInitialized:
\t\tif suggested != 0 {
\t\t\tui.setSelection(hwnd, suggested)
\t\t}
\t\t// A background Core starts with STARTF_USESHOWWINDOW/SW_HIDE. Windows
\t\t// may apply that startup state to the first ShowWindow call. Show only
\t\t// this Shell-owned chooser, then repeat if the startup state hid it.
\t\t// All calls finish on its owning thread; no deferred HWND survives it.
\t\tui.show(hwnd)
\t\tif !ui.visible(hwnd) {
\t\t\tui.show(hwnd)
\t\t}
\t\t// Foreground activation is best-effort under Windows focus rules.
\t\tui.foreground(hwnd)
\t}
\treturn 0
}

func warnNativeFolderInvalidPath(hwnd uintptr) {
\t// These fixed strings cannot contain embedded NULs. Never echo invalid input.
\ttext, _ := windows.UTF16PtrFromString("The folder path is invalid or does not exist. Enter an existing folder path and try again.")
\ttitle, _ := windows.UTF16PtrFromString("ResearchOS")
\tuser32FolderMessage.Call(hwnd, uintptr(unsafe.Pointer(text)), uintptr(unsafe.Pointer(title)), 0x30) // MB_OK | MB_ICONWARNING.
\truntime.KeepAlive(text)
\truntime.KeepAlive(title)
}

'''
source = source.replace(marker, helpers + marker, 1)
old_flags = "flags: bifReturnOnlyFileSystemDirs, callback: nativeFolderCallback,"
assert source.count(old_flags) == 1
source = source.replace(old_flags, "flags: bifReturnOnlyFileSystemDirs | bifEditBox | bifValidate, callback: nativeFolderCallback,", 1)

test_path = ROOT / "internal/host/native_folder_windows_test.go"
tests = test_path.read_text(encoding="utf-8")
assert "func TestNativeFolderValidationCallback" not in tests
tests += '''
func recordingNativeFolderUI(events *[]string, visible bool) nativeFolderUIEffects {
\treturn nativeFolderUIEffects{
\t\tsetSelection: func(hwnd, suggested uintptr) {
\t\t\t*events = append(*events, fmt.Sprintf("select:%x:%x", hwnd, suggested))
\t\t},
\t\tshow: func(hwnd uintptr) { *events = append(*events, fmt.Sprintf("show:%x", hwnd)) },
\t\tvisible: func(hwnd uintptr) bool {
\t\t\t*events = append(*events, fmt.Sprintf("visible:%x", hwnd))
\t\t\treturn visible
\t\t},
\t\tforeground:  func(hwnd uintptr) { *events = append(*events, fmt.Sprintf("foreground:%x", hwnd)) },
\t\twarnInvalid: func(hwnd uintptr) { *events = append(*events, fmt.Sprintf("warning:%x", hwnd)) },
\t}
}

func TestNativeFolderValidationCallbackRetainsOwnedDialog(t *testing.T) {
\tfor _, parameter := range []uintptr{0, 1, ^uintptr(0)} {
\t\tvar events []string
\t\t// 4 is BFFM_VALIDATEFAILEDW; neither Shell's invalid-text parameter nor
\t\t// the suggested-path pointer is valid memory in this test.
\t\tresult := handleNativeFolderBrowseMessage(0x25, 4, parameter, ^uintptr(0), recordingNativeFolderUI(&events, false))
\t\tif result != 1 || strings.Join(events, ",") != "warning:25" {
\t\t\tt.Fatalf("invalid Unicode input must warn its owner once and retain chooser: result=%d events=%v", result, events)
\t\t}
\t}
}

func TestNativeFolderValidationIgnoresOtherMessages(t *testing.T) {
\t// ANSI validation is 3, not the W chooser's message 4. Selection-change
\t// and unknown notifications must not read either pointer or perform UI.
\tfor _, message := range []uint32{0, 2, 3, 5, 0xffffffff} {
\t\tvar events []string
\t\tresult := handleNativeFolderBrowseMessage(0x25, message, 1, ^uintptr(0), recordingNativeFolderUI(&events, false))
\t\tif result != 0 || len(events) != 0 {
\t\t\tt.Fatalf("message %d: result=%d events=%v", message, result, events)
\t\t}
\t}
}

func TestNativeFolderInitializationEffectsPreserved(t *testing.T) {
\tfor _, visible := range []bool{false, true} {
\t\tfor _, suggested := range []uintptr{0, 0x1234} {
\t\t\tt.Run(fmt.Sprintf("visible=%v/suggested=%x", visible, suggested), func(t *testing.T) {
\t\t\t\tvar events, want []string
\t\t\t\tif suggested != 0 {
\t\t\t\t\twant = append(want, "select:25:1234")
\t\t\t\t}
\t\t\t\twant = append(want, "show:25", "visible:25")
\t\t\t\tif !visible {
\t\t\t\t\twant = append(want, "show:25")
\t\t\t\t}
\t\t\t\twant = append(want, "foreground:25")
\t\t\t\tresult := handleNativeFolderBrowseMessage(0x25, 1, ^uintptr(0), suggested, recordingNativeFolderUI(&events, visible))
\t\t\t\tif result != 0 || strings.Join(events, ",") != strings.Join(want, ",") {
\t\t\t\t\tt.Fatalf("initialization changed: result=%d events=%v want=%v", result, events, want)
\t\t\t\t}
\t\t\t})
\t\t}
\t}
}

func TestNativeFolderCancelledChoiceDoesNotGrant(t *testing.T) {
\tfor _, withPath := range []bool{false, true} {
\t\tt.Run(fmt.Sprintf("error-with-path=%v", withPath), func(t *testing.T) {
\t\t\th := firstUseHost(t)
\t\t\tframe := nativeFirstUseFrame(t, KindWorkspaceChooseRequest,
\t\t\t\tmap[string]any{"requested_path": nil, "requested_access": AccessReadWrite})
\t\t\tpicked := ""
\t\t\tif withPath {
\t\t\t\tpicked = t.TempDir()
\t\t\t}
\t\t\tcalls := 0
\t\t\treply, err := h.HandleNative(frame, true, func(initial string) (string, error) {
\t\t\t\tcalls++
\t\t\t\tif initial != "" {
\t\t\t\t\tt.Fatalf("unexpected initial path %q", initial)
\t\t\t\t}
\t\t\t\treturn picked, fmt.Errorf("%w: folder selection cancelled", ErrFrameShape)
\t\t\t})
\t\t\tif calls != 1 || reply != nil || !errors.Is(err, ErrFrameShape) {
\t\t\t\tt.Fatalf("cancel result: calls=%d reply=%s err=%v", calls, reply, err)
\t\t\t}
\t\t\tif len(h.Roots()) != 0 || h.selections.Outstanding() != 0 {
\t\t\t\tt.Fatalf("cancel granted authority: roots=%d selections=%d", len(h.Roots()), h.selections.Outstanding())
\t\t\t}
\t\t})
\t}
}
'''

source_path.write_bytes(source.encode("utf-8"))
test_path.write_bytes(tests.encode("utf-8"))
print(json.dumps({"written_exact2": list(EXPECTED), "base_hashes_verified": True}))
