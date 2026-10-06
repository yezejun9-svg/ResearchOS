"""Integrate the independently requested narrow W02 AST/reporting repair."""
from pathlib import Path
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
REV = '6f858d7bb78aaed95878cf89bf2f7792560e872e'
PREFIX = 'execution/v2.4/receipts/W02/W02-99/'

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

changed = subprocess.check_output(['git', 'diff-tree', '--no-commit-id', '--name-status', '-r', REV],
    cwd=ROOT, text=True).splitlines()
rows = [row.split('\t') for row in changed]
assert rows and all(len(row) == 2 and row[0] in ('A', 'M') and row[1].startswith(PREFIX) for row in rows)
assert {row[1] for row in rows if row[0] == 'M'} == {PREFIX + 'evidence_reuse.py', PREFIX + 'parent_driver.py'}
assert not any(row[1].startswith(PREFIX + 'integration_codex/') or row[1].startswith(PREFIX + 'independent-review-codex/') for row in rows)
tracked = subprocess.check_output(['git', 'ls-files', '--', PREFIX], cwd=ROOT, text=True).splitlines()
allowed = {PREFIX + 'evidence_reuse.py', PREFIX + 'parent_driver.py'}
old = {name: sha(ROOT / name) for name in tracked if name not in allowed}
protected = ['execution/v2.4/commands.json', 'execution/commands.json',
    'execution/v2.4/path_ownership.json', 'execution/path_ownership.json',
    'execution/v2.4/checkpoint.json', 'execution/v2.4/step_state.json',
    'apps/cli/build_check.py', 'ops/ci/build.py', 'execution/command_dispatcher/dispatch.py']
before = {name: sha(ROOT / name) for name in protected}
result = subprocess.run(['git', 'cherry-pick', REV], cwd=ROOT, capture_output=True)
(HERE / 'review_fix_cherry_pick.stdout.txt').write_bytes(result.stdout)
(HERE / 'review_fix_cherry_pick.stderr.txt').write_bytes(result.stderr)
assert result.returncode == 0, result.stderr.decode('utf-8', 'replace')
assert before == {name: sha(ROOT / name) for name in protected}
assert old == {name: sha(ROOT / name) for name in old}
expected = {'evidence_reuse.py': 'f6eb90db0a2bf43ffdba2852337eaaa7b6e9841caab9bebb07f3886cb6142918',
    'dispatch_parent_exact.py': 'c64b2d2bb83e6106f49cb526eb57e0e164ba6db496bc52044fc652dc4843ca0a',
    'parent_driver.py': '9a488ac4404d1be623fafcacc30a7ecaa72b3f193f8cf6924878b0b08da9779e'}
assert all(sha(ROOT / PREFIX / name) == value for name, value in expected.items())
record = {'status': 'PASS_NARROW_REVIEW_FIX_INTEGRATION', 'worker_commit': REV,
    'main_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
    'owned_files': len(rows), 'old_files_byte_preserved': len(old),
    'protected_hashes_unchanged': before, 'source_sha256': expected,
    'new_product_tests': 0, 'formal_case_count_delta': 0, 'card_accepted': False}
(HERE / 'review_fix_source_integration_codex.json').write_text(
    json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': record['status'], 'main_commit': record['main_commit'],
                  'owned_files': len(rows), 'old_files_byte_preserved': len(old)}))
