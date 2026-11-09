$ErrorActionPreference='Stop'
$utf8=[Text.UTF8Encoding]::new($false)
$root='D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/qualification_failure_b_revision03_independent_review_codex/20261015-current-chat'
foreach($i in 1..14) {
 $id='B-r3-review-'+$i.ToString('000')
 $result=Get-Content -LiteralPath (Join-Path $root ($id+'.result.json')) -Raw | ConvertFrom-Json
 $expected=if($i -eq 10){1}else{0}
 if($result.nativeExit -ne $expected -or $null -ne $result.runnerFailure){throw "unexpected native result $id"}
 foreach($pair in @(@('stdout.raw','stdoutSHA256'),@('stderr.raw','stderrSHA256'),@('invocation.json','invocationSHA256'))) {
  $actual=(Get-FileHash -LiteralPath (Join-Path $root ($id+'.'+$pair[0])) -Algorithm SHA256).Hash.ToLowerInvariant()
  if($actual -ne $result.($pair[1])){throw "capture hash changed $id $pair"}
 }
 $inv=Get-Content -LiteralPath (Join-Path $root ($id+'.invocation.json')) -Raw | ConvertFrom-Json
 if((Get-FileHash -LiteralPath $inv.recipe -Algorithm SHA256).Hash.ToLowerInvariant() -ne $inv.recipeSHA256){throw "recipe changed $id"}
}
$pins=Get-Content -LiteralPath (Join-Path $root 'final-source-pins.json') -Raw|ConvertFrom-Json
foreach($pin in $pins) {
 $path=Join-Path 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r3-20261015' $pin.path
 if((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $pin.sha256 -or (Get-Item -LiteralPath $path).Length -ne $pin.bytes){throw "source drift $path"}
}
$scope=Get-Content -LiteralPath 'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp525/B-r3-independent-review-scope.json' -Raw | ConvertFrom-Json
if((Get-FileHash -LiteralPath 'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp525/B-r3-independent-review-scope.json' -Algorithm SHA256).Hash.ToLowerInvariant() -ne '26e8d36f95e648a862f73a46a69bdcea131494a757abd88a512b6c68d161d8a6'){throw 'scope drift'}
foreach($pin in $scope.inputs) {
 $path=Join-Path 'D:/作品集/ResearchOS/research-os' $pin.path
 if((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $pin.sha256 -or (Get-Item -LiteralPath $path).Length -ne $pin.bytes){throw "input drift $path"}
}
$originals=@{
 'original-independent_b2_domain_windows_test.go'='c4aa9f2639c3a731406c5821aa14b9018de0867bdc844b8e3942976571a06fee'
 'original-independent_b2_adapter_windows_test.go'='451297c708559a9150257e64bb633f533185a03b9fc09547a2c9ddb71c6ca4c6'
 'original-independent_b2_followup_windows_test.go'='3d675956d4dfc77b7955eb0530fcef120c4d69cd1d2d0701cd68acfe1928dbe4'
}
foreach($name in $originals.Keys){if((Get-FileHash -LiteralPath (Join-Path $root $name) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $originals[$name]){throw "original overlay drift $name"}}
$head=git -C 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r3-20261015' rev-parse HEAD
if($LASTEXITCODE -ne 0 -or $head -ne 'fec4a4d7bc8aa4ce6ee1e0f9a7da024bd528ca3f'){throw 'HEAD mismatch'}
$tree=git -C 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r3-20261015' rev-parse 'HEAD^{tree}'
if($LASTEXITCODE -ne 0 -or $tree -ne '730be49f57988da8be32af27225848690d202e63'){throw 'tree mismatch'}
$dirty=git -C 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r3-20261015' status --porcelain --untracked-files=all
if($LASTEXITCODE -ne 0 -or $dirty){throw 'source worktree not clean'}
[ordered]@{priorCapturedNativeCommands=14;expectedPriorNativeFailures=@('B-r3-review-010');verifiedSourcePins=$pins.Count;verifiedInputs=$scope.inputs.Count;verifiedOriginalOverlays=$originals.Count;candidate=$head;tree=$tree;sourceClean=$true;actual=$false;formalIncrement=0} | ConvertTo-Json -Depth 8

