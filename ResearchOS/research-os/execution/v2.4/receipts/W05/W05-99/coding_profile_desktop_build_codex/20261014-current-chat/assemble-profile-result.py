"""Assemble the fixed CP477 Desktop package without launching the product."""
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path('D:/作品集/ResearchOS/research-os')
SOURCE = ROOT / '.local/worktrees/profile-result-build-20261014'
BUILD = SOURCE / '.local/builds/profile-result-c8b7adab-20261014'
RAW = SOURCE / '.local/receipts/profile-result-c8b7adab-20261014'
OLD = Path('C:/Users/yqyyds/.codex/researchos-resource-cache/normal-coding-any-a7ec7ebf-20261014')
DEST = Path('C:/Users/yqyyds/.codex/researchos-resource-cache/normal-coding-profile-c8b7adab-20261014')
HERE = Path(__file__).resolve().parent
SCOPE = ROOT / 'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261014-current-chat/continuation-cp477/package-build-scope.json'
REVIEW = ROOT / 'execution/v2.4/receipts/W05/W05-99/coding_profile_result_independent_review_codex/20261014-current-chat/FINAL-report.json'
INTEGRATION = ROOT / 'execution/v2.4/receipts/W05/W05-99/coding_profile_result_integration_codex/20261014-current-chat/integration.json'
OLD_COMP = ROOT / 'execution/v2.4/receipts/W05/W05-99/coding_any_desktop_build_codex/20261014-current-chat/composition.json'
OLD_FINAL = ROOT / 'execution/v2.4/receipts/W05/W05-99/coding_any_desktop_build_codex/20261014-current-chat/FINAL-manifest.json'
CANDIDATE = 'c8b7adab9f0c15eb33f235f8d0d9eb205794e376'
TREE = 'cd951533206a6a4545a6e55fec374e62289d2dd4'
CORE = 'a7ec7ebf2d53848ea163b6115667b3e3761a6bd2'
MU = '8dfebe36508ac0c2508735bb866756dab9283e74'
CHANGED = {'apps/desktop/main/lib/desktop-management.js',
           'tests/ui/desktop/coding-authorization-boundary.test.mjs'}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def ref(path):
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': sha(path)}

def need(condition, message):
    if not condition:
        raise RuntimeError(message)

def load(path):
    return json.loads(path.read_bytes())

def git(*args):
    return subprocess.check_output(['git', *args], cwd=SOURCE, text=True).strip()

def write_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

def main():
    need(not DEST.exists() and not (HERE / 'composition.json').exists(), 'destination or composition exists')
    need(sha(SCOPE) == '74f119940664f9d1e41489f7cca3690c25add7d9d9c12a8011c0a20a64fb42a0', 'scope changed')
    need(sha(REVIEW) == '25d17fcf3cf9dd0710c67b6cc96cdef41a9278e4011c38debd9a5980b983a719', 'review changed')
    need(sha(INTEGRATION) == '7fdc711348ab95e31a58858405da1f6e0e2b170201fcca5cda61ce67dbeca867', 'integration changed')
    need(git('rev-parse', 'HEAD') == CANDIDATE and git('rev-parse', 'HEAD^{tree}') == TREE, 'fixed source changed')
    need(git('status', '--porcelain=v1') == '', 'fixed source dirty')
    need(set(git('diff', '--name-only', CORE, CANDIDATE).splitlines()) == CHANGED, 'source delta changed')
    old = load(OLD_COMP)
    old_final = load(OLD_FINAL)
    need(old_final['source']['candidate_commit'] == CORE and old_final['package']['core_source_commit'] == CORE and
         old_final['package']['mu_commit'] == MU and old_final['package']['member_count'] == 58, 'old provenance')
    need(old['source_commit'] == CORE and old['source_tree'] == '5b54aa0b8b94cb8012413efd401dc417671b06de', 'old source')
    old_rows = {x['path']: x for x in old['package_files']}
    need(len(old_rows) == 58, 'old package inventory')
    for relative, row in old_rows.items():
        old_file = OLD / relative
        need(old_file.is_file() and not old_file.is_symlink() and sha(old_file) == row['sha256'],
             'old member drift: ' + relative)
    mu_meta = load(OLD / 'apps/desktop/resources/control/runtime/mu-worker.mjs.build.json')
    need(mu_meta['mu_commit'] == MU, 'Mu provenance')
    result = load(RAW / 'result.json')
    desc = load(BUILD / 'apps/desktop/resources/client-wire/descriptor.json')
    inputs = load(RAW / 'inputs.before.json')
    after = load(RAW / 'inputs.after.json')
    need(result['status'] == 'BUILT_NOT_TESTED' and not result['drift'] and
         len(inputs) == len(after) == 6444 and
         all(row['sha256'] == current['current_sha256'] for row, current in zip(inputs, after)) and
         result['build_input_digest'] == desc['build_input_digest'] and
         desc['build_input_digest'] != old_final['build']['input_digest'], 'fresh bound build')
    input_by_path = {row['path']: row for row in inputs}
    for relative in CHANGED:
        source_file = SOURCE / relative
        need(str(source_file) in input_by_path and input_by_path[str(source_file)]['sha256'] == sha(source_file),
             'changed source absent from input digest: ' + relative)
    need(len(desc['exact_module_source_inventory']) == 14 and
         len(desc['compiled_React_asset_inventory']) == 3, 'Desktop/React census')
    validator = BUILD / 'apps/desktop/resources/client-wire/researchos-client-wire-validator.exe'
    need(sha(validator) == desc['binary_sha256'] == result['binary_sha256'] and
         sha(validator) != old_rows['apps/desktop/resources/client-wire/researchos-client-wire-validator.exe']['sha256'],
         'validator provenance')
    for entry in desc['exact_module_source_inventory']:
        relative = 'apps/desktop/' + entry['path']
        need(sha(SOURCE / relative) == sha(BUILD / relative) == entry['sha256'], 'Main/preload binding: ' + relative)
        if relative not in CHANGED:
            need(entry['sha256'] == old_rows[relative]['sha256'], 'unexpected Main/preload difference: ' + relative)
    for entry in desc['compiled_React_asset_inventory']:
        relative = 'apps/web/dist/' + entry['path']
        need(sha(BUILD / relative) == entry['sha256'] == old_rows[relative]['sha256'],
             'React binding: ' + relative)
    public_rows = [row for row in old_rows.values() if row['component'] == 'PUBLIC_SOURCE_EQUAL_OLD']
    need(len(public_rows) == 32, 'public inventory')
    for row in public_rows:
        need(sha(SOURCE / row['path']) == row['sha256'], 'public source changed: ' + row['path'])

    DEST.mkdir(parents=True)
    rows = []
    def copy(source, relative, component, commit):
        need(source.is_file() and not source.is_symlink(), 'invalid source: ' + relative)
        target = DEST / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        need(sha(target) == sha(source), 'copy drift: ' + relative)
        rows.append({'path': relative, 'sha256': sha(target), 'bytes': target.stat().st_size,
                     'component': component, 'source_commit': commit, 'source': str(source)})
    for row in old['package_files']:
        relative = row['path']
        if relative == 'apps/desktop/resources/control/runtime-verifier-installation.json' or relative.startswith('apps/web/dist/'):
            continue
        if relative in ('apps/desktop/resources/control/researchos-control.exe',
                        'apps/desktop/resources/control/runtime-verifier.exe'):
            source, component, commit = OLD / relative, 'REUSED_CORE_A7EC', CORE
        elif relative.startswith('apps/desktop/resources/control/runtime/'):
            source, component, commit = OLD / relative, 'REUSED_MU_8DF', MU
        elif relative.startswith('apps/desktop/resources/client-wire/'):
            source, component, commit = BUILD / relative, 'FRESH_SOURCE_BOUND_VALIDATOR_C8', CANDIDATE
        elif relative.startswith('apps/desktop/'):
            source, component, commit = BUILD / relative, 'FRESH_BOUND_MAIN_PRELOAD_C8', CANDIDATE
        else:
            source, component, commit = SOURCE / relative, 'PUBLIC_SOURCE_EQUAL_OLD', CANDIDATE
        copy(source, relative, component, commit)
    for entry in desc['compiled_React_asset_inventory']:
        relative = 'apps/web/dist/' + entry['path']
        copy(BUILD / relative, relative, 'FRESH_BOUND_REACT_C8', CANDIDATE)
    verifier = DEST / 'apps/desktop/resources/control/runtime-verifier.exe'
    install_relative = 'apps/desktop/resources/control/runtime-verifier-installation.json'
    install = DEST / install_relative
    write_new(install, {'schema': 'researchos.runtime-verifier-installation.v1',
                        'service_id': 'researchos.runtime-qualification-verifier.v1',
                        'protocol': 'researchos.runtime-verifier/1',
                        'executable': str(verifier), 'executable_hash': 'sha256:' + sha(verifier),
                        'source_commit': CORE, 'arguments': []})
    rows.append({'path': install_relative, 'sha256': sha(install), 'bytes': install.stat().st_size,
                 'component': 'NEW_INSTALLATION_MANIFEST_REUSED_CORE_A7EC',
                 'source_commit': CORE, 'source': str(HERE / 'assemble-profile-result.py')})
    need(len(rows) == 58 and len({x['path'] for x in rows}) == 58, 'new package inventory')
    need({p.relative_to(DEST).as_posix() for p in DEST.rglob('*') if p.is_file()} ==
         {x['path'] for x in rows}, 'filesystem inventory')
    migrations = sorted(int(Path(row['path']).name[:4]) for row in rows if
                        row['path'].startswith('migrations/sqlite/') and Path(row['path']).name[:4].isdigit())
    need(migrations == list(range(1, 25)), 'numbered migrations')
    report = {'schema': 'researchos.cp477-profile-result-composition/1',
              'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'package_root': str(DEST), 'source_commit': CANDIDATE, 'source_tree': TREE,
              'core_source_commit': CORE, 'mu_source_commit': MU,
              'scope': ref(SCOPE), 'source_review': ref(REVIEW), 'source_integration': ref(INTEGRATION),
              'old_composition': ref(OLD_COMP), 'old_final': ref(OLD_FINAL),
              'changed_source_paths_exact': sorted(CHANGED),
              'build_input_count': len(inputs), 'build_input_digest': result['build_input_digest'],
              'old_build_input_digest': old_final['build']['input_digest'],
              'descriptor': ref(DEST / 'apps/desktop/resources/client-wire/descriptor.json'),
              'validator_sha256': desc['binary_sha256'],
              'Main_preload_count': len(desc['exact_module_source_inventory']),
              'React_asset_count': len(desc['compiled_React_asset_inventory']),
              'migration_numbered_inventory': migrations, 'package_files': rows,
              'installation_manifest': ref(install), 'activation': 'NOT_STARTED', 'formal_increment': 0}
    write_new(HERE / 'composition.json', report)
    print(json.dumps({'status': 'ASSEMBLED_NOT_LAUNCHED', 'members': len(rows),
                      'composition_sha256': sha(HERE / 'composition.json')}, ensure_ascii=False))

if __name__ == '__main__':
    main()
