import json
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");E=R/'execution/v2.4/receipts/W05/W05-99/react_workbench_redesign_codex/20261025-current-chat'
for name in ['SOURCE14-SEAL.json','CI-REFS.json','SOURCE14-CI-PROBE.json','real-isolated-03/report.json','browser-fixture-05/report.json']:
 p=E/name;v=json.loads(p.read_text(encoding='utf8'));out={}
 for k,x in v.items():
  if isinstance(x,list):out[k]={'count':len(x),'first':x[:1] if k not in ['checks','files','source_manifest'] else []}
  elif isinstance(x,dict):out[k]={'keys':list(x)[:14],'count':len(x)}
  else:out[k]=x
 print(json.dumps({'file':name,'summary':out},ensure_ascii=False))
p=E/'FINAL-SOURCE14.md';v=p.read_text(encoding='utf8');print('FINAL-SOURCE14.md chars='+str(len(v)));print(v if len(v)<15000 else v[:15000]+' [NEEDS_MORE_READ]')
rows=[json.loads(x)for x in(E/'LEDGER.jsonl').read_text(encoding='utf8').splitlines()if x.strip()]
print(json.dumps({'ledger_rows':len(rows),'entries':rows},ensure_ascii=False,indent=2))
