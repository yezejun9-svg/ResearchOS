$ErrorActionPreference='Stop'
$e='D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/owned_core_stop_effect_state_revision05_independent_review_codex/20261015-current-chat'
$t='D:/作品集/ResearchOS/research-os/.local/owned-core-stop-r5-independent-review-20261015-tmp'
$c='C:/Users/yqyyds/.codex/researchos-fixture-cache/owned-core-stop-r5-independent-review-20261015'
$sid=[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$acl=Get-Acl -LiteralPath $c
$acl.SetSecurityDescriptorSddlForm("O:${sid}D:P(A;OICI;FA;;;${sid})(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)")
Set-Acl -LiteralPath $c -AclObject $acl
$pins=@()
foreach($name in @('fixture-r4.exe','fixture-parent-r4.exe')) {
Copy-Item -LiteralPath "$t/$name" -Destination "$c/$name"
$a=(Get-FileHash -LiteralPath "$t/$name").Hash;$b=(Get-FileHash -LiteralPath "$c/$name").Hash
if($a -ne $b){throw 'copy hash mismatch'}
$pins+=@{build="$t/$name";copy="$c/$name";sha256=$b;acl=(Get-Acl -LiteralPath "$c/$name").Sddl}
}
$pins | ConvertTo-Json -Depth 6 | Set-Content -Encoding utf8 "$e/native-copy-pins.json"
$paths=@($c,"$c/fixture-r4.exe","$c/fixture-parent-r4.exe")
$p=Split-Path $c
while($p){$paths+=$p;$n=Split-Path $p;if($n -eq $p){break};$p=$n}
$paths | ForEach-Object {@{path=$_;sddl=(Get-Acl -LiteralPath $_).Sddl}} | ConvertTo-Json -Depth 6 | Set-Content -Encoding utf8 "$e/native-acl-snapshot.json"
Get-Content "$e/native-copy-pins.json"
Set-Location 'D:/作品集/ResearchOS/research-os/.local/worktrees/owned-core-stop-effect-state-r5-20261015'
& 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe' -B -X utf8 "$e/reviewer_logger.py" 'D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/bin/go.exe' build -o "$t/warm-stop-cli.exe" ./ops/owned_core_stop
exit $LASTEXITCODE
