"""Amend only W02's bound argv to a frozen exact-parent reporting wrapper."""
from pathlib import Path
import copy
import datetime as dt
import hashlib
import json
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
PREFIX = 'execution/v2.4/receipts/W02/W02-99/'

def load(path): return json.loads(path.read_bytes())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2); stream.write('\n')

assert len(sys.argv) == 2
revision = sys.argv[1]
assert len(revision) == 40 and all(c in '0123456789abcdef' for c in revision)
baseline = load(HERE / 'binding_baseline_codex.json')
previous = load(HERE / 'binding_codex.json')
path = ROOT / 'execution/v2.4/commands.json'
registry = load(path)
assert registry['revision'] == 35 and sha(path) == previous['registry_sha256']
before = copy.deepcopy(registry)
for name in ('dispatch_parent_exact.py', 'evidence_reuse.py', 'parent_driver.py'):
    frozen = subprocess.check_output(['git', 'show', revision + ':' + PREFIX + name], cwd=ROOT)
    assert (ROOT / PREFIX / name).read_bytes() == frozen, name
assert sha(ROOT / PREFIX / 'dispatch_parent.py') == '4d8e4f843cd7cea15e21eb250c732a5553a33cb8b23a54cc109d21335ee1681b'
for rel, expected in baseline['protected_source_hashes'].items(): assert sha(ROOT / rel) == expected, rel
assert sha(ROOT / 'execution/commands.json') == baseline['legacy_registry_sha256']
entry = registry['commands']['build.check']
assert entry['argv'] == ['-B', PREFIX + 'dispatch_parent.py']
entry['argv'] = ['-B', PREFIX + 'dispatch_parent_exact.py']
entry['expected_artifacts'].append(PREFIX + 'dispatch_parent_exact.py')
entry['note'] += (' Exact-parent wrapper now reports only the frozen W02-G01/G02/G03 ID '
    'after strict child receipt, manifest, exit and internal assertion validation. '
    'All original internal IDs and raw evidence remain separately referenced; legacy branches use the unchanged bridge.')
registry['revision'] = 36
assert {k: v for k, v in registry['commands'].items() if k != 'build.check'} == {
    k: v for k, v in baseline['v24_decoded_commands'].items() if k != 'build.check'}
for name in ('executable_tool', 'cwd', 'platforms', 'required_env', 'allowed_env',
             'fixed_env', 'tool_env', 'timeout_seconds', 'assertion_field', 'state', 'selectors'):
    assert entry[name] == before['commands']['build.check'][name], name
assert {k: v for k, v in registry.items() if k not in ('commands', 'revision')} == {
    k: v for k, v in before.items() if k not in ('commands', 'revision')}
path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
save(HERE / 'exact_binding_codex.json', {
    'schema': 'researchos.exact-command-binding.v1', 'actor': 'codex:/root',
    'registered_at': dt.datetime.now(dt.timezone.utc).isoformat(),
    'source_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
    'worker_repair_commit': revision, 'registry_revision': 36, 'registry_sha256': sha(path),
    'previous_binding_sha256': sha(HERE / 'binding_codex.json'),
    'previous_registry_sha256': previous['registry_sha256'], 'new_entry': entry,
    'other_decoded_entries_preserved': 30,
    'legacy_registry_sha256_before_after': baseline['legacy_registry_sha256'],
    'protected_source_hashes_unchanged': baseline['protected_source_hashes'],
    'wrapper_sha256': sha(ROOT / PREFIX / 'dispatch_parent_exact.py'),
    'reuse_helper_sha256': sha(ROOT / PREFIX / 'evidence_reuse.py'),
    'parent_driver_sha256': sha(ROOT / PREFIX / 'parent_driver.py'),
    'formal_case_count_delta': 0, 'card_accepted': False,
})
print(json.dumps({'status': 'PASS_EXACT_PARENT_BINDING_ONLY', 'revision': 36,
                  'other_entries_preserved': 30}))
