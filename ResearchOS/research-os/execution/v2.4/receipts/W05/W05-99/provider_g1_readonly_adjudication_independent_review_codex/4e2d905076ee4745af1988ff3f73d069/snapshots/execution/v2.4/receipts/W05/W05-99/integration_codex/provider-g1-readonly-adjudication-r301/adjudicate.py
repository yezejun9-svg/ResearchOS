import datetime
import hashlib
import json
from pathlib import Path
import re
import sys

if sys.flags.optimize != 0:
    raise RuntimeError('Optimized Python prohibited')
ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
PUBLIC = ROOT / 'execution/v2.4/receipts/W05/W05-99'
REG = PUBLIC / 'integration_codex/handler-and-g1-originals-r301'
ORIGINAL = PUBLIC / 'provider_whole9_g1_root_executor_codex/788ce69c409b472799ee1389b778f9da'
TAP = PUBLIC / 'provider_whole9_g1_tap_harness_readonly_codex/ae441a8a6f194cb193b23344225ef408'
READS = {}


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def check(condition, reason):
    if not condition:
        raise RuntimeError(reason)


def read(path):
    path = Path(path).resolve()
    if path not in READS:
        READS[path] = path.read_bytes()
    return READS[path]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def ref(path):
    path = Path(path).resolve()
    check(path.is_relative_to(ROOT), 'Receipt outside Root public scope')
    raw = read(path)
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(raw), 'bytes': len(raw)}


def save(name, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    with (OUT / name).open('xb') as stream:
        stream.write(raw)
    return ref(OUT / name)


DIRECTIVE = re.compile(rb'^\s*(?:ok|not ok)\s+\d+\b.*?\s+#\s*(?:SKIP|TODO)\b', re.I)
NOT_OK = re.compile(rb'^\s*not ok\b')
POINT = re.compile(rb'^ok (\d+) - (.+)$')
SUMMARY = re.compile(rb'^# (tests|pass|fail|cancelled|skipped|todo) (\d+)\r?$')


def parse_tap(raw):
    check(raw.endswith(b'\n'), 'Truncated TAP terminal line')
    points = []
    counts = {}
    plans = []
    for line in raw.splitlines():
        check(not NOT_OK.match(line), 'Actual not-ok test point')
        check(not DIRECTIVE.search(line), 'Actual SKIP/TODO test-point directive')
        point = POINT.match(line)
        if point:
            points.append((int(point[1]), point[2].decode('utf-8')))
        match = SUMMARY.match(line)
        if match:
            key = match[1].decode('ascii')
            check(key not in counts, 'Duplicate TAP summary ' + key)
            counts[key] = int(match[2])
        plan = re.fullmatch(rb'1\.\.(\d+)', line)
        if plan:
            plans.append(int(plan[1]))
    check(counts == {'tests': 26, 'pass': 26, 'fail': 0, 'cancelled': 0, 'skipped': 0, 'todo': 0}, 'TAP complete summary mismatch')
    check(plans == [26], 'TAP plan missing, duplicate or mismatched')
    check([point[0] for point in points] == list(range(1, 27)), 'TAP actual test-point IDs incomplete/duplicate/gapped')
    check(len({point[1] for point in points}) == 26, 'Repeated TAP test title')
    return {'counts': counts, 'actual_points': [{'ordinal': number, 'title': title} for number, title in points]}


def main():
    started = now()
    cp_raw = (ROOT / 'execution/v2.4/checkpoint.json').read_bytes()
    ow_raw = (ROOT / 'execution/v2.4/path_ownership.json').read_bytes()
    cp = json.loads(cp_raw)
    ow = json.loads(ow_raw)
    check(cp['revision'] == 301 and ow['revision'] == 129 and len(cp['failure_counters']) == 322, 'CAS301 exact state required')
    scope_path = REG / 'provider_g1_readonly_adjudication_scope.json'
    check(sha(read(scope_path)) == 'e21a09b9409b1991f2710278f3e8eef9eca7f088fa54a0943de66d49e9926e73', 'Scope bytes drift')
    scope_ref = ref(scope_path)
    check(cp['work_in_progress']['provider_whole9_g1_readonly_adjudication_scope_ref'] == scope_ref, 'Canonical scope binding mismatch')
    check(ow['card_path_bindings']['W05-99']['subtasks']['provider_whole9_g1_independent']['readonly_adjudication_scope_ref'] == scope_ref, 'Ownership scope binding mismatch')
    save('canonical-start.json', {'at': started, 'checkpoint_sha256': sha(cp_raw), 'ownership_sha256': sha(ow_raw), 'scope_ref': scope_ref,
        'checkpoint_revision': 301, 'ownership_revision': 129, 'failure_origins': 322, 'execution': 'offline Python readonly adjudication only'})
    proposal = json.loads(read(TAP / 'proposal.json'))
    check(sha(read(TAP / 'proposal.json')) == 'a456735d8fc523d45515927a4fb7ccb210ada3c1a2f320e103f54e6506af3fba', 'Proposal drift')
    controls = []
    for control in proposal['future_string_controls_NOT_RUN']:
        line = control['line'].encode('utf-8')
        detected = bool(DIRECTIVE.search(line))
        check(detected == control['directive'], 'Offline directive control mismatch')
        if isinstance(control.get('acceptable'), bool):
            check((not detected and not NOT_OK.match(line)) == control['acceptable'], 'Offline point acceptance mismatch')
        if isinstance(control.get('summary_acceptable'), bool):
            summary = SUMMARY.match(line)
            check(summary is not None and (int(summary[2]) == 0) == control['summary_acceptable'], 'Offline summary acceptance mismatch')
        controls.append({**control, 'actual_directive': detected, 'result': 'PASS', 'type': 'OFFLINE_STRING_CONTROL_NOT_PRODUCT_TEST'})
    check(len(controls) == 10, 'Expected ten proposed string controls')
    save('tap-string-controls.actual.json', {'controls': controls, 'pass': 10, 'fail': 0, 'product_test_executions': 0})
    original_audit = json.loads(read(REG / 'g1.originals.audit.json'))
    for row in original_audit['g1_original_refs'] + original_audit['outer_original_refs']:
        raw = read(ROOT / row['path'])
        check(sha(raw) == row['sha256'] and len(raw) == row['bytes'], 'Original receipt drift ' + row['path'])
    go_inv = json.loads(read(ORIGINAL / 'go3.invocation.json'))
    js_inv = json.loads(read(ORIGINAL / 'js3.invocation.json'))
    check(go_inv['actual_exit'] == js_inv['actual_exit'] == 0, 'Original native child nonzero')
    go = [json.loads(line) for line in read(ORIGINAL / 'go3.stdout.raw').splitlines() if line]
    check(not any(event.get('Action') in ['fail', 'skip'] for event in go), 'Original Go fail/skip')
    expected_go = {'TestProviderBindingConfigAndBody', 'TestProviderBindingReasoningExactHistory', 'TestProviderBindingWireSignatureWhitespaceAndBlocks'}
    top_pass = {event['Test'] for event in go if event.get('Action') == 'pass' and event.get('Test') in expected_go}
    check(top_pass == expected_go, 'Original Go3 missing actual top-level pass')
    check({event['Test'] for event in go if 'Test' in event and '/' not in event['Test']} == expected_go, 'Unexpected original Go top selector')
    parsed = parse_tap(read(ORIGINAL / 'js3.stdout.raw'))
    raw = read(ORIGINAL / 'js3.stdout.raw')
    mutations = {
        'nonzero-todo': raw.replace(b'# todo 0\n', b'# todo 1\n'),
        'nonzero-skipped': raw.replace(b'# skipped 0\n', b'# skipped 1\n'),
        'duplicate-summary': raw + b'# tests 26\n',
        'missing-summary': raw.replace(b'# todo 0\n', b''),
        'missing-point': re.sub(rb'^ok 26 - .*\n', b'', raw, flags=re.M),
        'duplicate-point-id': re.sub(rb'^ok 26 - ', b'ok 25 - ', raw, flags=re.M),
        'actual-not-ok': re.sub(rb'^ok 26 - ', b'not ok 26 - ', raw, flags=re.M),
        'actual-skip-directive': re.sub(rb'(^ok 26 - .*?)(\n)', rb'\1 # SKIP unavailable\2', raw, flags=re.M),
        'actual-todo-directive': re.sub(rb'(^ok 26 - .*?)(\n)', rb'\1 # TODO later\2', raw, flags=re.M),
        'truncated-final-line': raw[:-1],
        'duplicate-plan': raw + b'1..26\n',
    }
    mutation_results = []
    for name, changed in mutations.items():
        check(changed != raw, 'Offline negative mutation did not alter input')
        try:
            parse_tap(changed)
        except RuntimeError as error:
            mutation_results.append({'control': name, 'actual_expected_rejection': str(error), 'result': 'PASS'})
        else:
            raise RuntimeError('Offline corrupted TAP accepted ' + name)
    save('tap-complete-raw-controls.actual.json', {'original': parsed, 'negative_controls': mutation_results,
        'negative_controls_pass': len(mutation_results), 'product_test_executions': 0})
    frozen = json.loads(read(ORIGINAL / 'compiled-dependencies.before.json'))
    check(frozen == json.loads(read(ORIGINAL / 'inputs.pre-case.json')) == json.loads(read(ORIGINAL / 'inputs.failure.current.json')), 'Original input vector drift')
    check(len(frozen) == 48392, 'Original closure count mismatch')
    lock = json.loads((ROOT / 'execution/toolchains/locked.json').read_bytes())['tools']
    check(Path(sys.executable).resolve() == Path(lock['python']['path']).resolve(), 'Different current Python')
    allowed_roots = [ROOT, Path(lock['go']['path']).parent.parent, Path(lock['node']['path']).parent, Path(lock['python']['path']).parent, Path(lock['git']['path']).parent]
    current = {}
    for index, (name, expected) in enumerate(frozen.items(), 1):
        path = Path(name).resolve()
        check(any(path.is_relative_to(allowed.resolve()) for allowed in allowed_roots) or path == Path('C:/Windows/System32/taskkill.exe').resolve(), 'Unregistered input path')
        check(not any(path.is_relative_to(private.resolve()) for private in [ROOT / '.local/resources', ROOT / 'vault', ROOT / '.vault']), 'Private input prohibited')
        data = path.read_bytes()
        actual = {'sha256': sha(data), 'bytes': len(data)}
        check(actual == expected, 'Current retained input drift ' + str(path))
        current[name] = actual
        if index % 10000 == 0:
            print(json.dumps({'input_hash_progress': index, 'total': len(frozen)}, ensure_ascii=True), flush=True)
    vector_ref = save('inputs.current.verified.json', current)
    artifacts = json.loads(read(ORIGINAL / 'artifacts.before-case.json'))
    work = ROOT / '.local/worktrees/codex-w0599-provider-binding/.local/provider-whole9-g1-esm-788ce69c409b472799ee1389b778f9da'
    actual_artifacts = {}
    for path in [work / 'domain.g1.test.exe', work / 'mu-worker.mjs', work / 'mu-worker.mjs.build.json']:
        expected = artifacts[str(path)]
        data = path.read_bytes()
        actual = {'sha256': sha(data), 'bytes': len(data)}
        check(actual == expected, 'Executed artifact drift ' + str(path))
        actual_artifacts[str(path)] = actual
    generated = {}
    for name, expected in artifacts.items():
        if Path(name).name == '_testmain.go':
            data = Path(name).read_bytes()
            actual = {'sha256': sha(data), 'bytes': len(data)}
            check(actual == expected, 'Original generated testmain drift')
            generated[name] = actual
    check(len(generated) == 1, 'Actual generated testmain proof missing/ambiguous')
    metadata = json.loads(read(ORIGINAL / 'bundle.build.original.json'))
    check(metadata['bundle_sha256'] == sha(read(ORIGINAL / 'bundle.original.mjs')), 'Original bundle provenance mismatch')
    check(actual_artifacts[str(work / 'mu-worker.mjs')]['sha256'] == metadata['bundle_sha256'], 'Executed bundle mismatches original provenance')
    for path, original in READS.items():
        check(path.read_bytes() == original, 'Sealed receipt changed during readonly adjudication')
    check((ROOT / 'execution/v2.4/checkpoint.json').read_bytes() == cp_raw and (ROOT / 'execution/v2.4/path_ownership.json').read_bytes() == ow_raw, 'Canonical changed during adjudication')
    result = save('result.json', {'status': 'ORIGINAL_NATIVE_G1_EVIDENCE_VERIFIED_UNDER_PRESERVED_FAILED_HARNESS',
        'actor': 'codex:/root', 'source_author': 'codex:/root/command_queue_impl', 'started_at': started, 'ended_at': now(),
        'scope_ref': scope_ref, 'original_audit_ref': ref(REG / 'g1.originals.audit.json'),
        'original_Go3_actual_exit': 0, 'original_Go_top_pass': sorted(top_pass),
        'original_Go_test_pass_events': sum(event.get('Action') == 'pass' and 'Test' in event for event in go),
        'original_JS3_actual_exit': 0, 'original_JS_actual_counts': parsed['counts'],
        'original_outer_actual_exit': 1, 'original_termination_actual_exit': 128,
        'original_harness_failure_preserved': True, 'actual_full_input_count': len(current), 'current_input_vector_ref': vector_ref,
        'retained_executed_artifacts': actual_artifacts, 'original_generated_testmain': generated,
        'offline_string_controls': 10, 'offline_complete_raw_negative_controls': len(mutation_results),
        'new_Go_Node_SQL_HTTP_model_executions': 0, 'external_paid_or_private_calls': 0,
        'source_or_canonical_writes': 0, 'held_positive_cases_unlocked': 0, 'whole9_source_acceptance': False,
        'Main23_handler38_composition_acceptance': False, 'formal_increment': 0,
        'qualification': 'Only original exact3 Go controls and26 JS FIXTURE transport controls. No real Go MODEL/provider HTTP, SQL, Session lifecycle, held history, LIVE or full whole9 acceptance.'})
    print(json.dumps({'result_ref': result}, ensure_ascii=True), flush=True)


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        save('failure.origin.json', {'at': now(), 'actual_error': repr(error), 'automatic_retry': False,
            'counter_reset': False, 'original_harness_failure_preserved': True, 'scope': 'Readonly adjudication; no test reexecution or source mutation'})
        raise
