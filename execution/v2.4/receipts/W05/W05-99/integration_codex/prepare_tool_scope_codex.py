"""Freeze the precise effect-to-session projection proposal and reviewer inputs."""
from pathlib import Path
import datetime as dt
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
def ref(path):
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

paths = ['internal/domain/runtime_broker_windows.go', 'internal/domain/runtime_sessions_windows.go',
         'internal/domain/runtime_session_events_windows.go', 'internal/domain/runtime_session_events_windows_test.go']
scope = {
    'schema': 'researchos.w05.tool-projection-scope-proposal.v1',
    'slice_id': 'W05-99-S3-DURABLE-TOOL-EVENTS',
    'status': 'PROPOSED_NOT_AUTHORIZED',
    'prepared_at': dt.datetime.now(dt.timezone.utc).isoformat(),
    'proposer': 'codex:/root',
    'proposed_owner': 'codex:/root',
    'worktree': '.local/worktrees/codex-w0599-tools',
    'source_head': '135b0de35c16b11dc26cdbed1c02f611253df6e5',
    'exact_paths': paths,
    'existing_source_refs': [ref(ROOT / p) for p in paths if (ROOT / p).is_file()],
    'new_paths': [p for p in paths if not (ROOT / p).exists()],
    'independent_architecture_refs': [ref(ROOT / p) for p in [
        'execution/v2.4/receipts/W05/W05-99/architecture_review_codex/tool_event_projection_scope.md',
        'execution/v2.4/receipts/W05/W05-99/architecture_review_codex/tool_event_projection_inputs.json']],
    'implementation_contract': [
        'Persist logical TOOL_STARTED in beginEffectTx transaction, before brokerEffect commits and before any physical RunTool call. Event failure prevents the call; permission waiting is not physical IO.',
        'Project only canonical effect/ledger facts after complete existing ingest validation. Confirmed effect is not tool success: nonzero run_check/timed_out maps FAILED; pre-effect NOT_APPLIED maps BLOCKED; incomplete cancellation remains UNKNOWN.',
        'Use deterministic host tool identity and deterministic event IDs, current real session CAS and original canonical run/task binding. parent_tool_call_id stays null without proven SDK parent facts.',
        'Replay/recovery and the duplicate-ingest branch may repair missed projection/Artifacts, but never redo tool, replay budget charges or renew execution authority. Preserve UNKNOWN observations followed by a real late result.',
        'Derive immutable output/log Artifacts from exact validated host evidence and verify raw byte/base64 and content hashes; never turn omitted bytes or missing raw evidence into empty logs.',
        'USAGE is derived from each actual immutable BudgetLedgerEntry. Reservations and unknown cost yield cost_known=false/money=null with original reservation retained; only genuine ACTUAL entries show known money. Token/provider-usage IDs remain null unless real facts support them.',
        'Current Scan repairs missing effects and bounded historical run ledger projection using original RUN_STATE association, never the newest task as an arbitrary target. Sealed sessions do not acquire new events and cannot block trusted old billing facts.',
        'No new scheduler/fact table, worker, sandbox rewrite, schema/migration/locks/routes or tool behavior edits. No token-stream, nested SDK parent or full LIVE acceptance claim.',
    ],
    'required_tests': [
        'A real current broker invocation blocked inside a tool exposes committed STARTED from another connection before any RESULT; projection failure rolls begin back and physical invocation count stays zero.',
        'Known success, run_check nonzero/timed_out, NOT_APPLIED, UNKNOWN and late trusted result remain distinct; Run cancellation alone never invents tool CANCELLED.',
        'Repeated same effect/fact, restoration after lost projection, original historical session/run and current writer handoff keep deterministic IDs, continuous watermarks and no extra call/cost/Artifact.',
        'Wrong source bindings/fact/evidence hash and unbounded raw data refuse; actual long stdout/stderr refs preserve exact decoded bytes/hash; missing raw stays null.',
        'Original model unknown cost/upper reservation and actual local TOOL zero remain separate; immutable usage entries replay once and late usage stays on original run.',
        'Necessary existing current session/tool/permission/recovery tests remain valid; fixtures and actual current SDK with local fixture ports remain explicitly distinguished from LIVE.',
    ],
    'mode': 'CURRENT_SOURCE_WITH_EXPLICIT_FIXTURE_TESTS_NOT_LIVE_ACCEPTANCE',
    'parent_or_formal_acceptance': False,
    'formal_case_count_delta': 0,
    'current_w04_effect': 'Candidate domain source changes require new current W04 evidence after integration; preserve old proof/history without self-acceptance.',
}
with (HERE / 'tool_source_scope_proposal_codex.json').open('x', encoding='utf8', newline='\n') as stream:
    json.dump(scope, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps({'status': 'PROPOSED_NOT_AUTHORIZED', 'scope_ref': ref(HERE / 'tool_source_scope_proposal_codex.json')}))
