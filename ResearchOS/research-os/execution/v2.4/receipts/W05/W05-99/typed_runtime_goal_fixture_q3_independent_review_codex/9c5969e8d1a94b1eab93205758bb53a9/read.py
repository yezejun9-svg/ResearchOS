from pathlib import Path
import json,sys
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
Q=B/'typed_runtime_goal_fixture_jsonl_digest_revision_codex/794a6ecddad942d69e6f8fb19bcc2e49'
if sys.argv[1]=='initial':
 print('\n'.join(p.relative_to(Q).as_posix() for p in Q.rglob('*') if p.is_file()))
 for name in ['HDF.json','MF.json']:
  p=Q/name;print('\nFILE '+str(p));print(p.read_text(encoding='utf-8'))
elif sys.argv[1]=='diff':
 for p in list(Q.glob('*.patch'))+[Q/'report.md',Q/'static-checks.json']:
  print('\nFILE '+str(p));print(p.read_text(encoding='utf-8'))
elif sys.argv[1]=='lines':
 p=Q/'candidate-root/internal/domain/runtime_typed_client_fixture_windows_test.go';lines=p.read_text(encoding='utf-8').splitlines()
 for n in range(int(sys.argv[2]),min(int(sys.argv[3]),len(lines))+1):print(f'{n}: {lines[n-1]}')
