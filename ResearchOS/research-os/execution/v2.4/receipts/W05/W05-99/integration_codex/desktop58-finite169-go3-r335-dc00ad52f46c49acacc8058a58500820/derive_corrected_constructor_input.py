import copy, hashlib, json, os, sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path('D:/作品集/ResearchOS/research-os')
REG=Path(__file__).resolve().parent
BASE=REG/'input_capture_v2'
CFG=json.loads("{\"old_request_ref\":{\"path\":\"D:\\\\作品集\\\\ResearchOS\\\\research-os\\\\execution\\\\v2.4\\\\receipts\\\\W05\\\\W05-99\\\\integration_codex\\\\desktop58-finite169-go3-r335-dc00ad52f46c49acacc8058a58500820\\\\root-construction.parameters.desktop58.json\",\"sha256\":\"59dd4883d4005756e7b283a202a0b8257729a95d087d15ae51d670aeb1f3b831\",\"bytes\":34932},\"constructor_ref\":{\"path\":\"D:\\\\作品集\\\\ResearchOS\\\\research-os\\\\execution\\\\v2.4\\\\receipts\\\\W05\\\\W05-99\\\\integration_codex\\\\desktop58-finite169-go3-r335-dc00ad52f46c49acacc8058a58500820\\\\construct_root_inputs.desktop58.v3.py\",\"sha256\":\"2735a4c19b84721fe343662648766f9ffaf09b470ecd8c958a6ef5587d685df4\",\"bytes\":24167},\"pipeline_ref\":{\"bytes\":38316,\"path\":\"D:\\\\作品集\\\\ResearchOS\\\\research-os\\\\execution\\\\v2.4\\\\receipts\\\\W13\\\\W13-03\\\\desktop58_cli_root_closure_adapter_revision_preparation_codex\\\\156343f1960f409cbfb1b13af160735f\\\\metadata_pipeline.desktop58.bound.v3.proposed.py\",\"sha256\":\"60078d505a33da7570e7c747ecf4cc81bd46e66560120a07cd85162606421d98\"}}")
def need(ok,why):
    if not ok: raise RuntimeError(why)
def pin(p):
    raw=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def verified(r):
    p=Path(r['path'])
    need(p.is_absolute() and p.resolve(strict=True)==p and '..' not in p.parts,'Canonical input')
    for a in (p,*p.parents):
        if os.path.lexists(a): need(not a.is_symlink() and not(getattr(a.lstat(),'st_file_attributes',0)&0x400),'Reparse')
    raw=p.read_bytes()
    need(len(raw)==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256'],'Exact pin')
    return raw
def put(name,raw):
    p=BASE/name
    with p.open('xb') as f: f.write(raw)
    return pin(p)
def save(name,value):
    return put(name,(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
need(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode,'Pinned flags')
original=verified(CFG['old_request_ref'])
old=json.loads(original)
new=copy.deepcopy(old)
new['metadata_pipeline_ref']=CFG['pipeline_ref']
verified(CFG['pipeline_ref'])
need(old['metadata_pipeline_ref']!=new['metadata_pipeline_ref'] and new['metadata_pipeline_ref']==new['pipeline_source_ref'] and new['metadata_pipeline_ref'] in new['metadata_code_refs'],'Exact consumed metadata pipeline correction')
inverse=copy.deepcopy(new)
inverse['metadata_pipeline_ref']=old['metadata_pipeline_ref']
need(inverse==old,'One field only')
need(Path(new['allocation']['registration_namespace'])==REG and new['after']==[335,163,564],'Same actual allocation and frozen cut')
need(not os.path.lexists(BASE),'Fresh immutable input container')
BASE.mkdir()
ctor_ref=put('construct_root_inputs.desktop58.v3.py',verified(CFG['constructor_ref']))
request_ref=save('root-construction.parameters.desktop58.json',new)
audit_ref=save('input-correction.audit.json',{'schema':'researchos.desktop58-literal-input-correction.v1','actor':'codex:/root','old_request_ref':CFG['old_request_ref'],'new_request_ref':request_ref,'changed_fields':['metadata_pipeline_ref'],'before_value':old['metadata_pipeline_ref'],'after_value':new['metadata_pipeline_ref'],'whole_document_inverse':True,'constructor_ref':ctor_ref,'registration_namespace':new['allocation']['registration_namespace'],'input_container':str(BASE),'expected_resource_output_container':str(BASE),'before':new['before'],'after':new['after'],'origin_count':len(new['pending_origin_refs']),'old_inputs_unchanged':True,'constructor_invocations':0,'canonical_writes':0,'formal_increment':0})
print(json.dumps({'request_ref':request_ref,'constructor_ref':ctor_ref,'audit_ref':audit_ref,'registration_namespace':new['allocation']['registration_namespace'],'before':new['before'],'after':new['after'],'origin_count':len(new['pending_origin_refs'])},ensure_ascii=False))

