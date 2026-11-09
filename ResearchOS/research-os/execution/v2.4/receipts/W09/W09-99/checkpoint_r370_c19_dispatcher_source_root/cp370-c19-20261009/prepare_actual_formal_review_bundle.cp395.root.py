"""Add actual current4 to the prepared public inventory, then seal a constructible bundle."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,uuid
S=Path(__file__).resolve().parent;V=S.parents[4];W=S.parents[1];R=S.parents[6]
def pin(p):
    b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
inv=W/'w09_br8_formal_review_resource_inventory_codex/inventory-20261010-01/resource-inventory.json'
b=inv.read_bytes();assert hashlib.sha256(b).hexdigest()=='1f0e6bd74b7b5f77b5687b9e6153412463fa38e447f17f2b19a222ce458a1f43' and len(b)==1507066
d=json.loads(b)
assert d['resource_count']==len(d['resource_refs'])==2102 and d['later_Root_current4_refs'] is None
current=[pin(V/n) for n in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')]
assert current[0]['sha256']=='60c2b89163ebf1522454331a6b774bf80c801d262208872db981b7b1e85a09d2' and current[1]['sha256']=='b949831cc4827ae2cadae77235188dfff0776a0c8074a57714c1445e16c32a86'
resources=d['resource_refs']+current
keys=[str(Path(r['path']).resolve(strict=True)).casefold() for r in resources]
assert len(keys)==len(set(keys))==2106 and all(Path(r['path']).is_absolute() and set(r)=={'path','sha256','bytes'} for r in resources)
assert pin(Path(d['context_resource_ref3']['path']))==d['context_resource_ref3'] and d['context_ref2']['sha256']==d['context_resource_ref3']['sha256']=='70a5fc149e2fda2fbf6d9ce518ec7c34d11d07f2f1985cf8d68f32b20652562c'
body=dict(schema='researchos.w09-br6-formal-actual-review-input.v1',context_ref=d['context_ref2'],consumer_result_ref=d['consumer_result_ref'],root_publication_refs=d['root_publication_refs'],current4_refs=current,resource_refs=resources,native_mode_qualification_ref=d['native_mode_qualification_ref'])
sid=uuid.uuid4().hex;RUN=W/'w09_br8_actual_root/actual-20261010-01';p=RUN/('formal-review-'+sid+'.bundle.actual.root.json')
with p.open('xb') as f:f.write((json.dumps(body,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
input_ref=pin(p);assert str(p.resolve()).casefold() not in keys
caller=W/'w09_br8_formal_actual_review_codex/prepare-20261010-01/br8_actual_review.source.py';assert pin(caller)['sha256']=='08db9f87cd186f14713e74f853dff88a169bb979fa566db5c1e661c134f700c6'
review=W/'w09_br8_formal_actual_review_independent_source_review_codex/review-20261010-01-full/review-decision.json';assert pin(review)['sha256']=='212ad90068ed7a11c65062b28a12a5b09fc63534e0f75f341d686211eea2938b'
actual_capture=S/'w09.br8-and-main24-source-review-redelivery02.actual-audit.root.json';assert pin(actual_capture)['sha256']=='37b1da9e066ca894355c106e2c30abe421009edd7c9c899bc4811c46fbc45ec8'
out=caller.parent/('actual-'+sid);assert not out.exists()
packet=dict(schema='researchos.w09-root-actual-formal-review-packet.v1',issued_by='codex:/root',verifier_actor='/root/backup_regression_resources',created_at=datetime.now(timezone.utc).isoformat(),input_ref=input_ref,caller_ref=pin(caller),independent_Source_review_ref=pin(review),independent_Source_true_final_capture_ref=pin(actual_capture),output_root=str(out),current4=current,resource_count=2106,execution_grant_scope='ONE_ACTUAL_INDEPENDENT_FORMAL_REVIEW_NO_NATIVE_REPLAY',formal_acceptance=False,Root_capture_index_issuance_owner_future=True)
pp=RUN/('formal-review-'+sid+'.packet.actual.root.json')
with pp.open('xb') as f:f.write((json.dumps(packet,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
assert current==[pin(V/n) for n in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')]
print(json.dumps(dict(packet_ref=pin(pp),input_ref=input_ref,caller_ref=pin(caller),output_root=str(out),resource_count=2106,current4=current,formal_acceptance=False),ensure_ascii=False))
