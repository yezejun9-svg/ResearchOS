import hashlib
import json
from pathlib import Path

ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
REPLAY = ROOT / 'execution/v2.4/receipts/W05/W05-99/provider_g2_independent_replay_codex/3ed3a3da52c3471d9ddc524897100842'


def ref(path):
    path = Path(path).resolve()
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': h.hexdigest(), 'bytes': path.stat().st_size}


def save(name, value):
    with (OUT / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
    return ref(OUT / name)


outer = json.loads((OUT / 'invocation.json').read_bytes())
assert outer['actual_exit'] == 0 and outer['wrapper_error'] is None
assert json.loads((REPLAY / 'prepare/completed.json').read_bytes())['status'] == 'COMPLETED_NOT_ACCEPTED'
prepared = json.loads((REPLAY / 'prepared.json').read_bytes())
assert prepared['status'] == 'COMPILED_NOT_EXECUTED' and prepared['source_commit'] == '8d0921b7c42ecd40300c58192d54af1064947aed'
assert prepared['runner']['sha256'] == 'e687bd35560d4c34b4e939609b617a5d4770b4a45d51c3b132fca60a4bfa39f5'
exe = Path(prepared['exe']['path'])
assert ref(exe)['sha256'] == prepared['exe']['sha256'] and exe.stat().st_size == prepared['exe']['bytes']
processes = sorted((REPLAY / 'prepare').glob('process-*/invocation.json'))
assert len(processes) == 9
for path in processes:
    invocation = json.loads(path.read_bytes())
    result = invocation['result']
    assert invocation['actual_exit'] == result['actual_exit'] == 0 and result['error'] is None and result['timed_out'] is False
    cleanup = result['job_cleanup']
    assert result['resumed'] is True and all(cleanup[name] is True for name in ['kill_on_job_close_configured', 'assigned_before_resume', 'primary_exit_confirmed', 'job_idle_confirmed', 'handles_closed']) and cleanup['errors'] == []
audit = save('preparation-audit.json', {'status': 'ACTUAL_NONAUTHOR_PREPARATION_COMPILED_NO_CASES',
    'candidate': prepared['source_commit'], 'outer_ref': ref(OUT / 'invocation.json'),
    'prepared_ref': ref(REPLAY / 'prepared.json'), 'exe_ref': ref(exe), 'inputs': len(prepared['inputs']),
    'generated_count': prepared['generated_count'], 'archive_count': prepared['archive_count'],
    'all9_owned_process_native_exits': 0, 'all9_full_owned_job_cleanup_confirmed': True,
    'resource_baseline_checks': [ref(REPLAY / 'prepare' / name) for name in ['resources.before.json', 'resources.after-export-and-graph.json', 'resources.after-build.json']],
    'before_after_build_input_refs': [ref(REPLAY / 'prepare' / name) for name in ['inputs.before-build.json', 'inputs.after-build.json']],
    'actual_all_WORK_ref': ref(REPLAY / 'prepare/actual_WORK.allfiles.json'),
    'cases_run': 0, 'all29': 'NOT_RUN_REQUIRES_ACTUAL_PREPARED_SHA_NEW_GRANT',
    'SDK_MODEL_external_paid_calls': 0, 'source_acceptance': False, 'Main_integration_authorized': False,
    'formal_increment': 0, 'automatic_retry': False})
entries = [ref(p) for root in [OUT, REPLAY] for p in sorted(root.rglob('*')) if p.is_file() and p.name != 'manifest.json']
manifest = save('manifest.json', {'entries': entries, 'count': len(entries), 'self_excluded': True,
    'prepare_only_no_product_acceptance': True})
print(json.dumps({'audit': audit, 'manifest': manifest, 'prepared': ref(REPLAY / 'prepared.json'),
    'exe': ref(exe), 'inputs': len(prepared['inputs']), 'listed': len(entries)}, ensure_ascii=True))
