from pathlib import Path
import json
R=Path('D:/作品集/ResearchOS/research-os');N=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r339-9eccde97a9fa4815941768cacaf590dc'
d=json.loads((N/'tool-observations.seventh-final-binding-draft.closed.original.json').read_bytes())
print(json.dumps({'keys':list(d),'shapes':{k:({'keys':list(v)} if isinstance(v,dict) else {'len':len(v),'first_keys':list(v[0]) if v and isinstance(v[0],dict) else None} if isinstance(v,list) else v) for k,v in d.items()}},ensure_ascii=False))
