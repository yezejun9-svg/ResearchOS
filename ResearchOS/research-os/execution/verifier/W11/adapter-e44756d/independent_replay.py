"""Read-only replay of the already completed 60-case DEVELOPMENT run. No network code."""
import base64
import collections
import hashlib
import json
import math
import pathlib
import statistics

ROOT = pathlib.Path(__file__).resolve().parents[4]
OUT = pathlib.Path(__file__).resolve().parent
RUN = ROOT / 'execution/receipts/W11/development-live/3dd0b57c-5a59-4b59-9201-951d6ecd3be1'
DATA = ROOT / 'evaluation/development/jev/dataset.json'
FAMILIES = DATA.with_name('source_families.json')
checks = []


def sha(raw):
    return 'sha256:' + hashlib.sha256(raw).hexdigest()


def canonical(v):
    # All hash-bound data here has finite integral evidence values and the decimal threshold 0.8.
    # Exact parity with the persisted Go/JCS digests is checked for every request/state/rubric.
    def normalize(x):
        if isinstance(x, float) and math.isfinite(x) and x.is_integer():
            return int(x)
        if isinstance(x, list):
            return [normalize(y) for y in x]
        if isinstance(x, dict):
            return {k: normalize(y) for k, y in x.items()}
        return x
    return json.dumps(normalize(v), ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def strict(raw):
    def unique(pairs):
        o = {}
        for k, v in pairs:
            if k in o:
                raise ValueError('duplicate JSON key: ' + k)
            o[k] = v
        return o
    return json.loads(raw, object_pairs_hook=unique, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))


def check(name, expected, actual):
    checks.append({'id': name, 'expected': expected, 'actual': actual, 'status': 'PASS' if expected == actual else 'FAIL'})
    if expected != actual:
        raise AssertionError((name, expected, actual))


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


source_files = [DATA, FAMILIES] + sorted(p for p in RUN.iterdir() if p.is_file())
source_before = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in source_files}
data = strict(DATA.read_bytes())
families = strict(FAMILIES.read_bytes())
before = strict((RUN / 'before.json').read_bytes())
old = strict((RUN / 'report.json').read_bytes())
check('frozen-dataset-hash', before['dataset_sha256'], sha(DATA.read_bytes()))
check('frozen-families-hash', before['development_families_sha256'], sha(FAMILIES.read_bytes()))
check('rubric-threshold-unchanged', 0.8, data['rubric']['confidence_threshold'])
check('development-only', ['DEVELOPMENT_ONLY', 'PROJECT', 0, 'NONE'], [data['split'], data['access_class'], data['holdout_count'], data['qualification_authority']])
check('source-family-limits', [1, 0], [families['source_family_count'], families['independent_empirical_source_count']])
rubric_hash = sha(canonical(data['rubric']))
check('frozen-rubric-hash', before['rubric_sha256'], rubric_hash)
ids = [c['id'] for c in data['cases']]
check('unique-sixty-cases', [60, 60], [len(ids), len(set(ids))])
check('exact-raw-inventory', sorted(ids), sorted(p.name.removesuffix('.raw.json') for p in RUN.glob('*.raw.json')))
check('family-case-inventory', sorted(ids), sorted(families['cases']))
check('old-result-inventory', sorted(ids), sorted(c['id'] for c in old['cases']))
old_rows = {c['id']: c for c in old['cases']}
rows = []
for case in data['cases']:
    cid = case['id']
    raw_path = RUN / (cid + '.raw.json')
    env = strict(raw_path.read_bytes())
    raw_response = base64.b64decode(env['response'], validate=True)
    answer = strict(raw_response)
    ev = case['state']['evidence']
    objective = 'ACCEPT' if (ev['test_status'] == 'PASS' and ev['citation_exists'] is True and ev['content_hash_matches'] is True and ev['revision_current'] is True and ev['contradictory'] is False and ev['observed_total'] == sum(ev['observations'])) else 'REJECT'
    check(cid + '/objective-label', [objective, objective == 'REJECT'], [case['expected'], case['critical']])
    check(cid + '/scope', case['scope'], env['binding']['scope'])
    check(cid + '/project', 'W11-development', env['binding']['project_id'])
    check(cid + '/exact-request', {'model': case['scope']['model_revision'], 'state': case['state'], 'questions': data['rubric']['questions']}, env['request'])
    check(cid + '/input-hash', sha(canonical(case['state'])), env['binding']['input_hash'])
    check(cid + '/request-hash', sha(canonical(env['request'])), env['request_hash'])
    check(cid + '/rubric-hash', rubric_hash, env['binding']['rubric_hash'])
    check(cid + '/response-hash', sha(raw_response), env['response_hash'])
    check(cid + '/original-live-response', [1, 'LIVE', True, 200, ''], [env['version'], env['measurement_mode'], env['jev_called'], env['http_status'], env['transport_error']])
    check(cid + '/exact-response-keys', ['answers', 'model', 'usage'], sorted(answer))
    check(cid + '/actual-model', case['scope']['model_revision'], answer['model'])
    check(cid + '/answer-ids', ['action'], sorted(answer['answers']))
    a = answer['answers']['action']
    check(cid + '/typed-choice-keys', ['choice', 'confidence', 'probabilities', 'type'], sorted(a))
    check(cid + '/choice-type', 'choice', a['type'])
    check(cid + '/option-set', sorted(data['rubric']['questions']['action']['criteria']), sorted(a['probabilities']))
    check(cid + '/finite-range', True, all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) and 0 <= v <= 1 for v in [a['confidence'], *a['probabilities'].values()]))
    check(cid + '/sum-one', True, abs(sum(a['probabilities'].values()) - 1) <= 1e-5)
    check(cid + '/selected-known', True, a['choice'] in a['probabilities'])
    check(cid + '/selected-maximum', True, max(a['probabilities'].values()) <= a['probabilities'][a['choice']] + 1e-5)
    check(cid + '/usage-valid', True, set(answer['usage']) == {'input_tokens', 'output_tokens'} and all(isinstance(v, int) and not isinstance(v, bool) and v >= 0 for v in answer['usage'].values()))
    abstain = a['confidence'] < data['rubric']['confidence_threshold']
    old_abstain = abs(a['confidence'] - a['probabilities'][a['choice']]) > 1e-5 or abstain
    expected_old_selected = '' if abs(a['confidence'] - a['probabilities'][a['choice']]) > 1e-5 else a['choice']
    check(cid + '/old-outcome-reproducible', [old_abstain, expected_old_selected, env['response_hash']], [old_rows[cid]['abstained'], old_rows[cid]['selected'], old_rows[cid]['response_sha256']])
    rows.append({'id': cid, 'scope': case['scope'], 'objective_expected': objective, 'critical': case['critical'], 'raw_choice': a['choice'], 'selected': a['choice'], 'confidence': a['confidence'], 'selected_probability': a['probabilities'][a['choice']], 'abstained': abstain, 'correct': not abstain and a['choice'] == objective, 'false_accept': not abstain and a['choice'] == 'ACCEPT' and objective == 'REJECT', 'false_reject': not abstain and a['choice'] == 'REJECT' and objective == 'ACCEPT', 'raw_prediction_correct': a['choice'] == objective, 'old_abstained': old_abstain, 'newly_parseable': old_abstain and abs(a['confidence'] - a['probabilities'][a['choice']]) > 1e-5, 'latency_ms_original_call': env['latency_ms'], 'usage_original_call': answer['usage'], 'raw_file_sha256': sha(raw_path.read_bytes()), 'response_sha256': env['response_hash']})


def metrics(items):
    n = len(items)
    pos = sum(x['objective_expected'] == 'ACCEPT' for x in items)
    neg = n - pos
    fa = sum(x['false_accept'] for x in items)
    fr = sum(x['false_reject'] for x in items)
    abst = sum(x['abstained'] for x in items)
    return {'case_count': n, 'positive_label_count': pos, 'negative_label_count': neg, 'parseable_response_count': n, 'correct_count': sum(x['correct'] for x in items), 'false_accept_count': fa, 'critical_false_accept_count': sum(x['false_accept'] and x['critical'] for x in items), 'false_reject_count': fr, 'abstain_count': abst, 'abstain_rate': abst / n, 'false_accept_rate_over_all_cases': fa / n, 'false_accept_rate_over_negative_cases': fa / neg, 'false_reject_rate_over_positive_cases': fr / pos, 'host_nonabstained_rate': (n - abst) / n, 'automatic_action_coverage': 0, 'raw_prediction_correct_count_before_threshold': sum(x['raw_prediction_correct'] for x in items), 'input_tokens_original_calls': sum(x['usage_original_call']['input_tokens'] for x in items), 'output_tokens_original_calls': sum(x['usage_original_call']['output_tokens'] for x in items), 'original_latency_ms_median': statistics.median(x['latency_ms_original_call'] for x in items), 'original_latency_ms_max': max(x['latency_ms_original_call'] for x in items)}


overall = metrics(rows)
by_language = {language: metrics([x for x in rows if x['scope']['language'] == language]) for language in ['zh', 'zh-en']}
check('original-summary-recomputed', [old['correct_count'], old['abstain_count']], [sum(not x['old_abstained'] and x['raw_prediction_correct'] for x in rows), sum(x['old_abstained'] for x in rows)])
check('all-source-bytes-preserved', source_before, {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in source_files})
dump(OUT / 'python-checks.json', checks)
dump(OUT / 'python-rows.json', rows)
dump(OUT / 'input-hashes.json', source_before)
dump(OUT / 'python-replay.json', {'schema': 'W11_INDEPENDENT_OFFLINE_REINTERPRETATION_V1', 'original_run': RUN.relative_to(ROOT).as_posix(), 'new_live_calls': 0, 'new_samples': 0, 'formal_holdout_read': False, 'measurement_mode': 'OFFLINE_REPLAY_OF_EXISTING_LIVE_DEVELOPMENT_RESPONSES', 'frozen_threshold': data['rubric']['confidence_threshold'], 'dataset_sha256': sha(DATA.read_bytes()), 'source_families_sha256': sha(FAMILIES.read_bytes()), 'original_report_sha256': source_before[(RUN / 'report.json').relative_to(ROOT).as_posix()], 'original_counts_unchanged': {'correct': old['correct_count'], 'abstain': old['abstain_count']}, 'overall': overall, 'by_language': by_language, 'qualification': 'BLOCKED_INDEPENDENT_HOLDOUT_NOT_INCLUDED', 'maximum_mode': 'ADVISORY', 'automatic_authority': 'NONE', 'cost': None, 'cost_status': 'UNKNOWN_NOT_BILLING_EVIDENCE', 'source_family_count': 1, 'independent_empirical_source_count': 0, 'coverage_limits': families['coverage'], 'independent_check_count': len(checks)})
print(json.dumps({'overall': overall, 'by_language': by_language, 'checks': len(checks)}, ensure_ascii=False))
