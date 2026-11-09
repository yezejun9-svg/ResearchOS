"""Read-only PE graph and frozen Scope7 event analysis. Never loads an image."""
import ast, collections, hashlib, json, pathlib, struct

ROOT = pathlib.Path(__file__).resolve().parents[7]
OUT = pathlib.Path(__file__).resolve().parent
SYS = pathlib.Path('C:/Windows/System32')
UID = '9eccde97a9fa4815941768cacaf590dc'
REG = ROOT / ('execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r339-' + UID)
EXEC = ROOT / ('execution/v2.4/receipts/W13/W13-03/desktop58_finite_executor_codex/' + UID)
REVIEW = ROOT / 'execution/v2.4/receipts/W13/W13-03/desktop58_scope7_failure_independent_review_codex/1ed40efbf3ed4b51b4ccf89b8f6a9fcd'
PARSER = ROOT / 'execution/v2.4/receipts/W13/W13-03/desktop58_conhost_resource_diagnostic_codex/0a2dfbb74d3b4f0fb12192390b80cbea/pe_reader.py'
CAP = 2048
READS = {}

def ref(p, raw=None):
    p = pathlib.Path(p)
    if raw is None: raw = p.read_bytes()
    return {'path': p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else str(p), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def read(p, expected=None):
    p = pathlib.Path(p); raw = p.read_bytes(); r = ref(p,raw)
    if expected is not None: assert r['sha256'] == expected['sha256'] and r['bytes'] == expected['bytes'], p
    key = str(p).casefold()
    if key in READS: assert READS[key] == r, p
    READS[key] = r
    return raw

def put(name, value):
    p = OUT/name; raw = (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf8')
    with p.open('xb') as f: f.write(raw)
    return ref(p,raw)

def pure_parser():
    raw = read(PARSER); tree = ast.parse(raw.decode('utf8'))
    allowed = {'u16','u32','u64','cstr','parse_pe'}
    assert all((isinstance(n,ast.Import) and [x.name for x in n.names] == ['struct']) or (isinstance(n,ast.FunctionDef) and n.name in allowed) for n in tree.body)
    assert {n.name for n in tree.body if isinstance(n,ast.FunctionDef)} == allowed
    ns = {}; exec(compile(tree,str(PARSER),'exec'),ns)
    return ns['parse_pe'],ref(PARSER,raw)

def apiset_map(raw):
    # Windows v6 namespace from the file's .apiset PE section. Each entry and
    # UTF-16 span is range checked; values with qualifiers remain alternatives.
    pe = struct.unpack_from('<I',raw,0x3c)[0]; coff = pe+4
    count = struct.unpack_from('<H',raw,coff+2)[0]; opt = coff+20
    optsize = struct.unpack_from('<H',raw,coff+16)[0]
    section = None
    for i in range(count):
        at = opt+optsize+i*40
        if raw[at:at+8].rstrip(b'\0') == b'.apiset':
            virtual_size,_,raw_size,raw_off = struct.unpack_from('<IIII',raw,at+8)
            assert raw_off+raw_size <= len(raw) and virtual_size <= raw_size
            section = raw[raw_off:raw_off+virtual_size]
    assert section is not None
    version,size,flags,n,entry_at,hash_at,hashfactor = struct.unpack_from('<7I',section,0)
    assert version == 6 and size == len(section) and n < 10000 and entry_at+n*24 <= size
    def utf(off,length):
        assert length%2 == 0 and off+length <= size
        return section[off:off+length].decode('utf-16le')
    out = {}
    for i in range(n):
        flags,no,nl,hl,vo,vc = struct.unpack_from('<6I',section,entry_at+i*24)
        assert vc < 100 and vo+vc*20 <= size
        name = utf(no,nl).casefold(); assert name and name not in out
        vals = []
        for j in range(vc):
            vf,vno,vnl,vvo,vvl = struct.unpack_from('<5I',section,vo+j*20)
            vals.append({'qualifier':utf(vno,vnl),'host':utf(vvo,vvl),'flags':vf})
        out[name] = vals
    return out,{'version':version,'count':n,'section_bytes':len(section),'entry_offset':entry_at,'hash_offset':hash_at,'hash_factor':hashfactor}

def path_index():
    names = {}
    for p in SYS.iterdir():
        if p.suffix.casefold() not in ('.dll','.exe'): continue
        key = p.name.casefold(); assert key not in names
        names[key] = p
    return names

def main():
    parser, parser_ref = pure_parser()
    schema_path = SYS/'apisetschema.dll'; schema_raw = read(schema_path)
    amap, schema_meta = apiset_map(schema_raw)
    schema_ref = ref(schema_path,schema_raw)
    runtime_path = REG/'runtime-resources.desktop58.json'; catalog_path = REG/'resource-catalog.desktop58.json'
    binding = json.loads(read(REG/'binding.json'))
    runtime = json.loads(read(runtime_path,binding['runtime_resources_ref']))
    catalog = json.loads(read(catalog_path))
    assert len(runtime['files']) == 1303
    frozen = {pathlib.Path(x['path']).name.casefold():x for x in runtime['files'] if str(x['path']).casefold().startswith(str(SYS).casefold())}
    catalog_files = {pathlib.Path(x['path']).name.casefold():x for x in catalog['files'] if str(x['path']).casefold().startswith(str(SYS).casefold())}
    catalog_images = {pathlib.Path(x['path']).name.casefold():x for x in catalog['images'] if str(x['path']).casefold().startswith(str(SYS).casefold())}
    names = path_index(); queue = collections.deque([('net.exe',0),('net1.exe',0)])
    visited = {}; edges = []; unresolved = []; capped = False
    while queue:
        name,depth = queue.popleft(); key = name.casefold()
        if key in visited: continue
        if len(visited) >= CAP: capped = True; unresolved.append({'name':name,'reason':'CAP_2048'}); continue
        p = names.get(key)
        if p is None: unresolved.append({'name':name,'reason':'NO_TOP_LEVEL_SYSTEM32_FILE'}); continue
        if p.is_symlink() or p.is_junction(): unresolved.append({'name':name,'reason':'SYSTEM32_REPARSE'}); continue
        raw = read(p); file_ref = ref(p,raw)
        try: pe = parser(raw)
        except Exception as exc:
            unresolved.append({'name':name,'reason':'PE_PARSE_ERROR','error':repr(exc),'file_ref':file_ref}); continue
        visited[key] = {'file_ref':file_ref,'depth':depth,'pe':pe,'frozen_runtime_ref':frozen.get(key),'frozen_catalog_file_ref':catalog_files.get(key),'frozen_catalog_image_ref':catalog_images.get(key),'actual_loaded_proven':False}
        for kind in ('imports','delay_imports'):
            for imported in pe[kind]:
                low = imported.casefold(); edge = {'parent':key,'kind':kind,'import_name':imported,'static_only':True}
                if low.startswith(('api-','ext-')):
                    vals = amap.get(low.removesuffix('.dll'))
                    edge['api_set_values'] = vals
                    if vals is None:
                        edge['resolution'] = 'API_SET_NAME_MISSING_IN_SCHEMA'; unresolved.append(edge.copy())
                    else:
                        hosts = sorted({x['host'].casefold() for x in vals if x['host']})
                        edge['resolution'] = 'API_SET_V6_STATIC_HOST_CANDIDATES_NOT_LOADER_PROOF'
                        if not hosts: unresolved.append({**edge,'reason':'API_SET_NO_HOST'})
                        for host in hosts: queue.append((host,depth+1))
                elif low in names:
                    edge['resolution'] = 'EXPLICIT_SYSTEM32_FILE_CANDIDATE_NOT_LOADER_PROOF'
                    queue.append((low,depth+1))
                else:
                    edge['resolution'] = 'NO_TOP_LEVEL_SYSTEM32_FILE'; unresolved.append(edge.copy())
                edges.append(edge)
    # All observed debug facts are read from the frozen original invocation.
    invocation_path = EXEC/'build-current58.invocation.json'; invraw = read(invocation_path)
    invocation = json.loads(invraw); capture = invocation['result']['debug_capture']
    review = json.loads(read(REVIEW/'review.json'))
    assert capture['create_process_count'] == capture['exit_process_count'] == 806
    assert review['first_rejected_load']['before'] == {k:visited['net.exe']['file_ref'][k] for k in ('sha256','bytes')}
    pairs = json.loads(read(REVIEW/'process-event-pairs.json',review['process_event_pairs_ref']))['pairs']
    final = []
    for generation in (803,804,805,806):
        row = next(x for x in pairs if x['generation']==generation)
        images = [x for x in capture['modules'] if x['event_code']==3 and x['pid']==row['pid']]
        final.append({'generation':generation,'pair':row,'create_process_image_facts':images})
    actual_net1 = [x for x in capture['modules'] if str(x.get('path_from_actual_file_handle','')).casefold().endswith('\\net1.exe')]
    builder_source_ref = json.loads(read(REG/'scope_registration.json'))['builder_source_ref']
    builder_source_path = pathlib.Path(builder_source_ref['path']);builder_source_raw=read(builder_source_path,builder_source_ref)
    imported_json = put('pe-graph.json',{'schema':'researchos.scope7-net-static-pe-graph.v1','parser_ref':parser_ref,'api_set_schema_ref':schema_ref,'api_set_schema_meta':schema_meta,'api_set_resolution_basis':'Windows v6 .apiset namespace, range-checked UTF-16 entries and all value hosts; not a loader trace','seed_names':['net.exe','net1.exe'],'visited_count':len(visited),'edges_count':len(edges),'cap':CAP,'cap_reached':capped,'visited':visited,'edges':edges,'unresolved':unresolved,'static_only':True})
    actual_ref = put('actual-chain.json',{'schema':'researchos.scope7-net-actual-debug-chain.v1','invocation_ref':ref(invocation_path,invraw),'failure_review_ref':ref(REVIEW/'review.json'),'process_event_pairs_ref':review['process_event_pairs_ref'],'builder_source_ref':builder_source_ref,'observed_generation_803_806':final,'net_rejected_fact':review['first_rejected_load'],'net1_actual_loaded_events':actual_net1,'parent_pid_in_debug_event':False,'parent_pid_in_process_pairs':False,'builder_last_completed_nested_invocation':'web-module-junction','builder_next_source_invocation':'react-build','react_build_invocation_file_exists':(ROOT/'.local/desktop58-export-9eccde97a9fa4815941768cacaf590dc/.desktop58-build-receipts/react-build.invocation.json').exists(),'claim':'Node then cmd then conhost then net are chronologically observed, but their exact parent PID edges and net.exe command line are not in the frozen debug event record. Source indicates the next builder call was react-build; attribution to that call is inference, not observed argv for net.exe.','static_imports_are_actual_loaded':False})
    missing_runtime = [r['file_ref'] for name,r in visited.items() if r['frozen_runtime_ref'] is None]
    missing_catalog_files = [r['file_ref'] for name,r in visited.items() if r['frozen_catalog_file_ref'] is None]
    needs_images = [visited[n]['file_ref'] for n in ('net.exe','net1.exe') if visited[n]['frozen_catalog_image_ref'] is None]
    before = sorted(READS.values(),key=lambda x:x['path'].casefold())
    before_ref = put('inputs.before.json',{'files':before})
    after = []
    for r in before:
        p = pathlib.Path(r['path']);p = p if p.is_absolute() else ROOT/p
        now = ref(p,read(p,r));assert now['sha256']==r['sha256'] and now['bytes']==r['bytes']
        after.append(now)
    after_ref = put('inputs.after.json',{'files':after,'drift':[]})
    report = put('report.json',{'schema':'researchos.scope7-net-resource-readonly-candidate.v1','actor':'codex:/root/live_resource_lookup','observed_failure_count':672,'old_scope_rerun_authorized':False,'net_actual_rejected_file_ref':visited['net.exe']['file_ref'],'net1_static_file_ref':visited['net1.exe']['file_ref'],'net1_actual_loaded_proven':False,'frozen_runtime_member_count':len(runtime['files']),'frozen_catalog_file_count':len(catalog['files']),'frozen_catalog_image_count':len(catalog['images']),'static_pe_graph_ref':imported_json,'actual_chain_ref':actual_ref,'input_before_ref':before_ref,'input_after_ref':after_ref,'explicit_static_file_count':len(visited),'explicit_static_edge_count':len(edges),'unresolved_edge_count':len(unresolved),'cap_reached':capped,'missing_frozen_runtime_candidate_refs':missing_runtime,'missing_frozen_catalog_file_candidate_refs':missing_catalog_files,'missing_process_image_candidate_refs':needs_images,'api_set_resolution_basis':schema_ref,'qualification_notes':['API-set host candidates use static .apiset metadata, not a loader trace. Qualified/conditional mappings and runtime loader policy may differ.','Export forwarders, dynamic LoadLibrary, search policy, and conditional branches remain unknown. Static graph is not full actual loaded closure.','Only net.exe is an actual rejected load. net1.exe is a separate potential child entry, not observed here.','Parent PID edges and net.exe command line absent from frozen debug capture; preserve uncertainty.'],'new_scope_required':True,'new_grant_created':False,'source_acceptance':False,'formal_increment':0,'new_failure_count':0,'native_program_calls':0,'main_writes':0,'canonical_writes':0})
    print(json.dumps({'report_ref':report,'graph_ref':imported_json,'chain_ref':actual_ref,'visited':len(visited),'edges':len(edges),'unresolved':len(unresolved),'missing_runtime':len(missing_runtime),'missing_catalog':len(missing_catalog_files),'capped':capped},ensure_ascii=False))

if __name__=='__main__': main()
