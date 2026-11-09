import hashlib
import json
from pathlib import Path
import subprocess
import sys

if sys.flags.optimize != 0:
    raise RuntimeError('Optimized Python prohibited')
ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
items = [
    'internal/domain/client_protocol.go',
    'internal/domain/client_protocol_sessions.go',
    'internal/domain/client_protocol_queue_control.go',
    'internal/domain/durability.go',
    'internal/domain/runtime_coordinator_windows.go',
    'internal/domain/runtime_sessions_windows.go',
    'internal/domain/operations.go',
    'internal/domain/orchestration_controls.go',
    'apps/cli/cli_verbs.go',
    'adapters/runtime/mu/worker.mjs',
    '.local/worktrees/v24-continuation/spec/v2.4/22_CLIENT_INTERFACE_DETAILS.md',
    '.local/worktrees/v24-continuation/spec/v2.4/contracts/client.protocol.schema.json',
]


def save(name, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    with (OUT / name).open('xb') as stream:
        stream.write(raw)
    return {'path': (OUT / name).relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


refs = []
originals = {}
for index, relative in enumerate(items):
    path = ROOT / relative
    raw = path.read_bytes()
    originals[path] = raw
    target = OUT / 'sources' / (str(index).zfill(2) + '-' + path.name + '.txt')
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as stream:
        stream.write(raw)
    assert target.read_bytes() == raw
    refs.append({'original_path': relative, 'snapshot_path': target.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)})
git = 'C:/Program Files/Git/cmd/git.exe'
head = subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
assert head == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
assert all(path.read_bytes() == raw for path, raw in originals.items())
diagnostics = save('root-tool-originals.json', {'origins': [
    {'origin_key': 'W05-99/root-resume-readonly/tool-424441', 'actual_outer_exit': 1,
     'tool_chunk': '424441', 'cause': 'Root positional Windows literal wildcards client_protocol*.go/goal*.go and guessed tasks.go failed IO; no product or canonical change.',
     'original_locator': 'functions.exec/exec_command chunk424441; original tool response retained in conversation', 'separately_captured_native_raw_file_available': False,
     'correction': 'daa6a9 used actual directory with -g filters and returned actual0; no same-argv rerun.'},
    {'origin_key': 'W05-99/root-resume-readonly/tool-4a367e', 'actual_outer_exit': 1,
     'tool_chunk': '4a367e', 'cause': 'Root guessed nonexistent internal/domain/control.go in second rg query; known source reads were readonly; no product/canonical change.',
     'original_locator': 'functions.exec/exec_command chunk4a367e; original tool response retained in conversation', 'separately_captured_native_raw_file_available': False,
     'correction': '175b04 actual directory query found orchestration_controls.go and returned actual0; no same-argv rerun.'}
], 'tests_SQL_Go_Node_models': 0, 'counter_reset': False, 'count_once_per_outer_query_batch': True})
findings = save('findings.json', {'status': 'READONLY_REAL_RESUME_PRODUCER_GAP_NOT_A_CLOSED_IMPLEMENTATION_SCOPE',
    'actor': 'codex:/root', 'Main_head': head, 'public_source_refs': refs,
    'facts': [
        {'id': 'R01', 'locator': '22_CLIENT_INTERFACE_DETAILS.md:76,151-153', 'fact': 'session.control target must belong to current session Goal/Run. Resume requires valid paused/recovery context, cancelled Run not revived; explicit continuation may create provenance-preserving new attempt/run, retaining original cancellation/budget/failure counts.'},
        {'id': 'R02', 'locator': 'internal/domain/client_protocol.go:1120-1149', 'fact': 'Existing special RESUME target=session checks queue/previous terminal stop facts, builds snapshot, returns COMPLETED without checkpoint resume, new attempt or runtime producer.'},
        {'id': 'R03', 'locator': 'apps/cli/cli_verbs.go:77-110', 'fact': 'Both CLI resume operation lists send target_id=session. The schema minLength alone does not establish prose-required Goal/Run membership.'},
        {'id': 'R04', 'locator': 'internal/domain/durability.go:259-401', 'fact': 'ResumeCheckpoint has its own BeginTx/Commit and token-based SCHEDULER validation. It requires current nonterminal Run/active Task/Goal/checkpoint/trusted stopped observation/effects reconciliation/input/dependency/admission; rebuilds context, rotates lease, carries checkpoint and prepares native dispatch if native. Terminal/cancel-requested cannot use it.'},
        {'id': 'R05', 'locator': 'internal/domain/client_protocol_sessions.go:14-20', 'fact': 'ClientSessionRuntime interface exposes only sameTx ValidateBinding/AdmitTurn; comments prohibit launch/provider requests/second Tx. Calling public ResumeCheckpoint inside this interface or envelope Tx would violate the existing transaction boundary.'}
    ],
    'implementation_obligations': [
        'Resolve lawful current Goal/Run target from authoritative snapshot and original membership; refuse session-id target or wrong/foreign/obsolete identity with typed error, without manufacturing execution.',
        'Define actual PAUSE checkpoint/stop reconciliation producer and RESUME admission/new attempt routes separately from snapshot observation; determine exact worker/coordinator/bridge support before claiming a closed file list.',
        'Retain CANCELLED Run and immutable old command/effect/budget/failure/event facts; never nested-call token service methods in current client Tx and never relabel permanent ACK or snapshot-only COMPLETED as recovery.',
        'Protect old22/23 controls, F08 sameTx finalization scope and history/LIVE held lanes. Before edits, freeze exact path/function/producer/control/native selectors and obtain nonauthor scope review plus Root canonical registration.'
    ], 'control_execution': 'NOT_RUN', 'SQL_or_source_edit_authorization': False,
    'formal_increment': 0, 'source_acceptance': False, 'paid_calls': 0,
    'diagnostics_ref': diagnostics})
handoff = save('handoff.json', {'status': 'ACTIVE_PRODUCT_GAP_PENDING_EXACT_PRODUCER_SCOPE', 'findings_ref': findings,
    'original_cli69_26_preserved': True, 'P02_cli_and_aggregate_ids': 'HOLD_PENDING_REAL_RECOVERY',
    'other_P01_P03_P04_exact_fix_proposal': 'Independent Source branch continues; no source edits in this receipt.',
    'original_failure_refs': diagnostics, 'Main_source_or_canonical_writes': 0, 'Go_Node_SQL_HTTP_model_executions': 0,
    'all22_and42_required': True, 'counter_reset': False})
files = [{'path': path.relative_to(OUT).as_posix(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'bytes': path.stat().st_size} for path in sorted(OUT.rglob('*')) if path.is_file()]
manifest = save('manifest.json', {'self_excluded': True, 'files': files})
print(json.dumps({'findings_ref': findings, 'handoff_ref': handoff, 'manifest_ref': manifest, 'captured_public_sources': len(refs), 'product_execution': 0}, ensure_ascii=True))
