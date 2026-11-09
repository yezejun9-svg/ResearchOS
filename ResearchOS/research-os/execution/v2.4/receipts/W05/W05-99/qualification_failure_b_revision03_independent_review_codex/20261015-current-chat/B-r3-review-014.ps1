$ErrorActionPreference='Stop'
$stats=@(foreach($id in @('006','008','012')) {
 $p='D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/qualification_failure_b_revision03_independent_review_codex/20261015-current-chat/B-r3-review-'+$id+'.stdout.raw'
 $text=[IO.File]::ReadAllText($p)
 $lines=$text -split "\r?\n"
 $top=@($lines|Where-Object{$_ -match '^--- PASS:'}).Count
 $sub=@($lines|Where-Object{$_ -match '^\s+--- PASS:'}).Count
 $skip=@($lines|Where-Object{$_ -match '--- SKIP:'}).Count
 $fail=@($lines|Where-Object{$_ -match '--- FAIL:'}).Count
 $result=Get-Content -LiteralPath ('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/qualification_failure_b_revision03_independent_review_codex/20261015-current-chat/B-r3-review-'+$id+'.result.json') -Raw | ConvertFrom-Json
 if($result.nativeExit -ne 0 -or $skip -ne 0 -or $fail -ne 0){throw "unexpected test result $id"}
 [ordered]@{id=$id;topLevelPass=$top;subtestPass=$sub;skip=$skip;fail=$fail;nativeExit=$result.nativeExit;stdoutSHA256=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
})
[IO.File]::WriteAllText('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/qualification_failure_b_revision03_independent_review_codex/20261015-current-chat/test-summary.json',($stats|ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
$stats|ConvertTo-Json -Depth 10
$expected=[IO.Path]::GetFullPath('D:/作品集/ResearchOS/research-os/.local/qualification-failure-b-r3-independent-review-20261015-tmp')
$workspace=[IO.Path]::GetFullPath('D:/作品集/ResearchOS/research-os')+[IO.Path]::DirectorySeparatorChar
$resolved=(Resolve-Path -LiteralPath 'D:/作品集/ResearchOS/research-os/.local/qualification-failure-b-r3-independent-review-20261015-tmp' -ErrorAction Stop).Path
if(![string]::Equals($resolved,$expected,[StringComparison]::OrdinalIgnoreCase) -or !$resolved.StartsWith($workspace,[StringComparison]::OrdinalIgnoreCase) -or (Split-Path -Leaf $resolved) -ne 'qualification-failure-b-r3-independent-review-20261015-tmp'){throw 'temporary target guard failed'}
Write-Output ("verified own temporary delete target="+$resolved)
Remove-Item -LiteralPath $resolved -Recurse -Force -ErrorAction Stop
if(Test-Path -LiteralPath $resolved){throw 'own temporary cleanup incomplete'}
[IO.File]::WriteAllText('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/qualification_failure_b_revision03_independent_review_codex/20261015-current-chat/temporary-cleanup.json',([ordered]@{target=$resolved;resolvedBeforeDelete=$true;withinWorkspace=$true;deleted=$true;oldAuthorDeniedTargetTouched=$false;at=[DateTime]::UtcNow.ToString('o')}|ConvertTo-Json),[Text.UTF8Encoding]::new($false))
Write-Output 'own new temporary cache removed; old denied author target untouched'

