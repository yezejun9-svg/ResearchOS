$own=$PSScriptRoot
@{group='Q12';recipe='Seal own CP518 artifacts only; hash all own files except FINAL-manifest.json';shell='PowerShell';cwd=(Get-Location).Path;ps_version=$PSVersionTable.PSVersion.ToString();actual_authority=$false}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $own 'Q12.command.json') -Encoding utf8
[IO.File]::WriteAllText((Join-Path $own 'Q12.fullraw.txt'),'Own artifact sealing only. Static integrity verified Q11; no external enumeration.')
@{group='Q12';exit_code=0;native_exit_code=$null}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $own 'Q12.result.json') -Encoding utf8
$files=@(Get-ChildItem -LiteralPath $own -File|Where-Object Name -ne 'FINAL-manifest.json'|Sort-Object Name|ForEach-Object {@{path=$_.Name;bytes=$_.Length;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLower()}})
@{schema='researchos.CP518.official-entry-resource-final.v1';owner='codex:/root/qualification_boot_design';status='FINITE_READONLY_RESOURCE_COLLECTION_COMPLETE_WITH_GAPS';scope_sha256='eeac5e55ab5df7a60c5361095bd48d50a382cf666888c878f09092ea5751bb9d';actual_authority=$false;source_C_authority=$false;formal_increment=0;author_acceptance=$false;surfaces=15;public_package_members=116;file_ancestor_records=67;mechanism='POTENTIALLY_APPLICABLE_KNOWN_FIXED_FILES_FULL_COVERAGE_UNPROVEN';independent_design_review_required=$true;files=$files}|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $own 'FINAL-manifest.json') -Encoding utf8
(Get-FileHash -LiteralPath (Join-Path $own 'FINAL-manifest.json') -Algorithm SHA256).Hash.ToLower()

