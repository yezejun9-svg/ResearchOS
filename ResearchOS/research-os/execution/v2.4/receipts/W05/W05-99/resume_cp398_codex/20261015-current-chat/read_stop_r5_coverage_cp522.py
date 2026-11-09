import json,hashlib
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');B=Path(__file__).parent;S=R/'execution/v2.4/receipts/W05/W05-99/owned_core_stop_effect_state_revision05_independent_review_codex/20261015-current-chat'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 x=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(x).hexdigest(),'bytes':len(x)}
print('COVERAGE',json.dumps(read(S/'coverage.json'),ensure_ascii=False))
m=read(S/'FINAL-manifest.json');a=[]
for x in m['excluded_terminal_envelope']:
 name=x if isinstance(x,str)else x['path'];p=Path(name)
 if not p.is_absolute():p=S/p
 if p.is_file():
  row={'ref':ref(p)}
  if p.suffix=='.json':row['json']=read(p)
  elif p.name.endswith('.stdout.raw')or p.name.endswith('.stdout.txt'):row['tail']=p.read_text(encoding='utf-8-sig')[-1200:]
  a.append(row)
 else:a.append({'path':str(p),'exists':False})
out={'excluded_terminal_envelope':a,'coverage':ref(S/'coverage.json'),'original_manifest_unchanged':ref(S/'FINAL-manifest.json')}
p=B/'stop-r5-review-terminal-supplement.json';assert not p.exists();p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('TERMINAL',json.dumps(out,ensure_ascii=False))
