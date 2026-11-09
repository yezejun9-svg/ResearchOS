"""Read bounded Root refs and return one typed line for genuine host capture."""
from pathlib import Path
import json, hashlib, sys
THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
allowed={'SOURCE_REVIEW_WITNESS','BUILDER_SOURCE_REVIEW_WITNESS','RUNTIME_QUALIFICATION_ISSUANCE',
    'POSTREVIEW_CURRENT_FOUR','ACTIVATION_FACTS_CURRENT_FOUR','OLD21_BUILD_PREREQUISITES'}
path=Path(sys.argv[1]); assert path.is_absolute()
request=json.loads(path.read_bytes()); assert request['operation'] in allowed
for ref in request['observed_refs']:
    target=Path(ref['path']); assert target.is_absolute() and '..' not in target.parts
    raw=target.read_bytes(); assert (len(raw),hashlib.sha256(raw).hexdigest())==(ref['bytes'],ref['sha256'])
print(json.dumps(dict(schema='researchos.root-old21-capture-result.v2',issued_by='codex:/root',
    observer_actor='codex:/root',root_thread_id=THREAD,operation=request['operation'],source='tools.exec_command',
    formal_acceptance=False,observed_refs=request['observed_refs'],peer_actor=request['peer_actor']),ensure_ascii=False))
