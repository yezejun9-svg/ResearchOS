"""Actually read the complete finite reference set for programme qualification."""
from pathlib import Path
import hashlib,json,sys
request=json.loads(Path(sys.argv[1]).read_bytes())
assert request['operation']=='OLD21_PROGRAMME_QUALIFICATION_BINDING'
for ref in request['observed_refs']:
    p=Path(ref['path']);assert p.is_absolute() and '..' not in p.parts
    raw=p.read_bytes();assert len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256']
print(json.dumps(dict(schema='researchos.root-old21-capture-result.v2',issued_by='codex:/root',observer_actor='codex:/root',
    root_thread_id='01a11007-5233-7ca1-b71f-9e9e5ce84c98',operation=request['operation'],source='tools.exec_command',
    observed_refs=request['observed_refs'],peer_actor=request['peer_actor'],formal_acceptance=False,parent_acceptance=False,execution_grant=False),ensure_ascii=False))
