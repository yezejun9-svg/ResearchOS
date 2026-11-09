import ast
import hashlib
import json
import pathlib
from collections import Counter
from datetime import datetime, timezone

P=pathlib.Path(__file__).resolve().parent
def ref(p):
    b=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def write(name,value):
    b=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    with (P/name).open('xb') as f:
        f.write(b)
    return ref(P/name)

for name in ['recursive.py','pe-parser.exact.py','seal.py']:
    ast.parse((P/name).read_text(encoding='utf-8'))
f=json.loads((P/'findings.json').read_text(encoding='utf-8'))
e=json.loads((P/'recursive-import-edges.json').read_text(encoding='utf-8'))
r=json.loads((P/'runtime-v3.json').read_text(encoding='utf-8'))
oldpath=pathlib.Path(r['old_basis_ref']['path'])
assert ref(oldpath)==r['old_basis_ref']
old=json.loads(oldpath.read_text(encoding='utf-8'))
newby={x['path'].casefold():x for x in r['files']}
assert len(newby)==1242 and all(newby[x['path'].casefold()]==x for x in old['files'])
before=json.loads((P/'inputs.before.json').read_text(encoding='utf-8'))
after=json.loads((P/'inputs.after.json').read_text(encoding='utf-8'))
assert before['files']==after['files'] and after['drift']==[]
assert f['discovered_count']==128 and f['files_read_count']==54 and f['cap_reached'] is True
assert f['additional_count']==21 and len(f['unread_discovered'])==74
unknown_by_name={}
for i,row in enumerate(e['unknown']):
    name=row.get('dll_name')
    key=name.casefold() if name else '<UNNAMED>'
    item=unknown_by_name.setdefault(key,{'name':name,'reasons':[], 'edge_locators':[]})
    reason=row.get('reason',row.get('resolution'))
    if reason not in item['reasons']:
        item['reasons'].append(reason)
    item['edge_locators'].append({'json_pointer':'/unknown/'+str(i)})
unknownref=write('unknown-name-index.json',{'edge_evidence_ref':ref(P/'recursive-import-edges.json'),
    'names':list(unknown_by_name.values()),'unknown_unique_name_count':len(unknown_by_name),
    'export_forwarders':{'status':'UNKNOWN_NOT_INSPECTED','per_parsed_image_field':'export_forwarder_resolution',
                         'names_not_fabricated':True},
    'inventory_miss_does_not_claim_absence_outside_top_level_DLL_inventory':True})
diagref=write('tool-diagnostics.json',{'schema':'researchos.public-resource-tool-observations.v1',
    'tools':[{'chunk':chunk,'purpose':purpose,'actual_outer_exit':0,'actual_native_python_exit':0,
              'native_bridge':'PowerShell exit $LASTEXITCODE','separate_native_stream_files':None,
              'original_tool_result':'conversation chunk '+chunk}
        for chunk,purpose in [('e21e7d','Read prior parser fixed bytes and references'),
                              ('1769c9','AST-only parse recursive observer'),
                              ('25967b','Bounded static PE import traversal'),
                              ('13b3a3','Read resulting counters and cap boundary')]],
    'new_nonzero_origins':[],'counter_reset':False,
    'product_or_image_execution':0})
handoff=write('handoff.json',{'schema':'researchos.windows-recursive-resource-handoff.v1',
    'actor':'codex:/root/sources_parent_impl','status':'SEALED_BOUNDED_STATIC_PARTIAL_CATALOG_STOPPED',
    'writer':'STOPPED','findings_ref':ref(P/'findings.json'),'runtime_v3_ref':ref(P/'runtime-v3.json'),
    'system32_union_ref':ref(P/'system32-recursive-union.files.json'),
    'edge_ref':ref(P/'recursive-import-edges.json'),'parsed_ref':ref(P/'parsed-pe-records.json'),
    'unknown_index_ref':unknownref,'tool_diagnostics_ref':diagref,
    'before_ref':ref(P/'inputs.before.json'),'after_ref':ref(P/'inputs.after.json'),
    'cap_unique_discovered_nodes':128,'discovered_nodes':128,'parsed_read_PE_files':54,
    'unread_discovered_nodes':74,'stopped_at_first_129th_candidate':True,
    'boundary':e['unknown'][-1], 'runtime_inherited_ref_count':1221,
    'runtime_added_ref_count':21,'runtime_total_ref_count':1242,'OS_union_ref_count':54,
    'additional_names':f['additional_names'],'edges':2148,
    'unknown_reason_counts':dict(Counter(x.get('reason',x.get('resolution')) for x in e['unknown'])),
    'all_inherited_1221_refs_byte_for_byte_equal':True,
    'current_PE_read_before_after_count':54,'metadata_plus_PE_inputs':len(before['files']),
    'other_inherited_resources_rehashed':False,'drift':[],
    'actual_loaded_complete':None,'static_dependency_graph_complete':False,
    'API_set_mapping_or_export_forwarder_resolution':'UNKNOWN',
    'delay_import_support':'Existing exact parser accepts RVA attributes=1; other forms UNKNOWN. Parsed descriptors retained with parent SHA and offsets.',
    'future_runtime_policy':'Refuse actual loaded resource not in reviewed exact-ref catalog; this catalog does not authorize execution.',
    'Go_Node_SQL_HTTP_model_calls':0,'DLL_load_or_Win32_API_enumeration':0,
    'source_canonical_index_writes':0,'formal_increment':0,'source_acceptance':False,
    'new_nonzero_origins':[],'failure_counters_modified':False,
    'manifest_path':str(P/'manifest.json'),'sealed_at':datetime.now(timezone.utc).isoformat()})
entries=[ref(p) for p in sorted(P.iterdir(),key=lambda p:p.name) if p.is_file() and p.name!='manifest.json']
mf=write('manifest.json',{'schema':'researchos.public-resource-observation-manifest.v1','entries':entries,
                         'count':len(entries),'self_excluded':True,'handoff_included':True,'product_execution':0})
print(json.dumps({'handoff_ref':handoff,'manifest_ref':mf,'runtime_v3_ref':ref(P/'runtime-v3.json'),
                  'OS_union_ref':ref(P/'system32-recursive-union.files.json'),
                  'diagnostics_ref':diagref},ensure_ascii=False))
