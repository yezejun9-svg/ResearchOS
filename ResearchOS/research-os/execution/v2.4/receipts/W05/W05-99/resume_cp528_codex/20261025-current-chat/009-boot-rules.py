import json
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os"); B=R/'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat'
p=B/'continuation-cp521/boot-proposal-adopted-limits.json';v=json.loads(p.read_text(encoding='utf8'))
print(json.dumps({k:x for k,x in v.items() if k not in ['source57','gates']},ensure_ascii=False,indent=2))
for path in [Path('C:/Users/yqyyds/AGENTS.md'),R/'AGENTS.md']:
 print('FILE '+str(path));print(path.read_text(encoding='utf-8-sig'))
