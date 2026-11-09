$ErrorActionPreference='Stop'
$e='D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/owned_core_stop_effect_state_revision05_independent_review_codex/20261015-current-chat'
$t=[IO.Path]::GetFullPath('D:/作品集/ResearchOS/research-os/.local/owned-core-stop-r5-independent-review-20261015-tmp')
$removed=@()
foreach($leaf in @('gocache','gotmp','warm-stop-cli.exe')){
$p=[IO.Path]::GetFullPath((Join-Path $t $leaf))
if(-not $p.StartsWith($t+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'outside task temporary root'}
if(Test-Path -LiteralPath $p){$removed+=@{path=$p;bytes=(Get-ChildItem -LiteralPath $p -File -Recurse | Measure-Object Length -Sum).Sum};Remove-Item -LiteralPath $p -Recurse -Force}
}
@{removed=$removed;retained='D build fixture images and original three data/operation fixture roots; C copied images; evidence and archived operations';actual_data_touched=$false} | ConvertTo-Json -Depth 8 | Set-Content -Encoding utf8 "$e/cleanup.json"
Get-Content "$e/cleanup.json"
