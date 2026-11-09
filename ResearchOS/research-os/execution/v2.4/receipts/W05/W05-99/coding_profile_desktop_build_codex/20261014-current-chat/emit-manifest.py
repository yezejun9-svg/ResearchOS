"""Freeze a reviewable CP477 package manifest; this does not grant acceptance."""
import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path('D:/作品集/ResearchOS/research-os')
SOURCE = ROOT / '.local/worktrees/profile-result-build-20261014'
BUILD = SOURCE / '.local/builds/profile-result-c8b7adab-20261014'
DEST = Path('C:/Users/yqyyds/.codex/researchos-resource-cache/normal-coding-profile-c8b7adab-20261014')
OLD = Path('C:/Users/yqyyds/.codex/researchos-resource-cache/normal-coding-any-a7ec7ebf-20261014')
HERE = Path(__file__).resolve().parent
CANDIDATE = 'c8b7adab9f0c15eb33f235f8d0d9eb205794e376'
TREE = 'cd951533206a6a4545a6e55fec374e62289d2dd4'
CORE = 'a7ec7ebf2d53848ea163b6115667b3e3761a6bd2'
MU = '8dfebe36508ac0c2508735bb866756dab9283e74'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def ref(path):
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': sha(path)}

def need(value, message):
    if not value:
        raise RuntimeError(message)

def load(path):
    return json.loads(path.read_bytes())

def git(*args):
    return subprocess.check_output(['git', *args], cwd=SOURCE, text=True).strip()

def exit_code(name):
    return int((HERE / (name + '.exit.txt')).read_text(encoding='utf-8-sig').strip())

def main():
    final = HERE / 'FINAL-manifest.json'
    need(not final.exists(), 'final manifest already exists')
    need(git('rev-parse', 'HEAD') == CANDIDATE and git('rev-parse', 'HEAD^{tree}') == TREE and
         git('status', '--porcelain=v1') == '', 'fixed source changed')
    composition = load(HERE / 'composition.json')
    descriptor_path = DEST / 'apps/desktop/resources/client-wire/descriptor.json'
    descriptor = load(descriptor_path)
    result = load(HERE / 'raw-build-receipts/result.json')
    before = load(HERE / 'raw-build-receipts/inputs.before.json')
    after = load(HERE / 'raw-build-receipts/inputs.after.json')
    need(result['status'] == 'BUILT_NOT_TESTED' and not result['drift'] and
         len(before) == len(after) == 6444 and
         all(b['sha256'] == a['current_sha256'] for b, a in zip(before, after)) and
         result['build_input_digest'] == descriptor['build_input_digest'] == composition['build_input_digest'],
         'fresh input digest or source drift')
    need(composition['source_commit'] == CANDIDATE and composition['source_tree'] == TREE and
         composition['core_source_commit'] == CORE and composition['mu_source_commit'] == MU and
         composition['changed_source_paths_exact'] == [
             'apps/desktop/main/lib/desktop-management.js',
             'tests/ui/desktop/coding-authorization-boundary.test.mjs'], 'composition provenance')
    rows = composition['package_files']
    need(len(rows) == 58 and len({row['path'] for row in rows}) == 58 and
         {path.relative_to(DEST).as_posix() for path in DEST.rglob('*') if path.is_file()} ==
         {row['path'] for row in rows}, 'package census')
    for row in rows:
        path = DEST / row['path']
        need(path.is_file() and not path.is_symlink() and path.stat().st_size == row['bytes'] and
             sha(path) == row['sha256'], 'package member drift: ' + row['path'])
        if row['component'] == 'REUSED_CORE_A7EC':
            need(row['source_commit'] == CORE and sha(OLD / row['path']) == row['sha256'],
                 'Core reuse drift: ' + row['path'])
        if row['component'] == 'REUSED_MU_8DF':
            need(row['source_commit'] == MU and sha(OLD / row['path']) == row['sha256'],
                 'Mu reuse drift: ' + row['path'])
    need(len([r for r in rows if r['component'] == 'REUSED_CORE_A7EC']) == 2 and
         len([r for r in rows if r['component'] == 'REUSED_MU_8DF']) == 3 and
         len([r for r in rows if r['component'] == 'PUBLIC_SOURCE_EQUAL_OLD']) == 32 and
         composition['migration_numbered_inventory'] == list(range(1, 25)), 'component census')
    need(len(descriptor['exact_module_source_inventory']) == 14 and
         len(descriptor['compiled_React_asset_inventory']) == 3, 'UI descriptor census')
    for entry in descriptor['exact_module_source_inventory']:
        relative = Path('apps/desktop') / entry['path']
        need(sha(DEST / relative) == sha(SOURCE / relative) == entry['sha256'],
             'UI source drift: ' + entry['path'])
    for entry in descriptor['compiled_React_asset_inventory']:
        relative = Path('apps/web/dist') / entry['path']
        need(sha(DEST / relative) == sha(BUILD / relative) == entry['sha256'],
             'React drift: ' + entry['path'])
    validator = DEST / 'apps/desktop/resources/client-wire/researchos-client-wire-validator.exe'
    stamp = (HERE / 'validator-go-version-m.stdout.txt').read_text(encoding='utf-8')
    need(sha(validator) == descriptor['binary_sha256'] and exit_code('validator-go-version-m') == 0 and
         'vcs.revision=' + CANDIDATE in stamp and 'vcs.modified=false' in stamp and
         'main.buildInputDigest=' + descriptor['build_input_digest'] in stamp, 'fresh validator stamp')
    installation_path = DEST / 'apps/desktop/resources/control/runtime-verifier-installation.json'
    installation = load(installation_path)
    verifier = DEST / 'apps/desktop/resources/control/runtime-verifier.exe'
    need(installation['executable'] == str(verifier) and
         installation['executable_hash'] == 'sha256:' + sha(verifier) and
         installation['source_commit'] == CORE, 'installation manifest provenance')
    acl = load(HERE / 'acl-readback.json')
    need(acl['status'] == 'LIVE_READBACK_PASS' and acl['protected'] and acl['rule_count'] == 1 and
         acl['current_user_sid'] == acl['owner_sid'] == acl['single_ace_identity'] and
         acl['manifest_sha256'] == sha(installation_path), 'installer ACL readback')
    suite = (HERE / 'validator-suite.stdout.txt').read_text(encoding='utf-8')
    top_pass = re.findall(r'^--- PASS: ([^\s]+)', suite, flags=re.M)
    need(exit_code('validator-suite') == 0 and suite.rstrip().endswith('PASS') and
         len(top_pass) == 4 and suite.count('--- PASS:') == 71 and '--- FAIL:' not in suite,
         'validator suite')
    cases = load(HERE / 'package-cases.invocation.json')
    need(exit_code('package-cases') == cases['native_exit'] == 0 and
         cases['counts'] == {'tests': 214, 'pass': 214, 'fail': 0, 'skipped': 0, 'cancelled': 0} and
         cases['environment']['RESEARCHOS_DESKTOP_WIRE_ROOT'] == str(DEST / 'apps/desktop'),
         'actual package cases')
    freeze = load(HERE / 'raw-freeze.json')
    need(exit_code('freeze-raw') == 0 and freeze['raw_count'] == 32 and
         freeze['WORK_count'] == 1844 and freeze['archive_count'] == 680, 'formal raw freeze census')
    for row in freeze['raw_files'] + freeze['compiler_files']['WORK'] + freeze['compiler_files']['archives']:
        copy = Path(row['copy'])
        need(copy.is_file() and copy.is_relative_to(HERE) and copy.stat().st_size == row['bytes'] and
             sha(copy) == row['sha256'], 'formal raw copy drift: ' + str(copy))
    invocations = {}
    for path in sorted((HERE / 'raw-build-receipts').glob('*.invocation.json')):
        row = load(path)
        need(row['exit'] == 0, 'failed builder invocation: ' + path.name)
        invocations[path.name] = {'receipt': ref(path), 'actualargv': row['actualargv'],
                                  'cwd': row['cwd'], 'numeric_exit': row['exit'],
                                  'environment': row['environment']}
    need({'go-build.invocation.json', 'go-test-build.invocation.json',
          'react-build.invocation.json'} <= set(invocations), 'missing build invocation')
    need(all(exit_code(name) == 0 for name in ('build', 'assemble', 'protect03', 'readback',
                                               'package-cases', 'freeze-raw', 'validator-go-version-m')) and
         exit_code('protect') == exit_code('protect02') == 1, 'attempt exit mismatch')
    failures = load(HERE / 'failed-attempts.json')
    need(failures['count'] == len(failures['attempts']) == 3, 'failed attempt count')
    case_files = []
    for path in sorted((HERE / 'package-cases').rglob('*')):
        if path.is_file():
            case_files.append({'path': str(path), 'bytes': path.stat().st_size, 'sha256': sha(path)})
    payload = {'schema': 'researchos.cp477-profile-result-desktop-package-manifest/1',
               'status': 'ASSEMBLED_HASHED_NOT_LAUNCHED_PENDING_INDEPENDENT_PACKAGE_REVIEW',
               'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'owner': 'codex:/root/coding_profile_fix', 'model': 'gpt-6-sol',
               'reasoning_effort': 'high',
               'scope': composition['scope'], 'source_review': composition['source_review'],
               'source_integration': composition['source_integration'],
               'source': {'worktree': str(SOURCE), 'commit': CANDIDATE, 'tree': TREE,
                          'tracked_clean': True, 'changed_paths_exact': composition['changed_source_paths_exact'],
                          'builder': ref(SOURCE / 'apps/desktop/build-validator.py')},
               'build': {'output': str(BUILD), 'input_count': len(before),
                         'input_digest': descriptor['build_input_digest'], 'input_drift': [],
                         'inputs_before': ref(HERE / 'raw-build-receipts/inputs.before.json'),
                         'inputs_after': ref(HERE / 'raw-build-receipts/inputs.after.json'),
                         'result': ref(HERE / 'raw-build-receipts/result.json'),
                         'tools_before': ref(HERE / 'raw-build-receipts/tools.before.json'),
                         'raw_freeze': ref(HERE / 'raw-freeze.json'),
                         'compiler_work_archive': ref(HERE / 'raw-build-receipts/compiler-work-archive.json'),
                         'builder_invocations': invocations,
                         'builder_top_level': {'command': ref(HERE / 'build.command.txt'),
                                               'stdout': ref(HERE / 'build.stdout.txt'),
                                               'stderr': ref(HERE / 'build.stderr.txt'), 'numeric_exit': 0}},
               'local_tests': {'validator_top_level_pass': top_pass, 'validator_all_pass_markers': 71,
                               'validator_suite_stdout': ref(HERE / 'validator-suite.stdout.txt'),
                               'validator_suite_numeric_exit': 0,
                               'packaged_non_gui_counts': cases['counts'],
                               'packaged_non_gui_invocation': ref(HERE / 'package-cases.invocation.json'),
                               'packaged_case_files': case_files,
                               'renderer_GUI_cases_executed': False},
               'package': {'root': str(DEST), 'member_count': len(rows),
                           'bytes': sum(row['bytes'] for row in rows), 'members': rows,
                           'composition': ref(HERE / 'composition.json'),
                           'descriptor': ref(descriptor_path),
                           'Main_preload_count': 14, 'React_asset_count': 3,
                           'core_source_commit': CORE, 'mu_source_commit': MU,
                           'migration_numbered_inventory': composition['migration_numbered_inventory'],
                           'installation_manifest': ref(installation_path),
                           'installation_acl_readback': ref(HERE / 'acl-readback.json')},
               'failed_attempts_preserved': ref(HERE / 'failed-attempts.json'),
               'failed_attempt_count': 3,
               'source_modified': False, 'activation': 'NOT_STARTED', 'GUI_first_use': False,
               'model_calls': 0, 'real_API_calls': 0, 'database_operations': 0,
               'package_independent_review': 'PENDING', 'formal_increment': 0,
               'parent_acceptance': False}
    with final.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'status': payload['status'], 'members': len(rows),
                      'packaged_non_gui_pass': cases['counts']['pass'],
                      'FINAL_sha256': sha(final)}, ensure_ascii=False))

if __name__ == '__main__':
    main()
