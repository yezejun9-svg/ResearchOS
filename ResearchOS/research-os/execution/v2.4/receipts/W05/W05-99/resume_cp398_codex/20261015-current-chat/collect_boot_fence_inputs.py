import datetime
import hashlib
import json
import os
import subprocess
from pathlib import Path

R = Path('D:/作品集/ResearchOS/research-os')
B = Path(__file__).parent
E = R / 'execution/v2.4/receipts/W05/W05-99'
O = E / 'qualification_boot_fence_input_map_codex/20261015-current-chat'


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def digest(p):
    h = hashlib.sha256()
    size = 0
    with p.open('rb') as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
            size += len(chunk)
    return h.hexdigest(), size


def ref(p):
    sha, size = digest(p)
    return {'path': str(p), 'sha256': sha, 'bytes': size}


def new(p, obj):
    with p.open('x', encoding='utf8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write('\n')


O.mkdir(parents=True, exist_ok=False)
new(O / 'command.json', {'argv': [os.sys.executable, '-B', '-X', 'utf8', str(Path(__file__))], 'cwd': str(R), 'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'purpose': 'READONLY_PUBLIC_INSTALLED_ENTRY_RESOURCE_MAP', 'allowed_current_process_fields': ['ProcessId', 'ParentProcessId', 'ExecutablePath', 'CreationDate'], 'process_ids_exact': [54076, 69996], 'not_read': ['CommandLine', 'Environment', 'product DB', 'private keys', 'credentials'], 'mutations': 'only new own E evidence files; no ACL/launch/stop/DB/source/shared change'})
shared_paths = [R / 'execution/v2.4' / name for name in ['checkpoint.json', 'path_ownership.json', 'step_state.json', 'HANDOFF_RESUME_PACK.md']]
shared_before = {p: p.read_bytes() for p in shared_paths}
resume_path = B / 'continuation-cp516/RESUME.current.json'
resume = read(resume_path)
inputs = [ref(resume_path)]


def pinned(item):
    p = Path(item['path'])
    if not p.is_absolute():
        p = R / p
    got = ref(p)
    assert got['sha256'] == item['sha256'] and got['bytes'] == item['bytes']
    inputs.append(got)
    return p


normal = read(pinned(resume['normal_package_build_ref']))
baseline = read(pinned(resume['desktop_profile_package_manifest_ref']))
normal_scope = read(pinned(resume['activation_scope_ref']))
profile_scope = read(pinned(resume['desktop_profile_activation_scope_ref']))
normal_inventory_path = pinned(normal['package_full_inventory'])
normal_inventory = read(normal_inventory_path)
new(O / 'normal-inventory-input.json', normal_inventory)
new(O / 'baseline-members-input.json', baseline['package']['members'])
new(O / 'input-shapes.json', {'normal_inventory_kind': type(normal_inventory).__name__, 'normal_inventory_keys': list(normal_inventory) if isinstance(normal_inventory, dict) else None, 'baseline_members_kind': type(baseline['package']['members']).__name__, 'baseline_member_count': baseline['package']['member_count']})
roots = {str(Path(normal['new_package']).resolve()), str(Path(normal['baseline_package']).resolve()), str(Path(baseline['package']['root']).resolve())}
expected_by_root = {
    str(Path(normal['new_package']).resolve()): normal_inventory['files'],
    str(Path(baseline['package']['root']).resolve()): baseline['package']['members'],
}
assert set(expected_by_root) == roots
packages = []
for root_text in sorted(roots):
    root = Path(root_text)
    inventory = []
    expected = {item['path']: item for item in expected_by_root[root_text]}
    assert len(expected) == 58
    unlisted_names = []
    if root.exists():
        unlisted_names = [p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p.relative_to(root).as_posix() not in expected]
        for relative, old in sorted(expected.items()):
            p = root / relative
            if not p.exists() or not p.resolve().is_relative_to(root.resolve()):
                inventory.append({'relative_path': relative, 'status': 'MISSING_OR_ALIAS_NOT_READ'})
                continue
            current = ref(p)
            inventory.append({'relative_path': relative, **current, 'matches_frozen': current['sha256'] == old['sha256'] and current['bytes'] == old['bytes']})
    packages.append({'root': str(root), 'exists': root.exists(), 'files': inventory, 'unlisted_names_not_read': unlisted_names})
new(O / 'current-public-package-file-inventories.json', packages)
ps_script = "Get-CimInstance -ClassName Win32_Process -Filter 'ProcessId = 54076 OR ProcessId = 69996' | Select-Object ProcessId,ParentProcessId,ExecutablePath,@{Name='CreationDateUTC';Expression={$_.CreationDate.ToUniversalTime().ToString('o')}} | ConvertTo-Json -Depth 4"
argv = ['pwsh', '-NoProfile', '-Command', ps_script]
new(O / 'known-process-images.command.json', {'argv': argv, 'cwd': str(R), 'env': {'PSModulePath_present': bool(os.environ.get('PSModulePath'))}, 'no_commandline_or_environment_read': True})
p = subprocess.run(argv, cwd=R, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
(O / 'known-process-images.stdout.raw').write_bytes(p.stdout)
(O / 'known-process-images.stderr.raw').write_bytes(p.stderr)
new(O / 'known-process-images.result.json', {'native_exit': p.returncode})
process_records = []
process_error = None
if p.returncode:
    process_error = 'CIM_PUBLIC_METADATA_QUERY_FAILED'
elif p.stdout.strip():
    process_records = json.loads(p.stdout.decode('utf-8-sig'))
    if isinstance(process_records, dict):
        process_records = [process_records]
image_refs = []
for item in process_records:
    assert item['ProcessId'] in [54076, 69996]
    text = item.get('ExecutablePath')
    if not text:
        image_refs.append({'process_id': item['ProcessId'], 'status': 'IMAGE_PATH_UNAVAILABLE'})
        continue
    path = Path(text).resolve()
    allowed = path.is_relative_to(R.resolve()) or any(path.is_relative_to(Path(root)) for root in roots)
    if not allowed:
        image_refs.append({'process_id': item['ProcessId'], 'path': str(path), 'status': 'OUTSIDE_PUBLIC_PACKAGE_ALLOWLIST_NOT_READ'})
        continue
    image_refs.append({'process_id': item['ProcessId'], 'image_file': ref(path), 'status': 'CURRENT_FILE_HASH_RESOURCE_ONLY'})
new(O / 'current-known-process-image-files.json', {'records': process_records, 'image_files': image_refs, 'query_error': process_error, 'parent_pid_is_not_parent_native_identity': True, 'not_an_execution_closure_or_isolation_proof': True})
launcher_rg = ['rg', '-n', '--glob', '*.js', '--glob', '*.go', 'RESEARCHOS_CORE|coreExecutable|corePath|spawnCore|installation-manifest|runtime-verifier-installation|AcquireDataRootLease|LockDataRoot', 'apps/desktop/main', 'apps/control', 'ops/supervisor', 'ops/backup']
new(O / 'official-entry-source-locator.command.json', {'argv': launcher_rg, 'cwd': str(R), 'relevant_env': {'GIT_OPTIONAL_LOCKS': '0'}, 'scope': 'bounded current official entry source only'})
located = subprocess.run(launcher_rg, cwd=R, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
(O / 'official-entry-source-locator.stdout.raw').write_bytes(located.stdout)
(O / 'official-entry-source-locator.stderr.raw').write_bytes(located.stderr)
new(O / 'official-entry-source-locator.result.json', {'native_exit': located.returncode})
new(O / 'INPUT-MAP.json', {
    'schema': 'researchos.qualification-boot-fence-input-map.v1',
    'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'inputs': inputs,
    'known_package_roots': sorted(roots), 'current_public_package_file_counts': {v['root']: len(v['files']) for v in packages},
    'activation_scope_data_root': normal_scope.get('data_root'), 'profile_activation_scope_data_root': profile_scope.get('data_root'),
    'known_process_metadata': process_records, 'current_image_file_resources': image_refs,
    'limitations': [
        'Frozen activation scope is historical input, not fresh attestation that its launcher or data root is active.',
        'Only exact two known process IDs were queried; no full process census or descendant/closure inference.',
        'Current public package hashes do not attest process-loaded image bytes, native file ID/ACL, startup registrations or complete official entry coverage.',
        'No old-binary execution fence is deployed or accepted. No future Source class is implemented by this input map.',
        'A later plan must bind the actual installed legacy/current official entry inventory and supported trusted-operator boundary; arbitrary same-SID hostile programs are not silently included in this resource discovery.',
        'No native process handle, database, credential, private authority, ACL change, package activation, launch, stop or Restart was performed.',
    ], 'source_authority': False, 'actual_operation_authority': False, 'formal_increment': 0,
})
for path, data in shared_before.items():
    assert path.read_bytes() == data
new(O / 'COLLECTION-manifest.json', {'schema': 'researchos.readonly-boot-fence-inputs-manifest.v1', 'files': [ref(path) for path in sorted(O.iterdir()) if path.is_file()], 'helper': ref(Path(__file__)), 'source_authority': False, 'actual_operation_authority': False, 'shared_files_unchanged': True})
print(json.dumps({'manifest': ref(O / 'COLLECTION-manifest.json'), 'package_file_counts': {v['root']: len(v['files']) for v in packages}, 'process_ids_returned': [v['ProcessId'] for v in process_records], 'known_image_statuses': [v['status'] for v in image_refs], 'process_query_exit': p.returncode, 'locator_exit': located.returncode, 'shared_unchanged': True}, ensure_ascii=False))
