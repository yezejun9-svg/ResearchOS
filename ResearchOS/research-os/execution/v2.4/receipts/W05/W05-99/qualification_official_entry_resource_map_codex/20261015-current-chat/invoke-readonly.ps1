param([Parameter(Mandatory=$true)][string]$Group,[Parameter(Mandatory=$true)][string]$RecipeFile)
$ErrorActionPreference='Stop'
$own=$PSScriptRoot
$resolved=[IO.Path]::GetFullPath($RecipeFile)
if(-not $resolved.StartsWith([IO.Path]::GetFullPath($own)+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Recipe must be ownE'}
$recipe=[IO.File]::ReadAllText($resolved)
$invocation=[ordered]@{group=$Group;recipe_file=$resolved;recipe=$recipe;shell='PowerShell';ps_version=$PSVersionTable.PSVersion.ToString();cwd=(Get-Location).Path;environment=@{OutputEncoding=[Console]::OutputEncoding.WebName;policy='No full environment dump; no credentials';native_command_exit_policy='Every native call explicitly prints and records LASTEXITCODE'};at=[DateTimeOffset]::Now.ToString('o');actual_authority=$false;source_C_authority=$false;formal_increment=0}
$invocation|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $own ($Group+'.command.json')) -Encoding utf8
$raw=@();$exitCode=0
try {$raw=@(& $resolved *>&1)} catch {$raw+=($_|Out-String);$exitCode=1}
$rawText=$raw|Out-String -Width 500
[IO.File]::WriteAllText((Join-Path $own ($Group+'.fullraw.txt')),$rawText)
@{group=$Group;exit_code=$exitCode;native_exit_code=$null;native_exits='Recorded per native command in fullraw';raw=($Group+'.fullraw.txt');finished_at=[DateTimeOffset]::Now.ToString('o')}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $own ($Group+'.result.json')) -Encoding utf8
$rawText
exit $exitCode

