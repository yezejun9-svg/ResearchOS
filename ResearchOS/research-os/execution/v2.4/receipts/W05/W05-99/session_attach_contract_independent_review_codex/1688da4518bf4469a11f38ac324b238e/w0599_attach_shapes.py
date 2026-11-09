from pathlib import Path
import json
R=Path('D:/作品集/ResearchOS/research-os');Q=R/'execution/v2.4/receipts/W05/W05-99/session_attach_contract_revision_codex/1a11ded594f5378b7512125d'
for name in ('production-replacements.json','final-static-checks.json','static-evidence.json'):
 x=json.loads((Q/name).read_text(encoding='utf-8'))
 if name=='production-replacements.json':
  print(name,type(x).__name__,list(x) if isinstance(x,dict) else len(x))
  if isinstance(x,list):print([{k:(len(v) if isinstance(v,str) else v) for k,v in row.items()} for row in x])
 else:print(name,json.dumps(x,ensure_ascii=False))
