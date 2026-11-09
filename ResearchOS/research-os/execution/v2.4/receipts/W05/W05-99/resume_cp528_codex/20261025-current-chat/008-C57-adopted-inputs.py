import json,hashlib
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os'); N=Path(__file__).parent; B=R/'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat'
for rel in ['future-C57-unissued-input-map-cp528.json','future-C57-core-contract-input-addendum-cp528.json','continuation-cp521/boot-proposal-adopted-limits.json','continuation-cp511/C-design-adopted-constraints.json']:
 p=B/rel; v=json.loads(p.read_text(encoding='utf-8-sig')); print(json.dumps({'file':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'content':v},ensure_ascii=False))
