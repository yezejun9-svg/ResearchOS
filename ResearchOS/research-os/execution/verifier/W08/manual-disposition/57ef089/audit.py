"""Read-only independent audit of frozen W08 attempts. Does not invoke tests."""
from pathlib import Path
import collections
import hashlib
import json
import subprocess

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[4]
WT = ROOT / '.local/worktrees/research-manual-disposition'
FIX = WT / 'execution/receipts/W08/manual-disposition'
OLD = ROOT / 'execution/receipts/W21/current-source-research/609837e'
FINAL = '57ef0892e60c9fdf9a57aad2dd62f82e002ff337'
PROD = '78d4de057ca9f0810d8bfe4f5aac5c4c856c44ba'
RAW = 'f820a2b2df592034faecf4bd4d2278ab10cc4795'

def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def git(*args):
    return subprocess.check_output(['git', '-C', str(WT), *args]).decode('utf-8').strip()

def blob(commit, path):
    return subprocess.check_output(['git', '-C', str(WT), 'show', f'{commit}:{path}'])

def parse_raw(path):
    events = [json.loads(line) for line in path.read_text(encoding='utf-8-sig').splitlines() if line.strip()]
    streams = collections.defaultdict(str)
    for event in events:
        if event.get('Action') == 'output':
            streams[(event.get('Package'), event.get('Test'))] += event.get('Output', '')
    assertions = []
    interesting = []
    for (_, test), output in streams.items():
        for line in output.splitlines():
            if '_ASSERTION ' in line:
                assertions.append({'test': test, **json.loads(line.split('_ASSERTION ', 1)[1])})
            if any(word in line for word in ['got 422', 'want 200', 'UNIQUE', 'constraint', 'missing', 'W08 manual boundary', 'W08 work-only', 'W08 monitor']):
                interesting.append({'test': test, 'output': line})
    terminal = [{k: e.get(k) for k in ('Action', 'Test', 'Package')} for e in events if e.get('Action') in ('pass', 'fail', 'skip')]
    return {'raw_sha256': sha(path), 'event_count': len(events), 'terminal_events': terminal,
            'assertions': assertions, 'selected_output': interesting,
            'top_level_tests': [e for e in terminal if e['Test'] and '/' not in e['Test']],
            'subtest_counts': dict(collections.Counter(e['Action'] for e in terminal if e['Test'] and '/' in e['Test'])),
            'package_terminal': [e for e in terminal if e['Test'] is None]}

manifest = read(FIX / 'sha256-manifest.json')
checked = []
for item in manifest['files']:
    path = WT / item['path']
    actual = {'path': item['path'], 'actual_sha256': sha(path), 'actual_bytes': path.stat().st_size}
    actual['matches'] = actual['actual_sha256'] == item['sha256'] and actual['actual_bytes'] == item['bytes']
    assert actual['matches'], actual
    checked.append(actual)
assert manifest['source_commit'] == FINAL
assert git('rev-parse', 'HEAD') == RAW
assert git('status', '--porcelain') == ''
fixture_delta = git('diff', '--name-only', PROD, FINAL).splitlines()
assert fixture_delta == ['internal/domain/research_manual_disposition_test.go']
raw_delta = git('diff', '--name-only', FINAL, RAW).splitlines()
assert all(p.startswith('execution/receipts/W08/manual-disposition/') for p in raw_delta)
source_items = [i for i in manifest['files'] if i['path'].startswith('internal/')]
for item in source_items:
    assert hashlib.sha256(blob(FINAL, item['path'])).hexdigest() == item['sha256']
unchanged_c05 = all(blob(c, 'internal/domain/research_test.go') == blob(PROD, 'internal/domain/research_test.go') for c in [FINAL, '609837ef84c93dd691ed968586309faa25f06bd0'])
assert unchanged_c05
write('input-manifest-audit.json', {'status': 'PASS', 'manifest_sha256': sha(FIX / 'sha256-manifest.json'), 'checked': checked,
    'source_commit': FINAL, 'production_commit': PROD, 'raw_commit': RAW, 'worktree_clean': True,
    'source_files_match_git': len(source_items), 'fixture_only_delta': fixture_delta, 'raw_only_delta': raw_delta, 'original_c05_source_unchanged': unchanged_c05})

rounds = {}
for name in ['78d4de0', '57ef089']:
    record = parse_raw(FIX / name / 'go-test.raw.jsonl')
    record['command'] = read(FIX / name / 'command.json')
    record['exit'] = read(FIX / name / 'exit.json')
    rounds[name] = record
assert rounds['78d4de0']['exit']['exit_code'] == 1
assert rounds['78d4de0']['subtest_counts'] == {'pass': 19, 'fail': 2}
assert rounds['57ef089']['exit']['exit_code'] == 0
assert rounds['57ef089']['subtest_counts'] == {'pass': 21}
assert all(e['Action'] == 'pass' for e in rounds['57ef089']['terminal_events'])
c05 = [e for e in rounds['78d4de0']['top_level_tests'] if e['Test'] == 'TestW08C05CompleteWithoutAdoption']
assert len(c05) == 1 and c05[0]['Action'] == 'pass'
c05_assertions = [a for a in rounds['78d4de0']['assertions'] if a['test'] == 'TestW08C05CompleteWithoutAdoption']
assert len(c05_assertions) == 8 and all(a['status'] == 'PASS' and a['actual'] == a['expected'] for a in c05_assertions)
report = read(FIX / 'execution-report.json')
for derived in report['rounds']:
    actual = rounds[derived['directory']]
    assert derived['command'] == actual['command'] and derived['exit'] == actual['exit']
    assert [{k: e.get(k) for k in ('Action', 'Test', 'Package')} for e in derived['terminal_events']] == actual['terminal_events']
write('raw-attempt-review.json', {'status': 'PASS_IN_SCOPE', 'parser': 'Go Output reconstructed by Package/Test before parsing complete lines', 'rounds': rounds})

old = parse_raw(OLD / 'stdout.jsonl')
old_command = read(OLD / 'command.json')
assert old_command['exit_code'] == 1 and old_command['stdout_sha256'] == old['raw_sha256']
assert old_command['stderr_sha256'] == sha(OLD / 'stderr.log')
assert len(old['top_level_tests']) == 6
assert sum(t['Action'] == 'pass' for t in old['top_level_tests']) == 5
assert [t['Test'] for t in old['top_level_tests'] if t['Action'] == 'fail'] == ['TestW08C05CompleteWithoutAdoption']
before, after = read(OLD / 'source-before.json'), read(OLD / 'source-after.json')
assert before['files'] == after['files'] and len(before['files']) == 340
source_delta = []
for path, recorded_hash in before['files'].items():
    try:
        actual_hash = hashlib.sha256(blob(FINAL, path)).hexdigest()
    except subprocess.CalledProcessError:
        actual_hash = None
    if actual_hash != recorded_hash:
        source_delta.append({'path': path, 'old_hash': recorded_hash, 'final_hash': actual_hash})
write('original-r02-review.json', {'status': 'HISTORICAL_BOUNDED_PASS_REUSE_WITH_C05_SUPERSEDED',
    'original_aggregate_exit': 1, 'original_source_files_before_after_equal': 340,
    'scope': 'Five earlier PASS tests are reused at their recorded revision; source delta is explicit and not called a fresh final-source rerun.',
    'command': old_command, 'raw': old, 'final_source_delta_among_original_340_files': source_delta,
    'limits': ['A05 live classification is source metadata and historical byte binding; no new live-provider qualification.',
               'C06 frontend acceptance is a separate scope; these backend tests do not complete the whole case.',
               'Original C05 failure and package failure remain preserved.']})

snap = read(FIX / '78d4de0/c05-no-adopt-sqlite.json')
objects = snap['objects']
cycles = [x['body'] for x in objects if x['kind'] == 'ResearchCycle']
experiments = [x['body'] for x in objects if x['kind'] == 'Experiment']
receipts = [x['body'] for x in objects if x['kind'] == 'AcceptanceReceipt']
assert len(cycles) == 1 and cycles[0]['status'] == 'COMPLETE' and cycles[0]['decision_ids'] == []
assert len(experiments) == 1 and experiments[0]['status'] == 'COMPLETED' and experiments[0]['outcome'] == 'NO_IMPROVEMENT'
assert experiments[0]['acceptance_id'] in [x['id'] for x in receipts]
assert len(snap['pages']) == 3 and len(snap['reviews']) == 3
assert sorted(x['outcome'] for x in snap['reviews']) == ['INCONCLUSIVE', 'REJECT', 'WATCH']
write('c05-snapshot-review.json', {'status': 'PASS', 'snapshot_sha256': sha(FIX / '78d4de0/c05-no-adopt-sqlite.json'),
    'cycle_status': cycles[0]['status'], 'decision_ids': cycles[0]['decision_ids'],
    'experiment_status': experiments[0]['status'], 'experiment_outcome': experiments[0]['outcome'],
    'experiment_acceptance_present': True, 'pages': len(snap['pages']), 'review_outcomes': sorted(x['outcome'] for x in snap['reviews']),
    'limits': 'Saved public SQLite projection, not a reopened database or new execution. Stable release before/after null is only the original fixture assertion, not a positive existing release retention test.'})

inputs = [FIX / 'sha256-manifest.json', *[WT / i['path'] for i in manifest['files']], *[p for p in OLD.iterdir() if p.is_file()]]
write('reviewed-inputs.json', [{'path': str(p), 'sha256': sha(p), 'bytes': p.stat().st_size} for p in inputs])
print(json.dumps({'status': 'PASS_IN_SCOPE', 'manifest_items': len(checked), 'final_subtests_pass': 21, 'c05_assertions_pass': 8,
                  'original_r02_tests_pass': 5, 'original_r02_tests_fail': 1, 'prior_source_delta': len(source_delta), 'tests_executed_by_verifier': 0}))
