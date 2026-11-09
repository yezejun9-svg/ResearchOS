$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
foreach($p in @('D:/作品集/ResearchOS/AGENTS.md','D:/作品集/ResearchOS/research-os/AGENTS.md','D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp525/B-r3-independent-review-scope.json')){
 if(Test-Path -LiteralPath $p){'FILE '+$p;'SHA256 '+(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant();Get-Content -LiteralPath $p -Raw -Encoding utf8}else{'ABSENT '+$p}
}
exit 0
