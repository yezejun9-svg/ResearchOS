"""Read sealed public metadata only; never open/load an OS DLL or start a child."""
import hashlib
import json
from pathlib import Path, PureWindowsPath

ROOT = Path('D:/作品集/ResearchOS/research-os')
HERE = Path(__file__).resolve().parent
N05 = ROOT / 'execution/v2.4/receipts/W05/W05-99'
N13 = ROOT / 'execution/v2.4/receipts/W13/W13-03'
READS = {}
UNION = {}


def ref(p):
    p = Path(p)
    assert p.is_relative_to(ROOT / 'execution/v2.4/receipts')
    b = p.read_bytes()
    return {'path': str(p), 'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}


def load(p, expected=None):
    p = Path(p)
    if not p.is_absolute():
        p = ROOT / p
    r = ref(p)
    if expected is not None:
        assert r['sha256'] == expected['sha256'] and r['bytes'] == expected['bytes']
    assert str(p) not in READS or READS[str(p)] == r
    READS[str(p)] = r
    return json.loads(p.read_text(encoding='utf-8')), r


def save(name, value):
    with (HERE / name).open('xb') as f:
        f.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    return ref(HERE / name)


def canon(v):
    if v.startswith('\\\\?\\'):
        v = v[4:]
    return str(PureWindowsPath(v))


def is_os(v):
    return canon(v).casefold().startswith('c:\\windows\\') and canon(v).casefold().endswith('.dll')


def walk(value, pointer=''):
    if isinstance(value, dict):
        yield pointer, value
        for k, v in value.items():
            yield from walk(v, pointer + '/' + k.replace('~', '~0').replace('/', '~1'))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from walk(v, pointer + '/' + str(i))


def add(row, basis, source, pointer, process_scope, extra=None):
    if not is_os(row['path']):
        return
    key = canon(row['path']).casefold()
    item = UNION.setdefault(key, {'path': canon(row['path']), 'original_path_spellings': [], 'versions': []})
    if row['path'] not in item['original_path_spellings']:
        item['original_path_spellings'].append(row['path'])
    version = next((x for x in item['versions'] if x['sha256'] == row['sha256'] and x['bytes'] == row['bytes']), None)
    if version is None:
        version = {'sha256': row['sha256'], 'bytes': row['bytes'], 'evidence': []}
        item['versions'].append(version)
    evidence = {'basis': basis, 'source_ref': source, 'locator': {'json_pointer': pointer}, 'process_scope': process_scope}
    if extra:
        evidence.update(extra)
    version['evidence'].append(evidence)


def rows(value):
    return [(p, x) for p, x in walk(value) if isinstance(x.get('path'), str) and 'sha256' in x and type(x.get('bytes')) is int]


rootmf_path = N05 / 'root14_evidence_sealed_codex/e1b3d1e2a8404f6997dab28af163d25c/manifest.json'
g2mf_path = N05 / 'integration_codex/root-g2-execute29-launch-r313/manifest.json'
rootmf, rootmr = load(rootmf_path)
g2mf, g2mr = load(g2mf_path)
assert g2mr['sha256'] == '7839b708640f215320a2d62d1e44914ec739575123deed98f1ad0de0504ad26b'
members = {}
for mf, mr in [(rootmf, rootmr), (g2mf, g2mr)]:
    for pointer, row in rows(mf):
        members[canon(row['path']).casefold()] = (row, mr, pointer)
        if is_os(row['path']):
            add(row, 'resourceinventory', mr, pointer, 'Root14 sealed input membership; no child-load inference')


def member_load(row):
    d, r = load(row['path'], row)
    return d, r


selected = []
for row, mr, pointer in members.values():
    basename = PureWindowsPath(row['path']).name
    if basename == 'controller_runtime_resources.json' or basename.endswith('.runtime.json') or basename in ['runtime.after_inner.json', 'runtime.before_inner.json', 'runtime.before_git.json']:
        selected.append((row, 'resourceinventory' if basename == 'controller_runtime_resources.json' else 'priorpointtime', 'Root14/controller Python process point observation; not native test child loading'))
    elif basename.startswith('python-os-runtime.') and basename.endswith('.json'):
        selected.append((row, 'g2point', 'G2 controller Python process; not Go/CLI/worker lifecycle'))
    elif basename == 'inputs.before-first.json':
        selected.append((row, 'g2vector', 'G2 sealed compilation/resource inventory; not load proof'))

g2vectors = {}
g2points = []
read_metadata = []
for row, kind, context in selected:
    value, r = member_load(row)
    read_metadata.append({'ref': r, 'kind': kind, 'container': type(value).__name__})
    if kind == 'g2point':
        g2points.append((value, r))
    else:
        for pointer, item in rows(value):
            if is_os(item['path']):
                basis = 'resourceinventory' if kind == 'g2vector' else kind
                add(item, basis, r, pointer, context)
                if kind == 'g2vector':
                    g2vectors[canon(item['path']).casefold()] = (item, r, pointer)
missing = []
for d, r in g2points:
    values = d.get('loaded_DLL_paths', []) if isinstance(d, dict) else []
    for i, p in enumerate(values):
        if isinstance(p, str) and is_os(p):
            key = canon(p).casefold()
            if key not in g2vectors:
                missing.append({'path': p, 'point_ref': r, 'locator': {'json_pointer': '/loaded_DLL_paths/' + str(i)}, 'sha256': None, 'bytes': None, 'state': 'UNKNOWN_NO_SAME_G2_VECTOR_HASH'})
            else:
                item, vr, ptr = g2vectors[key]
                add(item, 'priorpointtime', r, '/loaded_DLL_paths/' + str(i), 'G2 controller Python loaded_DLL_paths snapshot; not Go/CLI/worker load proof',
                    {'same_G2_hash_vector_ref': vr, 'same_G2_hash_locator': {'json_pointer': ptr}})

go_dir = N13 / 'desktop_go3_os_capture_revision_codex/01fc890602df43b89935fdbef4424137/actual-once'
gomf, gomr = load(go_dir / 'inner.manifest.json')
actual_row = next(x for _, x in rows(gomf) if PureWindowsPath(x['path']).name == 'inner.owned-result.json')
go, gor = member_load(actual_row)
assert gor['sha256'] == 'ac33a009a17657819c2bfe1c87f483fc9f074e87bb0b776ec777f2fc04504d8e'
result = go['result']
assert result['actual_exit'] == 0 and result['debug_capture']['mode'] == 'CREATE_OWN_CHILD_DEBUG_ONLY_THIS_PROCESS'
mods = result['debug_capture']['modules']
for i, m in enumerate(mods):
    p = m['path_from_actual_file_handle']
    if is_os(p):
        assert m['before'] == m['after']
        add({'path': p, **m['before']}, 'loaded_actual_handle', gor, '/result/debug_capture/modules/' + str(i),
            'Actual Go3 validator.test.exe DEBUG_ONLY_THIS_PROCESS component; not HTTP/CLI branch',
            {'original_image_event': m['event_code'], 'retained_handle_before_after_equal': True, 'owned_child_pid': result['owned_child_pid'],
             'creation_time_100ns': result['creation_time_100ns'], 'recorded_actual_exit': result['actual_exit'], 'trace_manifest_ref': gomr})

rootaudit, ra = load(N05 / 'root14_evidence_sealed_codex/e1b3d1e2a8404f6997dab28af163d25c/audit.json')
g2review, g2rr = load(N05 / 'provider_g2_bounded29_evidence_independent_review_codex/55a125ea5d084f7bb9a6e9eb4532c2c4/review.final.json')
union = sorted(UNION.values(), key=lambda x: x['path'].casefold())
flat = [{'path': x['path'], 'sha256': x['versions'][0]['sha256'], 'bytes': x['versions'][0]['bytes']} for x in union if len(x['versions']) == 1]
conflicts = [x for x in union if len(x['versions']) != 1]
unionref = save('windows-os-union.evidence.json', union)
flatref = save('windows-os-union.candidate-refs.json', flat)
sources = save('metadata-inputs.before.json', list(READS.values()))
for r in READS.values():
    assert ref(Path(r['path'])) == r
save('metadata-inputs.after.json', list(READS.values()))
save('findings.json', {
    'schema': 'researchos.windows-resource-readonly-observation.v1', 'actor': 'codex:/root/sources_parent_impl',
    'union_count': len(union), 'single_version_count': len(flat), 'historical_conflicts': conflicts,
    'basis_counts': {kind: sum(any(e['basis'] == kind for v in x['versions'] for e in v['evidence']) for x in union) for kind in ['loaded_actual_handle', 'priorpointtime', 'resourceinventory']},
    'metadata_files_read': len(READS), 'metadata_drift': 0, 'current_OS_files_opened_or_hashed': 0,
    'OS_modules_loaded_by_probe': 0, 'ProcessModule_or_ctypes_calls': 0, 'product_Go_Node_SQL_HTTP_MODEL_calls': 0,
    'historical_http_context': {'Root14_HTTP78': rootaudit.get('HTTP_calls_including_setup'), 'Root14_audit_ref': ra,
        'G2_loopback_MODEL4': g2review.get('loopback_MODEL_calls'), 'G2_review_ref': g2rr,
        'interpretation': 'These historical cohorts exercised HTTP, but their stored Python controller loaded-DLL snapshots do not prove DLL loads in native Go or child CLI processes.'},
    'G2_missing_hashes': missing, 'true_HTTP_CLI_child_loaded_module_trace_found': False,
    'network_specific_resource_completeness': 'UNKNOWN', 'future_CLI43_runtime_qualification': False,
    'union_ref': unionref, 'candidate_refs': flatref, 'metadata_inputs_ref': sources,
    'limitations': ['Only actual named sealed inputs were read; no generic Windows folder enumeration or speculative DLL names.',
        'Case and extended handle prefix normalized only for dedup; original spellings and raw locators retained.',
        'Resource inventory is not loaded proof. Python point snapshots are not child-process or lifetime evidence.',
        'Go3 nine OS DLL hFile records are for the component DEBUG process; they do not close prior normal-mode or network/CLI coverage.',
        'No current OS bytes were rehashed. Before future execution Root must separately freeze these resource candidates and stop on unknown actual modules according to that new scope.',
        'No source/canonical/index mutation or execution authority is produced.'],
})
print(json.dumps({'union': len(union), 'basis_counts': {kind: sum(any(e['basis'] == kind for v in x['versions'] for e in v['evidence']) for x in union) for kind in ['loaded_actual_handle', 'priorpointtime', 'resourceinventory']}, 'metadata_reads': len(READS), 'conflicts': len(conflicts), 'missing_hashes': len(missing), 'files': [unionref,flatref]}, ensure_ascii=False))
