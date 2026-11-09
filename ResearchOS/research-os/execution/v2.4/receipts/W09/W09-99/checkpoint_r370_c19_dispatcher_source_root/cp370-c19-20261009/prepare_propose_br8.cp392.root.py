"""Prepare a fresh finite proposal lease; retain prior failure and seed."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib,json,os,runpy,sys,uuid
S=Path(__file__).resolve().parent; W=S.parents[1]
RUN=W/'w09_br8_actual_root/actual-20261010-01'
p=RUN/'seed-c0b41d982ba14201965fe05216e9c82b/result.json'; b=p.read_bytes()
assert hashlib.sha256(b).hexdigest()=='60f9250bdf24683e51c4663351b45a02728e9d883cc334767b3f6730d9b66291' and len(b)==90563
seed=json.loads(b)['context_ref']
body=dict(context_seed_ref=seed,c19_policy='RUN_CURRENT_CM40',lease_expires_at=(datetime.now(timezone.utc)+timedelta(minutes=45)).isoformat())
extras=RUN/('propose-finite-lease-'+uuid.uuid4().hex+'.extras.root.json')
with extras.open('xb') as f: f.write((json.dumps(body,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
sys.argv=[str(S/'prepare_br8_actual_stage.root.py'),'prepare','propose',str(extras)]
runpy.run_path(sys.argv[0],run_name='__main__')
