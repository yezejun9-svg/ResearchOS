"""Build fresh Core binaries with source census, raw compiler commands, and VCS stamps."""
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
TREE = '5b54aa0b8b94cb8012413efd401dc417671b06de'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def put(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')

def stream_json(text):
    decoder = json.JSONDecoder()
    i = 0
    while i < len(text):
        while i < len(text) and text[i].isspace():
            i += 1
        if i >= len(text):
            break
        obj, i = decoder.raw_decode(text, i)
        yield obj

def main():
    if subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=SOURCE, text=True).strip() != COMMIT:
        raise RuntimeError('source HEAD changed')
    if subprocess.check_output(['git', 'rev-parse', 'HEAD^{tree}'], cwd=SOURCE, text=True).strip() != TREE:
        raise RuntimeError('source tree changed')
    if subprocess.check_output(['git', 'status', '--porcelain=v1'], cwd=SOURCE) != b'':
        raise RuntimeError('source dirty')
    result = json.loads((RAW / 'result.json').read_bytes())
    if result['status'] != 'BUILT_NOT_TESTED' or result['drift']:
        raise RuntimeError('validator input drift')
    env = dict(os.environ)
    env.update(GOTOOLCHAIN='local', GOENV='off', GOROOT=str(GO.parent.parent),
               GOPATH='D:/作品集/ResearchOS/research-os/.local/tools/gopath',
               GOMODCACHE='D:/作品集/ResearchOS/research-os/.local/tools/gopath/pkg/mod',
               GOCACHE=str(BUILD / 'go-cache'), GOTMPDIR=str(BUILD / 'go-tmp'),
               GOPROXY='off', GOSUMDB='off')
    def run(name, argv, timeout=600):
        started = datetime.datetime.now(datetime.timezone.utc).isoformat()
        proc = subprocess.run([str(x) for x in argv], cwd=SOURCE, env=env,
                              capture_output=True, timeout=timeout)
        out, err = RAW / (name + '.stdout'), RAW / (name + '.stderr')
        out.write_bytes(proc.stdout)
        err.write_bytes(proc.stderr)
        row = {'actualargv': [str(x) for x in argv], 'cwd': str(SOURCE),
               'started_at': started, 'ended_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'native_exit': proc.returncode,
               'stdout': {'path': str(out), 'bytes': out.stat().st_size, 'sha256': sha(out)},
               'stderr': {'path': str(err), 'bytes': err.stat().st_size, 'sha256': sha(err)},
               'environment': {k: env.get(k) for k in ('GOTOOLCHAIN', 'GOENV', 'GOROOT',
                                'GOPATH', 'GOMODCACHE', 'GOCACHE', 'GOTMPDIR', 'GOPROXY', 'GOSUMDB')}}
        put(RAW / (name + '.invocation.json'), row)
        if proc.returncode:
            raise RuntimeError(f'{name} native exit {proc.returncode}')
        return proc.stdout.decode('utf-8', errors='replace')
    inventory = list(stream_json(run('core-go-list', [GO, 'list', '-deps', '-compiled', '-json',
                                                    './apps/control', './apps/runtime-verifier'])))
    paths = {SOURCE / 'go.mod', SOURCE / 'go.sum'}
    for item in inventory:
        module = item.get('Module') or {}
        if module.get('GoMod'):
            paths.add(Path(module['GoMod']))
        directory = Path(item.get('Dir', ''))
        if not directory.is_dir():
            continue
        paths.update(directory.glob('*.go'))
        for field in ('GoFiles', 'CompiledGoFiles', 'CgoFiles', 'CFiles', 'CXXFiles',
                      'MFiles', 'HFiles', 'FFiles', 'SFiles', 'SwigFiles', 'SwigCXXFiles',
                      'SysoFiles', 'EmbedFiles', 'TestEmbedFiles', 'XTestEmbedFiles'):
            for name in item.get(field, []):
                p = Path(name)
                paths.add(p if p.is_absolute() else directory / p)
    paths.update(p for p in (GO.parent.parent / 'pkg/tool').rglob('*') if p.is_file())
    before = [{'path': str(p.resolve()), 'sha256': sha(p), 'bytes': p.stat().st_size}
              for p in sorted(paths) if p.is_file()]
    put(RAW / 'core-inputs.before.json', before)
    bound = hashlib.sha256(json.dumps(before, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    for name, package in (('core-control', './apps/control'),
                          ('core-runtime-verifier', './apps/runtime-verifier')):
        binary = BUILD / (name + '.exe')
        if binary.exists():
            raise RuntimeError('binary already exists: ' + name)
        run(name + '-build', [GO, 'build', '-mod=readonly', '-buildvcs=true', '-work', '-x',
                             '-o', binary, package])
        stamp = run(name + '-go-version-m', [GO, 'version', '-m', binary])
        if 'vcs.revision=' + COMMIT not in stamp or 'vcs.modified=false' not in stamp:
            raise RuntimeError('VCS stamp mismatch: ' + name)
    validator = BUILD / 'apps/desktop/resources/client-wire/researchos-client-wire-validator.exe'
    stamp = run('validator-go-version-m', [GO, 'version', '-m', validator])
    if 'vcs.revision=' + COMMIT not in stamp or 'vcs.modified=false' not in stamp:
        raise RuntimeError('validator VCS stamp mismatch')
    suite = run('validator-suite', [BUILD / 'validator.test.exe', '-test.v'])
    top = re.findall(r'^--- PASS: ([^\s]+)', suite, re.M)
    if not suite.rstrip().endswith('PASS') or not top or '--- FAIL:' in suite:
        raise RuntimeError('validator suite failed')
    after = [{**row, 'current_sha256': sha(Path(row['path']))} for row in before]
    drift = [x for x in after if x['sha256'] != x['current_sha256']]
    put(RAW / 'core-inputs.after.json', after)
    put(RAW / 'core-result.json', {'schema': 'researchos.cp465-core-build-result.v1',
                                  'candidate_commit': COMMIT, 'tree': TREE,
                                  'input_count': len(before), 'input_digest': bound,
                                  'drift': drift,
                                  'control_binary_sha256': sha(BUILD / 'core-control.exe'),
                                  'runtime_verifier_binary_sha256': sha(BUILD / 'core-runtime-verifier.exe'),
                                  'validator_binary_sha256': sha(validator),
                                  'validator_top_level_pass_count': len(top),
                                  'validator_all_pass_markers': suite.count('--- PASS:'),
                                  'native_exit': 0})
    if drift:
        raise RuntimeError('Core input drift')
    print(json.dumps({'status': 'FRESH_CORE_AND_VALIDATOR_PASSED', 'core_input_count': len(before),
                      'core_input_digest': bound, 'validator_top_level_pass': len(top),
                      'validator_all_pass_markers': suite.count('--- PASS:')}))

if __name__ == '__main__':
    main()
