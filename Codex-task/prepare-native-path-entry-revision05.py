from pathlib import Path
import json,hashlib,difflib

cwd=Path(__file__).resolve().parent
old=cwd/'product-v1-native-path-entry-prepare-04'
new=cwd/'product-v1-native-path-entry-prepare-05'
new.mkdir()
for name in ['real-electron-flow.mjs','choose-owned-folder.ps1','scope.template.json','README.md']:
    (new/name).write_bytes((old/name).read_bytes())
evidence=cwd/'product-v1-native-path-entry-中文-run-03/receipts/native-folder-automation.json'
evidence_sha='392cd6f17926114f890b74dc28952dc1696d4b20a3444dfd2821b52ddb826423'
assert hashlib.sha256(evidence.read_bytes()).hexdigest()==evidence_sha
selector={'expected_control_id':2,'expected_button_count':1,'basis':'ACTUAL03_OBSERVED_SINGLE_BUTTON_CONTROL_ID_2',
 'message_box_result_is_control_id':False,'evidence_path':str(evidence),'evidence_sha256':evidence_sha,
 'evidence_event':'WARNING_IDOK_CHILD_METADATA','evidence_event_sequence':36}
helper=(new/'choose-owned-folder.ps1').read_text(encoding='utf-8')
helper=helper.replace('Select-UniqueWarningIdOk','Select-UniqueWarningDismissButton').replace('Get-OwnedWarningIdOk','Get-OwnedWarningDismissButton')
a=helper.index('function Select-UniqueWarningDismissButton(')
b=helper.index('function Assert-DialogThreadFacts(',a)
helper=helper[:a]+r'''function Assert-WarningDismissSelector($Selector) {
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
'''+helper[b:]
marker="  $runRoot=[IO.Path]::GetFullPath($scope.run_root)"
assert helper.count(marker)==1
helper=helper.replace(marker,"""  $warningDismissSelector=$scope.native_picker.validation_warning.dismiss_selector
  Assert-WarningDismissSelector $warningDismissSelector
  Require ((Get-FileHash -LiteralPath $warningDismissSelector.evidence_path -Algorithm SHA256).Hash.ToLowerInvariant() -ceq $warningDismissSelector.evidence_sha256) 'ACTUAL03_WARNING_SELECTOR_EVIDENCE_FILE_PIN'
  $warningControlId=[int]$warningDismissSelector.expected_control_id
"""+marker)
helper=helper.replace('$direct=[OwnedPathWin32]::GetDlgItem($Warning,1)','$direct=[OwnedPathWin32]::GetDlgItem($Warning,$warningControlId)')
helper=helper.replace("'WARNING_IDOK_","'WARNING_DISMISS_").replace("'WARNING_DIRECT_IDOK_","'WARNING_DIRECT_DISMISS_")
helper=helper.replace("$Selector.evidence_event -cne 'WARNING_DISMISS_CHILD_METADATA'", "$Selector.evidence_event -cne 'WARNING_IDOK_CHILD_METADATA'")
helper=helper.replace('control_id=1;hwnd=$direct.ToInt64()','control_id=$warningControlId;hwnd=$direct.ToInt64()')
helper=helper.replace('$lookup.control_id -ne 1','$lookup.control_id -ne $warningControlId')
helper=helper.replace('$script:truncated $direct.ToInt64()','$script:truncated $direct.ToInt64() $warningControlId')
helper=helper.replace("if ($Id -ne 1 -or $Purpose -cne 'WARNING_DISMISS') {throw 'WARNING_ONLY_IDOK_DISMISS_ALLOWED'}", "if ($Id -ne $warningControlId -or $Purpose -cne 'WARNING_DISMISS') {throw 'WARNING_ONLY_PINNED_DISMISS_CONTROL_ALLOWED'}")
helper=helper.replace("Post-OwnedButton $warning 1 'WARNING_DISMISS' -Warning", "Post-OwnedButton $warning $warningControlId 'WARNING_DISMISS' -Warning")
(new/'choose-owned-folder.ps1').write_text(helper,encoding='utf-8',newline='\n')
runner=(new/'real-electron-flow.mjs').read_text(encoding='utf-8')
marker='function requirePathEntryScope(scope) {'
gate=r'''function requireWarningDismissSelector(scope) {
  const selector = scope?.native_picker?.validation_warning?.dismiss_selector;
  requireThat(selector?.expected_control_id === 2 && selector.expected_button_count === 1 &&
    selector.basis === 'ACTUAL03_OBSERVED_SINGLE_BUTTON_CONTROL_ID_2' && selector.message_box_result_is_control_id === false &&
    selector.evidence_event === 'WARNING_IDOK_CHILD_METADATA' && selector.evidence_event_sequence === 36 &&
    selector.evidence_sha256 === '392cd6f17926114f890b74dc28952dc1696d4b20a3444dfd2821b52ddb826423' &&
    folded(selector.evidence_path || '') === folded('C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-native-path-entry-中文-run-03/receipts/native-folder-automation.json'),
    'ACTUAL03_WARNING_DISMISS_SELECTOR_PIN_REQUIRED');
}

'''
assert runner.count(marker)==1
runner=runner.replace(marker,gate+marker+'\n  requireWarningDismissSelector(scope);')
marker='  requirePathEntryScope(scope);'
assert runner.count(marker)==1
runner=runner.replace(marker,marker+"\n  pin(scope.native_picker.validation_warning.dismiss_selector.evidence_path, scope.native_picker.validation_warning.dismiss_selector.evidence_sha256);")
(new/'real-electron-flow.mjs').write_text(runner,encoding='utf-8',newline='\n')
for name in ['choose-owned-folder.ps1','real-electron-flow.mjs']:
    (new/('helper.diff' if name.endswith('.ps1') else 'runner.diff')).write_text(''.join(difflib.unified_diff((old/name).read_text(encoding='utf-8').splitlines(True),(new/name).read_text(encoding='utf-8').splitlines(True),fromfile='freeze04/'+name,tofile='revision05/'+name)),encoding='utf-8')
scope=json.loads((new/'scope.template.json').read_text(encoding='utf-8'))
scope['harness']={'runner_sha256':hashlib.sha256((new/'real-electron-flow.mjs').read_bytes()).hexdigest(),
 'folder_helper_sha256':hashlib.sha256((new/'choose-owned-folder.ps1').read_bytes()).hexdigest()}
scope['native_picker']['validation_warning']['dismiss_selector']=selector
scope['native_picker']['warning_idok']='PINNED_MB_OK_WARNING_DISMISS_SINGLE_ACTUAL_BUTTON_CONTROL_ID_2_NOT_MESSAGEBOX_RETURN_IDOK'
(new/'scope.template.json').write_text(json.dumps(scope,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
readme=(new/'README.md').read_text(encoding='utf-8').replace('# Native path entry candidate 04 — NOT_RUN','# Native path entry candidate 05 — NOT_RUN',1)
readme+='''
Revision 05 supersedes the incorrect warning child-ID1 assumption in 04. The
actual03 wrapper is pinned as selector evidence (SHA392cd6f17926114f890b74dc28952dc1696d4b20a3444dfd2821b52ddb826423),
event WARNING_IDOK_CHILD_METADATA sequence36. It proves exactly one actual
visible/enabled same-Core child Button with control ID2; the other rows are
Static20/65535. The preceding ID1 GetDlgItem lookup was NULL. Actual03 remains
failed and unchanged. MessageBox return IDOK=1 is not its child-control ID.

Only this fixed production-source-pinned MB_OK warning may use the scoped
dismiss selector: expected_control_id=2, expected_button_count=1, basis
ACTUAL03_OBSERVED_SINGLE_BUTTON_CONTROL_ID_2, and the exact evidence path/hash/
event/sequence. Helper and Node enforce the same scope gate and re-hash the
evidence file. Selection counts every actual class Button; exactly one must
exist and have ID2 and be visible/enabled. Extra Button controls (even hidden,
disabled or another ID) block. No ID1, arbitrary-ID or label fallback exists.
Positive direct lookup must agree. Same Core, exact warning text/caption and
GW_OWNER, IsChild, bounded metadata, two rediscoveries, active/focus, final
deadline, one BM_CLICK and observed warning disappearance/chooser recovery are
unchanged. Chooser OK/Cancel still use their original strict direct IDs.

The new scope must include the evidence file as an explicit Root outer input
with its exact SHA. It is historical metadata only, never a reused HWND, path
authorization, selectionRef, project success, or model result. Only new selector
and scope-pin predicates plus helper AST/Node syntax are checked. The 66 prior
pure cases are inherited, not rerun. Revision05 runtime is NOT_RUN.
'''
(new/'README.md').write_text(readme,encoding='utf-8')
print(json.dumps({'status':'REVISION05_SOURCE_PREPARED_NOT_RUN','path':str(new),'harness':scope['harness'],'dismiss_selector':selector},ensure_ascii=True))
