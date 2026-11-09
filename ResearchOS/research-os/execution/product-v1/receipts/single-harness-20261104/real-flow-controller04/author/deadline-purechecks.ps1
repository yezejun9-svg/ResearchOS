$ErrorActionPreference = 'Stop'
$tokens=$null
$errors=$null
$sourcePath=Join-Path $PSScriptRoot 'choose-owned-folder.ps1'
$ast=[Management.Automation.Language.Parser]::ParseFile($sourcePath,[ref]$tokens,[ref]$errors)
if ($errors.Count -ne 0) { throw 'HELPER_AST_PARSE_FAILED' }
$defs=@($ast.FindAll({param($node)
  $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -ceq 'Convert-NativeDeadlineUtc'
},$true))
if ($defs.Count -ne 1) { throw 'DATE_FUNCTION_NOT_UNIQUE' }
# Extract one pure function only, never the helper entrypoint, process
# inspections, Add-Type, UIAutomation, Windows messages or a model.
. ([ScriptBlock]::Create($defs[0].Extent.Text))
$script:cases=[Collections.Generic.List[object]]::new()
function Check([string]$Name,[ScriptBlock]$Action) {
  try { & $Action; $script:cases.Add(@{name=$Name;status='PASS'}) }
  catch {
    @{status='DATE_PURE_FAILURE';case=$Name;reason=$_.Exception.Message}|ConvertTo-Json -Compress|Write-Output
    throw
  }
}
function Equal($Actual,$Expected) {
  if ($Actual -ne $Expected) { throw ('EXPECTED:'+ $Expected + ';ACTUAL:'+$Actual) }
}
function Reject($Value,[string]$Code) {
  $caught=$false
  try { $null=Convert-NativeDeadlineUtc -Value $Value }
  catch {
    if ($_.Exception.Message -notlike ('*'+$Code+'*')) { throw }
    $caught=$true
  }
  if (-not $caught) { throw 'INVALID_WIRE_ACCEPTED' }
}
$wire='2026-11-04T21:52:54.266Z'
$expected=[DateTimeOffset]::new(2026,11,4,21,52,54,266,[TimeSpan]::Zero)
Check 'locked shell supports DateKind String' {
  Equal ((Get-Command ConvertFrom-Json).Parameters.ContainsKey('DateKind')) $true
}
Check 'actual identity ingress preserves string' {
  $source=Get-Content -LiteralPath $sourcePath -Raw -Encoding UTF8
  if (-not $source.Contains('$identity = Get-Content -LiteralPath $identityFile -Raw -Encoding UTF8 | ConvertFrom-Json -DateKind String')) { throw 'IDENTITY_RAW_STRING_INGRESS_NOT_CONNECTED' }
  $identity=('{"action_deadline_utc":"'+$wire+'"}')|ConvertFrom-Json -DateKind String
  Equal ($identity.action_deadline_utc -is [string]) $true
  Equal $identity.action_deadline_utc $wire
}
Check 'actual wire UTC kind and exact Unix milliseconds' {
  $parsed=Convert-NativeDeadlineUtc $wire
  Equal $parsed.Kind ([DateTimeKind]::Utc)
  Equal ([DateTimeOffset]::new($parsed).ToUnixTimeMilliseconds()) $expected.ToUnixTimeMilliseconds()
  Equal $parsed.Millisecond 266
}
Check 'actual sample start retains full five minutes' {
  $parsed=Convert-NativeDeadlineUtc $wire
  $start=[DateTimeOffset]::new(2026,11,4,21,47,54,266,[TimeSpan]::Zero).UtcDateTime
  Equal ($start -ge $parsed) $false
  Equal ($parsed-$start).TotalMilliseconds 300000
}
Check 'deadline before tick not expired' {
  $parsed=Convert-NativeDeadlineUtc $wire
  Equal ($parsed.AddTicks(-1) -ge $parsed) $false
}
Check 'deadline equality remains expired' {
  $parsed=Convert-NativeDeadlineUtc $wire
  Equal ($parsed -ge $parsed) $true
}
Check 'deadline after tick remains expired' {
  $parsed=Convert-NativeDeadlineUtc $wire
  Equal ($parsed.AddTicks(1) -ge $parsed) $true
}
Check 'cleanup extension retains UTC and milliseconds' {
  $parsed=Convert-NativeDeadlineUtc $wire
  $cleanup=$parsed.AddMilliseconds(30000)
  Equal $cleanup.Kind ([DateTimeKind]::Utc)
  Equal ([DateTimeOffset]::new($cleanup).ToUnixTimeMilliseconds()) ($expected.ToUnixTimeMilliseconds()+30000)
  Equal ($cleanup -ge $cleanup) $true
}
$originalCulture=[Globalization.CultureInfo]::CurrentCulture
try {
  foreach ($name in @('zh-CN','en-US','fr-FR','ar-SA','th-TH')) {
    [Globalization.CultureInfo]::CurrentCulture=[Globalization.CultureInfo]::GetCultureInfo($name)
    Check ('Invariant under '+$name) {
      $parsed=Convert-NativeDeadlineUtc $wire
      Equal ([DateTimeOffset]::new($parsed).ToUnixTimeMilliseconds()) $expected.ToUnixTimeMilliseconds()
      Equal $parsed.Kind ([DateTimeKind]::Utc)
    }
  }
} finally { [Globalization.CultureInfo]::CurrentCulture=$originalCulture }
Check 'DateTime object cannot be implicitly stringified' { Reject ([DateTime]::UtcNow) 'UTC_WIRE_STRING_REQUIRED' }
Check 'DateTimeOffset object cannot be implicitly stringified' { Reject ([DateTimeOffset]::UtcNow) 'UTC_WIRE_STRING_REQUIRED' }
Check 'null rejected' { Reject $null 'UTC_WIRE_STRING_REQUIRED' }
Check 'integer rejected' { Reject 1793829174266 'UTC_WIRE_STRING_REQUIRED' }
Check 'array rejected' { Reject ([object[]]@($wire)) 'UTC_WIRE_STRING_REQUIRED' }
foreach ($bad in @(
  '', '2026-11-04T21:52:54Z', '2026-11-04T21:52:54.26Z',
  '2026-11-04T21:52:54.2660Z', '2026-11-04T21:52:54.266+00:00',
  '2026-11-04T21:52:54.266+08:00', '2026-11-04T21:52:54.266',
  '2026-11-04t21:52:54.266Z', '2026-11-04T21:52:54.266z',
  (' '+$wire), ($wire+' '), ($wire+[char]10), '11/04/2026 21:52:54'
)) { Check ('reject shape '+$bad.Replace([string][char]10,'\n')) { Reject $bad 'UTC_WIRE_STRING_REQUIRED' } }
foreach ($bad in @('2026-02-30T21:52:54.266Z','2026-13-04T21:52:54.266Z','2026-11-04T21:52:60.266Z','0000-11-04T21:52:54.266Z')) {
  Check ('reject invalid calendar '+$bad) { Reject $bad 'INVALID_UTC_WIRE_VALUE' }
}
Check 'valid Gregorian leap day' {
  Equal (Convert-NativeDeadlineUtc '2024-02-29T00:00:00.001Z').Millisecond 1
}
$report=@{schema='researchos.native-deadline.purechecks/1';status='PURE_DATE_FUNCTION_PASS';
  passed=$script:cases.Count;cases=@($script:cases);helper_entrypoint=0;add_type=0;uia=0;gui=0;native=0;model=0}
$report|ConvertTo-Json -Depth 12 -Compress
