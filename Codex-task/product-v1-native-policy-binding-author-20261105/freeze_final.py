from pathlib import Path
import hashlib, json, shutil

task = Path(r'C:\Users\yqyyds\Documents\Codex\2026-11-04\task')
author = Path(__file__).resolve().parent
snapshot = author / 'test02-source'
out = author / 'final'
assert not out.exists(), 'final freeze already exists'
root = Path(r'D:\作品集\ResearchOS\research-os')
wt = root / '.local/worktrees/product-v1-native-policy-binding-20261105'
scope = json.loads((root / 'execution/product-v1/receipts/single-harness-20261104/native-policy-binding/scope.json').read_text(encoding='utf-8'))
test02 = json.loads((snapshot / 'manifest.json').read_text(encoding='utf-8'))
changed = {}
unchanged = {}
for rel, pin in test02['source_hashes'].items():
    baseline = scope['baseline_sha256'][rel]
    raw = (wt / rel).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == pin, ('WT drift', rel)
    if baseline == pin:
        unchanged[rel] = pin
        continue
    changed[rel] = {'baseline_sha256': baseline, 'source_sha256': pin, 'bytes': len(raw)}
    src = snapshot / 'patches' / (rel.replace('/', '__') + '.patch')
    dst = out / 'patches' / src.name
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
assert len(changed) == 9 and len(unchanged) == 2
source = {'scope_id': scope['scope_id'], 'base_head': scope['base_head'], 'test02_scope_sha256': '3fd6cea77bc60f44df20b63e35e58b2a60f9c40f7e728007331795b583a3d76d', 'changed': changed, 'reviewed_unchanged_input': unchanged, 'source_snapshot': str(snapshot / 'source')}
(out / 'SOURCE.json').write_text(json.dumps(source, indent=2) + '\n', encoding='utf-8')
diagnostics = {
    'mode_key_wrong_namespace': {'origin': 'native-policy-A:mode-key-wrong-namespace', 'prior_candidate': str(author / 'prior-mode-key'), 'state': 'source-only, no Native/Go run', 'fix': 'global windows.sandbox="mxc" in canonical builder and independent argv tests'},
    'source_binding_toctou': {'origin': 'independent source review', 'fix': 'Host-sealed binding ref/principal/project/access/revision/canonical path digest; compare at admission, scan, launch and BeforeResume against selected driver source'},
    'ready_with_reason': {'origin': 'independent source review', 'fix': 'shared readiness predicate rejects every nonempty reason even when provider claims READY'},
    'public_dto_enum': {'origin': 'author static check', 'fix': 'preserved harness.v1 workspace_read_scope=UNVERIFIED and enforcement_verified=false'},
    'runtime_limit': 'Production NewCodexCLI and actual Host composition remain UNVERIFIED; no same-start native effective-profile barrier exists in Slice A. No Native CLI/model/probe/auth executed by author.',
    'history': 'Historical Get/List remains readable; old input without source snapshot fails new admission and is never automatically requeued.',
}
(out / 'DIAGNOSTICS.json').write_text(json.dumps(diagnostics, indent=2) + '\n', encoding='utf-8')
runs = {}
for n in (1, 2):
    name = f'product-v1-native-policy-tests-0{n}'
    src = task / 'product-v1-owned-verification-20261104' / 'runs' / name
    dest = out / 'runs' / name
    dest.mkdir(parents=True, exist_ok=True)
    run = json.loads((src / 'RESULT.json').read_text(encoding='utf-8'))
    assert run['status'] == 'COMPLETED_OWNED_JOB_STOPPED' and run['root_exit_code'] == 0 and run['stop_proved'] and not run['input_drift']
    for file in ('RESULT.json', 'stdout.raw', 'stderr.raw'):
        shutil.copyfile(src / file, dest / file)
    runs[name] = {'scope_sha256': run['scope_sha256'], 'exit_code': run['root_exit_code'], 'stop_proved': run['stop_proved'], 'raw': run['raw']}
manifest = {'scope_id': scope['scope_id'], 'source': 'SOURCE.json', 'diagnostics': 'DIAGNOSTICS.json', 'runs': runs, 'files_sha256': {}}
for file in sorted(out.rglob('*')):
    if file.is_file(): manifest['files_sha256'][str(file.relative_to(out)).replace('\\', '/')] = hashlib.sha256(file.read_bytes()).hexdigest()
(out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'final': str(out), 'changed': len(changed), 'unchanged': len(unchanged), 'archived_files': len(manifest['files_sha256'])}))
