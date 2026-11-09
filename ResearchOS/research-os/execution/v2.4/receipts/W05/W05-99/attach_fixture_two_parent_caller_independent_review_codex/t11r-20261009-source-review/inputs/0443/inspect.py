import sys
sys.dont_write_bytecode=True
from pathlib import Path
import hashlib,json
Q=Path(__file__).parent
R=Path('D:/作品集/ResearchOS/research-os')
T=R/'.local/worktrees/codex-w0599-native-harness43-d74319468b584322b516e3b8b3aee4f2'
B=R/'execution/v2.4/receipts/W05/W05-99'
C=B/'remaining_full_failure_cause_review_codex/8c83a215358ce0e859da44f08b8a69d3'
I=B/'integration_codex/native-harness43-compile-unit-root-c16a0730cf914bc5/actual-tagged-compiler-input-inventory.json'
def pin(p):
 raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
names=['client_session_bootstrap_test.go','retrieval_test.go']
rows=[]
for name in names:
 p=T/'internal/domain'/name;raw=p.read_text(encoding='utf-8');lines=raw.splitlines()
 ranges=[(1,len(lines))] if name==names[0] else [(1,35),(470,560)]
 print('SOURCE',json.dumps(pin(p),ensure_ascii=False))
 for a,b in ranges:
  for n in range(a,min(b,len(lines))+1):print(str(n)+': '+lines[n-1])
 rows.append({'ref':pin(p),'source':raw})
data=json.loads(I.read_text(encoding='utf-8'))
def refs(x):
 if isinstance(x,dict):
  if isinstance(x.get('path'),str):yield x
  for v in x.values():yield from refs(v)
 elif isinstance(x,list):
  for v in x:yield from refs(v)
selected=[x for x in refs(data) if any(str(T/'internal/domain'/n).replace('\\','/').lower()==x['path'].replace('\\','/').lower() for n in names)]
manifest=json.loads((C/'manifest.json').read_text(encoding='utf-8'))
print('CAUSE_MANIFEST_KEYS',list(manifest))
print('T5_INVENTORY',json.dumps({'ref':pin(I),'selected_refs':selected},ensure_ascii=False))
out={'authority':'NONE','test_sources':rows,'cause_manifest_ref':pin(C/'manifest.json'),'cause_report_ref':pin(C/'report.md'),'cause_source_pins_ref':pin(C/'source-pins.json'),'T5_actual_inventory_ref':pin(I),'T5_actual_test_refs':selected}
with (Q/'inspection.json').open('x',encoding='utf-8') as f:f.write(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
