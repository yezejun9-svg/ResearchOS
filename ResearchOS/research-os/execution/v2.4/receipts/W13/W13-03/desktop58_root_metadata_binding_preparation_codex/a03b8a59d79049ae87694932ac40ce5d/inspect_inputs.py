import hashlib,json
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os')
OUT=Path(__file__).resolve().parent
base=ROOT/'.local/worktrees/codex-w1303-desktop-http-r311/execution/v2.4/receipts/W13/W13-03/desktop_http_exact15_executor_codex/revision-r317-a7f44ed9b4ae4225bd072adcf708e24b'
paths=[base/'final-audit-2d44db33d4874f8bb806b44137292e08/handoff.json',base/'cohort-19e75d3970f54c2eab44fcac2f43d61d/full-finite-inputs.json']
rows=[]
for path in paths:
    raw=path.read_bytes();doc=json.loads(raw)
    summary={'type':type(doc).__name__,'keys':list(doc) if isinstance(doc,dict) else None,'length':len(doc)}
    if isinstance(doc,dict):
        summary['fields']={k:({'type':type(v).__name__,'length':len(v),'sample':v[:1]} if isinstance(v,list) else v) for k,v in doc.items() if k in ('files','entries','resources','toolchain','tools','resource_refs','resource_ref','runtime','runtime_ref','resource_catalog_ref','source_before_ref','source_after_ref','manifest_ref')}
    elif isinstance(doc,list):summary['sample']=doc[:1]
    rows.append({'ref':{'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)},'summary':summary})
with (OUT/'resource-input-shapes.json').open('xb') as f:f.write((json.dumps(rows,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps(rows,ensure_ascii=False))
