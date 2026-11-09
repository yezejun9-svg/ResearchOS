import sys,json,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
R=Path('D:/作品集/ResearchOS/research-os')
N=Path(__file__).resolve().parent
B=R/'execution/v2.4/receipts/W05/W05-99/checkpoint_r367_transaction_operation_v5_source_root/cp367-operation-v5-20261009'
def pin(p):
 p=Path(p).resolve(strict=True);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def read(ref):
 assert set(ref)=={'path','sha256','bytes'} and pin(ref['path'])==ref
 return json.loads(Path(ref['path']).read_bytes())
def save(name,v):
 with (N/name).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
 return pin(N/name)
sref=pin(N/'main-seven-target.scope-registration.root.json');assert sref['sha256']=='83c8d7cae4e8630a7378eaa40563b5b26812199e8d7869aa38318be5f8fdb2e0' and sref['bytes']==4355
scope=read(sref);assert scope['issued_by']==scope['executor']=='codex:/root'
caller=scope['caller_ref'];assert caller['sha256']=='285fd72ab1b5b62f75956f676fe9abc842150ffb4c93b32f111eaeeccb779103' and caller['bytes']==29712
read_source=Path(caller['path']).read_bytes();assert pin(caller['path'])==caller
refs=[pin(R/'execution/v2.4'/(name+'.json')) for name in ('checkpoint','path_ownership','step_state','commands')]
c,o=map(read,refs[:2]);proof=read(pin(B/'canonical_pair.actual.json'))
assert c['revision']==367 and o['revision']==171 and len(c['failure_counters'])==949
assert proof['checkpoint_ref']==refs[0] and proof['ownership_ref']==refs[1] and proof['next_original_failure_ordinal_live']==952
assert o['card_path_bindings']['W09-99']['subtasks']['c19_main_source_registry_adoption']['scope_ref']==sref
assert c['work_in_progress']['root_next_failure_ordinal_live']==952
change=read(scope['change_set_ref']);assert refs[3]==change['targets'][6]['before_ref']
vector=save('canonical-vector.actual.root.json',dict(schema='researchos.w09-main-c19-adoption-canonical-vector.v1',checkpoint_revision=367,ownership_revision=171,refs=refs))
request=save('adoption-request.actual.root.json',dict(schema='researchos.root-w09-main-c19-adoption-request.v1',issued_by='codex:/root',scope_ref=sref,canonical_vector_ref=vector,caller_ref=caller))
print(json.dumps(dict(request_ref=request,vector_ref=vector,scope_ref=sref,caller_ref=caller,canonical_refs=refs)),flush=True)
