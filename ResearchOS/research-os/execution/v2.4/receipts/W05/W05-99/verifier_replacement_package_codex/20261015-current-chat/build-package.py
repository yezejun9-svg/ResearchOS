"""Build the frozen 4f Core pair and compose the bounded Desktop replacement package."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path('D:/作品集/ResearchOS/research-os')
SOURCE = ROOT / '.local/worktrees/verifier-replacement-20261014'
BUILD = ROOT / '.local/builds/verifier-replacement-4f4023-20261015'
HERE = ROOT / 'execution/v2.4/receipts/W05/W05-99/verifier_replacement_package_codex/20261015-current-chat'
OLD = Path('C:/Users/yqyyds/.codex/researchos-resource-cache/normal-coding-profile-c8b7adab-20261014')
DEST = Path('C:/Users/yqyyds/.codex/researchos-resource-cache/normal-verifier-replacement-4f4023-20261015')
OLD_COMP = ROOT / 'execution/v2.4/receipts/W05/W05-99/coding_profile_desktop_build_codex/20261014-current-chat/composition.json'
OLD_FINAL = ROOT / 'execution/v2.4/receipts/W05/W05-99/coding_profile_desktop_build_codex/20261014-current-chat/FINAL-manifest.json'
SCOPE = ROOT / 'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp491/verifier-normal-package-scope.json'
REVIEW = ROOT / 'execution/v2.4/receipts/W05/W05-99/runtime_verifier_replacement_independent_review_codex/20261015-current-chat/REVIEW.md'
GO = ROOT / '.local/tools/go1.27.1/go/bin/go.exe'
COMMIT = '4f4023c956f84d65743f39ce77d6c8899a21ada1'
TREE = '3db13a15cc52b2b0bd75cae3452c66509a9f55c9'
CONTROL = 'apps/desktop/resources/control/researchos-control.exe'
VERIFIER = 'apps/desktop/resources/control/runtime-verifier.exe'
INSTALL = 'apps/desktop/resources/control/runtime-verifier-installation.json'
ENV_KEYS = ('GOTOOLCHAIN', 'GOENV', 'GOROOT', 'GOPATH', 'GOMODCACHE', 'GOCACHE', 'GOTMPDIR', 'GOPROXY', 'GOSUMDB', 'GOFLAGS', 'TEMP', 'TMP')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def ref(path):
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': sha(path)}

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')

def require(condition, why):
    if not condition:
        raise RuntimeError(why)

def run(name, args, env=None, cwd=SOURCE, timeout=600):
    argv = list(map(str, args))
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    try:
        result = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, timeout=timeout)
        exit_code, stdout, stderr = result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as err:
        exit_code, stdout, stderr = 124, err.stdout or b'', err.stderr or b''
    out, error = HERE / (name + '.stdout'), HERE / (name + '.stderr')
    out.write_bytes(stdout)
    error.write_bytes(stderr)
    row = {'argv': argv, 'cwd': str(cwd), 'started_at': started,
           'ended_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'native_exit': exit_code,
           'environment_allowlist': {key: env.get(key) for key in ENV_KEYS} if env else {},
           'stdout': ref(out), 'stderr': ref(error)}
    write(HERE / (name + '.json'), row)
    require(exit_code == 0, name + ' failed: ' + stderr.decode('utf-8', 'replace')[-500:])
    return stdout

def stream_json(raw):
    text = raw.decode('utf-8', 'replace')
    decoder = json.JSONDecoder()
    pos = 0
    while pos < len(text):
        while pos < len(text) and text[pos].isspace():
            pos += 1
        if pos < len(text):
            obj, pos = decoder.raw_decode(text, pos)
            yield obj

def main():
    require(not BUILD.exists() and not DEST.exists(), 'exclusive build/package path already exists')
    require(sha(SCOPE) == '491def288f03df983b227f1b647f74f77a98362187c9dc99f444d6fdc34dd4ad', 'scope changed')
    require(sha(REVIEW) == '1e21084a7b57d56d7e7e5f9ee26fe0ece6de3913bdf0d3a0a1f00d91d19793b2', 'review changed')
    require(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=SOURCE).decode().strip() == COMMIT, 'source commit changed')
    require(subprocess.check_output(['git', 'rev-parse', 'HEAD^{tree}'], cwd=SOURCE).decode().strip() == TREE, 'source tree changed')
    require(subprocess.check_output(['git', 'status', '--porcelain=v1', '--untracked-files=no'], cwd=SOURCE) == b'', 'source tracked dirty')
    require((SOURCE / 'apps/runtime-verifier/main_windows.go').is_file(), 'sparse verifier source missing')
    old_comp, old_final = json.loads(OLD_COMP.read_bytes()), json.loads(OLD_FINAL.read_bytes())
    require(old_comp['source_commit'].startswith('c8b7adab') and old_comp['core_source_commit'].startswith('a7ec7ebf')
            and old_comp['mu_source_commit'].startswith('8dfebe36'), 'baseline component provenance')
    old_rows = {row['path']: row for row in old_comp['package_files']}
    require(len(old_rows) == 58 and old_final['package']['member_count'] == 58, 'old inventory count')
    for rel, row in old_rows.items():
        path = OLD / rel
        require(path.is_file() and not path.is_symlink() and sha(path) == row['sha256'], 'old member drift: ' + rel)
    BUILD.mkdir(parents=True)
    (BUILD / 'go-cache').mkdir()
    (BUILD / 'go-tmp').mkdir()
    env = dict(os.environ)
    env.update(GOTOOLCHAIN='local', GOENV='off', GOROOT=str(GO.parent.parent),
               GOPATH=str(ROOT / '.local/tools/gopath'), GOMODCACHE=str(ROOT / '.local/tools/gopath/pkg/mod'),
               GOCACHE=str(BUILD / 'go-cache'), GOTMPDIR=str(BUILD / 'go-tmp'),
               GOPROXY='off', GOSUMDB='off', GOFLAGS='-buildvcs=true', TEMP=str(BUILD / 'go-tmp'), TMP=str(BUILD / 'go-tmp'))
    raw = run('go-list', [GO, 'list', '-deps', '-compiled', '-json', './apps/control', './apps/runtime-verifier'], env)
    paths = {SOURCE / 'go.mod', SOURCE / 'go.sum', GO}
    for item in stream_json(raw):
        directory = Path(item.get('Dir', ''))
        module = item.get('Module') or {}
        if module.get('GoMod'):
            paths.add(Path(module['GoMod']))
        if directory.is_dir():
            for key in ('GoFiles', 'CompiledGoFiles', 'CgoFiles', 'CFiles', 'CXXFiles', 'SFiles', 'SysoFiles', 'EmbedFiles'):
                for name in item.get(key, []):
                    p = Path(name)
                    paths.add(p if p.is_absolute() else directory / p)
    before = [{'path': str(p.resolve()), 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in sorted(paths) if p.is_file()]
    write(HERE / 'compiler-module-inputs.before.json', before)
    digest = hashlib.sha256(json.dumps(before, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    results = {}
    for key, package in [('control', './apps/control'), ('runtime-verifier', './apps/runtime-verifier')]:
        output = BUILD / (key + '.exe')
        run(key + '-build', [GO, 'build', '-mod=readonly', '-buildvcs=true', '-work', '-x', '-o', output, package], env)
        info = run(key + '-buildinfo', [GO, 'version', '-m', output], env).decode('utf-8', 'replace')
        require('vcs.revision=' + COMMIT in info and 'vcs.modified=false' in info, key + ' VCS stamp')
        results[key] = ref(output)
    after = [{**row, 'current_sha256': sha(Path(row['path']))} for row in before]
    write(HERE / 'compiler-module-inputs.after.json', after)
    require(all(x['sha256'] == x['current_sha256'] for x in after), 'compiler/module input drift')
    require(subprocess.check_output(['git', 'status', '--porcelain=v1', '--untracked-files=no'], cwd=SOURCE) == b'', 'source changed during build')
    write(HERE / 'build-result.json', {'source_commit': COMMIT, 'source_tree': TREE,
          'compiler': ref(GO), 'go_mod': ref(SOURCE / 'go.mod'), 'go_sum': ref(SOURCE / 'go.sum'),
          'input_count': len(before), 'input_digest': digest, 'drift': [], 'binaries': results})
    DEST.mkdir(parents=True)
    rows = []
    for rel, row in old_rows.items():
        if rel == INSTALL:
            continue
        src = BUILD / ('control.exe' if rel == CONTROL else 'runtime-verifier.exe') if rel in (CONTROL, VERIFIER) else OLD / rel
        target = DEST / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, target)
        require(sha(target) == sha(src), 'copy drift: ' + rel)
        rows.append({'path': rel, 'bytes': target.stat().st_size, 'sha256': sha(target),
                     'source': str(src), 'component': 'FRESH_CORE_4F' if rel in (CONTROL, VERIFIER) else row['component'],
                     'source_commit': COMMIT if rel in (CONTROL, VERIFIER) else row['source_commit']})
    install = json.loads((OLD / INSTALL).read_bytes())
    require(install['schema'] == 'researchos.runtime-verifier-installation.v1'
            and install['service_id'] == 'researchos.runtime-qualification-verifier.v1'
            and install['protocol'] == 'researchos.runtime-verifier/1' and install['arguments'] == [], 'loader contract changed')
    install.update(executable=str(DEST / VERIFIER), executable_hash='sha256:' + sha(DEST / VERIFIER), source_commit=COMMIT)
    manifest = DEST / INSTALL
    with manifest.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(install, f, ensure_ascii=False, indent=2)
        f.write('\n')
    rows.append({'path': INSTALL, 'bytes': manifest.stat().st_size, 'sha256': sha(manifest),
                 'source': str(HERE / 'build-package.py'), 'component': 'NEW_INSTALLATION_MANIFEST_4F', 'source_commit': COMMIT})
    require(len(rows) == 58 and len({x['path'] for x in rows}) == 58, 'new inventory count')
    require({p.relative_to(DEST).as_posix() for p in DEST.rglob('*') if p.is_file()} == set(old_rows), 'new filesystem inventory')
    same = sorted(rel for rel in old_rows if rel not in (CONTROL, VERIFIER, INSTALL))
    require(len(same) == 55 and all(sha(DEST / rel) == old_rows[rel]['sha256'] for rel in same), 'c8 or Mu asset drift')
    def eol(path):
        raw = path.read_bytes()
        return {'crlf': raw.count(b'\r\n'), 'lf': raw.count(b'\n'), 'nul': raw.count(b'\0')}
    inventory = [{**row, 'line_endings': eol(DEST / row['path'])} for row in sorted(rows, key=lambda x: x['path'])]
    write(HERE / 'package-inventory.json', {'package_root': str(DEST), 'member_count': len(rows),
           'unchanged_c8_member_count': len(same), 'unchanged_paths': same, 'files': inventory})
    write(HERE / 'composition.json', {'schema': 'researchos.verifier-replacement-package-composition/1',
           'source_commit': COMMIT, 'source_tree': TREE, 'baseline_package': str(OLD), 'package_root': str(DEST),
           'scope': ref(SCOPE), 'source_review': ref(REVIEW), 'old_composition': ref(OLD_COMP),
           'old_final': ref(OLD_FINAL), 'build': ref(HERE / 'build-result.json'),
           'inventory': ref(HERE / 'package-inventory.json'), 'installation_manifest': ref(manifest),
           'activation': 'NOT_STARTED', 'formal_increment': 0})
    print(json.dumps({'status': 'COMPOSED_AWAITING_ACL_AND_REVIEW', 'package_root': str(DEST),
                      'control_sha256': sha(DEST / CONTROL), 'verifier_sha256': sha(DEST / VERIFIER),
                      'manifest_sha256': sha(manifest), 'unchanged_members': len(same)}))

if __name__ == '__main__':
    main()
