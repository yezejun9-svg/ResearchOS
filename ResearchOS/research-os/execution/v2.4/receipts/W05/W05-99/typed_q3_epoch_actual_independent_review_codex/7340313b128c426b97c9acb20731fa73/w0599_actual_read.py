from pathlib import Path
import json,sys
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99';Q=B/'integration_codex/typed-q3-epoch-targeted-root-0c4318e1c10443f2'
if sys.argv[1]=='initial':
 print('\n'.join(p.relative_to(Q).as_posix() for p in Q.rglob('*') if p.is_file()))
 p=Q/'validation.closed.json';print('\nCLOSED');print(p.read_text(encoding='utf-8'))
elif sys.argv[1]=='read':
 for name in sys.argv[2:]:
  p=Q/name;print('\nFILE '+str(p));print(p.read_text(encoding='utf-8'))
elif sys.argv[1]=='summary':
 for p in Q.glob('*.json'):
  x=json.loads(p.read_text(encoding='utf-8'))
  print(p.name,[(k,len(v) if isinstance(v,(dict,list,str)) else v) for k,v in x.items()] if isinstance(x,dict) else type(x).__name__)
 e=R/'.local/typed-q3-epoch-run-env-3c6a88ed57744a0a/typed-child-evidence'
 print('CHILD_EVIDENCE')
 print('\n'.join(p.relative_to(e).as_posix() for p in e.rglob('*') if p.is_file()))
