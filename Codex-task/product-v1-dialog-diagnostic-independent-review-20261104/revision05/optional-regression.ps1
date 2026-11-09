$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$sourcePath=Join-Path (Split-Path $PSScriptRoot -Parent | Split-Path -Parent) 'product-v1-real-electron-tree-diagnostic-revision-05/choose-owned-folder.ps1'
if ((Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash.ToLowerInvariant() -cne '8d2811eb8e8c3fd93cbbf460b5562c899df88cb1458dc522fbadad5def284875') {throw 'SOURCE_DRIFT'}
# Passive managed identifiers only. No helper entrypoint, native functions,
# AutomationElement instance, FromHandle, COM object, or dynamic C# compile.
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$tokens=$null;$errors=$null
$source=Get-Content -LiteralPath $sourcePath -Raw -Encoding UTF8
$ast=[Management.Automation.Language.Parser]::ParseInput($source,[ref]$tokens,[ref]$errors)
if ($errors.Count) {throw 'SOURCE_SYNTAX'}
foreach ($name in @('Limit-DiagnosticText','Project-PublicUiaValue','Read-PublicPatterns','Read-DiagnosticField','Diagnostic-Number','Project-TreeDiagnostic')) {
  $defs=@($ast.FindAll({param($node)$node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -ceq $name},$true))
  if ($defs.Count -ne 1) {throw 'FUNCTION_NOT_UNIQUE'}
  . ([ScriptBlock]::Create($defs[0].Extent.Text))
}
function Assert-DirectNativeTree { $script:guardCalls++ }
$coreId=42
$script:guardCalls=0;$script:nameReads=0;$script:queries=[Collections.Generic.List[int]]::new()
$valueId=[Windows.Automation.ValuePattern]::Pattern.Id
$selectionId=[Windows.Automation.SelectionPattern]::Pattern.Id
if ($null -ne ([Management.Automation.PSTypeName]::new('System.Windows.Automation.LegacyIAccessiblePattern')).Type) {throw 'EXPECTED_INSTALLED_MISSING_LEGACY'}
$info=[pscustomobject]@{ProcessId=42}
$info|Add-Member ScriptProperty Name {$script:nameReads++;'SYNTHETIC_OWNED_NAME'}
$element=[pscustomobject]@{Current=$info}
$element|Add-Member ScriptMethod TryGetCurrentPattern {
  param($id,$out)
  $script:queries.Add($id.Id)
  if ($id.Id -eq $valueId) {
    $out.Value=[pscustomobject]@{Current=[pscustomobject]@{Value='C:\synthetic\workspace'}}
    return $true
  }
  if ($id.Id -eq $selectionId) {
    $fake=[pscustomobject]@{}
    $fake|Add-Member ScriptMethod GetCurrentSelection {return @()}
    $out.Value=$fake
    return $true
  }
  throw 'UNEXPECTED_PATTERN_QUERY'
}
$read=Read-PublicPatterns $element
if ($read.support.LegacyIAccessiblePattern.status -cne 'UNSUPPORTED_TYPE' -or
    $read.support.LegacyIAccessiblePattern.supported -ne $false -or
    $read.support.ValuePattern.supported -ne $true -or
    @($read.values|Where-Object {$_.source -ceq 'ValuePattern' -and $_.value -ceq 'C:\synthetic\workspace' -and $_.selection_authority -eq $false}).Count -ne 1 -or
    $script:queries.Count -ne 1 -or $script:queries[0] -ne $valueId) {throw 'MISSING_LEGACY_ABORTED_VALUE'}
# Reuse source-fragment method with the corrected line-start outer-catch anchor.
# Parse before executing; this fragment contains only fake Selection operations.
$a=$source.IndexOf('      $selection=$null;$supported=$element.TryGetCurrentPattern(')
$end=[regex]::Match($source.Substring($a),'(?m)^    \} catch \{')
if ($a -lt 0 -or -not $end.Success -or $end.Index -le 0) {throw 'SELECTION_FRAGMENT_BOUNDARY'}
$fragment=$source.Substring($a,$end.Index)
$fragmentTokens=$null;$fragmentErrors=$null
$null=[Management.Automation.Language.Parser]::ParseInput($fragment,[ref]$fragmentTokens,[ref]$fragmentErrors)
if ($fragmentErrors.Count) {throw 'SELECTION_FRAGMENT_SYNTAX'}
$direct=@{patterns=$read.support}
. ([ScriptBlock]::Create($fragment))
if ($direct.patterns.SelectionPattern.supported -ne $true -or $direct.selection_count -ne 0 -or
    $script:queries.Count -ne 2 -or $script:queries[1] -ne $selectionId -or $script:nameReads -ne 1) {throw 'MISSING_LEGACY_ABORTED_SELECTION'}
$cases=@(@{name='missing Legacy type preserves Value and actual Selection continuation';status='PASS';legacy_status=$read.support.LegacyIAccessiblePattern.status;value_queries=1;selection_queries=1;selection_authority=$false})

$script:nameReads=0;$script:queries.Clear()
$foreign=[pscustomobject]@{ProcessId=99}
$foreign|Add-Member ScriptProperty Name {$script:nameReads++;'FORBIDDEN_NAME'}
$element.Current=$foreign
$caught=$false
try {$null=Read-PublicPatterns $element} catch {$caught=$_.Exception.Message -like '*OWNER_UNCONFIRMED*'}
if (-not $caught -or $script:nameReads -ne 0 -or $script:queries.Count -ne 0) {throw 'FOREIGN_VALUES_READ'}
$element.Current=$null
$nullCaught=$false
try {$null=Read-PublicPatterns $element} catch {$nullCaught=$_.Exception.Message -like '*OWNER_UNCONFIRMED*'}
if (-not $nullCaught -or $script:nameReads -ne 0 -or $script:queries.Count -ne 0) {throw 'NULL_CURRENT_VALUES_READ'}
$cases+=@{name='foreign and null Current refuse Name and every pattern query';status='PASS';foreign_name_reads=$script:nameReads;pattern_queries=$script:queries.Count}

$script:foreignNameReads=0;$script:foreignIdReads=0;$script:selectedCurrentReads=0
$foreign|Add-Member ScriptProperty AutomationId {$script:foreignIdReads++;'FORBIDDEN_ID'}
$selected=[pscustomobject]@{}
$selected|Add-Member ScriptProperty Current {$script:selectedCurrentReads++;if ($script:selectedCurrentReads -eq 1) {[pscustomobject]@{ProcessId=42}}else{$foreign}}
if ($selected.Current.ProcessId -ne 42) {throw 'SYNTHETIC_PRECHECK'}
$row=Project-TreeDiagnostic $selected 1 42
if ($script:selectedCurrentReads -ne 2 -or $row.status -cne 'FOREIGN_PROVIDER_OWNER' -or
    $script:nameReads -ne 0 -or $script:foreignIdReads -ne 0 -or $row.ContainsKey('name') -or $row.ContainsKey('automation_id')) {throw 'PROJECTOR_FOREIGN_SNAPSHOT_LEAK'}
$script:currentReads=0;$script:pidReads=0;$script:ownedNameReads=0;$script:ownedIdReads=0
$good=[pscustomobject]@{ControlType=[pscustomobject]@{ProgrammaticName='SYNTHETIC'};BoundingRectangle=$null;NativeWindowHandle=123;ClassName='SYNTHETIC';IsOffscreen=$false;IsEnabled=$true}
$good|Add-Member ScriptProperty ProcessId {$script:pidReads++;42}
$good|Add-Member ScriptProperty Name {$script:ownedNameReads++;'SYNTHETIC_OWNED_NAME'}
$good|Add-Member ScriptProperty AutomationId {$script:ownedIdReads++;'SYNTHETIC_OWNED_ID'}
$owned=[pscustomobject]@{}
$owned|Add-Member ScriptProperty Current {$script:currentReads++;$good}
$row=Project-TreeDiagnostic $owned 0 42
if ($row.status -cne 'METADATA_ONLY' -or $script:currentReads -ne 1 -or $script:pidReads -ne 1 -or $script:ownedNameReads -ne 1 -or $script:ownedIdReads -ne 1) {throw 'PROJECTOR_SNAPSHOT_RETAKEN'}
if (-not $source.Contains('$current=Project-TreeDiagnostic $element 0 $coreId') -or -not $source.Contains('Project-TreeDiagnostic $selected[$i] $i $coreId')) {throw 'OWNER_ARGUMENT_MISSING'}
$cases+=@{name='Project keeps same-Current owner guard after selected owner changes';status='PASS';foreign_metadata_reads=0;owned_Current_reads=1;owned_ProcessId_reads=1}

@{schema='researchos.optional-legacy-independent-pure/1';status='PASS';passed=$cases.Count;cases=$cases;helper_AST_syntax=0;selection_fragment_syntax=0;passive_assembly_loads=2;dynamic_csharp_compile=0;com_objects=0;helper_entrypoint=0;real_uia_element_calls=0;gui=0;model=0;formal_increment=0;product_increment=0}|ConvertTo-Json -Depth 10 -Compress
