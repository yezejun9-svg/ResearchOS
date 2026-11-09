"""Read D: source/evidence; write only the explicitly authorized C: packet."""
import collections
import datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'w14-diagnosis'
MAIN = Path('D:/作品集/ResearchOS/research-os')
SPEC = Path('D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4')
PRIOR = MAIN / 'execution/v2.4/receipts/W05/W05-99/cli-prompt-bridge-20261104/author'
PURE = ROOT / 'pure-scalar'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def put(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

def load(path):
    return json.loads(Path(path).read_bytes())

OUT.mkdir(exist_ok=False)
session = load(ROOT / 'SESSION.json')
put(OUT / 'collection-operation.json', {'argv': sys.argv, 'cwd': str(Path.cwd()), 'controller': str(Path(__file__).resolve()),
    'operations': 'Read and hash explicit D source/evidence paths; write only C w14-diagnosis and the requested pure-scalar evidence statistics file.',
    'subprocesses': [], 'tests_rerun': False, 'd_writes': False})
sources = [
    (MAIN / 'apps/cli/cli_sessions_test.go', [(27, 40), (135, 174), (198, 262)]),
    (MAIN / 'internal/domain/client_protocol.go', [(632, 657), (725, 762), (905, 979), (1144, 1247), (1301, 1319), (1336, 1371), (1374, 1495)]),
    (MAIN / 'internal/domain/client_protocol_sessions.go', [(14, 21), (416, 467)]),
    (MAIN / 'internal/domain/client_protocol_atomic_test.go', [(60, 72), (232, 245)]),
    (MAIN / 'internal/domain/client_protocol_queue_control.go', [(174, 211), (214, 232)]),
    (MAIN / 'internal/domain/runtime_coordinator_windows.go', [(689, 725)]),
    (MAIN / 'internal/domain/runtime_command_queue_windows.go', [(15, 44), (307, 316)]),
    (MAIN / 'internal/domain/v24_sessions.go', [(152, 179)]),
    (MAIN / 'internal/host/native.go', [(120, 137), (175, 196)]),
    (MAIN / 'internal/host/bootstrap.go', [(53, 98)]),
    (MAIN / 'internal/api/v2.go', [(64, 81)]),
    (SPEC / '22_CLIENT_INTERFACE_DETAILS.md', [(128, 147)]),
    (SPEC / '19_DESKTOP_IMPLEMENTATION_BLUEPRINT.md', [(190, 195)]),
    (SPEC / '14_CLI_DESKTOP_PRODUCT.md', [(68, 72)]),
]
source_evidence = []
for path, ranges in sources:
    text = path.read_text(encoding='utf-8')
    lines = text.splitlines()
    source_evidence.append({'path': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size,
        'excerpts': [{'first_line': first, 'last_line': last,
                      'lines': [{'line': n, 'text': lines[n-1]} for n in range(first, min(last, len(lines))+1)]}
                     for first, last in ranges]})
put(OUT / 'source-evidence.json', {'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'baseline_checkpoint': session['baseline_checkpoint'], 'baseline_head_from_checkpoint': session['baseline_head_from_checkpoint'],
    'git_recheck_in_this_packet': 'NOT_EXECUTED',
    'identity_limit': 'Hashes bind the files actually read now. No new Git/CP state or commit ancestry is inferred from a source read.',
    'files': source_evidence})

evidence_rows = []
for label, directory, names in [
    ('candidate-checks02', PRIOR / 'checks-02', ['inputs.json', 'result.json', 'stdout.txt', 'stderr.txt']),
    ('base-overlay-w14', PRIOR / 'baseline-w14-01', ['inputs.json', 'result.json', 'stdout.txt', 'stderr.txt', 'overlay.json', 'git-commands.json']),
]:
    target = OUT / 'prior-evidence' / label
    target.mkdir(parents=True)
    for name in names:
        path = directory / name
        copy = target / name
        shutil.copyfile(path, copy)
        evidence_rows.append({'original_path': str(path), 'copied_path': str(copy.relative_to(OUT)),
                              'sha256': sha(path), 'copy_sha256': sha(copy)})
candidate_output = (PRIOR / 'checks-02/stdout.txt').read_text(encoding='utf-8')
base_output = (PRIOR / 'baseline-w14-01/stdout.txt').read_text(encoding='utf-8')
if 'HOST_REJECTED:WRITER_BUSY' not in candidate_output or 'HOST_REJECTED:WRITER_BUSY' not in base_output:
    raise RuntimeError('prior W14 failure evidence not found')
put(OUT / 'prior-test-evidence.json', {'status': 'COPIED_EXISTING_FAILURE_EVIDENCE_NO_RERUN',
    'candidate_exit': load(PRIOR / 'checks-02/result.json')['exit_code'],
    'base_overlay_exit': load(PRIOR / 'baseline-w14-01/result.json')['exit_code'],
    'base_head': load(PRIOR / 'baseline-w14-01/inputs.json')['base_head'],
    'same_failure': 'TestW14CLICommandsUseRealSessionHTTP / cli_sessions_test.go:237 / HOST_REJECTED:WRITER_BUSY',
    'baseline_overlay_environment': load(PRIOR / 'baseline-w14-01/inputs.json')['environment_overrides'],
    'boundary': 'Historical candidate and exact base overlay both fail. This packet did not re-run them against CP586/Main556cdc35.',
    'files': evidence_rows})

brief = '''# W14 writer takeover diagnosis and construction brief

This packet is read-only diagnosis and a proposed future scope. It does not change ResearchOS, qualify native identity, or mark W14 accepted. CP586/Main556cdc353f47167e5609f23291bf2746e3c8896f is the checkpoint baseline; this archival run does not repeat the disconnected Git check.

## Verified failure and distinction

The unchanged W14 CLI/API fixture and the preserved fc2b1a50662580b1a0fca92559ca26be6e959f01 build overlay both failed at apps/cli/cli_sessions_test.go:237 with HOST_REJECTED:WRITER_BUSY. Original evidence is copied byte-for-byte under prior-evidence/ and hashed in prior-test-evidence.json. No unchanged test was rerun for this packet.

The immediate cause is internal/domain/client_protocol.go:1197-1198: a still-valid lease owned by a different client_id is rejected before settlement is examined. W14 created the session immediately, reused its authenticated Owner token, and changed only the client id (test:234-237). This is not a regression caused by the later prompt bridge.

The frozen specification requires more than this conservative refusal: 22_CLIENT_INTERFACE_DETAILS.md:130 defines attach(true) with observed expected_revision and null writer_epoch; :132 requires current, proven same authenticated local OS subject; :136 requires one durable handoff intent; :137 explicitly says another same-subject client with a valid lease is accepted as ACKNOWLEDGED while the target remains read-only; :138 requires pausing new dispatch and preserving work/checkpoints/queued follow-ups; :139 requires rechecking authority and input state before atomic owner/epoch/revision transfer and CLIENT_HANDOFF; :140-141 preserve CAS conflict and CANCEL priority; :143 defines renewal and host time; :145 says lease expiry proves no process settlement. Related UI behavior is fixed at 19_DESKTOP_IMPLEMENTATION_BLUEPRINT.md:194; current-writer handoff ordering is also in 14_CLI_DESKTOP_PRODUCT.md:71. Exact bytes, hashes and numbered excerpts are in source-evidence.json.

## Preconditions missing from the old fixture

1. cliSessionBindingFixture.AdmitTurn (cli_sessions_test.go:38-40) always returns RESOURCE_UNAVAILABLE: there is no LIVE runtime or Coordinator. The message is saved as BLOCKED plus ERROR, with no Run, not as proof that every process/effect/control is settled. The test's comment at :232 conflates blocked and settled.
2. The fixture has a synthetic domain Owner token and supplied client ids, not fresh native evidence that both current and target client belong to the same authenticated OS principal on the current host. It is not a native identity qualification.
3. It never establishes a durable takeover intent, dispatch hold, completed checkpoint/queue reconciliation, or a completed transfer receipt before assuming control can move.
4. It does not distinguish ACK admission from final ownership. An ACK cannot be treated as a new epoch or authority to write. The test must wait for canonical completion and observe the returned snapshot.

There is also a second implementation barrier: attachSettlement (client_protocol.go:1374, :1408-1410) reuses clientTurnSettled (client_protocol_sessions.go:416, :428-430). A task with no active_run_id must be ACCEPTED/CANCELLED/FAILED; a never-dispatched BLOCKED task does not pass. Expiring the fixture's lease or deleting the first guard alone therefore cannot supply the missing proof. Do not relax this shared predicate: it also prevents new messages from overwriting unfinished tasks and guards configuration changes.

## Missing completion and Coordinator boundary

Execute at client_protocol.go:732 returns original ACKs unchanged for every method except session.control. Only session.control ACK reaches finalizeClientCancel (:749-750). Returning ACK from attach without an attach-specific replay/finalization path would produce a permanent ACK. Keep the original ACK and the later final receipt independently auditable under the same exact command/hash; do not mutate old immutable receipts into invented completions.

ClientSessionRuntime currently has only ValidateBinding and AdmitTurn (client_protocol_sessions.go:17-20); its contract explicitly forbids worker launches or second transactions inside the command transaction. RuntimeCoordinator handling at runtime_coordinator_windows.go:693-720 finalizes and consumes an already-PAUSED journal, but does not establish that attach requested a safe pause. The existing CANCEL controls/fenceClientTask clear/fence work and are not a handoff implementation. ClientService currently has no attach-specific durable intent consumer or fresh same-OS client proof port.

## Proposed bounded construction scope

The first slice may handle only an authenticated same-OS takeover whose complete session relation is proven to have no dispatch, Run, effect, pending tool/queue/control, permission or recovery fence. A BLOCKED Task can remain BLOCKED, preserving Goal/Task/checkpoint identity; ownership transfer must not label it accepted or resume it. Active or unknown work remains visibly pending/blocked until a separate Coordinator pause path is implemented and validated.

Production changes proposed for a separately owned worktree:

- internal/domain/client_protocol.go: route attach through the durable state machine and permit only its exact pending command to make progress on replay; retain current ownership, revision, epoch, role, archival and schema gates.
- New internal/domain/client_protocol_attach.go: attach-only work-settlement proof, original-identity binding, intent creation/progress, current state revalidation, atomic final grant and one CLIENT_HANDOFF event. Keep clientTurnSettled unchanged.
- A new migration filename allocated serially by the root/migration owner: persistent unique active intent per session, requester/current owner/epoch/revision/hash, original ACK and final receipt. Do not edit frozen contracts or historical migration evidence. Do not reuse cancellation rows without a typed distinction.
- Host/API composition files only in an explicitly expanded scope: expose trusted current local OS subject/client facts from the existing Host boundary. A caller-supplied client_id, claimed Owner role, stale credential or old epoch is not evidence. Do not create a public OWNER registration or a bypass.
- internal/domain/runtime_coordinator_windows.go and runtime_command_queue_windows.go only when implementing the active-work branch: persist the intent first, hold new dispatch after commit, request a real safe pause through the selected runtime, wait outside the SQL transaction, reconcile exact process/effect/queue/checkpoint state, then recheck before grant. Preserve unconsumed follow-ups. Do not issue business CANCEL or delete a queue to manufacture settlement. If no compatible pause capability exists, retain an explicit implementation gap.
- apps/cli/cli_sessions_test.go plus attach-specific domain/API tests: supply explicit synthetic authority and settlement facts for fixture tests, distinguish ACK from final completion, and keep the native qualification gap separately visible. The current test must not simply change its expected error to pass.

## Meaningful regression coverage

- Same current client renews without an epoch change; read-only attach neither acquires nor renews.
- Fresh proven same-OS target with a valid old lease gets ACK and stays read-only; exact replay neither repeats pause nor creates another intent.
- Missing, foreign, stale, remote-device or fabricated authority fails without mutating owner/epoch/journal.
- A quiescent never-dispatched BLOCKED task can move ownership only after complete session-history proof; task, Goal, work, checkpoint and accepted/pending queue state remain unchanged; no auto-resume.
- Current and historical Runs, hidden older effects, queued commands, pending permissions, unknown process/effect state and restore fences prevent completion, even after lease expiry.
- Concurrent intents, changed revision/owner/epoch/input/permission and same-command changed payload preserve one winner or refuse; no automatic revision replacement.
- CANCEL wins during pending transfer; later completion cannot revive cancelled work, clear resume_requires_explicit_user or discard follow-ups.
- Faults and restart between intent/ACK/reconciliation/CAS/journal do not produce dual owners; final replay is stable and old writer writes remain rejected.

No part of this diagnosis permits changing the writer/CAS/native gates merely to make a fixture green. No pure-scalar result is authority to bypass the ordinary LIVE Goal gate.
'''
(OUT / 'construction-brief.md').write_text(brief, encoding='utf-8', newline='\n')
put(OUT / 'diagnostics.json', {
    'status': 'READ_ONLY_DIAGNOSIS_ARCHIVED_C_ONLY',
    'no_product_or_test_source_modified': True, 'no_test_rerun': True, 'no_d_writes': True,
    'physical_transport': {'reported_action': 'elevated read-only Git/identity check', 'reported_error': 'CreateProcess: exec-server transport disconnected',
                           'reported_execution_state': 'NOT_EXECUTED', 'session_ref': '../SESSION.json', 'not_retried_here': True},
    'prior_source_read_chunks': ['44bfa0', '024546', 'f78156', 'de68c6', 'b89ab4', 'da3f8e'],
    'prior_read_diagnostics': ['Several rg path arguments used Windows wildcards or guessed absent filenames, producing os error 123/2; actual files were subsequently located and read with -g filters. These are read diagnostics, not test/native failures.'],
    'classification': 'Existing fail-closed implementation gap plus unproven fixture takeover assumptions; not a prompt bridge regression and not evidence that relaxing the guards is safe.',
    'counter_reset': False, 'formal_increment': 0,
})

# Add statistics without modifying the frozen prototype source or old attempts.
manifest = load(PURE / 'evidence/attempt-02/source-manifest.json')
for row in manifest['files']:
    if sha(PURE / row['path']) != row['sha256']:
        raise RuntimeError('pure-scalar frozen source changed: ' + row['path'])
test_output = (PURE / 'evidence/attempt-02/go-test.stdout.txt').read_text(encoding='utf-8')
pass_rows = re.findall(r'^(\s*)--- PASS: (\S+) \(', test_output, re.M)
top_names = [name for indent, name in pass_rows if not indent]
sub_names = [name for indent, name in pass_rows if indent]
if len(top_names) != 10 or top_names != load(PURE / 'evidence/attempt-02/author-summary.json')['passed_test_functions']:
    raise RuntimeError('unexpected pure-scalar top-level statistics')
failed_names = re.findall(r'^\s*--- FAIL: (\S+) \(', test_output, re.M)
if failed_names:
    raise RuntimeError('unexpected pure-scalar failures')
by_parent = collections.Counter(name.split('/', 1)[0] for name in sub_names)
statistics = {
    'status': 'FROZEN_STANDALONE_TEST_STATISTICS',
    'top_level_test_functions_passed': len(top_names), 'top_level_test_functions': top_names,
    'nested_t_run_pass_records': len(sub_names), 'nested_t_run_pass_records_by_parent': dict(by_parent),
    'total_pass_records_including_parents': len(pass_rows), 'failed_test_records': [],
    'counting_rule': 'Count actual go test verbose PASS lines. Top-level functions, nested t.Run records and parent rows are separate; none is a formal business assertion count.',
    'failure_origin': 'cli-pure-scalar-missing-test-helper-20261104',
    'attempt_01': {'result': load(PURE / 'evidence/attempt-01/go-test.result.json'),
                   'diagnosis': 'Test compilation failed: omitted assertRejected helper; no tests ran.',
                   'stderr_sha256': sha(PURE / 'evidence/attempt-01/go-test.stderr.txt'),
                   'summary_sha256': sha(PURE / 'evidence/attempt-01/author-summary.json')},
    'attempt_02': {'result': load(PURE / 'evidence/attempt-02/go-test.result.json'),
                   'stdout_sha256': sha(PURE / 'evidence/attempt-02/go-test.stdout.txt'),
                   'summary_sha256': sha(PURE / 'evidence/attempt-02/author-summary.json'),
                   'source_manifest_sha256': sha(PURE / 'evidence/attempt-02/source-manifest.json')},
    'validator_implementation_sha256': sha(PURE / 'validate.go'),
    'validator_unchanged_between_attempts': next(row['sha256'] for row in load(PURE / 'evidence/attempt-01/source-manifest.json')['files'] if row['path'] == 'validate.go') == sha(PURE / 'validate.go'),
    'original_attempts_unchanged': True, 'frozen_sources_unchanged': True,
    'researchos_applied': False, 'formal_increment': 0, 'counter_reset': False,
}
stats_path = PURE / 'evidence/test-statistics.json'
put(stats_path, statistics)
put(OUT / 'pure-scalar-reference.json', {'statistics_path': str(stats_path), 'statistics_sha256': sha(stats_path),
                                       'top_level_passed': len(top_names), 'nested_pass_records': len(sub_names),
                                       'all_source_hashes_still_match_attempt02': True, 'original_attempt01_and_attempt02_preserved': True})
shutil.copyfile(Path(__file__), OUT / 'archive-diagnosis-controller.py.txt')
evidence = {str(path.relative_to(OUT)).replace('\\', '/'): sha(path) for path in sorted(OUT.rglob('*')) if path.is_file()}
put(OUT / 'manifest.json', {'evidence_sha256': evidence, 'pure_scalar_statistics': {'path': str(stats_path), 'sha256': sha(stats_path)}, 'no_d_writes': True, 'no_tests_rerun': True})
print(json.dumps({'w14_packet': str(OUT), 'manifest_sha256': sha(OUT / 'manifest.json'),
                  'statistics': str(stats_path), 'top_level_passed': len(top_names), 'nested_pass_records': len(sub_names),
                  'total_pass_records': len(pass_rows), 'frozen_sources_unchanged': True}, ensure_ascii=False))
