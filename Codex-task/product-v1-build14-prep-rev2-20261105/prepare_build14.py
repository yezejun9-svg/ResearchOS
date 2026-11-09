"""Root-only materialization of a fresh build14 worktree and owned scope. Never launches it."""
import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('D:/作品集/ResearchOS/research-os')
HERE = Path(__file__).resolve().parent
CONTROL = HERE.parent / 'product-v1-owned-verification-20261104'
WT = ROOT / '.local/worktrees/product-v1-build-14-20261105'
BASE = ROOT / 'execution/product-v1/receipts/single-harness-20261104/build14-scope'
SCOPE = CONTROL / 'scopes/product-v1-build-14.json'
QUAL = HERE.parent / 'product-v1-native-qualification-中文-root-01'
HELPER = HERE.parent / 'product-v1-native-helper-build01/buildout/qualification-helper.exe'
HELPER_SHA = '4ac03d2af358ab0ecb4d2f06a12bbc0bcde043e7e3610ee114a64c0416f1b4ef'
CANARIES = {'README.md': 'bbf19460eb93f739649abce74a96c045bb03dfebe500220d6b1c7c75e768dbb9',
            'probe.txt': 'c22341092e51220d3dc26a8a13dbec78b9e65b40096cf1365363cf8471bddfd3'}
OWNER_SHA = 'f13f630d21548bf8bbb9f1bdaf08b78adc41546d32f00216c05f6ae3664a218c'
PYTHON = Path('C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe')
GO = ROOT / '.local/tools/go1.27.1/go/bin/go.exe'
NODE = Path('C:/nvm4w/nodejs/node.exe')
ELECTRON = ROOT / 'apps/desktop/node_modules/electron/dist'
MODULE_CACHE = ROOT / '.local/tools/gopath/pkg/mod'
WEB = ROOT / '.local/product-v1-build-inputs-20261104/web-node_modules-02/node_modules'
WEB_MANIFEST = WEB.parent / 'INPUTS-02.json'
WEB_MANIFEST_SHA = '75beb02ce4a6a6c0eec69ede2d8da6a29cca4596632bbb6b2c29956473766493'
VITE = WEB / 'vite/bin/vite.js'
VITE_SHA = 'de5833362e640673962f16e255bf8738d4380a68601b9af26217eee4e1bac36d'
PYTHON_SHA = 'cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b'
GO_SHA = 'd3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490'
NODE_SHA = '5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6'
ELECTRON_SHA = '8d205e25b40da3ada4a08c92f32bfbd8e8d38edb4bfe443deea77fc9de685bac'
UI_REF = 'apps/web/src/components/workbench-layout.jsx'
UI_SCOPE = 'PRODUCT_V1_WORKBENCH_ASSISTANT_REFINEMENT'
BOUND = ('PRODUCT_V1_QUALIFICATION_BUILD_BINDING', 'PRODUCT_V1_NATIVE_PRELAUNCH_INTENT', UI_SCOPE)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    return json.loads(path.read_bytes())

def put_new(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

def git(cwd, *args):
    return subprocess.check_output(['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false',
                                    '--no-optional-locks', *args], cwd=cwd, stderr=subprocess.STDOUT).decode('utf-8').strip()

def pinned(path, digest):
    assert path.is_file() and sha(path) == digest, path
    return dict(path=str(path), sha256=digest)

parser = argparse.ArgumentParser(description='Root-only build14 registration; does not execute scope')
parser.add_argument('--materialize', action='store_true', required=True)
parser.add_argument('--final-head', required=True)
parser.add_argument('--source-union-sha256', required=True)
parser.add_argument('--ui-layout-sha256', required=True)
args = parser.parse_args()
for value in (args.final_head, args.source_union_sha256, args.ui_layout_sha256):
    assert re.fullmatch('[0-9a-f]{40}' if value == args.final_head else '[0-9a-f]{64}', value)
assert not WT.exists() and not BASE.exists() and not SCOPE.exists()
assert not (CONTROL / 'runs/product-v1-build-14').exists()
assert sha(CONTROL / 'owned_run.py') == OWNER_SHA
cp = read(ROOT / 'execution/v2.4/checkpoint.json')
assert cp['current_Main_HEAD'] == args.final_head == git(ROOT, 'rev-parse', 'HEAD')
assert not git(ROOT, 'diff', '--cached', '--name-only')
state = read(ROOT / 'execution/product-v1/state.json')
active = {row['scope_id']: row for row in state['active_scopes']}
for scope_id in BOUND:
    assert active[scope_id]['status'] == 'SOURCE_INTEGRATED_NOT_LIVE_QUALIFIED', scope_id
assert any(row['scope_id'] == UI_SCOPE for row in state['integrated_source'])
pins = {ref: digest for item in state['integrated_source']
        for ref, digest in item['source_sha256'].items()}
assert pins[UI_REF] == args.ui_layout_sha256
union_sha = hashlib.sha256(json.dumps(pins, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
assert union_sha == args.source_union_sha256
for ref, digest in pins.items():
    assert not Path(ref).is_absolute() and '..' not in Path(ref).parts
    pinned(ROOT / ref, digest)
assert QUAL.is_dir() and sorted(p.name for p in (QUAL / 'S').iterdir()) == ['README.md', 'probe.txt', 'qualification-helper.exe']
assert sha(HELPER) == HELPER_SHA
assert sha(QUAL / 'S/qualification-helper.exe') == HELPER_SHA
for name, digest in CANARIES.items():
    pinned(QUAL / 'S' / name, digest)
assert WEB.is_dir() and MODULE_CACHE.is_dir()
for path, digest in ((WEB_MANIFEST, WEB_MANIFEST_SHA), (VITE, VITE_SHA),
                     (PYTHON, PYTHON_SHA), (GO, GO_SHA), (NODE, NODE_SHA),
                     (ELECTRON / 'electron.exe', ELECTRON_SHA)):
    pinned(path, digest)

# Nothing above mutates D. Root may inspect the exact head and union before this point.
git(ROOT, 'worktree', 'add', '--no-checkout', '-b', 'codex/product-v1-build-14-20261105', str(WT), args.final_head)
patterns = ['/.gitignore', '/AGENTS.md', '/go.mod', '/go.sum', '/go.work', '/go.work.sum',
            '/apps/', '/cmd/', '/tests/desktop/', '/internal/', '/adapters/',
            '/migrations/sqlite/', '/spec/v2.0/contracts/', '/spec/v2.0/ui/',
            '/ops/', '/tests/ui/', '/tests/runtime/', '/docs/installation/', '/execution/toolchains/']
git(WT, 'sparse-checkout', 'set', '--no-cone', *patterns)
git(WT, 'checkout', 'HEAD')
deps = git(WT, 'ls-tree', '-r', '--name-only', 'HEAD', '--',
           'evaluation/holdout/jev', 'evaluation/evolution', 'evaluation/skills').splitlines()
code = ['/' + ref for ref in deps if ref.endswith('.go') and not ref.endswith('_test.go')]
if code:
    git(WT, 'sparse-checkout', 'add', *code)
assert not git(WT, 'status', '--porcelain=v1')
for ref, digest in pins.items():
    pinned(WT / ref, digest)
required = ['.gitignore', 'spec/v2.0/ui/design-tokens.json', 'execution/toolchains/locked.json',
            'apps/desktop/build-development.py', 'apps/desktop/build-validator.py',
            'apps/desktop/launch-development.mjs', 'docs/installation/desktop-development.md',
            'go.mod', 'go.sum']
for ref in required:
    assert (WT / ref).is_file(), ref
bundle = WT / '.local/desktop-v1-build-14'
producer = BASE / 'producer-14'
assert not bundle.exists() and not producer.exists()
builder = WT / 'apps/desktop/build-development.py'
builder_sha = sha(builder)
builder_argv = ['--go', str(GO), '--node', str(NODE), '--electron-dist', str(ELECTRON),
                '--module-cache', str(MODULE_CACHE), '--web-modules', str(WEB),
                '--mu-common', str(ROOT), '--output', str(bundle), '--receipts', str(producer),
                '--qualification-root', str(QUAL), '--qualification-helper', str(HELPER),
                '--qualification-helper-sha256', HELPER_SHA]
wrapper = HERE / 'build_desktop_serial14.py'
registration = dict(status='REGISTERED_NOT_EXECUTED', at=datetime.now(timezone.utc).isoformat(),
                    main_head=args.final_head, main_checkpoint=cp['revision'], clean_worktree=str(WT),
                    source_sha256=pins, source_union_sha256=union_sha, ui_layout_sha256=args.ui_layout_sha256,
                    builder_sha256=builder_sha, builder_argv=builder_argv,
                    wrapper=str(wrapper), wrapper_sha256=sha(wrapper), gomaxprocs=1,
                    qualification_root=str(QUAL), qualification_helper=str(HELPER),
                    qualification_helper_sha256=HELPER_SHA, qualification_canaries_sha256=CANARIES,
                    bundle=str(bundle), producer_receipts=str(producer),
                    web_manifest=str(WEB_MANIFEST), web_manifest_sha256=WEB_MANIFEST_SHA,
                    model_gui_started=False, formal_increment=0, product_acceptance_increment=0)
BASE.mkdir()
put_new(BASE / 'registration.json', registration)
inputs = [pinned(WT / ref, digest) for ref, digest in pins.items()]
for path in (wrapper, HERE / 'prepare_build14.py', BASE / 'registration.json',
             CONTROL / 'owned_run.py', HELPER, QUAL / 'S/qualification-helper.exe'):
    inputs.append(pinned(path, sha(path)))
for name, digest in CANARIES.items():
    inputs.append(pinned(QUAL / 'S' / name, digest))
for scope_id in BOUND:
    path = ROOT / active[scope_id]['scope_ref']
    inputs.append(pinned(path, sha(path)))
fixture = ROOT / 'execution/product-v1/receipts/single-harness-20261104/native-fixture-preparation01'
helper_receipts = ROOT / 'execution/product-v1/receipts/single-harness-20261104/native-helper-build01'
for path in (fixture / 'product-v1-first-native-fixture-canaries-preparation.json',
             fixture / 'product-v1-first-native-fixture-preparation.json',
             helper_receipts / 'scope.json', helper_receipts / 'RESULT.json',
             helper_receipts / 'POSTCHECK.json', helper_receipts / 'MANIFEST.json'):
    inputs.append(pinned(path, sha(path)))
for path in [WT / ref for ref in required] + [GO, NODE, ELECTRON / 'electron.exe', WEB_MANIFEST, VITE]:
    inputs.append(pinned(path, sha(path)))
scope = dict(schema='researchos.owned-windows-run/1', scope_id='product-v1-build-14', purpose='build',
             authorization='ROOT_REVIEWED_EXACT_COMMAND', controller_sha256=OWNER_SHA,
             executable=str(PYTHON), executable_sha256=PYTHON_SHA,
             argv=['-B', '-X', 'utf8', str(wrapper), str(builder), *builder_argv], cwd=str(WT),
             inputs=inputs, timeout_seconds=1200, graceful='none', grace_seconds=0,
             cleanup_seconds=5, process_limit=48, memory_mib=6144, max_raw_bytes=67108864,
             env=dict(GOENV='off', GOTOOLCHAIN='local', GOPROXY='off', GOSUMDB='off', GOWORK='off'))
put_new(SCOPE, scope)
put_new(BASE / 'registration-binding.json', dict(status='REGISTERED_NOT_EXECUTED', scope_path=str(SCOPE),
                                                 scope_sha256=sha(SCOPE), main_head=args.final_head,
                                                 source_union_sha256=union_sha))
print(json.dumps(dict(status='REGISTERED_NOT_EXECUTED', scope_path=str(SCOPE), scope_sha256=sha(SCOPE),
                      source_count=len(pins), main_head=args.final_head), ensure_ascii=False))
