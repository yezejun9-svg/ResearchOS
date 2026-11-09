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
                require((token == '0' or token.isascii() and token.isdigit() and not token.startswith('0')) and int(token) < len(value),
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
    require(selector in ('A04', *GATES), 'OPEN_EXACT_SELECTOR')
    module = REPO / 'execution/v2.4/formal_profile_w05.py'
    require(module.is_file() and not module.is_symlink() and not module.is_junction(),
            'OPEN_FIXED_MAIN_PROFILE')
    for parent in module.parents:
        if parent == REPO.parent:
            break
        require(not parent.is_symlink() and not parent.is_junction(), 'OPEN_PROFILE_REPARSE')
    code = module.read_bytes()
    require(hashlib.sha256(code).hexdigest() == 'b9a807787da6b9d5fda81f4de44059a544ad9a6c6f1842fc33dd46b9975c29c3',
            'OPEN_CURRENT_PROFILE_SOURCE')
    namespace = {'__name__': 'researchos_trusted_w05_live_semantics',
                 '__file__': str(module)}
    exec(compile(code, str(module), 'exec'), namespace)
    require(hashlib.sha256(module.read_bytes()).hexdigest() == 'b9a807787da6b9d5fda81f4de44059a544ad9a6c6f1842fc33dd46b9975c29c3',
            'OPEN_PROFILE_CHANGED')
    return namespace['verify_capture_bundle'](
        lambda ref: read_ref(ref)[0], lambda ref: pin_raw(ref)[0], bundle, selector)



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
                          'status': 'OPEN', 'reason': type(exc).__name__ + ':' + str(exc),
                          'independent_acceptance': 'NOT_EVALUATED'},
                         ensure_ascii=False), file=sys.stderr)
        return 3


if __name__ == '__main__':
    raise SystemExit(main())
