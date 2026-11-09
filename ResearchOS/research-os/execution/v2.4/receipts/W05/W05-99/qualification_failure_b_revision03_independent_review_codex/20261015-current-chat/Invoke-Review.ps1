param([Parameter(Mandatory=$true)][string]$Id)
$ErrorActionPreference='Stop'
$utf8=[Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding=$utf8
$recipePath=Join-Path $PSScriptRoot ($Id+'.recipe.json')
$rawRecipe=[IO.File]::ReadAllText($recipePath,$utf8)
$recipe=$rawRecipe|ConvertFrom-Json
$vars=[ordered]@{PSVersion=$PSVersionTable.PSVersion.ToString()}
foreach($p in $recipe.environment.PSObject.Properties){[Environment]::SetEnvironmentVariable($p.Name,[string]$p.Value,'Process');$vars[$p.Name]=[string]$p.Value}
$exe=(Get-Command -Name $recipe.executable -CommandType Application -ErrorAction Stop|Select-Object -First 1).Source
$inv=[ordered]@{schema='researchos.independent-native-invocation.v1';id=$Id;recipe=$recipePath;recipeSHA256=(Get-FileHash -LiteralPath $recipePath -Algorithm SHA256).Hash.ToLowerInvariant();argv=@($exe)+@($recipe.argv);cwd=$recipe.cwd;environment=$vars;inheritedEnvironment='not exhaustively captured; no secret enumeration';started=[DateTime]::UtcNow.ToString('o');runnerSHA256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()}
[IO.File]::WriteAllText((Join-Path $PSScriptRoot ($Id+'.invocation.json')),($inv|ConvertTo-Json -Depth 20),$utf8)
$stdout=Join-Path $PSScriptRoot ($Id+'.stdout.raw')
$stderr=Join-Path $PSScriptRoot ($Id+'.stderr.raw')
$exitCode=$null;$failure=$null
$old=(Get-Location).Path
try {Set-Location -LiteralPath $recipe.cwd;& $exe @($recipe.argv) 1> $stdout 2> $stderr;$exitCode=$LASTEXITCODE}
catch {$failure=$_|Out-String;[IO.File]::AppendAllText($stderr,$failure,$utf8)}
finally {Set-Location -LiteralPath $old}
if(!(Test-Path -LiteralPath $stdout)){[IO.File]::WriteAllText($stdout,'',$utf8)}
if(!(Test-Path -LiteralPath $stderr)){[IO.File]::WriteAllText($stderr,'',$utf8)}
$result=[ordered]@{id=$Id;nativeExit=$exitCode;runnerFailure=$failure;finished=[DateTime]::UtcNow.ToString('o');invocationSHA256=(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot ($Id+'.invocation.json')) -Algorithm SHA256).Hash.ToLowerInvariant();stdoutSHA256=(Get-FileHash -LiteralPath $stdout -Algorithm SHA256).Hash.ToLowerInvariant();stderrSHA256=(Get-FileHash -LiteralPath $stderr -Algorithm SHA256).Hash.ToLowerInvariant()}
[IO.File]::WriteAllText((Join-Path $PSScriptRoot ($Id+'.result.json')),($result|ConvertTo-Json -Depth 15),$utf8)
Get-Content -LiteralPath $stdout -Raw -Encoding utf8
Get-Content -LiteralPath $stderr -Raw -Encoding utf8
if($null -eq $exitCode){exit 1}
exit $exitCode
