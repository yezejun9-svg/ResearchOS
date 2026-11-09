$ErrorActionPreference='Stop'
$E='D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\qualification_failure_b_independent_review_codex\20261015-current-chat'
$files=@()
Get-ChildItem -LiteralPath $E -File | Where-Object {$_.Name -ne 'FINAL-manifest.json' -and $_.Name -notlike 'r23-*'} | Sort-Object Name | ForEach-Object {
$files+=@{path=$_.Name;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLower();bytes=$_.Length}
}
$manifest=@{schema='researchos.qualification-failure-B-independent-source-review-manifest.v1';at=(Get-Date).ToUniversalTime().ToString('o');status='NEEDS_CHANGES';candidate='75e5257c19b2e21e6cabd5e912e2ac6a3e2fe603';tree='ba3f9d4c101df39ab17856158d5fc72a9f0600ce';base='f48fca0e4013bda19913a34d91da0cd23157a08b';formal_increment=0;actual_authority=$false;source_acceptance=$false;files=$files;excluded_self_envelope=@('FINAL-manifest.json','r23-seal-manifest.recipe.ps1','r23-seal-manifest.raw.txt','r23-seal-manifest.result.json');temporary_root_removed=$true;source_guard='final-source-guard.json'}
$manifest|ConvertTo-Json -Depth 10|Set-Content -Encoding utf8 "$E\FINAL-manifest.json"
$bad=@($files|Where-Object {(Get-FileHash -LiteralPath "$E\$($_.path)").Hash.ToLower() -ne $_.sha256})
if($bad.Count -ne 0){throw 'Final manifest verify mismatch'}
@{files=$files.Count;mismatches=$bad.Count;manifest_sha256=(Get-FileHash -LiteralPath "$E\FINAL-manifest.json").Hash.ToLower();review_sha256=(Get-FileHash -LiteralPath "$E\review.json").Hash.ToLower();status='NEEDS_CHANGES'}|ConvertTo-Json
