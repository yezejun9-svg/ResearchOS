param([Parameter(Mandatory=$true)][string]$Id)
$ErrorActionPreference='Stop'
$utf8=[Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding=$utf8
$recipePath=Join-Path $PSScriptRoot ($Id+'.recipe.json')
$r=Get-Content -LiteralPath $recipePath -Raw -Encoding utf8 | ConvertFrom-Json
$old=(Get-Location).Path
$started=[DateTime]::UtcNow.ToString('o')
$vars=[ordered]@{}
foreach($p in $r.environment.PSObject.Properties){[Environment]::SetEnvironmentVariable($p.Name,[string]$p.Value,'Process');$vars[$p.Name]=[string]$p.Value}
$vars.PSVersion=$PSVersionTable.PSVersion.ToString()
$exitCode=1
try { Set-Location -LiteralPath $r.cwd; & $r.executable @($r.argv) 1> (Join-Path $PSScriptRoot ($Id+'.stdout.txt')) 2> (Join-Path $PSScriptRoot ($Id+'.stderr.txt')); $exitCode=$LASTEXITCODE } catch { [IO.File]::AppendAllText((Join-Path $PSScriptRoot ($Id+'.stderr.txt')),($_ | Out-String),$utf8) } finally {Set-Location -LiteralPath $old}
$record=[ordered]@{id=$Id;recipe=$recipePath;recipeSHA256=(Get-FileHash -LiteralPath $recipePath -Algorithm SHA256).Hash.ToLowerInvariant();executable=$r.executable;argv=$r.argv;cwd=$r.cwd;environment=$vars;started=$started;finished=[DateTime]::UtcNow.ToString('o');nativeExit=$exitCode}
[IO.File]::WriteAllText((Join-Path $PSScriptRoot ($Id+'.command.json')),($record | ConvertTo-Json -Depth 15),$utf8)
Get-Content -LiteralPath (Join-Path $PSScriptRoot ($Id+'.stdout.txt')) -Raw -Encoding utf8
Get-Content -LiteralPath (Join-Path $PSScriptRoot ($Id+'.stderr.txt')) -Raw -Encoding utf8
exit $exitCode
