$ErrorActionPreference='Stop'
$source=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'choose-owned-folder.ps1') -Raw -Encoding UTF8
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseInput($source,[ref]$tokens,[ref]$errors)
if ($errors.Count) {throw ('HELPER_AST_SYNTAX: '+($errors.Message -join '; '))}
foreach ($name in @('Assert-WindowHandleOwner','Select-UniqueWarningIdOk')) {
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
$owner=@{hwnd=31;is_window=$true;thread_id=101;process_id=42}
Assert-WindowHandleOwner $owner 42
$passed.Add('actual_owned_handle')
$bad=@{}+$owner;$bad.hwnd=0;$bad.is_window=$false;$bad.thread_id=0;$bad.process_id=0
Expect-Code 'zero_is_not_foreign' 'WINDOW_HANDLE_ZERO_NO_TARGET' {Assert-WindowHandleOwner $bad 42}
$bad=@{}+$owner;$bad.is_window=$false
Expect-Code 'invalid_is_not_foreign' 'WINDOW_HANDLE_INVALID_NO_TARGET' {Assert-WindowHandleOwner $bad 42}
$bad=@{}+$owner;$bad.thread_id=0;$bad.process_id=0
Expect-Code 'unavailable_pid_is_not_foreign' 'WINDOW_THREAD_PID_UNAVAILABLE_NO_TARGET' {Assert-WindowHandleOwner $bad 42}
$bad=@{}+$owner;$bad.process_id=43
Expect-Code 'confirmed_foreign_pid' 'FOREIGN_WINDOW_PID' {Assert-WindowHandleOwner $bad 42}
$button=@{hwnd=31;process_id=42;parent=7;root_dialog=7;is_child=$true;control_id=1;class_name='Button';visible=$true;enabled=$true}
if ((Select-UniqueWarningIdOk @($button) 42 7 $false 31).hwnd -ne 31) {throw 'DIRECT_IDOK'}
$passed.Add('unique_actual_direct_idok')
$nested=@{}+$button;$nested.parent=9
if ((Select-UniqueWarningIdOk @($nested) 42 7 $false 0).hwnd -ne 31) {throw 'NESTED_IDOK'}
$passed.Add('unique_actual_nested_idok_with_null_direct_lookup')
Expect-Code 'no_idok' 'WARNING_IDOK_NOT_UNIQUE_NO_POST' {Select-UniqueWarningIdOk @() 42 7 $false 0}
Expect-Code 'duplicate_idok' 'WARNING_IDOK_NOT_UNIQUE_NO_POST' {Select-UniqueWarningIdOk @($button,$nested) 42 7 $false 0}
$bad=@{}+$button;$bad.class_name='Static'
Expect-Code 'id1_wrong_class' 'WARNING_IDOK_CLASS_OR_STATE_UNCONFIRMED_NO_POST' {Select-UniqueWarningIdOk @($bad) 42 7 $false 0}
$bad=@{}+$button;$bad.control_id=2
Expect-Code 'button_wrong_control_id' 'WARNING_IDOK_NOT_UNIQUE_NO_POST' {Select-UniqueWarningIdOk @($bad) 42 7 $false 0}
$bad=@{}+$button;$bad.process_id=43
Expect-Code 'foreign_candidate' 'WARNING_CHILD_OWNERSHIP_OR_RELATION_UNCONFIRMED_NO_POST' {Select-UniqueWarningIdOk @($bad) 42 7 $false 0}
$bad=@{}+$button;$bad.is_child=$false
Expect-Code 'outside_warning_candidate' 'WARNING_CHILD_OWNERSHIP_OR_RELATION_UNCONFIRMED_NO_POST' {Select-UniqueWarningIdOk @($bad) 42 7 $false 0}
$bad=@{}+$button;$bad.enabled=$false
Expect-Code 'disabled_idok' 'WARNING_IDOK_CLASS_OR_STATE_UNCONFIRMED_NO_POST' {Select-UniqueWarningIdOk @($bad) 42 7 $false 0}
$bad=@{}+$button;$bad.visible=$false
Expect-Code 'hidden_idok' 'WARNING_IDOK_CLASS_OR_STATE_UNCONFIRMED_NO_POST' {Select-UniqueWarningIdOk @($bad) 42 7 $false 0}
Expect-Code 'truncated_enumeration' 'WARNING_CHILD_ENUMERATION_TRUNCATED_NO_POST' {Select-UniqueWarningIdOk @($button) 42 7 $true 0}
Expect-Code 'direct_lookup_changed' 'WARNING_IDOK_LOOKUP_CHANGED_NO_POST' {Select-UniqueWarningIdOk @($button) 42 7 $false 32}
@{schema='researchos.native-path-entry-warning04-pure/1';helper_ast='PASS';pure_cases=$passed.ToArray()
  inherited_pure_cases_not_rerun=49;helper_entrypoint=0;dynamic_csharp_compile=0;uia=0;win32_calls=0;app=0;cli=0;task=0;model=0} |
  ConvertTo-Json -Depth 5
