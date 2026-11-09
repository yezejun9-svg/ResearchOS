from pathlib import Path
import hashlib,json,os
R=Path(r'D:\作品集\ResearchOS\research-os');V=R/'execution/v2.4';RUN=V/'receipts/W09/W09-99/w09_br8_actual_root/actual-20261010-01'
P=RUN/'capture-a7067db724ce4a34a71a01055c9e00c8/result.json'
def checked(ref):
 p=Path(ref['path']);p=p if p.is_absolute() else R/p;b=p.read_bytes()
 assert hashlib.sha256(b).hexdigest()==ref['sha256'] and len(b)==ref['bytes'];return b
def save(p,b):
 with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
 return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
b=P.read_bytes();assert hashlib.sha256(b).hexdigest()=='8a9e3a2915c12bd67df0768f13696e9a087704fbf72f1c5ba22cef68ff1c884f' and len(b)==6058
d=json.loads(b);targets=[(d['origin_fixed_path'],d['origin_payload_ref']),(d['capture_fixed_path'],d['capture_payload_ref']),(d['fixed_path'],d['payload_ref'])]
assert targets[2][0]=='execution/v2.4/root_delivery_captures/W09/W09-99/index.json'
assert targets[0][0].startswith('execution/v2.4/root_original_events/W09/W09-99/') and targets[0][0].endswith('.jsonl')
assert targets[1][0].startswith('execution/v2.4/root_delivery_captures/W09/W09-99/') and targets[1][0].endswith('.json')
payloads=[checked(ref) for _,ref in targets]
for fixed,_ in targets:
 p=R/fixed;assert p.resolve().is_relative_to(V) and not p.exists() and p.parent.is_dir()
published=[save(R/fixed,raw) for (fixed,_),raw in zip(targets,payloads)]
extras=dict(publication_ref=dict(path=str(P),sha256='8a9e3a2915c12bd67df0768f13696e9a087704fbf72f1c5ba22cef68ff1c884f',bytes=6058),expected_previous_registry_ref=None)
er=save(RUN/'capture-registration.actual.extras.root.json',(json.dumps(extras,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps(dict(published_refs=published,extras_ref=er,canonical_acceptance_written=False),ensure_ascii=False))
