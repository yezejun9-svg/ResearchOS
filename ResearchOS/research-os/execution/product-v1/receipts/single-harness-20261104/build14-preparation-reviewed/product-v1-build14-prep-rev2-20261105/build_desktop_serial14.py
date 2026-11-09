"""Pinned, single-process entry to the actual Desktop development builder."""
import hashlib
import json
import os
import runpy
import subprocess
import sys
from pathlib import Path

ROOT = Path('D:/作品集/ResearchOS/research-os')
HERE = Path(__file__).resolve().parent
WT = ROOT / '.local/worktrees/product-v1-build-14-20261105'
REG = ROOT / 'execution/product-v1/receipts/single-harness-20261104/build14-scope/registration.json'
BUILDER = WT / 'apps/desktop/build-development.py'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def git(*args):
    return subprocess.check_output(['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false',
                                    '--no-optional-locks', *args], cwd=ROOT).decode('utf-8').strip()

registration = json.loads(REG.read_bytes())
assert registration['status'] == 'REGISTERED_NOT_EXECUTED'
assert registration['main_head'] == git('rev-parse', 'HEAD')
assert registration['main_head'] == git('-C', str(WT), 'rev-parse', 'HEAD')
assert sha(BUILDER) == registration['builder_sha256']
assert Path(sys.argv[1]).resolve() == BUILDER.resolve()
assert sys.argv[2:] == registration['builder_argv']
assert sha(HERE / 'build_desktop_serial14.py') == registration['wrapper_sha256']
state = json.loads((ROOT / 'execution/product-v1/state.json').read_bytes())
pins = {ref: digest for item in state['integrated_source']
        for ref, digest in item['source_sha256'].items()}
assert pins == registration['source_sha256']
assert hashlib.sha256(json.dumps(pins, sort_keys=True, separators=(',', ':')).encode()).hexdigest() == registration['source_union_sha256']
for ref, digest in pins.items():
    assert sha(WT / ref) == digest, ref
assert sha(Path(registration['qualification_helper'])) == registration['qualification_helper_sha256']
for name, digest in registration['qualification_canaries_sha256'].items():
    assert sha(Path(registration['qualification_root']) / 'S' / name) == digest
os.environ['GOMAXPROCS'] = '1'
sys.argv = [str(BUILDER), *sys.argv[2:]]
runpy.run_path(str(BUILDER), run_name='__main__')
