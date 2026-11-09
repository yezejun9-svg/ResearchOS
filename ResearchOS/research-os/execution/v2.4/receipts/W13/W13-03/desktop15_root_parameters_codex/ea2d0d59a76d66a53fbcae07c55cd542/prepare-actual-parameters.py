import sys
sys.dont_write_bytecode=True
import hashlib,json,os,ast
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os')
N05=ROOT/'execution/v2.4/receipts/W05/W05-99'
N13=ROOT/'execution/v2.4/receipts/W13/W13-03'
OUT=Path(__file__).resolve().parent
UID=OUT.name
def need(x,msg):
    if not x: raise RuntimeError(msg)
def parse(raw):
    def pairs(rows):
        d={}
        for k,v in rows:
            need(k not in d,'duplicate JSON key')
            d[k]=v
        return d
    return json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
def pin(value):
    p=Path(value)
    need(p.is_absolute() and p.is_relative_to(ROOT) and '..' not in p.parts and p.resolve(strict=True)==p.absolute(),'path boundary')
    for q in [p,*p.parents]:
        if os.path.lexists(q):
            need(not q.is_symlink() and not(getattr(q.lstat(),'st_file_attributes',0)&0x400),'reparse')
    b=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def verified(p,sha,size):
    r=pin(p)
    need(r['sha256']==sha and r['bytes']==size,'fixed input drift: '+str(p))
    return r
def doc(r): 
    need(pin(r['path'])==r,'ref drift')
    return parse(Path(r['path']).read_bytes())
def save(name,value,raw=False):
    b=value if raw else (json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
    with (OUT/name).open('xb') as f: f.write(b)
    return pin(OUT/name)
need(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode and not sys.flags.optimize and Path.cwd()==ROOT,'flags/cwd')
canon=[ROOT/'execution/v2.4'/(x+'.json') for x in ['checkpoint','path_ownership','step_state','commands']]
before=[p.read_bytes() for p in canon]
refs=[pin(p) for p in canon]
cp,ow=[parse(b) for b in before[:2]]
need([cp['revision'],ow['revision'],len(cp['failure_counters'])]==[331,159,509],'actual canonical tuple')
need(cp['head']=='a510dbef4a7e08fb5c428df44c39b133f3ffa856','actual source head')
need(doc(pin(ROOT/'execution/project_identity.json'))['project_id']=='aede0678-7308-43dc-b9f2-cfe3d90cfdfb','permanent identity')
prior=N05/'integration_codex/cli43-fresh-held2-r331-c4f309c5528f5d42be5e7eeb146a20aa'
cut2=verified(prior/'late-origins.capture.for-next-r332.json','0211da19c7888ced1ca7273ba82e3d7b0b436cbb3087fedc4d5ab48d99a3ca08',5093)
old=doc(cut2)
need(old['before']==[331,159,509] and old['after']==[332,160,511] and len(old['origins'])==2,'original immutable historical cut')
specs=[
(ROOT/'execution/v2.4/receipts/W09/W09-99/w09_controller_revision_independent_review_codex/bd6b0994244f4676a3c3a2be8ef3661a/coordination-failure-origin.json','21eb69a5dcc61a1f6ea23ca7ef9075a4e9f3b928ea409643671b263ea713161f',2400,None,None),
(N05/'cli43_successful_execution_independent_review_codex/6f07498ca19a49c7866b9e528d401aa0/failure-origin.61653a.json','35b6490d2158d5bccc5f9d78d807c90a4a66d9cc61ad79b3010877363cf6e6bf',818,1,None),
(prior/'failure-origin.4e8b35.json','6bf5972d575c6c80386d2fac2fbe609d560cc994b5cf2eedc29d5b35450cfc5f',1757,1,1),
(N13/'desktop15_cli_qualification_gate_preparation_codex/c9cfe978648d42699b703203c6ccb239/failure-origin.add941.json','e27edcccd09d3af4e27a72cc1210b23f693979243fcb7bc952d659008a3095a4',1388,1,None),
(prior/'failure-origin.0b66ac.json','a5c7751682f4defa62243e3c201478a7e3eb075fdf250fac8541cbfdfe0b4a6c',5660,1,None),
(N13/'desktop15_current_cli_qualification_gate_mapping_codex/e13ae06a1bac48fe8a1b91e33e6537bd/failure-origin.2fe4a0.json','5d2e4e4008674b33ade7b99f8efc406679ed2633095303e959207a74ca5d3fba',2386,1,1)
]
origins=[]
registered={r.get('evidence_ref',{}).get('sha256') for r in cp['failure_counters']}
for i,(p,sha,size,outer,native) in enumerate(specs):
    r=verified(p,sha,size)
    need(sha not in registered and sha not in {x['evidence_ref']['sha256'] for x in origins},'no duplicate origin')
    payload=doc(r)
    origins.append({'origin':'desktop15-root-cut-'+str(i)+'-'+sha[:12],'evidence_ref':r,'original_payload':payload,
        'classification':'DISTINCT_ORIGINAL_METADATA_OR_COORDINATION_FAILURE','count_once':True,'counter_reset':False,
        'automatic_retry':False,'actual_outer_exit':outer,'actual_native_exit':native,'product_cases_run':0})
copies=[save(p.stem+'.current.raw',b,True) for p,b in zip(canon,before)]
handoff=save('current-root.handoff.json',{'schema':'researchos.root-current-canonical-handoff.v1','actor':'codex:/root',
    'canonical_refs':refs,'canonical_copies':copies,'tuple':[331,159,509],'head':cp['head'],'canonical_writes':0,
    'formal_increment':0,'source_acceptance':False,'current_formal_acceptance':'0/42'})
hmf=save('current-root.manifest.json',{'count':5,'entries':[handoff,*copies],'self_excluded':True})
cut=save('pending-origins.cut.json',{'schema':'researchos.root-pending-origin-cut.v1','actor':'codex:/root',
    'registered_before':[331,159,509],'registration_after':[332,160,515],'confirmed_origins':origins,
    'retained_aftercut_origin_refs':[],'counter_reset':False,'canonical_writes':0,'formal_increment':0,
    'historical_two_origin_cut_ref_preserved':cut2,'historical_cut_rewritten':False,'unknown_native_preserved':True})
template=pin(N13/'desktop15_root_scope_binding_preparation_codex/5097ef19e4414a81b6457363a3b76060/root-request.example.json')
request=doc(template)
del request['example_not_executable']
gate=doc(verified(N13/'desktop15_cli_qualification_gate_preparation_codex/0293420914814321ac0897bdfa7d9ee7/handoff.json',
    'fd197299c5429d15ee218102fc4188ff4045da060e8f3141b6782b2d04d364f0',4843))
for key,r in gate['qualification_refs'].items(): need(pin(r['path'])==r,'qualification input unchanged')
builder=gate['builder_ref']; need(pin(builder['path'])==builder,'builder unchanged'); ast.parse(Path(builder['path']).read_bytes())
runtime=verified(N05/'integration_codex/session-list-closedcopy-root-replay-draft/gate-launcher-preparation-d58b6cfd52a44f0f9cee84344abda03d/controller_runtime_resources.json',
    '5ba6aa64a86f3e3cd7fe8be1393e569dcf13ad36556643e9e59d0190f1569eee',281843)
status=save('status.expected.raw',(prior/'prepare.status.stdout.raw').read_bytes(),True)
need(status['sha256']=='e03849874f27dcf3b079cb84c9bae69ad97311118da47c3122a5a9b32b9611b4' and status['bytes']==894,'original current status bytes')
for key in ['desktop_source_review_ref','desktop_source_review_manifest_ref']: need(pin(request[key]['path'])==request[key],'desktop suitability unchanged')
binding_parent=N13/'desktop15_root_scope_binding_executor_codex'
if not binding_parent.exists(): binding_parent.mkdir(exist_ok=False)
need(binding_parent.is_dir(),'explicit binding parent')
reg=N05/'integration_codex'/('desktop15-source-integration-r332-'+UID)
need(not reg.exists() and not (binding_parent/UID).exists(),'unused future scopes')
request.update(expected_before=[331,159,509],expected_after=[332,160,515],expected_main_branch='refs/heads/main',
    operation_uuid=UID,registration_namespace=str(reg),binding_output_root=str(binding_parent/UID),
    canonical_before_refs=refs,current_root_handoff_ref=handoff,current_root_manifest_ref=hmf,runtime_resources_ref=runtime,
    status_ref=status,origin_cut_ref=cut,confirmed_pending_origins=origins,cli43_bounded_qualification_refs=gate['qualification_refs'])
rq=save('root-request.actual.json',request)
need([p.read_bytes() for p in canon]==before,'canonical writes/drift')
prep=save('preparation.json',{'schema':'researchos.root-desktop15-parameters-preparation.v1','actor':'codex:/root',
    'request_ref':rq,'builder_ref':builder,'current_canonical_refs':refs,'current_tuple':[331,159,509],
    'future_tuple':[332,160,515],'confirmed_origin_count':6,'actual_future_registration':False,
    'candidate_execution':False,'target_native_calls':0,'canonical_writes':0,'source_acceptance':False,'formal_increment':0,
    'independent_gate_review_required_before_builder':True,'later_origins_must_remain_outside_fixed_cut':True})
rows=[pin(p) for p in sorted(OUT.iterdir()) if p.is_file()]
mf=save('manifest.json',{'count':len(rows),'entries':rows,'self_excluded':True})
print(json.dumps({'request_ref':rq,'preparation_ref':prep,'manifest_ref':mf,'tuple':[331,159,509],
    'future_tuple':[332,160,515],'origin_count':6,'canonical_writes':0,'target_native_calls':0},ensure_ascii=False))
