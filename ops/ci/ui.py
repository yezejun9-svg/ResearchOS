"""W13 development browser acceptance subset; no independent verifier claim."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / 'apps/web'


def main():
    if os.environ.get('RESEARCHOS_TASK_ID') != 'W13':
        raise SystemExit('RESEARCHOS_TASK_ID=W13 required')
    locked = json.loads((ROOT / 'execution/toolchains/locked.json').read_text(encoding='utf-8'))
    node = Path(locked['tools']['node']['path'])
    vite = WEB / 'node_modules/vite/bin/vite.js'
    if not node.is_file() or not vite.is_file():
        raise SystemExit('pinned Node or npm ci dependencies unavailable')
    build = subprocess.run([str(node), str(vite), 'build'], cwd=WEB)
    if build.returncode:
        return build.returncode
    return subprocess.run([sys.executable, str(ROOT / 'tests/ui/browser_smoke.py')], cwd=ROOT).returncode


if __name__ == '__main__':
    raise SystemExit(main())
