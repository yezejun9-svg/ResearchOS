from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone

root = Path(__file__).resolve().parent
repo = Path('D:/作品集/ResearchOS/research-os')
wt = repo / '.local/worktrees/product-v1-workbench-20261104'
scope_path = repo / 'execution/product-v1/receipts/single-harness-20261104/workbench/scope.json'
scope = json.loads(scope_path.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert not (root / 'FROZEN.json').exists()
assert sha(scope_path) == '8311d3b82db9f17781ef8bba70d2e029cf3f5d95722650b58afdd4e8249bef0b'
contract = repo / 'execution/product-v1/contracts/harness.v1.interface.rev2.json'
assert sha(contract) == '046a49b2b1f82593fe86924913b2ee4d77152ac1cef7dbbb86562f6dfe0cfa1c'
pins = json.loads((root / 'checks-04/source-pins.json').read_text(encoding='utf-8'))
assert all(json.loads((root / 'checks-04/source-readback.json').read_text(encoding='utf-8')).values())
assert all(row['exit_code'] == 0 for row in json.loads((root / 'checks-04/results.json').read_text(encoding='utf-8')))
git = json.loads((root / 'git-final-01/result.json').read_text(encoding='utf-8'))
assert git['exact_scope'] and all(row['exit_code'] == 0 for row in git['commands'])
vite = json.loads((root / 'vite-05/result.json').read_text(encoding='utf-8'))
assert vite['exit_code'] == 0 and vite['all_source_unchanged'] and len(vite['outputs']) == 3
source_pins = {}
for name in scope['production_paths'] + scope['test_paths']:
    assert sha(wt / name) == pins[name] == sha(root / 'candidate' / name)
    raw = (wt / name).read_bytes()
    target = root / 'source-snapshot' / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    source_pins[name] = sha(target)

diagnostics = json.loads((root / 'AUTHOR-DIAGNOSTICS.json').read_text(encoding='utf-8'))
diagnostics['phase'] = 'source_frozen'
diagnostics['diagnostics'] += [
    {'origin':'apply_patch/3be7cb','classification':'author_patch_context','detail':'Initial combined activity patch expected a different existing Chinese label and failed verification. Readback3be7cb proved neither file was partially modified; corrected against actual technical-receipt text.'},
    {'origin':'12a9db','classification':'build_harness_input_failure','detail':'Vite01 actually exited1 because C snapshot omitted design-tokens.json. Raw command, inputs, stdout/stderr and result retained in vite-01; no product source assertion failed.'},
    {'origin':'exec-server-transport-closed/a120c2','classification':'tool_transport_uncertain_then_readback','detail':'A C build-helper patch reported transport closed. Readbacka120c2 proved the patch was not applied and vite-02 did not exist, before a new attempt was started. No uncertain call was replayed blindly.'},
    {'origin':'e29a92/55fa05','classification':'build_harness_early_input_failure','detail':'Vite02 helper actually exited1 while copying the absent WT design-tokens dependency, before Vite invocation. Partial snapshot retained; the actual public Main token file is pinned as an explicit common input in later attempts.'},
    {'origin':'fb5e60/00b619','classification':'source_added_eol_whitespace','detail':'The first combined Git read emitted diff-check errors for CRLF in newly added lines of an already mixed-EOL workbench file. Its aggregate exit0 came from later status and is not a diff-check success. Baseline EOL counts were read back; only added-line EOLs were normalized. Separate final Git commands951366 all exited0.'},
    {'origin':'158641/93ad4f','classification':'build_nonblocking_notice','detail':'Vite reports outDir outside the snapshot root will not be emptied. Each attempt uses a fresh C-owned directory, so no automatic deletion was requested. Notice preserved in raw stderr.'},
    {'origin':'56f919/484065','classification':'root_authorized_contract_revision','detail':'Root froze revision2 PLATFORM_POLICY. Old interface and the actual ten pre-revision source files are retained under contract-r1.interface.json and history/pre-interface-revision-02. New contract pin is exact.'},
]
(root / 'AUTHOR-DIAGNOSTICS.json').write_text(json.dumps(diagnostics, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
report = {
    'state': 'SOURCE_FROZEN_FOR_INDEPENDENT_REVIEW', 'construction_frozen': True, 'source_modification_permitted': False,
    'at': datetime.now(timezone.utc).isoformat(), 'worktree': str(wt), 'base_head': scope['base_head'],
    'scope': {'path': str(scope_path), 'sha256': sha(scope_path)},
    'interface': {'path': str(contract), 'sha256': sha(contract), 'revision': 2},
    'source_sha256': {name: source_pins[name] for name in scope['production_paths']},
    'test_sha256': {name: source_pins[name] for name in scope['test_paths']},
    'checks': {
        'node_syntax': {'exit_code':0, 'commands':4, 'raw_directory':'checks-04', 'tool_origin':'8ccd35'},
        'pure_tests': {'exit_code':0, 'tests':40, 'pass':40, 'fail':0, 'skip':0, 'raw_stdout':'checks-04/05.stdout', 'raw_stderr':'checks-04/05.stderr', 'tool_origin':'8ccd35'},
        'vite': {'exit_code':0, 'outputs':3, 'all_inputs_unchanged':True, 'raw_directory':'vite-05', 'tool_origin':'93ad4f'},
        'git': {'diff_check_exit':0, 'status_exit':0, 'stat_exit':0, 'exact_scope':True, 'raw_directory':'git-final-01', 'tool_origin':'951366'},
    },
    'prior_attempts_retained': ['checks-01','checks-02','checks-03','vite-01','vite-02','vite-03','vite-04','history/pre-interface-revision-02'],
    'limitations': ['No real Desktop render or Windows Desktop package built in this scope.', 'No real Host HTTP/Harness/Codex/model execution or permission/cancel qualification.', 'UNKNOWN recovery is GET-only; no manual replay UI is provided.', 'Original Mu controls and file/diff paths are preserved; its existing Host only implements CANCEL Run and RESUME session.'],
    'real_gui_runs':0, 'real_http_requests':0, 'real_native_or_harness_runs':0, 'model_runs':0, 'old_probe_replays':0,
    'formal_increment':0, 'product_acceptance_increment':0, 'commit_created':False, 'pending_processes':[],
    'independent_source_approval':False, 'native_execution_authorized':False,
}
(root / 'FROZEN.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
manifest = []
for path in sorted(root.rglob('*')):
    if path.is_file() and path.name != 'EVIDENCE_MANIFEST.json' and '__pycache__' not in path.parts:
        manifest.append({'path': path.relative_to(root).as_posix(), 'sha256': sha(path), 'bytes': path.stat().st_size})
(root / 'EVIDENCE_MANIFEST.json').write_text(json.dumps({'files': manifest, 'file_count': len(manifest), 'source_frozen_sha256': sha(root / 'FROZEN.json')}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'FROZEN_sha256':sha(root/'FROZEN.json'),'MANIFEST_sha256':sha(root/'EVIDENCE_MANIFEST.json'),'files':len(manifest),'source_paths':len(source_pins)}))
