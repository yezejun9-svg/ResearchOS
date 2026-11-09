from pathlib import Path
import hashlib,json,os
S=Path(__file__).resolve().parent;R=S.parents[6];V=R/'execution/v2.4';RUN=V/'receipts/W09/W09-99/w09_br8_actual_root/actual-20261010-01'
p=S/'w09.br8-review-redelivery02.actual-audit.root.json';a=json.loads(p.read_bytes())
assert a['binding_sha256']=='57421d40ecd5380dcb7fe3d49d11c017c8371c6b0cb8a500f2f89eb981a3e9b4'
extras=json.loads((RUN/'capture.actual.extras.root.json').read_bytes());extras['original_offsets']=a['source_line_offsets']
ix=V/'root_delivery_captures/W09/W09-99/index.json';b=ix.read_bytes();assert hashlib.sha256(b).hexdigest()=='ce0424c83c54d08e82682382be3fbdd1c856fff8c2f697b8104a5a761962d9cb'
extras['previous_index_ref']=dict(path=ix.relative_to(R).as_posix(),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
p=RUN/'capture.redelivery02.extras.root.json';raw=(json.dumps(extras,ensure_ascii=False,indent=2)+'\n').encode()
with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
print(json.dumps(dict(extras_path=str(p),formal_acceptance=False),ensure_ascii=False))
