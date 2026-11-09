$ErrorActionPreference='Stop'
$sourcePath=Join-Path (Split-Path $PSScriptRoot -Parent | Split-Path -Parent) 'product-v1-real-electron-tree-diagnostic-revision-04/choose-owned-folder.ps1'
if ((Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash.ToLowerInvariant() -cne '88e4b33142d8e8274ec0edcc99314f4f867a749217f869298ae8e7fdc52d9d47') {throw 'SOURCE_DRIFT'}
$tokens=$null;$errors=$null
$source=Get-Content -LiteralPath $sourcePath -Raw -Encoding UTF8
$ast=[Management.Automation.Language.Parser]::ParseInput($source,[ref]$tokens,[ref]$errors)
if ($errors.Count) {throw 'SOURCE_SYNTAX'}
foreach ($name in @('Limit-DiagnosticText','Read-DiagnosticField','Diagnostic-Number','Project-TreeDiagnostic')) {
 $defs=@($ast.FindAll({param($n)$n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq $name},$true))
 if ($defs.Count -ne 1) {throw 'FUNCTION_NOT_UNIQUE'}
 . ([ScriptBlock]::Create($defs[0].Extent.Text))
}
$script:foreignNameReads=0;$script:foreignIdReads=0
$foreign=[pscustomobject]@{ProcessId=99;ControlType=[pscustomobject]@{ProgrammaticName='SYNTHETIC'};BoundingRectangle=$null;NativeWindowHandle=123;ClassName='SYNTHETIC';IsOffscreen=$false;IsEnabled=$true}
$foreign | Add-Member -MemberType ScriptProperty -Name Name -Value {$script:foreignNameReads++;'SYNTHETIC_FOREIGN_NAME'}
$foreign | Add-Member -MemberType ScriptProperty -Name AutomationId -Value {$script:foreignIdReads++;'SYNTHETIC_FOREIGN_ID'}
$element=[pscustomobject]@{Current=$foreign}
$projected=Project-TreeDiagnostic $element 0 42
if ($script:foreignNameReads -ne 0 -or $script:foreignIdReads -ne 0 -or $projected.status -cne 'FOREIGN_PROVIDER_OWNER' -or $projected.process_id -ne 99 -or $projected.ContainsKey('name') -or $projected.ContainsKey('automation_id')) {throw 'FOREIGN_METADATA_LEAK'}
$passed=1
$script:selectedCurrentReads=0
$selected=[pscustomobject]@{}
$selected | Add-Member -MemberType ScriptProperty -Name Current -Value {$script:selectedCurrentReads++;if ($script:selectedCurrentReads -eq 1) {[pscustomobject]@{ProcessId=42}}else{$foreign}}
if ($selected.Current.ProcessId -ne 42) {throw 'PRECHECK_FIXTURE'}
$row=Project-TreeDiagnostic $selected 1 42
if ($script:selectedCurrentReads -ne 2 -or $row.status -cne 'FOREIGN_PROVIDER_OWNER' -or $script:foreignNameReads -ne 0 -or $script:foreignIdReads -ne 0) {throw 'SELECTED_OWNER_CHANGE_LEAK'}
$passed++
$script:currentReads=0;$script:pidReads=0;$script:nameReads=0;$script:idReads=0
$good=[pscustomobject]@{ControlType=[pscustomobject]@{ProgrammaticName='SYNTHETIC'};BoundingRectangle=$null;NativeWindowHandle=123;ClassName='SYNTHETIC';IsOffscreen=$false;IsEnabled=$true}
$good | Add-Member -MemberType ScriptProperty -Name ProcessId -Value {$script:pidReads++;42}
$good | Add-Member -MemberType ScriptProperty -Name Name -Value {$script:nameReads++;'SYNTHETIC_OWNED_NAME'}
$good | Add-Member -MemberType ScriptProperty -Name AutomationId -Value {$script:idReads++;'SYNTHETIC_OWNED_ID'}
$owned=[pscustomobject]@{}
$owned | Add-Member -MemberType ScriptProperty -Name Current -Value {$script:currentReads++;$good}
$row=Project-TreeDiagnostic $owned 0 42
if ($row.status -cne 'METADATA_ONLY' -or $script:currentReads -ne 1 -or $script:pidReads -ne 1 -or $script:nameReads -ne 1 -or $script:idReads -ne 1) {throw 'OWNED_SNAPSHOT_NOT_SINGLE_READ'}
$passed++
if (-not $source.Contains('$current=Project-TreeDiagnostic $element 0 $coreId') -or -not $source.Contains('Project-TreeDiagnostic $selected[$i] $i $coreId')) {throw 'BOTH_CALLS_MUST_PASS_OWNER'}
@{status='OWNER_BEFORE_METADATA_REGRESSION_PASS';passed=$passed;foreign_name_reads=0;foreign_id_reads=0;selected_owner_change_refused=$true;owned_current_reads=1;owned_pid_reads=1;helper_syntax=0;helper_entrypoint=0;AddType=0;UIA=0;GUI=0;model=0}|ConvertTo-Json -Compress
