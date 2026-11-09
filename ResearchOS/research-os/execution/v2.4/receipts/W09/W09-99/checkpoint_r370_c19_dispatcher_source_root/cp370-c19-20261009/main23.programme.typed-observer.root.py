"""Actually read every reference needed for Root's programme binding."""
from pathlib import Path
import json,hashlib,sys
request_path=Path(sys.argv[1]);request=json.loads(request_path.read_bytes())
assert request['operation']=='PROGRAMME_QUALIFICATION_BINDING'
for ref in request['observed_refs']:
    p=Path(ref['path']);assert p.is_absolute() and '..' not in p.parts
    raw=p.read_bytes();assert len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256']
print(json.dumps(dict(schema='researchos.root-main23-capture-result.v2',issued_by='codex:/root',
    observer_actor='codex:/root',root_thread_id='01a11007-5233-7ca1-b71f-9e9e5ce84c98',
    operation=request['operation'],source='tools.exec_command',formal_acceptance=False,
    observed_refs=request['observed_refs'],peer_actor=None),ensure_ascii=False))
