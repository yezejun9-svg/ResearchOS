"""Integrate the frozen receipt-only W02 reuse patch without shared changes."""
from pathlib import Path
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
REV = 'f327ee10844810d8ada7a7b83aae05412d757c4a'
PREFIX = 'execution/v2.4/receipts/W02/W02-99/'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

names = subprocess.check_output(['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', REV],
                                cwd=ROOT, text=True).splitlines()
assert len(names) == 125 and all(name.startswith(PREFIX) for name in names)
assert not any(name.startswith(PREFIX + 'integration_codex/') or
               name.startswith(PREFIX + 'independent-review-codex/') for name in names)
old_files = subprocess.check_output(['git', 'diff-tree', '--no-commit-id', '--name-only', '-r',
    'b2f8f0d60ca7cd5728c9cab47f22dd9eda602df6'], cwd=ROOT, text=True).splitlines()
old_hashes = {name: sha(ROOT / name) for name in old_files if name != PREFIX + 'parent_driver.py'}
protected = ['execution/v2.4/commands.json', 'execution/commands.json',
    'execution/v2.4/path_ownership.json', 'execution/path_ownership.json',
    'execution/v2.4/checkpoint.json', 'execution/v2.4/step_state.json',
    'apps/cli/build_check.py', 'ops/ci/build.py', 'execution/command_dispatcher/dispatch.py']
before = {name: sha(ROOT / name) for name in protected}
result = subprocess.run(['git', 'cherry-pick', REV], cwd=ROOT, capture_output=True)
(HERE / 'reuse_cherry_pick.stdout.txt').write_bytes(result.stdout)
(HERE / 'reuse_cherry_pick.stderr.txt').write_bytes(result.stderr)
assert result.returncode == 0, result.stderr.decode('utf-8', 'replace')
assert before == {name: sha(ROOT / name) for name in protected}
assert old_hashes == {name: sha(ROOT / name) for name in old_hashes}
assert sha(ROOT / (PREFIX + 'parent_driver.py')) == '6330347595da5f3cce102fc3cbb62f293f0b037f31a78d30714dbd24bc3360bb'
assert sha(ROOT / (PREFIX + 'evidence_reuse.py')) == '3e9e060609e34b190807f06d14e5cf984ddcef855454caafa94c93a7eede78b5'
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
record = {'status': 'PASS_REUSE_SOURCE_INTEGRATION', 'worker_commit': REV,
    'main_commit': head, 'owned_files': len(names), 'old_files_byte_preserved': len(old_hashes),
    'protected_hashes_unchanged': before, 'product_source_changes': 0,
    'registry_changes': 0, 'card_accepted': False}
(HERE / 'reuse_source_integration_codex.json').write_text(
    json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': record['status'], 'main_commit': head,
                  'old_files_byte_preserved': len(old_hashes)}))
