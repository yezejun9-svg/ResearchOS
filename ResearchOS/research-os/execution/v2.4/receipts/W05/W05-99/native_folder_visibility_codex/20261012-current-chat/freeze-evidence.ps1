$ErrorActionPreference='Stop'
$receipt=$PSScriptRoot
$wt='C:\Users\yqyyds\.codex\researchos-build-worktrees\native-folder-visibility-20261012'
$root='D:\作品集\ResearchOS\research-os'
Set-Location -LiteralPath $wt
function FileRecord([string]$path){ $item=Get-Item -LiteralPath $path; return [ordered]@{path=$path;sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLower();bytes=$item.Length} }
$base='b806a06fb62576c18dfd1e7174c1dfd929677506'
$head=(& git rev-parse HEAD).Trim()
if($head -ne 'b45008a754414cd795a4be396475aab8e74b2a8c'){throw 'HEAD mismatch'}
$dirty=@(& git status --porcelain=v1)
if($dirty.Count -ne 0){throw 'worktree dirty'}
$allowed=@('internal/host/native_folder_windows.go','internal/host/native_folder_windows_test.go')
$changed=@(& git diff --name-only $base $head)
if(($changed -join '|') -ne ($allowed -join '|')){throw 'source scope mismatch'}
$diff=& git diff $base $head -- $allowed
$diff | Set-Content -LiteralPath (Join-Path $receipt 'source-code.diff') -Encoding utf8
$sourceFiles=@()
foreach($file in $allowed){$rec=FileRecord (Join-Path $wt $file);$rec.path=$file;$sourceFiles+=$rec;Copy-Item -LiteralPath (Join-Path $wt $file) -Destination (Join-Path $receipt ([IO.Path]::GetFileName($file)))}
$source=[ordered]@{base=$base;candidate=$head;worktree=$wt;common_git_dir=(& git rev-parse --git-common-dir);clean=$true;exact_paths=$changed;files=$sourceFiles;all_other_tracked_sources_unchanged=$true}
$source | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $receipt 'source-frozen.json') -Encoding utf8
$raw=Join-Path $receipt 'attempt06-frozen-native-tests.stdout'
$events=@()
foreach($line in Get-Content -LiteralPath $raw){$pos=$line.IndexOf('{"event":');if($pos -ge 0){$events+=($line.Substring($pos) | ConvertFrom-Json)}}
$dialogs=@($events | Where-Object event -eq 'dialog')
$startups=@($events | Where-Object event -eq 'startup')
$cancels=@($events | Where-Object event -eq 'cancelled')
if($dialogs.Count -ne 4 -or $startups.Count -ne 2 -or $cancels.Count -ne 4){throw 'native event count mismatch'}
foreach($dialog in $dialogs){if(-not $dialog.visible -or $dialog.class -ne '#32770' -or $dialog.rect[2] -le $dialog.rect[0] -or $dialog.rect[3] -le $dialog.rect[1]){throw 'invalid dialog fact'}}
$facts=[ordered]@{raw=FileRecord $raw;startups=$startups;dialogs=$dialogs;cancellations=$cancels;stable_visibility_ms_minimum=500;foreground_obtained=@($dialogs | Where-Object {$_.hwnd -eq $_.foreground_hwnd}).Count;normal_exits=@(64128,62580);controller_show_calls=0;component_chosen_paths=0;component_workspace_bindings=0}
$facts | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $receipt 'native-dialog-observed-facts.json') -Encoding utf8
$buildInfo=Get-Content -Raw -LiteralPath (Join-Path $receipt 'attempt09-build-provenance.stdout')
if(([regex]::Matches($buildInfo,"vcs.revision=$head")).Count -ne 2 -or ([regex]::Matches($buildInfo,'vcs.modified=false')).Count -ne 2){throw 'build provenance mismatch'}
$builds=@()
foreach($name in @('control.exe','runtime-verifier.exe')){$rec=FileRecord (Join-Path $wt ".local\builds\native-folder-visibility-20261012\$name");$rec.source=$head;$rec.vcs_modified=$false;$builds+=$rec}
$builds | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $receipt 'frozen-builds.json') -Encoding utf8
$refs=@()
foreach($relative in @('execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261012-current-chat/continuation-cp431/native-folder-visibility-scope.json','execution/v2.4/receipts/W05/W05-99/native_folder_visibility_scope_assessment_codex/20261012-current-chat/scope-repair-assessment.json','execution/v2.4/receipts/W05/W05-99/normal_desktop_first_use_causal_retry02_codex/20261012-current-chat/native-dialog-core-hidden-enumeration.json')){$rec=FileRecord (Join-Path $root $relative);$rec.path=$relative;$refs+=$rec}
if($refs[0].sha256 -ne '87379d10cc49dd17038085d37d5f310390c241a805398f4ae34de0bd7170a4c4' -or $refs[1].sha256 -ne 'c0076635e7b4545a51cca52688c9df2155a446760f8cdce56339894ff72f58cd' -or $refs[2].sha256 -ne 'f600b1809a571021f1ab6f0fceb8df4e5fec28c855ed4db8a369f2a4d54e5bff'){throw 'input evidence mismatch'}
$files=@(Get-ChildItem -LiteralPath $receipt -File | Where-Object Name -ne 'source-bundle-final.json' | Sort-Object Name | ForEach-Object {$rec=FileRecord $_.FullName;$rec.path=$_.Name;$rec})
$bundle=[ordered]@{schema='researchos.native-folder-visibility-source-bundle.v1';frozen_at=(Get-Date).ToUniversalTime().ToString('o');source=$source;input_references=$refs;builds=$builds;frozen_tests=@{attempt='attempt06-frozen-native-tests';top_level_passes=7;subtest_passes=13;failures=0;skips=0;actual_hidden_helpers=2;actual_visible_dialogs=4;normal_helper_exits=2;selected_paths=0};original_failures_preserved=$true;real_product_model_calls=0;real_product_tool_calls=0;formal_acceptance_increment=0;parent_acceptance_increment=0;independent_review='PENDING';scope='SOURCE_AND_REAL_NATIVE_GUI_COMPONENT_ONLY';files=$files}
$bundle | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $receipt 'source-bundle-final.json') -Encoding utf8
FileRecord (Join-Path $receipt 'source-bundle-final.json') | ConvertTo-Json
$builds | ConvertTo-Json
