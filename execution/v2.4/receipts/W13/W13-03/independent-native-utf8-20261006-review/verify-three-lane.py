"""Offline three-lane transcript verification. Does not launch product processes."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path('D:/作品集/ResearchOS/research-os')
BASE = ROOT / 'execution/v2.4/receipts/W13/W13-03'
OUT = Path(__file__).resolve().parent
name, expected_status, output_name = sys.argv[1:4]
RAW = BASE / name

def load(name):
    return json.loads((RAW / name).read_text(encoding='utf-8-sig'))

def digest(raw):
    return 'sha256:' + hashlib.sha256(raw).hexdigest()

checks = []
def check(name, okay):
    checks.append({'id': name, 'pass': bool(okay)})
    if not okay:
        raise AssertionError(name)

run, electron, ready, diagnostic = map(load, ['run.json', 'electron-transcript.json', 'fixture.ready.json', 'last-text-diagnostic.json'])
check('EXPECTED_RUN_STATUS', run['status'] == electron['status'] == expected_status)
check('FIXTURE_NOT_WHOLE_CARD', run['measurement_mode'] == electron['measurement_mode'] == 'FIXTURE' and run['whole_card_accepted'] is False and electron['whole_card_accepted'] is False)
expected = ('transcript-final:' + '续' * 14000).encode('utf8')
lanes = {lane: (RAW / (lane + '-last-text.utf8.txt')).read_bytes() for lane in ['cli', 'native', 'ui']}
check('CLI_EXACT_42017', lanes['cli'] == expected and len(lanes['cli']) == ready['last_text_bytes'] == 42017 and digest(lanes['cli']) == ready['last_text_hash'])
for lane in ['native', 'ui']:
    check('DIAGNOSTIC_MATCHES_RAW:' + lane, diagnostic[lane]['utf8_bytes'] == len(lanes[lane]) and diagnostic[lane]['sha256'] == digest(lanes[lane]))
check('NATIVE_UI_IDENTICAL', lanes['native'] == lanes['ui'])
check('EXPECTED_DIAGNOSTIC', diagnostic['expected']['message_id'] == ready['last_message_id'] and diagnostic['expected']['sha256'] == digest(expected) and diagnostic['expected']['utf8_bytes'] == 42017)
snap = diagnostic['native_snapshot']
for key in ['project_id', 'session_id', 'goal_id', 'first_visible_message_id', 'transcript_artifact_ref']:
    check('SCOPE_PRESERVED:' + key, snap[key] == ready[key])
check('LAST_ID_COMPLETE', snap['last_visible_message_id'] == ready['last_message_id'] and snap['last_complete'] is True and snap['last_parts'] == 1 and snap['visible_count'] == 200)
check('REVISION_WATERMARK', snap['revision'] == 605 and snap['event_sequence'] == ready['snapshot_event_sequence'] == 604)
check('CONTEXT_PRESERVED', diagnostic['native_context'] == {'project_id': ready['project_id'], 'session_id': ready['session_id']})
cli = [json.loads(line) for line in (RAW / 'cli-before.stdout.txt').read_text(encoding='utf8').splitlines() if line.strip()]
check('CLI_STATUS', len(cli) == 1 and cli[0]['status'] == 'COMPLETED')
cli_snap = cli[0]['operations'][0]['result']
check('CLI_SCOPE_AND_LAST', all(cli_snap[k] == ready[k] for k in ['project_id', 'session_id', 'goal_id', 'transcript_artifact_ref']) and cli_snap['messages'][-1]['message_id'] == ready['last_message_id'])
check('CLI_RAW_FROM_ACTUAL_SNAPSHOT', ''.join(p['text'] for p in cli_snap['messages'][-1]['parts']).encode('utf8') == lanes['cli'])
check('NO_PROVIDER_RUN_EFFECT', ready['provider_calls'] == ready['before_run_count'] == ready['after_run_count'] == ready['before_effect_count'] == ready['after_effect_count'] == 0)
check('SEND_TASK_DELTA_DISTINCT_FROM_READS', ready['before_task_count'] == 1 and ready['after_task_count'] == 2)
if expected_status == 'FAIL':
    check('REAL_OLD_MISMATCH', len(lanes['native']) == len(lanes['ui']) == 42020 and lanes['native'] != expected and lanes['native'].decode('utf8').count('\ufffd') == 2)
    check('FAILS_MEANINGFUL_CHECK', any(c['id'] == 'LAST_VISIBLE_EXACT_TEXT_HASH' and c['status'] == 'FAIL' for c in electron['checks']))
    old = (OUT / 'main-before-fix.js').read_bytes()
    check('OLD_SOURCE_MATCHES_FAIL', run['source_hashes']['apps/desktop/main/main.js'] == hashlib.sha256(old).hexdigest())
else:
    check('ALL_THREE_LANES_EXACT', all(raw == expected for raw in lanes.values()))
    raw = (RAW / 'full-transcript.raw.json').read_bytes()
    full = json.loads(raw)
    check('SEALED_ARTIFACT_HASH', digest(raw) == ready['transcript_artifact_ref']['content_hash'])
    check('ARTIFACT_SCOPE_SCHEMA', full['schema'] == 'researchos.session-transcript.v1' and full['origin'] == 'SESSION_MESSAGE_JOURNAL' and full['project_id'] == ready['project_id'] and full['session_id'] == ready['session_id'])
    check('ALL_201_MESSAGES', len(full['messages']) == len(full['message_sequences']) == 201)
    check('MESSAGE_WATERMARK', full['through_sequence'] == ready['transcript_through_sequence'] == 603)
    for i, (m, seq) in enumerate(zip(full['messages'], full['message_sequences'])):
        text = f'u{i+1:03d}' if i < 200 else expected.decode('utf8')
        check(f'EXACT_MESSAGE_{i+1}', m['role'] == 'USER' and m['complete'] is True and m['parts'] == [{'part_index': 0, 'text': text, 'complete': True}])
        check(f'EXACT_SEQUENCE_{i+1}', seq == {'message_id': m['message_id'], 'start_sequence': 3*i+1, 'end_sequence': 3*i+3, 'source_run_id': None})
    check('CLI_LAST_200_EXACT', cli_snap['messages'] == full['messages'][1:])
    after = [json.loads(line) for line in (RAW / 'cli-after.stdout.txt').read_text(encoding='utf8').splitlines() if line.strip()]
    check('CLI_AFTER_READ_NO_CHANGES', len(after) == 1 and after[0]['operations'][0]['result'] == cli_snap)
    counts = load('read-only-counts.json')
    check('READS_NO_NEW_TASK_RUN_EFFECT', counts['before'] == counts['after'] == {'task': 2, 'run': 0, 'effect': 0})
    check('OBSERVED_NO_LIVE_CLAIM', full['measurement_basis'] == 'USER_JOURNAL_ONLY' and full['source_run_refs'] == [])
    check('CURRENT_TRANSPORT_SOURCE_MATCHES', run['source_hashes']['apps/desktop/main/main.js'] == hashlib.sha256((ROOT / 'apps/desktop/main/main.js').read_bytes()).hexdigest())
    check('ALL_RECORDED_CHECKS_PASS', all(v is True for v in run['checks'].values()) and all(c['status'] == 'PASS' for c in electron['checks']))
    for image in electron['screenshots']:
        check('SCREENSHOT_HASH:' + image['name'], digest((RAW / image['name']).read_bytes()) == image['sha256'])
manifest = [{'name': p.name, 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(RAW.iterdir()) if p.is_file()]
result = {'receipt': name, 'expected_status': expected_status, 'verification': 'PASS', 'assertions_passed': len(checks), 'checks': checks,
          'lanes': {lane: {'bytes': len(raw), 'sha256': digest(raw), 'replacement_count': raw.decode('utf8').count('\ufffd')} for lane, raw in lanes.items()},
          'source_main_sha256': run['source_hashes']['apps/desktop/main/main.js'],
          'source_frozen_check': run['checks'].get('SOURCE_FROZEN_DURING_OBSERVATION'),
          'manifest': manifest}
(OUT / output_name).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print(json.dumps({'receipt': name, 'assertions_passed': len(checks), 'verification': 'PASS'}, ensure_ascii=False))
