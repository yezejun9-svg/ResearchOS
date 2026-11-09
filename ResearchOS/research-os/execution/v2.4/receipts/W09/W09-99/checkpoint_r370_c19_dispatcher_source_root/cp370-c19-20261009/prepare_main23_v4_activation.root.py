"""Observe the actual checked registration facts and current Canon bytes."""
from pathlib import Path
import json,hashlib,os
N=Path(__file__).resolve().parent
R=Path(r'D:\作品集\ResearchOS\research-os')
reg=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/fresh-main23-registration-3ef8ee61a94e4adca86a00f55a8b7a13'
def pin(p):
    raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
facts_ref=pin(reg/'facts.root.json')
assert (facts_ref['sha256'],facts_ref['bytes'])==('dfec0137c083e384cabf9d9d7b0f3f7a2e3b5ad28e8a3c2b1da4fde6509be84b',3558)
result_ref=pin(reg/'check.result.json')
assert (result_ref['sha256'],result_ref['bytes'])==('26b799c21f9c9ba5908a10bcdf542ea4e6b7878317ccd3275e4e36448995465f',2557)
facts=json.loads(Path(facts_ref['path']).read_bytes())
cleanup=json.loads((reg/'check.guard-cleanup.json').read_bytes())
assert cleanup['closed'] and cleanup['retained_handles_count']==0 and not cleanup['errors']
for ref in facts['before_canonical_refs']:
    actual=pin(Path(ref['path']));assert actual==ref
request=dict(operation='ACTIVATION_FACTS_CURRENT_FOUR',observed_refs=[facts_ref]+facts['before_canonical_refs'],peer_actor=None)
p=N/'main23.v4.activation-current4.observer-input.root.json'
with p.open('xb') as f:f.write((json.dumps(request,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
print(json.dumps(dict(observer_input_ref=pin(p),facts_ref=facts_ref,check_result_ref=result_ref,
    Canonical_unchanged=True,guard_closed_zero=True),ensure_ascii=False,indent=2))
