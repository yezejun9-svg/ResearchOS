"""Publish the reviewed role proposal byte-for-byte, without overwriting history."""
from pathlib import Path
import contextlib,hashlib,io,json,os,runpy,sys,uuid
S=Path(__file__).resolve().parent; W=S.parents[1]; V=S.parents[4]; R=S.parents[6]; RUN=W/'w09_br8_actual_root/actual-20261010-01'
def pin(p):
    b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def checked(ref):
    p=Path(ref['path']);p=p if p.is_absolute() else R/p;b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==ref['sha256'] and len(b)==ref['bytes'];return b
pubref=pin(RUN/'roles-764da9a75846495cb9557bb8114f6151/result.json');assert pubref['sha256']=='849d93daa16bbdc82427bc1abeb62f669229b6a38acc2bc13d1f76b2c2824e58'
pub=json.loads(checked(pubref));assert pub['fixed_path']=='execution/v2.4/root_delivery_captures/W09/W09-99/execution-roles.json'
raw=checked(pub['payload_ref']);roles=json.loads(raw)
assert roles['writer_actor']=='codex:/root' and roles['run_id']=='5e23bbf04e234bff89472bbdbf9653b2'
assert len(roles['provenance'])==5 and len(roles['route_execution_refs'])==6 and roles['roles']['verifier']=='/root/backup_regression_resources'
cp=json.loads((V/'checkpoint.json').read_bytes());assert cp['revision']==393
previous=cp['work_in_progress'].get('w09_execution_role_registry_ref');assert previous is None
fixed=R/pub['fixed_path'];assert not fixed.exists();fixed.parent.mkdir(parents=True,exist_ok=True)
with fixed.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
assert fixed.read_bytes()==raw
extras=RUN/('publish-registration-'+uuid.uuid4().hex+'.extras.root.json')
body=dict(publication_ref=pubref,expected_previous_registry_ref=previous)
with extras.open('xb') as f:f.write((json.dumps(body,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
sys.argv=[str(S/'prepare_br8_actual_stage.root.py'),'prepare','publish-registration',str(extras)]
stream=io.StringIO()
with contextlib.redirect_stdout(stream):runpy.run_path(sys.argv[0],run_name='__main__')
prepared=json.loads(stream.getvalue());prepared.update(Root_fixed_registry_ref=pin(fixed),exact_publication_bytes=True,Canon_written=False)
print(json.dumps(prepared,ensure_ascii=False))
