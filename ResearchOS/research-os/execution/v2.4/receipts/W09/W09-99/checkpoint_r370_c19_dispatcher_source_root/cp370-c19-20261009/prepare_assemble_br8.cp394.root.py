"""Bind actual consumers, registered-role seed, frozen plan and refusal evidence."""
from pathlib import Path
import hashlib,json,os,runpy,sys,uuid
S=Path(__file__).resolve().parent;W=S.parents[1];R=S.parents[6];RUN=W/'w09_br8_actual_root/actual-20261010-01'
def pin(p):
    b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def doc(ref):
    p=Path(ref['path']);p=p if p.is_absolute() else R/p;b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==ref['sha256'] and ('bytes' not in ref or len(b)==ref['bytes']);return json.loads(b)
seed_result=pin(RUN/'seed-e8289431c01f463f9abd2173d5789c5e/result.json');assert seed_result['sha256']=='771fc68490f33787e56c0e01dde466257283de830c3d9b3767c76d9248395e0f'
seed=doc(seed_result)['context_ref'];context=doc(seed);assert context['run_id']=='5e23bbf04e234bff89472bbdbf9653b2'
proposal=pin(RUN/'propose-e1111124d5e54bfc810d9ebe1d167664/result.json');assert proposal['sha256']=='8dec4c07f3e01ef93ffd208ffd2d0a5a0b4b2413c0edf2ed1305de76ca1e381f'
consumer=pin(RUN/'consume-fb16497eef2f43c2858a3e00df3ba31f/result.json');assert consumer['sha256']=='02ebf5113249e0e0d74ad425be3f78e5898826da95ebe41f21ef86f77d8008f0'
template=json.loads((W/'w09_br8_postactivation_call_preparation_codex/prepare-20261010-01/extras/assemble.template.json').read_bytes())
refusal=template['refusal_evidence_refs'];assert type(refusal) is list and len(refusal)>0
for ref in refusal:
    actual=doc({k:ref[k] for k in ('path','sha256')})['actual'];assert actual['http_path_traversal_rejected'] is True and actual['secret_marker_leaks']==0
manifest=[r for r in context['version_vector']['spec_files'] if Path(r['path']).name=='PACKAGE_MANIFEST.json'];assert len(manifest)==1;doc(manifest[0])
body=dict(proposal_ref=proposal,context_seed_ref=seed,consumer_result_ref=consumer,c19_policy='RUN_CURRENT_CM40',plan_ref=pin(R.parent/'ResearchOS_Implementation_Package_v2.4/contracts/execution.plan.json'),code_revision='adc460c2138528f163f7fdab5e8d81dde157b7fb',dirty=True,package_manifest_ref=manifest[0],refusal_evidence_refs=refusal)
p=RUN/('assemble-'+uuid.uuid4().hex+'.extras.root.json')
with p.open('xb') as f:f.write((json.dumps(body,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
sys.argv=[str(S/'prepare_br8_actual_stage.root.py'),'prepare','assemble',str(p)]
runpy.run_path(sys.argv[0],run_name='__main__')
