$ErrorActionPreference='Stop'
$b='C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-backend-author'
$files=@()
$files+=@(Get-ChildItem -LiteralPath $b -File | Where-Object { $_.Name -match '^(source-\d+.*\.json|install-source-\d+\.ps1|attempt-\d+.*\.ps1|freeze\.ps1|diagnostics\.json)$' })
$files+=@(Get-ChildItem -LiteralPath ($b+'/final') -File -Recurse)
foreach($i in 1..5){$files+=@(Get-ChildItem -LiteralPath ($b+'/attempt-'+$i.ToString('00')) -File)}
$files+=@(Get-ChildItem -LiteralPath ($b+'/attempt-06-compatibility') -File)
$rows=@($files | Sort-Object FullName -Unique | ForEach-Object {[ordered]@{relative_path=[IO.Path]::GetRelativePath($b,$_.FullName).Replace('\','/');sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant();bytes=$_.Length}})
$index=[ordered]@{schema='researchos.product-v1-archive-file-list.v1';base_directory=$b;excluded=@('**/gocache/**','**/tmp/**','module cache','temporary helper executables');original_c_preserved=$true;files=$rows}
[IO.File]::WriteAllText(($b+'/archive-file-list.json'),($index|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
[ordered]@{files=$rows.Count;bytes=($rows|Measure-Object bytes -Sum).Sum;index_sha256=(Get-FileHash -LiteralPath ($b+'/archive-file-list.json') -Algorithm SHA256).Hash.ToLowerInvariant()}|ConvertTo-Json
