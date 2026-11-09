$ErrorActionPreference='Stop'
Get-Content -LiteralPath (Join-Path $PSScriptRoot 'B-r2-review-018.command.json') -Raw -Encoding utf8
rg -n '^func Hash|^func Digest|^func Bytes' 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r2-20261015/internal/domain'
$code=$LASTEXITCODE
'NATIVE_HASH_SEARCH_EXIT '+$code
if($code -ne 0){exit $code}
Get-ChildItem -LiteralPath $PSScriptRoot -Filter '*.command.json' -File | Sort-Object Name | ForEach-Object {
 $c=Get-Content -LiteralPath $_.FullName -Raw -Encoding utf8|ConvertFrom-Json
 [ordered]@{file=$_.Name;id=$c.id;commandId=$c.commandId;nativeExit=$c.nativeExit;bootstrapExit=$c.exitCode}|ConvertTo-Json -Compress
}
exit 0
