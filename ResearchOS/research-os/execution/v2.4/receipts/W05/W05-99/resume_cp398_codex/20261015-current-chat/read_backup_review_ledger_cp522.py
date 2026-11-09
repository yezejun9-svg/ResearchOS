import json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');Q=R/'execution/v2.4/receipts/W05/W05-99/online_backup_fixture_independent_review_codex/20261015-current-chat'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
print('LEDGER',json.dumps(read(Q/'diagnostic-ledger.json'),ensure_ascii=False))
v=read(Q/'review.json');print('REVIEW_JSON',json.dumps(v,ensure_ascii=False))
