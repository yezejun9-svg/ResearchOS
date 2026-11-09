from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent
old=R/'execution/v2.4/receipts/W13/W13-03/desktop58_current_bound_scope_independent_review_codex/b4d53db07f1e4ab8b9c0b37e291a6da5'
for name in ('supplement.py','final_checks.py'):
    raw=(old/name).read_bytes();needle=b'desktop58-finite169-go3-r337-'
    assert raw.count(needle)==1
    with (O/name).open('xb') as f:f.write(raw.replace(needle,b'desktop58-finite169-go3-r339-'))
print('Created two independent audit algorithms; candidate execution zero.')
