"""Proposed W05-only post-capture test.runtime handler.

It reads a Root-selected, immutable LIVE_WINDOWS bundle. The actual product
execution must be a separate registered, granted producer. This handler is
not a model caller or an independent formal reviewer.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
BOUNDARY = REPO / 'execution/v2.4/receipts/W05/W05-99'
IDS = tuple('A04-0' + str(i) for i in range(1, 7))
GATES = ('W05-G01', 'W05-G02', 'W05-H08', 'W05-P01', 'W05-U02')
SCENARIOS = ('success', 'tool_failed', 'request_timeout',
             'pending_queue_cancel', 'executor_crash')


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def strict_json(raw):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            require(key not in value, 'DUPLICATE_JSON_KEY')
            value[key] = item
        return value
    return json.loads(raw, object_pairs_hook=unique,
                      parse_constant=lambda _: require(False, 'NONFINITE_JSON'))


def pin_raw(ref):
    require(type(ref) is dict and set(ref) in ({'path', 'sha256'},
                                                 {'path', 'sha256', 'locator'}), 'REF_SHAPE')
    require(type(ref['path']) is str and type(ref['sha256']) is str and
            len(ref['sha256']) == 64, 'REF_FORMAT')
    relative = Path(ref['path'])
    require(not relative.is_absolute() and '..' not in relative.parts and
            '\\' not in ref['path'], 'REF_PATH')
    candidate = REPO / relative
    for part in (candidate, *candidate.parents):
        if part == REPO.parent:
            break
        require(not part.is_symlink() and not part.is_junction(), 'REF_REPARSE')
    path = candidate.resolve(strict=True)
    require(path.is_file() and path.is_relative_to(BOUNDARY.resolve(strict=True)),
            'REF_SCOPE')
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == ref['sha256'], 'REF_CHANGED')
    return raw, path


def read_ref(ref):
    raw, path = pin_raw(ref)
    value = strict_json(raw)
    if 'locator' in ref:
        location = ref['locator']
        require(type(location) is dict and set(location) == {'json_pointer'},
                'JSON_LOCATOR_REQUIRED')
        pointer = location['json_pointer']
        require(type(pointer) is str and (not pointer or pointer.startswith('/')),
                'JSON_POINTER_FORMAT')
        for token in pointer[1:].split('/') if pointer else ():
            require('~' not in token.replace('~1', '').replace('~0', ''),
                    'JSON_POINTER_ESCAPE')
            token = token.replace('~1', '/').replace('~0', '~')
            if type(value) is dict:
                require(token in value, 'JSON_POINTER_MISSING')
                value = value[token]
            elif type(value) is list:
                require(token.isdigit() and int(token) < len(value),
                        'JSON_POINTER_MISSING')
                value = value[int(token)]
            else:
                raise ValueError('JSON_POINTER_MISSING')
    return value, path


def selected_selector():
    task = os.environ.get('RESEARCHOS_TASK_ID')
    check = os.environ.get('RESEARCHOS_CHECK_ID') or ''
    case = os.environ.get('RESEARCHOS_CASE_ID') or ''
    require(task == 'W05' and ((case == 'A04' and not check) or
            (check in GATES and not case)), 'W05_EXACT_SELECTOR')
    return case or check


def verify_bundle(bundle, selector):
    require(type(bundle) is dict and bundle.get('schema') ==
            'researchos.w05.live-dispatch-bundle.v1' and
            bundle.get('task_id') == 'W05' and bundle.get('case_id') == 'A04' and
            bundle.get('mode') == 'LIVE_WINDOWS' and
            type(bundle.get('run_id')) is str and bundle['run_id'] and
            bundle.get('producer_actor') == 'codex:/root' and
            bundle.get('independent_acceptance') == 'NOT_EVALUATED',
            'BUNDLE_IDENTITY')
    accounting = bundle.get('accounting')
    require(type(accounting) is dict and set(accounting) ==
            {'mode', 'status', 'amount_usd', 'source_refs'} and
            accounting['mode'] in ('UNLIMITED_AMOUNT', 'CAPPED') and
            accounting['status'] in ('UNKNOWN', 'RECORDED') and
            type(accounting['source_refs']) is list and
            ((accounting['status'] == 'UNKNOWN' and
              accounting['amount_usd'] is None) or
             (accounting['status'] == 'RECORDED' and
              type(accounting['amount_usd']) in (int, float) and
              accounting['amount_usd'] >= 0 and
              bool(accounting['source_refs']))),
            'COST_ACCOUNTING_UNKNOWN_IS_NULL')
    for reference in accounting['source_refs']:
        pin_raw(reference)
    grant, _ = read_ref(bundle['root_grant_ref'])
    require(grant.get('schema') == 'researchos.w05.a04-root-grant.v1' and
            grant.get('run_id') == bundle['run_id'] and
            grant.get('decision') == 'GRANTED' and
            grant.get('mode') == 'LIVE_WINDOWS' and
            grant.get('accounting_mode') == accounting['mode'] and
            grant.get('selected_runtime') == bundle.get('selected_runtime') and
            grant.get('fixed_model') == bundle.get('fixed_model'),
            'ROOT_GRANT_SCOPE')
    originals = bundle.get('product_original_refs')
    require(type(originals) is list and originals and
            len({item.get('path') for item in originals}) == len(originals),
            'ROOT_PRODUCT_ORIGINALS_ABSENT')
    original_paths = {item['path'] for item in originals}
    for reference in originals:
        pin_raw(reference)
    invocations = bundle.get('invocations')
    require(type(invocations) is list and
            {row.get('lane') for row in invocations} == set(SCENARIOS) | {'H08', 'P01', 'U02'} and
            len(invocations) == 8, 'LIVE_LANES_INCOMPLETE')
    for row in invocations:
        require(type(row) is dict and set(row) ==
                {'lane', 'invocation_ref', 'scope_ref'}, 'INVOCATION_SHAPE')
        invocation, _ = read_ref(row['invocation_ref'])
        scope, _ = read_ref(row['scope_ref'])
        require(scope.get('schema') == 'researchos.w05.a04-live-scope.v1' and
                invocation.get('run_id') == scope.get('run_id') == bundle['run_id'] and
                invocation.get('lane') == scope.get('lane') == row['lane'] and
                invocation.get('root_grant_ref') ==
                scope.get('root_grant_ref') == bundle['root_grant_ref'] and
                invocation.get('argv') == scope.get('argv') and
                invocation.get('cwd') == scope.get('cwd') and
                invocation.get('env_names') == scope.get('env_names'),
                'INVOCATION_SCOPE')
        for key in ('stdout_ref', 'stderr_ref'):
            pin_raw(invocation[key])
            require(invocation[key]['path'] in original_paths,
                    'INVOCATION_RAW_NOT_ROOT_CAPTURED')
    rows = bundle.get('assertions')
    require(type(rows) is list and len(rows) == 6 and
            {row.get('id') for row in rows} == set(IDS), 'A04_EXACT_ASSERTIONS')
    for row in rows:
        require(row.get('status') == 'PASS' and
                type(row.get('raw_evidence_refs')) is list and
                row['raw_evidence_refs'], 'A04_MISSING_OR_FAILED')
        originals = []
        for reference in row['raw_evidence_refs']:
            original, _ = read_ref(reference)
            originals.append(original)
        require(any(type(item) is dict and item.get('schema') ==
                    'researchos.w05.a04-raw-observation.v1' and
                    item.get('assertion_id') == row['id'] and
                    item.get('run_id') == bundle['run_id'] and
                    item.get('lane') == row.get('lane') and
                    item.get('actual') == row.get('actual')
                    for item in originals), 'A04_ORIGINAL_OBSERVATION_MISSING')
        for item in originals:
            if type(item) is dict and item.get('assertion_id') == row['id']:
                facts, sources = item.get('facts'), item.get('fact_source_refs')
                require(type(facts) is dict and type(sources) is dict and
                        set(facts) == set(sources) and
                        all(type(ref) is dict and ref.get('path') in original_paths and
                            ref.get('path') not in
                            {entry['path'] for entry in row['raw_evidence_refs']} and
                            read_ref(ref)[0] == facts[key]
                            for key, ref in sources.items()),
                        'A04_RAW_FACT_NOT_FROM_PRODUCT_ORIGINAL')
    gates = bundle.get('gate_results')
    require(type(gates) is list and len(gates) == 5 and
            {row.get('id') for row in gates} == set(GATES), 'W05_EXACT_GATES')
    for row in gates:
        require(row.get('status') == 'PASS' and
                type(row.get('raw_evidence_refs')) is list and
                row['raw_evidence_refs'], 'W05_GATE_MISSING_OR_FAILED')
        for reference in row['raw_evidence_refs']:
            pin_raw(reference)
    return rows if selector == 'A04' else [row for row in gates if row['id'] == selector]


def main():
    try:
        selector = selected_selector()
        require(os.name == 'nt' and os.environ.get('RESEARCHOS_RUNTIME_LIVE') == '1',
                'LIVE_WINDOWS_NOT_GRANTED')
        source = os.environ.get('RESEARCHOS_W05_LIVE_BUNDLE_PATH')
        digest = os.environ.get('RESEARCHOS_W05_LIVE_BUNDLE_SHA256')
        require(source and digest and len(digest) == 64, 'ROOT_BUNDLE_NOT_SELECTED')
        path = Path(source)
        require(path.is_absolute() and path.is_file() and
                path.resolve(strict=True).is_relative_to(BOUNDARY.resolve(strict=True)) and
                not path.is_symlink() and not path.is_junction(), 'ROOT_BUNDLE_PATH')
        raw = path.read_bytes()
        require(hashlib.sha256(raw).hexdigest() == digest, 'ROOT_BUNDLE_CHANGED')
        bundle = strict_json(raw)
        rows = verify_bundle(bundle, selector)
        print(json.dumps({'schema': 'researchos.w05.test-runtime-live-result.v1',
                          'task_id': 'W05', 'selector': selector, 'run_id': bundle['run_id'],
                          'mode': 'LIVE_WINDOWS', 'status': 'PASS',
                          'cost_status': bundle['accounting']['status'],
                          'cost_amount_usd': bundle['accounting']['amount_usd'],
                          'assertion_ids': [row['id'] for row in rows],
                          'independent_acceptance': 'NOT_EVALUATED'},
                         ensure_ascii=False, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({'schema': 'researchos.w05.test-runtime-live-result.v1',
                          'status': 'NOT_RUN', 'reason': type(exc).__name__ + ':' + str(exc),
                          'independent_acceptance': 'NOT_EVALUATED'},
                         ensure_ascii=False), file=sys.stderr)
        return 3


if __name__ == '__main__':
    raise SystemExit(main())
