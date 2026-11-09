"""Bounded package wire checks; no product host or GUI is launched."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path('D:/作品集/ResearchOS/research-os')
SOURCE = ROOT / '.local/worktrees/profile-result-build-20261014'
DEST = Path('C:/Users/yqyyds/.codex/researchos-resource-cache/normal-verifier-replacement-4f4023-20261015')
HERE = Path(__file__).resolve().parent
NODE = Path('C:/Users/yqyyds/AppData/Local/nvm/v24.9.0/node.exe')
GO = ROOT / '.local/tools/go1.27.1/go/bin/go.exe'
CONTROL = DEST / 'apps/desktop/resources/control/researchos-control.exe'
VERIFIER = DEST / 'apps/desktop/resources/control/runtime-verifier.exe'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def ref(path):
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': sha(path)}

def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')

def run(name, argv, cwd, env, expected, timeout=450):
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    try:
        p = subprocess.run(list(map(str, argv)), cwd=cwd, env=env, capture_output=True, timeout=timeout)
        code, stdout, stderr = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as e:
        code, stdout, stderr = 124, e.stdout or b'', e.stderr or b''
    out, err = HERE / (name + '.stdout'), HERE / (name + '.stderr')
    out.write_bytes(stdout)
    err.write_bytes(stderr)
    row = {'argv': list(map(str, argv)), 'cwd': str(cwd), 'started_at': started,
           'ended_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'native_exit': code,
           'expected_exit': expected, 'environment_allowlist': {k: env.get(k) for k in
              ('RESEARCHOS_DESKTOP_WIRE_ROOT', 'RESEARCHOS_DESKTOP_CASE_RECEIPT',
               'RESEARCHOS_DESKTOP_ELECTRON', 'TEMP', 'TMP')},
           'stdout': ref(out), 'stderr': ref(err)}
    write(HERE / (name + '.json'), row)
    if code != expected:
        raise RuntimeError(f'{name}: exit {code}, expected {expected}')
    return stdout

def main():
    if not (SOURCE / 'tests/ui/desktop/http-wire-boundary.test.mjs').is_file():
        raise RuntimeError('frozen profile test source missing')
    case = HERE / 'package-cases'
    case.mkdir(exist_ok=False)
    temp = case / 'temp'
    temp.mkdir()
    env = dict(os.environ)
    env.update(RESEARCHOS_DESKTOP_WIRE_ROOT=str(DEST / 'apps/desktop'),
               RESEARCHOS_DESKTOP_CASE_RECEIPT=str(case),
               RESEARCHOS_DESKTOP_ELECTRON=str(ROOT / 'apps/desktop/node_modules/electron/dist/electron.exe'),
               TEMP=str(temp), TMP=str(temp))
    raw = run('package-wire-214', [NODE, '--test', '--test-concurrency=1',
              '--test-name-pattern=^(desktop-http|qualification-lane)/',
              'tests/ui/desktop/http-wire-boundary.test.mjs'], SOURCE, env, 0)
    text = raw.decode('utf-8', 'replace')
    counts = {}
    for key in ('tests', 'pass', 'fail', 'skipped', 'cancelled'):
        found = re.findall(r'^[#ℹ]\s+' + key + r'\s+(\d+)\s*$', text, re.M)
        counts[key] = int(found[0]) if len(found) == 1 else None
    write(HERE / 'package-wire-summary.json', {'counts': counts, 'native_exit': 0,
           'source_test': ref(SOURCE / 'tests/ui/desktop/http-wire-boundary.test.mjs'),
           'package': str(DEST), 'formal_increment': 0})
    if counts != {'tests': 214, 'pass': 214, 'fail': 0, 'skipped': 0, 'cancelled': 0}:
        raise RuntimeError('package wire roster mismatch: ' + str(counts))
    run('verifier-no-pipes-rejected', [VERIFIER], DEST / 'apps/desktop', env, 2, 20)
    run('control-incomplete-replacement-rejected', [CONTROL, '--runtime-verifier-replacement'],
        DEST / 'apps/desktop', env, 2, 20)
    for name, exe in [('control', CONTROL), ('runtime-verifier', VERIFIER)]:
        raw = run(name + '-packaged-buildinfo', [GO, 'version', '-m', exe], SOURCE, env, 0, 30)
        stamp = raw.decode('utf-8', 'replace')
        if 'vcs.revision=4f4023c956f84d65743f39ce77d6c8899a21ada1' not in stamp or 'vcs.modified=false' not in stamp:
            raise RuntimeError(name + ' packaged VCS stamp mismatch')
    print(json.dumps({'status': 'BOUNDED_PACKAGE_SMOKE_PASS', 'counts': counts,
                      'no_real_host': True, 'formal_increment': 0}))

if __name__ == '__main__':
    main()
