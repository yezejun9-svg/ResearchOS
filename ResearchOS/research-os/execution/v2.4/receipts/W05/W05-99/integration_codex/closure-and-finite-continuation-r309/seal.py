import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent


def ref(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def save(name, value):
    with (OUT / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
    return ref(OUT / name)


prepared = json.loads((OUT / 'prepared_refs.v2.json').read_bytes())
paths = [ROOT / pin['path'] for pin in prepared['canonical_before']]
assert all(path.read_bytes() == (OUT / (path.stem + '.desired.json')).read_bytes() for path in paths[:2])
assert all(ref(path) == pin for path, pin in zip(paths[2:], prepared['canonical_before'][2:]))
cp, ow = [json.loads(path.read_bytes()) for path in paths[:2]]
old_cp = json.loads((OUT / 'checkpoint.original.json').read_bytes())
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [309, 137, 379]
assert cp['failure_counters'][:371] == old_cp['failure_counters']
assert cp['current_effective_formal_status'] == old_cp['current_effective_formal_status']
assert ow['card_path_bindings']['W05-99']['subtasks']['provider_g2_finite_exact2']['current_source_writer'] is None
git = json.loads((ROOT / 'execution/toolchains/locked.json').read_bytes())['tools']['git']['path']
assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == prepared['head']
assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == (OUT / 'git-status.original.raw').read_bytes()
assert subprocess.check_output([git, 'diff', '--cached', '--name-only'], cwd=ROOT) == b''
audit = save('postaudit.json', {'status': 'ACTUAL_CAS309_COMPLETE_NO_SOURCE_OR_FORMAL_ACCEPTANCE',
    'native_register_exit': json.loads((OUT / 'invocation.json').read_bytes())['actual_exit'],
    'canonical_refs': [ref(path) for path in paths], 'transition': [308, 136, 371, 309, 137, 379],
    'old371_failure_prefix_unchanged': True, 'step_state_commands_MainHEAD_old11D_unchanged': True,
    'G2_frozen_source_writer_released': True, 'new_CLI44_list14_grants_only': True,
    'all22_and42_effective_acceptances_required': True, 'formal_increment': 0, 'external_paid_MODEL': 0})
entries = [ref(path) for path in sorted(OUT.rglob('*')) if path.is_file() and path.name != 'manifest.json']
manifest = save('manifest.json', {'entries': entries, 'count': len(entries), 'self_excluded': True,
    'canonical_registered_scopes_only': True, 'new_product_execution_results': 'Separate readonly replay namespaces, not included here'})
print(json.dumps({'postaudit': audit, 'manifest': manifest, 'listed': len(entries)}, ensure_ascii=True))
