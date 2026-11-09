$ErrorActionPreference = 'Stop'
$scope = 'D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\resume_cp398_codex\20261015-current-chat\continuation-cp526\host-stored-finalpath-source-diagnosis-scope.json'
Get-FileHash -LiteralPath $scope -Algorithm SHA256
Get-Content -LiteralPath $scope -Raw -Encoding UTF8