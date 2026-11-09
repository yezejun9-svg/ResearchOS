import json
from pathlib import Path
q=json.loads(Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/cli43_successful_execution_independent_review_codex/6f07498ca19a49c7866b9e528d401aa0/qualification.json').read_bytes())
out={}
for k in ['executor_manifest_ref','launcher_manifest_ref','root_closed_manifest_ref','result_ref','launcher_completed_ref']:
    d=json.loads(Path(q['evidence_refs'][k]['path']).read_bytes())
    out[k]={a:({'kind':'list','count':len(b),'first':b[:1]} if isinstance(b,list) else b) for a,b in d.items()}
print(json.dumps(out,ensure_ascii=False,indent=2))
