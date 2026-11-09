"""Record the Root's current, exact references for one actual host observation."""
from pathlib import Path
import json, hashlib, sys

THREAD = '01a11007-5233-7ca1-b71f-9e9e5ce84c98'
ALLOWED = {'RUNTIME_QUALIFICATION_ISSUANCE', 'SOURCE_REVIEW_WITNESS',
           'POSTREVIEW_CURRENT_FOUR', 'ACTIVATION_FACTS_CURRENT_FOUR'}
request_path = Path(sys.argv[1])
assert request_path.is_absolute()
request = json.loads(request_path.read_bytes())
assert request['operation'] in ALLOWED
for ref in request['observed_refs']:
    path = Path(ref['path'])
    assert path.is_absolute() and '..' not in path.parts
    raw = path.read_bytes()
    assert len(raw) == ref['bytes'] and hashlib.sha256(raw).hexdigest() == ref['sha256']
result = dict(schema='researchos.root-main23-capture-result.v2', issued_by='codex:/root',
              observer_actor='codex:/root', root_thread_id=THREAD,
              operation=request['operation'], source='tools.exec_command',
              formal_acceptance=False, observed_refs=request['observed_refs'],
              peer_actor=request['peer_actor'])
print(json.dumps(result, ensure_ascii=False, indent=2))
