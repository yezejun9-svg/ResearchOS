$ErrorActionPreference='Stop'
$t=$null;$e=$null
$ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'source/choose-owned-folder.ps1'),[ref]$t,[ref]$e)
if($e.Count -ne 0){throw 'AST_SYNTAX_FAILED'}
$f=@($ast.FindAll({param($n)$n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq 'Convert-NativeDeadlineUtc'},$true))
if($f.Count -ne 1){throw 'ONE_PURE_DATE_FUNCTION_REQUIRED'}
# Evaluate exactly one audited pure date function, never helper entrypoint.
. ([ScriptBlock]::Create($f[0].Extent.Text))
$cases=[Collections.Generic.List[object]]::new()
function Check($Name,[ScriptBlock]$Body){& $Body;$cases.Add(@{name=$Name;status='PASS'})}
function Equal($A,$B){if($A -ne $B){throw ('MISMATCH:'+ $A +':'+$B)}}
function Reject($Value){$caught=$false;try{$null=Convert-NativeDeadlineUtc $Value}catch{$caught=$true};if(-not $caught){throw 'INVALID_VALUE_ACCEPTED'}}
$wire='2026-11-04T21:52:54.266Z'
$expected=[DateTimeOffset]::new(2026,11,4,21,52,54,266,[TimeSpan]::Zero)
$original=[Threading.Thread]::CurrentThread.CurrentCulture
try{
 foreach($culture in @('en-US','zh-CN','ar-SA')){
  [Threading.Thread]::CurrentThread.CurrentCulture=[Globalization.CultureInfo]::GetCultureInfo($culture)
  Check ('invariant UTC milliseconds under '+$culture) {$d=Convert-NativeDeadlineUtc $wire;Equal $d.Kind ([DateTimeKind]::Utc);Equal ([DateTimeOffset]::new($d).ToUnixTimeMilliseconds()) $expected.ToUnixTimeMilliseconds();Equal $d.Millisecond 266}
 }
 Check 'actual JSON ingress retains raw wire string and no implicit date object' {$o=('{"action_deadline_utc":"'+$wire+'"}')|ConvertFrom-Json -DateKind String;Equal ($o.action_deadline_utc -is [string]) $true;Equal $o.action_deadline_utc $wire;Equal (Convert-NativeDeadlineUtc $o.action_deadline_utc).Ticks $expected.UtcDateTime.Ticks}
 Check 'five minute budget cleanup extension and expired instant stay exact' {$now=Convert-NativeDeadlineUtc '2026-11-04T21:47:54.266Z';$d=Convert-NativeDeadlineUtc $wire;Equal ($d-$now).TotalMilliseconds 300000;Equal ($d.AddMilliseconds(30000)-$now).TotalMilliseconds 330000;$past=Convert-NativeDeadlineUtc '2026-11-04T21:47:54.265Z';Equal ($past -lt $now) $true}
 Check 'DateTime and DateTimeOffset objects never silently coerce to local strings' {Reject $expected.UtcDateTime;Reject $expected;Reject $null;Reject 1793829174266}
 Check 'ambiguous offset locale precision and invalid calendar wires fail closed' {foreach($value in @('2026-11-04T21:52:54.266+00:00','2026-11-05T05:52:54.266+08:00','11/04/2026 21:52:54','2026-11-04T21:52:54.266z','2026-11-04T21:52:54Z','2026-11-04T21:52:54.2660000Z','2025-02-29T21:52:54.266Z','2026-11-04T21:52:60.266Z')){Reject $value}}
}finally{[Threading.Thread]::CurrentThread.CurrentCulture=$original}
@{status='INDEPENDENT_PURE_DEADLINE_CASES_PASS';passed=$cases.Count;cases=@($cases);helper_entrypoint=0;AddType=0;UIA=0;GUI=0;Native=0;model=0;formal_increment=0}|ConvertTo-Json -Depth 8 -Compress
