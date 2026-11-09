$ErrorActionPreference='Stop'
$r='D:\作品集\ResearchOS\research-os'
rg --files (Join-Path $r 'execution\v2.4\receipts\W05\W05-99') -g 'final-v12-additive-seal.json' -g '*v12*manifest*' -g 'final-v12-six-source.patch'
"NATIVE_EXIT=$LASTEXITCODE"