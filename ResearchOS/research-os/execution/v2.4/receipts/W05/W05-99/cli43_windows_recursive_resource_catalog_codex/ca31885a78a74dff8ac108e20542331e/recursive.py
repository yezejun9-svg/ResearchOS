"""Bounded static PE import graph; no image loading or Windows API calls."""
import ast
import hashlib
import json
import pathlib
import stat
import struct
from collections import deque
from datetime import datetime, timezone

OUT = pathlib.Path(__file__).resolve().parent
ROOT = pathlib.Path('D:/作品集/ResearchOS/research-os')
OLD = ROOT/'execution/v2.4/receipts/W05/W05-99/cli43_windows_static_resource_catalog_codex/ebd3948fac514bcbb9c4f1465c066aca'
SYSTEM = pathlib.Path('C:/Windows/System32')
CAP = 128
READS = {}

def ref(p, raw):
    return {'path': str(p), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def read(p, expected=None):
    p = pathlib.Path(p)
    raw = p.read_bytes()
    r = ref(p, raw)
    if expected is not None:
        assert r['sha256'] == expected['sha256'] and r['bytes'] == expected['bytes'], str(p)
    k = str(p).casefold()
    if k in READS:
        assert READS[k] == r
    READS[k] = r
    return raw

def write(name, value):
    b = (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    with (OUT/name).open('xb') as f:
        f.write(b)
    return ref(OUT/name,b)

def main():
    started = datetime.now(timezone.utc).isoformat()
    # Copy/evaluate only the exact previously sealed Python function definition.
    # This is byte parsing code, not import/execution of an image or old collector.
    oldsource = read(OLD/'observe.py')
    assert hashlib.sha256(oldsource).hexdigest() == '6d6f68fcb8a69083c6fdd9565d16504b03726a61b7a57d0a59000e98b816c62a'
    tree = ast.parse(oldsource.decode('utf-8'))
    function = next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='pe_imports')
    segment = ast.get_source_segment(oldsource.decode('utf-8'),function)
    assert hashlib.sha256(segment.encode()).hexdigest() == 'cd044d9fe06b0776742c6162a4537938501e75d0c2dffa008c52795aea6c1cd9'
    with (OUT/'pe-parser.exact.py').open('xb') as f:
        f.write(segment.encode())
    exec(compile(ast.Module(body=[function],type_ignores=[]),str(OLD/'observe.py'),'exec'),globals())
    parserref = ref(OUT/'pe-parser.exact.py',segment.encode())
    runtime_raw = read(OLD/'runtime-v2.json')
    assert hashlib.sha256(runtime_raw).hexdigest() == '446a1c15cfa797cb63ef7107097ed5dab878e0444d7e37e8eadfc885bb88795a'
    runtime = json.loads(runtime_raw)
    seed_raw = read(OLD/'system32-union.files.json')
    assert hashlib.sha256(seed_raw).hexdigest() == '9899914d0ebe9d62e769ec772c96534743c829ca44c8352c51164be9c7868062'
    seeds = json.loads(seed_raw)['files']
    assert len(runtime['files'])==1221 and len(seeds)==33
    inventory = []
    for p in sorted(SYSTEM.iterdir(),key=lambda p:p.name.casefold()):
        if p.suffix.casefold()!='.dll':
            continue
        s = p.lstat()
        inventory.append({'path':str(p),'name':p.name,'bytes_lstat':s.st_size,
            'regular_file':stat.S_ISREG(s.st_mode),
            'reparse':bool(getattr(s,'st_file_attributes',0)&stat.FILE_ATTRIBUTE_REPARSE_POINT)})
    invref = write('system32-inventory.json',{'basis':'FILESYSTEM_TOP_LEVEL_ONLY','files':inventory})
    available = {r['name'].casefold():r for r in inventory if r['regular_file'] and not r['reparse']}
    assert len(available)==sum(r['regular_file'] and not r['reparse'] for r in inventory)
    seed_by_name={pathlib.Path(r['path']).name.casefold():r for r in seeds}
    discovered={name:{'path':available[name]['path'],'depth':0,'seed_ref':r}
                for name,r in seed_by_name.items()}
    queue=deque(sorted(discovered))
    parsed=[]
    edges=[]
    unknown=[]
    capped=False
    file_refs={}
    while queue and not capped:
        name=queue.popleft()
        node=discovered[name]
        p=pathlib.Path(node['path'])
        if p.parent!=SYSTEM or not available[name]['regular_file'] or available[name]['reparse']:
            unknown.append({'name':name,'reason':'INVENTORY_PATH_NOT_REGULAR_TOP_LEVEL'})
            continue
        # Current bytes are captured even if their import format is unsupported.
        raw=read(p,node['seed_ref'] if node['depth']==0 else None)
        current=ref(p,raw)
        file_refs[name]=current
        try:
            pe=pe_imports(p,current)
        except (AssertionError,ValueError,UnicodeError,struct.error,IndexError) as e:
            parsed.append({'image_ref':current,'depth':node['depth'],'parse_status':'UNKNOWN',
                           'parse_error_type':type(e).__name__,'parse_error':str(e)})
            unknown.append({'parent_pe_ref':current,'reason':'PE_FORMAT_NOT_SUPPORTED_BY_SEALED_PARSER',
                            'error_type':type(e).__name__,'error':str(e)})
            continue
        parsed.append({'image_ref':current,'depth':node['depth'],'parse_status':'PARSED',
                       'pe':pe,'export_forwarder_resolution':'UNKNOWN_NOT_INSPECTED'})
        for item in pe['unknown']:
            unknown.append({'parent_pe_ref':current,**item})
        for imported in pe['imports']:
            child=imported['dll_name'].casefold()
            edge={'parent_pe_ref':current,'parent_depth':node['depth'],**imported}
            if child not in available:
                edge['resolution']='UNKNOWN'
                edge['reason']=('API_SET_VIRTUAL_MAPPING_NOT_RESOLVED' if child.startswith(('api-','ext-'))
                                else 'NAME_NOT_IN_ACTUAL_SYSTEM32_INVENTORY')
                edge['existing_file_ref']=None
                unknown.append(edge.copy())
                edges.append(edge)
                continue
            edge['inventory_path']=available[child]['path']
            if child not in discovered:
                if len(discovered)>=CAP:
                    edge['resolution']='NOT_COLLECTED_CAP_128'
                    edge['existing_file_ref']=None
                    edges.append(edge)
                    unknown.append(edge.copy())
                    capped=True
                    break
                discovered[child]={'path':available[child]['path'],'depth':node['depth']+1,
                                   'first_parent_pe_ref':current}
                queue.append(child)
            edge['resolution']='EXISTING_SYSTEM32_FILE'
            edges.append(edge)
    # Only successfully read current files enter the catalog. Pending nodes stay explicit.
    for edge in edges:
        if edge['resolution']=='EXISTING_SYSTEM32_FILE':
            name=edge['dll_name'].casefold()
            edge['existing_file_ref']=file_refs.get(name)
            if name not in file_refs:
                edge['resolution']='DISCOVERED_NOT_READ_BEFORE_COLLECTION_STOP'
    before=list(READS.values())
    before_ref=write('inputs.before.json',{'files':before})
    after=[]
    for row in before:
        raw=pathlib.Path(row['path']).read_bytes()
        now=ref(pathlib.Path(row['path']),raw)
        assert now==row,('INPUT_DRIFT',row['path'])
        after.append(now)
    after_ref=write('inputs.after.json',{'files':after,'drift':[]})
    all_runtime={r['path'].casefold():r for r in runtime['files']}
    added=[]
    for r in file_refs.values():
        key=r['path'].casefold()
        if key in all_runtime:
            assert r['sha256']==all_runtime[key]['sha256'] and r['bytes']==all_runtime[key]['bytes']
        else:
            all_runtime[key]=r
            added.append(r)
    edge_ref=write('recursive-import-edges.json',{'edges':edges,'unknown':unknown})
    parsed_ref=write('parsed-pe-records.json',{'files':parsed,'parser_ref':parserref})
    osref=write('system32-recursive-union.files.json',{'files':sorted(file_refs.values(),key=lambda r:r['path'].casefold())})
    runtime_ref=write('runtime-v3.json',{'schema':'researchos.cli43-public-runtime-resources.static-candidate.v3',
        'files':sorted(all_runtime.values(),key=lambda r:r['path'].casefold()),
        'old_basis_ref':ref(OLD/'runtime-v2.json',runtime_raw),'added_static_candidate_files':added,
        'candidate_evidence_ref':edge_ref,'parser_ref':parserref,
        'inherited_refs_rehashed_except_current_read_PE_files':False,
        'current_read_PE_files_ref':osref,'future_actual_loaded_complete':None,
        'unknown_loaded_module_policy':'REFUSE_UNRECOGNIZED_RESOURCE','execution_authorized':False})
    unparsed=[{'name':n,**discovered[n]} for n in discovered if n not in file_refs]
    findings={'schema':'researchos.windows-recursive-static-resource-observation.v1',
        'actor':'codex:/root/sources_parent_impl','started_at':started,'ended_at':datetime.now(timezone.utc).isoformat(),
        'cap_unique_nodes':CAP,'discovered_count':len(discovered),'files_read_count':len(file_refs),
        'parsed_count':sum(r['parse_status']=='PARSED' for r in parsed),
        'parse_unknown_count':sum(r['parse_status']=='UNKNOWN' for r in parsed),
        'edge_count':len(edges),'unknown_rows':len(unknown),'cap_reached':capped,'unread_discovered':unparsed,
        'additional_names':sorted(pathlib.Path(r['path']).name for r in added),
        'additional_count':len(added),'runtime_v3_count':len(all_runtime),
        'inventory_ref':invref,'parser_ref':parserref,'edge_ref':edge_ref,'parsed_ref':parsed_ref,
        'system32_union_ref':osref,'runtime_v3_ref':runtime_ref,'before_ref':before_ref,'after_ref':after_ref,
        'complete_static_load_graph':False,'actual_loaded_complete':None,
        'open_gates':['API_SET_VIRTUAL_MAPPING_UNKNOWN','EXPORT_FORWARDER_TARGETS_NOT_INSPECTED_PER_PE',
                      'DLL_RUNTIME_DYNAMIC_LOADS_AND_CONDITIONAL_PATHS_UNKNOWN',
                      'STATIC_IMPORT_RELATION_IS_NOT_FUTURE_ACTUAL_HANDLE_OBSERVATION'],
        'source_canonical_index_writes':0,'DLL_load_or_Win32_enumeration_calls':0,
        'Go_Node_SQL_HTTP_model_calls':0,'formal_increment':0,'new_failure_origins':[],
        'source_acceptance':False,'future_execution_authorized':False}
    fr=write('findings.json',findings)
    print(json.dumps({'findings_ref':fr,'runtime_v3_ref':runtime_ref,'files_read':len(file_refs),
        'additional_count':len(added),'additional_names':findings['additional_names'],
        'unknown_rows':len(unknown),'cap_reached':capped,'parsed_count':findings['parsed_count']},ensure_ascii=False))

if __name__=='__main__':
    main()
