from pathlib import Path
import json
R=Path('D:/作品集/ResearchOS/research-os'); B=R/'execution/v2.4/receipts/W05/W05-99'; Q=B/'integration_codex/typed-q3-epoch-targeted-root-0c4318e1c10443f2'
print((B/'integration_codex/typed-q3-isolation-root-7fe91a34b0814df0/isolation.ready.json').read_text(encoding='utf-8'))
overlay=json.loads((Q/'source-overlay.json').read_text(encoding='utf-8'))
for n,r in overlay['sources'].items():
 if 'typed' in n or 'runtime_tool_integration_windows_test.go' in n:
  print('SOURCE',n,r)
  lines=Path(r['path']).read_text(encoding='utf-8').splitlines()
  found=set()
  for i,line in enumerate(lines):
   if any(t in line for t in ('session.attach','func muClientCall','COMPLETED')):
    for j in range(max(0,i-4),min(len(lines),i+10)):
     if j not in found:print(j+1,lines[j]);found.add(j)
print('PARENT_FAIL_AND_SELECTED')
closed=json.loads((Q/'validation.closed.json').read_text(encoding='utf-8'))
print(json.dumps(closed['actions'],ensure_ascii=False))
