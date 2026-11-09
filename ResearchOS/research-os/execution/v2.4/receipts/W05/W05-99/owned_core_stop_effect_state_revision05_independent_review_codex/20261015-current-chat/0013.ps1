$e='D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/owned_core_stop_effect_state_revision05_independent_review_codex/20261015-current-chat'
Get-Content "$e/fixture_e2e_review.py" | Select-Object -Skip 205 -First 110
Get-ChildItem "$e/command-captures" -Recurse -Filter result.json | ForEach-Object { Get-Content $_.FullName }
