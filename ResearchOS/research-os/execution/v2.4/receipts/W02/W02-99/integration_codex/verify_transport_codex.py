"""Observe the bridge's exact subprocess transport without executing old builds."""
from pathlib import Path
import contextlib
import hashlib
import importlib.util
import io
import json
import unittest.mock as mock

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
path = HERE.parent / 'dispatch_parent.py'
spec = importlib.util.spec_from_file_location('w02_bridge_transport_review', path)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)
baseline = json.loads((HERE / 'binding_baseline_codex.json').read_bytes())
legacy = baseline['original_legacy_build_entry']
cases = [
    ('omitted-task-empty-check', {}, 'v24'),
    ('explicit-W02-empty-check', {'RESEARCHOS_TASK_ID': 'W02'}, 'v24'),
    ('existing-W02-03', {'RESEARCHOS_TASK_ID': 'W02', 'RESEARCHOS_CHECK_ID': 'W02-03'}, 'v24'),
    ('legacy-valid', {'RESEARCHOS_TASK_ID': 'W03', 'RESEARCHOS_CHECK_ID': 'W03-G01'}, 'legacy'),
    ('legacy-mismatched-handler-refusal-retained', {'RESEARCHOS_TASK_ID': 'W03', 'RESEARCHOS_CHECK_ID': 'W04-G01'}, 'legacy'),
    ('parent', {'RESEARCHOS_TASK_ID': 'W02', 'RESEARCHOS_CHECK_ID': 'W02-G01'}, 'parent'),
    ('case-rejected', {'RESEARCHOS_CASE_ID': 'A03'}, 'reject'),
    ('unknown-task-rejected', {'RESEARCHOS_TASK_ID': 'W99'}, 'reject'),
]
rows = []
for label, selectors, kind in cases:
    environment = {'PYTHONUTF8': '1', 'GOTOOLCHAIN': 'local', 'GOENV': 'off',
        'ELECTRON_OVERRIDE_DIST_PATH': 'synthetic-electron-location',
        'RESEARCHOS_GO': 'synthetic-go', 'RESEARCHOS_NODE': 'synthetic-node',
        'RESEARCHOS_NPM_CLI': 'synthetic-npm', **selectors}
    calls = []
    def intercepted(argv, **kwargs):
        calls.append({'argv': argv, **kwargs})
        print('synthetic-child-byte-stream')
        return 27
    stream = io.StringIO()
    with mock.patch.dict(bridge.os.environ, environment, clear=True), \
            mock.patch.object(bridge.subprocess, 'call', side_effect=intercepted), \
            contextlib.redirect_stdout(stream):
        code = bridge.main()
    if kind == 'reject':
        report = json.loads(stream.getvalue())
        assert code == 3 and calls == [] and report['status'] == 'NOT_IMPLEMENTED'
        assert report['assertion_ids'] == [] and report['assertions'] == 0
    else:
        assert code == 27 and stream.getvalue() == 'synthetic-child-byte-stream\n'
        assert len(calls) == 1
        call = calls[0]
        expected_environment = dict(environment)
        if kind == 'legacy':
            expected_environment.pop('ELECTRON_OVERRIDE_DIST_PATH')
            expected_environment.update(legacy['fixed_env'])
            expected_args = legacy['argv']
        elif kind == 'v24':
            expected_args = baseline['original_v24_build_entry']['argv']
        else:
            expected_args = ['-B', str(HERE.parent / 'parent_driver.py'), 'W02-G01']
        assert call['argv'] == [bridge.sys.executable, *expected_args]
        assert call['cwd'] == ROOT and call['shell'] is False
        assert call['env'] == expected_environment
    rows.append({'id': label, 'ok': True, 'kind': kind, 'observed_return': code,
                 'subprocess_intercepted': True, 'old_build_executed': False})
result = {'status': 'PASS_INSTRUMENTED_TRANSPORT', 'checks': rows,
    'bridge_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
    'scope': 'Intercepted subprocess API verifies argv/cwd/environment/streams/exit. '
             'No claim of new historical handler/product execution.',
    'new_product_tests': 0, 'formal_case_count_delta': 0}
(HERE / 'transport_verification_codex.json').write_text(
    json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': result['status'], 'checks': len(rows)}))
