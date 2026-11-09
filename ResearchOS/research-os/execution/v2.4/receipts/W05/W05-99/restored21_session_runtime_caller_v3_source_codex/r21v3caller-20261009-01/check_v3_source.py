"""Source-only lexical and injected-failure controls; never execute either Root caller."""
import ast
import copy
import hashlib
import json
import symtable
import sys
import types
from pathlib import Path

sys.dont_write_bytecode = True
N = Path(__file__).resolve().parent
C = json.loads((N / 'contract.json').read_bytes())


def pin(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def exact(ref):
    actual = pin(ref['path'])
    assert actual['sha256'] == ref['sha256'] and ('bytes' not in ref or actual['bytes'] == ref['bytes'])
    return actual


def save(name, payload):
    path = N / name
    with path.open('xb') as stream:
        stream.write((json.dumps(payload, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    return pin(path)


def main_function(path):
    source = path.read_text(encoding='utf-8')
    tree = ast.parse(source, filename=str(path))
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
    guarded = next(node for node in main.body if isinstance(node, ast.Try) and node.body and
                   isinstance(node.body[0], ast.Expr) and
                   isinstance(node.body[0].value, ast.Call) and
                   isinstance(node.body[0].value.func, ast.Attribute) and
                   node.body[0].value.func.attr == 'acquire')
    return source, main, guarded


def probe(body, scope):
    unit = ast.Module(body=[ast.FunctionDef(name='probe', args=ast.arguments(posonlyargs=[], args=[], vararg=None,
        kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]), body=body, decorator_list=[])], type_ignores=[])
    ast.fix_missing_locations(unit)
    exec(compile(unit, '<source-only-memory-probe>', 'exec'), scope)
    try:
        scope['probe']()
    except BaseException as error:
        return type(error).__name__, repr(error)
    return None, None


class FakeGuard:
    def __init__(self, name, fail_acquire=False, fail_close=False):
        self.name, self.fail_acquire, self.fail_close = name, fail_acquire, fail_close
        self.calls = []

    def acquire(self, _):
        self.calls.append('acquire')
        if self.fail_acquire:
            raise OSError('IN_MEMORY_' + self.name + '_ACQUIRE_ERROR')

    def close(self):
        self.calls.append('close')
        if self.fail_close:
            raise OSError('IN_MEMORY_' + self.name + '_CLOSE_ERROR')
        return {'closed': True, 'errors': [], 'retained_handles_count': 0}


def main():
    assert len(sys.argv) == 1 and Path(sys.executable).resolve() == Path(C['python']['path']).resolve()
    input_names = ('v2_source_handoff', 'v2_source_manifest', 'v2_review_handoff', 'v2_review_manifest',
                   'exact_source_roster', 'source_guard', 'python')
    refs = [exact(C[name]) for name in input_names]
    refs.extend(pin(N / name) for name in ('contract.json', 'prepare_root_actual.py',
                'validate_root_actual.py', 'check_v3_source.py'))
    old_manifest = json.loads(Path(C['v2_source_manifest']['path']).read_bytes())
    review_manifest = json.loads(Path(C['v2_review_manifest']['path']).read_bytes())
    refs.extend(exact(item) for item in old_manifest['members'])
    refs.extend(exact(item) for item in review_manifest['members'])
    dedup = {}
    for ref in refs:
        key = ref['path'].casefold()
        assert key not in dedup or dedup[key] == ref
        dedup[key] = ref
    refs = list(dedup.values())
    guard_source = Path(C['source_guard']['path']).read_bytes()
    mod = types.ModuleType('v3_source_guard')
    mod.__file__ = C['source_guard']['path']
    sys.modules[mod.__name__] = mod
    exec(compile(guard_source, mod.__file__, 'exec'), mod.__dict__)
    guard = mod.SourceReadGuard(per_file_cap=256 * 1024 * 1024, total_cap=2 * 1024 * 1024 * 1024)
    guard.acquire(refs)
    checks = []

    def check(label, passed):
        checks.append({'name': label, 'passed': bool(passed)})
        assert passed, label

    try:
        vsource, vm, vt = main_function(N / 'validate_root_actual.py')
        psource, pm, pt = main_function(N / 'prepare_root_actual.py')
        check('both Root caller files parse', bool(vm and pm))
        review = json.loads(Path(C['v2_review_handoff']['path']).read_bytes())
        check('review identifies two P1 and one P2', review['status'] == 'REQUEST_CHANGES'
              and review['P1_findings'] == 2 and review['P2_findings'] == 1)
        check('v2 sealed and only v3 output paths', C['worktree'].endswith('r21v3caller-20261009-01')
              and 'v3-' in C['validation_output'] and 'v3-' in C['isolation_output'])
        check('new Root output directories absent', not Path(C['isolation_output']).exists()
              and not Path(C['validation_output']).exists())
        symbols = next(item for item in symtable.symtable(vsource, 'validator', 'exec').get_children()
                       if item.get_name() == 'main')
        check('module loader is global in validator main', symbols.lookup('module').is_global()
              and not symbols.lookup('module').is_local())
        loader_call = next(node for node in vm.body if isinstance(node, ast.Assign) and
                           any(isinstance(t, ast.Name) and t.id == 'gm' for t in node.targets))
        meta_assign = next(node for node in ast.walk(vm) if isinstance(node, ast.Assign) and
                           any(isinstance(t, ast.Name) and t.id == 'go_module_info' for t in node.targets))
        calls = []
        fake_path = types.SimpleNamespace(read_bytes=lambda: b'IN_MEMORY')
        kind, _ = probe([copy.deepcopy(loader_call), copy.deepcopy(meta_assign)], {
            'module': lambda *args: calls.append(args), 'gp': {'path': 'IN_MEMORY'},
            'Path': lambda _: fake_path, 'pkg': {'Module': None}})
        check('actual lexical loader and metadata assignments are reachable', kind is None and len(calls) == 1)
        closed_def = next(node for node in vm.body if isinstance(node, ast.FunctionDef) and node.name == 'closed')
        check('closed finalizer defined before guarded try', vm.body.index(closed_def) < vm.body.index(vt))
        check('reviewed 63 roster remains external exact ref', C['expected_composed_sources'] == 63
              and C['exact_source_roster']['path'].endswith('r21v2caller-20261009-02/exact-source-roster.json'))
        check('nine parents plus four leaves unchanged', C['expected_parents'] == 9
              and C['expected_unique_test_runs'] == 13)
        check('13 pass is partial with native open',
              'DEVELOPMENT_TESTS_13_ACTUAL_PASS_COMPONENT_PARTIAL_NATIVE_QUALIFICATION_OPEN' in vsource
              and "'native_qualification_accepted': False" in vsource)

        # Retain the exact extracted finalizer, except/finally and post-try tail.
        # Only guard acquisition and filesystem writers are memory adapters.
        vt_index = vm.body.index(vt)
        tail = copy.deepcopy(vm.body[vt_index + 1:])
        for failure in ('input', 'runtime'):
            input_guard = FakeGuard('input', fail_acquire=failure == 'input')
            runtime_guard = FakeGuard('runtime', fail_acquire=failure == 'runtime')
            saved = []
            def recorder(name, value):
                saved.append((name, value))
                return {'path': name}
            body = [copy.deepcopy(closed_def)]
            source = 'phase_error=None\nguard_cleanup_refs=[]\nguard_cleanup_errors=[]\ncleanup_attempts_ref=None\nall_guards_closed=True\njobs=[]\ninvocations=[]\ndevelopment_tests_observed=False'
            body = ast.parse(source).body + body
            acquire = 'input_guard.acquire([])'
            if failure == 'runtime':
                acquire += '\nruntime_guard.acquire([])'
            test_try = copy.deepcopy(vt)
            test_try.body = ast.parse(acquire).body
            body += [test_try, *tail]
            scope = {'input_guard': input_guard, 'runtime_guard': runtime_guard,
                'binary_guard': None, 'compiler_guard': None, 'evidence_guard': None,
                'candidate_guard': None, 'save': recorder, 'json': json,
                'print': lambda *args, **kwargs: None,
                'before': {}, 'main_before': {}, 'sources': {}, 'binary': None,
                'formatted_ref': None, 'inventory_ref': None, 'overlay_ref': None,
                'parents': [], 'terminals': set(), 'started': set(), 'actions': {},
                'preparation_cleanup_ref': {'path': 'IN_MEMORY'},
                'actual_test_jsonl_primary_ref': None, 'typed_evidence_ref': None,
                'expected': [], 'C': {'component_scope': 'IN_MEMORY'}}
            kind, detail = probe(body, scope)
            final = next((value for name, value in saved if name == 'validation.closed.json'), None)
            check(failure + ' acquisition error produces failed closed receipt',
                  kind == 'RuntimeError' and 'IN_MEMORY_' + failure + '_ACQUIRE_ERROR' in detail
                  and final is not None and final['status'].startswith('FAILED_')
                  and 'IN_MEMORY_' + failure + '_ACQUIRE_ERROR' in final['error'])
            check(failure + ' acquisition closes acquired guards', input_guard.calls[-1] == 'close'
                  and (failure == 'input' or runtime_guard.calls[-1] == 'close'))

        for stage, script_try in (('prepare', pt), ('validate', vt)):
            first = FakeGuard('first', fail_close=True)
            second = FakeGuard('second')
            saved = []
            def fail_first_receipt(name, value):
                saved.append((name, value))
                if name == ('runtime-source-guard.cleanup.actual.json' if stage == 'prepare'
                            else 'binary-source-guard.cleanup.actual.json'):
                    raise OSError('IN_MEMORY_RECEIPT_WRITE_ERROR')
                return {'path': name}
            if stage == 'prepare':
                init = ast.parse('cleanup_refs=[]\ncleanup_errors=[]\ncleanup_ok=True\nattempts_ref=None\njobs=[]').body
                finalbody = copy.deepcopy(script_try.finalbody)
                post = copy.deepcopy(pm.body[pm.body.index(pt) + 1:pm.body.index(pt) + 2])
                scope = {'runtime_guard': first, 'guard': second, 'save': fail_first_receipt,
                         'json': json, 'print': lambda *args, **kwargs: None}
            else:
                init = ast.parse('guard_cleanup_refs=[]\nguard_cleanup_errors=[]\nall_guards_closed=True\ncleanup_attempts_ref=None\njobs=[]\nphase_error=None').body
                finalbody = copy.deepcopy(script_try.finalbody)
                post = copy.deepcopy(vm.body[vm.body.index(vt) + 1:])
                scope = {'binary_guard': first, 'compiler_guard': second,
                         'evidence_guard': None, 'candidate_guard': None,
                         'runtime_guard': None, 'input_guard': None,
                         'save': fail_first_receipt, 'json': json,
                         'print': lambda *args, **kwargs: None,
                         'invocations': [], 'before': {}, 'main_before': {},
                         'development_tests_observed': False, 'phase_error': None,
                         'sources': {}, 'binary': None, 'formatted_ref': None,
                         'inventory_ref': None, 'overlay_ref': None, 'parents': [],
                         'terminals': set(), 'started': set(), 'actions': {},
                         'preparation_cleanup_ref': {'path': 'IN_MEMORY'},
                         'actual_test_jsonl_primary_ref': None, 'typed_evidence_ref': None,
                         'expected': [], 'C': {'component_scope': 'IN_MEMORY'}}
                post = [copy.deepcopy(closed_def), *post]
            wrapper = ast.Try(body=[ast.Pass()], handlers=[], orelse=[], finalbody=finalbody)
            kind, _ = probe([*init, wrapper, *post], scope)
            attempts = next((value for name, value in saved if name.endswith('.cleanup.attempts.json')), None)
            check(stage + ' later guard close attempted after receipt error',
                  first.calls == ['close'] and second.calls == ['close'])
            check(stage + ' preserves close and persistence errors', attempts is not None
                  and {error['operation'] for error in attempts['errors']} == {'close', 'persist'})
            check(stage + ' never publishes success after receipt error',
                  kind in ('AssertionError', 'RuntimeError') and
                  not any(name in ('isolation.ready.json',) for name, _ in saved) and
                  not any(value.get('status', '').startswith('DEVELOPMENT_TESTS_')
                          for name, value in saved if name == 'validation.closed.json'))

        check('all exact inputs unchanged', all(pin(ref['path']) == ref for ref in refs))
        save('source-controls.json', {'schema': 'researchos.a21-v3-caller-source-controls.v1',
            'status': 'PASS_SOURCE_ONLY', 'checks': checks, 'count': len(checks),
            'input_refs': len(refs), 'actual_Root_Git_Go_SQL_native_CLI_model': False})
        print(json.dumps({'source_checks': len(checks), 'input_refs': len(refs)}), flush=True)
    finally:
        cleanup = guard.close()
        save('source-guard.cleanup.actual.json', cleanup)
        assert cleanup['closed'] and not cleanup['errors'] and cleanup['retained_handles_count'] == 0


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        print('SOURCE_PYTHON_EXIT=1', flush=True)
        raise
    print('SOURCE_PYTHON_EXIT=0', flush=True)
