param([Parameter(Mandatory=$true)][string]$Id)
$ErrorActionPreference='Stop'
$utf8=[Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding=$utf8
$rpath=Join-Path $PSScriptRoot ($Id+'.recipe.json')
$r=Get-Content -LiteralPath $rpath -Raw -Encoding utf8|ConvertFrom-Json
$started=[DateTime]::UtcNow.ToString('o')
$vars=[ordered]@{PSVersion=$PSVersionTable.PSVersion.ToString()}
foreach($p in $r.environment.PSObject.Properties){[Environment]::SetEnvironmentVariable($p.Name,[string]$p.Value,'Process');$vars[$p.Name]=[string]$p.Value}
$exitCode=1
Set-Location -LiteralPath $r.cwd
try { & $r.executable @($r.argv) 1> (Join-Path $PSScriptRoot ($Id+'.stdout.txt')) 2> (Join-Path $PSScriptRoot ($Id+'.stderr.txt'));$exitCode=$LASTEXITCODE }catch{[IO.File]::AppendAllText((Join-Path $PSScriptRoot ($Id+'.stderr.txt')),($_|Out-String),$utf8)}
$rec=[ordered]@{id=$Id;recipe=$rpath;recipeSHA256=(Get-FileHash -LiteralPath $rpath -Algorithm SHA256).Hash.ToLowerInvariant();executable=$r.executable;argv=$r.argv;cwd=$r.cwd;environment=$vars;started=$started;finished=[DateTime]::UtcNow.ToString('o');nativeExit=$exitCode;postCapture='This prewritten runner generates command-index and FINAL-manifest after raw/native capture closes.'}
[IO.File]::WriteAllText((Join-Path $PSScriptRoot ($Id+'.command.json')),($rec|ConvertTo-Json -Depth 20),$utf8)
Get-Content -LiteralPath (Join-Path $PSScriptRoot ($Id+'.stdout.txt')) -Raw -Encoding utf8
Get-Content -LiteralPath (Join-Path $PSScriptRoot ($Id+'.stderr.txt')) -Raw -Encoding utf8
if($exitCode -ne 0){exit $exitCode}
$commands=@()
foreach($file in Get-ChildItem -LiteralPath $PSScriptRoot -Filter '*.command.json' -File|Sort-Object Name){
 $c=Get-Content -LiteralPath $file.FullName -Raw -Encoding utf8|ConvertFrom-Json
 $tag=$c.id
 if(!$tag){$tag=$c.commandId}
 $parts=@()
 foreach($suffix in @('.command.json','.recipe.json','.ps1','.stdout.txt','.stderr.txt')){
  $path=Join-Path $PSScriptRoot ($tag+$suffix)
  if(Test-Path -LiteralPath $path){$parts+=[ordered]@{path=[IO.Path]::GetFileName($path);sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant();bytes=(Get-Item -LiteralPath $path).Length}}
 }
 $native=$c.nativeExit;if($tag -eq 'B-r2-review-001'){$native=$c.exitCode}
 $commands+=[ordered]@{id=$tag;nativeExit=$native;artifacts=$parts}
}
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'command-index.json'),([ordered]@{schema='researchos.B-r2-independent-command-index.v1';count=$commands.Count;commands=$commands;bootstrapMetadataLimit='See diagnostic-ledger.json; original bootstrap recipe/script retained separately.'}|ConvertTo-Json -Depth 20),$utf8)
$payload=@()
foreach($file in Get-ChildItem -LiteralPath $PSScriptRoot -File|Sort-Object Name){if($file.Name -ne 'FINAL-manifest.json'){$payload+=[ordered]@{path=$file.Name;sha256=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant();bytes=$file.Length}}}
$manifest=[ordered]@{schema='researchos.B-r2-independent-review-final-manifest.v1';status='NEEDS_CHANGES';candidate='1d3cc504da79df5bf0f69755011738d5adb827b0';tree='be0c58bc3d0d103434663d53bf4b03d94ad25580';scopeSHA256='c2759670490545bbbdcc8c772998b2f5420e3ebf0281e6e08bd6f822d1d640f2';owner='codex:/root/qualification_failure_b_r2_review';frozenAt=[DateTime]::UtcNow.ToString('o');formal_increment=0;actual_authority=$false;source_acceptance=$false;findings=@('B-r2-F01','B-r2-F02');command_count=$commands.Count;payload_file_count=$payload.Count;payload_files=$payload;selfExclusion='Only FINAL-manifest.json excludes its own hash; all closed command captures, recipes, overlays, reports and runner files are included.'}
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'FINAL-manifest.json'),($manifest|ConvertTo-Json -Depth 30),$utf8)
'FINAL_MANIFEST_SHA256 '+(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'FINAL-manifest.json') -Algorithm SHA256).Hash.ToLowerInvariant()
'FROZEN_PAYLOAD_FILES '+$payload.Count
'COMMAND_COUNT '+$commands.Count
exit 0
