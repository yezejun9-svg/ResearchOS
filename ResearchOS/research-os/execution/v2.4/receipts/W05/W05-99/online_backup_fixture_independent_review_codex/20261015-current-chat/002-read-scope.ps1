$ErrorActionPreference='Stop'
$paths=@('D:\AGENTS.md','D:\作品集\AGENTS.md','D:\作品集\ResearchOS\AGENTS.md','D:\作品集\ResearchOS\research-os\AGENTS.md')
foreach($p in $paths){if(Test-Path -LiteralPath $p){Write-Output "FILE $p";Get-Content -LiteralPath $p -Raw}}
$scope='D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\resume_cp398_codex\20261015-current-chat\continuation-cp522\online-backup-fixture-independent-review-scope.json'
$hash=(Get-FileHash -LiteralPath $scope -Algorithm SHA256).Hash.ToLowerInvariant()
Write-Output "SCOPE_SHA256 $hash"
if($hash -ne 'b6cfd9fdd2406ae771e6a8949dedba611dc0764bd4671747c49a654c208c45a3'){throw 'scope hash mismatch'}
Get-Content -LiteralPath $scope -Raw
