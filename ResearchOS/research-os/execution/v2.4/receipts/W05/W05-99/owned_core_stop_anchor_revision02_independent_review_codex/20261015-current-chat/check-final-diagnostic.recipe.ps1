$d=Get-Content "$e\diagnostic-audit.json" -Raw | ConvertFrom-Json
$d.own_nonzero | ConvertTo-Json -Depth 5
Get-ChildItem "$e\command-captures" -Directory | Where-Object Name -Match 'relative-base' | ForEach-Object { Get-Content "$($_.FullName)\after.json","$($_.FullName)\stderr.bin" -Raw }
