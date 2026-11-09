from pathlib import Path
import json,sys
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99';Q=B/'session_attach_contract_revision_codex/1a11ded594f5378b7512125d'
if sys.argv[1]=='initial':
 print('FILES',[p.relative_to(Q).as_posix() for p in Q.rglob('*') if p.is_file()])
 for name in ('HDF.json','MF.json','report.md'):
  p=Q/name;print('FILE',name);print(p.read_text(encoding='utf-8'))
elif sys.argv[1]=='read':
 for n in sys.argv[2:]:
  p=Q/n;print('FILE',n)
  for i,l in enumerate(p.read_text(encoding='utf-8').splitlines(),1):print(f'{i}: {l}')
