"""Seal a reviewable package receipt without source or acceptance authority."""
import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path('D:/作品集/ResearchOS/research-os')
SOURCE = Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/qualification-status-repair-20261014')
BUILD = SOURCE / '.local/builds/qualification-status-combined-20261014'
RAW = SOURCE / '.local/receipts/qualification-status-combined-20261014'
DEST = Path('C:/Users/yqyyds/.codex/researchos-resource-cache/normal-status-combined-5ddc0abb-20261014')
HERE = Path(__file__).resolve().parent
SCOPE = ROOT / 'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261014-current-chat/continuation-cp458/package-build-scope.json'
INTEGRATION = ROOT / 'execution/v2.4/receipts/W05/W05-99/qualification_status_integration_codex/20261014-current-chat/integration.json'
SOURCE_REVIEW = Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/qualification-status-independent-review-20261014/FINAL-report.json')
FINAL = HERE / 'FINAL-manifest.json'
CANDIDATE = '5ddc0abb8c6d95e9ca071a4eb41a7e12b8559456'
TREE = 'bfade6fd49897f53e2ec629c71691405be2f2fbe'
OLD_CORE = 'b955c8665281193d5cbf90a146f936c9212c7940'
MAIN_COMMIT = '454492f78fc0536966c8c8343d4bdd2fd99250b7'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def ref(path):
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': sha(path)}

def need(value, message):
    if not value:
        raise RuntimeError(message)

def load(path):
    return json.loads(path.read_bytes())

def main():
    need(not FINAL.exists(), 'FINAL already exists')
    need(sha(SCOPE) == '6a22d3c48b735fc6d2c599d04993dc2463bc210728d80811cf726b6c09dd7b26', 'scope changed')
    need(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=SOURCE, text=True).strip() == CANDIDATE, 'source changed')
    need(subprocess.check_output(['git', 'rev-parse', 'HEAD^{tree}'], cwd=SOURCE, text=True).strip() == TREE, 'source tree changed')
    need(subprocess.check_output(['git', 'status', '--porcelain=v1'], cwd=SOURCE) == b'', 'source dirty')
    need(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == MAIN_COMMIT, 'Main commit changed')
    need(subprocess.check_output(['git', 'rev-parse', 'HEAD^{tree}'], cwd=ROOT, text=True).strip() == TREE, 'Main tree differs')
    need(sha(INTEGRATION) == '7eaafefd2841fd292c8a03c95fca205cca066948dfe630b50aa286da1338163c', 'integration changed')
    need(sha(SOURCE_REVIEW) == 'a93a2332607797d6dda7eb5a4abb5a047453e2b78f69b88a3feee06843609a65', 'source review changed')
    composition = load(HERE / 'composition.json')
    result = load(RAW / 'result.json')
    descriptor_path = DEST / 'apps/desktop/resources/client-wire/descriptor.json'
    descriptor = load(descriptor_path)
    acl = load(HERE / 'acl-readback.json')
    installation_path = DEST / 'apps/desktop/resources/control/runtime-verifier-installation.json'
    installation = load(installation_path)
    need(result['status'] == 'BUILT_NOT_TESTED' and not result['drift'], 'build drift')
    need(result['build_input_digest'] == descriptor['build_input_digest'] == composition['bound_full_input_digest'], 'input digest mismatch')
    rows = composition['package_files']
    need(len(rows) == 58 and len({x['path'] for x in rows}) == 58, 'package row census')
    actual = {p.relative_to(DEST).as_posix() for p in DEST.rglob('*') if p.is_file()}
    need(actual == {x['path'] for x in rows}, 'package filesystem census')
    for row in rows:
        p = DEST / row['path']
        need(p.is_file() and not p.is_symlink() and p.stat().st_size == row['bytes'] and sha(p) == row['sha256'],
             'package member changed: ' + row['path'])
    for entry in descriptor['exact_module_source_inventory']:
        p = DEST / 'apps/desktop' / entry['path']
        need(sha(p) == entry['sha256'], 'Main/preload changed: ' + entry['path'])
    for entry in descriptor['compiled_React_asset_inventory']:
        p = DEST / 'apps/web/dist' / entry['path']
        need(sha(p) == entry['sha256'], 'React changed: ' + entry['path'])
    verifier = DEST / 'apps/desktop/resources/control/runtime-verifier.exe'
    need(installation['executable'] == str(verifier) and installation['executable_hash'] == 'sha256:' + sha(verifier), 'installer binding')
    need(installation['source_commit'] == OLD_CORE, 'installer reused Core provenance')
    need(acl['status'] == 'LIVE_READBACK_PASS' and acl['protected'] and acl['rule_count'] == 1 and
         acl['current_user_sid'] == acl['single_ace_identity'] and acl['manifest_sha256'] == sha(installation_path), 'ACL readback')
    validator = DEST / 'apps/desktop/resources/client-wire/researchos-client-wire-validator.exe'
    need(sha(validator) == descriptor['binary_sha256'], 'validator changed')
    stamp = (RAW / 'validator-go-version-m.stdout').read_text(encoding='utf-8')
    need('vcs.revision=' + CANDIDATE in stamp and 'vcs.modified=false' in stamp, 'validator stamp')
    suite = (RAW / 'validator-suite.stdout').read_text(encoding='utf-8')
    top_pass = re.findall(r'^--- PASS: ([^\s]+)', suite, flags=re.M)
    all_pass_count = suite.count('--- PASS:')
    need(suite.rstrip().endswith('PASS') and len(top_pass) == 4 and all_pass_count == 71 and '--- FAIL:' not in suite, 'validator suite')
    package_cases = load(RAW / 'package-cases.invocation.json')
    need(package_cases['native_exit'] == 0 and package_cases['counts'] ==
         {'tests': 214, 'pass': 214, 'fail': 0, 'skipped': 0, 'cancelled': 0} and
         package_cases['environment']['RESEARCHOS_DESKTOP_WIRE_ROOT'] == str(DEST / 'apps/desktop'), 'actual package cases')
    invocations = {}
    for path in sorted(RAW.glob('*.invocation.json')):
        row = load(path)
        native = row.get('native_exit', row.get('exit'))
        need(native == 0, 'nonzero native exit: ' + path.name)
        invocations[path.stem] = {'receipt': ref(path), 'actualargv': row.get('actualargv', row.get('argv')),
                                  'cwd': row['cwd'], 'native_exit': native}
    need({'go-build.invocation', 'react-build.invocation', 'validator-suite.invocation',
          'validator-go-version-m.invocation', 'package-cases.invocation'} <= set(invocations), 'missing raw command receipts')
    core = {x['path']: {'sha256': x['sha256'], 'source_commit': x['source_commit']} for x in rows
            if x['component'] == 'REUSED_CORE_UNCHANGED_GO_DEPS_ASSETS'}
    mu = {x['path']: {'sha256': x['sha256'], 'source_commit': x['source_commit']} for x in rows
          if x['component'] == 'REUSED_MU_FIXED'}
    payload = {'schema': 'researchos.cp458-status-combined-desktop-build-manifest.v1',
               'status': 'ASSEMBLED_HASHED_NOT_LAUNCHED_PENDING_INDEPENDENT_SOURCE_AND_PACKAGE_REVIEW',
               'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'owner': 'codex:/root/status_desktop_builder', 'model': 'gpt-6-sol', 'reasoning_effort': 'high',
               'scope': ref(SCOPE), 'source_review': ref(SOURCE_REVIEW), 'integration': ref(INTEGRATION),
               'source': {'worktree': str(SOURCE), 'candidate_commit': CANDIDATE,
                                             'main_commit': MAIN_COMMIT, 'main_tree_equal_candidate': True,
                                             'candidate_tree': TREE, 'candidate_clean': True,
                                             'changed_paths_exact': composition['changed_paths_exact']},
               'build': {'output': str(BUILD), 'raw_receipts': str(RAW),
                         'input_count': composition['bound_full_input_count'],
                         'input_digest': result['build_input_digest'], 'input_drift': [],
                         'inputs_before': ref(RAW / 'inputs.before.json'),
                         'inputs_after': ref(RAW / 'inputs.after.json'),
                         'compiler_work_archive': ref(RAW / 'compiler-work-archive.json'),
                         'tools_before': ref(RAW / 'tools.before.json'),
                         'builder': ref(SOURCE / 'apps/desktop/build-validator.py'),
                         'result': ref(RAW / 'result.json'), 'invocations': invocations,
                         'compiler_input_boundary': 'Broad Go list inventory; -work/-x compiler commands retained raw. No claim that broad inventory is only selected inputs.'},
               'local_tests': {'validator_top_level_pass_count': len(top_pass),
                               'validator_top_level_tests': top_pass,
                               'validator_all_pass_markers': all_pass_count,
                               'package_validator_non_gui_counts': package_cases['counts'],
                               'package_validator_non_gui_receipt': ref(RAW / 'package-cases.invocation.json'),
                               'package_case_wrapper_correction': ref(HERE / 'package-case-wrapper-correction.json'),
                               'renderer_gui_cases_executed': False},
               'package': {'root': str(DEST), 'member_count': len(rows),
                           'bytes': sum(x['bytes'] for x in rows), 'members': rows,
                           'composition': ref(HERE / 'composition.json'),
                           'descriptor': ref(descriptor_path),
                           'module_count': len(descriptor['exact_module_source_inventory']),
                           'React_asset_count': len(descriptor['compiled_React_asset_inventory']),
                           'core_reuse': core, 'core_old_commit': OLD_CORE,
                           'core_old_tree_equal_base': True,
                           'mu_reuse': mu, 'mu_commit': composition['mu_commit'],
                           'installation_manifest': ref(installation_path),
                           'installation_acl_readback': ref(HERE / 'acl-readback.json'),
                           'installer_current_user_single_ace': True},
               'source_modified': False, 'activation': 'NOT_STARTED', 'GUI_first_use': False,
               'model_calls': 0, 'real_API_calls': 0, 'database_operations': 0,
               'source_independent_review': 'PASS_AS_REPORTED_BY_INTEGRATION', 'package_independent_review': 'PENDING',
               'formal_increment': 0, 'parent_acceptance': False}
    with FINAL.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(json.dumps({'status': payload['status'], 'members': len(rows),
                      'package_non_gui_pass': package_cases['counts']['pass'],
                      'FINAL_sha256': sha(FINAL)}, ensure_ascii=False))

if __name__ == '__main__':
    main()
