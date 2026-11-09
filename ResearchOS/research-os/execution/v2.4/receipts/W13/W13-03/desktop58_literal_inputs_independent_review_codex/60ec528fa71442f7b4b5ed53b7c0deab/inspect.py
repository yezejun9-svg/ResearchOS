from pathlib import Path
import json
R=Path('D:/作品集/ResearchOS/research-os');N=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r335-429e1734d9da4efba276680e78e2510b'
q=json.loads((N/'root-construction.parameters.desktop58.json').read_bytes())
for k,v in q.items():
 if isinstance(v,list):out={'type':'list','count':len(v),'first':v[:1]}
 elif isinstance(v,dict):out=v if len(str(v))<2800 else {'type':'dict','keys':list(v)}
 else:out=v
 print(json.dumps({k:out},ensure_ascii=False))
