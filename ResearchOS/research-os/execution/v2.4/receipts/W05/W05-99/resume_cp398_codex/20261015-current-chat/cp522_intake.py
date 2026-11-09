import json
import hashlib
from pathlib import Path

R=Path('D:/作品集/ResearchOS/research-os')
E=R/'execution/v2.4/receipts/W05/W05-99'
B=E/'resume_cp398_codex/20261015-current-chat'
def show(p):
    p=Path(p)
    x=p.read_bytes()
    print('\nFILE',str(p),'SHA256',hashlib.sha256(x).hexdigest(),'BYTES',len(x))
    print(x.decode('utf-8-sig'))
for p in [R.parent/'AGENTS.md', R/'AGENTS.md']:
    if p.is_file(): show(p)
for name in ['qualification_failure_b_revision02_independent_review_codex','owned_core_stop_effect_state_revision05_source_codex','online_backup_fixture_qualification_codex']:
    d=E/name/'20261015-current-chat'
    print('TOPLEVEL',str(d),json.dumps([p.name for p in d.iterdir()],ensure_ascii=False))
    if name.startswith('qualification_failure_b_'):
        for p in sorted(d.glob('*.md')): show(p)
        for p in sorted(d.glob('*ledger*.json')): show(p)
        for p in sorted(d.glob('*review*.json')): show(p)
    if name.startswith('online_backup_'): show(d/'capture-index-supplement.json')
show(B/'register_cp521.py')
