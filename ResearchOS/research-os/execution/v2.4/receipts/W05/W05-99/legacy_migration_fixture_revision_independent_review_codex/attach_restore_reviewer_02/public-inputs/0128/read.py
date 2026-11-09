from pathlib import Path
import json,sys
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99';Q=B/'legacy_migration_fixture_source_codex/edd7ae2789974a469dd2fc3a1bce50a9'
if sys.argv[1]=='list':
 print('\n'.join(p.relative_to(Q).as_posix() for p in sorted(Q.rglob('*')) if p.is_file()))
elif sys.argv[1]=='read':
 for n in sys.argv[2:]:
  p=Q/n;print('FILE',n)
  for i,l in enumerate(p.read_text(encoding='utf-8').splitlines(),1):print(f'{i}: {l}')
elif sys.argv[1]=='slice':
 p=Path(sys.argv[2]);print('FILE',str(p))
 for i,l in enumerate(p.read_text(encoding='utf-8').splitlines(),1):
  if int(sys.argv[3])<=i<=int(sys.argv[4]):print(f'{i}: {l}')
elif sys.argv[1]=='shape':
 for n in sys.argv[2:]:
  p=Q/n;x=json.loads(p.read_text(encoding='utf-8'));print(n,[(k,len(v) if isinstance(v,(list,dict,str)) else v) for k,v in x.items()] if isinstance(x,dict) else type(x).__name__)
elif sys.argv[1]=='find':
 T=R/'.local/worktrees/codex-w0599-native-harness43-d74319468b584322b516e3b8b3aee4f2'
 for p in (T/'internal/domain').glob('*.go'):
  matches=[(i,l) for i,l in enumerate(p.read_text(encoding='utf-8').splitlines(),1) if any(term in l for term in sys.argv[2:])]
  if matches:print('FILE',str(p));print('\n'.join(f'{i}: {l}' for i,l in matches))
