import collections
import datetime
import hashlib
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[4]
OUT = pathlib.Path(__file__).resolve().parent
WORK = ROOT / '.local/worktrees/w11-adapter-review-e44756d'
LIVE = ROOT / 'execution/receipts/W11/development-live/3dd0b57c-5a59-4b59-9201-951d6ecd3be1'
AUTHOR = ROOT / 'execution/receipts/W11/development-reanalysis/fc84f1f4-7b8d-4df3-9e2b-5c1cda3c51a4'
checks = []


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(raw):
    return 'sha256:' + sha(raw)


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def check(name, want, got):
    checks.append({'id': name, 'expected': want, 'actual': got, 'status': 'PASS' if want == got else 'FAIL'})
    assert want == got, (name, want, got)


commit = subprocess.check_output(['git', '-C', str(WORK), 'rev-parse', 'HEAD'], text=True).strip()
check('frozen-adapter-commit', True, commit.startswith('e44756d'))
check('clean-source-worktree', '', subprocess.check_output(['git', '-C', str(WORK), 'status', '--porcelain'], text=True))
py = json.loads((OUT / 'python-replay.json').read_text(encoding='utf-8'))
py_rows = {x['id']: x for x in json.loads((OUT / 'python-rows.json').read_text(encoding='utf-8'))}
go_rows = {}
go_checks = []
for n, line in enumerate((OUT / 'independent-adapter.stdout.txt').read_text(encoding='utf-8-sig').splitlines(), 1):
    if line.startswith('RV11_ADAPTER_ASSERTION '):
        row = json.loads(line.removeprefix('RV11_ADAPTER_ASSERTION '))
        row['raw_line'] = n
        row['raw_line_sha256'] = sha(line.encode())
        go_checks.append(row)
    if line.startswith('RV11_ADAPTER_REPLAY '):
        row = json.loads(line.removeprefix('RV11_ADAPTER_REPLAY '))
        row['raw_line'] = n
        row['raw_line_sha256'] = sha(line.encode())
        go_rows[row['id']] = row
check('all-independent-go-assertions-pass', {'PASS': 79}, dict(collections.Counter(x['status'] for x in go_checks)))
check('go-response-inventory', sorted(py_rows), sorted(go_rows))
author = json.loads((AUTHOR / 'report.json').read_text(encoding='utf-8'))
author_before = json.loads((AUTHOR / 'before.json').read_text(encoding='utf-8'))
author_rows = {x['id']: x for x in author['cases']}
check('author-case-inventory', sorted(py_rows), sorted(author_rows))
check('author-offline-only', ['OFFLINE_REANALYSIS_OF_LIVE_RESPONSES', 0, 'ADVISORY', 0], [author['environment_mode'], author['provider_calls_this_run'], author['maximum_mode'], author['holdout_count']])
for cid, p in py_rows.items():
    g, a = go_rows[cid], author_rows[cid]
    check(cid + '/python-vs-go', [p['selected'], p['abstained'], p['objective_expected'], p['scope'], p['response_sha256'], p['raw_file_sha256'], p['usage_original_call']], [g['selected'], g['abstained'], g['expected'], g['scope'], g['response_hash'], g['raw_file_hash'], g['usage']])
    check(cid + '/abstention-reason', ['action:LOW_CONFIDENCE'] if p['abstained'] else [], g['reasons'])
    check(cid + '/python-vs-author', [p['selected'], p['abstained'], p['objective_expected'], p['scope'], p['response_sha256'], p['latency_ms_original_call']], [a['selected'], a['abstained'], a['expected'], a['scope'], a['response_sha256'], a['latency_ms']])
    check(cid + '/reanalysis-raw-byte-identical', (LIVE / (cid + '.raw.json')).read_bytes().hex(), (AUTHOR / (cid + '.raw.json')).read_bytes().hex())
    check(cid + '/author-input-hash', digest((LIVE / (cid + '.raw.json')).read_bytes()), author['reanalysis_input_sha256'][cid + '.raw.json'])
check('author-before-original-hash', digest((LIVE / 'before.json').read_bytes()), author['reanalysis_input_sha256']['before.json'])
check('author-before-report-consistent', author_before['reanalysis_input_sha256'], author['reanalysis_input_sha256'])
for field in ['case_count', 'correct_count', 'false_accept_count', 'critical_false_accept_count', 'false_reject_count', 'abstain_count', 'abstain_rate', 'false_accept_rate_over_all_cases', 'false_accept_rate_over_negative_cases', 'false_reject_rate_over_positive_cases']:
    check('author-overall-' + field, py['overall'][field], author[field])
check('author-typed-count', 60, author['successful_typed_response_count'])
check('author-token-counts', [py['overall']['input_tokens_original_calls'], py['overall']['output_tokens_original_calls']], [author['input_tokens'], author['output_tokens']])
inputs = json.loads((OUT / 'input-hashes.json').read_text(encoding='utf-8'))
for path, expected in inputs.items():
    check('original-input-still-unchanged/' + path, expected, digest((ROOT / path).read_bytes()))
snapshot = ['adapters/decision/jev.go', 'adapters/decision/jev_test.go', 'internal/domain/decision_test.go', 'evaluation/development/jev/dataset.json', 'evaluation/development/jev/source_families.json', 'go.mod', 'go.sum']
sources = []
for path in snapshot:
    raw = (WORK / path).read_bytes()
    dest = OUT / 'snapshot' / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(raw)
    sources.append({'path': path, 'sha256': sha(raw), 'size': len(raw)})
adapter_author = subprocess.check_output(['git', '-C', str(ROOT), 'show', author['source_revision'] + ':adapters/decision/jev.go'])
check('author-reanalysis-same-adapter', sha((WORK / 'adapters/decision/jev.go').read_bytes()), sha(adapter_author))
replayer_source = subprocess.check_output(['git', '-C', str(ROOT), 'show', author['source_revision'] + ':tests/jev/live/main.go'])
(OUT / 'author-reanalysis-main.go.txt').write_bytes(replayer_source)
(OUT / 'review_test.go.txt').write_bytes((ROOT / '.local/w11-adapter-review-e44756d/review_test.go').read_bytes())
dump(OUT / 'adapter-checks.json', go_checks)
dump(OUT / 'go-replay-rows.json', list(go_rows.values()))
# Avoid duplicating whole raw envelopes in the comparison log. Full byte comparison occurred above.
for row in checks:
    if row['id'].endswith('/reanalysis-raw-byte-identical'):
        row['expected'] = sha(bytes.fromhex(row['expected']))
        row['actual'] = sha(bytes.fromhex(row['actual']))
dump(OUT / 'comparison-checks.json', checks)
dump(OUT / 'source-manifest.json', sources)
dump(OUT / 'author-reanalysis-files.json', [{'path': p.relative_to(ROOT).as_posix(), 'sha256': sha(p.read_bytes()), 'size': p.stat().st_size} for p in sorted(AUTHOR.iterdir()) if p.is_file()])
py_checks = json.loads((OUT / 'python-checks.json').read_text(encoding='utf-8'))
report = {
    'schema_version': '1.0.0', 'review_id': 'W11-ADAPTER-E44756D', 'reviewer': 'orchestration_verifier',
    'source_commit': commit, 'completed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'verdict': 'PASS_IN_SCOPE', 'stage_completed': False, 'formal_acceptance_signed': False,
    'finding_closed': {'id': 'W11-TYPED-CONFIDENCE-02', 'status': 'CLOSED_IN_SCOPE', 'evidence': '15 independent boundary scenarios plus two frozen threshold checks prove confidence is distinct from selected probability, .8 remains exact, chosen action must be argmax within 1e-5, and malformed range/distribution still abstains.'},
    'official_sources_independently_read': [{'url': 'https://docs.typesafe.ai/api', 'support': 'Choice is highest-probability option. Official example probability .88 and confidence .81.'}, {'url': 'https://docs.typesafe.ai/confidence', 'support': 'Confidence is derived from distribution shape, not equality to selected probability.'}],
    'independent_validation': {'go_adapter_assertions': len(go_checks), 'python_integrity_and_label_checks': len(py_checks), 'go_python_author_comparison_checks': len(checks), 'all_pass': True, 'go_exit_code': 0},
    'offline_replay': {'original_run': LIVE.relative_to(ROOT).as_posix(), 'author_reanalysis': AUTHOR.relative_to(ROOT).as_posix(), 'author_reanalysis_source_commit': author['source_revision'], 'new_live_calls': 0, 'new_samples': 0, 'formal_holdout_read': False, 'original_raw_and_report_unchanged': True, 'original_outcome_preserved': {'correct_count': 16, 'parser_abstain_count': 44}, 'corrected_overall': py['overall'], 'corrected_by_language': py['by_language'], 'critical_false_accept_cases': [{'id': x['id'], 'confidence': x['confidence'], 'selected_probability': x['selected_probability'], 'objective_sum': 60, 'observed_total': 61} for x in py_rows.values() if x['false_accept']]},
    'interpretation': [
        '51 non-abstained responses consist of 49 correct and 2 critical false accepts; 9 low-confidence responses abstain.',
        'Both critical false accepts accept observed_total=61 where 20+35+5=60. They are paired language variants of one template, not two independent empirical source families.',
        'Overall false accepts / all cases is 2/60=3.33%; false accepts / negative labels is 2/30=6.67%. Each language has one critical false accept and 15 negative labels.',
        'Original usage across all 60 saved responses is 30154 input tokens and 2220 output tokens. Original report usage counted only its 16 parseable responses. Offline replay incurred no new provider usage; no billing cost is inferred.',
        'The corrected parser exposes existing model mistakes; this is not a new model evaluation or a performance improvement claim.'
    ],
    'qualification_limits': {'maximum_mode': 'ADVISORY', 'automatic_authority': 'NONE', 'holdout_count': 0, 'development_cases_per_language_key': 30, 'required_development_cases_per_key': 60, 'critical_errors_present': True, 'A08': 'BLOCKED_INDEPENDENT_HOLDOUT_NOT_INCLUDED', 'source_family_count': 1, 'independent_empirical_source_count': 0},
    'scope_limits': ['No protected holdout boundary, independent professional research judgment, formal A08 completion or W11 stage completion is claimed.', 'The review calls no network endpoint for replay. The Go replay test replaces the default HTTP transport with a fatal-on-use guard; Python replay imports no networking library.', 'The root replay tool was read and its existing outputs compared; the reviewer did not rerun that tool or request new LIVE credentials.'],
    'iteration_notes': ['Initial Python canonical hash check exposed 1.0 versus JCS 1 numeric encoding. The independent canonicalizer now normalizes integral floats and verifies every persisted Go/JCS request/input/rubric digest; no original bytes changed.'],
}
dump(OUT / 'review.json', report)
index = [{'path': p.relative_to(OUT).as_posix(), 'sha256': sha(p.read_bytes()), 'size': p.stat().st_size} for p in sorted(OUT.rglob('*')) if p.is_file() and p.name != 'index.json']
dump(OUT / 'index.json', {'source_commit': commit, 'files': index})
print(json.dumps({'report_sha256': sha((OUT / 'review.json').read_bytes()), 'index_sha256': sha((OUT / 'index.json').read_bytes()), 'files': len(index), 'go_assertions': len(go_checks), 'python_checks': len(py_checks), 'comparison_checks': len(checks)}, ensure_ascii=False))
