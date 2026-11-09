$ErrorActionPreference='Stop'
$source=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'choose-owned-folder.ps1') -Raw -Encoding UTF8
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseInput($source,[ref]$tokens,[ref]$errors)
if ($errors.Count) {throw ('HELPER_AST_SYNTAX: '+($errors.Message -join '; '))}
# Extract new pure predicates only. Never execute the helper body/Add-Type/API.
foreach ($name in @('Select-UniqueEdit','Assert-ExactText')) {
  $defs=@($ast.FindAll({param($node)$node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -ceq $name},$true))
  if ($defs.Count -ne 1) {throw 'PURE_FUNCTION_NOT_UNIQUE'}
  . ([ScriptBlock]::Create($defs[0].Extent.Text))
}
$passed=[Collections.Generic.List[string]]::new()
function Expect-Failure([string]$Name,[scriptblock]$Action) {
  $failed=$false;try {& $Action} catch {$failed=$true}
  if (-not $failed) {throw ('EXPECTED_FAILURE:'+ $Name)}
  $passed.Add($Name)
}
$edit=@{hwnd=99;process_id=42;parent=7;class_name='Edit';visible=$true;enabled=$true}
if ((Select-UniqueEdit @($edit) 42 7 $false).hwnd -ne 99) {throw 'DIRECT_EDIT'}
$passed.Add('unique_direct_owned_edit')
Expect-Failure 'duplicate_edit' {Select-UniqueEdit @($edit,$edit) 42 7 $false}
Expect-Failure 'foreign_pid' {Select-UniqueEdit @($edit) 43 7 $false}
Expect-Failure 'wrong_parent' {Select-UniqueEdit @($edit) 42 8 $false}
Expect-Failure 'truncated_enumeration' {Select-UniqueEdit @($edit) 42 7 $true}
$disabled=@{}+$edit;$disabled.enabled=$false
Expect-Failure 'disabled_edit' {Select-UniqueEdit @($disabled) 42 7 $false}
Assert-ExactText 'C:\owned\workspace' 'C:\owned\workspace' 18 4096
$passed.Add('exact_readback')
Expect-Failure 'contradictory_text' {Assert-ExactText 'C:\other' 'C:\owned' 8 4096}
Expect-Failure 'truncated_readback' {Assert-ExactText 'abc' 'abc' 3 4}
@{schema='researchos.native-path-entry-pure/1';helper_ast='PASS';pure_cases=$passed.ToArray()
  helper_entrypoint=0;dynamic_csharp_compile=0;uia=0;win32_calls=0;app=0;cli=0;task=0;model=0} |
  ConvertTo-Json -Depth 5
