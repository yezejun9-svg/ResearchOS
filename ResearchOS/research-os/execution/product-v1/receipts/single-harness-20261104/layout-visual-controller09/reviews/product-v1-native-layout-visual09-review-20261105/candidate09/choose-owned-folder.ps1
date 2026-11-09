param(
  [Parameter(Mandatory=$true)][string]$ScopePath,
  [Parameter(Mandatory=$true)][string]$ScopeSHA256,
  [Parameter(Mandatory=$true)][string]$ScopeNonce,
  [Parameter(Mandatory=$true)][string]$CoreIdentityPath,
  [Parameter(Mandatory=$true)][string]$HistoryPath
)
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$process=$null;$chooser=[IntPtr]::Zero;$dialogValidated=$false
$phase='PREFLIGHT';$uncertain=$false;$validOkAttempted=$false;$invalidOkAttempted=$false
$history=[Collections.Generic.List[object]]::new()
$historyFile=$null
$result=@{schema='researchos.owned-native-path-entry/1';status='BLOCKED';clicked_ok=$false
  input_is_authorization=$false;actual_task_submissions=0;model_outcome='NOT_RUN_ZERO_BUDGET'
  authorization_state='NOT_ESTABLISHED';cleanup=@{attempted=$false;status='NOT_NEEDED'}}
function Record([string]$Event,$Evidence) {
  $row=@{sequence=$history.Count+1;at=[DateTime]::UtcNow.ToString('o');phase=$script:phase;event=$Event;evidence=$Evidence}
  $history.Add($row)
  if ($null -ne $script:historyFile) {
    try {[IO.File]::AppendAllText($script:historyFile,(($row | ConvertTo-Json -Depth 8 -Compress)+[Environment]::NewLine),[Text.UTF8Encoding]::new($false))}
    catch {$script:journalFailure=$_.Exception.Message;throw 'HELPER_HISTORY_WRITE_FAILED_NO_NEW_ACTION'}
  }
}
function Require([bool]$Condition,[string]$Code) {
  Record 'GUARD' @{code=$Code;passed=$Condition}
  if (-not $Condition) {throw $Code}
}
function Convert-NativeDeadlineUtc($Value) {
  if ($Value -isnot [string] -or $Value -cnotmatch '\A[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}Z\z') {throw 'UTC_WIRE_STRING_REQUIRED'}
  try {return [DateTimeOffset]::ParseExact($Value,"yyyy-MM-dd'T'HH:mm:ss.fff'Z'",[Globalization.CultureInfo]::InvariantCulture,
    ([Globalization.DateTimeStyles]::AssumeUniversal -bor [Globalization.DateTimeStyles]::AdjustToUniversal)).UtcDateTime}
  catch {throw 'UTC_WIRE_VALUE_INVALID'}
}
function Select-UniqueEdit($Rows,[int]$ExpectedPid,[long]$ExpectedParent,[bool]$Truncated) {
  if ($Truncated) {throw 'CHILD_ENUMERATION_TRUNCATED'}
  $edits=@($Rows | Where-Object {$_.process_id -eq $ExpectedPid -and $_.parent -eq $ExpectedParent -and
    $_.class_name -ceq 'Edit' -and $_.visible -eq $true -and $_.enabled -eq $true})
  if ($edits.Count -ne 1) {throw 'OWNED_DIRECT_EDIT_NOT_UNIQUE'}
  return $edits[0]
}
function Assert-ExactText([string]$Actual,[string]$Expected,[int]$Copied,[int]$Capacity) {
  if ($Capacity -lt 2 -or $Copied -lt 0 -or $Copied -ge ($Capacity-1) -or
    $Copied -ne $Actual.Length -or -not [string]::Equals($Actual,$Expected,[StringComparison]::Ordinal)) {throw 'INPUT_READBACK_NOT_EXACT_OR_TRUNCATED'}
}
function Assert-WindowHandleOwner($Identity,[int]$ExpectedPid) {
  if ($Identity.hwnd -eq 0) {throw 'WINDOW_HANDLE_ZERO_NO_TARGET'}
  if ($Identity.is_window -ne $true) {throw 'WINDOW_HANDLE_INVALID_NO_TARGET'}
  if ($Identity.thread_id -le 0 -or $Identity.process_id -le 0) {throw 'WINDOW_THREAD_PID_UNAVAILABLE_NO_TARGET'}
  if ($Identity.process_id -ne $ExpectedPid) {throw 'FOREIGN_WINDOW_PID'}
}
function Assert-WarningDismissSelector($Selector) {
  if (($Selector.expected_control_id -isnot [int] -and $Selector.expected_control_id -isnot [long]) -or
    $Selector.expected_control_id -ne 2 -or
    ($Selector.expected_button_count -isnot [int] -and $Selector.expected_button_count -isnot [long]) -or $Selector.expected_button_count -ne 1 -or
    $Selector.basis -cne 'ACTUAL03_OBSERVED_SINGLE_BUTTON_CONTROL_ID_2' -or
    $Selector.message_box_result_is_control_id -isnot [bool] -or $Selector.message_box_result_is_control_id -ne $false -or
    $Selector.evidence_event -cne 'WARNING_IDOK_CHILD_METADATA' -or
    ($Selector.evidence_event_sequence -isnot [int] -and $Selector.evidence_event_sequence -isnot [long]) -or $Selector.evidence_event_sequence -ne 36 -or
    $Selector.evidence_sha256 -cne '392cd6f17926114f890b74dc28952dc1696d4b20a3444dfd2821b52ddb826423' -or
    [IO.Path]::GetFullPath($Selector.evidence_path) -ine [IO.Path]::GetFullPath('C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-native-path-entry-中文-run-03/receipts/native-folder-automation.json')) {
    throw 'ACTUAL03_WARNING_DISMISS_SELECTOR_PIN_REQUIRED'
  }
}
function Select-UniqueWarningDismissButton($Rows,[int]$ExpectedPid,[long]$WarningHwnd,[bool]$Truncated,[long]$DirectLookupHwnd,[int]$ExpectedControlId) {
  if ($ExpectedControlId -ne 2) {throw 'WARNING_DISMISS_EXPECTED_CONTROL_ID_MUST_BE_PINNED_2'}
  if ($Truncated) {throw 'WARNING_CHILD_ENUMERATION_TRUNCATED_NO_POST'}
  foreach ($row in $Rows) {
    if ($row.hwnd -le 0 -or $row.process_id -ne $ExpectedPid -or $row.is_child -ne $true -or
      $row.root_dialog -ne $WarningHwnd) {throw 'WARNING_CHILD_OWNERSHIP_OR_RELATION_UNCONFIRMED_NO_POST'}
  }
  # MessageBox's return IDOK is not a child-control ID contract. The pinned
  # actual03 metadata showed one Button, control ID 2. Count every Button,
  # including hidden/disabled/different-ID Buttons; no arbitrary-ID fallback.
  $buttons=@($Rows | Where-Object {$_.class_name -ceq 'Button'})
  if ($buttons.Count -ne 1) {throw 'WARNING_DISMISS_BUTTON_NOT_UNIQUE_NO_POST'}
  $candidate=$buttons[0]
  if ($candidate.control_id -ne $ExpectedControlId -or $candidate.visible -ne $true -or $candidate.enabled -ne $true) {
    throw 'WARNING_DISMISS_CONTROL_ID_OR_STATE_UNCONFIRMED_NO_POST'
  }
  if ($DirectLookupHwnd -ne 0 -and $candidate.hwnd -ne $DirectLookupHwnd) {throw 'WARNING_DISMISS_LOOKUP_CHANGED_NO_POST'}
  return $candidate
}
function Assert-DialogThreadFacts($Snapshot,[int]$ExpectedPid,[long]$ExpectedDialog) {
  if ($Snapshot.query_succeeded -ne $true -or $Snapshot.dialog_hwnd -ne $ExpectedDialog -or
    $Snapshot.dialog_pid_before -ne $ExpectedPid -or $Snapshot.dialog_pid_after -ne $ExpectedPid -or
    $Snapshot.dialog_tid_before -le 0 -or $Snapshot.dialog_tid_after -ne $Snapshot.dialog_tid_before -or
    $Snapshot.active_hwnd -ne $ExpectedDialog -or $Snapshot.active_pid -ne $ExpectedPid -or
    $Snapshot.active_tid -ne $Snapshot.dialog_tid_before -or
    $Snapshot.focus_hwnd -le 0 -or $Snapshot.focus_pid -ne $ExpectedPid -or
    $Snapshot.focus_is_dialog_or_child -ne $true) {throw 'DIALOG_THREAD_ACTIVE_OR_FOCUS_UNCONFIRMED_NO_POST'}
}
function Assert-MessageDeadline([DateTime]$Now,[DateTime]$Limit) {
  if ($Now.Kind -ne [DateTimeKind]::Utc -or $Limit.Kind -ne [DateTimeKind]::Utc -or $Now -ge $Limit) {
    throw 'MESSAGE_SEND_DEADLINE_EXPIRED_OR_NON_UTC'
  }
}
try {
  Require ((Get-FileHash -LiteralPath $ScopePath -Algorithm SHA256).Hash.ToLowerInvariant() -ceq $ScopeSHA256) 'SCOPE_PIN'
  $scope=Get-Content -LiteralPath $ScopePath -Raw -Encoding UTF8 | ConvertFrom-Json -DateKind String
  Require ($scope.status -ceq 'ROOT_APPROVED_REAL_RUN' -and $scope.scope_nonce -ceq $ScopeNonce) 'SCOPE_AUTHORIZED'
  Require ($scope.budget.task_submissions -eq 0 -and $scope.budget.model_calls -eq 0 -and $scope.budget.automatic_retries -eq 0 -and
    $scope.native_picker.profile -ceq 'INVALID_VALID_PATH_ENTRY_ONLY' -and $scope.native_picker.operator_fallback -eq $false) 'ZERO_BUDGET_PATH_PROFILE'
  Require ($scope.native_picker.validation_warning.caption -is [string] -and $scope.native_picker.validation_warning.caption.Length -gt 0 -and
    $scope.native_picker.validation_warning.text -is [string] -and $scope.native_picker.validation_warning.text.Length -gt 0 -and
    $scope.native_picker.validation_warning.source_sha256 -cmatch '^[a-f0-9]{64}$') 'FROZEN_PRODUCTION_WARNING_PINS_REQUIRED'
  Require (@($scope.source.pins | Where-Object {$_.path -ceq 'internal/host/native_folder_windows.go' -and
    $_.sha256 -ceq $scope.native_picker.validation_warning.source_sha256}).Count -eq 1) 'WARNING_NATIVE_SOURCE_BINDING'
  $warningDismissSelector=$scope.native_picker.validation_warning.dismiss_selector
  Assert-WarningDismissSelector $warningDismissSelector
  Require ((Get-FileHash -LiteralPath $warningDismissSelector.evidence_path -Algorithm SHA256).Hash.ToLowerInvariant() -ceq $warningDismissSelector.evidence_sha256) 'ACTUAL03_WARNING_SELECTOR_EVIDENCE_FILE_PIN'
  $warningControlId=[int]$warningDismissSelector.expected_control_id
  $runRoot=[IO.Path]::GetFullPath($scope.run_root)
  $fixture=[IO.Path]::GetFullPath((Join-Path $runRoot 'workspace'))
  $invalid=[IO.Path]::GetFullPath((Join-Path $runRoot ('invalid-nonexistent-'+$ScopeNonce)))
  Require ([IO.Path]::GetFullPath($CoreIdentityPath) -ieq (Join-Path $runRoot 'receipts\owned-core.json')) 'IDENTITY_RECEIPT_PATH'
  Require ([IO.Path]::GetFullPath($HistoryPath) -ieq (Join-Path $runRoot 'receipts\native-helper-history.ndjson')) 'HISTORY_RECEIPT_PATH'
  Require ((Test-Path -LiteralPath $HistoryPath -PathType Leaf) -and (Get-Item -LiteralPath $HistoryPath).Length -eq 0) 'FRESH_EMPTY_HISTORY_RECEIPT'
  $historyFile=[IO.Path]::GetFullPath($HistoryPath)
  foreach ($row in $history.ToArray()) {[IO.File]::AppendAllText($historyFile,(($row|ConvertTo-Json -Depth 8 -Compress)+[Environment]::NewLine),[Text.UTF8Encoding]::new($false))}
  $identity=Get-Content -LiteralPath $CoreIdentityPath -Raw -Encoding UTF8 | ConvertFrom-Json -DateKind String
  Require ($identity.scope_nonce -ceq $ScopeNonce -and $identity.identity_source -ceq 'ROS_DESKTOP_REPORT.ready_to_show') 'IDENTITY_SOURCE'
  $core=$identity.owned_core_identity;$coreId=[int]$core.pid
  Require ($coreId -gt 0 -and $core.created_ns -cmatch '^[0-9]+$' -and $core.image_sha256 -ceq $scope.bundle.control_sha256) 'CORE_IDENTITY'
  $actionDeadline=Convert-NativeDeadlineUtc $identity.action_deadline_utc
  $cleanupDeadline=$actionDeadline.AddMilliseconds([int]$scope.deadlines.close_ms)
  $expectedImage=[IO.Path]::GetFullPath((Join-Path $scope.bundle.root 'apps\desktop\resources\control\researchos-control.exe'))
  $process=[Diagnostics.Process]::GetProcessById($coreId);$null=$process.Handle
  function Assert-Core([switch]$ForCleanup) {
    $limit=$actionDeadline;if ($ForCleanup) {$limit=$cleanupDeadline}
    if ([DateTime]::UtcNow -ge $limit) {throw 'NATIVE_DEADLINE'}
    if ($process.HasExited) {throw 'OWNED_CORE_EXITED'}
    $created=[decimal]($process.StartTime.ToUniversalTime().Ticks-621355968000000000)*100
    if ($created.ToString('0',[Globalization.CultureInfo]::InvariantCulture) -cne $core.created_ns) {throw 'CORE_CREATION_CHANGED'}
    if ([IO.Path]::GetFullPath($process.MainModule.FileName) -ine $expectedImage) {throw 'CORE_IMAGE_PATH_CHANGED'}
    if ((Get-FileHash -LiteralPath $expectedImage -Algorithm SHA256).Hash.ToLowerInvariant() -cne $core.image_sha256) {throw 'CORE_IMAGE_HASH_CHANGED'}
    $discovery=Get-Content -LiteralPath (Join-Path $runRoot 'discovery.json') -Raw -Encoding UTF8 | ConvertFrom-Json -DateKind String
    if ($discovery.pid -ne $coreId -or [IO.Path]::GetFullPath($discovery.data_dir) -ine (Join-Path $runRoot 'data')) {throw 'FRESH_DISCOVERY_CHANGED'}
    if ([DateTime]::UtcNow -ge $limit) {throw 'NATIVE_DEADLINE_AFTER_IDENTITY_CHECK'}
  }
  Assert-Core
  function Assert-Fixture {
    $cursor=Get-Item -LiteralPath $fixture
    Require $cursor.PSIsContainer 'FIXTURE_DIRECTORY'
    while ($null -ne $cursor) {Require (($cursor.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) 'FIXTURE_NO_REPARSE';$cursor=$cursor.Parent}
  }
  Assert-Fixture
  Require (-not (Test-Path -LiteralPath $invalid)) 'INVALID_TARGET_ABSENT'
  Add-Type -TypeDefinition @'
using System;
using System.Text;
using System.Runtime.InteropServices;
public static class OwnedPathWin32 {
  public delegate bool EnumCallback(IntPtr hwnd, IntPtr extra);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumCallback callback, IntPtr extra);
  [DllImport("user32.dll")] public static extern bool EnumChildWindows(IntPtr parent, EnumCallback callback, IntPtr extra);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hwnd, out uint pid);
  [DllImport("user32.dll",CharSet=CharSet.Unicode)] static extern int GetClassNameW(IntPtr hwnd,StringBuilder b,int length);
  [DllImport("user32.dll")] public static extern bool IsWindow(IntPtr hwnd);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hwnd);
  [DllImport("user32.dll")] public static extern bool IsWindowEnabled(IntPtr hwnd);
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [StructLayout(LayoutKind.Sequential)]
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

  [DllImport("user32.dll")] public static extern IntPtr GetAncestor(IntPtr hwnd,uint flags);
  [DllImport("user32.dll")] public static extern IntPtr GetWindow(IntPtr hwnd,uint flags);
  [DllImport("user32.dll")] public static extern IntPtr GetDlgItem(IntPtr hwnd,int id);
  [DllImport("user32.dll")] public static extern int GetDlgCtrlID(IntPtr hwnd);
  [DllImport("user32.dll",SetLastError=true)] public static extern bool PostMessageW(IntPtr hwnd,uint msg,IntPtr w,IntPtr l);
  [DllImport("user32.dll",EntryPoint="SendMessageTimeoutW",CharSet=CharSet.Unicode,SetLastError=true)]
  public static extern IntPtr SetText(IntPtr hwnd,uint msg,UIntPtr w,[MarshalAs(UnmanagedType.LPWStr)]string text,uint flags,uint timeout,out UIntPtr result);
  [DllImport("user32.dll",EntryPoint="SendMessageTimeoutW",CharSet=CharSet.Unicode,SetLastError=true)]
  public static extern IntPtr ReadText(IntPtr hwnd,uint msg,UIntPtr w,[Out]StringBuilder text,uint flags,uint timeout,out UIntPtr result);
  public static string Class(IntPtr hwnd) {var b=new StringBuilder(256);GetClassNameW(hwnd,b,b.Capacity);return b.ToString();}
}
'@
  function Facts([IntPtr]$Handle) {
    $identity=@{hwnd=$Handle.ToInt64();is_window=$false;thread_id=0;process_id=0}
    if ($Handle -ne [IntPtr]::Zero) {
      $identity.is_window=[OwnedPathWin32]::IsWindow($Handle)
      if ($identity.is_window) {
        [uint32]$owner=0
        $identity.thread_id=[OwnedPathWin32]::GetWindowThreadProcessId($Handle,[ref]$owner)
        $identity.process_id=$owner
      }
    }
    # NULL, stale/unavailable, and a confirmed foreign PID are distinct.
    # Failed ownership reads record numeric identity only, never foreign text.
    try {Assert-WindowHandleOwner $identity $coreId}
    catch {Record 'WINDOW_IDENTITY_REJECTED' @{identity=$identity;reason=$_.Exception.Message};throw}
    return @{hwnd=$Handle.ToInt64();process_id=$identity.process_id;class_name=[OwnedPathWin32]::Class($Handle)
      parent=[OwnedPathWin32]::GetAncestor($Handle,1).ToInt64();owner=[OwnedPathWin32]::GetWindow($Handle,4).ToInt64()
      visible=[OwnedPathWin32]::IsWindowVisible($Handle);enabled=[OwnedPathWin32]::IsWindowEnabled($Handle)}
  }
  function Read-OwnedText([IntPtr]$Handle) {
    $null=Facts $Handle
    $capacity=4096;$buffer=[Text.StringBuilder]::new($capacity);[UIntPtr]$copied=[UIntPtr]::Zero
    $sent=[OwnedPathWin32]::ReadText($Handle,0x000D,[UIntPtr]$capacity,$buffer,0x23,1000,[ref]$copied)
    if ($sent -eq [IntPtr]::Zero) {$script:uncertain=$true;throw 'WM_GETTEXT_OUTCOME_UNKNOWN'}
    $null=Facts $Handle
    if ($copied.ToUInt64() -ge ($capacity-1) -or $copied.ToUInt64() -ne $buffer.Length) {throw 'WM_GETTEXT_TRUNCATED'}
    return @{text=$buffer.ToString();copied=[int]$copied.ToUInt64();capacity=$capacity}
  }
  function OwnedDialogs([switch]$ForCleanup) {
    Assert-Core -ForCleanup:$ForCleanup
    $script:dialogs=[Collections.Generic.List[object]]::new()
    $script:enumError=$null
    $callback=[OwnedPathWin32+EnumCallback]{param($window,$unused)
      try {
        [uint32]$owner=0;$null=[OwnedPathWin32]::GetWindowThreadProcessId($window,[ref]$owner)
        if ($owner -eq $coreId -and [OwnedPathWin32]::IsWindowVisible($window) -and [OwnedPathWin32]::Class($window) -ceq '#32770') {
          if ($script:dialogs.Count -ge 8) {throw 'OWNED_DIALOG_ENUMERATION_LIMIT'}
          $script:dialogs.Add((Facts $window))
        };return $true
      } catch {$script:enumError=$_.Exception.Message;return $false}
    }
    $null=[OwnedPathWin32]::EnumWindows($callback,[IntPtr]::Zero)
    if ($null -ne $script:enumError) {throw $script:enumError}
    return $script:dialogs.ToArray()
  }
  function ChildFacts([IntPtr]$Parent) {
    $script:children=[Collections.Generic.List[object]]::new();$script:truncated=$false
    $script:childEnumError=$null
    $null=Facts $Parent
    $callback=[OwnedPathWin32+EnumCallback]{param($child,$unused)
      try {
        if ($script:children.Count -ge 128) {$script:truncated=$true;return $false}
        $row=Facts $child
        $row.root_dialog=$Parent.ToInt64()
        $row.is_child=[OwnedPathWin32]::IsChild($Parent,$child)
        $row.control_id=$null
        # GetDlgCtrlID is defined for child controls, not top-level windows.
        if ($row.is_child) {$row.control_id=[OwnedPathWin32]::GetDlgCtrlID($child)}
        $script:children.Add($row);return $true
      } catch {$script:childEnumError=$_.Exception.Message;return $false}
    }
    $null=[OwnedPathWin32]::EnumChildWindows($Parent,$callback,[IntPtr]::Zero)
    if ($null -ne $script:childEnumError) {throw $script:childEnumError}
    if ($script:truncated) {throw 'CHILD_ENUMERATION_TRUNCATED'}
    return $script:children.ToArray()
  }
  function Assert-Chooser([switch]$WithWarning,[switch]$ForCleanup) {
    Assert-Core -ForCleanup:$ForCleanup
    $rows=@(OwnedDialogs -ForCleanup:$ForCleanup)
    if ((-not $WithWarning -and $rows.Count -ne 1) -or ($WithWarning -and $rows.Count -ne 2)) {throw 'OWNED_DIALOG_SET_CHANGED'}
    $found=@($rows|Where-Object {$_.hwnd -eq $chooser.ToInt64()})
    if ($found.Count -ne 1 -or (-not $WithWarning -and $found[0].enabled -ne $true)) {throw 'CHOOSER_CHANGED_OR_DISABLED'}
    $prompt=@()
    foreach ($row in @(ChildFacts $chooser)) {
      if ($row.class_name -ceq 'Static') {
        $text=Read-OwnedText ([IntPtr]$row.hwnd)
        if ($text.text -ceq 'Select a ResearchOS workspace folder') {$prompt+=1}
      }
    }
    if ($prompt.Count -ne 1) {throw 'CHOOSER_FIXED_PROMPT_NOT_UNIQUE'}
  }
  function Discover-Edit {
    Assert-Chooser
    $rows=@(ChildFacts $chooser)
    $row=Select-UniqueEdit $rows $coreId $chooser.ToInt64() $false
    $edit=[IntPtr]$row.hwnd
    $again=Facts $edit
    if ($again.parent -ne $chooser.ToInt64() -or $again.class_name -cne 'Edit' -or -not $again.visible -or -not $again.enabled) {throw 'EDIT_IDENTITY_CHANGED'}
    return $edit
  }
  function Enter-Path([string]$Path) {
    Require ($Path.Length -gt 0 -and $Path.Length -lt 3000 -and -not $Path.Contains([char]0)) 'BOUNDED_PATH_INPUT'
    $edit=Discover-Edit
    [UIntPtr]$messageResult=[UIntPtr]::Zero
    Record 'WM_SETTEXT_INTENT' @{hwnd=$edit.ToInt64();path=$Path;input_is_authorization=$false}
    # Standard WM_SETTEXT (0xC) / WM_GETTEXT (0xD), below WM_USER.
    # Windows marshals these system messages; no custom LPWSTR or remote memory.
    Assert-Core
    if ((Discover-Edit) -ne $edit) {throw 'EDIT_CHANGED_IMMEDIATELY_BEFORE_INPUT'}
    Assert-MessageDeadline ([DateTime]::UtcNow) $actionDeadline
    $sent=[OwnedPathWin32]::SetText($edit,0x000C,[UIntPtr]::Zero,$Path,0x23,1000,[ref]$messageResult)
    if ($sent -eq [IntPtr]::Zero) {$script:uncertain=$true;throw 'WM_SETTEXT_OUTCOME_UNKNOWN_NO_RETRY'}
    if ($messageResult.ToUInt64() -ne 1) {throw 'WM_SETTEXT_REJECTED'}
    $fresh=Discover-Edit
    if ($fresh -ne $edit) {throw 'EDIT_REPLACED_AFTER_INPUT'}
    $read=Read-OwnedText $fresh
    Assert-ExactText $read.text $Path $read.copied $read.capacity
    Record 'INPUT_READBACK_EXACT' @{hwnd=$fresh.ToInt64();path=$read.text;input_is_authorization=$false}
    return @{hwnd=$fresh.ToInt64();dialog_hwnd=$chooser.ToInt64();path=$read.text;method='SYSTEM_MARSHALLED_WM_SETTEXT_WM_GETTEXT';input_is_authorization=$false}
  }
  function Assert-DialogThreadState([IntPtr]$Dialog,[switch]$ForCleanup) {
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
  function Get-OwnedWarningDismissButton([IntPtr]$Warning) {
    Assert-Warning $Warning
    $direct=[OwnedPathWin32]::GetDlgItem($Warning,$warningControlId)
    Record 'WARNING_DISMISS_DIRECT_LOOKUP' @{dialog=$Warning.ToInt64();control_id=$warningControlId;hwnd=$direct.ToInt64();is_zero=($direct -eq [IntPtr]::Zero)}
    if ($direct -ne [IntPtr]::Zero) {
      $lookup=Facts $direct
      $lookup.is_child=[OwnedPathWin32]::IsChild($Warning,$direct)
      $lookup.control_id=$null
      if ($lookup.is_child) {$lookup.control_id=[OwnedPathWin32]::GetDlgCtrlID($direct)}
      Record 'WARNING_DISMISS_DIRECT_LOOKUP_FACTS' $lookup
      if (-not $lookup.is_child -or $lookup.control_id -ne $warningControlId -or $lookup.class_name -cne 'Button' -or
        -not $lookup.visible -or -not $lookup.enabled) {throw 'WARNING_DIRECT_DISMISS_LOOKUP_INVALID_NO_POST'}
    }
    $rows=@()
    try {$rows=@(ChildFacts $Warning)}
    catch {
      Record 'WARNING_DISMISS_CHILD_METADATA' @{dialog=$Warning.ToInt64();limit=128;truncated=$script:truncated
        rows=$script:children.ToArray();enumeration_error=$_.Exception.Message;window_text_read=$false}
      throw
    }
    Record 'WARNING_DISMISS_CHILD_METADATA' @{dialog=$Warning.ToInt64();limit=128;truncated=$script:truncated
      rows=$rows;enumeration_error=$null;window_text_read=$false}
    $candidate=Select-UniqueWarningDismissButton $rows $coreId $Warning.ToInt64() $script:truncated $direct.ToInt64() $warningControlId
    return [IntPtr]$candidate.hwnd
  }
  function Post-OwnedButton([IntPtr]$Dialog,[int]$Id,[string]$Purpose,[switch]$Warning,[switch]$ForCleanup) {
    Assert-Chooser -WithWarning:$Warning -ForCleanup:$ForCleanup
    if ($Warning) {Assert-Warning $Dialog}
    Assert-DialogThreadState $Dialog -ForCleanup:$ForCleanup
    if ($Warning) {
      if ($Id -ne $warningControlId -or $Purpose -cne 'WARNING_DISMISS') {throw 'WARNING_ONLY_PINNED_DISMISS_CONTROL_ALLOWED'}
      $button=Get-OwnedWarningDismissButton $Dialog
    } else {
      $button=[OwnedPathWin32]::GetDlgItem($Dialog,$Id);$row=Facts $button
      if ($row.parent -ne $Dialog.ToInt64() -or $row.class_name -cne 'Button' -or -not $row.visible -or -not $row.enabled) {throw 'OWNED_BUTTON_IDENTITY_OR_STATE'}
    }
    Record 'BUTTON_QUEUE_INTENT' @{dialog=$Dialog.ToInt64();button=$button.ToInt64();control_id=$Id;purpose=$Purpose}
    # Async standard BM_CLICK avoids blocking the controller in the modal
    # validation callback. Queue acceptance alone never establishes its result.
    Assert-Core -ForCleanup:$ForCleanup
    if ($Warning) {
      $fresh=Get-OwnedWarningDismissButton $Dialog
      if ($fresh -ne $button) {throw 'WARNING_DISMISS_CHANGED_IMMEDIATELY_BEFORE_QUEUE'}
    } else {
      $fresh=[OwnedPathWin32]::GetDlgItem($Dialog,$Id);$now=Facts $fresh
      if ($fresh -ne $button -or $now.parent -ne $Dialog.ToInt64() -or $now.class_name -cne 'Button' -or
        -not $now.visible -or -not $now.enabled) {throw 'BUTTON_CHANGED_IMMEDIATELY_BEFORE_QUEUE'}
    }
    Assert-DialogThreadState $Dialog -ForCleanup:$ForCleanup
    $messageDeadline=$actionDeadline
    if ($ForCleanup) {$messageDeadline=$cleanupDeadline}
    Assert-MessageDeadline ([DateTime]::UtcNow) $messageDeadline
    $script:uncertain=$true
    if ($Purpose -ceq 'INVALID_OK') {$script:invalidOkAttempted=$true}
    if ($Purpose -ceq 'VALID_OK') {$script:validOkAttempted=$true}
    if (-not [OwnedPathWin32]::PostMessageW($button,0x00F5,[IntPtr]::Zero,[IntPtr]::Zero)) {throw 'BUTTON_QUEUE_FAILED_OUTCOME_UNKNOWN'}
    Record 'BUTTON_POST_ACCEPTED_EFFECT_UNKNOWN' @{dialog=$Dialog.ToInt64();button=$button.ToInt64();control_id=$Id;purpose=$Purpose}
  }
  function Assert-Warning([IntPtr]$Warning) {
    Assert-Chooser -WithWarning
    $rows=@(OwnedDialogs);$other=@($rows|Where-Object {$_.hwnd -ne $chooser.ToInt64()})
    if ($other.Count -ne 1 -or $other[0].hwnd -ne $Warning.ToInt64() -or $other[0].owner -ne $chooser.ToInt64() -or -not $other[0].enabled) {throw 'WARNING_OWNER_OR_IDENTITY_CHANGED'}
    $caption=Read-OwnedText $Warning
    if ($caption.text -cne $scope.native_picker.validation_warning.caption) {throw 'WARNING_CAPTION_PIN_MISMATCH'}
    $matches=0
    foreach ($row in @(ChildFacts $Warning)) {
      if ($row.class_name -ceq 'Static') {
        $text=Read-OwnedText ([IntPtr]$row.hwnd)
        if ($text.text -ceq $scope.native_picker.validation_warning.text) {$matches++}
      }
    }
    if ($matches -ne 1) {throw 'WARNING_TEXT_PIN_MISMATCH'}
  }
  $phase='DISCOVER_CHOOSER'
  $waitUntil=[DateTime]::UtcNow.AddSeconds(15)
  do {$rows=@(OwnedDialogs);if ($rows.Count -gt 1) {throw 'CHOOSER_NOT_UNIQUE'}
    if ($rows.Count -eq 0) {Start-Sleep -Milliseconds 100}
  } while ($rows.Count -eq 0 -and [DateTime]::UtcNow -lt $waitUntil)
  Require ($rows.Count -eq 1) 'CHOOSER_FOUND'
  $chooser=[IntPtr]$rows[0].hwnd;Assert-Chooser;$dialogValidated=$true
  $result.dialog_hwnd=$chooser.ToInt64()
  Record 'CHOOSER_VERIFIED' @{hwnd=$chooser.ToInt64();owner_pid=$coreId;prompt='Select a ResearchOS workspace folder'}
  $phase='INVALID_PATH'
  $result.invalid_input=Enter-Path $invalid
  Require (-not (Test-Path -LiteralPath $invalid)) 'INVALID_TARGET_STILL_ABSENT'
  Post-OwnedButton $chooser 1 'INVALID_OK'
  $warning=[IntPtr]::Zero;$waitUntil=[DateTime]::UtcNow.AddSeconds(10)
  do {
    $rows=@(OwnedDialogs)
    if ($rows.Count -gt 2) {throw 'INVALID_WARNING_DIALOG_SET_UNEXPECTED'}
    $other=@($rows|Where-Object {$_.hwnd -ne $chooser.ToInt64()})
    if ($other.Count -eq 1) {$warning=[IntPtr]$other[0].hwnd;Assert-Warning $warning;break}
    Start-Sleep -Milliseconds 100
  } while ([DateTime]::UtcNow -lt $waitUntil)
  Require ($warning -ne [IntPtr]::Zero) 'INVALID_WARNING_OBSERVED'
  $uncertain=$false
  $result.invalid_warning=@{hwnd=$warning.ToInt64();owner=$chooser.ToInt64();owner_pid=$coreId
    caption=$scope.native_picker.validation_warning.caption;text=$scope.native_picker.validation_warning.text;observed=$true}
  Record 'INVALID_WARNING_VERIFIED' $result.invalid_warning
  Post-OwnedButton $warning $warningControlId 'WARNING_DISMISS' -Warning
  $waitUntil=[DateTime]::UtcNow.AddSeconds(5)
  do {$rows=@(OwnedDialogs);if ($rows.Count -eq 1 -and $rows[0].hwnd -eq $chooser.ToInt64() -and $rows[0].enabled) {break};Start-Sleep -Milliseconds 100}
  while ([DateTime]::UtcNow -lt $waitUntil)
  Assert-Chooser;$uncertain=$false
  Require (-not (Test-Path -LiteralPath $invalid)) 'INVALID_INPUT_DID_NOT_CREATE_TARGET'
  $result.invalid_kept_chooser_open=$true;Record 'INVALID_DISMISSED_SAME_CHOOSER_RETAINED' @{hwnd=$chooser.ToInt64()}
  $phase='VALID_PATH'
  Assert-Fixture
  $result.valid_input=Enter-Path $fixture
  # Input text remains non-authoritative. The real Shell must produce its PIDL,
  # then production canonical/reparse/selectionRef checks and Main bootstrap run.
  Assert-Fixture
  Post-OwnedButton $chooser 1 'VALID_OK'
  $waitUntil=[DateTime]::UtcNow.AddSeconds(10)
  do {$rows=@(OwnedDialogs);if ($rows.Count -eq 0 -and -not [OwnedPathWin32]::IsWindow($chooser)) {break};Start-Sleep -Milliseconds 100}
  while ([DateTime]::UtcNow -lt $waitUntil)
  Require ($rows.Count -eq 0 -and -not [OwnedPathWin32]::IsWindow($chooser)) 'VALID_SHELL_DIALOG_CLOSED'
  $uncertain=$false;$result.clicked_ok=$true;$result.status='VALID_SHELL_OK_CLOSED_REQUIRES_MAIN_BINDING'
  $result.authorization_state='SHELL_CONFIRM_OBSERVED_MAIN_BINDING_NOT_YET_VERIFIED'
  Record 'VALID_SHELL_DIALOG_CLOSED' @{main_binding_required=$true;path=$fixture}
} catch {
  $result.reason=$_.Exception.Message
  try {Record 'FAILURE' @{reason=$result.reason;uncertain=$uncertain;invalid_ok_attempted=$invalidOkAttempted;valid_ok_attempted=$validOkAttempted}} catch {}
  if ($null -ne $script:journalFailure) {$uncertain=$true;$result.history_write_failure=$script:journalFailure}
  if ($uncertain -or $validOkAttempted -or ($invalidOkAttempted -and -not $result.invalid_kept_chooser_open)) {
    $result.cleanup.status='OUTCOME_UNKNOWN_NO_FURTHER_CLICK_ROOT_JOB_REQUIRED'
    $result.authorization_state='UNKNOWN_NO_AUTHORIZATION_INFERRED_NO_RETRY'
  } elseif ($dialogValidated) {
    $result.cleanup.attempted=$true
    try {
      Post-OwnedButton $chooser 2 'CANCEL' -ForCleanup
      $limit=$cleanupDeadline
      do {
        Assert-Core -ForCleanup
        if (-not [OwnedPathWin32]::IsWindow($chooser)) {break}
        Start-Sleep -Milliseconds 100
      } while ([DateTime]::UtcNow -lt $limit)
      if ([OwnedPathWin32]::IsWindow($chooser)) {throw 'CANCEL_CLOSE_UNCONFIRMED'}
      $uncertain=$false;$result.cleanup.status='OWNED_IDCANCEL_CLOSED'
      $result.authorization_state='NO_VALID_OK_CONFIRMED'
    } catch {$result.cleanup.status='OWNERSHIP_OR_CANCEL_UNKNOWN_ROOT_JOB_REQUIRED';$result.cleanup.reason=$_.Exception.Message}
  } else {$result.cleanup.status='OWNERSHIP_UNCONFIRMED_NO_CLICK'}
} finally {
  $result.phase=$phase;$result.invalid_ok_attempted=$invalidOkAttempted;$result.valid_ok_attempted=$validOkAttempted
  $result.history=$history.ToArray();$result.outcome_uncertain=$uncertain
  if ($null -ne $process) {$process.Dispose()}
}
$result | ConvertTo-Json -Depth 14 -Compress
if (-not $result.clicked_ok) {exit 2}
