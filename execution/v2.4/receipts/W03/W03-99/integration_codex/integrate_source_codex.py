"""Guard and integrate only the uniquely owned W03 implementation commit."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
CANDIDATE = ROOT / '.local/worktrees/codex-w0199'
EXECUTOR_REL = 'execution/v2.4/receipts/W03/W03-99/executor_codex/'

def load(path):
    return json.loads(path.read_bytes())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def git(*args, cwd=ROOT):
    return subprocess.check_output(['git', *args], cwd=cwd, text=True).strip()

assert len(sys.argv) == 2, 'One exact implementation commit is required.'
revision = sys.argv[1]
assert git('rev-parse', revision) == revision
assert git('rev-parse', 'HEAD', cwd=CANDIDATE) == revision
assert git('branch', '--show-current', cwd=CANDIDATE) == 'work/codex-w0399'
assert not git('status', '--porcelain', '--untracked-files=no', cwd=CANDIDATE)
scope_path = HERE / 'source_repair_scope_codex.json'
scope = load(scope_path)
allowed = set(scope['existing_allowed_paths']) | set(scope['new_allowed_worker_paths'])
files = git('diff-tree', '--no-commit-id', '--name-only', '-r', revision).splitlines()
assert files and all(name in allowed or name.startswith(EXECUTOR_REL) for name in files)
assert scope['root_owned_projection_path'] not in files
assert any(name in allowed for name in files), 'Implementation commit must contain its concrete registered production repair.'
assert not git('diff', '--name-only', '--', *sorted(allowed))
assert not git('diff', '--cached', '--name-only')
for name, digest in scope['existing_allowed_paths'].items():
    assert sha(ROOT / name) == digest, name
for name in scope['new_allowed_worker_paths']:
    assert not (ROOT / name).exists(), name
projection = load(HERE / 'persistence_projection_generation_codex.json')['projection']
assert sha(ROOT / projection['path']) == projection['sha256']
assert sha(CANDIDATE / projection['path']) == projection['sha256']
baseline = load(HERE / 'binding_baseline_codex.json')
protected_names = list(dict.fromkeys(list(baseline['protected_source_hashes']) +
    ['execution/v2.4/commands.json', 'execution/commands.json', 'execution/v2.4/checkpoint.json',
     'execution/v2.4/path_ownership.json', 'execution/v2.4/step_state.json',
     scope['root_owned_projection_path'], 'internal/domain/contracts/evaluation-v24.schema.json',
     'internal/domain/contracts_evaluation_v24.go']))
protected_before = {name: sha(ROOT / name) for name in protected_names}
assert not (HERE / 'source_integration_codex.json').exists()
for gate in ['W03-G01', 'W03-G02', 'W03-G03']:
    report = load(CANDIDATE / EXECUTOR_REL / ('candidate_' + gate + '.json'))
    assert report['status'] == 'PASS' and report['assertion_ids'] == [gate]
    assert report['formal_product_acceptance'] == 'NOT_RUN' and report['owned_acceptance_ids'] == []
subprocess.run(['git', 'cherry-pick', revision], cwd=ROOT, check=True)
assert all(sha(ROOT / name) == digest for name, digest in protected_before.items())
input_hashes = {name: sha(ROOT / name) for name in files if (ROOT / name).is_file()}
assert all((ROOT / name).read_bytes() == (CANDIDATE / name).read_bytes() for name in input_hashes)
atoms = []
for gate in ['W03-G01', 'W03-G02', 'W03-G03']:
    index = load(ROOT / EXECUTOR_REL / ('current_' + gate + '.json'))
    for kind, reference in index['atoms'].items():
        directory = ROOT / EXECUTOR_REL / reference['path']
        assert sha(directory / 'receipt.json') == reference['receipt_sha256']
        assert sha(directory / 'manifest.json') == reference['manifest_sha256']
        receipt = load(directory / 'receipt.json')
        assert receipt['status'] == 'PASS' and type(receipt['exit_code']) is int and receipt['exit_code'] == 0
        manifest = load(directory / 'manifest.json')
        for name, digest in manifest['source_hashes'].items():
            if name.startswith('executor/'):
                target = ROOT / EXECUTOR_REL / name[len('executor/'):]
            elif name == 'toolchain/locked.json':
                target = ROOT / 'execution/toolchains/locked.json'
            elif name == 'toolchain/go.exe':
                target = Path(load(ROOT / 'execution/toolchains/locked.json')['tools']['go']['path'])
            elif name.startswith('frozen/v2.4/'):
                target = ROOT / '.local/worktrees/v24-continuation/spec/v2.4/contracts' / name[len('frozen/v2.4/'):]
            else:
                target = ROOT / name
            assert sha(target) == digest, 'Main/candidate current input mismatch: ' + name
        atoms.append({'gate': gate, 'kind': kind, 'receipt_sha256': reference['receipt_sha256'],
            'manifest_sha256': reference['manifest_sha256'], 'current_main_source_vector_equal': True})
record = {'schema': 'researchos.scoped-source-integration.v1', 'actor': 'codex:/root',
    'status': 'PASS_SCOPED_SOURCE_INTEGRATION', 'worker_commit': revision, 'main_commit': git('rev-parse', 'HEAD'),
    'production_repair_scope_sha256': sha(scope_path), 'allowed_integrated_files': files,
    'integrated_input_hashes': input_hashes, 'protected_hashes_unchanged': protected_before,
    'current_atoms': atoms, 'new_product_executions': 0, 'formal_case_count_delta': 0, 'parent_accepted': False}
with (HERE / 'source_integration_codex.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps({'status': record['status'], 'integrated_files': len(files),
    'current_atoms': len(atoms), 'new_product_executions': 0}))
