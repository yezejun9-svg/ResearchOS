from pathlib import Path
import json
R=Path('D:/作品集/ResearchOS/research-os');U=Path(__file__).parent.name
N=R/('execution/v2.4/receipts/W13/W13-03/desktop58_root_caller_allocationseventh_source_preparation_codex/'+U)
o=json.loads((N/'original-input.json').read_bytes())
print(json.dumps({'keys':list(o),'children':{k:list(v) if isinstance(v,dict) else type(v).__name__ for k,v in o.items()}},ensure_ascii=False))
