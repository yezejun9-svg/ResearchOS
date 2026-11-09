$ErrorActionPreference='Stop'
$workspaceRoot=(Resolve-Path -LiteralPath 'D:/作品集/ResearchOS/research-os').Path
$taskCacheTargets=@(
 'D:/作品集/ResearchOS/research-os/.local/owned-core-stop-effect-state-r5-20261015-tmp/gocache',
 'D:/作品集/ResearchOS/research-os/.local/online-backup-fixture-qualification-20261015-tmp/go-cache'
)
$checked=@()
foreach($taskCacheTarget in $taskCacheTargets){
 $resolvedTarget=(Resolve-Path -LiteralPath $taskCacheTarget).Path
 if(-not $resolvedTarget.StartsWith($workspaceRoot+'\.local\',[StringComparison]::OrdinalIgnoreCase)){throw 'Cache target escaped workspace .local'}
 if($resolvedTarget -notmatch '\\(owned-core-stop-effect-state-r5-20261015-tmp\\gocache|online-backup-fixture-qualification-20261015-tmp\\go-cache)$'){throw 'Unexpected exact cache path'}
 $currentTarget=Get-Item -LiteralPath $resolvedTarget
 while($currentTarget.FullName -ne $workspaceRoot){
  if(($currentTarget.Attributes -band [IO.FileAttributes]::ReparsePoint)-ne 0){throw 'Reparse ancestor refused'}
  $currentTarget=$currentTarget.Parent
 }
 $cacheItems=@(Get-ChildItem -LiteralPath $resolvedTarget -Recurse -Force)
 if(@($cacheItems|Where-Object {($_.Attributes -band [IO.FileAttributes]::ReparsePoint)-ne 0}).Count -ne 0){throw 'Reparse descendant refused'}
 $cacheBytes=($cacheItems|Where-Object {-not $_.PSIsContainer}|Measure-Object -Property Length -Sum).Sum
 $checked+=@{path=$resolvedTarget;bytes=$cacheBytes;file_count=@($cacheItems|Where-Object {-not $_.PSIsContainer}).Count}
}
$checked|ConvertTo-Json -Depth 5
foreach($taskCacheTarget in $checked){
 Remove-Item -LiteralPath $taskCacheTarget.path -Recurse -Force
 if(Test-Path -LiteralPath $taskCacheTarget.path){throw 'Cache deletion incomplete'}
}
[IO.DriveInfo]::new('D').AvailableFreeSpace
