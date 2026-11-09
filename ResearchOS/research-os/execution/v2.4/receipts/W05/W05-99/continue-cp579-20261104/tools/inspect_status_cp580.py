import json
from pathlib import Path
r=Path('D:/作品集/ResearchOS/research-os')
c=json.loads((r/'execution/v2.4/checkpoint.json').read_bytes())
for k in ['current_effective_formal_status','parent_tasks_accepted','current_Main_HEAD','current_Main_tree','current_implementation','blocked_resources','workers']:
    v=c.get(k)
    print(json.dumps({k:v},ensure_ascii=True)[:6500])
