$ErrorActionPreference='Stop'
$base='D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/prepared_abandonment_v4_independent_review_codex/839da8e0a9014ebd91b3fc57c4e1502c'
$source='D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/prepared_run_abandonment_source_v4_codex/f1cd47ca0f9544bfbe94b51a80d7c492'
$utf8=New-Object System.Text.UTF8Encoding($false)
function Ref([string]$p){$f=Get-Item -LiteralPath $p;[ordered]@{path=$f.FullName;bytes=$f.Length;sha256=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}}
$seen=@{}
function Check($r){$a=Ref $r.path;if($a.bytes -ne $r.bytes -or $a.sha256 -ne $r.sha256){throw "PIN_MISMATCH $($r.path)"};$seen[$a.path]=$a}
function Recurse($v){if($null -eq $v -or $v -is [string] -or $v -is [ValueType]){return};if($v -is [System.Collections.IEnumerable] -and $v -isnot [pscustomobject]){foreach($item in $v){Recurse $item};return};if($v.PSObject.Properties['path'] -and $v.PSObject.Properties['sha256'] -and $v.PSObject.Properties['bytes']){Check $v};foreach($prop in $v.PSObject.Properties){Recurse $prop.Value}}
Check ([pscustomobject]@{path="$source/HDF.json";bytes=10136;sha256='16034d64a0e95c9697a1afda1fa1babcdaa79652c3e9e3847503fc5b87896565'})
Check ([pscustomobject]@{path="$source/MF.json";bytes=24295;sha256='fc99c790329ebf190adb04e6b7243c3c3c375f9bb361a3173c910b55b0a45733'})
$hdf=Get-Content -LiteralPath "$source/HDF.json" -Raw -Encoding UTF8|ConvertFrom-Json
$mf=Get-Content -LiteralPath "$source/MF.json" -Raw -Encoding UTF8|ConvertFrom-Json
Recurse $hdf
Recurse $mf
Check ([pscustomobject]@{path='D:/作品集/ResearchOS/research-os/migrations/sqlite/0017_runtime_dispatch.sql';bytes=1075;sha256='e5a2671c25725205bb5306c7fcbab254d53e3ef7a0448a163a41c5ac24a7b558'})
$sourceDiffs=@()
foreach($p in $mf.source_refs.PSObject.Properties){$ref=$p.Value;$sourceDiffs+=[ordered]@{name=$p.Name;byte_identical_v3=($ref.sha256 -eq $ref.previous_ref.sha256 -and $ref.bytes -eq $ref.previous_ref.bytes)}}
if(@($sourceDiffs | Where-Object {!$_.byte_identical_v3}).Count -ne 1){throw 'SOURCE_DIFF_SCOPE'}
$files=@(Get-ChildItem -LiteralPath $source -Recurse -File)
if($files.Count -ne 16 -or $mf.member_count -ne 14 -or $mf.source_file_count -ne 6){throw 'SOURCE_FILE_SCOPE'}
$summary=[ordered]@{schema='researchos.prepared-abandonment-v4-source-intake.v1';source_root=$source;unique_verified_ref_count=$seen.Count;pins=@($seen.Values);source_diffs=$sourceDiffs;source_files=6;members=14;files=16;production_authority=$false}
[IO.File]::WriteAllText("$base/inspected-source-pins.json",(($summary|ConvertTo-Json -Depth 100)+"`n"),$utf8)
[ordered]@{unique_verified_refs=$seen.Count;source_diffs=$sourceDiffs;source_pins=(Ref "$base/inspected-source-pins.json")}|ConvertTo-Json -Depth 10

