"""Seal a reviewable package receipt without source or acceptance authority."""
import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path('D:/作品集/ResearchOS/research-os')
SOURCE = Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/coding-any-combined-build-20261014')
BUILD = SOURCE / '.local/builds/coding-any-combined-20261014'
RAW = SOURCE / '.local/receipts/coding-any-combined-20261014'
DEST = Path('C:/Users/yqyyds/.codex/researchos-resource-cache/normal-coding-any-a7ec7ebf-20261014')
HERE = Path(__file__).resolve().parent
SCOPE = ROOT / 'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261014-current-chat/continuation-cp465/package-build-scope.json'
SOURCE_REVIEW = ROOT / 'execution/v2.4/receipts/W05/W05-99/coding_any_independent_review_codex/20261014-current-chat/FINAL-report.json'
MU_REVIEW = ROOT / 'execution/v2.4/receipts/W17/W17-03/mu_m1_01_independent_review_codex/20261014-current-chat/FINAL-report.json'
FINAL = HERE / 'FINAL-manifest.json'
CANDIDATE = 'a7ec7ebf2d53848ea163b6115667b3e3761a6bd2'
TREE = '5b54aa0b8b94cb8012413efd401dc417671b06de'

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
    need(sha(SCOPE) == 'a575686adf3b4733c4a1cb01bf701fc190e50076c443b5aa9504aa3452c43a30', 'scope changed')
    need(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=SOURCE, text=True).strip() == CANDIDATE, 'source changed')
    need(subprocess.check_output(['git', 'rev-parse', 'HEAD^{tree}'], cwd=SOURCE, text=True).strip() == TREE, 'source tree changed')
    need(subprocess.check_output(['git', 'status', '--porcelain=v1'], cwd=SOURCE) == b'', 'source dirty')
    need(sha(SOURCE_REVIEW) == '0dc1d8e251b07f48d83648f7dfe02453bd7567dc23385feee28f9ea9723e19aa', 'coding any review changed')
    need(sha(MU_REVIEW) == '9418ec17e353f1dc7667ac30ab9eef17111d3f84a6304f531e1d16892ef2b526', 'M1 review changed')
    composition = load(HERE / 'composition.json')
    result = load(RAW / 'result.json')
    core_result = load(RAW / 'core-result.json')
    descriptor_path = DEST / 'apps/desktop/resources/client-wire/descriptor.json'
    descriptor = load(descriptor_path)
    acl = load(HERE / 'acl-readback.json')
    installation_path = DEST / 'apps/desktop/resources/control/runtime-verifier-installation.json'
    installation = load(installation_path)
    need(result['status'] == 'BUILT_NOT_TESTED' and not result['drift'], 'build drift')
    need(core_result['candidate_commit'] == CANDIDATE and core_result['tree'] == TREE and
         core_result['native_exit'] == 0 and not core_result['drift'], 'Core build drift')
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
    control = DEST / 'apps/desktop/resources/control/researchos-control.exe'
    need(sha(control) == core_result['control_binary_sha256'] and
         sha(verifier) == core_result['runtime_verifier_binary_sha256'], 'fresh Core binary mismatch')
    for name in ('core-control', 'core-runtime-verifier'):
        stamp_text = (RAW / (name + '-go-version-m.stdout')).read_text(encoding='utf-8')
        need('vcs.revision=' + CANDIDATE in stamp_text and 'vcs.modified=false' in stamp_text,
             'fresh Core VCS stamp mismatch: ' + name)
    need(installation['executable'] == str(verifier) and installation['executable_hash'] == 'sha256:' + sha(verifier), 'installer binding')
    need(installation['source_commit'] == CANDIDATE, 'installer Core provenance')
    need(acl['status'] == 'LIVE_READBACK_PASS' and acl['protected'] and acl['rule_count'] == 1 and
         acl['current_user_sid'] == acl['single_ace_identity'] and acl['manifest_sha256'] == sha(installation_path), 'ACL readback')
    validator = DEST / 'apps/desktop/resources/client-wire/researchos-client-wire-validator.exe'
    need(sha(validator) == descriptor['binary_sha256'] == core_result['validator_binary_sha256'], 'validator changed')
    stamp = (RAW / 'validator-go-version-m.stdout').read_text(encoding='utf-8')
    need('vcs.revision=' + CANDIDATE in stamp and 'vcs.modified=false' in stamp, 'validator stamp')
    suite = (RAW / 'validator-suite-corrected.stdout').read_text(encoding='utf-8')
    top_pass = re.findall(r'^--- PASS: ([^\s]+)', suite, flags=re.M)
    all_pass_count = suite.count('--- PASS:')
    need(suite.rstrip().endswith('PASS') and len(top_pass) == 4 and all_pass_count == 71 and '--- FAIL:' not in suite, 'validator suite')
    package_cases = load(RAW / 'package-cases.invocation.json')
    need(package_cases['native_exit'] == 0 and package_cases['counts'] ==
         {'tests': 214, 'pass': 214, 'fail': 0, 'skipped': 0, 'cancelled': 0} and
         package_cases['environment']['RESEARCHOS_DESKTOP_WIRE_ROOT'] == str(DEST / 'apps/desktop'), 'actual package cases')
    invocations = {}
    failed_invocations = {}
    for path in sorted(RAW.glob('*.invocation.json')):
        row = load(path)
        native = row.get('native_exit', row.get('exit'))
        target = invocations if native == 0 else failed_invocations
        target[path.stem] = {'receipt': ref(path), 'actualargv': row.get('actualargv', row.get('argv')),
                             'cwd': row['cwd'], 'native_exit': native}
    need({'go-build.invocation', 'react-build.invocation', 'validator-suite.invocation',
          'validator-go-version-m.invocation', 'package-cases.invocation'} <= set(invocations) | set(failed_invocations), 'missing raw command receipts')
    need(set(failed_invocations) == {'validator-suite.invocation'} and
         failed_invocations['validator-suite.invocation']['native_exit'] == 1 and
         'validator-suite-corrected.invocation' in invocations, 'unexpected failed raw command')
    core = {x['path']: {'sha256': x['sha256'], 'source_commit': x['source_commit']} for x in rows
            if x['component'] == 'FRESH_CORE_FROM_CURRENT_MAIN'}
    mu = {x['path']: {'sha256': x['sha256'], 'source_commit': x['source_commit']} for x in rows
          if x['component'] == 'REUSED_MU_FIXED'}
    need(len(core) == 2 and composition['migration_numbered_inventory'] == list(range(1, 25)), 'Core or migration inventory')
    payload = {'schema': 'researchos.cp465-coding-any-combined-desktop-build-manifest.v1',
               'status': 'ASSEMBLED_HASHED_NOT_LAUNCHED_PENDING_INDEPENDENT_PACKAGE_REVIEW',
               'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'owner': 'codex:/root/status_desktop_builder', 'model': 'gpt-6-sol', 'reasoning_effort': 'high',
               'scope': ref(SCOPE), 'coding_any_source_review': ref(SOURCE_REVIEW),
               'mu_m1_source_review': ref(MU_REVIEW),
               'source': {'worktree': str(SOURCE), 'candidate_commit': CANDIDATE,
                                             'main_commit_at_scope': CANDIDATE,
                                             'candidate_tree': TREE, 'candidate_clean': True,
                                             'changed_paths_exact': composition['changed_paths_exact']},
               'build': {'output': str(BUILD), 'raw_receipts': str(RAW),
                         'input_count': composition['bound_full_input_count'],
                         'input_digest': result['build_input_digest'], 'input_drift': [],
                         'inputs_before': ref(RAW / 'inputs.before.json'),
                         'inputs_after': ref(RAW / 'inputs.after.json'),
                         'core_input_count': core_result['input_count'],
                         'core_input_digest': core_result['input_digest'],
                         'core_inputs_before': ref(RAW / 'core-inputs.before.json'),
                         'core_inputs_after': ref(RAW / 'core-inputs.after.json'),
                         'core_result': ref(RAW / 'core-result.json'),
                         'compiler_work_archive': ref(RAW / 'compiler-work-archive.json'),
                         'tools_before': ref(RAW / 'tools.before.json'),
                         'builder': ref(SOURCE / 'apps/desktop/build-validator.py'),
                         'result': ref(RAW / 'result.json'), 'invocations': invocations,
                         'failed_invocations_preserved': failed_invocations,
                         'compiler_input_boundary': 'Broad Go list inventory; -work/-x compiler commands retained raw. No claim that broad inventory is only selected inputs.'},
               'local_tests': {'validator_top_level_pass_count': len(top_pass),
                               'validator_top_level_tests': top_pass,
                               'validator_all_pass_markers': all_pass_count,
                               'package_validator_non_gui_counts': package_cases['counts'],
                               'package_validator_non_gui_receipt': ref(RAW / 'package-cases.invocation.json'),
                               'first_validator_suite_failed_due_to_cwd': True,
                               'corrected_validator_suite_receipt': ref(RAW / 'validator-suite-corrected.invocation.json'),
                               'renderer_gui_cases_executed': False},
               'package': {'root': str(DEST), 'member_count': len(rows),
                           'bytes': sum(x['bytes'] for x in rows), 'members': rows,
                           'composition': ref(HERE / 'composition.json'),
                           'descriptor': ref(descriptor_path),
                           'module_count': len(descriptor['exact_module_source_inventory']),
                           'React_asset_count': len(descriptor['compiled_React_asset_inventory']),
                           'fresh_core': core, 'core_source_commit': CANDIDATE,
                           'mu_reuse': mu, 'mu_commit': composition['mu_commit'],
                           'migration_numbered_inventory': composition['migration_numbered_inventory'],
                           'installation_manifest': ref(installation_path),
                           'installation_acl_readback': ref(HERE / 'acl-readback.json'),
                           'installer_current_user_single_ace': True},
               'source_modified': False, 'activation': 'NOT_STARTED', 'GUI_first_use': False,
               'model_calls': 0, 'real_API_calls': 0, 'database_operations': 0,
               'source_independent_review': 'APPROVED_LIMITED_SCOPES', 'package_independent_review': 'PENDING',
               'formal_increment': 0, 'parent_acceptance': False}
    with FINAL.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(json.dumps({'status': payload['status'], 'members': len(rows),
                      'package_non_gui_pass': package_cases['counts']['pass'],
                      'FINAL_sha256': sha(FINAL)}, ensure_ascii=False))

if __name__ == '__main__':
    main()
