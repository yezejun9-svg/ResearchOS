$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
$toolsRoot = Join-Path $repoRoot '.local\tools'
$targetRoot = Join-Path $toolsRoot 'go1.27.1'
$goBinary = Join-Path $targetRoot 'go\bin\go.exe'
$expectedHash = 'a3911b5e0e1b1053f25ed0675f4c1c6aad1e2bfcf253df2b9be4caabd2edd95d'
$downloadUrl = 'https://go.dev/dl/go1.27.1.windows-amd64.zip'
$started = [DateTime]::UtcNow.ToString('o')
if (-not (Test-Path -LiteralPath $goBinary)) {
    New-Item -ItemType Directory -Path $targetRoot -Force | Out-Null
    $archivePath = Join-Path $toolsRoot 'go1.27.1.windows-amd64.zip'
    if (-not (Test-Path -LiteralPath $archivePath)) {
        Invoke-WebRequest -Uri $downloadUrl -OutFile $archivePath -TimeoutSec 300
    }
    if ((Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLower() -ne $expectedHash) {
        throw 'Go archive integrity check failed; archive retained for diagnosis'
    }
    Expand-Archive -LiteralPath $archivePath -DestinationPath $targetRoot -Force
    Remove-Item -LiteralPath $archivePath
}
$actualVersion = & $goBinary version
if ($LASTEXITCODE -ne 0 -or $actualVersion -ne 'go version go1.27.1 windows/amd64') {
    throw 'Pinned Go version verification failed'
}
$evidenceDir = Join-Path $repoRoot 'execution\toolchains'
New-Item -ItemType Directory -Path $evidenceDir -Force | Out-Null
@{ tool='go'; version='1.27.1'; platform='windows/amd64'; executable=$goBinary; source=$downloadUrl;
   archive_sha256=$expectedHash; executable_sha256=(Get-FileHash -LiteralPath $goBinary -Algorithm SHA256).Hash.ToLower();
   started_at=$started; ended_at=[DateTime]::UtcNow.ToString('o'); verification_command=@($goBinary,'version');
   exit_code=$LASTEXITCODE; stdout=$actualVersion; global_path_modified=$false
} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $evidenceDir 'go.json') -Encoding utf8
$actualVersion
