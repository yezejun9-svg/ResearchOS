"""Call the frozen Source replacementRead through a test overlay, with only package files."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path('D:/作品集/ResearchOS/research-os')
SOURCE = ROOT / '.local/worktrees/verifier-replacement-20261014'
BUILD = ROOT / '.local/builds/verifier-replacement-4f4023-20261015'
HERE = Path(__file__).resolve().parent
DEST = Path('C:/Users/yqyyds/.codex/researchos-resource-cache/normal-verifier-replacement-4f4023-20261015')
GO = ROOT / '.local/tools/go1.27.1/go/bin/go.exe'
MANIFEST = DEST / 'apps/desktop/resources/control/runtime-verifier-installation.json'
EXE = DEST / 'apps/desktop/resources/control/runtime-verifier.exe'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def ref(path):
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': sha(path)}

def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')

def main():
    overlay = BUILD / 'overlay.json'
    source_test = BUILD / 'replacement_package_probe_windows_test.go'
    if not overlay.is_file() or not source_test.is_file():
        raise RuntimeError('probe overlay missing')
    if subprocess.check_output(['git', 'status', '--porcelain=v1', '--untracked-files=no'], cwd=SOURCE) != b'':
        raise RuntimeError('source dirty')
    env = dict(os.environ)
    env.update(GOTOOLCHAIN='local', GOENV='off', GOROOT=str(GO.parent.parent),
               GOPATH=str(ROOT / '.local/tools/gopath'), GOMODCACHE=str(ROOT / '.local/tools/gopath/pkg/mod'),
               GOCACHE=str(BUILD / 'go-cache'), GOTMPDIR=str(BUILD / 'go-tmp'),
               GOPROXY='off', GOSUMDB='off', GOFLAGS='-buildvcs=true',
               TEMP=str(BUILD / 'go-tmp'), TMP=str(BUILD / 'go-tmp'),
               RESEARCHOS_REPLACEMENT_PACKAGE_MANIFEST=str(MANIFEST),
               RESEARCHOS_REPLACEMENT_PACKAGE_MANIFEST_SHA=sha(MANIFEST),
               RESEARCHOS_REPLACEMENT_PACKAGE_EXE=str(EXE),
               RESEARCHOS_REPLACEMENT_PACKAGE_EXE_SHA=sha(EXE))
    argv = [str(GO), 'test', '-overlay', str(overlay), '-run', '^TestReplacementPackageNativeRead$',
            '-count=1', '-v', './internal/host']
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    try:
        proc = subprocess.run(argv, cwd=SOURCE, env=env, capture_output=True, timeout=240)
        code, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as e:
        code, stdout, stderr = 124, e.stdout or b'', e.stderr or b''
    out, err = HERE / 'native-source-read.stdout', HERE / 'native-source-read.stderr'
    out.write_bytes(stdout)
    err.write_bytes(stderr)
    receipt = {'schema': 'researchos.verifier-replacement-native-source-read/1',
               'argv': argv, 'cwd': str(SOURCE), 'started_at': started,
               'ended_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'native_exit': code,
               'environment_allowlist': {k: env[k] for k in ('GOTOOLCHAIN', 'GOENV', 'GOROOT', 'GOPATH',
                   'GOMODCACHE', 'GOCACHE', 'GOTMPDIR', 'GOPROXY', 'GOSUMDB', 'GOFLAGS',
                   'RESEARCHOS_REPLACEMENT_PACKAGE_MANIFEST', 'RESEARCHOS_REPLACEMENT_PACKAGE_MANIFEST_SHA',
                   'RESEARCHOS_REPLACEMENT_PACKAGE_EXE', 'RESEARCHOS_REPLACEMENT_PACKAGE_EXE_SHA')},
               'overlay': ref(overlay), 'probe_source': ref(source_test),
               'manifest': ref(MANIFEST), 'exe': ref(EXE), 'stdout': ref(out), 'stderr': ref(err),
               'formal_increment': 0}
    write(HERE / 'native-source-read.json', receipt)
    if code or b'--- PASS: TestReplacementPackageNativeRead' not in stdout:
        raise RuntimeError('frozen replacementRead package probe failed')
    if subprocess.check_output(['git', 'status', '--porcelain=v1', '--untracked-files=no'], cwd=SOURCE) != b'':
        raise RuntimeError('source changed')
    write(HERE / 'SUPPLEMENT-manifest.json', {'schema': 'researchos.verifier-replacement-package-supplement/1',
          'prior_final': ref(HERE / 'FINAL-manifest.json'), 'native_source_read': ref(HERE / 'native-source-read.json'),
          'status': 'FROZEN_SOURCE_REPLACEMENT_READ_BOTH_NEW_FILES_PASS',
          'scope': 'isolated new package, no product DataRoot/Host', 'formal_increment': 0})
    print(json.dumps({'status': 'FROZEN_SOURCE_REPLACEMENT_READ_BOTH_NEW_FILES_PASS',
                      'supplement_sha256': sha(HERE / 'SUPPLEMENT-manifest.json')}))

if __name__ == '__main__':
    main()
