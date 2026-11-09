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
$result = @{ schema='researchos.owned-native-folder-automation/1'; status='BLOCKED'; clicked_ok=$false }
try {
  if ((Get-FileHash -LiteralPath $ScopePath -Algorithm SHA256).Hash.ToLowerInvariant() -cne $ScopeSHA256) { throw 'SCOPE_PIN_MISMATCH' }
  $scope = Get-Content -LiteralPath $ScopePath -Raw -Encoding UTF8 | ConvertFrom-Json
  if ($scope.status -cne 'ROOT_APPROVED_REAL_RUN' -or $scope.scope_nonce -cne $ScopeNonce) { throw 'SCOPE_NOT_AUTHORIZED' }
  $runRoot = [IO.Path]::GetFullPath($scope.run_root)
  $fixture = [IO.Path]::GetFullPath((Join-Path $runRoot 'workspace'))
  $identityFile = [IO.Path]::GetFullPath($CoreIdentityPath)
  if ($identityFile -ine (Join-Path $runRoot 'receipts\owned-core.json')) { throw 'IDENTITY_PATH_OUTSIDE_SCOPE' }
  $identity = Get-Content -LiteralPath $identityFile -Raw -Encoding UTF8 | ConvertFrom-Json
  if ($identity.scope_nonce -cne $ScopeNonce -or $identity.identity_source -cne 'ROS_DESKTOP_REPORT.ready_to_show') { throw 'CORE_IDENTITY_SOURCE_MISMATCH' }
  $core = $identity.owned_core_identity
  $actionDeadline = [DateTimeOffset]::Parse($identity.action_deadline_utc).UtcDateTime
  $coreId = [int]$core.pid
  if ($coreId -le 0 -or $core.created_ns -cnotmatch '^[0-9]+$' -or $core.image_sha256 -cnotmatch '^[a-f0-9]{64}$') { throw 'CORE_IDENTITY_INVALID' }
  if ($core.image_sha256 -cne $scope.bundle.control_sha256) { throw 'CORE_IMAGE_PIN_MISMATCH' }
  $expectedImage = [IO.Path]::GetFullPath((Join-Path $scope.bundle.root 'apps\desktop\resources\control\researchos-control.exe'))
  $process = [Diagnostics.Process]::GetProcessById($coreId)
  # Retain the process handle throughout selection; PID or HWND alone is insufficient.
  $null = $process.Handle
  function Assert-Core {
    if ([DateTime]::UtcNow -ge $actionDeadline) { throw 'NATIVE_UI_ACTION_DEADLINE_EXPIRED' }
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
  function Assert-Dialog {
    Assert-Core
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
  [UIntPtr]$messageResult = [UIntPtr]::Zero
  # Never send BFFM_SETSELECTIONW/WM_USER pointers across processes. That old
  # candidate is preserved as REJECTED_NOT_RUN. Only real UIAutomation patterns
  # below may navigate/select; no remote memory, injection or fabricated reply.
  function Assert-UiaElement($element) {
    Assert-Dialog
    if ($null -eq $element -or $element.Current.ProcessId -ne $coreId -or -not $element.Current.IsEnabled) { throw 'UIA_ELEMENT_NOT_OWNED_AND_ENABLED' }
  }
  function Get-UiaFullPath($element) {
    foreach ($id in @([Windows.Automation.ValuePattern]::Pattern,[Windows.Automation.LegacyIAccessiblePattern]::Pattern)) {
      $pattern = $null
      if ($element.TryGetCurrentPattern($id,[ref]$pattern)) {
        $value = $pattern.Current.Value
        if ($value -and [IO.Path]::IsPathRooted($value)) { return [IO.Path]::GetFullPath($value) }
      }
    }
    return $null
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
        if ($node.Current.Name -match $drivePattern -or (Get-UiaFullPath $node) -ieq $fixture.Substring(0,3)) { $driveMatches.Add($node) }
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
        if ($child.Current.Name -ieq $segment -or (Get-UiaFullPath $child) -ieq $prefix) { $childMatches.Add($child) }
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
  $verified = $false
  $method = $null
  foreach ($id in @([Windows.Automation.ValuePattern]::Pattern,[Windows.Automation.LegacyIAccessiblePattern]::Pattern)) {
    $pattern = $null
    if ($selected.TryGetCurrentPattern($id,[ref]$pattern)) {
      $value = $pattern.Current.Value
      if ($value -and [IO.Path]::IsPathRooted($value) -and [IO.Path]::GetFullPath($value) -ieq $fixture) { $verified=$true; $method='SELECTED_ITEM_FULL_PATH' }
    }
  }
  $chain = [Collections.Generic.List[string]]::new()
  $node = $selected
  for ($depth=0; $depth -lt 80 -and $null -ne $node; $depth++) {
    if ($node.Current.ControlType -eq [Windows.Automation.ControlType]::TreeItem) { $chain.Add($node.Current.Name) }
    $node = [Windows.Automation.TreeWalker]::ControlViewWalker.GetParent($node)
  }
  if (-not $verified) {
    $parts = $fixture.Substring(3).Split([char]'\')
    if ($chain.Count -ge $parts.Count + 1) {
      $verified = $true
      for ($i=0; $i -lt $parts.Count; $i++) { if ($chain[$i] -ine $parts[$parts.Count-1-$i]) { $verified=$false } }
      $drive = [regex]::Escape($fixture.Substring(0,2))
      if ($chain[$parts.Count] -notmatch ('(^|\()' + $drive + '(\)|\\)?$')) { $verified=$false }
      if ($verified) { $method='EXACT_FILESYSTEM_ANCESTOR_CHAIN' }
    }
  }
  if (-not $verified) { throw 'DIALOG_SELECTION_PATH_UNVERIFIABLE_NO_CLICK' }
  return @{ method=$method; chain=@($chain) }
  }
  Select-FixtureThroughRealTree
  $selectedBefore = Get-VerifiedSelection
  Assert-Dialog
  $ok = [OwnedFolderWin32]::GetDlgItem($hwnd,1)
  [uint32]$buttonOwner = 0
  $null = [OwnedFolderWin32]::GetWindowThreadProcessId($ok,[ref]$buttonOwner)
  if ($ok -eq [IntPtr]::Zero -or $buttonOwner -ne $coreId -or -not [OwnedFolderWin32]::IsWindowEnabled($ok)) { throw 'DIALOG_OK_UNAVAILABLE' }
  $selectedFinal = Get-VerifiedSelection
  Assert-Dialog
  $result.caption=[OwnedFolderWin32]::Text($hwnd)
  $sent = [OwnedFolderWin32]::ClickTimeout($ok,0x00F5,[IntPtr]::Zero,[IntPtr]::Zero,2,1000,[ref]$messageResult)
  if ($sent -eq [IntPtr]::Zero) { throw 'DIALOG_OK_UNCONFIRMED' }
  $result.status='REAL_SHELL_OK_CLICKED'
  $result.clicked_ok=$true
  $result.hwnd=$hwnd.ToInt64().ToString()
  $result.prompt='Select a ResearchOS workspace folder'
  $result.selection_verification=$selectedFinal.method
  $result.selection_chain=$selectedFinal.chain
  $result.fixture_path=$fixture
  $result.owned_core_identity=$core
} catch {
  $result.reason=$_.Exception.Message
} finally {
  if ($null -ne $process) { $process.Dispose() }
}
$result | ConvertTo-Json -Depth 12 -Compress
if (-not $result.clicked_ok) { exit 2 }
