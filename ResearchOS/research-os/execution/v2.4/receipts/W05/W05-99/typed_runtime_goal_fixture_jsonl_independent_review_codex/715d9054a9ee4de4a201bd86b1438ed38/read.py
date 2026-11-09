from pathlib import Path
import json,hashlib,sys
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
Q=B/'typed_runtime_goal_fixture_jsonl_revision_codex/3adf21aec07c4b5db6eb2fcf317f85e9'
if sys.argv[1]=='initial':
 print('\n'.join(str(p.relative_to(Q)) for p in Q.rglob('*') if p.is_file()))
 for name in ['HDF.json','report.md']:
  p=Q/name;print('\nFILE '+str(p));print(p.read_text(encoding='utf-8'))
elif sys.argv[1]=='helper':
 p=Q/'candidate-root/internal/domain/runtime_typed_client_fixture_windows_test.go'
 for n,line in enumerate(p.read_text(encoding='utf-8').splitlines(),1):
  if int(sys.argv[2])<=n<=int(sys.argv[3]): print(f'{n}: {line}')
elif sys.argv[1]=='read':
 for name in sys.argv[2:]:
  p=Q/name;print('\nFILE '+str(p));print(p.read_text(encoding='utf-8'))
elif sys.argv[1]=='definitions':
 base=R/'.local/worktrees/codex-w0599-native-harness43-d74319468b584322b516e3b8b3aee4f2/internal/domain'
 for p in base.glob('*.go'):
  text=p.read_text(encoding='utf-8');lines=text.splitlines()
  for i,line in enumerate(lines):
   if 'func Digest(' in line or 'type Object ' in line:
    print('\nFILE '+str(p));print('\n'.join(f'{n+1}: {lines[n]}' for n in range(i,min(i+12,len(lines)))))
 p=R/'.local/tools/go1.27.1/go/src/cmd/test2json/main.go'
 print('\nOFFICIAL MAIN');print(p.read_text(encoding='utf-8'))
 p=R/'.local/tools/go1.27.1/go/src/cmd/internal/test2json/test2json.go'
 print('\nOFFICIAL EVENT/PASS')
 lines=p.read_text(encoding='utf-8').splitlines()
 for i,line in enumerate(lines):
  if any(x in line for x in ['type event struct','Action: "start"','Action: "pass"','func (c *Converter) writeEvent','Elapsed']):
   print('\n'.join(f'{n+1}: {lines[n]}' for n in range(max(0,i-3),min(i+12,len(lines)))))
elif sys.argv[1]=='official':
 p=R/'.local/tools/go1.27.1/go/src/cmd/internal/test2json/test2json.go';lines=p.read_text(encoding='utf-8').splitlines()
 for a,b in [(370,425),(528,547)]:
  print('\n'.join(f'{n}: {lines[n-1]}' for n in range(a,b+1)))
