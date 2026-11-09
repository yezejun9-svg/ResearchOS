$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new()
$p='D:/作品集/ResearchOS/research-os/.local/worktrees/host-candidate-capture-20261104/internal/host/runtime_check_delivery_windows_test.go'
if((Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant() -ne 'ebdc03435a4602d425ebef8971b07a729c069c73099fece0318b1c85756c14e0'){throw 'source drift'}
$s=[IO.File]::ReadAllText($p)
foreach($needle in @('type candidateFixture struct {','candidateFixture{view: v, source: source,','f.check, f.view.PolicyHash, f.manifest')){if($s.IndexOf($needle) -lt 0 -or $s.IndexOf($needle) -ne $s.LastIndexOf($needle)){throw 'fixture patch cardinality'}}
$s=$s.Replace('type candidateFixture struct {',"type candidateFixture struct {`n`tpolicyHash string").Replace('candidateFixture{view: v, source: source,','candidateFixture{view: v, policyHash: v.PolicyHash, source: source,').Replace('f.check, f.view.PolicyHash, f.manifest','f.check, f.policyHash, f.manifest')
[IO.File]::WriteAllText($p,$s,[Text.UTF8Encoding]::new($false))
$r=[ordered]@{status='FIXTURE_INDEPENDENT_POLICY_BASELINE_CORRECTED';sha256=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
[IO.File]::WriteAllText('C:/Users/yqyyds/Documents/Codex/2026-11-04/task/cp599-candidate-capture-author/fixture-fix-04.json',($r|ConvertTo-Json),[Text.UTF8Encoding]::new($false))
$r|ConvertTo-Json -Compress

