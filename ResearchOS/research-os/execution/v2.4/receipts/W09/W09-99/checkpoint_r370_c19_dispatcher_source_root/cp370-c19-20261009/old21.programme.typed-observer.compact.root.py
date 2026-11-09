"""Read the pinned finite request and return its exact binding without large stdout."""
from pathlib import Path
import hashlib,json,sys
p=Path(sys.argv[1]);raw=p.read_bytes()
assert len(raw)==43589 and hashlib.sha256(raw).hexdigest()=='f3b605d9ee53962d73e314387fdd65ee3cee3ad63b7e34f2cddde7dc6e0f1cf4'
request=json.loads(raw);assert request['operation']=='OLD21_PROGRAMME_QUALIFICATION_BINDING'
for ref in request['observed_refs']:
    path=Path(ref['path']);assert path.is_absolute() and '..' not in path.parts
    data=path.read_bytes();assert len(data)==ref['bytes'] and hashlib.sha256(data).hexdigest()==ref['sha256']
print(json.dumps(dict(schema='researchos.root-old21-programme-compact-capture-result.v1',issued_by='codex:/root',
    observer_actor='codex:/root',root_thread_id='01a11007-5233-7ca1-b71f-9e9e5ce84c98',operation=request['operation'],
    source='tools.exec_command',observer_input_ref=dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw)),
    observed_ref_count=len(request['observed_refs']),all_requested_refs_read_and_verified=True,payload_ref=request['payload_ref'],
    peer_actor=request['peer_actor'],formal_acceptance=False,parent_acceptance=False,execution_grant=False),ensure_ascii=False))
