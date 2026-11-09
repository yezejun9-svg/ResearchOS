$ErrorActionPreference='Stop'
$tokens=$null;$errors=$null
$source=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'choose-owned-folder.ps1') -Raw -Encoding UTF8
$ast=[Management.Automation.Language.Parser]::ParseInput($source,[ref]$tokens,[ref]$errors)
if ($errors.Count) { throw 'HELPER_SYNTAX' }
foreach ($name in @('Select-UniqueNativeTree','Assert-DirectNativeFacts','Project-PublicUiaValue')) {
  $defs=@($ast.FindAll({param($node)$node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -ceq $name},$true))
  if ($defs.Count -ne 1) { throw 'PURE_FUNCTION_NOT_UNIQUE' }
  . ([ScriptBlock]::Create($defs[0].Extent.Text))
}
function Reject([ScriptBlock]$Action) {
  $caught=$false
  try {$null=& $Action} catch {$caught=$true}
  if (-not $caught) {throw 'UNSAFE_ACCEPTANCE'}
}
$passed=0
$one=@{hwnd='123';process_id=42;class_name='SysTreeView32';visible=$true;enabled=$true}
if ((Select-UniqueNativeTree @($one) 42 $false).hwnd -cne '123') {throw 'UNIQUE_TREE'};$passed++
Reject {Select-UniqueNativeTree @() 42 $false};$passed++
Reject {Select-UniqueNativeTree @($one,$one) 42 $false};$passed++
Reject {Select-UniqueNativeTree @($one) 42 $true};$passed++
$facts=@{process_id=42;is_child=$true;class_name='SysTreeView32';visible=$true;enabled=$true}
Assert-DirectNativeFacts $facts 42;$passed++
$changed=$facts.Clone();$changed.process_id=99
Reject {Assert-DirectNativeFacts $changed 42};$passed++
$changed=$facts.Clone();$changed.is_child=$false
Reject {Assert-DirectNativeFacts $changed 42};$passed++
$value=Project-PublicUiaValue 'LegacyIAccessiblePattern' 'C:\owned\workspace'
if (-not $value.absolute_candidate -or $value.selection_authority -ne $false) {throw 'ABSOLUTE_NOT_AUTHORITY'};$passed++
$value=Project-PublicUiaValue 'ValuePattern' ('C:\'+('x'*1200))
if (-not $value.truncated -or $value.value.Length -gt 1024) {throw 'VALUE_BOUND'};$passed++
if ($source.Contains('Get-OwnedDialogButton 1') -or $source.Contains('$result.clicked_ok=$true') -or $source.Contains('$okAttempted=$true')) {throw 'OK_PATH'};$passed++
if (-not $source.Contains('AutomationElement]::FromHandle($nativeHwnd)') -or
  -not $source.Contains('EnumChildWindows($hwnd,$childCallback') -or
  -not $source.Contains('$cancel = Get-OwnedDialogButton 2 -ForCleanup')) {throw 'DIRECT_SCOPE_OR_CANCEL'};$passed++
@{status='DIRECT_NATIVE_PURE_PASS';passed=$passed;helper_entrypoint=0;add_type=0;uia=0;gui=0;model=0}|ConvertTo-Json -Compress
