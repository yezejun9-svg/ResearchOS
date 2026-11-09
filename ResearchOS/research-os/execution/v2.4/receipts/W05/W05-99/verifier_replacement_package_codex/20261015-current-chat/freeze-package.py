"""Read-only final package audit and evidence freeze."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/作品集/ResearchOS/research-os')
SOURCE = ROOT / '.local/worktrees/verifier-replacement-20261014'
HERE = Path(__file__).resolve().parent
OLD = Path('C:/Users/yqyyds/.codex/researchos-resource-cache/normal-coding-profile-c8b7adab-20261014')
DEST = Path('C:/Users/yqyyds/.codex/researchos-resource-cache/normal-verifier-replacement-4f4023-20261015')
COMMIT = '4f4023c956f84d65743f39ce77d6c8899a21ada1'
TREE = '3db13a15cc52b2b0bd75cae3452c66509a9f55c9'
CONTROL = 'apps/desktop/resources/control/researchos-control.exe'
VERIFIER = 'apps/desktop/resources/control/runtime-verifier.exe'
INSTALL = 'apps/desktop/resources/control/runtime-verifier-installation.json'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def ref(path):
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': sha(path)}

def need(ok, reason):
    if not ok:
        raise RuntimeError(reason)

def load(name):
    return json.loads((HERE / name).read_bytes())

def main():
    final = HERE / 'FINAL-manifest.json'
    need(not final.exists(), 'final already exists')
    need(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=SOURCE).decode().strip() == COMMIT, 'source HEAD')
    need(subprocess.check_output(['git', 'rev-parse', 'HEAD^{tree}'], cwd=SOURCE).decode().strip() == TREE, 'source tree')
    need(subprocess.check_output(['git', 'status', '--porcelain=v1', '--untracked-files=no'], cwd=SOURCE) == b'', 'source dirty')
    rows = load('package-inventory.json')
    need(rows['member_count'] == 58 and rows['unchanged_c8_member_count'] == 55, 'inventory count')
    package_files = {p.relative_to(DEST).as_posix(): p for p in DEST.rglob('*') if p.is_file()}
    need(len(package_files) == 58 and set(package_files) == {r['path'] for r in rows['files']}, 'package file census')
    need(all(not p.is_symlink() for p in package_files.values()), 'package symlink')
    need(all(sha(package_files[r['path']]) == r['sha256'] and package_files[r['path']].stat().st_size == r['bytes']
             for r in rows['files']), 'package member drift')
    old_rows = {r['path']: r for r in json.loads((ROOT / 'execution/v2.4/receipts/W05/W05-99/coding_profile_desktop_build_codex/20261014-current-chat/composition.json').read_bytes())['package_files']}
    need(len(old_rows) == 58 and all(sha(OLD / rel) == old_rows[rel]['sha256'] for rel in old_rows), 'baseline package drift')
    need(all(sha(DEST / rel) == old_rows[rel]['sha256'] for rel in rows['unchanged_paths']), 'unchanged asset drift')
    need({CONTROL, VERIFIER, INSTALL} == set(old_rows) - set(rows['unchanged_paths']), 'changed member set')
    install = json.loads((DEST / INSTALL).read_bytes())
    old_install = json.loads((OLD / INSTALL).read_bytes())
    need({k: v for k, v in install.items() if k not in ('executable', 'executable_hash', 'source_commit')} ==
         {k: v for k, v in old_install.items() if k not in ('executable', 'executable_hash', 'source_commit')}, 'loader contract drift')
    need(install['executable'] == str(DEST / VERIFIER) and install['executable_hash'] == 'sha256:' + sha(DEST / VERIFIER)
         and install['source_commit'] == COMMIT, 'installation mismatch')
    native = load('acl-native-readback-02.json')
    need(len(native) == 2 and all(row['valid'] for row in native), 'native ACL fail')
    by_path = {row['path']: row for row in native}
    for rel in (VERIFIER, INSTALL):
        path = DEST / rel
        need(str(path) in by_path and by_path[str(path)]['sha256'] == sha(path), 'native ACL hash mismatch')
    counts = load('package-wire-summary.json')['counts']
    need(counts == {'tests': 214, 'pass': 214, 'fail': 0, 'skipped': 0, 'cancelled': 0}, 'wire smoke count')
    for name, expected in [('package-wire-214', 0), ('verifier-no-pipes-rejected', 2),
                           ('control-incomplete-replacement-rejected', 2),
                           ('control-packaged-buildinfo', 0), ('runtime-verifier-packaged-buildinfo', 0)]:
        need(load(name + '.json')['native_exit'] == expected, name + ' actual exit')
    build = load('build-result.json')
    need(build['source_commit'] == COMMIT and build['source_tree'] == TREE and build['drift'] == [] and
         build['binaries']['control']['sha256'] == sha(DEST / CONTROL) and
         build['binaries']['runtime-verifier']['sha256'] == sha(DEST / VERIFIER), 'build binding')
    before, after = load('compiler-module-inputs.before.json'), load('compiler-module-inputs.after.json')
    need(len(before) == len(after) == build['input_count'] and all(a['sha256'] == b['current_sha256']
         for a, b in zip(before, after)), 'compiler input bound')
    evidence = []
    for p in sorted(HERE.rglob('*')):
        if p.is_file() and p != final and '__pycache__' not in p.parts:
            evidence.append({'relative_path': p.relative_to(HERE).as_posix(), 'bytes': p.stat().st_size, 'sha256': sha(p)})
    report = {'schema': 'researchos.verifier-replacement-normal-package-final/1',
              'at': dt.datetime.now(dt.timezone.utc).isoformat(),
              'owner': 'codex:/root/verifier_package_builder', 'model': 'gpt-6-sol', 'reasoning_effort': 'high',
              'status': 'BUILT_BOUNDED_SMOKE_PASSED_AWAITING_INDEPENDENT_PACKAGE_REVIEW',
              'source_commit': COMMIT, 'source_tree': TREE, 'source_worktree': str(SOURCE),
              'baseline_package': str(OLD), 'new_package': str(DEST),
              'changed_members_exact': [CONTROL, VERIFIER, INSTALL],
              'unchanged_member_count': 55, 'member_count': 58,
              'core_binary': ref(DEST / CONTROL), 'runtime_verifier_binary': ref(DEST / VERIFIER),
              'installation_manifest': ref(DEST / INSTALL),
              'package_full_inventory': ref(HERE / 'package-inventory.json'),
              'composition': ref(HERE / 'composition.json'),
              'compiler_module_inputs_before': ref(HERE / 'compiler-module-inputs.before.json'),
              'compiler_module_inputs_after': ref(HERE / 'compiler-module-inputs.after.json'),
              'native_acl_readback': ref(HERE / 'acl-native-readback-02.json'),
              'wire_smoke': ref(HERE / 'package-wire-summary.json'),
              'prior_failures': ref(HERE / 'attempt-ledger.json'),
              'evidence_file_count': len(evidence), 'evidence_files': evidence,
              'skipped': ['actual Desktop/GUI/product DataRoot/Host/provider/model/qualification/registration',
                          'independent package review and Root normal reopen'],
              'temporary_pycache_cleanup': 'BLOCKED_BY_AUTOMATIC_POLICY; single pyc retained outside package',
              'formal_increment': 0}
    with final.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(json.dumps({'status': report['status'], 'package': str(DEST), 'evidence_files': len(evidence),
                      'manifest_sha256': sha(final), 'formal_increment': 0}))

if __name__ == '__main__':
    main()
