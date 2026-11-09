"""Flat-bind all five actual role origins before the grant body is sealed."""
from pathlib import Path
import hashlib,json,os,runpy,sys,uuid
S=Path(__file__).resolve().parent; W=S.parents[1]; R=S.parents[5]; RUN=W/'w09_br8_actual_root/actual-20261010-01'
def pin(p):
    b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def doc(ref):
    p=Path(ref['path']);p=p if p.is_absolute() else R/p;b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==ref['sha256'] and len(b)==ref['bytes'];return json.loads(b)
builder=pin(W/'w09_br8_role_inputs_root/d2abba5f35784840acaed5cf70b98aed/result.json');assert builder['sha256']=='35e74a5002614b6d1fdb035a60c93f21288da6d10a25ef3ccbd22d2bd2edf389'
value=doc(builder);protection=doc(value['role_protection_refs_ref'])['role_protection_refs'];assert type(protection) is list and len(protection)>0
proposal=pin(RUN/'propose-e1111124d5e54bfc810d9ebe1d167664/result.json');assert proposal['sha256']=='8dec4c07f3e01ef93ffd208ffd2d0a5a0b4b2413c0edf2ed1305de76ca1e381f'
body=dict(proposal_ref=proposal,c19_policy='RUN_CURRENT_CM40',role_registry_input_ref=value['role_registry_input_ref'],role_protection_refs=protection)
p=RUN/('roles-'+uuid.uuid4().hex+'.extras.root.json')
with p.open('xb') as f:f.write((json.dumps(body,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
sys.argv=[str(S/'prepare_br8_actual_stage.root.py'),'prepare','roles',str(p)]
runpy.run_path(sys.argv[0],run_name='__main__')
