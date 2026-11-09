from pathlib import Path
import json,sys
R=Path('D:/作品集/ResearchOS/research-os'); B=R/'execution/v2.4/receipts/W05/W05-99'; Q=B/'integration_codex/typed-q3-epoch-targeted-root-0c4318e1c10443f2'
E=R/'.local/typed-q3-epoch-run-env-3c6a88ed57744a0a/typed-child-evidence'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
for p in sorted(E.rglob('*.json')):
 x=read(p)
 print(str(p.relative_to(E)),json.dumps(x,ensure_ascii=False) if p.parent.name==sorted(E.iterdir())[0].name else list(x) if isinstance(x,dict) else type(x).__name__)
for p in Q.glob('*guard.cleanup.actual.json'):
 x=read(p);print(p.name,json.dumps({k:v if not isinstance(v,list) or len(v)<3 else v[:1] for k,v in x.items()},ensure_ascii=False))
for name in ('failure-origin.823.json','original-tool-io.json'):
 x=read(Q/name);print(name,json.dumps(x,ensure_ascii=False)[:5000])
for p in sorted(E.rglob('child.stdout.jsonl')):
 events=[json.loads(l) for l in p.read_text(encoding='utf-8').splitlines()]
 print('EVENTS',str(p.relative_to(E)),json.dumps([e for e in events if e.get('Action') in ('run','pass','fail','skip') or 'attach' in e.get('Output','')],ensure_ascii=False))
