$root='D:/作品集/ResearchOS/research-os'
$card=Get-Content -LiteralPath (Join-Path $root 'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp518/official-entry-readonly-resource-scope.json') -Raw|ConvertFrom-Json
foreach($i in $card.inputs){$h=(Get-FileHash -LiteralPath (Join-Path $root $i.path) -Algorithm SHA256).Hash.ToLower();if($h -ne $i.sha256){throw ('INPUT_DRIFT '+$i.path)};'INPUT_HASH_MATCH '+$i.path}
foreach($rel in @('execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261014-current-chat/continuation-cp470/normal-activation-scope.json','execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261014-current-chat/continuation-cp481/profile-normal-activation-scope.json','apps/desktop/package.json','package.json')){
 $p=Join-Path $root $rel
 if(Test-Path -LiteralPath $p){'FILE '+$rel;Get-Content -LiteralPath $p -Raw}else{'ABSENT '+$rel}
}
$packages=@('C:/Users/yqyyds/.codex/researchos-resource-cache/normal-coding-profile-c8b7adab-20261014','C:/Users/yqyyds/.codex/researchos-resource-cache/normal-verifier-replacement-4f4023-20261015')
$inventory=@()
foreach($p in $packages){if(-not(Test-Path -LiteralPath $p)){throw ('PACKAGE_MISSING '+$p)};$f=@(Get-ChildItem -LiteralPath $p -Recurse -File -Force);'PACKAGE '+$p+' FILES='+$f.Count;foreach($x in $f){$rel=$x.FullName.Substring($p.Length).TrimStart('/','\');$inventory+=@{package_root=$p;relative_path=$rel;absolute_path=$x.FullName;bytes=$x.Length};$rel}}
$inventory|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $PSScriptRoot 'package-file-locations.json') -Encoding utf8
foreach($dir in @('apps/desktop','ops/backup','ops/supervisor/release_host','scripts')){
 $p=Join-Path $root $dir
 if(Test-Path -LiteralPath $p){'SOURCE_LOCATORS '+$dir;& rg --files $p -g '*.ts' -g '*.js' -g '*.mjs' -g '*.cjs' -g '*.json' -g '*.ps1' -g '*.cmd' -g '*.go' -g '!node_modules' -g '!package-lock.json';'NATIVE_RG_EXIT='+$LASTEXITCODE}else{'ABSENT_SOURCE_DIRECTORY '+$dir}
}

