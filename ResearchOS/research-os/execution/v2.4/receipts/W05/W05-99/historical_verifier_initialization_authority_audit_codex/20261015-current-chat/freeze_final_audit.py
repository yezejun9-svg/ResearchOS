import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

base = Path(__file__).resolve().parent
if (base / 'FINAL-manifest.json').exists():
    raise SystemExit('Already frozen')
env = {k: os.environ[k] for k in ('SystemRoot', 'WINDIR', 'TEMP', 'TMP', 'PATH', 'PATHEXT', 'COMSPEC') if k in os.environ}
env.update({'PYTHONUTF8': '1', 'PYTHONIOENCODING': 'utf-8'})
script = """import json
from pathlib import Path
p=Path.cwd()
a=json.loads((p/'audit.json').read_text(encoding='utf8'))
c=json.loads((p/'selected-init-coverage.json').read_text(encoding='utf8'))
assert a['decision']=='NOT_PROVABLE_NO_NEW_OPERATIONAL_CLASS'
assert not a['self_acceptance'] and a['formal_increment']==0
assert len(c['entries'])==5413 and c['covered_original_entries']==4696
assert not c['semantic_closure_complete']
assert all(not (p/n).exists() for n in ('analysis-cache','analysis-tmp','analysis-gopath'))
print(json.dumps({'decision':a['decision'],'original_init_coverage':4696,'entries':5413,'semantic_acceptance':False,'formal_increment':0}))
"""
argv = [sys.executable, '-X', 'utf8', '-c', script]
recipe = {'schema': 'researchos.final-audit-freeze-command.v1', 'cwd': str(base), 'argv': argv, 'environment_exact': env, 'before_execution_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'wrapper': str(Path(__file__).resolve()), 'wrapper_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(base / '031-final-verification.recipe.json').open('x', encoding='utf8').write(json.dumps(recipe, ensure_ascii=False, indent=2) + '\n')
result = subprocess.run(argv, cwd=base, env=env, capture_output=True)
raw = []
for suffix, data in (('stdout.raw', result.stdout), ('stderr.raw', result.stderr)):
    p = base / ('031-final-verification.' + suffix)
    p.open('xb').write(data)
    raw.append({'path': p.name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
(base / '031-final-verification.result.json').open('x', encoding='utf8').write(json.dumps({'native_exit': result.returncode, 'raw': raw, 'ended_at': datetime.datetime.now(datetime.timezone.utc).isoformat()}, indent=2) + '\n')
if result.returncode:
    sys.stdout.buffer.write(result.stdout)
    sys.stderr.buffer.write(result.stderr)
    raise SystemExit(result.returncode)
files = []
for p in sorted(base.rglob('*')):
    if p.is_file():
        data = p.read_bytes()
        files.append({'path': p.relative_to(base).as_posix(), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
manifest = {'schema': 'researchos.immutable-semantic-audit-manifest.v1', 'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'decision': 'NOT_PROVABLE_NO_NEW_OPERATIONAL_CLASS', 'files': files, 'file_count': len(files), 'exclusions': ['FINAL-manifest.json (self hash returned by outer tool transcript)'], 'semantic_acceptance': False, 'formal_increment': 0}
path = base / 'FINAL-manifest.json'
path.open('x', encoding='utf8').write(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
for ref in files:
    data = (base / ref['path']).read_bytes()
    assert len(data) == ref['bytes'] and hashlib.sha256(data).hexdigest() == ref['sha256']
print(json.dumps({'manifest': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'file_count': len(files), 'verified_manifest_entries': len(files), 'native_child_exit': result.returncode, 'decision': manifest['decision']}, ensure_ascii=False))
