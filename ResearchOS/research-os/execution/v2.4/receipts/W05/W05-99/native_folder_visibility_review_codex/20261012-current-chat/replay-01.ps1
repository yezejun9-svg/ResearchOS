$ErrorActionPreference='Stop'
$receipt=$PSScriptRoot
$repo='D:\作品集\ResearchOS\research-os'
$wt='C:\Users\yqyyds\.codex\researchos-build-worktrees\native-folder-visibility-20261012'
$author=Join-Path $repo 'execution/v2.4/receipts/W05/W05-99/native_folder_visibility_codex/20261012-current-chat'
$bundle=Join-Path $author 'source-bundle-final.json'
$expectedBundle='2a2c2796ff3bfed1feeb1c3a46c80b00c98b4f5df3210840b2f5b5cce80d62fd'
if(Test-Path -LiteralPath (Join-Path $receipt 'replay-01.invocation.json')){throw 'Existing evidence attempt may not be overwritten'}
$b=Get-Content -LiteralPath $bundle -Raw | ConvertFrom-Json
function Check-Pins {
  if((Get-FileHash -LiteralPath $bundle -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedBundle){throw 'Author bundle changed'}
  $checks=@()
  foreach($group in @(@{rows=$b.source.files;root=$wt},@{rows=$b.input_references;root=$repo},@{rows=$b.files;root=$author},@{rows=$b.builds;root=''})) {
    foreach($row in $group.rows) {
      $p=if($group.root){Join-Path $group.root $row.path}else{$row.path}
      $actual=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()
      if($actual -ne $row.sha256 -or (Get-Item -LiteralPath $p).Length -ne $row.bytes){throw "Pin mismatch: $p"}
      $checks += [ordered]@{path=$p;sha256=$actual;matched=$true}
    }
  }
  $head=(& git -C $wt rev-parse HEAD).Trim()
  $dirty=@(& git -C $wt status --short)
  $paths=@(& git -C $wt diff --name-only $b.source.base $head)
  if($head -ne $b.source.candidate -or $dirty.Count -ne 0 -or (@(Compare-Object $paths $b.source.exact_paths)).Count -ne 0){throw 'Source head/status/scope mismatch'}
  [ordered]@{head=$head;dirty=$dirty;exact_diff_paths=$paths;all_other_tracked_files_byte_unchanged_from_base=$true;checked_count=$checks.Count;checks=$checks}
}
Check-Pins | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $receipt 'pins-before-01.json') -Encoding utf8NoBOM
$goRoot=Join-Path $repo '.local/tools/go1.27.1/go'
$go=Join-Path $goRoot 'bin/go.exe'
$ownTemp=Join-Path $wt '.local/builds/native-folder-review-20261012'
$env:GOTOOLCHAIN='local'; $env:GOENV='off'; $env:GOROOT=$goRoot
$env:GOPATH=Join-Path $repo '.local/tools/gopath'; $env:GOMODCACHE=Join-Path $env:GOPATH 'pkg/mod'
$env:GOCACHE='C:\Users\yqyyds\.codex\researchos-build-worktrees\coding-client-v2-20261012\.local\builds\product-coding-client-repair-v2-20261012\go-cache'
$env:GOTMPDIR=Join-Path $ownTemp 'go-tmp'; $env:TEMP=Join-Path $ownTemp 'temp'; $env:TMP=$env:TEMP
$env:GOPROXY='off'; $env:GOSUMDB='off'; $env:RESEARCHOS_NATIVE_FOLDER_GUI_TEST='1'
New-Item -ItemType Directory -Force -Path $env:GOTMPDIR,$env:TEMP | Out-Null
$argsGo=@('test','-mod=readonly','./internal/host','-run','^(TestNativeFolderHiddenProcess|TestNativeWorkspaceChooseNeedsConfirmedHostSelection|TestNativeWorkspaceChooseRequiresExplicitNullablePath|TestNativeWindowsFolderChooserAPIsPresent|TestNativePublishedBootstrapRebindsAndRenews|TestManagedRequestFilePrivateACLAndStrictJSON|TestDesktopManagementStrictFrames)$','-count=1','-v','-timeout=150s')
$record=[ordered]@{argv=@($go)+$argsGo;cwd=$wt;started_at=[DateTime]::UtcNow.ToString('o');environment=@{};author_bundle_sha256=$expectedBundle;scope='SOURCE_AND_OWN_NATIVE_OS_COMPONENT_ONLY';model_calls=0;product_tool_calls=0;real_workspace_authorizations=0;root_data_or_gui_operations=0;formal_acceptance_delta=0}
foreach($key in @('GOROOT','GOPATH','GOMODCACHE','GOCACHE','GOTMPDIR','TEMP','TMP','GOTOOLCHAIN','GOENV','GOPROXY','GOSUMDB','RESEARCHOS_NATIVE_FOLDER_GUI_TEST')){$record.environment[$key]=[Environment]::GetEnvironmentVariable($key)}
$record | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $receipt 'replay-01.invocation.json') -Encoding utf8NoBOM
Set-Location -LiteralPath $wt
& $go @argsGo 1> (Join-Path $receipt 'replay-01.stdout') 2> (Join-Path $receipt 'replay-01.stderr')
$testExit=$LASTEXITCODE
$record.ended_at=[DateTime]::UtcNow.ToString('o');$record.exit_code=$testExit
$record | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $receipt 'replay-01.result.json') -Encoding utf8NoBOM
Check-Pins | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $receipt 'pins-after-01.json') -Encoding utf8NoBOM
foreach($build in $b.builds){ & $go version -m $build.path }
Get-Content -LiteralPath (Join-Path $receipt 'replay-01.stdout')
Get-Content -LiteralPath (Join-Path $receipt 'replay-01.stderr')
exit $testExit
