import json
from pathlib import Path
N=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/cli58-fresh-held2-r334-v2-0e298790cd484ec9ba319a379e7e34ed')
out={}
for name in ['prepared_refs.json','prepare.runtime.json','prepare.tool-observations.closed.json']:
 d=json.loads((N/name).read_bytes());out[name]={'keys':list(d),'fields':{k:(len(v) if isinstance(v,(list,dict)) else v) for k,v in d.items()}}
 if name=='prepared_refs.json':out[name]['canonical_before']=d['canonical_before'];out[name]['verified_sample']=d['verified_refs'][:2]
with (Path(__file__).parent/'inspection.json').open('xb') as f:f.write((json.dumps(out,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps(out,ensure_ascii=False))
