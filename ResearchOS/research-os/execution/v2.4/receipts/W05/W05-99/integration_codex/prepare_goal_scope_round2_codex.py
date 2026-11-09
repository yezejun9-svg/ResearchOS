"""Retain the original proposal and add the two observed provenance readers."""
from pathlib import Path
import datetime as dt
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
def ref(path):
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

previous = HERE / 'goal_source_scope_proposal_codex.json'
scope = json.loads(previous.read_bytes())
scope['schema'] = 'researchos.w05.goal-scope-proposal.v2'
scope['prepared_at'] = dt.datetime.now(dt.timezone.utc).isoformat()
scope['previous_proposal_ref'] = ref(previous)
extra = ['internal/domain/runtime_tools_windows.go', 'internal/domain/runtime_permission_windows.go']
scope['exact_paths'].extend(extra)
scope['existing_source_refs'].extend(ref(ROOT / p) for p in extra)
scope['implementation_contract'].append(
    'The two added runtime tool/permission files may only replace the session.create-only principal attribution with the shared real creation receipt helper. This must recognize a successful goal.start snapshot without fabricated receipts, retain original session.create handling, and fail closed on conflicting principal/project/session attribution; no other tool/permission behavior changes.')
scope['required_tests'].append(
    'A project-level Goal-created session has real principal attribution through goal.start; its original frozen tool and permission gates work for that same principal and refuse another principal. No fake session.create idempotency row is created.')
scope['additional_path_reason'] = (
    'Independent reviewer and proposed implementer separately observed current runtime_tools_windows.go:84 and runtime_permission_windows.go:139 JOIN only v2:session.create; the six-path proposal would refuse tools for legitimate Goal-created sessions.')
with (HERE / 'goal_source_scope_proposal_round2_codex.json').open('x', encoding='utf8', newline='\n') as stream:
    json.dump(scope, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps({'status': 'PROPOSED_NOT_AUTHORIZED', 'paths': len(scope['exact_paths']),
                  'scope_ref': ref(HERE / 'goal_source_scope_proposal_round2_codex.json')}))
