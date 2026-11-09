"""Assemble a fixed-source Desktop candidate from the repository's bound build."""
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path('D:/作品集/ResearchOS/research-os')
SOURCE = Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/qualification-status-repair-20261014')
BUILD = SOURCE / '.local/builds/qualification-status-combined-20261014'
RAW = SOURCE / '.local/receipts/qualification-status-combined-20261014'
OLD = Path('C:/Users/yqyyds/.codex/researchos-resource-cache/normal-attach-combined-c465d135-20261014')
DEST = Path('C:/Users/yqyyds/.codex/researchos-resource-cache/normal-status-combined-5ddc0abb-20261014')
HERE = Path(__file__).resolve().parent
SCOPE = ROOT / 'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261014-current-chat/continuation-cp458/package-build-scope.json'
OLD_COMP = ROOT / 'execution/v2.4/receipts/W05/W05-99/approved_attach_combined_desktop_build_codex/20261014-current-chat/composition.json'
OLD_FINAL = ROOT / 'execution/v2.4/receipts/W05/W05-99/approved_attach_combined_desktop_build_codex/20261014-current-chat/FINAL-manifest.json'
CANDIDATE = '5ddc0abb8c6d95e9ca071a4eb41a7e12b8559456'
TREE = 'bfade6fd49897f53e2ec629c71691405be2f2fbe'
BASE = 'c465d1356480d6e6a90da84656724f9fc02b31c7'
OLD_CORE = 'b955c8665281193d5cbf90a146f936c9212c7940'
OLD_TREE = '00d44e133662227b115eb3b16bef3d4edcc35630'
SCOPE_SHA = '6a22d3c48b735fc6d2c599d04993dc2463bc210728d80811cf726b6c09dd7b26'
CHANGED = {'apps/desktop/main/lib/desktop-management.js', 'apps/web/src/workbench.jsx',
           'tests/ui/desktop/coding-authorization-boundary.test.mjs',
           'tests/ui/desktop/desktop-management-boundary.test.mjs'}

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
    need(git('rev-parse', OLD_CORE + '^{tree}') == OLD_TREE and git('rev-parse', BASE + '^{tree}') == OLD_TREE, 'old Core tree changed')
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
    need(old_final['package']['member_count'] == 58 and old_final['source']['candidate_commit'] == OLD_CORE, 'old Core provenance')
    for label, relative in [('control', 'apps/desktop/resources/control/researchos-control.exe'),
                            ('runtime_verifier', 'apps/desktop/resources/control/runtime-verifier.exe')]:
        row = old_final['package']['binaries'][label]
        p = OLD / relative
        stamp = Path(row['version_m_raw']['path']).read_text(encoding='utf-8')
        need(row['source_commit'] == OLD_CORE and 'vcs.revision=' + OLD_CORE in stamp and 'vcs.modified=false' in stamp, label + ' VCS provenance')
        need(sha(p) == old_rows[relative]['sha256'] == row['binary']['sha256'], label + ' old package changed')
    for row in public_rows:
        relative = row['path']
        need(relative not in CHANGED and sha(SOURCE / relative) == sha(OLD / relative) == row['sha256'], 'public asset changed: ' + relative)
    mu = json.loads((OLD / 'apps/desktop/resources/control/runtime/mu-worker.mjs.build.json').read_bytes())
    need(mu['mu_commit'] == '8dfebe36508ac0c2508735bb866756dab9283e74', 'Mu pin changed')
    for row in desc['exact_module_source_inventory']:
        relative = 'apps/desktop/' + row['path']
        need(sha(BUILD / relative) == sha(SOURCE / relative) == row['sha256'], 'UI binding: ' + relative)
        if relative not in CHANGED:
            need(row['sha256'] == old_rows[relative]['sha256'], 'unexpected UI change: ' + relative)
        else:
            need(row['sha256'] != old_rows[relative]['sha256'], 'changed UI equals old')
    for row in desc['compiled_React_asset_inventory']:
        need(sha(BUILD / 'apps/web/dist' / row['path']) == row['sha256'], 'React binding: ' + row['path'])
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
            source, component, commit = OLD / relative, 'REUSED_CORE_UNCHANGED_GO_DEPS_ASSETS', OLD_CORE
        elif relative.startswith('apps/desktop/resources/control/runtime/'):
            source, component, commit = OLD / relative, 'REUSED_MU_FIXED', mu['mu_commit']
            need(sha(source) == row['sha256'], 'Mu asset changed: ' + relative)
        elif relative.startswith('apps/desktop/resources/client-wire/'):
            source, component, commit = BUILD / relative, 'NEW_SOURCE_BOUND_VALIDATOR', CANDIDATE
        elif relative.startswith('apps/desktop/'):
            source, component, commit = BUILD / relative, 'NEW_BOUND_UI' if relative in CHANGED else 'REBUILT_BOUND_UI_EQUAL_OLD', CANDIDATE
        else:
            source, component, commit = SOURCE / relative, 'PUBLIC_SOURCE_EQUAL_OLD', CANDIDATE
            need(sha(source) == row['sha256'], 'public asset changed: ' + relative)
        copy(source, relative, component, commit)
    for row in desc['compiled_React_asset_inventory']:
        relative = 'apps/web/dist/' + row['path']
        copy(BUILD / relative, relative, 'NEW_BOUND_REACT', CANDIDATE)
    verifier = DEST / 'apps/desktop/resources/control/runtime-verifier.exe'
    install_relative = 'apps/desktop/resources/control/runtime-verifier-installation.json'
    install = DEST / install_relative
    write_new(install, {'schema': 'researchos.runtime-verifier-installation.v1',
                        'service_id': 'researchos.runtime-qualification-verifier.v1',
                        'protocol': 'researchos.runtime-verifier/1', 'executable': str(verifier),
                        'executable_hash': 'sha256:' + sha(verifier), 'source_commit': OLD_CORE,
                        'arguments': []})
    rows.append({'path': install_relative, 'sha256': sha(install), 'bytes': install.stat().st_size,
                 'component': 'NEW_INSTALLATION_MANIFEST_REUSED_VERIFIER', 'source_commit': OLD_CORE,
                 'source': str(HERE / 'assemble-status.py')})
    need(len(rows) == 58 and len({x['path'] for x in rows}) == 58, 'package census')
    need({p.relative_to(DEST).as_posix() for p in DEST.rglob('*') if p.is_file()} == {x['path'] for x in rows}, 'filesystem census')
    report = {'schema': 'researchos.cp458-status-combined-composition.v1',
              'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'package_root': str(DEST), 'source_commit': CANDIDATE, 'source_tree': TREE,
              'base_commit': BASE, 'old_core_commit': OLD_CORE, 'old_core_tree': OLD_TREE,
              'mu_commit': mu['mu_commit'], 'scope_sha256': SCOPE_SHA,
              'changed_paths_exact': sorted(changed),
              'core_reuse_proof': 'Only the exact four listed UI/test paths differ from c465; c465 and old Core b955 have identical tree 00d44e. All package public assets equal old hashes. Core binaries and Go VCS receipts equal old package.',
              'old_composition': ref(OLD_COMP), 'old_final': ref(OLD_FINAL),
              'bound_full_input_count': len(inputs), 'bound_full_input_digest': result['build_input_digest'],
              'descriptor': ref(DEST / 'apps/desktop/resources/client-wire/descriptor.json'),
              'validator_sha256': desc['binary_sha256'], 'package_files': rows,
              'installation_manifest': ref(install), 'activation': 'NOT_STARTED',
              'formal_increment': 0, 'parent_acceptance': False}
    write_new(HERE / 'composition.json', report)
    print(json.dumps({'status': 'ASSEMBLED_NOT_LAUNCHED', 'members': len(rows),
                      'composition_sha256': sha(HERE / 'composition.json')}, ensure_ascii=False))

if __name__ == '__main__':
    main()
