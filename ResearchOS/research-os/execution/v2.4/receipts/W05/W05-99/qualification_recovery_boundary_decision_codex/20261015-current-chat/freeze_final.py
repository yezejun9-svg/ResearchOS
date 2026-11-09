import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

base = Path(__file__).resolve().parent
if (base / 'FINAL-manifest.json').exists():
    raise SystemExit('already frozen')
env = {k: os.environ[k] for k in ('SystemRoot', 'WINDIR', 'TEMP', 'TMP', 'PATH', 'PATHEXT', 'COMSPEC') if k in os.environ}
env.update({'PYTHONUTF8': '1', 'PYTHONIOENCODING': 'utf-8'})
verification = r'''import hashlib,json,sys
from pathlib import Path
b=Path(sys.argv[1])
parsed=0
for p in b.glob('*.json'):
    json.loads(p.read_text(encoding='utf-8-sig'));parsed+=1
for p in b.glob('*.result.json'):
    for r in json.loads(p.read_text(encoding='utf8'))['raw']:
        f=b/r['path'];assert f.stat().st_size==r['bytes'];assert hashlib.sha256(f.read_bytes()).hexdigest()==r['sha256']
d=json.loads((b/'boundary-decision.json').read_text(encoding='utf8'))
assert d['actual_authority'] is False and d['source_write_authority'] is False
assert d['formal_increment']==0 and d['all_parent_tasks_open']==22
assert d['proposed_class_status']=='NOT_IMPLEMENTED_NOT_ACCEPTED'
assert d['query_groups_used']==8 and d['query_groups_limit']==12
l=json.loads((b/'command-ledger.json').read_text(encoding='utf8'))
assert len(l['groups'])==8 and l['query_budget_closed'] is True
assert (b/'boundary-decision.md').stat().st_size>0
print(json.dumps({'status':'PASS_ARTIFACT_CONSISTENCY_ONLY','json_files':parsed,'query_groups':8,'formal_increment':0,'actual_authority':False}))
'''
argv = [sys.executable, '-X', 'utf8', '-c', verification, str(base)]
recipe = {'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'cwd': str(base), 'argv': argv, 'environment_exact': env, 'purpose': 'Own-artifact consistency then freeze, not research query or Source acceptance'}
(base / '010-freeze.recipe.json').open('x', encoding='utf8').write(json.dumps(recipe, ensure_ascii=False, indent=2) + '\n')
r = subprocess.run(argv, cwd=base, env=env, capture_output=True)
raw = []
for suffix, data in (('stdout.raw', r.stdout), ('stderr.raw', r.stderr)):
    p = base / ('010-freeze.' + suffix)
    p.open('xb').write(data)
    raw.append({'path': p.name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
(base / '010-freeze.result.json').open('x', encoding='utf8').write(json.dumps({'native_exit': r.returncode, 'raw': raw}, indent=2) + '\n')
if r.returncode:
    sys.stdout.buffer.write(r.stdout)
    sys.stderr.buffer.write(r.stderr)
    raise SystemExit(r.returncode)
files = []
for p in sorted(base.rglob('*')):
    if p.is_file():
        files.append({'path': p.relative_to(base).as_posix(), 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()})
manifest = {'schema': 'researchos.qualification-recovery-boundary-decision-final.v1', 'frozen_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'owner': 'codex:/root/verifier_revision_review', 'status': 'BOUNDED_DECISION_FROZEN_NOT_ACCEPTANCE', 'decision': 'RECOMMEND_CONDITIONAL_FUTURE_FULL_RESTART_BOUNDARY', 'proposed_class_status': 'NOT_IMPLEMENTED_NOT_ACCEPTED', 'source_write_authority': False, 'actual_authority': False, 'formal_increment': 0, 'all_parent_tasks_open': 22, 'query_groups_used': 8, 'query_groups_limit': 12, 'final_self_excluded': True, 'refs': files, 'external_refs': json.loads((base / 'external-refs.json').read_text(encoding='utf8')), 'validation': 'Artifact syntax, frozen raw hashes, scoped external input hashes and report invariants only; no Source tests, live operation or class acceptance'}
p = base / 'FINAL-manifest.json'
p.open('x', encoding='utf8').write(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
for ref in files:
    f = base / ref['path']
    assert f.stat().st_size == ref['bytes']
    assert hashlib.sha256(f.read_bytes()).hexdigest() == ref['sha256']
print(json.dumps({'manifest': str(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'refs': len(files), 'external_refs': len(manifest['external_refs']), 'native_validation_exit': r.returncode, 'formal_increment': 0, 'actual_authority': False}, ensure_ascii=False))
