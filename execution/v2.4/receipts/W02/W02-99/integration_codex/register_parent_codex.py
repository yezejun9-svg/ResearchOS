"""Bind only W02's build entry; preserve its original transport and all other entries."""
from pathlib import Path
import copy
import datetime as dt
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
V24 = ROOT / 'execution/v2.4'

def load(path):
    return json.loads(path.read_bytes())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

baseline = load(HERE / 'binding_baseline_codex.json')
registry_path = V24 / 'commands.json'
registry = load(registry_path)
before = copy.deepcopy(registry)
assert registry['revision'] == baseline['commands_revision'] == 34
assert registry['commands'] == baseline['v24_decoded_commands']
assert sha(ROOT / 'execution/commands.json') == baseline['legacy_registry_sha256']
for rel, expected in baseline['protected_source_hashes'].items():
    assert sha(ROOT / rel) == expected, rel
bridge = HERE.parent / 'dispatch_parent.py'
assert sha(bridge) == '4d8e4f843cd7cea15e21eb250c732a5553a33cb8b23a54cc109d21335ee1681b'
assert sha(HERE.parent / 'evidence_reuse.py') == '3e9e060609e34b190807f06d14e5cf984ddcef855454caafa94c93a7eede78b5'
assert sha(HERE.parent / 'evidence_reuse_inputs_codex.json') == '3ff79fdb9d65c4b033f6e2f8dd8c37137988d0e8cc83483e6cb43e0caf4e006e'
old = baseline['original_v24_build_entry']
legacy = baseline['original_legacy_build_entry']
entry = copy.deepcopy(old)
entry['argv'] = ['-B', bridge.relative_to(ROOT).as_posix()]
entry['selectors'] = {
    'task_id': list(dict.fromkeys(old['selectors']['task_id'] + legacy['selectors']['task_id'])),
    'check_id': list(dict.fromkeys(old['selectors']['check_id'] + legacy['selectors']['check_id'])),
    'case_id': [],
}
entry['owner_card'] = 'W02-99'
entry['note'] = ('W02-G01/G02/G03 exact parent gates. G01/G03 verify immutable actual evidence '
    'and unchanged relevant inputs; G02 observes the current registry and path map. '
    'Empty W02 check and W02-03 preserve apps/cli/build_check.py. Other admitted legacy '
    'tuples preserve ops/ci/build.py argv/environment/streams/exit, including its own '
    'rejection of mismatched task/check pairs. Construction only; no formal case acceptance.')
entry['expected_artifacts'] = list(dict.fromkeys(old['expected_artifacts'] + [
    bridge.relative_to(ROOT).as_posix(),
    (HERE.parent / 'parent_driver.py').relative_to(ROOT).as_posix(),
    (HERE.parent / 'evidence_reuse.py').relative_to(ROOT).as_posix(),
    (HERE.parent / 'evidence_reuse_inputs_codex.json').relative_to(ROOT).as_posix(),
]))
for name in ('executable_tool', 'cwd', 'platforms', 'required_env', 'allowed_env',
             'fixed_env', 'tool_env', 'timeout_seconds', 'assertion_field', 'state'):
    assert entry[name] == old[name], name
registry['commands']['build.check'] = entry
registry['revision'] = 35
assert {k: v for k, v in registry['commands'].items() if k != 'build.check'} == {
    k: v for k, v in before['commands'].items() if k != 'build.check'}
assert {k: v for k, v in registry.items() if k not in ('commands', 'revision')} == {
    k: v for k, v in before.items() if k not in ('commands', 'revision')}
save(registry_path, registry)
assert load(registry_path) == registry
save(HERE / 'binding_codex.json', {
    'schema': 'researchos.exact-command-binding.v1',
    'registered_at': dt.datetime.now(dt.timezone.utc).isoformat(),
    'actor': 'codex:/root', 'source_head': subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
    'command_key': 'build.check', 'registry_revision': 35,
    'baseline_sha256': sha(HERE / 'binding_baseline_codex.json'),
    'registry_sha256': sha(registry_path), 'bridge_sha256': sha(bridge),
    'other_decoded_entries_preserved': len(registry['commands']) - 1,
    'legacy_registry_sha256_before_after': baseline['legacy_registry_sha256'],
    'protected_source_hashes_unchanged': baseline['protected_source_hashes'],
    'original_v24_entry': old, 'new_entry': entry,
    'new_product_tests': 0, 'formal_case_count_delta': 0,
})
print(json.dumps({'status': 'PASS_BINDING_ONLY', 'revision': 35,
                  'other_entries_preserved': len(registry['commands']) - 1}))
