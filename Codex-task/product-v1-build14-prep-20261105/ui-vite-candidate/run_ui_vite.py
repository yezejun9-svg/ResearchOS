"""Owned single-use Vite production build of staged exact UI worktree source."""
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
C = HERE.parents[1]
ROOT = Path('D:/作品集/ResearchOS/research-os')
REG = HERE / 'registration.json'
LIB = C / 'product-v1-build-inputs-20261104/copy_public_web.py'
READBACK = C / 'product-v1-build-inputs-20261104/repair-02/TARGET.readback.json'
WEB = ROOT / '.local/product-v1-build-inputs-20261104/web-node_modules-02/node_modules'
NODE = Path('C:/nvm4w/nodejs/node.exe')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

reg = json.loads(REG.read_bytes())
assert reg['status'] == 'REGISTERED_NOT_EXECUTED'
assert sha(Path(__file__)) == reg['runner_sha256']
assert sha(Path(reg['freeze_manifest'])) == reg['freeze_manifest_sha256']
assert sha(NODE) == reg['node_sha256']
assert sha(WEB / 'vite/bin/vite.js') == reg['vite_sha256']
wt = Path(reg['ui_worktree'])
assert wt == ROOT / '.local/worktrees/product-v1-workbench-assistant-refinement-20261105'
stage = Path(reg['stage'])
assert stage == HERE / 'stage-01' and not stage.exists()
sources = reg['sources_sha256']
for ref, digest in sources.items():
    assert sha(wt / ref) == digest, ref
for ref, digest in reg['exact6_sha256'].items():
    assert sha(wt / ref) == digest, ref
spec = importlib.util.spec_from_file_location('readonly_public_tree', LIB)
lib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lib)
before = lib.tree(WEB, True)
assert before == json.loads(READBACK.read_bytes())
assert sha(READBACK) == reg['module_readback_sha256']
assert before['file_count'] == reg['module_file_count'] and before['logical_bytes'] == reg['module_logical_bytes']

stage.mkdir()
for ref, digest in sources.items():
    target = stage / ref
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(wt / ref, target)
    assert sha(target) == digest, ref
web_stage = stage / 'apps/web'
link = web_stage / 'node_modules'
assert not link.exists()
subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(WEB)],
               cwd=HERE, check=True, capture_output=True, timeout=10)
assert link.is_dir()
out = web_stage / 'dist'
argv = [str(NODE), str(WEB / 'vite/bin/vite.js'), 'build', '--outDir', str(out)]
with (stage / 'vite.stdout.raw').open('xb') as stdout, (stage / 'vite.stderr.raw').open('xb') as stderr:
    completed = subprocess.run(argv, cwd=web_stage, stdin=subprocess.DEVNULL,
                               stdout=stdout, stderr=stderr, timeout=105)
after = lib.tree(WEB, True)
source_drift = [ref for ref, digest in sources.items() if sha(wt / ref) != digest or sha(stage / ref) != digest]
outputs = [dict(path=p.relative_to(out).as_posix(), sha256=sha(p), bytes=p.stat().st_size)
           for p in sorted(out.rglob('*')) if p.is_file()] if out.is_dir() else []
result = dict(status='BUILT_NOT_APP_OR_MODEL_TESTED' if completed.returncode == 0 and not source_drift and before == after else 'BUILD_FAILED_OR_DRIFT',
              exit_code=completed.returncode, argv=argv, cwd=str(web_stage), outputs=outputs,
              source_drift=source_drift, module_closure_unchanged=before == after,
              module_closure_sha256=sha(READBACK), source_count=len(sources),
              app_or_model_started=False, formal_increment=0)
with (stage / 'RESULT.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps(dict(status=result['status'], exit_code=completed.returncode,
                      output_files=len(outputs), source_drift=source_drift,
                      module_closure_unchanged=before == after), ensure_ascii=False))
raise SystemExit(0 if result['status'] == 'BUILT_NOT_APP_OR_MODEL_TESTED' else 1)
