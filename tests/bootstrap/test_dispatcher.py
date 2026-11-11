"""Real child-process checks for fail-closed construction command dispatch."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('dispatch', ROOT / 'execution/command_dispatcher/dispatch.py')
dispatch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dispatch)


def main():
    ids = []
    with tempfile.TemporaryDirectory(prefix='researchos-dispatch-') as directory:
        root = Path(directory)
        (root / 'execution/toolchains').mkdir(parents=True)
        locked = {'tools': {'python': {'path': sys.executable,
                   'sha256': hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest()}}}
        (root / 'execution/toolchains/locked.json').write_text(json.dumps(locked), encoding='utf-8')
        child = root / 'child.py'
        child.write_text('''import json,os,sys,time,subprocess,tempfile
mode=sys.argv[1]
if mode=='timeout': time.sleep(30)
if mode=='badexit': sys.exit(17)
if mode=='malformed': print('not json'); sys.exit(0)
if mode=='null': print('null'); sys.exit(0)
if mode=='array': print('[]'); sys.exit(0)
if mode=='duplicate-key': print('{"status":"FAIL","status":"PASS","assertion_ids":["X"],"assertions":1}'); sys.exit(0)
if mode=='nonfinite': print('{"status":"PASS","assertion_ids":["X"],"cost":NaN}'); sys.exit(0)
if mode=='orphan':
    subprocess.Popen([sys.executable,'-c','import time;time.sleep(4)'],cwd=tempfile.gettempdir())
    sys.exit(0)
ids=[] if mode=='zero' else ['CHILD-CHECK']
if mode=='duplicate': ids=['X','X']
if mode=='secret':
    value=os.environ['RESEARCHOS_TEST_API_KEY']
    print(value, file=sys.stderr)
    ids=[value]
if mode=='no-inheritance':
    assert 'RESEARCHOS_TEST_API_KEY' not in os.environ
print(json.dumps({'status':'PASS','assertions':len(ids),'assertion_ids':ids,'scope':'FIXTURE'}))
''', encoding='utf-8')
        base = dict(state='BOUND', platforms=[platform.system()], selectors={'task_id': ['W02']},
                    required_env=[], allowed_env=['SystemRoot', 'TEMP', 'TMP'], executable_tool='python',
                    argv=[str(child), 'pass'], cwd='.', timeout_seconds=10)

        def check(label, expected, **changes):
            entry = copy.deepcopy(base)
            entry.update(changes)
            (root / 'execution/commands.json').write_text(json.dumps({'commands': {'check': entry}}), encoding='utf-8')
            receipt, path = dispatch.execute('check', {'task_id': 'W02'}, root=root)
            assert receipt['status'] == expected, (label, receipt)
            assert (receipt['exit_code'] == 0) == (expected == 'PASS'), label
            for stream in ('stdout', 'stderr'):
                assert hashlib.sha256((root / receipt[stream]['path']).read_bytes()).hexdigest() == receipt[stream]['sha256']
            assert path.is_file()
            ids.append('W02-DISPATCH-' + label)
            return receipt, path

        first, _ = check('REAL_CHILD', 'PASS')
        second, _ = check('REPEATED_INVOCATION', 'PASS')
        assert first['invocation_id'] != second['invocation_id']
        check('UNBOUND', 'NOT_IMPLEMENTED', state='UNBOUND')
        check('PLATFORM', 'UNSUPPORTED_PLATFORM', platforms=['UnsupportedOS'])
        check('SELECTOR', 'NOT_IMPLEMENTED', selectors={'task_id': ['W99']})
        key = 'RESEARCHOS_TEST_API_KEY'
        original = os.environ.pop(key, None)
        try:
            check('MISSING_CREDENTIAL', 'MISSING_CREDENTIAL_OR_ENVIRONMENT', required_env=[key])
            secret = 'synthetic-only-quote"slash\\value'
            os.environ[key] = secret
            receipt, path = check('SECRET_REDACTION', 'PASS', argv=[str(child), 'secret'],
                                  required_env=[key], allowed_env=[*base['allowed_env'], key])
            for evidence in path.parent.iterdir():
                content = evidence.read_text(encoding='utf-8')
                assert secret not in content and json.dumps(secret)[1:-1] not in content
            assert receipt['assertion_ids'] == ['[REDACTED]']
            check('SECRET_ARG', 'SECRET_IN_ARGUMENTS', argv=[str(child), secret])
            check('NO_IMPLICIT_ENV', 'PASS', argv=[str(child), 'no-inheritance'])
        finally:
            os.environ.pop(key, None)
            if original is not None:
                os.environ[key] = original
        check('ZERO_ASSERTIONS', 'NOT_IMPLEMENTED', argv=[str(child), 'zero'])
        check('DUPLICATE_ASSERTIONS', 'INVALID_ASSERTION_REPORT', argv=[str(child), 'duplicate'])
        check('COMMAND_EXIT', 'COMMAND_FAILED', argv=[str(child), 'badexit'])
        check('MALFORMED_REPORT', 'INVALID_ASSERTION_REPORT', argv=[str(child), 'malformed'])
        for mode in ('null', 'array', 'duplicate-key', 'nonfinite'):
            check(mode.upper(), 'INVALID_ASSERTION_REPORT', argv=[str(child), mode])
        check('TIMEOUT', 'TIMEOUT', argv=[str(child), 'timeout'], timeout_seconds=0.3)
        started = time.monotonic()
        receipt, _ = check('ORPHAN_PIPE', 'TIMEOUT', argv=[str(child), 'orphan'], timeout_seconds=0.3)
        assert time.monotonic() - started < 3.5, 'timeout blocked on inherited pipe'
        assert receipt.get('timeout_cleanup_unconfirmed') is True
        # The synthetic descendant is bounded to four seconds; let it finish before fixture teardown.
        time.sleep(max(0, 4.2 - (time.monotonic() - started)))
        locked['tools']['python']['sha256'] = '0' * 64
        (root / 'execution/toolchains/locked.json').write_text(json.dumps(locked), encoding='utf-8')
        check('TOOLCHAIN_HASH', 'TOOLCHAIN_CHANGED')
        try:
            dispatch.within(root, '../outside')
            raise AssertionError('Path traversal accepted')
        except ValueError:
            ids.append('W02-DISPATCH-PATH_BOUNDARY')
    # ---- v2.4 versioned registry checks (W02-02) ----
    v24 = []
    def V(label, ok, detail=''):
        assert ok, ('V24-' + label, detail)
        v24.append('W02-V24-' + label)
    r_unknown, _ = dispatch.execute('no.such.key', spec='v2.4')
    V('UNKNOWN_KEY_NONZERO', r_unknown['status'] == 'NOT_IMPLEMENTED' and r_unknown['exit_code'] != 0 and r_unknown['registry_spec'] == 'v2.4', r_unknown['status'])
    r_unbound, _ = dispatch.execute('fork.build_worker', spec='v2.4')
    V('UNBOUND_NONZERO', r_unbound['status'] == 'NOT_IMPLEMENTED' and r_unbound['exit_code'] != 0, r_unbound['status'])
    r_bound, _ = dispatch.execute('package.validate_v24', spec='v2.4')
    V('BOUND_REAL_VALIDATE', r_bound['status'] == 'PASS' and len(r_bound['assertion_ids']) > 10, (r_bound['status'], len(r_bound['assertion_ids'])))
    r_oldkey_v24, _ = dispatch.execute('package.validate', spec='v2.4')
    r_newkey_v20, _ = dispatch.execute('package.validate_v24', spec='v2.0')
    V('VERSION_ISOLATION', r_oldkey_v24['status'] == 'NOT_IMPLEMENTED' and r_newkey_v20['status'] == 'NOT_IMPLEMENTED',
      (r_oldkey_v24['status'], r_newkey_v20['status']))
    r_auto, _ = dispatch.execute('package.validate_v24')
    V('AUTO_POINTER_V24', r_auto['status'] == 'PASS' and r_auto['registry_spec'] == 'v2.4', (r_auto['status'], r_auto.get('registry_spec')))
    r_sel, _ = dispatch.execute('package.validate_v24', {'check_id': 'other.check'}, spec='v2.4')
    V('SELECTOR_MISMATCH_FAILS', r_sel['status'] == 'NOT_IMPLEMENTED', r_sel['status'])
    mp = json.loads((ROOT / 'execution/v2.4/client_mapping.json').read_text(encoding='utf-8'))
    V('MAPPING_23_14_OWNED', len(mp['method_map']) == 23 and len(mp['event_map']) == 14
      and all(m.get('owner_card') for m in mp['method_map']) and all(e.get('owner_card') for e in mp['event_map']),
      (len(mp['method_map']), len(mp['event_map'])))
    reg24 = json.loads((ROOT / 'execution/v2.4/commands.json').read_text(encoding='utf-8'))
    V('REGISTRY_INVARIANTS', all(e['state'] in ('BOUND', 'UNBOUND') and isinstance(e['argv'], list)
      and e['timeout_seconds'] > 0 and e['owner_card'] for e in reg24['commands'].values())
      and sum(1 for e in reg24['commands'].values() if e['state'] == 'UNBOUND') >= 7, len(reg24['commands']))
    old_sha = hashlib.sha256((ROOT / 'execution/commands.json').read_bytes()).hexdigest()
    V('OLD_REGISTRY_PROTECTED', old_sha == '4239a0e6551c24915c12fb1e707738467d9d62d148c2e48560d5cdfa127b7961', old_sha[:12])
    ids.extend(v24)
    print(json.dumps(dict(status='PASS', assertions=len(ids), assertion_ids=sorted(set(ids)),
                          scope='DEVELOPMENT_ONLY', live_credentials_used=False,
                          registry_specs_tested=['v2.0-fixture', 'v2.4-real'])))


if __name__ == '__main__':
    main()
