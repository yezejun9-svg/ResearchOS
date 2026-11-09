import sys
sys.dont_write_bytecode=True
import copy,hashlib,json,os
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os')
OUT=Path(__file__).resolve().parent
UID=OUT.name
PREVIOUS=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-03/desktop15_root_parameters_codex/ea2d0d59a76d66a53fbcae07c55cd542")
N05=ROOT/'execution/v2.4/receipts/W05/W05-99'
N13=ROOT/'execution/v2.4/receipts/W13/W13-03'
def need(v,msg):
    if not v: raise RuntimeError(msg)
def pin(value,public_git=False):
    p=Path(value)
    need(p.is_absolute() and '..' not in p.parts and p.resolve(strict=True)==p.absolute(),'path alias')
    need(p.is_relative_to(ROOT) or public_git and p==Path('C:/Program Files/Git/cmd/git.exe'),'bounded public input')
    for q in [p,*p.parents]:
        if os.path.lexists(q): need(not q.is_symlink() and not(getattr(q.lstat(),'st_file_attributes',0)&0x400),'reparse')
    b=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def verify(r,public_git=False):
    a=pin(r['path'],public_git)
    need(a['sha256']==r['sha256'] and a['bytes']==r['bytes'],'fixed ref changed')
    return a
def doc(r):
    verify(r)
    def pairs(rows):
        d={}
        for k,v in rows:
            need(k not in d,'duplicate JSON key')
            d[k]=v
        return d
    return json.loads(Path(r['path']).read_bytes().decode('utf-8'),object_pairs_hook=pairs,
        parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
def fixed(p,sha,size):
    a=pin(p)
    need(a['sha256']==sha and a['bytes']==size,'fixed source')
    return a
def save(name,value):
    b=(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
    with (OUT/name).open('xb') as f:f.write(b)
    return pin(OUT/name)
need(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode and not sys.flags.optimize and Path.cwd()==ROOT,'flags/cwd')
request_ref=fixed(PREVIOUS/'root-request.actual.json','0ff2a105a3313e7920cf01f2291ed67776300431ea957c1c0f89f2f025507ce1',24998)
request=doc(request_ref)
for r in request['canonical_before_refs']: verify(r)
cp=doc(request['canonical_before_refs'][0]);ow=doc(request['canonical_before_refs'][1])
need([cp['revision'],ow['revision'],len(cp['failure_counters'])]==[331,159,509] and cp['head']==request['expected_cli43_head'],'current tuple')
old_cut_ref=request['origin_cut_ref']
old_cut=doc(old_cut_ref)
need(old_cut['registration_after']==[332,160,515] and len(old_cut['confirmed_origins'])==6,'original cut6')
origin_ref=fixed(PREVIOUS/'failure-origin.fe8430-1010c2.json','1a1c3a298e3580d8658893150f5024ff13574d226a7e4cf42e183a69c95bc912',6259)
origin_payload=doc(origin_ref)
need(origin_payload['actual_outer_exit']==origin_payload['actual_native_exit']==1 and origin_payload['child_native_exit'] is None,'actual failure facts')
inner=pin(Path(origin_payload['inner_original_failure_path']))
inner_payload=doc(inner)
need(inner_payload['first_error']['phase']=='RUNTIME_RESOURCE_PINS' and inner_payload['first_error']['actual_native_exit'] is None and inner_payload['secondary_errors']==[],'original inner NULL first error preserved')
inner_mf=doc(pin(Path(inner['path']).parent/'manifest.json'))
need(inner_mf['count']==len(inner_mf['entries'])==2,'closed inner failure2 plus self excluded MF')
for r in inner_mf['entries']:verify(r)
need(not list(Path(inner['path']).parent.glob('*.invocation.json')),'no child Git launched')
origins=copy.deepcopy(old_cut['confirmed_origins'])
for row in origins: need(doc(row['evidence_ref'])==row['original_payload'],'old six origins unchanged')
origins.append({'origin':origin_payload['origin'],'evidence_ref':origin_ref,'original_payload':origin_payload,
    'classification':'DISTINCT_ORIGINAL_BINDING_PYTHON_RESOURCE_REJECTION','count_once':True,'counter_reset':False,
    'automatic_retry':False,'actual_outer_exit':1,'actual_native_exit':1,'product_cases_run':0})
need(len({r['evidence_ref']['sha256'] for r in origins})==7,'unique origins7')
cut=save('pending-origins.cut.json',{'schema':'researchos.root-pending-origin-cut.v1','actor':'codex:/root',
    'registered_before':[331,159,509],'registration_after':[332,160,516],'confirmed_origins':origins,
    'retained_aftercut_origin_refs':[],'counter_reset':False,'canonical_writes':0,'formal_increment':0,
    'historical_cut6_ref_preserved':old_cut_ref,'historical_cut_rewritten':False,'unknown_child_native_preserved':True})
base_catalog_ref=request['runtime_resources_ref']
catalog=doc(base_catalog_ref)
lock_ref=pin(ROOT/'execution/toolchains/locked.json')
git=doc(lock_ref)['tools']['git']
actual_git=pin(git['path'],True)
need(actual_git['sha256']==git['sha256']=='da240fe9bc24895b3e04150a4990b8a6ff329ecabcd8f19684c2cc310da5ef3f','pinned actual Git SHA')
need(len(catalog['files'])==1211 and all(Path(r['path'])!=Path(actual_git['path']) for r in catalog['files']),'previous missing Git precisely')
catalog['files'].append(actual_git)
catalog['root_append_only_exact_git_image']={'actor':'codex:/root','base_catalog_ref':base_catalog_ref,
    'additional_ref':actual_git,'base_files_byte_payload_preserved':True,'new_file_count':1212,
    'OS_lifecycle_qualification':False,'compiler_or_product_qualification':False}
catalog_ref=save('runtime.with-locked-git.json',catalog)
need(doc(catalog_ref)['files'][:-1]==doc(base_catalog_ref)['files'],'only one catalogue member addition')
reg=N05/'integration_codex'/('desktop15-source-integration-r332-'+UID)
binding=N13/'desktop15_root_scope_binding_executor_codex'/UID
need(not reg.exists() and not binding.exists(),'new unused namespaces')
request.update(operation_uuid=UID,registration_namespace=str(reg),binding_output_root=str(binding),
    expected_after=[332,160,516],origin_cut_ref=cut,confirmed_pending_origins=origins,runtime_resources_ref=catalog_ref)
rq=save('root-request.actual.json',request)
prep=save('preparation.json',{'schema':'researchos.root-desktop15-resource-correction.v1','actor':'codex:/root',
    'request_ref':rq,'previous_request_ref':request_ref,'new_catalog_ref':catalog_ref,'actual_pinned_git_ref':actual_git,
    'new_origin_ref':origin_ref,'inner_failure_ref':inner,'current_tuple':[331,159,509],'future_tuple':[332,160,516],
    'confirmed_origin_count':7,'same_input_retry':False,'candidate_source_changed':False,
    'historical_cut_rewritten':False,'canonical_writes':0,'target_native_calls':0,'source_acceptance':False,'formal_increment':0})
for r in request['canonical_before_refs']:verify(r)
rows=[pin(p) for p in sorted(OUT.iterdir()) if p.is_file()]
mf=save('manifest.json',{'count':len(rows),'entries':rows,'self_excluded':True})
print(json.dumps({'request_ref':rq,'preparation_ref':prep,'manifest_ref':mf,'runtime_ref':catalog_ref,'Git_ref':actual_git,
    'before':[331,159,509],'after':[332,160,516],'same_input_retry':False,'canonical_writes':0},ensure_ascii=False))
