"""Root-reviewed C-only registration of exact6 UI worktree Vite candidate. No launch."""
import argparse
import hashlib
import importlib.util
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
C = HERE.parents[1]
ROOT = Path('D:/作品集/ResearchOS/research-os')
UI_WT = ROOT / '.local/worktrees/product-v1-workbench-assistant-refinement-20261105'
LEASE = ROOT / 'execution/product-v1/receipts/single-harness-20261104/workbench-assistant-refinement/scope.json'
CONTROL = C / 'product-v1-owned-verification-20261104'
SCOPE = CONTROL / 'scopes/product-v1-workbench-refinement-vite-01.json'
REG = HERE / 'registration.json'
STAGE = HERE / 'stage-01'
LIB = C / 'product-v1-build-inputs-20261104/copy_public_web.py'
READBACK = C / 'product-v1-build-inputs-20261104/repair-02/TARGET.readback.json'
WEB = ROOT / '.local/product-v1-build-inputs-20261104/web-node_modules-02/node_modules'
WEB_MANIFEST = WEB.parent / 'INPUTS-02.json'
PYTHON = Path('C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe')
NODE = Path('C:/nvm4w/nodejs/node.exe')
FIXED = {LIB: '71d671c387dd82b4b1982c1c45f6f77645249ff9872d6aef82208b833bc941c0',
         READBACK: 'e1c316403d5e6614a48ade25ad8169227d39200a30426f213dbec73bcdebde26',
         WEB_MANIFEST: '75beb02ce4a6a6c0eec69ede2d8da6a29cca4596632bbb6b2c29956473766493',
         WEB / 'vite/bin/vite.js': 'de5833362e640673962f16e255bf8738d4380a68601b9af26217eee4e1bac36d',
         PYTHON: 'cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b',
         NODE: '5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6',
         CONTROL / 'owned_run.py': 'f13f630d21548bf8bbb9f1bdaf08b78adc41546d32f00216c05f6ae3664a218c'}
EXACT6 = ('apps/web/src/workbench.jsx', 'apps/web/src/workbench.css',
          'apps/web/src/components/workbench-layout.jsx', 'apps/web/src/harness-progress.js',
          'tests/ui/desktop/harness-workbench.test.mjs', 'tests/ui/harness-progress.test.mjs')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def pin(path, expected=None):
    digest = sha(path)
    assert expected is None or digest == expected, path
    return dict(path=str(path), sha256=digest)

p = argparse.ArgumentParser()
p.add_argument('--register', action='store_true', required=True)
p.add_argument('--freeze-dir', type=Path, required=True)
p.add_argument('--freeze-manifest-sha256', required=True)
a = p.parse_args()
assert re.fullmatch('[0-9a-f]{64}', a.freeze_manifest_sha256)
assert not SCOPE.exists() and not REG.exists() and not STAGE.exists()
assert not (CONTROL / 'runs/product-v1-workbench-refinement-vite-01').exists()
for path, digest in FIXED.items():
    pin(path, digest)
lease = json.loads(LEASE.read_bytes())
assert lease['scope_id'] == 'PRODUCT_V1_WORKBENCH_ASSISTANT_REFINEMENT'
assert Path(lease['worktree']).resolve() == UI_WT.resolve()
freeze = a.freeze_dir.resolve()
manifest = freeze / 'manifest.json'
pin(manifest, a.freeze_manifest_sha256)
frozen = json.loads(manifest.read_bytes())
assert frozen['schema'] == 'researchos.workbench-refinement-freeze/1'
assert frozen['scope_id'] == 'PRODUCT_V1_WORKBENCH_ASSISTANT_REFINEMENT'
assert Path(frozen['candidate_root']).resolve() == UI_WT.resolve()
assert Path(frozen['archive_root']).resolve() == freeze
six = {row['repo_relative']: row['candidate_sha256'] for row in frozen['files']}
assert set(six) == set(EXACT6)
for ref, digest in six.items():
    pin(UI_WT / ref, digest)
assert WEB.is_dir()
spec = importlib.util.spec_from_file_location('readonly_public_tree', LIB)
lib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lib)
actual = lib.tree(WEB, True)
assert actual == json.loads(READBACK.read_bytes())
assert actual['file_count'] == 365 and actual['logical_bytes'] == 45843230

sources = [p for p in (UI_WT / 'apps/web/src').rglob('*') if p.is_file()]
sources += [UI_WT / 'apps/web' / name for name in ('index.html', 'package.json', 'package-lock.json')]
sources += [p for p in (UI_WT / 'apps/web').glob('vite.config.*') if p.is_file()]
if (UI_WT / 'apps/web/public').is_dir():
    sources += [p for p in (UI_WT / 'apps/web/public').rglob('*') if p.is_file()]
sources += [UI_WT / 'apps/desktop/main/lib/wire-values.mjs', UI_WT / 'spec/v2.0/ui/design-tokens.json']
source_pins = {p.relative_to(UI_WT).as_posix(): sha(p) for p in sources}
assert source_pins['apps/web/src/workbench.jsx'] == six['apps/web/src/workbench.jsx']
for ref in ('apps/desktop/main/lib/wire-values.mjs', 'spec/v2.0/ui/design-tokens.json'):
    assert ref in source_pins
runner = HERE / 'run_ui_vite.py'
registration = dict(status='REGISTERED_NOT_EXECUTED', scope_id='product-v1-workbench-refinement-vite-01',
                    freeze_manifest=str(manifest), freeze_manifest_sha256=a.freeze_manifest_sha256,
                    ui_worktree=str(UI_WT), exact6_sha256=six, stage=str(STAGE),
                    sources_sha256=source_pins, module_readback_sha256=FIXED[READBACK],
                    module_file_count=actual['file_count'], module_logical_bytes=actual['logical_bytes'],
                    runner_sha256=sha(runner), node_sha256=FIXED[NODE], vite_sha256=FIXED[WEB / 'vite/bin/vite.js'],
                    app_or_model_started=False, formal_increment=0)
with REG.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(registration, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
inputs = [pin(UI_WT / ref, digest) for ref, digest in source_pins.items()]
inputs += [pin(UI_WT / ref, digest) for ref, digest in six.items() if ref not in source_pins]
inputs += [pin(WEB / row['path'], row['sha256']) for row in actual['files']]
inputs += [pin(path, digest) for path, digest in FIXED.items()]
inputs += [pin(manifest, a.freeze_manifest_sha256), pin(LEASE), pin(runner), pin(Path(__file__)), pin(REG)]
scope = dict(schema='researchos.owned-windows-run/1', scope_id='product-v1-workbench-refinement-vite-01',
             purpose='build', authorization='ROOT_REVIEWED_EXACT_COMMAND',
             controller_sha256=FIXED[CONTROL / 'owned_run.py'], executable=str(PYTHON),
             executable_sha256=FIXED[PYTHON], argv=['-B', '-X', 'utf8', str(runner)], cwd=str(HERE),
             inputs=inputs, timeout_seconds=120, graceful='none', grace_seconds=0, cleanup_seconds=5,
             process_limit=24, memory_mib=3072, max_raw_bytes=67108864,
             env=dict(GOENV='off', GOTOOLCHAIN='local', GOPROXY='off', GOSUMDB='off', GOWORK='off'))
with SCOPE.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(scope, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps(dict(status='REGISTERED_NOT_EXECUTED', scope=str(SCOPE), scope_sha256=sha(SCOPE),
                      source_count=len(source_pins), module_files=actual['file_count']), ensure_ascii=False))
