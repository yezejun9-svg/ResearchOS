import collections
import datetime
import hashlib
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[4]
OUT = pathlib.Path(__file__).resolve().parent
WORK = ROOT / '.local/worktrees/w11-application-review-4545151'
PROBE = ROOT / '.local/w11-application-review-4545151/review_test.go'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def dump(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


commit = subprocess.check_output(['git', '-C', str(WORK), 'rev-parse', 'HEAD'], text=True).strip()
dirty = subprocess.check_output(['git', '-C', str(WORK), 'status', '--porcelain'], text=True)
assert commit.startswith('4545151') and not dirty
checks = []
lines = (OUT / 'final-independent.stdout.txt').read_text(encoding='utf-8-sig').splitlines()
for n, line in enumerate(lines, 1):
    if line.startswith('RV11_ASSERTION '):
        row = json.loads(line.removeprefix('RV11_ASSERTION '))
        row['raw_evidence'] = {'path': 'final-independent.stdout.txt', 'line': n, 'line_sha256': sha(line.encode())}
        checks.append(row)
assert len(checks) == 94
counts = dict(collections.Counter(x['status'] for x in checks))
assert counts == {'FAIL': 7, 'PASS': 87}
dump(OUT / 'checks.json', checks)
(OUT / 'review_test.go.txt').write_bytes(PROBE.read_bytes())
paths = subprocess.check_output(['git', '-C', str(WORK), 'ls-files'], text=True).splitlines()
sources = []
for path in paths:
    if (path.startswith(('adapters/decision/', 'internal/domain/', 'internal/canonical/', 'migrations/sqlite/', 'spec/v2.0/contracts/')) or path in ['go.mod', 'go.sum', 'spec/v2.0/06_ACCEPTANCE_TESTS.md', 'spec/v2.0/11_EVALUATION_AND_INTEGRATION.md']):
        raw = (WORK / path).read_bytes()
        sources.append({'path': path, 'sha256': sha(raw), 'size': len(raw)})
dump(OUT / 'source-manifest.json', sources)
for path in ['adapters/decision/jev.go', 'internal/domain/decision.go', 'internal/domain/qualification.go', 'internal/domain/changes.go', 'internal/domain/context.go', 'internal/domain/http.go', 'internal/domain/auth.go', 'internal/domain/operations.go', 'migrations/sqlite/0002_domain.sql']:
    dest = OUT / 'snapshot' / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes((WORK / path).read_bytes())

finding = {
    'id': 'W11-HARD-GATE-01', 'priority': 'P1', 'status': 'OPEN',
    'title': '无模型信号的决策跳过硬失败/缺证据门，并能经独立验收实际采用',
    'sources': ['internal/domain/decision.go:135', 'internal/domain/changes.go:85'],
    'trigger': 'POST /decisions with signals=[], qualification_id=null, status=DECIDED and either a deterministic FAIL result or nonempty missing_evidence.',
    'actual': 'Both requests return 201 DECIDED. POST /change-proposals returns 201. The standard independent verifier acceptance and apply flow returns APPLIED; ProjectState.current_decision_refs actually changes to the failing receipt.',
    'cause': 'prepareDecision returns before its hard-results/missing-evidence checks when no signals/qualification exist. validateDecisions only checks status==DECIDED and reference freshness, so historical failing DECIDED receipts can also be proposed.',
    'expected': 'Hard failures and missing evidence force ABSTAIN or request rejection independently of model signal presence. The adoption boundary also refuses equivalent historical receipts.',
    'recommended_fix': 'Remove or narrow the no-signal early return so universal hard gates always run; add corresponding adoption-time checks for historical DECIDED receipts without rewriting immutable history.',
    'evidence_checks': [x['id'] for x in checks if x['status'] == 'FAIL'],
    'boundary': 'The two current request variants are real HTTP + SQLite + independent acceptance/apply flows. The historical variant is an explicit trusted fixture insertion of a canonical immutable pre-fix receipt, followed by real HTTP adoption attempt. No external service or formal holdout used.'
}
report = {
    'schema_version': '1.0.0', 'review_id': 'W11-APPLICATION-4545151', 'reviewer': 'orchestration_verifier',
    'source_commit': commit, 'review_type': 'EARLY_INDEPENDENT_APPLICATION_REVIEW', 'verdict': 'NEEDS_FIX',
    'stage_completed': False, 'formal_acceptance_signed': False, 'measurement_mode': 'FIXTURE',
    'completed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'command': 'go1.27.1 test -overlay .local/w11-application-review-4545151/overlay.json ./internal/domain -run ^TestRV11 -count=1 -v',
    'command_worktree': str(WORK), 'exit_code': 1,
    'probe_sha256': sha(PROBE.read_bytes()), 'source_count': len(sources), 'source_worktree_clean': True,
    'independent_assertions': {'total': len(checks), 'counts': counts}, 'findings': [finding],
    'verified_in_scope': [
        'Independent choice/score/noul response positive and ten malformed/contradictory/unknown-field/schema mutations.',
        'Loopback invocation receives complete subject/input/rubric/evidence Artifact bodies with hash bindings; fixture sends no Authorization credential and cannot assert LIVE.',
        'In-flight subject/evidence/nested dependency invalidation and grant/credential/role revocation refuse publication; Artifact/decision/upload counts remain unchanged.',
        'SQLite sealed metadata/content triggers prevent reclassification, byte-size mutation and body overwrite; unchanged positive invocation remains valid.',
        'HTTP 503, redirect, malformed JSON, negative usage, mismatched confidence, timeout and oversized responses preserve hashed raw evidence and ABSTAIN without adoption or automatic authority; subsequent work continues.',
        'Imported LIVE claims including duplicate signals are downgraded to FIXTURE/jev_called=false and ABSTAIN; JSON cannot mint the private host capability.',
        'Measured high-confidence decisions with FAIL, NOT_RUN or missing evidence ABSTAIN and cannot enter a change proposal.',
        'Canonical raw Artifact reuse preserves one Artifact ID; changed provenance with same content is refused.',
        'Client LIVE declaration and huge claimed dataset counts still produce DRAFT/ADVISORY/jev_called=false; result admission and BOUNDED_AUTO return 503.'
    ],
    'limits': [
        'No A08 LIVE_SERVICE, independent labels, formal holdout, per-key model qualification or stage signature.',
        'No actual protected-store/AppContainer formal boundary was implemented or verified by this application review.',
        'Host positive testing used an explicit loopback fixture; trusted custom HTTP transports are outside client-supplied HTTP capability.',
        'Historical fixture tests model previously stored canonical receipts; they are not claims that the public API can directly insert arbitrary persisted records.'
    ],
    'iteration_notes': [
        'independent.stdout.txt was the first probe. Three mutation scenarios tried writes that SQLite immutability triggers correctly rejected; six resulting expectations were probe mistakes, not product findings. The final probe explicitly expects those database guards and retains successful completion.',
        'independent-complete.stdout.txt contains the corrected matrix plus expanded typed/hard-gate coverage; final-independent.stdout.txt adds historical adoption revalidation and is the sole final assertion tally.'
    ],
    'artifacts': ['checks.json', 'review_test.go.txt', 'final-independent.stdout.txt', 'source-manifest.json', 'snapshot/'],
}
dump(OUT / 'review.json', report)
index = []
for p in sorted(OUT.rglob('*')):
    if p.is_file() and p.name != 'index.json':
        index.append({'path': p.relative_to(OUT).as_posix(), 'sha256': sha(p.read_bytes()), 'size': p.stat().st_size})
dump(OUT / 'index.json', {'source_commit': commit, 'files': index})
print(json.dumps({'report_sha256': sha((OUT / 'review.json').read_bytes()), 'index_sha256': sha((OUT / 'index.json').read_bytes()), 'files': len(index), 'sources': len(sources), 'assertions': counts}, ensure_ascii=False))
