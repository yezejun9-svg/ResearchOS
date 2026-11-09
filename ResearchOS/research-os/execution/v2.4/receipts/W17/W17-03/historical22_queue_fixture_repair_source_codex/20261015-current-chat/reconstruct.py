import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import tarfile

MAIN = Path('D:/作品集/ResearchOS/research-os')
OUT = Path(__file__).resolve().parent
ROOT = MAIN / '.local/resources/historical22-active-queue-helper-20261015'
OLD = MAIN / 'execution/v2.4/receipts/W05/W05-99/host_configuration_upgrade_executor_codex/old22-build-40e94f3f6e53442fa07068089c0de64a'
PINS = MAIN / 'execution/v2.4/receipts/W17/W17-03/historical22_queue_fixture_resource_map_codex/20261015-current-chat/SOURCE-PINS-502.json'

def sha(data):
    return hashlib.sha256(data).hexdigest()

pins = json.loads(PINS.read_text(encoding='utf-8'))
expected = {item['relative_path']: item for item in pins['files']}
assert len(expected) == pins['count'] == 502
archive = (OLD / 'git-archive.stdout').read_bytes()
assert sha(archive) == '4a82f6471c644ef25489ebbedb3c32452391bcd0e00dcd58453f46200fb9a9b6'
found = {}
with tarfile.open(fileobj=io.BytesIO(archive), mode='r:') as tf:
    for member in tf:
        name = member.name.rstrip('/')
        p = PurePosixPath(name)
        assert name and not p.is_absolute() and ':' not in name and '\\' not in name
        assert all(x not in ('', '.', '..') for x in p.parts)
        if member.isdir():
            continue
        assert member.isfile() and name in expected and name not in found
        data = tf.extractfile(member).read()
        pin = expected[name]
        assert len(data) == member.size == pin['bytes'] and sha(data) == pin['sha256']
        found[name] = data
assert found.keys() == expected.keys()
ROOT.parent.mkdir(parents=True, exist_ok=True)
ROOT.mkdir(exist_ok=False)
for name, data in sorted(found.items()):
    dest = ROOT.joinpath(*PurePosixPath(name).parts)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open('xb') as f:
        f.write(data)
assert {p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file()} == set(expected)
for name, pin in expected.items():
    actual = ROOT.joinpath(*PurePosixPath(name).parts).read_bytes()
    assert len(actual) == pin['bytes'] and sha(actual) == pin['sha256']
(OUT / 'reconstruction.json').write_text(json.dumps({
    'archive': str(OLD / 'git-archive.stdout'), 'archive_sha256': sha(archive),
    'pins': str(PINS), 'pins_sha256': sha(PINS.read_bytes()),
    'root': str(ROOT), 'count': len(found), 'postcopy_verified': True,
    'git_tree_checkout': False,
}, indent=2) + '\n', encoding='utf-8')
print(ROOT)
