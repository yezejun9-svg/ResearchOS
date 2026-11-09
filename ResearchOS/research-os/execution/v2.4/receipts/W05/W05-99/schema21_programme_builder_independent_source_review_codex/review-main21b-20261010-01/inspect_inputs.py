import json,hashlib,collections
from pathlib import Path
S=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/schema21_programme_builder_source_codex/main21b-20261010-01')
def read(n):return json.loads((S/n).read_bytes())
def pin(n):
 p=S/n;b=p.read_bytes();return dict(path=p.as_posix(),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
mf=read('MF.json');ins=read('input-manifest.json');c=read('contract.v2.json');prep=read('source-preparation.json');off=read('offline-module-static-map.json');delivery=read('source-delivery.json');inv=read('frozen-source-manifest.json')
print(json.dumps(dict(pins=[pin(n) for n in ['HDF.json','MF.json','old21_builder.py','contract.v2.json','input-manifest.json']],MFkeys=list(mf),members=len(mf['members']),inputkeys=list(ins),kinds=dict(collections.Counter(i['kind'] for i in ins['items'])),totalbytes=sum(i['ref']['bytes'] for i in ins['items']),maxbytes=max(i['ref']['bytes'] for i in ins['items']),inventorykeys=list(inv),inventory_nonobjects={k:v for k,v in inv.items() if k!='objects'},prep=prep,offline=off,delivery=delivery,contractkeys=list(c)),ensure_ascii=False),flush=True)
