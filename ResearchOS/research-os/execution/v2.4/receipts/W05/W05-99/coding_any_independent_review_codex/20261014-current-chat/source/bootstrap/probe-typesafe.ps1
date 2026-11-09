$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSHOME 'Modules\Microsoft.PowerShell.Security\Microsoft.PowerShell.Security.psd1') -ErrorAction Stop
Add-Type -AssemblyName System.Net.Http
$root = Split-Path $PSScriptRoot -Parent
$evidenceRoot = Join-Path $root 'execution\readiness\typesafe'
$runId = [guid]::NewGuid().ToString()
$record = @{ invocation_id = $runId; method = 'GET'; url = 'https://api.typesafe.ai/v1/models'; started_at = [DateTime]::UtcNow.ToString('o'); credential_ref = '.local/secrets/typesafe.dpapi'; scope = 'AUTHENTICATED_MODEL_LIST_READINESS_ONLY'; live_evaluation = 'NOT_RUN'; cost = $null; status = 'ERROR' }
$pointer = [IntPtr]::Zero
$secure = $null
$client = $null
try {
    $secure = Get-Content -LiteralPath (Join-Path $root '.local\secrets\typesafe.dpapi') -Raw | ConvertTo-SecureString
    $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    $key = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
    $handler = New-Object System.Net.Http.HttpClientHandler
    $handler.AllowAutoRedirect = $false
    $client = New-Object System.Net.Http.HttpClient($handler)
    $client.Timeout = [TimeSpan]::FromSeconds(30)
    $client.DefaultRequestHeaders.Authorization = New-Object System.Net.Http.Headers.AuthenticationHeaderValue('Bearer', $key)
    $response = $client.GetAsync($record.url).GetAwaiter().GetResult()
    $record.http_status = [int]$response.StatusCode
    if ($response.IsSuccessStatusCode) {
        $body = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult() | ConvertFrom-Json
        $models = @($body.models | ForEach-Object { @{ name = $_.name; release_date = $_.release_date } })
        if ($models.Count -eq 0 -or @($models | Where-Object { -not $_.name }).Count -gt 0) { throw 'Model list invalid' }
        $record.models = $models
        $record.status = 'PASS'
    } else { $record.status = 'HTTP_ERROR' }
    $response.Dispose()
} catch {
    # Never persist response bodies or exception messages that might contain headers.
    $record.error_type = $_.Exception.GetType().Name
} finally {
    $key = $null
    if ($client) { $client.DefaultRequestHeaders.Clear(); $client.Dispose() }
    if ($pointer -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer) }
    if ($secure) { $secure.Dispose() }
}
$record.ended_at = [DateTime]::UtcNow.ToString('o')
New-Item -ItemType Directory -Path $evidenceRoot -Force | Out-Null
$evidence = Join-Path $evidenceRoot ($runId + '-models.json')
$record | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $evidence -Encoding UTF8
@{ status = $record.status; http_status = $record.http_status; evidence = $evidence; live_evaluation = 'NOT_RUN' } | ConvertTo-Json
exit $(if ($record.status -eq 'PASS') { 0 } else { 1 })
