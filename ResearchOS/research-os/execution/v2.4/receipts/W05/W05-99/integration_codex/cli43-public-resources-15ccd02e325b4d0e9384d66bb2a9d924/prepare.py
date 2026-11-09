"""Root fresh public resource freeze only; no helpers, Go, SQL, HTTP or credentials."""
import hashlib
import json
import os
import subprocess
import sys
import traceback
from pathlib import Path

ROOT = Path('D:/作品集/ResearchOS/research-os')
OUT = Path(__file__).absolute().parent
SOURCE = 'a510dbef4a7e08fb5c428df44c39b133f3ffa856'
PINNED = {
    'execution/v2.4/checkpoint.json': 'f79c2760b50729a62110aed4dd2ca012f08e7ee786351c9b4c30354a30fd1ca9',
    'execution/v2.4/path_ownership.json': '9b2a8a037e12e9d615037c560c2d5cfe3c3ccc4bd3f2fad98dbf4fff464211cf',
    'execution/v2.4/step_state.json': 'fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149',
    'execution/v2.4/commands.json': 'b357f60a9463b1a7504487bd8debf2b55f87f35938a26fe68a495aa834794129',
    'execution/toolchains/locked.json': '0958d3f313e8d09d471521787a2b8b9480a17a91d6e4aa722393741dcbd8e663',
    'execution/v2.4/receipts/W05/W05-99/integration_codex/session-list-closedcopy-root-replay-draft/gate-launcher-preparation-d58b6cfd52a44f0f9cee84344abda03d/controller_runtime_resources.json': '5ba6aa64a86f3e3cd7fe8be1393e569dcf13ad36556643e9e59d0190f1569eee',
}
GO = ROOT / '.local/tools/go1.27.1/go'
MODULES = ROOT / '.local/gopath/pkg/mod'
GIT = Path('C:/Program Files/Git')
CAPTURE = ROOT / 'execution/v2.4/receipts/W13/W13-03/desktop_go3_os_capture_revision_codex/01fc890602df43b89935fdbef4424137/actual-once/inner.owned-result.json'
PUBLIC_ENV = {'SystemRoot': os.environ['SystemRoot'], 'WINDIR': os.environ['WINDIR'],
              'ComSpec': os.environ['ComSpec'], 'PATH': str(GIT / 'cmd') + ';' + os.environ['SystemRoot'] + '/System32',
              'PATHEXT': '.COM;.EXE;.BAT;.CMD'}

def need(ok, message):
    if not ok:
        raise RuntimeError(message)

def pin(path):
    p = Path(path).absolute()
    h = hashlib.sha256()
    size = 0
    with p.open('rb') as f:
        while b := f.read(1048576):
            h.update(b)
            size += len(b)
    return {'path': str(p), 'sha256': h.hexdigest(), 'bytes': size}

def save(name, value):
    with (OUT / name).open('xb') as f:
        f.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))

def doc(path):
    return json.loads(Path(path).read_bytes().decode('utf-8'))

def regular(path):
    p = Path(path).absolute()
    for q in [p] + list(p.parents):
        if os.path.lexists(q):
            info = q.lstat()
            need(not q.is_symlink() and not getattr(info, 'st_file_attributes', 0) & 0x400,
                 'Public root contains reparse/symlink: ' + str(q))
    need(p.is_file(), 'Expected regular public file: ' + str(p))
    return p

def files(root):
    root = Path(root).absolute()
    need(root.is_dir(), 'Public root missing: ' + str(root))
    result = []
    for directory, dirs, names in os.walk(root, followlinks=False):
        for name in dirs + names:
            p = Path(directory) / name
            info = p.lstat()
            need(not p.is_symlink() and not getattr(info, 'st_file_attributes', 0) & 0x400,
                 'Public inventory contains reparse/symlink: ' + str(p))
        result.extend(Path(directory) / name for name in names)
    return sorted(result, key=lambda p: str(p).casefold())

def git_read(label, argv, tool):
    env = dict(PUBLIC_ENV)
    env.update(GIT_OPTIONAL_LOCKS='0', GIT_NO_REPLACE_OBJECTS='1',
               GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
    save(label + '.request.json', {'argv': [tool] + argv, 'cwd': str(ROOT),
         'environment': env, 'timeout_seconds': 30, 'read_only': True})
    r = subprocess.run([tool] + argv, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, timeout=30, check=False)
    for name, raw in [('stdout', r.stdout), ('stderr', r.stderr)]:
        with (OUT / (label + '.' + name + '.raw')).open('xb') as f:
            f.write(raw)
    save(label + '.invocation.json', {'actual_native_exit': r.returncode,
         'automatic_retry': False, 'counter_reset': False,
         'stdout_ref': pin(OUT / (label + '.stdout.raw')),
         'stderr_ref': pin(OUT / (label + '.stderr.raw')),
         'Windows_Job_or_DLL_lifecycle_qualification': False})
    need(r.returncode == 0, 'Read-only Git failed: ' + label)
    return r.stdout

def main():
    need(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode, 'Use -I -S -X utf8')
    sys.dont_write_bytecode = True
    save('started.json', {'actor': 'codex:/root', 'purpose': 'fresh_public_resource_freeze',
         'source_commit': SOURCE, 'product_execution': False, 'same_input_retry': False})
    before = [pin(ROOT / p) for p in PINNED]
    need(all(x['sha256'] == PINNED[Path(x['path']).relative_to(ROOT).as_posix()] for x in before),
         'Canonical/tool/resource basis changed before freeze')
    tools = doc(ROOT / 'execution/toolchains/locked.json')['tools']
    for name in ['python', 'go', 'git']:
        need(pin(regular(tools[name]['path']))['sha256'] == tools[name]['sha256'], 'Tool lock mismatch: ' + name)
    need(Path(sys.executable).resolve() == Path(tools['python']['path']).resolve(), 'Actual Python mismatch')
    cp, ow = doc(ROOT / 'execution/v2.4/checkpoint.json'), doc(ROOT / 'execution/v2.4/path_ownership.json')
    need([cp['revision'], ow['revision'], len(cp['failure_counters'])] == [324, 152, 430], 'Unexpected canonical tuple')
    head = git_read('git-head', ['rev-parse', 'HEAD'], tools['git']['path'])
    status = git_read('git-status', ['status', '--porcelain=v1', '--untracked-files=no'], tools['git']['path'])
    index = git_read('git-index', ['diff', '--cached', '--name-only'], tools['git']['path'])
    need(head.decode('ascii').strip() == cp['head'] == SOURCE and not index, 'Main HEAD/index changed')
    need(hashlib.sha256(status).hexdigest() == 'e03849874f27dcf3b079cb84c9bae69ad97311118da47c3122a5a9b32b9611b4',
         'Protected tracked status changed')
    roots = [{'path': str(p), 'files': [pin(q) for q in files(p)]} for p in [GO, MODULES, GIT]]
    compiler_files = {x['path']: x for r in roots for x in r['files']}
    images = [pin(GO / 'bin/go.exe')] + [pin(p) for p in files(GO / 'pkg/tool/windows_amd64') if p.suffix.lower() == '.exe']
    need(0 < len(images) <= 62, 'Finite compiler image inventory')
    compiler = {'schema': 'researchos.current43-public-compiler-resources.v1',
         'actor': 'codex:/root', 'source_commit': SOURCE, 'files': [compiler_files[p] for p in sorted(compiler_files)],
         'complete_public_roots': roots, 'compiler_images': images, 'GOROOT': str(GO),
         'GOPATH': str(ROOT / '.local/gopath'), 'GOMODCACHE': str(MODULES),
         'actual_compile_graph': None, 'actual_compiler_or_cases': 'NOT_RUN',
         'restriction': 'Public installed tool/module trees only. Future Go graph/WORK are captured separately; no prior executable/cache/graph reuse.'}
    save('compiler-resources.json', compiler)
    old_runtime = doc(ROOT / list(PINNED)[-1])
    runtime_paths = {str(regular(x['path'])) for x in old_runtime['files']}
    captured = doc(CAPTURE)['result']['debug_capture']['modules']
    os_sources = []
    for row in captured:
        p = row['path_from_actual_file_handle']
        if p.startswith('\\\\?\\'):
            p = p[4:]
        p = Path(p)
        if p.is_relative_to(Path(os.environ['SystemRoot'])):
            current = pin(regular(p))
            need(row['before'] == row['after'] == {k: current[k] for k in ['sha256', 'bytes']},
                 'Prior actually loaded OS file changed')
            runtime_paths.add(str(p.absolute()))
            os_sources.append(current)
    runtime_rows = [pin(p) for p in sorted(runtime_paths)]
    save('runtime-resources.json', {'schema': 'researchos.cli43-public-runtime-resources.v1',
         'actor': 'codex:/root', 'files': runtime_rows, 'old_basis_ref': before[-1],
         'actual_Go3_capture_basis_ref': pin(CAPTURE), 'additional_actual_OS_paths': os_sources,
         'helper_imports_or_DLL_calls': 0, 'point_in_time_only': True, 'Python_lifecycle_proof': False,
         'future_actual_module_observation': 'Must reject any unpinned actual Python/OS input; no guessed DLL names.'})
    drift = []
    for r in roots:
        actual = [pin(p) for p in files(r['path'])]
        if actual != r['files']:
            drift.append({'root': r['path'], 'expected': r['files'], 'actual': actual})
    runtime_after = [pin(x['path']) for x in runtime_rows]
    need(not drift and runtime_after == runtime_rows, 'Public resources changed during freeze')
    after = [pin(ROOT / p) for p in PINNED]
    need(after == before, 'Canonical/basis bytes changed during freeze')
    save('audit.json', {'schema': 'researchos.cli43-fresh-public-resource-preparation.v1',
         'actor': 'codex:/root', 'current': [324, 152, 430], 'source_commit': SOURCE,
         'before_refs': before, 'after_refs': after, 'before_after_drift': 0,
         'main_git': {'head': SOURCE, 'status_sha256': hashlib.sha256(status).hexdigest(),
              'status_bytes': len(status), 'status_rows': len(status.splitlines()), 'deleted_rows': 11, 'index_empty': True},
         'public_environment': PUBLIC_ENV, 'compiler_resources_ref': pin(OUT / 'compiler-resources.json'),
         'runtime_resources_ref': pin(OUT / 'runtime-resources.json'),
         'public_root_counts': [len(r['files']) for r in roots], 'compiler_image_count': len(images),
         'runtime_file_count': len(runtime_rows), 'actual_compile_graph': None,
         'canonical_source_writes': 0, 'readonly_Git_native_exits': [0, 0, 0],
         'Go_SQL_HTTP_helper_DLL_model_credentials_calls': 0, 'execution_authorized': False,
         'current43_cases': 'NOT_RUN', 'formal_increment': 0, 'goal_complete': False})
    print(json.dumps({'status': 'PUBLIC_RESOURCE_FREEZE_CLOSED_PREPARATION_ONLY',
          'audit_ref': pin(OUT / 'audit.json'), 'root_counts': [len(r['files']) for r in roots],
          'runtime_files': len(runtime_rows)}, ensure_ascii=False))

if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        failure = {'error': repr(error), 'traceback': traceback.format_exc(),
                   'actual_unobserved_native_exit': None, 'automatic_retry': False, 'counter_reset': False}
        if not (OUT / 'failure.json').exists():
            save('failure.json', failure)
        sys.stderr.write(json.dumps(failure, ensure_ascii=False) + '\n')
        raise
