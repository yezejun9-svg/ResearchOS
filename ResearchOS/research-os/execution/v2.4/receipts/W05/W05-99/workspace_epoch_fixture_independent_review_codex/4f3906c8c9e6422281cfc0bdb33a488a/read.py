from pathlib import Path
import sys,json
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
Q=B/'workspace_epoch_fixture_source_codex/fa7c40fcaeed4dd5bdb649c9a77d393c'
if sys.argv[1]=='initial':
 print('\n'.join(p.relative_to(Q).as_posix() for p in Q.rglob('*') if p.is_file()))
 for p in [Q/'HDF.json',Q/'MF.json',*Q.glob('*.patch')]:
  print('\nFILE '+str(p));print(p.read_text(encoding='utf-8'))
elif sys.argv[1]=='read':
 for name in sys.argv[2:]:
  p=Path(name);print('\nFILE '+str(p));print(p.read_text(encoding='utf-8'))
elif sys.argv[1]=='lines':
 p=Path(sys.argv[2]);lines=p.read_text(encoding='utf-8').splitlines()
 for n in range(int(sys.argv[3]),min(int(sys.argv[4]),len(lines))+1):print(f'{n}: {lines[n-1]}')
