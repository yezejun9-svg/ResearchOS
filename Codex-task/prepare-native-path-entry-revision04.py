from pathlib import Path
import json,hashlib,difflib

cwd=Path(__file__).resolve().parent
old=cwd/'product-v1-native-path-entry-prepare-03'
new=cwd/'product-v1-native-path-entry-prepare-04'
new.mkdir()
for name in ['real-electron-flow.mjs','choose-owned-folder.ps1','scope.template.json','README.md']:
    (new/name).write_bytes((old/name).read_bytes())
helper=(new/'choose-owned-folder.ps1').read_text(encoding='utf-8')
marker='function Assert-DialogThreadFacts('
pure=r'''function Assert-WindowHandleOwner($Identity,[int]$ExpectedPid) {
  if ($Identity.hwnd -eq 0) {throw 'WINDOW_HANDLE_ZERO_NO_TARGET'}
  if ($Identity.is_window -ne $true) {throw 'WINDOW_HANDLE_INVALID_NO_TARGET'}
  if ($Identity.thread_id -le 0 -or $Identity.process_id -le 0) {throw 'WINDOW_THREAD_PID_UNAVAILABLE_NO_TARGET'}
  if ($Identity.process_id -ne $ExpectedPid) {throw 'FOREIGN_WINDOW_PID'}
}
function Select-UniqueWarningIdOk($Rows,[int]$ExpectedPid,[long]$WarningHwnd,[bool]$Truncated,[long]$DirectLookupHwnd) {
  if ($Truncated) {throw 'WARNING_CHILD_ENUMERATION_TRUNCATED_NO_POST'}
  foreach ($row in $Rows) {
    if ($row.hwnd -le 0 -or $row.process_id -ne $ExpectedPid -or $row.is_child -ne $true -or
      $row.root_dialog -ne $WarningHwnd) {throw 'WARNING_CHILD_OWNERSHIP_OR_RELATION_UNCONFIRMED_NO_POST'}
  }
  # Control ID, never localized text, identifies IDOK. Even an invisible or
  # non-Button duplicate ID 1 makes this set ambiguous and must block.
  $matches=@($Rows | Where-Object {$_.control_id -eq 1})
  if ($matches.Count -ne 1) {throw 'WARNING_IDOK_NOT_UNIQUE_NO_POST'}
  $candidate=$matches[0]
  if ($candidate.class_name -cne 'Button' -or $candidate.visible -ne $true -or $candidate.enabled -ne $true) {
    throw 'WARNING_IDOK_CLASS_OR_STATE_UNCONFIRMED_NO_POST'
  }
  if ($DirectLookupHwnd -ne 0 -and $candidate.hwnd -ne $DirectLookupHwnd) {throw 'WARNING_IDOK_LOOKUP_CHANGED_NO_POST'}
  return $candidate
}
'''
assert helper.count(marker)==1
helper=helper.replace(marker,pure+marker)
marker='  [DllImport("user32.dll")] public static extern IntPtr GetDlgItem(IntPtr hwnd,int id);'
assert helper.count(marker)==1
helper=helper.replace(marker,marker+'\n  [DllImport("user32.dll")] public static extern int GetDlgCtrlID(IntPtr hwnd);')
a=helper.index('  function Facts([IntPtr]$Handle) {')
b=helper.index('  function Read-OwnedText(',a)
helper=helper[:a]+r'''  function Facts([IntPtr]$Handle) {
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
'''+helper[b:]
needle='''  function ChildFacts([IntPtr]$Parent) {
    $null=Facts $Parent
    $script:children=[Collections.Generic.List[object]]::new();$script:truncated=$false
    $script:childEnumError=$null'''
replacement='''  function ChildFacts([IntPtr]$Parent) {
    $script:children=[Collections.Generic.List[object]]::new();$script:truncated=$false
    $script:childEnumError=$null
    $null=Facts $Parent'''
assert helper.count(needle)==1
helper=helper.replace(needle,replacement)
needle='        $script:children.Add((Facts $child));return $true'
assert helper.count(needle)==1
helper=helper.replace(needle,'''        $row=Facts $child
        $row.root_dialog=$Parent.ToInt64()
        $row.is_child=[OwnedPathWin32]::IsChild($Parent,$child)
        $row.control_id=$null
        # GetDlgCtrlID is defined for child controls, not top-level windows.
        if ($row.is_child) {$row.control_id=[OwnedPathWin32]::GetDlgCtrlID($child)}
        $script:children.Add($row);return $true''')
marker='  function Post-OwnedButton('
discover=r'''  function Get-OwnedWarningIdOk([IntPtr]$Warning) {
    Assert-Warning $Warning
    $direct=[OwnedPathWin32]::GetDlgItem($Warning,1)
    Record 'WARNING_IDOK_DIRECT_LOOKUP' @{dialog=$Warning.ToInt64();control_id=1;hwnd=$direct.ToInt64();is_zero=($direct -eq [IntPtr]::Zero)}
    if ($direct -ne [IntPtr]::Zero) {
      $lookup=Facts $direct
      $lookup.is_child=[OwnedPathWin32]::IsChild($Warning,$direct)
      $lookup.control_id=$null
      if ($lookup.is_child) {$lookup.control_id=[OwnedPathWin32]::GetDlgCtrlID($direct)}
      Record 'WARNING_IDOK_DIRECT_LOOKUP_FACTS' $lookup
      if (-not $lookup.is_child -or $lookup.control_id -ne 1 -or $lookup.class_name -cne 'Button' -or
        -not $lookup.visible -or -not $lookup.enabled) {throw 'WARNING_DIRECT_IDOK_LOOKUP_INVALID_NO_POST'}
    }
    $rows=@()
    try {$rows=@(ChildFacts $Warning)}
    catch {
      Record 'WARNING_IDOK_CHILD_METADATA' @{dialog=$Warning.ToInt64();limit=128;truncated=$script:truncated
        rows=$script:children.ToArray();enumeration_error=$_.Exception.Message;window_text_read=$false}
      throw
    }
    Record 'WARNING_IDOK_CHILD_METADATA' @{dialog=$Warning.ToInt64();limit=128;truncated=$script:truncated
      rows=$rows;enumeration_error=$null;window_text_read=$false}
    $candidate=Select-UniqueWarningIdOk $rows $coreId $Warning.ToInt64() $script:truncated $direct.ToInt64()
    return [IntPtr]$candidate.hwnd
  }
'''
assert helper.count(marker)==1
helper=helper.replace(marker,discover+marker)
needle='''    $button=[OwnedPathWin32]::GetDlgItem($Dialog,$Id);$row=Facts $button
    if ($row.parent -ne $Dialog.ToInt64() -or $row.class_name -cne 'Button' -or -not $row.visible -or -not $row.enabled) {throw 'OWNED_BUTTON_IDENTITY_OR_STATE'}'''
assert helper.count(needle)==1
helper=helper.replace(needle,'''    if ($Warning) {
      if ($Id -ne 1 -or $Purpose -cne 'WARNING_DISMISS') {throw 'WARNING_ONLY_IDOK_DISMISS_ALLOWED'}
      $button=Get-OwnedWarningIdOk $Dialog
    } else {
      $button=[OwnedPathWin32]::GetDlgItem($Dialog,$Id);$row=Facts $button
      if ($row.parent -ne $Dialog.ToInt64() -or $row.class_name -cne 'Button' -or -not $row.visible -or -not $row.enabled) {throw 'OWNED_BUTTON_IDENTITY_OR_STATE'}
    }''')
needle='''    $fresh=[OwnedPathWin32]::GetDlgItem($Dialog,$Id);$now=Facts $fresh
    if ($fresh -ne $button -or $now.parent -ne $Dialog.ToInt64() -or $now.class_name -cne 'Button' -or
      -not $now.visible -or -not $now.enabled) {throw 'BUTTON_CHANGED_IMMEDIATELY_BEFORE_QUEUE'}'''
assert helper.count(needle)==1
helper=helper.replace(needle,'''    if ($Warning) {
      $fresh=Get-OwnedWarningIdOk $Dialog
      if ($fresh -ne $button) {throw 'WARNING_IDOK_CHANGED_IMMEDIATELY_BEFORE_QUEUE'}
    } else {
      $fresh=[OwnedPathWin32]::GetDlgItem($Dialog,$Id);$now=Facts $fresh
      if ($fresh -ne $button -or $now.parent -ne $Dialog.ToInt64() -or $now.class_name -cne 'Button' -or
        -not $now.visible -or -not $now.enabled) {throw 'BUTTON_CHANGED_IMMEDIATELY_BEFORE_QUEUE'}
    }''')
(new/'choose-owned-folder.ps1').write_text(helper,encoding='utf-8',newline='\n')
(new/'helper.diff').write_text(''.join(difflib.unified_diff((old/'choose-owned-folder.ps1').read_text(encoding='utf-8').splitlines(True),helper.splitlines(True),fromfile='freeze03/choose-owned-folder.ps1',tofile='revision04/choose-owned-folder.ps1')),encoding='utf-8')
scope=json.loads((new/'scope.template.json').read_text(encoding='utf-8'))
scope['harness']['folder_helper_sha256']=hashlib.sha256((new/'choose-owned-folder.ps1').read_bytes()).hexdigest()
scope['native_picker']['warning_idok']='EXACT_VERIFIED_WARNING_ONLY_BOUNDED_UNIQUE_SAME_CORE_DESCENDANT_BUTTON_CONTROL_ID_1_NO_LABEL_FALLBACK'
(new/'scope.template.json').write_text(json.dumps(scope,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
readme=(new/'README.md').read_text(encoding='utf-8').replace('# Native path entry candidate 03 — NOT_RUN','# Native path entry candidate 04 — NOT_RUN',1)
readme+='''
Revision 04 is limited to identity diagnostics and the exact verified MB_OK
warning's real IDOK control. actual02 remains failed and unchanged: it proved
invalid-path validation and the owned fixed warning, then failed before the
warning button queue intent. It did not record GetDlgItem's returned HWND, so
neither NULL, nesting nor a true foreign window is established as the cause.

Facts now classifies zero HWND, invalid HWND, unavailable TID/PID, and confirmed
foreign PID separately, recording numeric identity before failure. No foreign
window text/class is read. For an already exact caption/text/owner-verified
warning only, the helper records GetDlgItem(warning,1), then bounded (128)
same-Core child/descendant metadata. IsChild is checked before GetDlgCtrlID;
only a unique real control ID 1, class Button, visible/enabled candidate is
accepted. A nonzero direct lookup must also agree with that actual candidate.
Its parent may be a container inside the same warning. Missing, duplicate,
truncated, wrong-ID/class/state, foreign, stale or changed controls block.

The warning candidate is rediscovered twice with identical HWND, and its exact
warning, thread-active/focus and final deadline checks remain. Only one standard
BM_CLICK is posted; warning disappearance and original chooser recovery still
must prove dismissal. Chooser OK/Cancel retain their strict direct-parent ID
guards. No label guessing, arbitrary button, WM_COMMAND, activation, keyboard,
remote memory, new COM or PIDL/authority changes are introduced. Runner is
byte-exact to frozen03. Only new selector/identity pure cases and helper AST
syntax are checked; all 49 prior pure cases are inherited, not rerun.

Microsoft primary sources support the bounded candidate, not an assumption
about MessageBox internals:
https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getdlgitem
https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-enumchildwindows
https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getdlgctrlid
https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-ischild
https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-messageboxw

GetDlgItem failure is NULL; its documentation does not prove actual02's cause.
EnumChildWindows includes descendants. GetDlgCtrlID applies to known child
windows. MB_OK has an OK result IDOK=1, but internal HWND hierarchy/class/ID must
still be verified from actual bounded controls. Revision04 runtime is NOT_RUN.
'''
(new/'README.md').write_text(readme,encoding='utf-8')
print(json.dumps({'status':'REVISION04_SOURCE_PREPARED_NOT_RUN','path':str(new),'harness':scope['harness']}))
