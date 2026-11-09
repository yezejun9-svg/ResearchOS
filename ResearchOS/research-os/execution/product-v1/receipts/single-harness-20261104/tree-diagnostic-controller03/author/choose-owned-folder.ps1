param(
  [Parameter(Mandatory=$true)][string]$ScopePath,
  [Parameter(Mandatory=$true)][string]$ScopeSHA256,
  [Parameter(Mandatory=$true)][string]$ScopeNonce,
  [Parameter(Mandatory=$true)][string]$CoreIdentityPath
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$process = $null
$hwnd = [IntPtr]::Zero
$dialogValidated = $false
$okAttempted = $false
$result = @{ schema='researchos.owned-native-folder-diagnostic/1'; status='BLOCKED'; clicked_ok=$false; cleanup=@{ attempted=$false; status='NOT_NEEDED' } }

function Assert-DiagnosticOnly($Value) {
  if ($Value -isnot [bool] -or $Value -ne $true) { throw 'DIAGNOSTIC_ONLY_SCOPE_REQUIRED_NO_OK' }
}
function Select-UniqueNativeTree($Candidates,[int]$OwnerPid,[bool]$Truncated) {
  if ($Truncated) { throw 'NATIVE_TREE_ENUMERATION_TRUNCATED_NO_OK' }
  $matchesFound=@($Candidates | Where-Object {
    $_.class_name -ceq 'SysTreeView32' -and $_.process_id -eq $OwnerPid -and $_.visible -eq $true -and $_.enabled -eq $true
  })
  if ($matchesFound.Count -ne 1) { throw 'NATIVE_TREE_NOT_UNIQUE_NO_OK' }
  return $matchesFound[0]
}
function Assert-DirectNativeFacts($Facts,[int]$OwnerPid) {
  if ($Facts.process_id -ne $OwnerPid -or $Facts.is_child -ne $true -or
    $Facts.class_name -cne 'SysTreeView32' -or $Facts.visible -ne $true -or $Facts.enabled -ne $true) {
    throw 'DIRECT_NATIVE_TREE_OWNER_OR_STATE_CHANGED_NO_OK'
  }
}
function Project-PublicUiaValue([string]$Source,$Value) {
  $raw=$(if ($null -eq $Value) { '' } else { [string]$Value })
  $absolute=$false
  try { $absolute=[IO.Path]::IsPathRooted($raw) } catch {}
  $truncated=$raw.Length -gt 1024
  $text=$raw
  if ($truncated) { $text=$raw.Substring(0,1024) }
  if ($text.Length -gt 0 -and [char]::IsHighSurrogate($text[$text.Length-1])) { $text=$text.Substring(0,$text.Length-1);$truncated=$true }
  return @{source=$Source;value=$text;truncated=$truncated;absolute_candidate=$absolute;selection_authority=$false}
}
function Limit-DiagnosticText($Value) {
  if ($null -eq $Value) { return $null }
  $text=[regex]::Replace([string]$Value,'[\x00-\x1f\x7f]',' ')
  if ($text.Length -gt 96) { $text=$text.Substring(0,96) }
  if ($text.Length -gt 0 -and [char]::IsHighSurrogate($text[$text.Length-1])) { $text=$text.Substring(0,$text.Length-1) }
  return $text
}
function Read-DiagnosticField($Info,[string]$Property,$Failures) {
  try { return $Info.$Property }
  catch {
    $Failures.Add(@{ property=$Property; reason=(Limit-DiagnosticText $_.Exception.Message) })
    return $null
  }
}
function Diagnostic-Number($Value) {
  if ($null -eq $Value) { return $null }
  $number=[double]$Value
  if ([double]::IsNaN($number) -or [double]::IsInfinity($number)) { return $number.ToString([Globalization.CultureInfo]::InvariantCulture) }
  return $number
}
function Project-TreeDiagnostic($Element,[int]$Index) {
  try {
    $info=$Element.Current
    if ($null -eq $info) { throw 'ELEMENT_CURRENT_UNAVAILABLE' }
  } catch {
    return @{ index=$Index; status='ELEMENT_UNAVAILABLE'; reason=(Limit-DiagnosticText $_.Exception.Message) }
  }
  $failures=[Collections.Generic.List[object]]::new()
  $control=Read-DiagnosticField $info 'ControlType' $failures
  $rectangle=Read-DiagnosticField $info 'BoundingRectangle' $failures
  $bounds=$null
  if ($null -ne $rectangle) {
    $bounds=@{
      x=(Diagnostic-Number (Read-DiagnosticField $rectangle 'X' $failures))
      y=(Diagnostic-Number (Read-DiagnosticField $rectangle 'Y' $failures))
      width=(Diagnostic-Number (Read-DiagnosticField $rectangle 'Width' $failures))
      height=(Diagnostic-Number (Read-DiagnosticField $rectangle 'Height' $failures))
      is_empty=(Read-DiagnosticField $rectangle 'IsEmpty' $failures)
    }
  }
  $handle=Read-DiagnosticField $info 'NativeWindowHandle' $failures
  return @{
    index=$Index; status='METADATA_ONLY'
    control_type=(Limit-DiagnosticText $control.ProgrammaticName)
    process_id=(Read-DiagnosticField $info 'ProcessId' $failures)
    native_window_handle=$(if ($null -eq $handle) { $null } else { [string]$handle })
    class_name=(Limit-DiagnosticText (Read-DiagnosticField $info 'ClassName' $failures))
    automation_id=(Limit-DiagnosticText (Read-DiagnosticField $info 'AutomationId' $failures))
    is_offscreen=(Read-DiagnosticField $info 'IsOffscreen' $failures)
    enabled=(Read-DiagnosticField $info 'IsEnabled' $failures)
    bounding_rect=$bounds
    name=(Limit-DiagnosticText (Read-DiagnosticField $info 'Name' $failures))
    property_errors=@($failures)
  }
}

# These functions are pure string/evidence predicates. Tests extract their
# actual AST bodies without running Add-Type, UIAutomation or this script body.
function Convert-NativeDeadlineUtc($Value) {
  if ($Value -isnot [string] -or $Value -cnotmatch '\A[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}Z\z') {
    throw 'NATIVE_UI_DEADLINE_UTC_WIRE_STRING_REQUIRED'
  }
  try {
    $styles = [Globalization.DateTimeStyles]::AssumeUniversal -bor [Globalization.DateTimeStyles]::AdjustToUniversal
    return [DateTimeOffset]::ParseExact($Value, "yyyy-MM-dd'T'HH:mm:ss.fff'Z'",
      [Globalization.CultureInfo]::InvariantCulture, $styles).UtcDateTime
  } catch {
    throw 'NATIVE_UI_DEADLINE_INVALID_UTC_WIRE_VALUE'
  }
}
function Convert-UiaAbsolutePath($Value) {
  if ($null -eq $Value -or $Value -ceq '') { return $null }
  if ($Value -isnot [string] -or $Value.Contains([char]0)) { throw 'UIA_MALFORMED_PATH_NO_OK' }
  if (-not [IO.Path]::IsPathRooted($Value)) {
    if ($Value -match '^\s*[A-Za-z]:' -or $Value -match '^\s*[\\/]' ) { throw 'UIA_MALFORMED_PATH_NO_OK' }
    return $null
  }
  if ($Value -notmatch '^[A-Za-z]:[\\/]' -and $Value -notmatch '^\\\\[^\\]+\\[^\\]+') { throw 'UIA_NOT_FULLY_QUALIFIED_PATH_NO_OK' }
  try { return [IO.Path]::GetFullPath($Value) }
  catch { throw 'UIA_MALFORMED_PATH_NO_OK' }
}
function Assert-UiaPathEvidence($Readings, [string]$Expected, [bool]$RequireProof) {
  $expectedPath = [IO.Path]::GetFullPath($Expected)
  $absoluteValues = [Collections.Generic.List[object]]::new()
  $reliableCount = 0
  foreach ($reading in $Readings) {
    $absolute = Convert-UiaAbsolutePath $reading.value
    if ($null -eq $absolute) { continue }
    if (-not [string]::Equals($absolute,$expectedPath,[StringComparison]::OrdinalIgnoreCase)) { throw 'UIA_CONTRADICTORY_ABSOLUTE_PATH_NO_OK' }
    $absoluteValues.Add(@{ source=$reading.source; path=$absolute })
    if ($reading.source -cin @('ValuePattern','LegacyIAccessiblePattern')) { $reliableCount++ }
  }
  if ($RequireProof -and $reliableCount -lt 1) { throw 'UIA_RELIABLE_ABSOLUTE_PATH_MISSING_NO_OK' }
  return @{ reliable_count=$reliableCount; absolute_values=@($absoluteValues); path=$expectedPath }
}
function Test-UiaPathCandidate([string]$Name, [string]$ExpectedName, $Readings, [string]$ExpectedPath) {
  $candidate = -not [string]::IsNullOrEmpty($ExpectedName) -and $Name -ieq $ExpectedName
  foreach ($reading in $Readings) {
    $absolute = Convert-UiaAbsolutePath $reading.value
    if ($null -ne $absolute -and [string]::Equals($absolute,[IO.Path]::GetFullPath($ExpectedPath),[StringComparison]::OrdinalIgnoreCase)) { $candidate=$true }
  }
  if (-not $candidate) { return $false }
  # Even an exact display-name match cannot override a contradictory absolute
  # value exposed by either provider or the element's Name.
  $null = Assert-UiaPathEvidence $Readings $ExpectedPath $false
  return $true
}
try {
  if ((Get-FileHash -LiteralPath $ScopePath -Algorithm SHA256).Hash.ToLowerInvariant() -cne $ScopeSHA256) { throw 'SCOPE_PIN_MISMATCH' }
  $scope = Get-Content -LiteralPath $ScopePath -Raw -Encoding UTF8 | ConvertFrom-Json
  if ($scope.status -cne 'ROOT_APPROVED_REAL_RUN' -or $scope.scope_nonce -cne $ScopeNonce) { throw 'SCOPE_NOT_AUTHORIZED' }
  Assert-DiagnosticOnly $scope.native_picker.diagnostic_only
  Assert-DiagnosticOnly $scope.native_picker.direct_native_tree
  $runRoot = [IO.Path]::GetFullPath($scope.run_root)
  $fixture = [IO.Path]::GetFullPath((Join-Path $runRoot 'workspace'))
  $identityFile = [IO.Path]::GetFullPath($CoreIdentityPath)
  if ($identityFile -ine (Join-Path $runRoot 'receipts\owned-core.json')) { throw 'IDENTITY_PATH_OUTSIDE_SCOPE' }
  $identity = Get-Content -LiteralPath $identityFile -Raw -Encoding UTF8 | ConvertFrom-Json -DateKind String
  if ($identity.scope_nonce -cne $ScopeNonce -or $identity.identity_source -cne 'ROS_DESKTOP_REPORT.ready_to_show') { throw 'CORE_IDENTITY_SOURCE_MISMATCH' }
  $core = $identity.owned_core_identity
  $actionDeadline = Convert-NativeDeadlineUtc $identity.action_deadline_utc
  $cleanupDeadline = $actionDeadline.AddMilliseconds([int]$scope.deadlines.close_ms)
  $coreId = [int]$core.pid
  if ($coreId -le 0 -or $core.created_ns -cnotmatch '^[0-9]+$' -or $core.image_sha256 -cnotmatch '^[a-f0-9]{64}$') { throw 'CORE_IDENTITY_INVALID' }
  if ($core.image_sha256 -cne $scope.bundle.control_sha256) { throw 'CORE_IMAGE_PIN_MISMATCH' }
  $expectedImage = [IO.Path]::GetFullPath((Join-Path $scope.bundle.root 'apps\desktop\resources\control\researchos-control.exe'))
  $process = [Diagnostics.Process]::GetProcessById($coreId)
  # Retain the process handle throughout selection; PID or HWND alone is insufficient.
  $null = $process.Handle
  function Assert-Core([switch]$ForCleanup) {
    $limit = $actionDeadline
    if ($ForCleanup) { $limit=$cleanupDeadline }
    if ([DateTime]::UtcNow -ge $limit) { throw 'NATIVE_UI_ACTION_DEADLINE_EXPIRED' }
    if ($process.HasExited) { throw 'OWNED_CORE_EXITED' }
    $created = [decimal]($process.StartTime.ToUniversalTime().Ticks - 621355968000000000) * 100
    if ($created.ToString('0', [Globalization.CultureInfo]::InvariantCulture) -cne $core.created_ns) { throw 'OWNED_CORE_CREATION_MISMATCH' }
    if ([IO.Path]::GetFullPath($process.MainModule.FileName) -ine $expectedImage) { throw 'OWNED_CORE_PATH_MISMATCH' }
    if ((Get-FileHash -LiteralPath $expectedImage -Algorithm SHA256).Hash.ToLowerInvariant() -cne $core.image_sha256) { throw 'OWNED_CORE_HASH_MISMATCH' }
    $discovery = Get-Content -LiteralPath (Join-Path $runRoot 'discovery.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($discovery.pid -ne $coreId -or [IO.Path]::GetFullPath($discovery.data_dir) -ine (Join-Path $runRoot 'data')) { throw 'FRESH_DISCOVERY_MISMATCH' }
  }
  Assert-Core
  $item = Get-Item -LiteralPath $fixture
  if (-not $item.PSIsContainer) { throw 'FIXTURE_NOT_DIRECTORY' }
  $cursor = $item
  while ($null -ne $cursor) {
    if (($cursor.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'FIXTURE_ALIAS_REFUSED' }
    $cursor = $cursor.Parent
  }
  Add-Type -TypeDefinition @'
using System;
using System.Text;
using System.Runtime.InteropServices;
public static class OwnedFolderWin32 {
  public delegate bool EnumCallback(IntPtr hwnd, IntPtr extra);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumCallback callback, IntPtr extra);
  [DllImport("user32.dll")] public static extern bool EnumChildWindows(IntPtr parent, EnumCallback callback, IntPtr extra);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hwnd, out uint pid);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetClassName(IntPtr hwnd, StringBuilder text, int length);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr hwnd, StringBuilder text, int length);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hwnd);
  [DllImport("user32.dll")] public static extern bool IsWindowEnabled(IntPtr hwnd);
  [DllImport("user32.dll")] public static extern IntPtr GetDlgItem(IntPtr hwnd, int id);
  [DllImport("user32.dll")] public static extern IntPtr GetParent(IntPtr hwnd);
  [DllImport("user32.dll")] public static extern bool IsChild(IntPtr parent, IntPtr child);
  [DllImport("user32.dll", EntryPoint="SendMessageTimeoutW", SetLastError=true)] public static extern IntPtr ClickTimeout(IntPtr hwnd, uint msg, IntPtr wparam, IntPtr lparam, uint flags, uint timeout, out UIntPtr result);
  public static string Class(IntPtr hwnd) { var b=new StringBuilder(256); GetClassName(hwnd,b,b.Capacity); return b.ToString(); }
  public static string Text(IntPtr hwnd) { var b=new StringBuilder(1024); GetWindowText(hwnd,b,b.Capacity); return b.ToString(); }
}
'@
  Add-Type -AssemblyName UIAutomationClient
  Add-Type -AssemblyName UIAutomationTypes
  $dialogs = [Collections.Generic.List[IntPtr]]::new()
  $enum = [OwnedFolderWin32+EnumCallback]{ param($hwnd,$unused)
    [uint32]$ownerId = 0
    $null = [OwnedFolderWin32]::GetWindowThreadProcessId($hwnd,[ref]$ownerId)
    if ($ownerId -eq $coreId -and [OwnedFolderWin32]::IsWindowVisible($hwnd) -and [OwnedFolderWin32]::Class($hwnd) -ceq '#32770') { $dialogs.Add($hwnd) }
    return $true
  }
  $until = [DateTime]::UtcNow.AddSeconds(20)
  do {
    Assert-Core
    $dialogs.Clear()
    $null = [OwnedFolderWin32]::EnumWindows($enum,[IntPtr]::Zero)
    if ($dialogs.Count -gt 1) { throw 'MULTIPLE_OWNED_DIALOGS' }
    if ($dialogs.Count -eq 0) { Start-Sleep -Milliseconds 200 }
  } while ($dialogs.Count -eq 0 -and [DateTime]::UtcNow -lt $until)
  if ($dialogs.Count -ne 1) { throw 'OWNED_DIALOG_NOT_FOUND' }
  $hwnd = $dialogs[0]
  function Assert-Dialog([switch]$ForCleanup) {
    Assert-Core -ForCleanup:$ForCleanup
    $dialogs.Clear()
    $null = [OwnedFolderWin32]::EnumWindows($enum,[IntPtr]::Zero)
    if ($dialogs.Count -ne 1 -or $dialogs[0] -ne $hwnd) { throw 'OWNED_DIALOG_NOT_UNIQUE_OR_CHANGED' }
    [uint32]$dialogOwner = 0
    $null = [OwnedFolderWin32]::GetWindowThreadProcessId($hwnd,[ref]$dialogOwner)
    if ($dialogOwner -ne $coreId -or -not [OwnedFolderWin32]::IsWindowVisible($hwnd) -or [OwnedFolderWin32]::Class($hwnd) -cne '#32770') { throw 'DIALOG_IDENTITY_CHANGED' }
    $script:prompts = [Collections.Generic.List[string]]::new()
    $childEnum = [OwnedFolderWin32+EnumCallback]{ param($child,$unused)
      if ([OwnedFolderWin32]::Text($child) -ceq 'Select a ResearchOS workspace folder') { $script:prompts.Add('match') }
      return $true
    }
    $null = [OwnedFolderWin32]::EnumChildWindows($hwnd,$childEnum,[IntPtr]::Zero)
    # lpszTitle is an instruction label, not necessarily the localized caption.
    if ($script:prompts.Count -ne 1) { throw 'DIALOG_PROMPT_NOT_UNIQUE' }
  }
  Assert-Dialog
  $dialogValidated=$true
  [UIntPtr]$messageResult = [UIntPtr]::Zero
  # Never send BFFM_SETSELECTIONW/WM_USER pointers across processes. That old
  # candidate is preserved as REJECTED_NOT_RUN. Only real UIAutomation patterns
  # below may navigate/select; no remote memory, injection or fabricated reply.
  function Assert-UiaElement($element) {
    Assert-Dialog
    if ($null -eq $element -or $element.Current.ProcessId -ne $coreId -or -not $element.Current.IsEnabled) { throw 'UIA_ELEMENT_NOT_OWNED_AND_ENABLED' }
  }
  function Read-UiaPathFacts($element) {
    $readings = [Collections.Generic.List[object]]::new()
    $readings.Add(@{ source='Name'; value=$element.Current.Name })
    foreach ($provider in @(
      @{ source='ValuePattern'; id=[Windows.Automation.ValuePattern]::Pattern },
      @{ source='LegacyIAccessiblePattern'; id=[Windows.Automation.LegacyIAccessiblePattern]::Pattern }
    )) {
      $pattern = $null
      if ($element.TryGetCurrentPattern($provider.id,[ref]$pattern)) {
        $readings.Add(@{ source=$provider.source; value=$pattern.Current.Value })
      }
    }
    return @($readings)
  }
  function Expand-UiaNode($element) {
    Assert-UiaElement $element
    $pattern = $null
    if ($element.TryGetCurrentPattern([Windows.Automation.ExpandCollapsePattern]::Pattern,[ref]$pattern)) {
      if ($pattern.Current.ExpandCollapseState -eq [Windows.Automation.ExpandCollapseState]::Collapsed) {
        $pattern.Expand()
        Start-Sleep -Milliseconds 150
      }
    }
  }
  function Select-FixtureThroughRealTree {
    $dialogElement = [Windows.Automation.AutomationElement]::FromHandle($hwnd)
    $treeCondition = [Windows.Automation.PropertyCondition]::new([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::Tree)
    $itemCondition = [Windows.Automation.PropertyCondition]::new([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::TreeItem)
    $trees = $dialogElement.FindAll([Windows.Automation.TreeScope]::Descendants,$treeCondition)
    if ($trees.Count -ne 1) { throw 'UIA_TREE_NOT_UNIQUE_NO_CLICK' }
    $tree = $trees[0]
    Assert-UiaElement $tree
    $drivePattern = '(^|\()' + [regex]::Escape($fixture.Substring(0,2)) + '(\)|\\)?$'
    $driveMatches = [Collections.Generic.List[object]]::new()
    for ($round=0; $round -lt 3; $round++) {
      $driveMatches.Clear()
      $nodes = $tree.FindAll([Windows.Automation.TreeScope]::Descendants,$itemCondition)
      foreach ($node in $nodes) {
        $facts = Read-UiaPathFacts $node
        $driveName = ''
        if ($node.Current.Name -match $drivePattern) { $driveName=$node.Current.Name }
        if (Test-UiaPathCandidate $node.Current.Name $driveName $facts $fixture.Substring(0,3)) { $driveMatches.Add($node) }
      }
      if ($driveMatches.Count -gt 0) { break }
      # Only standard Shell navigation containers are expanded. No type-ahead,
      # global keyboard, clipboard, search box or arbitrary window receives input.
      foreach ($node in $nodes) {
        if ($node.Current.Name -cin @('Desktop','This PC','Computer','桌面','此电脑','计算机')) { Expand-UiaNode $node }
      }
    }
    if ($driveMatches.Count -ne 1) { throw 'UIA_DRIVE_NOT_UNIQUE_OR_NOT_EXPOSED_OPERATOR_REQUIRED' }
    $current = $driveMatches[0]
    $prefix = $fixture.Substring(0,3)
    foreach ($segment in $fixture.Substring(3).Split([char]'\')) {
      Expand-UiaNode $current
      $prefix = Join-Path $prefix $segment
      $childMatches = [Collections.Generic.List[object]]::new()
      foreach ($child in $current.FindAll([Windows.Automation.TreeScope]::Children,$itemCondition)) {
        $facts = Read-UiaPathFacts $child
        if (Test-UiaPathCandidate $child.Current.Name $segment $facts $prefix) { $childMatches.Add($child) }
      }
      if ($childMatches.Count -ne 1) { throw ('UIA_PATH_COMPONENT_NOT_UNIQUE_OR_NOT_EXPOSED:' + $segment) }
      $current = $childMatches[0]
    }
    Assert-UiaElement $current
    $selectionPattern = $null
    if (-not $current.TryGetCurrentPattern([Windows.Automation.SelectionItemPattern]::Pattern,[ref]$selectionPattern)) { throw 'UIA_SELECTION_PATTERN_UNAVAILABLE_NO_CLICK' }
    $selectionPattern.Select()
    Start-Sleep -Milliseconds 150
    Assert-Dialog
  }
  function Get-VerifiedSelection {
  $element = [Windows.Automation.AutomationElement]::FromHandle($hwnd)
  $treeCondition = [Windows.Automation.PropertyCondition]::new([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::Tree)
  $trees = $element.FindAll([Windows.Automation.TreeScope]::Descendants,$treeCondition)
  $selection = [Collections.Generic.List[object]]::new()
  foreach ($tree in $trees) {
    $pattern = $null
    if ($tree.TryGetCurrentPattern([Windows.Automation.SelectionPattern]::Pattern,[ref]$pattern)) {
      foreach ($selected in $pattern.GetCurrentSelection()) { $selection.Add($selected) }
    }
  }
  if ($selection.Count -ne 1) { throw 'DIALOG_SELECTION_NOT_UNIQUE' }
  $selected = $selection[0]
  Assert-UiaElement $selected
  $facts = Read-UiaPathFacts $selected
  $proof = Assert-UiaPathEvidence $facts $fixture $true
  return @{ method='CONSISTENT_RELIABLE_ABSOLUTE_PATHS_ONLY'; absolute_values=$proof.absolute_values; reliable_count=$proof.reliable_count }
  }
  function Get-OwnedDialogButton([int]$Id, [switch]$ForCleanup) {
    Assert-Dialog -ForCleanup:$ForCleanup
    $button = [OwnedFolderWin32]::GetDlgItem($hwnd,$Id)
    [uint32]$buttonOwner = 0
    $null = [OwnedFolderWin32]::GetWindowThreadProcessId($button,[ref]$buttonOwner)
    if ($button -eq [IntPtr]::Zero -or $buttonOwner -ne $coreId -or
      [OwnedFolderWin32]::GetParent($button) -ne $hwnd -or
      [OwnedFolderWin32]::Class($button) -ine 'Button' -or
      -not [OwnedFolderWin32]::IsWindowVisible($button) -or
      -not [OwnedFolderWin32]::IsWindowEnabled($button)) { throw 'OWNED_DIALOG_BUTTON_UNAVAILABLE' }
    return $button
  }
  function Read-OwnedTreeDiagnostic {
    Assert-Dialog
    $script:directChildren=[Collections.Generic.List[object]]::new()
    $script:directTruncated=$false
    $childCallback=[OwnedFolderWin32+EnumCallback]{ param($child,$unused)
      if ($script:directChildren.Count -ge 64) { $script:directTruncated=$true;return $false }
      [uint32]$childPid=0
      $null=[OwnedFolderWin32]::GetWindowThreadProcessId($child,[ref]$childPid)
      $script:directChildren.Add(@{hwnd=$child.ToInt64().ToString();process_id=$childPid
        class_name=[OwnedFolderWin32]::Class($child)
        visible=[OwnedFolderWin32]::IsWindowVisible($child);enabled=[OwnedFolderWin32]::IsWindowEnabled($child)})
      return $true
    }
    $null=[OwnedFolderWin32]::EnumChildWindows($hwnd,$childCallback,[IntPtr]::Zero)
    Assert-Dialog
    $native=Select-UniqueNativeTree @($script:directChildren) $coreId $script:directTruncated
    $nativeHwnd=[IntPtr][long]::Parse($native.hwnd,[Globalization.CultureInfo]::InvariantCulture)
    function Assert-DirectNativeTree {
      Assert-Dialog
      [uint32]$nativePid=0
      $null=[OwnedFolderWin32]::GetWindowThreadProcessId($nativeHwnd,[ref]$nativePid)
      Assert-DirectNativeFacts @{
        process_id=$nativePid;is_child=[OwnedFolderWin32]::IsChild($hwnd,$nativeHwnd)
        class_name=[OwnedFolderWin32]::Class($nativeHwnd)
        visible=[OwnedFolderWin32]::IsWindowVisible($nativeHwnd)
        enabled=[OwnedFolderWin32]::IsWindowEnabled($nativeHwnd)
      } $coreId
    }
    Assert-DirectNativeTree
    $direct=@{native_window=$native;provider_status='NOT_READ';patterns=@{};public_values=@();absolute_candidates=@();selected=@();selection_count=$null;selected_limit=4;selected_truncated=$false;can_authorize_selection=$false}
    $current=@{index=0;status='ELEMENT_UNAVAILABLE'}
    function Read-PublicPatterns($Element) {
      $support=@{};$values=[Collections.Generic.List[object]]::new()
      $info=$Element.Current
      if ($null -eq $info -or $info.ProcessId -ne $coreId) { throw 'UIA_PROVIDER_OWNER_UNCONFIRMED_NO_VALUES' }
      $values.Add((Project-PublicUiaValue 'Name' $info.Name))
      foreach ($provider in @(
        @{source='ValuePattern';id=[Windows.Automation.ValuePattern]::Pattern},
        @{source='LegacyIAccessiblePattern';id=[Windows.Automation.LegacyIAccessiblePattern]::Pattern}
      )) {
        Assert-DirectNativeTree
        try {
          $pattern=$null;$supported=$Element.TryGetCurrentPattern($provider.id,[ref]$pattern)
          $support[$provider.source]=@{supported=$supported}
          if ($supported) { $values.Add((Project-PublicUiaValue $provider.source $pattern.Current.Value)) }
        } catch { $support[$provider.source]=@{supported=$null;error=(Limit-DiagnosticText $_.Exception.Message)} }
      }
      return @{support=$support;values=@($values)}
    }
    try {
      $element=[Windows.Automation.AutomationElement]::FromHandle($nativeHwnd)
      $current=Project-TreeDiagnostic $element 0
      $direct.provider_status='FROM_HANDLE_RETURNED'
      $read=Read-PublicPatterns $element
      $direct.patterns=$read.support;$direct.public_values=$read.values
      $direct.absolute_candidates=@($read.values|Where-Object {$_.absolute_candidate})
      Assert-DirectNativeTree
      $selection=$null;$supported=$element.TryGetCurrentPattern([Windows.Automation.SelectionPattern]::Pattern,[ref]$selection)
      $direct.patterns.SelectionPattern=@{supported=$supported}
      if ($supported) {
        $selected=$selection.GetCurrentSelection();$direct.selection_count=$selected.Count
        $direct.selected_truncated=$selected.Count -gt 4
        $rows=[Collections.Generic.List[object]]::new()
        for ($i=0;$i -lt [Math]::Min($selected.Count,4);$i++) {
          Assert-DirectNativeTree
          try {
            $read=Read-PublicPatterns $selected[$i]
            $rows.Add(@{index=$i;current=(Project-TreeDiagnostic $selected[$i] $i);patterns=$read.support
              public_values=$read.values;absolute_candidates=@($read.values|Where-Object {$_.absolute_candidate});can_authorize_selection=$false})
          } catch { $rows.Add(@{index=$i;status='SELECTED_ELEMENT_UNAVAILABLE';error=(Limit-DiagnosticText $_.Exception.Message)}) }
        }
        $direct.selected=@($rows)
      }
    } catch {
      $direct.provider_status='PROVIDER_UNAVAILABLE_OR_UNCONFIRMED'
      $direct.error=Limit-DiagnosticText $_.Exception.Message
    }
    Assert-DirectNativeTree
    return @{
      schema='researchos.owned-dialog-tree-metadata/1'; diagnostic_only=$true
      dialog_hwnd=$hwnd.ToInt64().ToString(); dialog_owner_pid=$coreId
      tree_source='VERIFIED_NATIVE_SYSTREEVIEW32_FROM_HANDLE'
      tree_count=1; tree_limit=16; captured_count=1;tree_truncated=$false;trees=@($current)
      direct_native_tree=$direct
      win32_children_when_zero=$null
      no_treeitem_navigation=$true; no_ok=$true; no_workspace_authorization=$true
    }
  }
  $result.diagnostic=Read-OwnedTreeDiagnostic
  # Dedicated diagnostic controller: never select/expand a TreeItem or lookup OK.
  # The ordinary catch path can only revalidate and invoke owned IDCANCEL.
  throw 'DIAGNOSTIC_ONLY_TREE_SNAPSHOT_COMPLETE_NO_OK'
} catch {
  $result.reason=$_.Exception.Message
  if ($okAttempted) {
    $result.cleanup.status='OK_OUTCOME_UNKNOWN_NO_FURTHER_CLICK'
  } elseif ($dialogValidated -and $hwnd -ne [IntPtr]::Zero) {
    $result.cleanup.attempted=$true
    try {
      # Failed path proof never permits OK. Cleanup may only use the same owned
      # dialog's normal IDCANCEL, revalidated through the bounded close window.
      $cancel = Get-OwnedDialogButton 2 -ForCleanup
      Assert-Dialog -ForCleanup
      [UIntPtr]$cancelResult = [UIntPtr]::Zero
      $cancelSent = [OwnedFolderWin32]::ClickTimeout($cancel,0x00F5,[IntPtr]::Zero,[IntPtr]::Zero,2,1000,[ref]$cancelResult)
      if ($cancelSent -eq [IntPtr]::Zero) { throw 'IDCANCEL_CLICK_OUTCOME_UNCONFIRMED' }
      $result.cleanup.status='OWNED_IDCANCEL_CLICKED'
      $result.cleanup.hwnd=$hwnd.ToInt64().ToString()
      $result.authorization_state='NO_OK_CLICKED_NO_WORKSPACE_AUTHORIZATION_REQUESTED_BY_RUNNER'
    } catch {
      $result.cleanup.status='OWNERSHIP_OR_CANCEL_UNCONFIRMED_NO_FURTHER_ACTION'
      $result.cleanup.reason=$_.Exception.Message
    }
  } else {
    $result.cleanup.status='OWNERSHIP_UNCONFIRMED_NO_CLICK'
  }
} finally {
  $result.ok_attempted=$okAttempted
  if ($null -ne $process) { $process.Dispose() }
}
$result | ConvertTo-Json -Depth 12 -Compress
if (-not $result.clicked_ok) { exit 2 }
