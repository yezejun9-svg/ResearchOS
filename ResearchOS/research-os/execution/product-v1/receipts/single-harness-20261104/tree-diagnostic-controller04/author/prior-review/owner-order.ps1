$ErrorActionPreference='Stop'
$sourcePath=Join-Path (Split-Path $PSScriptRoot -Parent | Split-Path -Parent) 'product-v1-real-electron-tree-diagnostic-revision-03/choose-owned-folder.ps1'
if ((Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash.ToLowerInvariant() -cne '029a96be3fecc0e4154acdeb402c90ccf1120783492ba1b9d08aa840ce5ab732') {throw 'SOURCE_DRIFT'}
$tokens=$null;$errors=$null
$source=Get-Content -LiteralPath $sourcePath -Raw -Encoding UTF8
$ast=[Management.Automation.Language.Parser]::ParseInput($source,[ref]$tokens,[ref]$errors)
if ($errors.Count) {throw 'SOURCE_SYNTAX'}
foreach ($name in @('Limit-DiagnosticText','Read-DiagnosticField','Diagnostic-Number','Project-TreeDiagnostic')) {
 $defs=@($ast.FindAll({param($n)$n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq $name},$true))
 if ($defs.Count -ne 1) {throw 'FUNCTION_NOT_UNIQUE'}
 . ([ScriptBlock]::Create($defs[0].Extent.Text))
}
$script:foreignNameReads=0
$info=[pscustomobject]@{ProcessId=99;ControlType=[pscustomobject]@{ProgrammaticName='SYNTHETIC'};BoundingRectangle=$null;NativeWindowHandle=123;ClassName='SYNTHETIC';AutomationId='SYNTHETIC';IsOffscreen=$false;IsEnabled=$true}
$info | Add-Member -MemberType ScriptProperty -Name Name -Value {$script:foreignNameReads++;'SYNTHETIC_FOREIGN_NAME'}
$element=[pscustomobject]@{Current=$info}
$projected=Project-TreeDiagnostic $element 0
$before=$source.IndexOf('$current=Project-TreeDiagnostic $element 0')
$guard=$source.IndexOf('$read=Read-PublicPatterns $element',$before)
if ($before -lt 0 -or $guard -le $before) {throw 'SOURCE_ORDER_CHANGED'}
if ($script:foreignNameReads -ne 1 -or $projected.process_id -ne 99 -or $projected.name -cne 'SYNTHETIC_FOREIGN_NAME') {throw 'COUNTEREXAMPLE_NOT_REPRODUCED'}
@{status='FOREIGN_PROVIDER_NAME_READ_BEFORE_OWNER_GUARD_REPRODUCED';actual_ast_functions=$true;foreign_pid=99;expected_owner_pid=42;foreign_name_reads=$script:foreignNameReads;helper_entrypoint=0;AddType=0;UIA=0;GUI=0;model=0}|ConvertTo-Json -Compress
