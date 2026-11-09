from pathlib import Path
import json,types
D=Path(__file__).resolve().parent;W=Path(r'D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W09\W09-99')
p=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py';s=types.ModuleType('review_support');s.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),s.__dict__);s.D=D
print(json.dumps(s.capture('1d479e',1,None,1159),ensure_ascii=False))
