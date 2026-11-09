$ErrorActionPreference='Stop'
$e=$PSScriptRoot
$parent='D:\作品集\ResearchOS\research-os\.local\worktrees\profile-result-build-20261014\.local\desktop-wire-negative'
$parentFull=[IO.Path]::GetFullPath($parent)
$roots=@(Get-ChildItem -LiteralPath (Join-Path $e 'package-cases') -Filter 'negative-stage-*.jsonl' -File | ForEach-Object {
    $line=Get-Content -LiteralPath $_.FullName -TotalCount 1 | ConvertFrom-Json
    if($line.step -ne 'exclusive-short-root'){throw 'UNEXPECTED_STAGE'}
    [IO.Path]::GetFullPath($line.root)
} | Sort-Object -Unique)
$plan=@()
foreach($root in $roots){
    if([IO.Path]::GetDirectoryName($root) -ne $parentFull -or [IO.Path]::GetFileName($root) -notmatch '^[0-9a-f-]{36}$'){throw 'OUT_OF_SCOPE_FIXTURE'}
    if((Get-Item -LiteralPath $root).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'ROOT_ALIAS'}
    $links=@(Get-ChildItem -LiteralPath $root -Recurse -Force | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })
    foreach($link in $links){
        if($link.FullName -ne (Join-Path $root 'resources\client-wire')){throw 'UNEXPECTED_ALIAS'}
        if([IO.Path]::GetFullPath($link.Target) -ne (Join-Path $root 'resources\client-wire-held-original')){throw 'ALIAS_TARGET_OUT_OF_SCOPE'}
    }
    $plan+=@{root=$root; links=@($links | ForEach-Object {$_.FullName})}
}
@{at=[DateTime]::UtcNow.ToString('o'); count=$plan.Count; paths=$plan} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $e 'cleanup-plan.json') -Encoding utf8NoBOM
foreach($item in $plan){
    foreach($link in $item.links){Remove-Item -LiteralPath $link -Force}
    Remove-Item -LiteralPath $item.root -Recurse -Force
    if(Test-Path -LiteralPath $item.root){throw 'FIXTURE_REMAINS'}
}
$temp=Join-Path $e 'package-cases\temp'
if((Test-Path -LiteralPath $temp) -and @(Get-ChildItem -LiteralPath $temp -Force).Count -eq 0){Remove-Item -LiteralPath $temp}
@{at=[DateTime]::UtcNow.ToString('o'); removed=$plan.Count; remaining=@($roots | Where-Object {Test-Path -LiteralPath $_}); scope='only fixture roots from this review run'} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $e 'cleanup-result.json') -Encoding utf8NoBOM
Write-Output "CLEANUP_PASS count=$($plan.Count)"
