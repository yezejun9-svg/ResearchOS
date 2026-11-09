from pathlib import Path
import json
B=Path(r'D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W05\\W05-99\\resume_cp398_codex\\20261015-current-chat')
r=json.loads((B/'continuation-cp526'/'RESUME.current.json').read_text(encoding='utf-8-sig'))
print('RESUME_KEYS',list(r))
print(json.dumps({k:v for k,v in r.items() if k in ['checkpoint','next','next_actions','active_ownership','active_tasks','source_cards','status','counter','failure_count','diagnostic_count']},ensure_ascii=False))
for name in ['register_cp526.py','register_cp525.py']:
 p=B/name
 if p.exists():
  lines=p.read_text(encoding='utf-8-sig').splitlines()
  print('FILE',name,'LINES',len(lines))
  print('\\n'.join(f'{i+1}: {x}' for i,x in enumerate(lines) if i<45 or i>=len(lines)-105))
