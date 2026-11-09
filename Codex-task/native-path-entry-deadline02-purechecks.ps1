$ErrorActionPreference='Stop'
$folder=Join-Path $PSScriptRoot 'product-v1-native-path-entry-prepare-02'
$source=Get-Content -LiteralPath (Join-Path $folder 'choose-owned-folder.ps1') -Raw -Encoding UTF8
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseInput($source,[ref]$tokens,[ref]$errors)
if ($errors.Count) {throw ('HELPER_AST_SYNTAX: '+($errors.Message -join '; '))}
$defs=@($ast.FindAll({param($node)$node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -ceq 'Assert-MessageDeadline'},$true))
if ($defs.Count -ne 1) {throw 'DEADLINE_PREDICATE_NOT_UNIQUE'}
. ([ScriptBlock]::Create($defs[0].Extent.Text))
$passed=[Collections.Generic.List[string]]::new()
function Expect-Failure([string]$Name,[scriptblock]$Action) {
  $failed=$false;try {& $Action} catch {$failed=$true}
  if (-not $failed) {throw ('EXPECTED_FAILURE:'+ $Name)}
  $passed.Add($Name)
}
$action=[DateTime]::new(100000,[DateTimeKind]::Utc)
$cleanup=[DateTime]::new(130000,[DateTimeKind]::Utc)
Assert-MessageDeadline ([DateTime]::new(99000,[DateTimeKind]::Utc)) $action
$passed.Add('action_before_deadline')
Expect-Failure 'action_equal_deadline' {Assert-MessageDeadline $action $action}
Expect-Failure 'rediscovery_crossed_action_deadline' {Assert-MessageDeadline ([DateTime]::new(110000,[DateTimeKind]::Utc)) $action}
Assert-MessageDeadline ([DateTime]::new(110000,[DateTimeKind]::Utc)) $cleanup
$passed.Add('cleanup_uses_independent_later_deadline')
Expect-Failure 'cleanup_expired_no_message' {Assert-MessageDeadline $cleanup $cleanup}
@{schema='researchos.native-path-entry-deadline02-pure/1';helper_ast='PASS';pure_cases=$passed.ToArray()
  inherited_pure_cases_not_rerun=23;helper_entrypoint=0;dynamic_csharp_compile=0;uia=0;win32_calls=0;app=0;cli=0;task=0;model=0} |
  ConvertTo-Json -Depth 5
