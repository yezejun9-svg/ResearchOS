"""Execute the three registered W03 selectors with read-only atom revalidation."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import subprocess
import sys
import uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
CARD = HERE.parent
EXECUTOR = CARD / 'executor_codex'

def load(path):
    return json.loads(path.read_bytes())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save_new(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

binding = load(HERE / 'parent_command_binding_codex.json')
registry_path = ROOT / 'execution/v2.4/commands.json'
assert load(registry_path)['revision'] == 37 and sha(registry_path) == binding['registry_sha256']
for name, digest in binding['bridge_input_hashes'].items():
    assert sha(EXECUTOR / name) == digest, name
assert not (HERE / 'exact_parent_dispatch_results.json').exists()
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ-') + uuid.uuid4().hex[:12]
output = HERE / ('exact-parent-root-' + stamp)
output.mkdir(exist_ok=False)
rows = []
for gate, key, mode in [('W03-G01', 'contracts.validate', 'DEVELOPMENT'),
                        ('W03-G02', 'test.domain', 'FIXTURE'),
                        ('W03-G03', 'contracts.validate', 'FIXTURE')]:
    argv = [sys.executable, '-B', '-X', 'utf8', str(ROOT / 'execution/command_dispatcher/dispatch.py'),
        key, '--task-id', 'W03', '--check-id', gate, '--spec', 'v2.4']
    index_path = EXECUTOR / ('current_' + gate + '.json')
    before_index = index_path.read_bytes()
    result = subprocess.run(argv, cwd=ROOT, capture_output=True, timeout=960)
    (output / (gate + '.stdout.txt')).write_bytes(result.stdout)
    (output / (gate + '.stderr.txt')).write_bytes(result.stderr)
    save_new(output / (gate + '.launch.json'), {'argv': argv, 'exit_code': result.returncode,
        'gate': gate, 'mode': mode, 'command_key': key, 'source_head': head})
    assert result.returncode == 0, gate + ': original actual failure retained, no unchanged retry'
    emitted = json.loads(result.stdout)
    original = Path(emitted['receipt'])
    receipt = load(original)
    assert receipt['code_revision'] == head and receipt['command_key'] == key
    assert receipt['selectors'] == {'task_id': 'W03', 'check_id': gate, 'case_id': ''}
    assert receipt['registered_command_revision'] == sha(registry_path)
    assert receipt['status'] == 'PASS' and receipt['child_exit_code'] == 0
    assert receipt['assertion_ids'] == [gate]
    stdout_path = ROOT / receipt['stdout']['path']
    stderr_path = ROOT / receipt['stderr']['path']
    assert sha(stdout_path) == receipt['stdout']['sha256'] and sha(stderr_path) == receipt['stderr']['sha256']
    report = load(stdout_path)
    assert report['status'] == 'PASS' and report['task_id'] == 'W03' and report['check_id'] == gate
    assert report['assertion_ids'] == [gate] and type(report['assertions']) is int and report['assertions'] == 1
    assert report['mode'] == mode and report['formal_product_acceptance'] == 'NOT_RUN'
    assert report['owned_acceptance_ids'] == [] and report['errors'] == []
    assert report['associated_cases'] == {'A03': 'NOT_RUN', 'C04': 'NOT_RUN', 'C19': 'NOT_RUN'}
    assert report['evidence_index'] == index_path.relative_to(ROOT).as_posix()
    assert report['evidence_index_sha256'] == sha(index_path)
    assert index_path.read_bytes() == before_index, 'registered dispatch cannot mutate the archived index'
    atoms = load(index_path)['atoms']
    assert set(atoms) == ({'go'} if gate == 'W03-G02' else {'go', 'probe'})
    assert set(report['atomic_results']) == set(atoms)
    atom_records = {}
    for kind, atom in atoms.items():
        atom_path = (EXECUTOR / atom['path']).resolve()
        assert atom_path.is_relative_to((EXECUTOR / 'runs').resolve())
        assert sha(atom_path / 'receipt.json') == atom['receipt_sha256']
        assert sha(atom_path / 'manifest.json') == atom['manifest_sha256']
        atom_receipt = load(atom_path / 'receipt.json')
        assert atom_receipt['status'] == 'PASS' and atom_receipt['exit_code'] == 0
        assert atom_receipt['gate'] == gate and atom_receipt['mode'] == mode and atom_receipt['kind'] == kind
        assert atom_receipt['parsed'] == report['atomic_results'][kind]
        assert sha(atom_path / 'stdout.txt') == atom_receipt['stdout_sha256']
        assert sha(atom_path / 'stderr.txt') == atom_receipt['stderr_sha256']
        atom_records[kind] = {'path': atom_path.relative_to(ROOT).as_posix(),
            'receipt_sha256': atom['receipt_sha256'], 'manifest_sha256': atom['manifest_sha256'],
            'parsed': atom_receipt['parsed']}
    mirror = CARD / 'registered-dispatch-exact' / receipt['invocation_id']
    mirror.mkdir(parents=True, exist_ok=False)
    for source, name in [(original, 'receipt.json'), (stdout_path, 'stdout.txt'), (stderr_path, 'stderr.txt')]:
        with (mirror / name).open('xb') as stream:
            stream.write(source.read_bytes())
        assert source.read_bytes() == (mirror / name).read_bytes()
    rows.append({'gate': gate, 'mode': mode, 'command_key': key, 'argv': argv, 'exit_code': 0,
        'dispatcher': emitted, 'dispatcher_receipt_sha256': sha(original),
        'mirror_path': mirror.relative_to(ROOT).as_posix(), 'exact_parent_assertion_ids': [gate],
        'index_path': index_path.relative_to(ROOT).as_posix(), 'index_sha256': sha(index_path), 'atoms': atom_records})
    print(json.dumps({'gate': gate, 'status': 'PASS', 'invocation_id': receipt['invocation_id'],
        'exact_parent_assertions': 1, 'internal_atom_kinds': sorted(atoms), 'new_product_executions': 0}), flush=True)
save_new(HERE / 'exact_parent_dispatch_results.json', {
    'schema': 'researchos.actual-exact-parent-dispatch.v1', 'actor': 'codex:/root',
    'recorded_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'source_head': head,
    'registry_revision': 37, 'registry_sha256': sha(registry_path),
    'root_raw_directory': output.relative_to(ROOT).as_posix(), 'actual_registered_selectors': rows,
    'interpretation': 'Three actual registered dispatcher calls verify current immutable atom sources, raw outputs and exact singleton parent IDs. Internal Go tests, contract fixtures and new probe groups remain separate counts.',
    'new_product_executions': 0, 'new_provider_calls': 0, 'new_service_operations': 0,
    'new_gui_operations': 0, 'owned_acceptance_ids': [], 'formal_case_count_delta': 0,
    'parent_accepted': False,
})
