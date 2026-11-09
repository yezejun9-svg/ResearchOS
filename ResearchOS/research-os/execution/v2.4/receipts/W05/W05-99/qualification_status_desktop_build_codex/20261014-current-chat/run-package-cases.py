"""Exercise non-GUI registered Desktop cases against the assembled validator."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

SOURCE = Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/qualification-status-repair-20261014')
RAW = SOURCE / '.local/receipts/qualification-status-combined-20261014'
DEST = Path('C:/Users/yqyyds/.codex/researchos-resource-cache/normal-status-combined-5ddc0abb-20261014')
NODE = Path('C:/Users/yqyyds/AppData/Local/nvm/v24.9.0/node.exe')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    case = RAW / 'package-cases'
    case.mkdir(exist_ok=False)
    temp = case / 'temp'
    temp.mkdir()
    env = dict(os.environ)
    env.update(RESEARCHOS_DESKTOP_WIRE_ROOT=str(DEST / 'apps/desktop'),
               RESEARCHOS_DESKTOP_CASE_RECEIPT=str(case),
               RESEARCHOS_DESKTOP_ELECTRON='D:/作品集/ResearchOS/research-os/apps/desktop/node_modules/electron/dist/electron.exe',
               TEMP=str(temp), TMP=str(temp))
    argv = [str(NODE), '--test', '--test-concurrency=1',
            '--test-name-pattern=^(desktop-http|qualification-lane)/',
            'tests/ui/desktop/http-wire-boundary.test.mjs']
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    proc = subprocess.run(argv, cwd=SOURCE, env=env, capture_output=True, timeout=450)
    out, err = RAW / 'package-cases.stdout', RAW / 'package-cases.stderr'
    out.write_bytes(proc.stdout)
    err.write_bytes(proc.stderr)
    stdout = proc.stdout.decode('utf-8', errors='replace')
    counts = {}
    for key in ('tests', 'pass', 'fail', 'skipped', 'cancelled'):
        match = re.findall(r'^[#ℹ]\s+' + key + r'\s+(\d+)\s*$', stdout, re.M)
        counts[key] = int(match[0]) if len(match) == 1 else None
    row = {'schema': 'researchos.cp458-package-validator-cases.v1',
           'actualargv': argv, 'cwd': str(SOURCE), 'started_at': start,
           'ended_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'native_exit': proc.returncode, 'environment': {k: env[k] for k in
               ('RESEARCHOS_DESKTOP_WIRE_ROOT', 'RESEARCHOS_DESKTOP_CASE_RECEIPT',
                'RESEARCHOS_DESKTOP_ELECTRON', 'TEMP', 'TMP')},
           'stdout': {'path': str(out), 'bytes': out.stat().st_size, 'sha256': sha(out)},
           'stderr': {'path': str(err), 'bytes': err.stat().st_size, 'sha256': sha(err)},
           'counts': counts, 'renderer_GUI_cases_executed': False,
           'formal_increment': 0}
    with (RAW / 'package-cases.invocation.json').open('x', encoding='utf-8', newline='\n') as f:
        json.dump(row, f, ensure_ascii=False, indent=2)
        f.write('\n')
    if proc.returncode or counts != {'tests': 214, 'pass': 214, 'fail': 0, 'skipped': 0, 'cancelled': 0}:
        raise RuntimeError(f'package cases failed or roster changed: exit={proc.returncode} counts={counts}')
    print(json.dumps({'status': 'PACKAGE_VALIDATOR_CASES_PASSED', 'counts': counts}))

if __name__ == '__main__':
    main()
