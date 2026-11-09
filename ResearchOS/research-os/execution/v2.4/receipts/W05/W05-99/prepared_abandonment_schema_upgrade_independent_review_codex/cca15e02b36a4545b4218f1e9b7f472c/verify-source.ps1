$ErrorActionPreference='Stop'
$base='D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/prepared_abandonment_schema_upgrade_independent_review_codex/cca15e02b36a4545b4218f1e9b7f472c'
$source='D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/prepared_abandonment_schema_upgrade_source_codex/e841e7fcddaa45ecb115f84df9827af2'
function Ref([string]$p){$f=Get-Item -LiteralPath $p;[ordered]@{path=$f.FullName;bytes=$f.Length;sha256=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}}
$seen=@{}
$pins=[Collections.Generic.List[object]]::new()
function Check($r){$a=Ref $r.path;if($a.sha256 -ne $r.sha256 -or $a.bytes -ne $r.bytes){throw "PIN_MISMATCH $($r.path)"};if(-not $seen.ContainsKey($a.path)){$seen[$a.path]=$true;$pins.Add($a)}}
Check ([pscustomobject]@{path="$source/HDF.json";sha256='a6e03021860808f09d7e36622a6aff9206a3e2aa18008afd94c62ff00f177a99';bytes=12691})
Check ([pscustomobject]@{path="$source/MF.json";sha256='b1585d636212dfe6592bf51aff78257decff13a14d4efc148f6c0f66de94d42c';bytes=27291})
$mf=Get-Content -LiteralPath "$source/MF.json" -Raw -Encoding UTF8|ConvertFrom-Json
foreach($p in $mf.members.PSObject.Properties){Check $p.Value}
foreach($r in $mf.base_refs){Check $r}
foreach($p in $mf.source_refs.PSObject.Properties){Check $p.Value}
$hdf=Get-Content -LiteralPath "$source/HDF.json" -Raw -Encoding UTF8|ConvertFrom-Json
Check $hdf.manifest_ref
$result=[ordered]@{source_root=$source;verified_unique_pin_count=$pins.Count;member_count=@($mf.members.PSObject.Properties).Count;base_ref_count=@($mf.base_refs).Count;source_count=@($mf.source_refs.PSObject.Properties).Count;pins=@($pins.ToArray());go_executed=$false;native_executed=$false;sql_executed=$false;provider_requests=0;input_drift_count=0}
$raw=($result|ConvertTo-Json -Depth 50)+[Environment]::NewLine
[IO.File]::WriteAllText("$base/inspected-source-pins.json",$raw,[Text.UTF8Encoding]::new($false))
[ordered]@{verified_unique_pin_count=$pins.Count;member_count=$result.member_count;base_ref_count=$result.base_ref_count;source_count=$result.source_count;receipt=(Ref "$base/inspected-source-pins.json")}|ConvertTo-Json -Depth 10

