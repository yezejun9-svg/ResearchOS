"""Freeze the proposed Goal handler boundary; this does not grant source writes."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
paths = [
    'internal/domain/client_protocol.go',
    'internal/domain/client_protocol_sessions.go',
    'internal/domain/client_protocol_goal.go',
    'internal/domain/client_protocol_goal_test.go',
    'internal/domain/runtime_goal_bindings_windows.go',
    'internal/domain/runtime_goal_bindings_windows_test.go',
]
def ref(path):
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

scope = {
    'schema': 'researchos.w05.goal-scope-proposal.v1',
    'slice_id': 'W05-99-S2-GOAL-START',
    'status': 'PROPOSED_NOT_AUTHORIZED',
    'prepared_at': dt.datetime.now(dt.timezone.utc).isoformat(),
    'proposer': 'codex:/root',
    'proposed_owner': 'codex:/root/w1101_map',
    'source_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
    'exact_paths': paths,
    'existing_source_refs': [ref(ROOT / p) for p in paths if (ROOT / p).is_file()],
    'new_paths': [p for p in paths if not (ROOT / p).exists()],
    'inputs': [ref(ROOT / p) for p in [
        'internal/api/contracts/client.protocol.schema.json',
        'internal/domain/operations.go',
        'internal/domain/orchestration.go',
        'internal/domain/goal.go',
    ] if (ROOT / p).is_file()],
    'implementation_contract': [
        'Implement the frozen goal.start method inside the original authenticated, schema-first, idempotent transaction. A method COMPLETED means Goal creation only.',
        'Session-scoped requests retain every current principal/session Owner, client writer, revision, epoch, lease, workspace/model and previous-turn settlement gate. Project-scoped null CAS cannot weaken any existing session write.',
        'Project-only requests require an explicit host resolver for the unique currently authorized workspace/model binding. Refuse absent, multiple, revoked or mismatched bindings before business writes. Create a real mapped session with native reference and host lease, never a fabricated snapshot.',
        'Use an internal common finite execution builder from the existing sendClientMessage chain, rather than forging session.send responses, creating another coordinator or copying business authority.',
        'Empty contract refs use the existing clientTurnContract mandatory check, EXACT versions and independent verifier. This is one finite response with exact raw objective provenance, never proof that the business Goal is complete.',
        'Every supplied contract Artifact is visible to this principal/project, current/effective, sealed and byte/hash verified, then parsed into an actual valid acceptance contract. Merge only non-conflicting checks without silently dropping required IDs; reject invalid or conflicting content before creation.',
        'Draft creates the real Goal/Requirement/session association only and never a Task, Run or dispatch. Non-draft uses existing Goal activation, Task/Context/submission, runtime purpose/qualification and budget gates; unavailable admission is visibly BLOCKED.',
        'Keep original problem/candidate lineage and all prior failure, reservation and cancellation facts. Starting a Goal does not revive cancelled or unresolved work or reset its counters.',
        'Session creation attribution and list/owner visibility also recognize real goal.start receipts; never insert an invented session.create receipt.',
        'No schema, migration, fixed route/model selection, dependency lock, worker, tool or shared registry edits. CLI envelope compatibility belongs to the separately registered S1 owner.',
    ],
    'required_tests': [
        'Project-level null CAS with a real uniquely authorized binding produces schema-valid real SessionSnapshot; missing, multiple or revoked binding leaves no partial writes.',
        'Session-level stale revision/epoch, other principal/client, expired lease, archived/sealed session and unresolved previous Task refuse before new Goal/Task.',
        'Draft has no new Task/Run/provider effect; explicit non-draft empty refs use unchanged bounded independent contract, not business acceptance.',
        'Contract artifact wrong project, protected/invisible, stale, unsealed, hash-tampered, invalid structure, conflicting required IDs all refuse atomically; valid multiple contracts retain all required IDs.',
        'Same command ID and request replay the exact original identity/result; changed payload conflicts; typed rejection rolls back intermediate session/Requirement/Goal/Task.',
        'Current blocked admission preserves true Goal/Task status and fixed model; no unknown cost becomes zero, no missing provider or runtime becomes success.',
        'Existing session.send and session creation/list/owner regression remain valid; no independent acceptance is issued by the handler.',
    ],
    'mode': 'CURRENT_SOURCE_WITH_EXPLICIT_FIXTURE_TESTS_NOT_LIVE_ACCEPTANCE',
    'parent_or_formal_acceptance': False,
    'formal_case_count_delta': 0,
    'current_w04_effect': 'These domain paths intersect the W04 coverage vector. Actual changes must mark that current evidence NEEDS_REVALIDATION; old receipts remain immutable and no acceptance is fabricated.',
}
with (HERE / 'goal_source_scope_proposal_codex.json').open('x', encoding='utf8', newline='\n') as stream:
    json.dump(scope, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps({'status': 'PROPOSED_NOT_AUTHORIZED', 'scope_ref': ref(HERE / 'goal_source_scope_proposal_codex.json')}))
