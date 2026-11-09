"""Bind genuine existing role observations; no fixed registry publication."""
from pathlib import Path
import hashlib,json,os,uuid
S=Path(__file__).resolve().parent; W=S.parents[1]; R=S.parents[6]
RUN=W/'w09_br8_actual_root/actual-20261010-01'
def pin(p):
    b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
proposal=pin(RUN/'propose-e1111124d5e54bfc810d9ebe1d167664/result.json');assert proposal['sha256']=='8dec4c07f3e01ef93ffd208ffd2d0a5a0b4b2413c0edf2ed1305de76ca1e381f'
context=json.loads(Path(proposal['path']).read_bytes())['context_seed_ref']
refs={
    'mode01_observation_audit_ref':pin(S/'w09.br8-existing-mode01-observation.actual-audit.root.json'),
    'assembly_owner_observation_audit_ref':pin(S/'w09.br8-assembly-owner-observation.actual-audit.root.json'),
    'scope_observation_audit_ref':pin(S/'w09.br8-consumers-scope-observation.actual-audit.root.json')}
assert [refs[k]['sha256'] for k in refs]==['d9465bc133112cf36215fdee032138c9719d48249d3581d76a3450bf8c70b809','be792f6ef51ce05efa01cd215c37f9b9ae723cf4ef9d94a16ef3ece8028cf03c','45c2ab22427f68cec315f127aebba9394e5f6272e1813461c981951e87db7a76']
body=dict(schema='researchos.w09-role-input-builder-request.v1',actor_id='codex:/root',preparation_id=uuid.uuid4().hex,proposal_ref=proposal,context_seed_ref=context,**refs)
p=RUN/('role-builder-'+body['preparation_id']+'.request.root.json')
with p.open('xb') as f:f.write((json.dumps(body,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
print(json.dumps(dict(request_ref=pin(p),preparation_id=body['preparation_id'],formal_acceptance=False,registry_published=False),ensure_ascii=False))
