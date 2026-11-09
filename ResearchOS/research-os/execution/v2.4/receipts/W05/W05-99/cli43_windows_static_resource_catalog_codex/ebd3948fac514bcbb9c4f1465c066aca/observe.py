"""Public byte-only inventory. Does not load PE images or call DLL APIs."""
import ast
import hashlib
import json
import pathlib
import re
import stat
import struct
import sys
from datetime import datetime, timezone

ROOT = pathlib.Path('D:/作品集/ResearchOS/research-os')
OUT = pathlib.Path(__file__).resolve().parent
SEALED = ROOT / 'execution/v2.4/receipts/W05/W05-99/integration_codex/cli43-public-resources-15ccd02e325b4d0e9384d66bb2a9d924'
OLD = ROOT / 'execution/v2.4/receipts/W05/W05-99/cli43_windows_resource_observation_codex/7a89658e87ad469dab9d17c80ed7270d/windows-os-union.candidate-refs.json'
SYSTEM = pathlib.Path('C:/Windows/System32')
READS = {}

def ref(p, raw):
    return {'path': str(p), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def read(p, expected=None):
    p = pathlib.Path(p)
    if not p.is_absolute():
        p = ROOT / p
    raw = p.read_bytes()
    r = ref(p, raw)
    if expected is not None:
        assert r['sha256'] == expected['sha256'] and r['bytes'] == expected['bytes'], str(p)
    key = str(p).casefold()
    if key in READS:
        assert READS[key] == r
    READS[key] = r
    return raw

def write(name, data):
    raw = (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    with (OUT / name).open('xb') as f:
        f.write(raw)
    return ref(OUT / name, raw)

def pe_imports(p, expected):
    b = read(p, expected)
    image = ref(p, b)
    def u16(o):
        assert 0 <= o <= len(b)-2
        return struct.unpack_from('<H', b, o)[0]
    def u32(o):
        assert 0 <= o <= len(b)-4
        return struct.unpack_from('<I', b, o)[0]
    assert b[:2] == b'MZ'
    pe = u32(0x3c)
    assert b[pe:pe+4] == b'PE\x00\x00'
    coff = pe + 4
    count, opt_size = u16(coff+2), u16(coff+16)
    assert 0 < count <= 96
    opt = coff + 20
    magic = u16(opt)
    assert magic in (0x10b, 0x20b)
    numoff, diroff = (92, 96) if magic == 0x10b else (108, 112)
    assert opt_size >= diroff and opt+opt_size <= len(b)
    ndirs = u32(opt+numoff)
    assert ndirs <= (opt_size-diroff)//8
    headers = u32(opt+60)
    sections = []
    for n in range(count):
        o = opt+opt_size+n*40
        assert o+40 <= len(b)
        sections.append({'name': b[o:o+8].rstrip(b'\x00').decode('ascii'),
                         'virtual_size': u32(o+8), 'rva': u32(o+12),
                         'raw_size': u32(o+16), 'raw_offset': u32(o+20)})
    def offset(rva, size=1):
        if rva < headers and rva+size <= min(headers, len(b)):
            return rva
        matches = [s for s in sections if s['rva'] <= rva and
                   rva+size <= s['rva']+s['raw_size']]
        assert len(matches) == 1, ('unmapped/ambiguous RVA', rva, size)
        o = matches[0]['raw_offset'] + rva-matches[0]['rva']
        assert o+size <= len(b)
        return o
    def dllname(rva):
        o = offset(rva)
        chars = bytearray()
        for i in range(512):
            c = b[offset(rva+i)]
            if c == 0:
                name = chars.decode('ascii')
                assert name and '/' not in name and '\\' not in name
                return name, o
            chars.append(c)
        raise ValueError('unterminated DLL name')
    found, directories, unknown = [], [], []
    for index, label, width in [(1, 'IMPORT_DIRECTORY', 20), (13, 'DELAY_IMPORT_DIRECTORY', 32)]:
        if index >= ndirs:
            directories.append({'index': index, 'status': 'DIRECTORY_NOT_PRESENT'})
            continue
        d = opt+diroff+index*8
        rva, size = u32(d), u32(d+4)
        directories.append({'index': index, 'entry_file_offset': d, 'rva': rva, 'size': size})
        if rva == size == 0:
            continue
        assert rva and size >= width and size <= 1024*1024
        terminated = False
        for n in range(size//width):
            o = offset(rva+n*width, width)
            values = struct.unpack_from('<'+'I'*(width//4), b, o)
            if not any(values):
                terminated = True
                break
            if index == 13 and values[0] != 1:
                unknown.append({'basis': label, 'descriptor_file_offset': o,
                                'reason': 'DELAY_VA_OR_ATTRIBUTES_UNSUPPORTED', 'attributes': values[0]})
                continue
            name_rva = values[3] if index == 1 else values[1]
            name, no = dllname(name_rva)
            found.append({'dll_name': name, 'basis': 'STATIC_PE_'+label,
                          'image_ref': image, 'descriptor_file_offset': o,
                          'name_rva': name_rva, 'name_file_offset': no})
        assert terminated, ('missing null descriptor', str(p), label)
    return {'image_ref': image, 'pe_header_file_offset': pe, 'optional_magic': hex(magic),
            'sections': sections, 'directories': directories, 'imports': found, 'unknown': unknown}

def main():
    start = datetime.now(timezone.utc).isoformat()
    # First filesystem inventory; no LoadLibrary, ctypes or ProcessModule calls.
    inventory = []
    for p in sorted(SYSTEM.iterdir(), key=lambda p: p.name.casefold()):
        if p.suffix.casefold() != '.dll':
            continue
        s = p.lstat()
        inventory.append({'path': str(p), 'name': p.name, 'bytes_lstat': s.st_size,
                          'regular_file': stat.S_ISREG(s.st_mode),
                          'reparse': bool(getattr(s, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT)})
    invref = write('system32-top-level-inventory.json', {'basis': 'FILESYSTEM_DIRECTORY_INVENTORY_ONLY', 'files': inventory})
    available = {x['name'].casefold(): x for x in inventory if x['regular_file'] and not x['reparse']}
    assert len(available) == sum(x['regular_file'] and not x['reparse'] for x in inventory)
    mfraw = read(SEALED/'manifest.json')
    assert hashlib.sha256(mfraw).hexdigest() == '421a6f850e2a1ce6a5b85210c74329775eaa373732bfda081f1e2770a07ee00a'
    mf = json.loads(mfraw)
    members = {pathlib.Path(x['path']).name: x for x in mf['entries']}
    compiler = json.loads(read(SEALED/'compiler-resources.json', members['compiler-resources.json']))
    runtime = json.loads(read(SEALED/'runtime-resources.json', members['runtime-resources.json']))
    oldraw = read(OLD)
    assert hashlib.sha256(oldraw).hexdigest() == 'a5792a28439774898918240da0b6c7fa90ee5d590411540b925b81979445b4b6'
    old = json.loads(oldraw)
    assert len(old) == 25 and len(runtime['files']) == 1213
    goroot = pathlib.Path(compiler['GOROOT'])
    src = goroot/'src'
    roots = ['runtime', 'syscall', 'internal/syscall/windows', 'net']
    selected, observations, arrays, texts = [], [], {}, {}
    for row in compiler['files']:
        p = pathlib.Path(row['path'])
        if not p.is_relative_to(src) or p.suffix not in ('.go', '.s') or p.name.endswith('_test.go'):
            continue
        rel = p.relative_to(src).as_posix()
        if not any(rel.startswith(prefix+'/') for prefix in roots):
            continue
        if 'testdata' in p.parts:
            continue
        raw = read(p, row)
        sr = ref(p, raw)
        text = raw.decode('utf-8')
        selected.append(sr)
        texts[rel] = (sr, text)
        for n, line in enumerate(text.splitlines(), 1):
            basis = None
            if re.search(r'\bNewLazy(?:System)?DLL\(', line) and not line.lstrip().startswith('//'):
                basis = 'STATIC_GO_LAZY_DLL_LITERAL'
            elif line.startswith('//go:cgo_import_dynamic '):
                basis = 'STATIC_GO_CGO_IMPORT_DIRECTIVE'
            if basis:
                for name in re.findall(r'"([^"\\]+\.dll)"', line, re.I):
                    observations.append({'dll_name': name, 'basis': basis, 'source_ref': sr,
                                         'line': n, 'literal_line': line, 'conditional_usage': True})
            m = re.match(r'\s*(\w+)\s*=\s*\[\.\.\.\]uint16\{(.*)\}\s*$', line)
            if m:
                tokens = [t.strip() for t in m[2].split(',')]
                if tokens[-1] == '0' and all(re.fullmatch(r"'[^'\\]'", t) for t in tokens[:-1]):
                    name = ''.join(t[1] for t in tokens[:-1])
                    if name.lower().endswith('.dll'):
                        arrays[(rel, m[1])] = (name, n, line)
    for rel, (sr, text) in texts.items():
        for n, line in enumerate(text.splitlines(), 1):
            for m in re.finditer(r'windowsLoadSystemLib\((\w+)\[:\]\)', line):
                name, declaration, literal = arrays[(rel, m[1])]
                observations.append({'dll_name': name, 'basis': 'STATIC_GO_UINT16_SYSTEM_LOAD_LITERAL',
                                     'source_ref': sr, 'line': n, 'call_line': line,
                                     'declaration_line': declaration, 'literal_line': literal,
                                     'system32_loader_lines': [247, 249], 'conditional_usage': True})
    images = [x for x in compiler['compiler_images'] if pathlib.Path(x['path']).name in ('go.exe','compile.exe','link.exe')]
    assert len(images) == 3
    pes = [pe_imports(pathlib.Path(x['path']), x) for x in images]
    for pe in pes:
        observations.extend(pe['imports'])
    byname, unknown = {}, [x for pe in pes for x in pe['unknown']]
    for obs in observations:
        name = obs['dll_name'].casefold()
        if name not in available:
            unknown.append({**obs, 'reason': 'API_SET_OR_NAME_NOT_IN_SYSTEM32_INVENTORY_NO_MAPPING_ATTEMPT'})
        else:
            byname.setdefault(name, []).append(obs)
    oldmap = {pathlib.Path(x['path']).name.casefold(): x for x in old}
    union, evidence = [], []
    for name in sorted(set(byname) | set(oldmap)):
        assert name in available, name
        p = pathlib.Path(available[name]['path'])
        raw = read(p, oldmap.get(name))
        r = ref(p, raw)
        union.append(r)
        evidence.append({'file': r, 'new_static_basis': byname.get(name, []),
                         'prior_25_ref': oldmap.get(name),
                         'prior_basis_locator': {'ref': ref(OLD, oldraw), 'json_pointer': '/'+str(old.index(oldmap[name]))} if name in oldmap else None,
                         'observed_loaded_in_this_task': False})
    runtime_files = {str(pathlib.Path(x['path'])).casefold(): x for x in runtime['files']}
    added = []
    for r in union:
        k = str(pathlib.Path(r['path'])).casefold()
        if k in runtime_files:
            assert r['sha256'] == runtime_files[k]['sha256'] and r['bytes'] == runtime_files[k]['bytes']
        else:
            runtime_files[k] = r
            added.append(r)
    source_ref = write('frozen-go-source-scan.json', {'roots': roots, 'testdata_and_tests_excluded': True, 'files': selected, 'observations': observations})
    pe_ref = write('pe-static-imports.json', {'format_reference': 'https://learn.microsoft.com/en-us/windows/win32/debug/pe-format', 'images': pes, 'execution': False})
    ev_ref = write('os-candidate-evidence.json', {'files': evidence, 'unknown': unknown})
    union_ref = write('system32-union.files.json', {'files': union})
    runtime_ref = write('runtime-v2.json', {'schema': 'researchos.cli43-public-runtime-resources.static-candidate.v2',
        'files': sorted(runtime_files.values(), key=lambda x: x['path'].casefold()),
        'old_basis_ref': members['runtime-resources.json'], 'added_static_candidate_files': added,
        'candidate_evidence_ref': ev_ref, 'actual_future_loaded_complete': None,
        'execution_authorized': False, 'unknown_loaded_module_policy': 'REFUSE_UNRECOGNIZED_RESOURCE',
        'inherited_1213_rows_rehashed_in_this_task': False,
        'system32_union_rows_rehashed_in_this_task': True})
    before = list(READS.values())
    before_ref = write('inputs.before.json', {'files': before})
    after = []
    for r in before:
        raw = pathlib.Path(r['path']).read_bytes()
        current = ref(pathlib.Path(r['path']), raw)
        assert current == r, ('INPUT_DRIFT', r['path'])
        after.append(current)
    after_ref = write('inputs.after.json', {'files': after, 'drift': []})
    summary = {'schema': 'researchos.windows-static-resource-candidate-observation.v1',
        'actor': 'codex:/root/sources_parent_impl', 'started_at': start,
        'ended_at': datetime.now(timezone.utc).isoformat(), 'system32_inventory_count': len(inventory),
        'go_source_files_scanned': len(selected), 'source_and_pe_literal_observations': len(observations),
        'pe_images': len(pes), 'static_distinct_system32_names': len(byname),
        'prior_os_count': len(old), 'os_union_count': len(union), 'added_os_count': len(added),
        'added_names': [pathlib.Path(x['path']).name for x in added],
        'runtime_v2_count': len(runtime_files), 'inputs_count': len(before), 'input_drift': [],
        'inventory_ref': invref, 'source_ref': source_ref, 'pe_ref': pe_ref,
        'candidate_evidence_ref': ev_ref, 'os_union_ref': union_ref, 'runtime_v2_ref': runtime_ref,
        'before_ref': before_ref, 'after_ref': after_ref, 'unknown_literal_rows': unknown,
        'open_gates': ['ACTUAL_FUTURE_CLI_NETWORK_CHILD_LOADED_MODULE_TRACE_UNKNOWN',
                       'API_SET_VIRTUAL_MAPPING_NOT_RESOLVED', 'RECURSIVE_OS_DLL_IMPORTS_NOT_PARSED',
                       'STATIC_LITERAL_USE_MAY_BE_DEAD_OR_CONDITIONAL',
                       'CURRENT_INPUT_POINT_HASH_NOT_FUTURE_PROCESS_HANDLE_ATTESTATION'],
        'DLL_loads_or_API_enumeration': 0, 'Go_Node_SQL_HTTP_model_calls': 0,
        'source_canonical_index_writes': 0, 'formal_increment': 0,
        'current_actual_HTTP_status': None, 'actual_child_loaded_trace': None}
    sr = write('findings.json', summary)
    print(json.dumps({'findings_ref': sr, 'added_names': summary['added_names'],
                      'runtime_v2_count': len(runtime_files), 'os_union_count': len(union),
                      'source_files': len(selected), 'inputs': len(before)}, ensure_ascii=False))

if __name__ == '__main__':
    main()
