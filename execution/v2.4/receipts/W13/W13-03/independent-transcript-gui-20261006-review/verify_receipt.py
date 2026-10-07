"""Independent offline verification only; does not start CLI, GUI or a fixture."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/作品集/ResearchOS/research-os')
OUT = Path(__file__).resolve().parent
BASE = ROOT / 'execution/v2.4/receipts/W13/W13-03'
NAME = 'transcript-gui-20261005T190538Z-81e34944'
RAW = BASE / NAME
CANDIDATE = ROOT / '.local/worktrees/codex-w1303'

def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

checks = []
def check(name, okay):
    checks.append({'id': name, 'pass': bool(okay)})
    if not okay:
        save(OUT / 'assertions.json', checks)
        raise AssertionError(name)

run = load(RAW / 'run.json')
electron = load(RAW / 'electron-transcript.json')
fixture = load(RAW / 'fixture.ready.json')
wire = load(RAW / 'native-wire-summary.json')
counts = load(RAW / 'read-only-counts.json')
backend = load(BASE / 'independent_transcript_review_round1_codex.json')
gui_sources = ['tests/ui/w1303/transcript_run.py', 'tests/ui/w1303/transcript.cjs',
               'tests/ui/w1303/workspace_fixture/main_windows.go',
               'tests/ui/w1303/workspace_fixture/transcript_windows.go']
source_paths = gui_sources + [x['path'] for x in backend['source_hashes']]
cli_paths = [p for p in run['source_hashes'] if p.startswith('apps/cli/')]
source_paths += cli_paths
before = {p: sha(ROOT / p) for p in source_paths}
save(OUT / 'source-before.json', before)

for entry in backend['source_hashes']:
    expected = entry.get('main_sha256') or entry['sha256']
    check('BACKEND_BASELINE:' + entry['path'], before[entry['path']] == expected)
for p in gui_sources:
    check('GUI_SOURCE_MATCHES_EXECUTED:' + p, before[p] == run['source_hashes'][p])

copied = []
for p in sorted(RAW.iterdir()):
    if not p.is_file():
        continue
    source = CANDIDATE / 'execution/v2.4/receipts/W13/W13-03' / NAME / p.name
    check('COPIED_BYTE_IDENTICAL:' + p.name, source.is_file() and sha(source) == sha(p))
    copied.append({'name': p.name, 'sha256': sha(p), 'bytes': p.stat().st_size})
save(OUT / 'raw-manifest.json', copied)

check('RUNNER_STATUS', run['status'] == 'PASS' and run['measurement_mode'] == 'FIXTURE' and run['whole_card_accepted'] is False)
check('ELECTRON_STATUS', electron['status'] == 'PASS' and electron['measurement_mode'] == 'FIXTURE' and electron['whole_card_accepted'] is False)
check('RUNNER_NONZERO_23', len(run['checks']) == 23 and all(v is True for v in run['checks'].values()))
check('ELECTRON_NONZERO_17', len(electron['checks']) == 17 and all(v['status'] == 'PASS' for v in electron['checks']))
check('COMMANDS_EXIT_ZERO', len(run['commands']) == 6 and all(v['exit_code'] == 0 for v in run['commands']))

data = (RAW / 'full-transcript.raw.json').read_bytes()
full = json.loads(data)
ref = fixture['transcript_artifact_ref']
check('ARTIFACT_RAW_HASH', 'sha256:' + hashlib.sha256(data).hexdigest() == ref['content_hash'])
check('ARTIFACT_SIZE', len(data) == electron['artifact']['byte_size'] == 92174)
check('SCHEMA_ORIGIN_SCOPE', full['schema'] == 'researchos.session-transcript.v1' and full['origin'] == 'SESSION_MESSAGE_JOURNAL' and full['project_id'] == fixture['project_id'] and full['session_id'] == fixture['session_id'])
check('FIXTURE_PROVENANCE', full['measurement_basis'] == 'USER_JOURNAL_ONLY' and full['source_run_refs'] == [] and fixture['measurement_mode'] == 'FIXTURE')
messages, sequences = full['messages'], full['message_sequences']
check('FULL_201_AND_UNIQUE', len(messages) == len(sequences) == 201 and len({m['message_id'] for m in messages}) == 201)
final_text = 'transcript-final:' + '续' * 14000
for i, (message, seq) in enumerate(zip(messages, sequences)):
    expected = f'u{i+1:03d}' if i < 200 else final_text
    check(f'EXACT_MESSAGE_{i+1}', message['role'] == 'USER' and message['complete'] is True and message['parts'] == [{'part_index': 0, 'text': expected, 'complete': True}])
    check(f'EXACT_SEQUENCE_{i+1}', seq == {'message_id': message['message_id'], 'start_sequence': 3*i+1, 'end_sequence': 3*i+3, 'source_run_id': None})
check('ENDPOINT_IDS', messages[0]['message_id'] == fixture['first_message_id'] and messages[1]['message_id'] == fixture['first_visible_message_id'] and messages[-1]['message_id'] == fixture['last_message_id'])
check('FINAL_BYTES_AND_HASH', len(final_text.encode()) == fixture['last_text_bytes'] == 42017 and 'sha256:' + hashlib.sha256(final_text.encode()).hexdigest() == fixture['last_text_hash'])
check('MESSAGE_VS_EVENT_WATERMARK', full['through_sequence'] == fixture['transcript_through_sequence'] == 603 and fixture['snapshot_event_sequence'] == 604)

snapshots = []
for label in ['before', 'after']:
    rows = [json.loads(line) for line in (RAW / f'cli-{label}.stdout.txt').read_text(encoding='utf-8').splitlines() if line.strip()]
    check('CLI_ONE_COMPLETED:' + label, len(rows) == 1 and rows[0]['status'] == 'COMPLETED')
    ops = rows[0]['operations']
    check('CLI_READ_METHODS:' + label, [op['method'] for op in ops[:2]] == ['session.get', 'host.status'] and all(op['status'] == 'COMPLETED' for op in ops[:2]))
    snap = ops[0]['result']
    check('CLI_SAME_SCOPE_REF:' + label, all(snap[k] == fixture[k] for k in ['project_id', 'session_id', 'goal_id', 'transcript_artifact_ref']))
    check('CLI_200_EXACT:' + label, snap['messages'] == messages[1:] and snap['has_earlier_messages'] is True and snap['event_sequence'] == 604)
    snapshots.append(snap)
check('CLI_IDENTICAL_SNAPSHOTS', snapshots[0] == snapshots[1])
check('NATIVE_MATCHES_CLI', all(wire[k] == snapshots[0][k] for k in ['project_id', 'session_id', 'goal_id', 'event_sequence', 'revision', 'transcript_artifact_ref']) and wire['visible_count'] == 200)
check('READ_COUNTS_UNCHANGED', counts['before'] == counts['after'] == {'task': 2, 'run': 0, 'effect': 0})
check('REAL_SEND_DISTINGUISHED', fixture['before_task_count'] == 1 and fixture['after_task_count'] == 2 and fixture['before_run_count'] == fixture['after_run_count'] == 0 and fixture['before_effect_count'] == fixture['after_effect_count'] == 0)
check('NO_RENDERER_ERRORS', electron['renderer_errors'] == [])
for entry in electron['screenshots']:
    check('SCREENSHOT_HASH:' + entry['name'], 'sha256:' + sha(RAW / entry['name']) == entry['sha256'])
first_dir = BASE / 'transcript-gui-20261005T190459Z-5714dcf6'
first = load(first_dir / 'electron-transcript.json')
check('FIRST_FAILURE_RETAINED', first['status'] == 'FAIL' and 'page.goto' in first['error'] and 'ERR_ABORTED' in first['error'])
cli_differences = [{'path': p, 'executed_candidate_sha256': run['source_hashes'][p], 'current_main_sha256': before[p]} for p in cli_paths if before[p] != run['source_hashes'][p]]
check('CLI_DIFFERENCE_EXPLICIT', {e['path'] for e in cli_differences} == {'apps/cli/cli_continuation.go', 'apps/cli/cli_continuation_test.go'})
after = {p: sha(ROOT / p) for p in source_paths}
check('READ_ONLY_SOURCE_UNCHANGED', before == after)
save(OUT / 'source-after.json', after)
save(OUT / 'assertions.json', checks)
summary = {
    'schema': 'researchos.independent-transcript-gui-review.v1',
    'status': 'PASS_IN_SCOPE', 'verdict': 'APPROVE_IN_SCOPE', 'whole_card_accepted': False,
    'measurement_mode': 'FIXTURE', 'review_mode': 'OFFLINE_RECEIPT_SOURCE_AND_SCREENSHOT_REVIEW',
    'root_head_at_review': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
    'reviewer': '/root/w1303_transcript_review',
    'reviewed_candidate_receipt': NAME + '/run.json',
    'runner_checks_pass': 23, 'electron_checks_pass': 17,
    'independent_offline_assertions_pass': len(checks), 'independent_offline_assertions_fail': 0,
    'raw_directory': OUT.name, 'source_manifest': OUT.name + '/source-before.json',
    'source_unchanged': True, 'backend_nine_and_spec_match_previous_review': True,
    'gui_four_source_files_match_executed_hashes': True,
    'artifact': {'ref': ref, 'byte_size': len(data), 'messages': 201, 'last_message_bytes': 42017, 'through_message_sequence': 603, 'snapshot_event_sequence': 604},
    'read_only_counts': counts, 'seed_send_task_delta': {'before_real_send': 1, 'after_real_send': 2, 'note': 'The real session.send is a write; only subsequent CLI/preview reads are claimed read-only.'},
    'cli_source_difference': cli_differences,
    'main_cli_fix_commit_observed': 'd92cd639 fix(cli): exclude terminal runs from active continuation candidates',
    'main_gui_reexecution_claimed': False,
    'findings': {'critical': [], 'important': [], 'suggestion': []},
    'visual_observations': [
        '01-latest-200.png: real ResearchOS session UI, selected fixture session, visible first user message u002 followed by u003/u004; screenshot alone does not prove all 200 DOM nodes.',
        '02-sealed-ref.png: read-full-transcript button and REPORT metadata, CURRENT / OBSERVED / FIXTURE, exact sha256 ref, application/json 91 KiB PROJECT, controlled-preview button.',
        '03-full-preview.png: controlled preview opened; JSON contains USER_JOURNAL_ONLY and first original message ID with start 1/end 3. Entire 201-message content is established by raw bytes plus DOM checks, not single viewport screenshot.'
    ],
    'request_failure_observation': {'count': len(electron['request_failures']), 'details': electron['request_failures'], 'interpretation': 'Recorded ERR_ABORTED requests from default project navigation remain visible. No all-network-requests-success claim; target session and artifact flows independently completed.'},
    'first_failure': {'directory': first_dir.name, 'sha256_electron_report': sha(first_dir / 'electron-transcript.json'), 'error': first['error'], 'modified': False},
    'limits': [
        'No GUI or CLI process was launched in this review; root holds GUI ownership and will provide a new main registered transcript-stage receipt.',
        'Candidate receipt executes old CLI sources; current main contains terminal-run continuation fix. Candidate PASS is not main runtime verification.',
        'No workspace access/write/diff/modules audit or previously platform-interrupted audit was read, rerun or used for this verdict.',
        'Fixture uses 200 constructed typed USER messages and one actual production session.send; no LIVE provider/ASSISTANT run qualification.',
        'No NVDA/accessibility qualification or whole-card/formal acceptance.',
        'Read-only GUI evidence asserts Task/Run/effect counts and unchanged event watermarks/ref; it does not claim a full database-cell comparison in this GUI run.'
    ],
    'whats_done_well': ['Concrete production session.send crosses the 200-message boundary and retains exact text above 32 KiB.', 'Desktop native session read, controlled Artifact preview, raw Artifact hash and two CLI snapshots agree on scope and sealed reference.']
}
save(BASE / 'independent_transcript_gui_review_round1_codex.json', summary)
print(json.dumps({'status': summary['status'], 'offline_assertions': len(checks), 'raw_bytes': len(data), 'cli_difference_paths': [e['path'] for e in cli_differences]}, ensure_ascii=False))
