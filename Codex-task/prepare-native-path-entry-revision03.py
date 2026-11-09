from pathlib import Path
import json, hashlib, difflib

cwd=Path(__file__).resolve().parent
old=cwd/'product-v1-native-path-entry-prepare-02'
new=cwd/'product-v1-native-path-entry-prepare-03'
new.mkdir()
for name in ['real-electron-flow.mjs','choose-owned-folder.ps1','scope.template.json','README.md']:
    (new/name).write_bytes((old/name).read_bytes())

helper=(new/'choose-owned-folder.ps1').read_text(encoding='utf-8')
marker='function Assert-MessageDeadline('
predicate=r'''function Assert-DialogThreadFacts($Snapshot,[int]$ExpectedPid,[long]$ExpectedDialog) {
  if ($Snapshot.query_succeeded -ne $true -or $Snapshot.dialog_hwnd -ne $ExpectedDialog -or
    $Snapshot.dialog_pid_before -ne $ExpectedPid -or $Snapshot.dialog_pid_after -ne $ExpectedPid -or
    $Snapshot.dialog_tid_before -le 0 -or $Snapshot.dialog_tid_after -ne $Snapshot.dialog_tid_before -or
    $Snapshot.active_hwnd -ne $ExpectedDialog -or $Snapshot.active_pid -ne $ExpectedPid -or
    $Snapshot.active_tid -ne $Snapshot.dialog_tid_before -or
    $Snapshot.focus_hwnd -le 0 -or $Snapshot.focus_pid -ne $ExpectedPid -or
    $Snapshot.focus_is_dialog_or_child -ne $true) {throw 'DIALOG_THREAD_ACTIVE_OR_FOCUS_UNCONFIRMED_NO_POST'}
}
'''
assert helper.count(marker)==1
helper=helper.replace(marker,predicate+marker)
marker='  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();'
native=r'''  [StructLayout(LayoutKind.Sequential)]
  public struct WindowRect { public int left, top, right, bottom; }
  [StructLayout(LayoutKind.Sequential)]
  public struct GuiThreadInfo {
    public uint cbSize, flags;
    public IntPtr hwndActive, hwndFocus, hwndCapture, hwndMenuOwner, hwndMoveSize, hwndCaret;
    public WindowRect rcCaret;
  }
  [DllImport("user32.dll",SetLastError=true)]
  public static extern bool GetGUIThreadInfo(uint threadId, ref GuiThreadInfo info);
  [DllImport("user32.dll")] public static extern bool IsChild(IntPtr parent, IntPtr child);
  public static bool ReadThreadInfo(uint threadId, out GuiThreadInfo info) {
    info = new GuiThreadInfo();
    info.cbSize = (uint)Marshal.SizeOf(typeof(GuiThreadInfo));
    return GetGUIThreadInfo(threadId, ref info);
  }
'''
assert helper.count(marker)==1
helper=helper.replace(marker,marker+'\n'+native)
marker='  function Post-OwnedButton('
query=r'''  function Assert-DialogThreadState([IntPtr]$Dialog,[switch]$ForCleanup) {
    Assert-Core -ForCleanup:$ForCleanup
    [uint32]$beforePid=0
    $beforeTid=[OwnedPathWin32]::GetWindowThreadProcessId($Dialog,[ref]$beforePid)
    if ($beforePid -ne $coreId -or $beforeTid -eq 0) {throw 'DIALOG_THREAD_IDENTITY_UNCONFIRMED_NO_POST'}
    $info=[OwnedPathWin32+GuiThreadInfo]::new()
    $succeeded=[OwnedPathWin32]::ReadThreadInfo($beforeTid,[ref]$info)
    [uint32]$afterPid=0
    $afterTid=[OwnedPathWin32]::GetWindowThreadProcessId($Dialog,[ref]$afterPid)
    [uint32]$activePid=0;[uint32]$activeTid=0
    [uint32]$focusPid=0;[uint32]$focusTid=0
    if ($succeeded -and $info.hwndActive -ne [IntPtr]::Zero) {
      $activeTid=[OwnedPathWin32]::GetWindowThreadProcessId($info.hwndActive,[ref]$activePid)
    }
    if ($succeeded -and $info.hwndFocus -ne [IntPtr]::Zero) {
      $focusTid=[OwnedPathWin32]::GetWindowThreadProcessId($info.hwndFocus,[ref]$focusPid)
    }
    $focusOwned=$false
    if ($focusPid -eq $coreId -and $info.hwndFocus -ne [IntPtr]::Zero) {
      $focusOwned=($info.hwndFocus -eq $Dialog -or [OwnedPathWin32]::IsChild($Dialog,$info.hwndFocus))
    }
    $snapshot=@{dialog_hwnd=$Dialog.ToInt64();dialog_pid_before=$beforePid;dialog_tid_before=$beforeTid
      dialog_pid_after=$afterPid;dialog_tid_after=$afterTid;query_succeeded=$succeeded
      cb_size=$info.cbSize;flags=$info.flags;active_hwnd=$info.hwndActive.ToInt64();active_pid=$activePid;active_tid=$activeTid
      focus_hwnd=$info.hwndFocus.ToInt64();focus_pid=$focusPid;focus_tid=$focusTid;focus_is_dialog_or_child=$focusOwned
      global_foreground_hwnd=[OwnedPathWin32]::GetForegroundWindow().ToInt64()
      global_foreground_is_diagnostic_only=$true;window_text_read=$false;activation_attempted=$false}
    Record 'DIALOG_THREAD_ACTIVE_SNAPSHOT' $snapshot
    Assert-DialogThreadFacts $snapshot $coreId $Dialog.ToInt64()
  }
'''
assert helper.count(marker)==1
helper=helper.replace(marker,query+marker)
needle="    if ([OwnedPathWin32]::GetForegroundWindow() -ne $Dialog) {throw 'BUTTON_DIALOG_NOT_FOREGROUND_NO_CLICK'}"
assert helper.count(needle)==1
helper=helper.replace(needle,'    Assert-DialogThreadState $Dialog -ForCleanup:$ForCleanup')
needle="      -not $now.visible -or -not $now.enabled -or [OwnedPathWin32]::GetForegroundWindow() -ne $Dialog) {throw 'BUTTON_CHANGED_IMMEDIATELY_BEFORE_QUEUE'}"
assert helper.count(needle)==1
helper=helper.replace(needle,"      -not $now.visible -or -not $now.enabled) {throw 'BUTTON_CHANGED_IMMEDIATELY_BEFORE_QUEUE'}\n    Assert-DialogThreadState $Dialog -ForCleanup:$ForCleanup")
(new/'choose-owned-folder.ps1').write_text(helper,encoding='utf-8',newline='\n')

runner=(new/'real-electron-flow.mjs').read_text(encoding='utf-8')
marker='function parseNativeReply('
decode=r'''function decodeNativeReply(chosen) {
  requireThat(typeof chosen?.stdout === 'string' && Buffer.byteLength(chosen.stdout) > 0 &&
    Buffer.byteLength(chosen.stdout) <= 65536, 'NATIVE_REPLY_BOUNDED_UTF8_TEXT_REQUIRED');
  let reply;
  try { reply = JSON.parse(chosen.stdout); }
  catch { throw Object.assign(new Error('NATIVE_REPLY_JSON_INVALID'), {code: 'NATIVE_REPLY_JSON_INVALID'}); }
  requireThat(reply && typeof reply === 'object' && !Array.isArray(reply) &&
    reply.schema === 'researchos.owned-native-path-entry/1', 'NATIVE_REPLY_SCHEMA_REQUIRED');
  const phases = ['PREFLIGHT', 'DISCOVER_CHOOSER', 'INVALID_PATH', 'VALID_PATH'];
  const statuses = ['BLOCKED', 'VALID_SHELL_OK_CLOSED_REQUIRES_MAIN_BINDING'];
  const authorizations = ['NOT_ESTABLISHED', 'UNKNOWN_NO_AUTHORIZATION_INFERRED_NO_RETRY',
    'NO_VALID_OK_CONFIRMED', 'SHELL_CONFIRM_OBSERVED_MAIN_BINDING_NOT_YET_VERIFIED'];
  const cleanups = ['NOT_NEEDED', 'OUTCOME_UNKNOWN_NO_FURTHER_CLICK_ROOT_JOB_REQUIRED',
    'OWNED_IDCANCEL_CLOSED', 'OWNERSHIP_OR_CANCEL_UNKNOWN_ROOT_JOB_REQUIRED', 'OWNERSHIP_UNCONFIRMED_NO_CLICK'];
  requireThat(phases.includes(reply.phase) && statuses.includes(reply.status) &&
    authorizations.includes(reply.authorization_state) && cleanups.includes(reply.cleanup?.status) &&
    typeof reply.cleanup.attempted === 'boolean' && Array.isArray(reply.history) && reply.history.length <= 512,
    'NATIVE_REPLY_PHASE_STATUS_AUTH_CLEANUP_REQUIRED');
  for (const field of ['clicked_ok', 'invalid_ok_attempted', 'valid_ok_attempted', 'outcome_uncertain']) {
    requireThat(typeof reply[field] === 'boolean', 'NATIVE_REPLY_EXPLICIT_BOOLEAN_REQUIRED:' + field);
  }
  requireThat(reply.input_is_authorization === false && reply.actual_task_submissions === 0 &&
    reply.model_outcome === 'NOT_RUN_ZERO_BUDGET' &&
    (!Object.hasOwn(reply, 'invalid_kept_chooser_open') || typeof reply.invalid_kept_chooser_open === 'boolean'),
    'NATIVE_REPLY_ZERO_BUDGET_INPUT_SEMANTICS_REQUIRED');
  requireThat((reply.status === 'BLOCKED' && chosen.exit === 2 && typeof reply.reason === 'string' && reply.reason.length > 0 && reply.reason.length <= 2048) ||
    (reply.status === 'VALID_SHELL_OK_CLOSED_REQUIRES_MAIN_BINDING' && chosen.exit === 0), 'NATIVE_REPLY_EXIT_STATUS_MISMATCH');
  requireThat((!reply.clicked_ok || reply.valid_ok_attempted) &&
    (!reply.valid_ok_attempted || (reply.invalid_ok_attempted && reply.phase === 'VALID_PATH')) &&
    (!reply.invalid_ok_attempted || ['INVALID_PATH', 'VALID_PATH'].includes(reply.phase)) &&
    (!reply.invalid_kept_chooser_open || reply.invalid_ok_attempted) &&
    (reply.authorization_state !== 'SHELL_CONFIRM_OBSERVED_MAIN_BINDING_NOT_YET_VERIFIED' || reply.clicked_ok) &&
    (reply.status !== 'VALID_SHELL_OK_CLOSED_REQUIRES_MAIN_BINDING' || reply.clicked_ok), 'NATIVE_REPLY_ATTEMPT_FLAGS_CONTRADICTORY');
  return reply;
}

function observeNativeReply(reply) {
  const noOk = reply.invalid_ok_attempted === false && reply.valid_ok_attempted === false && reply.clicked_ok === false;
  let authorization = 'UNKNOWN_NO_AUTHORIZATION_INFERRED_NO_RETRY';
  if (!reply.outcome_uncertain && noOk) authorization = 'NOT_ESTABLISHED_NO_OK_ATTEMPT_RECORDED';
  else if (!reply.outcome_uncertain && !reply.valid_ok_attempted && reply.invalid_kept_chooser_open === true) {
    authorization = 'INVALID_OK_REJECTED_NO_VALID_OK_CONFIRMED';
  } else if (!reply.outcome_uncertain && reply.status === 'VALID_SHELL_OK_CLOSED_REQUIRES_MAIN_BINDING') {
    authorization = 'HELPER_REPORTED_SHELL_CONFIRM_REQUIRES_SUCCESS_EVIDENCE_AND_MAIN_BINDING';
  }
  return {phase: reply.phase, status: reply.status, reason: reply.reason || null,
    invalid_ok_attempted: reply.invalid_ok_attempted, valid_ok_attempted: reply.valid_ok_attempted,
    clicked_ok: reply.clicked_ok, outcome_uncertain: reply.outcome_uncertain,
    helper_reported_authorization_state: reply.authorization_state, authorization_observation: authorization,
    cleanup: reply.cleanup, no_ok_attempt_recorded: noOk};
}

'''
assert runner.count(marker)==1
runner=runner.replace(marker,decode+marker)
needle="  requireThat(chosen?.exit === 0 && typeof chosen.stdout === 'string' &&\n    Buffer.byteLength(chosen.stdout) <= 65536, 'NATIVE_REPLY_COMPLETE_BOUNDED_UTF8_JSON_REQUIRED');\n  const reply = JSON.parse(chosen.stdout);"
assert runner.count(needle)==1
runner=runner.replace(needle,"  const reply = decodeNativeReply(chosen);\n  requireThat(chosen.exit === 0, 'NATIVE_REPLY_NOT_SUCCESS');")
needle="    const pickerResult = parseNativeReply(chosen, core, workspace, invalid);"
assert runner.count(needle)==1
runner=runner.replace(needle,r'''    const envelope = decodeNativeReply(chosen);
    state.native_helper_observation = observeNativeReply(envelope);
    state.native_picker_cleanup = envelope.cleanup;
    state.native_workspace_authorization = state.native_helper_observation.authorization_observation;
    state.helper_pending = false;
    activeRunEvidence.phase = 'NATIVE_HELPER_COMPLETE_' + envelope.phase;
    if (envelope.status === 'BLOCKED') {
      state.native_picker = state.native_helper_observation.no_ok_attempt_recorded ? 'BLOCKED_BEFORE_ANY_OK_ATTEMPT' : 'BLOCKED_AFTER_RECORDED_NATIVE_ATTEMPT';
      throw Object.assign(new Error(envelope.reason), {code: 'NATIVE_HELPER_BLOCKED'});
    }
    const pickerResult = parseNativeReply(chosen, core, workspace, invalid);''')
(new/'real-electron-flow.mjs').write_text(runner,encoding='utf-8',newline='\n')
for name in ['choose-owned-folder.ps1','real-electron-flow.mjs']:
    (new/('helper.diff' if name.endswith('.ps1') else 'runner.diff')).write_text(''.join(difflib.unified_diff((old/name).read_text(encoding='utf-8').splitlines(True),(new/name).read_text(encoding='utf-8').splitlines(True),fromfile='freeze02/'+name,tofile='revision03/'+name)),encoding='utf-8')
scope=json.loads((new/'scope.template.json').read_text(encoding='utf-8'))
scope['harness']={'runner_sha256':hashlib.sha256((new/'real-electron-flow.mjs').read_bytes()).hexdigest(),
 'folder_helper_sha256':hashlib.sha256((new/'choose-owned-folder.ps1').read_bytes()).hexdigest()}
scope['native_picker']['button_active_guard']='SAME_CORE_ACTUAL_DIALOG_TID_GUI_THREAD_INFO_ACTIVE_DIALOG_AND_OWNED_FOCUS'
scope['native_picker']['global_foreground']='NUMERIC_DIAGNOSTIC_ONLY_NO_OTHER_WINDOW_TEXT_OR_ACTIVATION'
scope['status']='NOT_RUN_TEMPLATE_REQUIRES_ROOT_REVIEW_NEW_SCOPE_AND_EXACT_JOB'
(new/'scope.template.json').write_text(json.dumps(scope,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
readme=(new/'README.md').read_text(encoding='utf-8').replace('# Native path entry candidate 02 — NOT_RUN','# Native path entry candidate 03 — NOT_RUN',1)
readme=readme.replace('The verified dialog must be foreground; actual warning','The verified dialog must be active in its own GUI thread; actual warning')
readme+='''
Revision 03 is a controller semantics repair authorized by Root. The original
01/02 candidates and actual01 evidence remain unchanged and failed. actual01
recorded no OK attempt and no uncertain input: the global-foreground guard
blocked after exact Unicode path input. Byte-level decoding proves one backslash
per separator, not doubled paths. There is no recorded thread-active snapshot
from that run and no basis to diagnose a production foreground-permission bug.

Both former foreground equality guards now query GetGUIThreadInfo for the
actual dialog TID obtained from its same-Core PID. cbSize uses Marshal.SizeOf;
the sequential layout uses pointer-width IntPtr members. The query must succeed,
the dialog PID/TID must match before/after, hwndActive must equal that same
dialog, and nonzero hwndFocus must belong to the same Core and be the dialog or
its descendant. Owned-focus is an extra conservative guard; BM_CLICK does not
require the Button itself to have focus. Existing chooser/prompt/unique Edit/
Button/warning-owner guards and final action/cleanup deadlines remain intact.
Global foreground is recorded as an HWND number only; no foreign title/text,
activation, AttachThreadInput, keyboard, new COM, or replay is added. Failed
active-state observation is a no-post block, not proof of an uncertain OK.

Runner decoding now validates complete bounded JSON and explicit phase/status/
boolean/cleanup fields before classifying exit 2. A known BLOCKED helper outcome
is recorded with its real phase, attempts, uncertainty, and cleanup before the
runner fails. No-OK plus outcome_uncertain=false remains a known no-OK
observation; malformed envelopes remain unknown. Successful Native/Main
authorization checks are unchanged. No previous failed run is relabelled.

Only new active-thread/parser predicates and full AST/Node syntax are checked;
the 28 prior pure cases are inherited, not rerun. All revision03 runtime is
NOT_RUN. Microsoft references: GetActiveWindow explicitly directs callers to
GetGUIThreadInfo for another thread's active window:
https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getactivewindow
https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getguithreadinfo
https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-guithreadinfo
https://learn.microsoft.com/en-us/windows/win32/controls/bm-click
'''
(new/'README.md').write_text(readme,encoding='utf-8')
print(json.dumps({'status':'REVISION03_SOURCE_PREPARED_NOT_RUN','path':str(new),'harness':scope['harness']}))
