$ErrorActionPreference = 'Stop'
$repo = 'D:/作品集/ResearchOS/research-os/.local/worktrees/w05-normal-runtime-host-20261012'
$binary = 'D:/作品集/ResearchOS/research-os/.local/builds/normal-runtime-host-candidate-20261012/researchos-control.exe'
$receipts = Split-Path -Parent $PSCommandPath
$assets = 'D:/作品集/ResearchOS/research-os/.local/builds/current-chat-runtime-assets-20261012'
$env:RESEARCHOS_WEB_DIR = 'D:/作品集/ResearchOS/research-os/apps/web/dist'
$results = @()
foreach ($leg in @('missing-assets', 'production-assets')) {
    $dataRoot = 'D:/作品集/ResearchOS/research-os/.local/normal-runtime-host-smoke-' + $leg + '-' + [guid]::NewGuid().ToString('N')
    New-Item -ItemType Directory -Path $dataRoot | Out-Null
    $env:RESEARCHOS_DATA_DIR = $dataRoot
    $env:RESEARCHOS_LISTEN = '127.0.0.1:0'
    $discovery = Join-Path $dataRoot 'discovery.json'
    $arguments = @('--discovery-file', $discovery)
    if ($leg -eq 'production-assets') { $arguments += @('--runtime-assets-dir', $assets) }
    $process = Start-Process -FilePath $binary -ArgumentList $arguments -WorkingDirectory $repo -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $receipts ('attempt13-' + $leg + '-stdout.txt')) -RedirectStandardError (Join-Path $receipts ('attempt13-' + $leg + '-stderr.txt'))
    try {
        $deadline = [DateTime]::UtcNow.AddSeconds(15)
        while (!(Test-Path -LiteralPath $discovery) -and !$process.HasExited -and [DateTime]::UtcNow -lt $deadline) { Start-Sleep -Milliseconds 100 }
        if ($process.HasExited -or !(Test-Path -LiteralPath $discovery)) { throw 'control startup failed' }
        $hostInfo = Get-Content -LiteralPath $discovery -Raw | ConvertFrom-Json
        $pipe = [IO.Pipes.NamedPipeClientStream]::new('.', ('ResearchOSHost-v1-' + $hostInfo.host_instance_id.Substring(5)), [IO.Pipes.PipeDirection]::InOut)
        try {
            $pipe.Connect(5000)
            $request = @{kind='NATIVE_USER_BOOTSTRAP_REQUEST';client_id='offline-smoke';payload=@{}} | ConvertTo-Json -Compress
            $raw = [Text.Encoding]::UTF8.GetBytes($request)
            $pipe.Write($raw, 0, $raw.Length)
            $buffer = [byte[]]::new(8192)
            $length = $pipe.Read($buffer, 0, $buffer.Length)
            $bootstrap = [Text.Encoding]::UTF8.GetString($buffer, 0, $length) | ConvertFrom-Json
            if ($bootstrap.kind -ne 'NATIVE_USER_BOOTSTRAP_RESULT') { throw 'native bootstrap failed' }
        } finally { $pipe.Dispose() }
        $session = Get-Content -LiteralPath (Join-Path $dataRoot 'host/session.json') -Raw | ConvertFrom-Json
        $headers = @{Authorization=('Bearer ' + $session.token)}
        $envelope = @{protocol_version='researchos-client/2';command_id=[guid]::NewGuid().ToString('N');client_id='offline-smoke';project_id=$null;session_id=$null;expected_revision=$null;writer_epoch=$null;method='host.configure';payload=@{config_revision=1;provider_id='ollama';base_url='http://127.0.0.1:1/v1';model_id='qwen3:4b-instruct';credential_ref=$null}}
        $configured = Invoke-RestMethod -Method Post -Uri ($hostInfo.url + '/v2/command') -Headers $headers -ContentType 'application/json' -Body ($envelope | ConvertTo-Json -Depth 5 -Compress) -TimeoutSec 10
        if ($configured.status -ne 'COMPLETED') { throw 'ordinary host.configure failed' }
        $envelope.command_id = [guid]::NewGuid().ToString('N'); $envelope.method = 'host.status'; $envelope.payload = @{}
        $status = Invoke-RestMethod -Method Post -Uri ($hostInfo.url + '/v2/command') -Headers $headers -ContentType 'application/json' -Body ($envelope | ConvertTo-Json -Depth 5 -Compress) -TimeoutSec 10
        if ($status.status -ne 'COMPLETED' -or $status.result.config_revision -ne 1) { throw 'host.status did not preserve configuration' }
        $results += @{leg=$leg;data_root=$dataRoot;binary_sha256=(Get-FileHash -LiteralPath $binary -Algorithm SHA256).Hash.ToLowerInvariant();native_os_bootstrap='PASSED';ordinary_configure='COMPLETED';config_revision=$status.result.config_revision;configured_models=@($status.result.model_configurations).Count;no_project_created=$true;model_endpoint='unreachable-loopback-fixture';qualification='NOT_RUN'}
    } finally {
        if (!$process.HasExited) { $process.Kill(); $process.WaitForExit(10000) | Out-Null }
        $process.Dispose()
        $session = $null; $headers = $null
    }
}
$results | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $receipts 'control-offline-smoke.json') -Encoding utf8NoBOM
$results | Select-Object leg,native_os_bootstrap,ordinary_configure,config_revision,configured_models,qualification | ConvertTo-Json -Depth 3


