$ErrorActionPreference='Stop'
$utf8=[Text.UTF8Encoding]::new($false)
$root=$PSScriptRoot
$recipePath=Join-Path $root 'freeze-controller.recipe.json'
$inv=[ordered]@{schema='researchos.independent-freeze-controller-invocation.v1';recipe=$recipePath;recipeSHA256=(Get-FileHash -LiteralPath $recipePath -Algorithm SHA256).Hash.ToLowerInvariant();script=$PSCommandPath;scriptSHA256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant();cwd=(Get-Location).Path;PSVersion=$PSVersionTable.PSVersion.ToString();started=[DateTime]::UtcNow.ToString('o');nativeChild='B-r3-review-015';transportOutput='informational; all child native evidence closed before manifest creation'}
[IO.File]::WriteAllText((Join-Path $root 'freeze-controller.invocation.json'),($inv|ConvertTo-Json -Depth 12),$utf8)
& (Join-Path $root 'Invoke-Review.ps1') -Id B-r3-review-015
if($LASTEXITCODE -ne 0){throw 'final native validation failed'}
function FilePin([string]$path) {
 $f=Get-Item -LiteralPath $path
 [ordered]@{path=$f.Name;bytes=$f.Length;sha256=(Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}
}
$commands=@(foreach($i in 1..15){
 $id='B-r3-review-'+$i.ToString('000')
 $recipe=Get-Content -LiteralPath (Join-Path $root ($id+'.recipe.json')) -Raw|ConvertFrom-Json
 $result=Get-Content -LiteralPath (Join-Path $root ($id+'.result.json')) -Raw|ConvertFrom-Json
 [ordered]@{id=$id;purpose=$recipe.purpose;nativeExit=$result.nativeExit;files=@(foreach($suffix in @('recipe.json','invocation.json','stdout.raw','stderr.raw','result.json')){FilePin (Join-Path $root ($id+'.'+$suffix))})}
})
$index=[ordered]@{schema='researchos.independent-command-index.v1';capturedNativeCommands=$commands.Count;nativeFailures=@($commands|Where-Object{$_.nativeExit -ne 0}|ForEach-Object{$_.id});separateCaptureGap='context-resume-diagnostic.json';diagnosticLedger='diagnostic-ledger.jsonl';commands=$commands;scope='native child streams, excluding informational finalizer tool transport'}
[IO.File]::WriteAllText((Join-Path $root 'command-index.json'),($index|ConvertTo-Json -Depth 25),$utf8)
$announcement='B-r3 REVIEW FROZEN: PASS_WITH_LIMITS; candidate fec4a4d7bc8aa4ce6ee1e0f9a7da024bd528ca3f; actual=false; formalIncrement=0.'
[IO.File]::WriteAllText((Join-Path $root 'freeze-announcement.txt'),$announcement,$utf8)
$exclusions=@('FINAL-manifest.json','FINAL-seal.json')
$files=@(Get-ChildItem -LiteralPath $root -File|Where-Object{$_.Name -notin $exclusions}|Sort-Object Name|ForEach-Object{FilePin $_.FullName})
$manifest=[ordered]@{schema='researchos.independent-review-final-manifest.v1';candidate='fec4a4d7bc8aa4ce6ee1e0f9a7da024bd528ca3f';tree='730be49f57988da8be32af27225848690d202e63';verdict='PASS_WITH_LIMITS';closedAt=[DateTime]::UtcNow.ToString('o');files=$files;exclusions=$exclusions;exclusionReason='manifest cannot hash itself; adjacent seal created only after manifest and native streams close';actual=$false;formalIncrement=0;sourceAdoption='Root only'}
$manifestPath=Join-Path $root 'FINAL-manifest.json'
[IO.File]::WriteAllText($manifestPath,($manifest|ConvertTo-Json -Depth 25),$utf8)
foreach($pin in $files){$f=Get-Item -LiteralPath (Join-Path $root $pin.path);if($f.Length -ne $pin.bytes -or (Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash.ToLowerInvariant() -ne $pin.sha256){throw "manifest verification failed $($pin.path)"}}
$seal=[ordered]@{schema='researchos.independent-review-adjacent-seal.v1';manifest=(FilePin $manifestPath);manifestEntryCount=$files.Count;allManifestEntriesVerified=$true;finalNativeEvidence=@(foreach($suffix in @('recipe.json','invocation.json','stdout.raw','stderr.raw','result.json')){FilePin (Join-Path $root ('B-r3-review-015.'+$suffix))});announcement=(FilePin (Join-Path $root 'freeze-announcement.txt'));controllerInvocation=(FilePin (Join-Path $root 'freeze-controller.invocation.json'));finalNativeExit=0;sealedAt=[DateTime]::UtcNow.ToString('o');selfHashPolicy='seal intentionally self-excluded; seal SHA256 emitted as handoff metadata after write';noLaterNativeCommands=$true;actual=$false;formalIncrement=0}
$sealPath=Join-Path $root 'FINAL-seal.json'
[IO.File]::WriteAllText($sealPath,($seal|ConvertTo-Json -Depth 20),$utf8)
Write-Output $announcement
[ordered]@{manifestSHA256=$seal.manifest.sha256;sealSHA256=(Get-FileHash -LiteralPath $sealPath -Algorithm SHA256).Hash.ToLowerInvariant();manifestEntries=$files.Count;commands=$commands.Count;capturedNativeFailures=$index.nativeFailures;verdict='PASS_WITH_LIMITS';actual=$false;formalIncrement=0}|ConvertTo-Json -Depth 8
exit 0

