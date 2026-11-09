"""Observe actual registered Scope/Owner and prepare six current consumers."""
from pathlib import Path
import contextlib,hashlib,io,json,os,runpy,sys,uuid
S=Path(__file__).resolve().parent; W=S.parents[1]; V=S.parents[4]; RUN=W/'w09_br8_actual_root/actual-20261010-01'
def pin(p):
    b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def doc(ref):
    p=Path(ref['path']);p=p if p.is_absolute() else V.parents[1]/p;b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==ref['sha256'] and len(b)==ref['bytes'];return json.loads(b)
p=RUN/'propose-e1111124d5e54bfc810d9ebe1d167664/result.json';pr=pin(p)
assert pr['sha256']=='8dec4c07f3e01ef93ffd208ffd2d0a5a0b4b2413c0edf2ed1305de76ca1e381f' and pr['bytes']==2047990
proposal=doc(pr); act=pin(RUN/'activate-d012301df2404531b8a15ec84d1aeddd/result.json');assert act['sha256']=='ea2998bb8818f332b580f993803a9149ebc3a68ea109d53a8056058dc940d742'
activation=doc(act);assert pin(V/'checkpoint.json')==activation['checkpoint_ref'] and pin(V/'path_ownership.json')==activation['ownership_ref']
docs=proposal['documents']; scope=doc(docs['consumers']['scope_ref']); owner=doc(docs['assembly']['owner_ref'])
assert scope['issued_by']=='codex:/root' and owner['owner_id']=='codex:/root' and owner['lease_status']=='ACTIVE'
isolation=RUN/('isolated-consumers-'+uuid.uuid4().hex);isolation.mkdir()
env={k:str(isolation/k) for k in ('USERPROFILE','LOCALAPPDATA','APPDATA')}
for value in env.values():Path(value).mkdir()
env.update(TEMP=r'C:\Users\yqyyds\.researchos\w09-native-v5',TMP=r'C:\Users\yqyyds\.researchos\w09-native-v5')
extras=RUN/('consume-'+uuid.uuid4().hex+'.extras.root.json')
body=dict(proposal_ref=pr,context_seed_ref=proposal['context_seed_ref'],c19_policy='RUN_CURRENT_CM40',isolated_environment=env)
with extras.open('xb') as f:f.write((json.dumps(body,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
sys.argv=[str(S/'prepare_br8_actual_stage.root.py'),'prepare','consume',str(extras)]
stream=io.StringIO()
with contextlib.redirect_stdout(stream):runpy.run_path(sys.argv[0],run_name='__main__')
prepared=json.loads(stream.getvalue());prepared.update(actual_scope_observation_ref=docs['consumers']['scope_ref'],actual_assembly_owner_observation_ref=docs['assembly']['owner_ref'],activation_result_ref=act,Canon_written=False,producer_rerun=False)
print(json.dumps(prepared,ensure_ascii=False))
