[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$t=[IO.Path]::GetFullPath('D:\作品集\ResearchOS\research-os\.local\online-backup-independent-review-20261015-tmp')
$results=@()
foreach($n in @('go-cache','go-tmp')){
  $p=[IO.Path]::GetFullPath((Join-Path $t $n))
  if(-not $p.StartsWith($t+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'cleanup containment failure'}
  $b=(Get-ChildItem -LiteralPath $p -File -Recurse -ErrorAction SilentlyContinue|Measure-Object Length -Sum).Sum
  if(Test-Path -LiteralPath $p){Remove-Item -LiteralPath $p -Recurse -Force}
  $results+=[pscustomobject]@{path=$p;bytes_removed=$b;absent=(-not (Test-Path -LiteralPath $p))}
}
$results|ConvertTo-Json|Set-Content "$PSScriptRoot\cleanup.json" -Encoding utf8
$results|ConvertTo-Json
Get-Content "$PSScriptRoot\005.stderr.txt" -Raw -Encoding utf8
Get-Content "$PSScriptRoot\s04-go-build-info.stdout.raw" -Raw -Encoding utf8
exit 0