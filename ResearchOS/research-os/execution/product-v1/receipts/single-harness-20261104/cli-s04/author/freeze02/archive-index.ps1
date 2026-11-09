$ErrorActionPreference='Stop'
$b='C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-cli-s04-author'
$files=@(Get-ChildItem -LiteralPath $b -File|Where-Object{$_.Name -ne 'archive-file-list.json'})
$files+=@(Get-ChildItem -LiteralPath ($b+'/final') -File -Recurse)
foreach($dir in @('attempt-01','attempt-02','attempt-03')){$files+=@(Get-ChildItem -LiteralPath ($b+'/'+$dir) -File)}
$rows=@($files|Sort-Object FullName -Unique|ForEach-Object{[ordered]@{relative_path=[IO.Path]::GetRelativePath($b,$_.FullName).Replace('\','/');sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant();bytes=$_.Length}})
$total=0L;foreach($row in $rows){$total+=[int64]$row['bytes']}
$index=[ordered]@{schema='researchos.product-v1-archive-file-list.v1';base_directory=$b;excluded=@('**/gocache/**','**/tmp/**','module cache','temporary executables');original_c_preserved=$true;total_bytes=$total;files=$rows}
[IO.File]::WriteAllText(($b+'/archive-file-list.json'),($index|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
@('final/freeze.json','final/summary.json','diagnostics.json','final/source-manifest.json','archive-file-list.json')|ForEach-Object{[ordered]@{path=$_;sha256=(Get-FileHash -LiteralPath ($b+'/'+$_) -Algorithm SHA256).Hash.ToLowerInvariant()}}|ConvertTo-Json -Depth 4
