"""Bind the newly produced BR8 proposal to a fresh current4 grant."""
from pathlib import Path
import hashlib,json,os,runpy,sys,uuid
S=Path(__file__).resolve().parent; W=S.parents[1]; RUN=W/'w09_br8_actual_root/actual-20261010-01'
p=RUN/'propose-e1111124d5e54bfc810d9ebe1d167664/result.json'; b=p.read_bytes()
assert hashlib.sha256(b).hexdigest()=='8dec4c07f3e01ef93ffd208ffd2d0a5a0b4b2413c0edf2ed1305de76ca1e381f' and len(b)==2047990
proposal=json.loads(b); assert proposal['generation']=='bridge-20261010-08' and proposal['c19_policy']=='RUN_CURRENT_CM40'
extras=RUN/('activate-'+uuid.uuid4().hex+'.extras.root.json')
body=dict(proposal_ref=dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b)),c19_policy='RUN_CURRENT_CM40')
with extras.open('xb') as f: f.write((json.dumps(body,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
sys.argv=[str(S/'prepare_br8_actual_stage.root.py'),'prepare','activate',str(extras)]
runpy.run_path(sys.argv[0],run_name='__main__')
