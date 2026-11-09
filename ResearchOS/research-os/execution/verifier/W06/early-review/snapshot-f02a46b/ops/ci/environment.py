"""Verify actual, hash-pinned tools and the selected platform."""
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def main():
    locked = json.loads((ROOT / 'execution/toolchains/locked.json').read_text(encoding='utf-8'))
    assert platform.system() == locked['platform']['system'], 'Unsupported OS'
    assert platform.machine().upper() == locked['platform']['machine'].upper(), 'Unsupported architecture'
    ids = ['W02-ENV-PLATFORM']
    versions = {}
    for name, tool in locked['tools'].items():
        path = Path(tool['path'])
        assert path.is_absolute() and path.is_file(), name + ': missing executable'
        assert hashlib.sha256(path.read_bytes()).hexdigest() == tool['sha256'], name + ': tool changed'
        argv = [str(path), *tool['version_argv']]
        if tool.get('interpreter'):
            argv.insert(0, locked['tools'][tool['interpreter']]['path'])
        result = subprocess.run(argv, capture_output=True, text=True, encoding='utf-8', timeout=20)
        assert result.returncode == 0 and result.stdout.strip() == tool['version_output'], name + ': version changed'
        versions[name] = result.stdout.strip()
        ids.append('W02-ENV-' + name.upper())
    print(json.dumps(dict(status='PASS', assertions=len(ids), assertion_ids=ids,
                          scope='DEVELOPMENT_ONLY', versions=versions)))


if __name__ == '__main__':
    try:
        main()
    except (AssertionError, OSError, subprocess.SubprocessError) as exc:
        print(json.dumps({'status': 'FAIL', 'assertions': 0, 'assertion_ids': [], 'error': str(exc)}))
        sys.exit(1)
