$ErrorActionPreference='Stop'
$R='D:\作品集\ResearchOS\research-os'
$W='D:\作品集\ResearchOS\research-os\.local\worktrees\qualification-failure-b-20261015'
$c=Get-Content -Raw "$R\execution\v2.4\receipts\W05\W05-99\resume_cp398_codex\20261015-current-chat\continuation-cp512\qualification-failure-B-source-scope.json"|ConvertFrom-Json
$c.design_refs+@($c.C_write_shape_ref) | ForEach-Object {Get-FileHash "$R\$($_.path)";Get-Content -Raw "$R\$($_.path)"}
git -C $W rev-parse HEAD 'HEAD^{tree}'
git -C $W status --porcelain=v1
git -C $W diff --stat $c.base_commit HEAD
Get-Content -Raw "$W\internal\domain\runtime_qualification_failure_windows.go"
