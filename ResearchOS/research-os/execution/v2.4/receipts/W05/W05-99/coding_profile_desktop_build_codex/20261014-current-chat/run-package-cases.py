"""Run the registered non-GUI Desktop cases against the new package."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path('D:/作品集/ResearchOS/research-os')
SOURCE = ROOT / '.local/worktrees/profile-result-build-20261014'
DEST = Path('C:/Users/yqyyds/.codex/researchos-resource-cache/normal-coding-profile-c8b7adab-20261014')
NODE = Path('C:/Users/yqyyds/AppData/Local/nvm/v24.9.0/node.exe')
HERE = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    case = HERE / 'package-cases'
    case.mkdir(exist_ok=False)
    temp = case / 'temp'
    temp.mkdir()
    env = dict(os.environ)
    env.update(RESEARCHOS_DESKTOP_WIRE_ROOT=str(DEST / 'apps/desktop'),
               RESEARCHOS_DESKTOP_CASE_RECEIPT=str(case),
               RESEARCHOS_DESKTOP_ELECTRON=str(ROOT / 'apps/desktop/node_modules/electron/dist/electron.exe'),
               TEMP=str(temp), TMP=str(temp))
    argv = [str(NODE), '--test', '--test-concurrency=1',
            '--test-name-pattern=^(desktop-http|qualification-lane)/',
            'tests/ui/desktop/http-wire-boundary.test.mjs']
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        proc = subprocess.run(argv, cwd=SOURCE, env=env, capture_output=True, timeout=450)
        code, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as error:
        code, stdout, stderr = 124, error.stdout or b'', error.stderr or b''
    out, err = HERE / 'package-cases.stdout', HERE / 'package-cases.stderr'
    out.write_bytes(stdout)
    err.write_bytes(stderr)
    text = stdout.decode('utf-8', errors='replace')
    counts = {}
    for key in ('tests', 'pass', 'fail', 'skipped', 'cancelled'):
        matches = re.findall(r'^[#ℹ]\s+' + key + r'\s+(\d+)\s*$', text, re.M)
        counts[key] = int(matches[0]) if len(matches) == 1 else None
    receipt = {'schema': 'researchos.cp477-package-validator-cases/1',
               'actualargv': argv, 'cwd': str(SOURCE), 'started_at': start,
               'ended_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'native_exit': code,
               'environment': {key: env[key] for key in
                   ('RESEARCHOS_DESKTOP_WIRE_ROOT', 'RESEARCHOS_DESKTOP_CASE_RECEIPT',
                    'RESEARCHOS_DESKTOP_ELECTRON', 'TEMP', 'TMP')},
               'stdout': {'path': str(out), 'bytes': out.stat().st_size, 'sha256': sha(out)},
               'stderr': {'path': str(err), 'bytes': err.stat().st_size, 'sha256': sha(err)},
               'counts': counts, 'renderer_GUI_cases_executed': False, 'formal_increment': 0}
    path = HERE / 'package-cases.invocation.json'
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    if code or counts != {'tests': 214, 'pass': 214, 'fail': 0, 'skipped': 0, 'cancelled': 0}:
        raise RuntimeError(f'package cases failed or roster changed: exit={code} counts={counts}')
    print(json.dumps({'status': 'PACKAGE_VALIDATOR_CASES_PASSED', 'counts': counts}))

if __name__ == '__main__':
    main()
