$ErrorActionPreference = 'Continue'
$ownE='D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\qualification_failure_b_revision03_source_codex\20261015-current-chat'
$scope='D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\resume_cp398_codex\20261015-current-chat\continuation-cp522\qualification-failure-B-revision03-source-scope.json'
$paths=@('D:\作品集\ResearchOS\AGENTS.md','D:\作品集\ResearchOS\research-os\AGENTS.md',$scope)
$record=[ordered]@{argv=@('pwsh','-NoProfile','-File',(Join-Path $ownE 'CP522-bootstrap.ps1'));cwd=(Get-Location).Path;env=[ordered]@{TMP=$env:TMP;TEMP=$env:TEMP;GOTMPDIR=$env:GOTMPDIR;GOCACHE=$env:GOCACHE;GOPATH=$env:GOPATH};paths=$paths;expectedScopeSha256='6633dc25b4143d95601dd31606ef4649b48779e87a4fb462eabd0233a1658373'}
$record | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $ownE 'CP522-bootstrap-invocation.json') -Encoding utf8
$raw=Join-Path $ownE 'CP522-bootstrap-raw.txt'
Start-Transcript -LiteralPath $raw | Out-Null
try {
  foreach($p in $paths) {
    Write-Output "===== $p ====="
    if(!(Test-Path -LiteralPath $p)){Write-Output 'MISSING'; continue}
    if($p -eq $scope){$sha=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant(); Write-Output "SHA256=$sha"; if($sha -ne '6633dc25b4143d95601dd31606ef4649b48779e87a4fb462eabd0233a1658373'){throw 'SCOPE_HASH_MISMATCH'}}
    Get-Content -LiteralPath $p -Raw -Encoding utf8
  }
  $exit=0
} catch { Write-Error $_; $exit=1 } finally { Stop-Transcript | Out-Null; [ordered]@{exit=$exit;raw=$raw} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $ownE 'CP522-bootstrap-exit.json') -Encoding utf8 }
exit $exit
