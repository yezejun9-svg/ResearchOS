"""Assemble a fixed-source Desktop candidate from the repository's bound build."""
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path('D:/作品集/ResearchOS/research-os')
SOURCE = Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/coding-any-combined-build-20261014')
BUILD = SOURCE / '.local/builds/coding-any-combined-20261014'
RAW = SOURCE / '.local/receipts/coding-any-combined-20261014'
OLD = Path('C:/Users/yqyyds/.codex/researchos-resource-cache/normal-status-combined-5ddc0abb-20261014')
DEST = Path('C:/Users/yqyyds/.codex/researchos-resource-cache/normal-coding-any-a7ec7ebf-20261014')
HERE = Path(__file__).resolve().parent
SCOPE = ROOT / 'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261014-current-chat/continuation-cp465/package-build-scope.json'
OLD_COMP = ROOT / 'execution/v2.4/receipts/W05/W05-99/qualification_status_desktop_build_codex/20261014-current-chat/composition.json'
OLD_FINAL = ROOT / 'execution/v2.4/receipts/W05/W05-99/qualification_status_desktop_build_codex/20261014-current-chat/FINAL-manifest.json'
CANDIDATE = 'a7ec7ebf2d53848ea163b6115667b3e3761a6bd2'
TREE = '5b54aa0b8b94cb8012413efd401dc417671b06de'
BASE = '5ddc0abb8c6d95e9ca071a4eb41a7e12b8559456'
SCOPE_SHA = 'a575686adf3b4733c4a1cb01bf701fc190e50076c443b5aa9504aa3452c43a30'
CHANGED = {'adapters/runtime/bridge_control_windows_test.go', 'adapters/runtime/bridge_windows.go',
           'adapters/runtime/mu/build-candidate.mjs', 'adapters/runtime/mu/build-candidate.test.mjs',
           'adapters/runtime/mu/worker-pause.test.mjs', 'adapters/runtime/mu/worker.mjs',
           'internal/host/runtime_coding_windows.go', 'internal/host/runtime_coding_windows_test.go',
           'internal/host/runtime_setup_windows.go', 'internal/host/runtime_setup_windows_test.go'}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def ref(path):
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': sha(path)}

def need(cond, message):
    if not cond:
        raise RuntimeError(message)

def git(*args):
    return subprocess.check_output(['git', *args], cwd=SOURCE, text=True).strip()

def write_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')

def main():
    need(not DEST.exists(), 'destination already exists')
    need(sha(SCOPE) == SCOPE_SHA, 'scope changed')
    need(git('rev-parse', 'HEAD') == CANDIDATE and git('rev-parse', 'HEAD^{tree}') == TREE, 'candidate changed')
    need(git('status', '--porcelain=v1') == '', 'tracked source dirty')
    changed = set(git('diff', '--name-only', BASE, CANDIDATE).splitlines())
    need(changed == CHANGED, f'candidate diff changed: {changed}')
    old = json.loads(OLD_COMP.read_bytes())
    old_final = json.loads(OLD_FINAL.read_bytes())
    result = json.loads((RAW / 'result.json').read_bytes())
    desc = json.loads((BUILD / 'apps/desktop/resources/client-wire/descriptor.json').read_bytes())
    inputs = json.loads((RAW / 'inputs.before.json').read_bytes())
    after = json.loads((RAW / 'inputs.after.json').read_bytes())
    need(result['status'] == 'BUILT_NOT_TESTED' and not result['drift'], 'bound build drift')
    need(len(inputs) > 6000 and len(inputs) == len(after) and result['build_input_digest'] == desc['build_input_digest'], 'build input binding')
    need(len(desc['exact_module_source_inventory']) == 14 and len(desc['compiled_React_asset_inventory']) == 3, 'UI/React census')
    old_rows = {x['path']: x for x in old['package_files']}
    public_rows = [x for x in old['package_files'] if x['component'] == 'PUBLIC_SOURCE_EQUAL_OLD']
    need(len(old_rows) == 58 and len(public_rows) == 32, 'old package census')
    need(old_final['package']['member_count'] == 58 and old_final['source']['candidate_commit'] == BASE, 'old package provenance')
    core = json.loads((RAW / 'core-result.json').read_bytes())
    need(core['candidate_commit'] == CANDIDATE and core['tree'] == TREE and core['native_exit'] == 0 and not core['drift'], 'fresh Core build missing')
    for name, relative in [('core-control', 'apps/desktop/resources/control/researchos-control.exe'),
                           ('core-runtime-verifier', 'apps/desktop/resources/control/runtime-verifier.exe')]:
        stamp = (RAW / (name + '-go-version-m.stdout')).read_text(encoding='utf-8')
        need('vcs.revision=' + CANDIDATE in stamp and 'vcs.modified=false' in stamp, name + ' VCS stamp')
        need(sha(BUILD / (name + '.exe')) != sha(OLD / relative), name + ' unexpectedly equals old executable')
    for row in public_rows:
        relative = row['path']
        need(relative not in CHANGED and sha(SOURCE / relative) == sha(OLD / relative) == row['sha256'], 'public asset changed: ' + relative)
    mu = json.loads((OLD / 'apps/desktop/resources/control/runtime/mu-worker.mjs.build.json').read_bytes())
    need(mu['mu_commit'] == '8dfebe36508ac0c2508735bb866756dab9283e74', 'Mu pin changed')
    for row in desc['exact_module_source_inventory']:
        relative = 'apps/desktop/' + row['path']
        need(sha(BUILD / relative) == sha(SOURCE / relative) == row['sha256'], 'UI binding: ' + relative)
        need(row['sha256'] == old_rows[relative]['sha256'], 'unexpected UI source change: ' + relative)
    for row in desc['compiled_React_asset_inventory']:
        need(sha(BUILD / 'apps/web/dist' / row['path']) == row['sha256'], 'React binding: ' + row['path'])
        need(row['sha256'] == old_rows['apps/web/dist/' + row['path']]['sha256'], 'unexpected React change: ' + row['path'])
    validator = BUILD / 'apps/desktop/resources/client-wire/researchos-client-wire-validator.exe'
    need(sha(validator) == desc['binary_sha256'], 'validator binary changed')
    DEST.mkdir(parents=True)
    rows = []
    def copy(source, relative, component, source_commit):
        need(source.is_file() and not source.is_symlink(), 'invalid member source: ' + relative)
        target = DEST / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        need(sha(target) == sha(source), 'copy drift: ' + relative)
        rows.append({'path': relative, 'sha256': sha(target), 'bytes': target.stat().st_size,
                     'component': component, 'source_commit': source_commit, 'source': str(source)})
    for row in old['package_files']:
        relative = row['path']
        if relative == 'apps/desktop/resources/control/runtime-verifier-installation.json' or relative.startswith('apps/web/dist/'):
            continue
        if relative in ('apps/desktop/resources/control/researchos-control.exe', 'apps/desktop/resources/control/runtime-verifier.exe'):
            name = 'core-control' if relative.endswith('researchos-control.exe') else 'core-runtime-verifier'
            source, component, commit = BUILD / (name + '.exe'), 'FRESH_CORE_FROM_CURRENT_MAIN', CANDIDATE
        elif relative.startswith('apps/desktop/resources/control/runtime/'):
            source, component, commit = OLD / relative, 'REUSED_MU_FIXED', mu['mu_commit']
            need(sha(source) == row['sha256'], 'Mu asset changed: ' + relative)
        elif relative.startswith('apps/desktop/resources/client-wire/'):
            source, component, commit = BUILD / relative, 'NEW_SOURCE_BOUND_VALIDATOR', CANDIDATE
        elif relative.startswith('apps/desktop/'):
            source, component, commit = BUILD / relative, 'REBUILT_BOUND_UI_EQUAL_OLD', CANDIDATE
        else:
            source, component, commit = SOURCE / relative, 'PUBLIC_SOURCE_EQUAL_OLD', CANDIDATE
            need(sha(source) == row['sha256'], 'public asset changed: ' + relative)
        copy(source, relative, component, commit)
    for row in desc['compiled_React_asset_inventory']:
        relative = 'apps/web/dist/' + row['path']
        copy(BUILD / relative, relative, 'REBUILT_BOUND_REACT_EQUAL_OLD', CANDIDATE)
    verifier = DEST / 'apps/desktop/resources/control/runtime-verifier.exe'
    install_relative = 'apps/desktop/resources/control/runtime-verifier-installation.json'
    install = DEST / install_relative
    write_new(install, {'schema': 'researchos.runtime-verifier-installation.v1',
                        'service_id': 'researchos.runtime-qualification-verifier.v1',
                        'protocol': 'researchos.runtime-verifier/1', 'executable': str(verifier),
                        'executable_hash': 'sha256:' + sha(verifier), 'source_commit': CANDIDATE,
                        'arguments': []})
    rows.append({'path': install_relative, 'sha256': sha(install), 'bytes': install.stat().st_size,
                 'component': 'NEW_INSTALLATION_MANIFEST_FRESH_VERIFIER', 'source_commit': CANDIDATE,
                 'source': str(HERE / 'assemble-coding-any.py')})
    need(len(rows) == 58 and len({x['path'] for x in rows}) == 58, 'package census')
    need({p.relative_to(DEST).as_posix() for p in DEST.rglob('*') if p.is_file()} == {x['path'] for x in rows}, 'filesystem census')
    numbered = sorted(int(Path(x['path']).name[:4]) for x in rows if x['path'].startswith('migrations/sqlite/')
                    and Path(x['path']).name[:4].isdigit())
    need(numbered == list(range(1, 25)), 'migration inventory must be exact 1..24')
    report = {'schema': 'researchos.cp465-coding-any-combined-composition.v1',
              'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'package_root': str(DEST), 'source_commit': CANDIDATE, 'source_tree': TREE,
              'base_commit': BASE, 'old_package_core_commit': old_final['package']['core_old_commit'],
              'mu_commit': mu['mu_commit'], 'scope_sha256': SCOPE_SHA,
              'changed_paths_exact': sorted(changed),
              'fresh_core_build': ref(RAW / 'core-result.json'),
              'migration_numbered_inventory': numbered,
              'older_mu_provenance': 'Installed Mu8df node/worker/buildmeta copied byte-for-byte from approved CP458 package; candidate M1 source is not installed or activated.',
              'old_composition': ref(OLD_COMP), 'old_final': ref(OLD_FINAL),
              'bound_full_input_count': len(inputs), 'bound_full_input_digest': result['build_input_digest'],
              'core_input_count': core['input_count'], 'core_input_digest': core['input_digest'],
              'descriptor': ref(DEST / 'apps/desktop/resources/client-wire/descriptor.json'),
              'validator_sha256': desc['binary_sha256'], 'package_files': rows,
              'installation_manifest': ref(install), 'activation': 'NOT_STARTED',
              'formal_increment': 0, 'parent_acceptance': False}
    write_new(HERE / 'composition.json', report)
    print(json.dumps({'status': 'ASSEMBLED_NOT_LAUNCHED', 'members': len(rows),
                      'composition_sha256': sha(HERE / 'composition.json')}, ensure_ascii=False))

if __name__ == '__main__':
    main()
