$ErrorActionPreference='Stop'
$source=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'choose-owned-folder.ps1') -Raw -Encoding UTF8
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseInput($source,[ref]$tokens,[ref]$errors)
if ($errors.Count) {throw ('HELPER_AST_SYNTAX: '+($errors.Message -join '; '))}
$defs=@($ast.FindAll({param($node)$node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -ceq 'Assert-DialogThreadFacts'},$true))
if ($defs.Count -ne 1) {throw 'ACTIVE_THREAD_PREDICATE_NOT_UNIQUE'}
# Pure snapshot predicate only: no Add-Type, GUI, target query or helper body.
. ([ScriptBlock]::Create($defs[0].Extent.Text))
$passed=[Collections.Generic.List[string]]::new()
function Expect-Failure([string]$Name,[scriptblock]$Action) {
  $failed=$false;try {& $Action} catch {$failed=$true}
  if (-not $failed) {throw ('EXPECTED_FAILURE:'+ $Name)}
  $passed.Add($Name)
}
$good=@{query_succeeded=$true;dialog_hwnd=7;dialog_pid_before=42;dialog_pid_after=42
  dialog_tid_before=101;dialog_tid_after=101;active_hwnd=7;active_pid=42;active_tid=101
  focus_hwnd=8;focus_pid=42;focus_is_dialog_or_child=$true;global_foreground_hwnd=9001}
Assert-DialogThreadFacts $good 42 7
$passed.Add('actual_thread_active_owned_edit_despite_other_global_foreground')
$same=@{}+$good;$same.focus_hwnd=7
Assert-DialogThreadFacts $same 42 7
$passed.Add('dialog_itself_may_hold_focus')
$bad=@{}+$good;$bad.query_succeeded=$false
Expect-Failure 'query_failed_no_post' {Assert-DialogThreadFacts $bad 42 7}
$bad=@{}+$good;$bad.active_hwnd=0
Expect-Failure 'null_active_no_post' {Assert-DialogThreadFacts $bad 42 7}
$bad=@{}+$good;$bad.active_hwnd=9
Expect-Failure 'other_active_dialog_no_post' {Assert-DialogThreadFacts $bad 42 7}
$bad=@{}+$good;$bad.dialog_pid_after=43
Expect-Failure 'dialog_pid_changed_no_post' {Assert-DialogThreadFacts $bad 42 7}
$bad=@{}+$good;$bad.dialog_tid_after=102
Expect-Failure 'dialog_tid_changed_no_post' {Assert-DialogThreadFacts $bad 42 7}
$bad=@{}+$good;$bad.focus_hwnd=0
Expect-Failure 'null_focus_no_post' {Assert-DialogThreadFacts $bad 42 7}
$bad=@{}+$good;$bad.focus_pid=43
Expect-Failure 'foreign_focus_no_post' {Assert-DialogThreadFacts $bad 42 7}
$bad=@{}+$good;$bad.focus_is_dialog_or_child=$false
Expect-Failure 'same_core_focus_outside_dialog_no_post' {Assert-DialogThreadFacts $bad 42 7}
@{schema='researchos.native-path-entry-active03-pure/1';helper_ast='PASS';pure_cases=$passed.ToArray()
  inherited_pure_cases_not_rerun=28;helper_entrypoint=0;dynamic_csharp_compile=0;uia=0;win32_calls=0;app=0;cli=0;task=0;model=0} |
  ConvertTo-Json -Depth 5
