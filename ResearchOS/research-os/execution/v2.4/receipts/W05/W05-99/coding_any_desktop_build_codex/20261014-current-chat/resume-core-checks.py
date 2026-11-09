"""Preserve failed suite and finish Core census after fixing only the test cwd."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

SOURCE = Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/coding-any-combined-build-20261014')
BUILD = SOURCE / '.local/builds/coding-any-combined-20261014'
RAW = SOURCE / '.local/receipts/coding-any-combined-20261014'
GO = Path('D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/bin/go.exe')
COMMIT = 'a7ec7ebf2d53848ea163b6115667b3e3761a6bd2'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def put(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')

def main():
    first = json.loads((RAW / 'validator-suite.invocation.json').read_bytes())
    if first['native_exit'] != 1 or 'main_test.go:26: open ../../../tests/contracts/fixtures/' not in (RAW / 'validator-suite.stdout').read_text(encoding='utf-8'):
        raise RuntimeError('first failed suite is not the known cwd error')
    env = dict(os.environ)
    env.update(GOTOOLCHAIN='local', GOENV='off', GOROOT=str(GO.parent.parent),
               GOPATH='D:/作品集/ResearchOS/research-os/.local/tools/gopath',
               GOMODCACHE='D:/作品集/ResearchOS/research-os/.local/tools/gopath/pkg/mod',
               GOCACHE=str(BUILD / 'go-cache'), GOTMPDIR=str(BUILD / 'go-tmp'),
               GOPROXY='off', GOSUMDB='off')
    cwd = SOURCE / 'apps/desktop/validator'
    argv = [str(BUILD / 'validator.test.exe'), '-test.v']
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    proc = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, timeout=240)
    out, err = RAW / 'validator-suite-corrected.stdout', RAW / 'validator-suite-corrected.stderr'
    out.write_bytes(proc.stdout)
    err.write_bytes(proc.stderr)
    row = {'actualargv': argv, 'cwd': str(cwd), 'started_at': start,
           'ended_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'native_exit': proc.returncode,
           'stdout': {'path': str(out), 'bytes': out.stat().st_size, 'sha256': sha(out)},
           'stderr': {'path': str(err), 'bytes': err.stat().st_size, 'sha256': sha(err)},
           'environment': {k: env.get(k) for k in ('GOTOOLCHAIN', 'GOENV', 'GOROOT',
                            'GOPATH', 'GOMODCACHE', 'GOCACHE', 'GOTMPDIR', 'GOPROXY', 'GOSUMDB')},
           'prior_failed_attempt': str(RAW / 'validator-suite.invocation.json')}
    put(RAW / 'validator-suite-corrected.invocation.json', row)
    suite = proc.stdout.decode('utf-8', errors='replace')
    top = re.findall(r'^--- PASS: ([^\s]+)', suite, re.M)
    if proc.returncode or not suite.rstrip().endswith('PASS') or len(top) != 4 or '--- FAIL:' in suite:
        raise RuntimeError('corrected suite failed')
    before = json.loads((RAW / 'core-inputs.before.json').read_bytes())
    after = [{**item, 'current_sha256': sha(Path(item['path']))} for item in before]
    drift = [item for item in after if item['sha256'] != item['current_sha256']]
    put(RAW / 'core-inputs.after.json', after)
    bound = hashlib.sha256(json.dumps(before, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    control, verifier = BUILD / 'core-control.exe', BUILD / 'core-runtime-verifier.exe'
    validator = BUILD / 'apps/desktop/resources/client-wire/researchos-client-wire-validator.exe'
    put(RAW / 'core-result.json', {'schema': 'researchos.cp465-core-build-result.v1',
                                  'candidate_commit': COMMIT,
                                  'tree': '5b54aa0b8b94cb8012413efd401dc417671b06de',
                                  'input_count': len(before), 'input_digest': bound,
                                  'drift': drift, 'control_binary_sha256': sha(control),
                                  'runtime_verifier_binary_sha256': sha(verifier),
                                  'validator_binary_sha256': sha(validator),
                                  'validator_top_level_pass_count': len(top),
                                  'validator_all_pass_markers': suite.count('--- PASS:'),
                                  'first_suite_native_exit': first['native_exit'],
                                  'corrected_suite_native_exit': proc.returncode,
                                  'native_exit': 0})
    if drift:
        raise RuntimeError('Core input drift')
    print(json.dumps({'status': 'FRESH_CORE_AND_VALIDATOR_PASSED', 'core_input_count': len(before),
                      'core_input_digest': bound, 'validator_top_level_pass': len(top),
                      'validator_all_pass_markers': suite.count('--- PASS:')}))

if __name__ == '__main__':
    main()
