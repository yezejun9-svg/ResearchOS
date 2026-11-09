import sys
sys.dont_write_bytecode = True
import ast
import hashlib
import json
from pathlib import Path

assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode and not sys.flags.optimize
ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
PREVIOUS = OUT.parent / 'fresh-handler38-source-integration-r321-v2'
SCOPE_SHA = '52d8f686f07a606afaeb64eccca26f53edb2872bf93fa595132fd6afc067da71'
assert hashlib.sha256((OUT / 'scope_registration.json').read_bytes()).hexdigest() == SCOPE_SHA
scope = json.loads((OUT / 'scope_registration.json').read_bytes())
assert scope['expected_before_registration'] == [322, 150, 425] and scope['expected_registration'] == [323, 151, 425]

def once(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new, 1)

def save(name, text):
    ast.parse(text, filename=name)
    raw = text.encode('utf-8')
    with (OUT / name).open('xb') as stream:
        stream.write(raw)
    return {'path': (OUT / name).relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

producer_old = (PREVIOUS / 'grant-producer.py').read_bytes()
assert hashlib.sha256(producer_old).hexdigest() == 'dfbed4a9feb172a46aafa426775605428a1dc1f47d69b3d1c6cf91c50b0d6577'
producer = producer_old.decode('utf-8')
for old, new in [
    ('actual reviewed CP321 seal', 'actual reviewed CP323 seal'),
    ('[321, 149, 422]', '[323, 151, 425]'),
    ('254642660280442df4352e355d0e01f6c0fc8bab8bc7337554d6bbc26a223f90', SCOPE_SHA),
    ('main_exact38_integration_root_grant_codex', 'cli_exact8_integration_root_grant_codex'),
    ("scope['base_commit']", "scope['base']"),
    ('researchos.exact38-integration-controller-review.v1', 'researchos.cli8-source-integration-controller-review.v1'),
    ('READY_FOR_ROOT_EXACT38_FAST_FORWARD_ONCE', 'READY_FOR_ROOT_EXACT8_SOURCE_COMMIT_ONCE_WITH_OPEN_GATES'),
    ('handler38_source_integration_scope_ref', 'cli_exact8_source_integration_scope_ref'),
    ('handler38_source_integration_controller_review_ref', 'cli_exact8_source_integration_controller_review_ref'),
    ('[320, 148, 417]', '[322, 150, 425]'),
    ('main_exact38_integration_executor_codex', 'cli_exact8_integration_executor_codex'),
    ('researchos.exact38-source-integration-grant.v1', 'researchos.cli8-source-integration-grant.v1'),
    ("'source_chain': scope['source_chain']", "'base': scope['base'], 'candidate': scope['candidate'], 'candidate_parent': scope['candidate_parent']")]:
    producer = once(producer, old, new)
producer_ref = save('grant-producer.py', producer)
launcher_old = (PREVIOUS / 'launcher.v2.py').read_bytes()
assert hashlib.sha256(launcher_old).hexdigest() == 'be5fdfae7c321376dc60f964167a92f06725bfe83e97a826e50a6eae8f2a2bc2'
launcher = launcher_old.decode('utf-8')
for old, new in [
    ('fresh-handler38-source-integration-r321-v2', 'cli-exact8-source-integration-r323'),
    ('254642660280442df4352e355d0e01f6c0fc8bab8bc7337554d6bbc26a223f90', SCOPE_SHA),
    ('dfbed4a9feb172a46aafa426775605428a1dc1f47d69b3d1c6cf91c50b0d6577', producer_ref['sha256']),
    ('e2f98bded200afc15cf1afecbc73d0423dcc1ab0a16e5497ca4a1dd7e244d6ff', scope['controller_ref']['sha256']),
    ('main_exact38_integration_root_launcher_codex', 'cli_exact8_integration_root_launcher_codex'),
    ('[321, 149, 422]', '[323, 151, 425]'),
    ('main_exact38_integration_root_grant_codex', 'cli_exact8_integration_root_grant_codex'),
    ("'--grant', str(grant_path), '--grant-sha256', grant['sha256']], 4500)", "'--grant', str(grant_path), '--grant-sha256', grant['sha256']], 1200)"),
    ("'source_FF_attempts_max': 1", "'source_apply_attempts_max': 1, 'source_commit_attempts_max': 1")]:
    launcher = once(launcher, old, new)
launcher_ref = save('launcher.py', launcher)
audit = {'producer_ref': producer_ref, 'launcher_ref': launcher_ref, 'scope_sha256': SCOPE_SHA,
    'old_producer_sha256': hashlib.sha256(producer_old).hexdigest(),
    'old_launcher_sha256': hashlib.sha256(launcher_old).hexdigest(),
    'original_versions_preserved': True, 'actual_execution': False,
    'future_registered_tuple': [323, 151, 425], 'source_apply_cap': 1, 'source_commit_cap': 1,
    'producer_timeout_seconds': 600, 'controller_timeout_seconds': 1200,
    'each_cleanup_seconds': 5, 'Go_SQL_HTTP_models': 0, 'formal_increment': 0}
with (OUT / 'executor-derivation-audit.json').open('xb') as stream:
    stream.write((json.dumps(audit, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
print(json.dumps(audit))
