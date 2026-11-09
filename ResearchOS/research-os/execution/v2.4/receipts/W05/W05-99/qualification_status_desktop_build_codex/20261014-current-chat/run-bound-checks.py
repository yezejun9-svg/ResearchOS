"""Record native validator VCS and suite exits for the frozen candidate."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

SOURCE = Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/qualification-status-repair-20261014')
BUILD = SOURCE / '.local/builds/qualification-status-combined-20261014'
RAW = SOURCE / '.local/receipts/qualification-status-combined-20261014'
GO = Path('D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/bin/go.exe')
CANDIDATE = '5ddc0abb8c6d95e9ca071a4eb41a7e12b8559456'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(name, argv, cwd, env):
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    proc = subprocess.run([str(x) for x in argv], cwd=cwd, env=env, capture_output=True, timeout=240)
    out, err = RAW / (name + '.stdout'), RAW / (name + '.stderr')
    out.write_bytes(proc.stdout)
    err.write_bytes(proc.stderr)
    row = {'argv': [str(x) for x in argv], 'cwd': str(cwd), 'started_at': start,
           'ended_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'native_exit': proc.returncode,
           'stdout': {'path': str(out), 'sha256': sha(out), 'bytes': out.stat().st_size},
           'stderr': {'path': str(err), 'sha256': sha(err), 'bytes': err.stat().st_size},
           'environment': {k: env.get(k) for k in ('GOTOOLCHAIN', 'GOENV', 'GOROOT', 'GOPATH',
                             'GOMODCACHE', 'GOCACHE', 'GOTMPDIR', 'GOPROXY', 'GOSUMDB')}}
    with (RAW / (name + '.invocation.json')).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(row, f, ensure_ascii=False, indent=2)
        f.write('\n')
    if proc.returncode:
        raise RuntimeError(f'{name} exited {proc.returncode}')
    return proc.stdout.decode('utf-8', errors='replace')

def main():
    if subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=SOURCE, text=True).strip() != CANDIDATE:
        raise RuntimeError('source head changed')
    result = json.loads((RAW / 'result.json').read_bytes())
    if result['status'] != 'BUILT_NOT_TESTED' or result['drift']:
        raise RuntimeError('bound build drift')
    env = dict(os.environ)
    env.update(GOTOOLCHAIN='local', GOENV='off', GOROOT=str(GO.parent.parent),
               GOPATH='D:/作品集/ResearchOS/research-os/.local/tools/gopath',
               GOMODCACHE='D:/作品集/ResearchOS/research-os/.local/tools/gopath/pkg/mod',
               GOCACHE=str(BUILD / 'go-cache'), GOTMPDIR=str(BUILD / 'go-tmp'),
               GOPROXY='off', GOSUMDB='off')
    binary = BUILD / 'apps/desktop/resources/client-wire/researchos-client-wire-validator.exe'
    stamp = run('validator-go-version-m', [GO, 'version', '-m', binary], SOURCE, env)
    if 'vcs.revision=' + CANDIDATE not in stamp or 'vcs.modified=false' not in stamp:
        raise RuntimeError('validator source VCS stamp mismatch')
    suite = run('validator-suite', [BUILD / 'validator.test.exe', '-test.v'],
                SOURCE / 'apps/desktop/validator', env)
    if not suite.rstrip().endswith('PASS') or '--- PASS:' not in suite or '--- FAIL:' in suite:
        raise RuntimeError('validator suite did not pass')
    print(json.dumps({'status': 'VALIDATOR_SUITE_PASSED', 'binary_sha256': sha(binary),
                      'test_top_level_pass_count': suite.count('--- PASS:')}))

if __name__ == '__main__':
    main()
