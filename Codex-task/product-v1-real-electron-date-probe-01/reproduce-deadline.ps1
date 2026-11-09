$ErrorActionPreference = 'Stop'
$receipt = 'C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-real-electron-run-01/receipts/owned-core.json'
$raw = Get-Content -LiteralPath $receipt -Raw -Encoding UTF8
$supportsDateKind = (Get-Command ConvertFrom-Json).Parameters.ContainsKey('DateKind')
if (-not $supportsDateKind) { throw 'LOCKED_SHELL_DATEKIND_UNAVAILABLE' }
$default = $raw | ConvertFrom-Json
$retained = $raw | ConvertFrom-Json -DateKind String
$old = [DateTimeOffset]::Parse($default.action_deadline_utc).UtcDateTime
$styles = [Globalization.DateTimeStyles]::AssumeUniversal -bor [Globalization.DateTimeStyles]::AdjustToUniversal
$strict = [DateTimeOffset]::ParseExact(
  $retained.action_deadline_utc,
  "yyyy-MM-dd'T'HH:mm:ss.fff'Z'",
  [Globalization.CultureInfo]::InvariantCulture, $styles).UtcDateTime
# Fixed past sample anchors this replay to the actual run's start; current wall
# time cannot be used to judge a deadline belonging to a stopped old run.
$sampleNow = $strict.AddMinutes(-5)
$report = @{
  schema='researchos.native-deadline.pure-reproduction/1'
  status='PURE_REPRODUCTION_ONLY'
  receipt_path=$receipt
  receipt_sha256=(Get-FileHash -LiteralPath $receipt -Algorithm SHA256).Hash.ToLowerInvariant()
  shell_version=$PSVersionTable.PSVersion.ToString()
  local_timezone=[TimeZoneInfo]::Local.Id
  local_base_utc_offset=[TimeZoneInfo]::Local.BaseUtcOffset.ToString()
  current_culture=[Globalization.CultureInfo]::CurrentCulture.Name
  convert_from_json_datekind_supported=$supportsDateKind
  raw_utc_wire=$retained.action_deadline_utc
  raw_retained_type=$retained.action_deadline_utc.GetType().FullName
  default_json_type=$default.action_deadline_utc.GetType().FullName
  default_json_kind=$default.action_deadline_utc.Kind.ToString()
  default_json_roundtrip=$default.action_deadline_utc.ToString('o')
  implicit_string=[string]$default.action_deadline_utc
  old_parse_utc=$old.ToString('o')
  strict_parse_utc=$strict.ToString('o')
  old_minus_wire_ms=($old-$strict).TotalMilliseconds
  sample_now_utc=$sampleNow.ToString('o')
  old_declares_expired=($sampleNow -ge $old)
  correct_declares_expired=($sampleNow -ge $strict)
  correct_remaining_ms=($strict-$sampleNow).TotalMilliseconds
  helper_body=0; add_type=0; uia=0; gui=0; native=0; model=0
}
$output = Join-Path $PSScriptRoot 'REPRO.json'
if (Test-Path -LiteralPath $output) { throw 'REPRO_ALREADY_EXISTS_DO_NOT_OVERWRITE' }
$report | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $output -Encoding utf8
$report | ConvertTo-Json -Depth 12 -Compress
if ($report.default_json_type -cne 'System.DateTime' -or
    $report.raw_retained_type -cne 'System.String' -or
    -not $report.old_declares_expired -or $report.correct_declares_expired) {
  throw 'EXPECTED_CAUSE_NOT_REPRODUCED_REVIEW_OBSERVATIONS'
}
