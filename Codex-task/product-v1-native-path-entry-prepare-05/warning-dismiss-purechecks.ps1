$ErrorActionPreference='Stop'
$source=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'choose-owned-folder.ps1') -Raw -Encoding UTF8
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseInput($source,[ref]$tokens,[ref]$errors)
if ($errors.Count) {throw ('HELPER_AST_SYNTAX: '+($errors.Message -join '; '))}
foreach ($name in @('Assert-WarningDismissSelector','Select-UniqueWarningDismissButton')) {
  $defs=@($ast.FindAll({param($node)$node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -ceq $name},$true))
  if ($defs.Count -ne 1) {throw 'NEW_PREDICATE_NOT_UNIQUE'}
  . ([ScriptBlock]::Create($defs[0].Extent.Text))
}
$passed=[Collections.Generic.List[string]]::new()
function Expect-Code([string]$Name,[string]$Expected,[scriptblock]$Action) {
  $code=$null;try {& $Action} catch {$code=$_.Exception.Message}
  if ($code -cne $Expected) {throw ('WRONG_CLASSIFICATION:'+ $Name+':'+$code)}
  $passed.Add($Name)
}
$scope=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'scope.template.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$selector=$scope.native_picker.validation_warning.dismiss_selector
Assert-WarningDismissSelector $selector
$passed.Add('scope_expected2_actual03_evidence_pin')
$bad=$selector.PSObject.Copy();$bad.expected_control_id=1
Expect-Code 'old_id1_scope_rejected' 'ACTUAL03_WARNING_DISMISS_SELECTOR_PIN_REQUIRED' {Assert-WarningDismissSelector $bad}
$bad=$selector.PSObject.Copy();$bad.evidence_sha256='a'*64
Expect-Code 'wrong_evidence_sha_rejected' 'ACTUAL03_WARNING_DISMISS_SELECTOR_PIN_REQUIRED' {Assert-WarningDismissSelector $bad}
$bad=$selector.PSObject.Copy();$bad.evidence_event='WARNING_DISMISS_CHILD_METADATA'
Expect-Code 'historical_event_name_must_not_be_renamed' 'ACTUAL03_WARNING_DISMISS_SELECTOR_PIN_REQUIRED' {Assert-WarningDismissSelector $bad}
$evidence=$selector.evidence_path
$before=(Get-FileHash -LiteralPath $evidence -Algorithm SHA256).Hash.ToLowerInvariant()
if ($before -cne $selector.evidence_sha256) {throw 'ACTUAL03_FIXTURE_PIN'}
$wrapper=Get-Content -LiteralPath $evidence -Raw -Encoding UTF8 | ConvertFrom-Json
$reply=$wrapper.stdout | ConvertFrom-Json
$event=@($reply.history | Where-Object {$_.sequence -eq 36 -and $_.event -ceq 'WARNING_IDOK_CHILD_METADATA'})
if ($wrapper.exit -ne 2 -or $reply.status -cne 'BLOCKED' -or $event.Count -ne 1 -or $event[0].evidence.truncated) {throw 'ACTUAL03_EVIDENCE'}
$rows=@($event[0].evidence.rows);$dialog=[long]$event[0].evidence.dialog;$owner=[int]$rows[0].process_id
if ($rows.Count -ne 3 -or (Select-UniqueWarningDismissButton $rows $owner $dialog $false 0 2).control_id -ne 2) {throw 'ACTUAL03_SOLE_BUTTON2'}
$passed.Add('actual03_sole_button2_static20_static65535')
$button=@{hwnd=31;process_id=42;parent=7;root_dialog=7;is_child=$true;control_id=2;class_name='Button';visible=$true;enabled=$true}
$bad=@{}+$button;$bad.control_id=1
Expect-Code 'sole_button_id1_no_fallback' 'WARNING_DISMISS_CONTROL_ID_OR_STATE_UNCONFIRMED_NO_POST' {Select-UniqueWarningDismissButton @($bad) 42 7 $false 0 2}
$other=@{}+$button;$other.hwnd=32;$other.control_id=1
Expect-Code 'extra_button_other_id_rejected' 'WARNING_DISMISS_BUTTON_NOT_UNIQUE_NO_POST' {Select-UniqueWarningDismissButton @($button,$other) 42 7 $false 0 2}
$other.visible=$false
Expect-Code 'hidden_extra_button_still_rejected' 'WARNING_DISMISS_BUTTON_NOT_UNIQUE_NO_POST' {Select-UniqueWarningDismissButton @($button,$other) 42 7 $false 0 2}
Expect-Code 'duplicate_button2_rejected' 'WARNING_DISMISS_BUTTON_NOT_UNIQUE_NO_POST' {Select-UniqueWarningDismissButton @($button,$button) 42 7 $false 0 2}
Expect-Code 'positive_direct_lookup_must_agree' 'WARNING_DISMISS_LOOKUP_CHANGED_NO_POST' {Select-UniqueWarningDismissButton @($button) 42 7 $false 32 2}
Expect-Code 'truncated_metadata_rejected' 'WARNING_CHILD_ENUMERATION_TRUNCATED_NO_POST' {Select-UniqueWarningDismissButton @($button) 42 7 $true 0 2}
$bad=@{}+$button;$bad.enabled=$false
Expect-Code 'disabled_sole_button2_rejected' 'WARNING_DISMISS_CONTROL_ID_OR_STATE_UNCONFIRMED_NO_POST' {Select-UniqueWarningDismissButton @($bad) 42 7 $false 0 2}
Expect-Code 'unscoped_expected_id1_rejected' 'WARNING_DISMISS_EXPECTED_CONTROL_ID_MUST_BE_PINNED_2' {Select-UniqueWarningDismissButton @($button) 42 7 $false 0 1}
if ((Get-FileHash -LiteralPath $evidence -Algorithm SHA256).Hash.ToLowerInvariant() -cne $before) {throw 'ACTUAL03_CHANGED'}
@{schema='researchos.native-path-entry-dismiss05-pure/1';helper_ast='PASS';pure_cases=$passed.ToArray()
  actual03_record_read_only=$true;actual03_runtime_outcome='FAILED_UNCHANGED';inherited_pure_cases_not_rerun=66
  helper_entrypoint=0;dynamic_csharp_compile=0;win32_calls=0;app=0;cli=0;task=0;model=0} | ConvertTo-Json -Depth 5
