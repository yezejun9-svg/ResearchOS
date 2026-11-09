$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new()
$w='D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-cli-20261104'
$b='C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-cli-s04-author'
$main=Join-Path $w 'apps/cli/main.go';$target=Join-Path $w 'apps/cli/productv1.go'
if((Get-FileHash -LiteralPath $main -Algorithm SHA256).Hash.ToLowerInvariant() -ne 'a55afd3985781a1a2c9342d2bb38cad9b20814c6d03b2976b934ba8d7bf6062f'){throw 'main baseline changed'}
if(Test-Path -LiteralPath $target){throw 'new source already exists'}
$source=[IO.File]::ReadAllText(($b+'/productv1.template.go'))
$schema=[IO.File]::ReadAllText(($b+'/harness.v1.interface.rev2.json'))
$literal=ConvertTo-Json -InputObject $schema -Compress
$source=$source.Replace('@@HARNESS_SCHEMA_LITERAL@@',$literal)
$entry=[IO.File]::ReadAllText($main).Replace("`r`n","`n")
$old=[string][char]9+'case "doctor":'
if($entry.IndexOf($old) -ne $entry.LastIndexOf($old) -or $entry.IndexOf($old) -lt 0){throw 'main branch not unique'}
$entry=$entry.Replace($old,' case "harness":'+"`n"+'  cliHarness(args[1:])'+"`n"+$old)
$help=[string][char]9+[string][char]9+'cliHelpSurface(true)'
$entry=$entry.Replace($help,$help+"`n"+'  diag("harness: readonly native Harness; use researchos harness help")')
[IO.File]::WriteAllText($target,$source,[Text.UTF8Encoding]::new($false))
[IO.File]::WriteAllText($main,$entry,[Text.UTF8Encoding]::new($false))
$pins=@('apps/cli/main.go','apps/cli/productv1.go')|ForEach-Object{[ordered]@{path=$_;sha256=(Get-FileHash -LiteralPath (Join-Path $w $_) -Algorithm SHA256).Hash.ToLowerInvariant()}}
[IO.File]::WriteAllText(($b+'/source-02.result.json'),($pins|ConvertTo-Json -Depth 4),[Text.UTF8Encoding]::new($false))
$pins|ConvertTo-Json
