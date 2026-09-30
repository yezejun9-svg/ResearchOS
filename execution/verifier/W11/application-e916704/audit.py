import collections
import datetime
import difflib
import hashlib
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[4]
OUT = pathlib.Path(__file__).resolve().parent
WORK = ROOT / '.local/worktrees/w11-application-review-e916704'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def dump(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


commit = subprocess.check_output(['git', '-C', str(WORK), 'rev-parse', 'HEAD'], text=True).strip()
assert commit.startswith('e916704')
assert not subprocess.check_output(['git', '-C', str(WORK), 'status', '--porcelain'], text=True)
original = (ROOT / '.local/w11-application-review-4545151/review_test.go').read_bytes()
current = (ROOT / '.local/w11-application-review-e916704/review_test.go').read_bytes()
(OUT / 'original_probe.go.txt').write_bytes(original)
(OUT / 'diagnostic_probe.go.txt').write_bytes(current)
intermediate = current.decode().split('\ntype rv11TraceTransport')[0].rstrip() + '\n'
intermediate = intermediate.replace('HTTP: rv11TracingHTTP(server)', 'HTTP: server.Client()')
(OUT / 'loopback_isolated_probe.go.txt').write_text(intermediate, encoding='utf-8')
(OUT / 'probe-harness.diff').write_text(''.join(difflib.unified_diff(original.decode().splitlines(True), current.decode().splitlines(True), fromfile='original_probe', tofile='diagnostic_probe')), encoding='utf-8')

runs = []
selected = []
selection = {
    'retry.stdout.txt': lambda name: not name.startswith(('TestRV11PromptAndRaces', 'TestRV11FaultPersistence')),
    'loopback-isolated.stdout.txt': lambda name: name.startswith('TestRV11PromptAndRaces'),
    'transport-diagnostic.stdout.txt': lambda name: name.startswith('TestRV11FaultPersistence'),
}
for p in sorted(OUT.glob('*.stdout.txt')):
    case = ''
    rows = []
    for n, line in enumerate(p.read_text(encoding='utf-8-sig').splitlines(), 1):
        if line.startswith('=== RUN   '):
            case = line.removeprefix('=== RUN   ')
        if line.startswith('RV11_ASSERTION '):
            row = json.loads(line.removeprefix('RV11_ASSERTION '))
            row['test_case'] = case
            row['raw_evidence'] = {'path': p.name, 'line': n, 'line_sha256': sha(line.encode())}
            rows.append(row)
            if p.name in selection and selection[p.name](case):
                selected.append(row)
    runs.append({'path': p.name, 'sha256': sha(p.read_bytes()), 'assertions': len(rows), 'counts': dict(collections.Counter(x['status'] for x in rows))})
assert len(selected) == 92, len(selected)
assert all(x['status'] == 'PASS' for x in selected)
dump(OUT / 'selected-checks.json', selected)
dump(OUT / 'runs.json', runs)
sources = []
paths = subprocess.check_output(['git', '-C', str(WORK), 'ls-files'], text=True).splitlines()
for path in paths:
    if path.startswith(('adapters/decision/', 'internal/domain/', 'internal/canonical/', 'migrations/sqlite/', 'spec/v2.0/contracts/')) or path in ['go.mod', 'go.sum', 'spec/v2.0/06_ACCEPTANCE_TESTS.md', 'spec/v2.0/11_EVALUATION_AND_INTEGRATION.md']:
        raw = (WORK / path).read_bytes()
        sources.append({'path': path, 'sha256': sha(raw), 'size': len(raw)})
dump(OUT / 'source-manifest.json', sources)
for path in ['internal/domain/decision.go', 'internal/domain/changes.go', 'adapters/decision/jev.go']:
    dest = OUT / 'snapshot' / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes((WORK / path).read_bytes())
known_wrong = [r for r in selected if r['id'].startswith('FAULT-probability-mismatch-')]
dump(OUT / 'review.json', {
    'schema_version': '1.0.0', 'review_id': 'W11-APPLICATION-E916704', 'reviewer': 'orchestration_verifier',
    'source_commit': commit, 'completed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'verdict': 'HARD_GATE_FIX_PASS_IN_SCOPE_ADAPTER_DELTA_REQUIRED', 'stage_completed': False, 'formal_acceptance_signed': False,
    'measurement_mode': 'FIXTURE', 'source_worktree_clean': True, 'source_count': len(sources),
    'finding_closures': [{
        'id': 'W11-HARD-GATE-01', 'status': 'CLOSED_IN_SCOPE',
        'original_report': '../application-4545151/review.json',
        'evidence': 'The original exact probe on e916704 proves both public HTTP no-signal FAIL/missing requests become ABSTAIN and proposals reject. Synthetic historical immutable DECIDED+FAIL remains readable, but public adoption returns 422 with active decisions unchanged.',
        'implementation': 'decisionHardFailures always runs before decision publication and also runs in validateDecisions for new and historical adoption. The immutable receipt is not rewritten.',
        'checks': [r['id'] for r in selected if r['id'].startswith(('NO-SIGNAL-', 'HISTORICAL-'))],
        'scope_limit': 'The fixed requests stop at rejected proposals, so the two old conditional apply branches are no longer executed. That explains the count reduction from 94 to 92, not deleted assertions.'
    }],
    'regression_evidence': {
        'selected_assertion_coverage': 92, 'selected_pass': 92,
        'single_full_suite_green': False,
        'selection': {'retry.stdout.txt': 'all tests except PromptAndRaces/FaultPersistence', 'loopback-isolated.stdout.txt': 'PromptAndRaces only', 'transport-diagnostic.stdout.txt': 'FaultPersistence only'},
        'excluded_contract_validation': [r['id'] for r in known_wrong],
        'reason': 'Transient loopback transport failures occurred before handler arrival in different full batches. They correctly produced safe ABSTAIN but did not exercise intended scenarios. All raw failed batches remain. A dedicated client, longer positive deadlines and consumed request body made focused proof possible; substantive assertions were retained.',
        'timeout_diagnostic': 'Focused FaultPersistence passed all 21 assertions including a handler-entered timeout with context deadline exceeded, 503, redirect, oversize and continued work.',
        'harness_changes': 'See probe-harness.diff: positive deadline 1s -> 5s; explicit failure timeout 20ms -> 3s with handler fallback 10s; per-server client; consume request body; diagnostic transport error logging. No product source edits.',
        'original_probe_sha256': sha(original), 'diagnostic_probe_sha256': sha(current),
    },
    'open_adapter_issue': {
        'id': 'W11-TYPED-CONFIDENCE-02', 'status': 'OPEN_AWAITING_ROOT_DELTA',
        'source': 'adapters/decision/jev.go choice probability comparison',
        'finding': 'The frozen adapter incorrectly requires confidence to equal the selected option probability. Official docs explicitly permit distinct values. Consequently a probability-mismatch ABSTAIN assertion in the old fixture is not valid acceptance evidence and is excluded from contract approval.',
        'official_sources_independently_read': [
            {'url': 'https://docs.typesafe.ai/api', 'support': 'Choice is the highest-probability option; example selected probability 0.88 and confidence 0.81.'},
            {'url': 'https://docs.typesafe.ai/confidence', 'support': 'Confidence summarizes the shape of the distribution and is not simply the selected probability.'}
        ],
        'requested_delta_validation': 'Accept distinct in-range confidence/probability when chosen option is argmax and confidence passes frozen threshold. Reject unknown/nonmax chosen action, malformed distribution, low confidence and changed scope/model. Recompute existing development raw separately; no repeat live calls.'
    },
    'limits': ['No actual Jev request issued by this reviewer.', 'No formal holdout contents/labels read or generated.', 'A08 LIVE_SERVICE, W11-G03/G04, protected store and whole stage remain unaccepted.', '92 passing covered assertions are not a claim that the frozen typed contract is correct; the known confidence contract defect remains open.'],
    'commands': [
        'go test -overlay <original overlay> ./internal/domain -run ^TestRV11 -count=1 -v',
        'go test -overlay <isolated client overlay> ./internal/domain -run ^TestRV11(PromptAndRaces|FaultPersistence)$ -count=1 -v',
        'go test -overlay <diagnostic overlay> ./internal/domain -run ^TestRV11FaultPersistence$ -count=1 -v'
    ]
})
index = [{'path': p.relative_to(OUT).as_posix(), 'sha256': sha(p.read_bytes()), 'size': p.stat().st_size} for p in sorted(OUT.rglob('*')) if p.is_file() and p.name != 'index.json']
dump(OUT / 'index.json', {'source_commit': commit, 'files': index})
print(json.dumps({'report_sha256': sha((OUT / 'review.json').read_bytes()), 'index_sha256': sha((OUT / 'index.json').read_bytes()), 'files': len(index), 'selected_pass': len(selected), 'sources': len(sources)}, ensure_ascii=False))
