"""Publish the reviewed W09 profile first, then its index anchor. No acceptance."""
import ast,hashlib,json,os,sys,types
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os')
N=Path(__file__).resolve().parent
W=R/'execution/v2.4/receipts/W09/W09-99'
P=W/'w09_formal_profile_v4_source_codex/profv4-01a12c10'
V=W/'w09_formal_profile_v4_independent_review_codex/profv4r-01a12c10'
ACTOR='codex:/root'
PYREF=dict(path='C:\\Users\\yqyyds\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe',sha256='cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b',bytes=106328)
GP=dict(path=str(R/'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'),sha256='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',bytes=11404)
BEFORE=[('dd997457f14314374ee4577fff6fd87317e05ad908f4c24d01ce302af72edeb7',4370868),('da777233cf369e433d4db61f75b579cfcd9a3b9f5092f6b7acafc7c3106cc5d2',206009),('fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149',257446),('28b4ba18ce2ab3ce03287651e311ae2bd36293b53fd8c298e5bf1f231f56d027',68968)]
def require(v,code):
    if not v:raise ValueError(code)
def pin(p):
    p=Path(p).resolve(strict=True);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(v):
    require(type(v) is dict and set(v)=={'path','sha256','bytes'} and type(v['bytes']) is int,'EXACT_THREE_KEY_REF')
    p=Path(v['path']);require(p.is_absolute() and str(p.resolve(strict=True))==v['path'],'CANONICAL_REF_PATH')
    b=p.read_bytes();require(len(b)==v['bytes'] and hashlib.sha256(b).hexdigest()==v['sha256'],'EXACT_PIN');return b
def fixed(p,sha,size):
    v=dict(path=str(p.resolve(strict=True)),sha256=sha,bytes=size);read(v);return v
def decode(v):return json.loads(read(v))
def save(name,value):
    require(Path(name).name==name,'LOCAL_ONLY')
    with (N/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
    return pin(N/name)
def members(href,mref):
    h=decode(href);m=decode(mref);require(h['manifest_ref']==mref,'HDF_MF_BOUND')
    values=m['members'];values=list(values.values()) if isinstance(values,dict) else values
    require(isinstance(values,list),'MEMBERS_LIST')
    for v in values:read(v)
    return h,[href,mref,*values]
def prepare():
    read(PYREF);require(str(Path(sys.executable).resolve())==PYREF['path'],'LOCKED_PYTHON')
    sh=fixed(P/'HDF.json','e27b1ec5b48f19f23271ea7604d0f3bec04dcfe443191af2891f49dac2ba908a',2980)
    sm=fixed(P/'MF.json','e9fc7ae240d30d2ad1c6706d8e4aa783ace22623e372e2595e72e062e220792e',11007)
    rh=fixed(V/'HDF.json','b7f343874b9a2d2283f5294f4e332158cec760c2a80e37ab401b8074acb8decc',2150)
    rm=fixed(V/'MF.json','abfea152a8e1152c81ad63e35ae4c20e2528d18a2b85047e80980d313b691aa6',4465)
    h,refs=members(sh,sm);review,more=members(rh,rm);refs+=more
    dr=fixed(V/'source-decision.json','3665fae581e0fe7a5b73e2d49827e900b77529098ee430f5a046435d9e652d55',3872);d=decode(dr);refs.append(dr)
    require(d['decision']=='SOURCE_ACCEPTED_FOR_ROOT_ADOPTION','SOURCE_NOT_ACCEPTED')
    require(d['reviewer']=='codex:/root/attach_fixture_source_review','EXACT_NONAUTHOR_SOURCE_REVIEWER')
    require(d['source_handoff_ref']==sh and d['source_manifest_ref']==sm,'SOURCE_REVIEW_BINDING')
    targets=[R/'execution/v2.4/formal_case_index.py',R/'execution/v2.4/formal_profile_w09.py']
    for target in targets:
        require(target.parent.resolve(strict=True)==R/'execution/v2.4' and not target.is_symlink() and not target.is_junction(),'FIXED_TARGET_NO_ALIAS')
    old=read(h['original_index_ref']);new=[read(v) for v in h['after_refs']]
    require(targets[0].read_bytes()==old and not targets[1].exists(),'CURRENT_INDEX_AND_PROFILE_ABSENT')
    require(old[:51719]==new[0][:51719],'W07_PREFIX_FULL_BYTES')
    for b in new:ast.parse(b)
    canonical=[fixed(R/'execution/v2.4'/name,sha,size) for name,(sha,size) in zip(('checkpoint.json','path_ownership.json','step_state.json','commands.json'),BEFORE)]
    cp,ow=[decode(v) for v in canonical[:2]]
    require(cp['revision']==369 and ow['revision']==173 and cp['work_in_progress']['construction_active_parents']==['W05','W09'],'CURRENT_CP369_OW173')
    require(ow['active_integrator']['id']==ACTOR and ow['card_path_bindings']['W09-99']['owner']==ACTOR,'ROOT_SERIAL_W09_INTEGRATOR')
    refs += [*canonical,GP,PYREF,pin(__file__),h['original_index_ref'],*h['after_refs']]
    for mod in tuple(sys.modules.values()):
        for key in ('__file__','__cached__'):
            p=getattr(mod,key,None)
            if p and Path(p).is_file():refs.append(pin(p))
    unique={}
    for v in refs:read(v);key=v['path'].casefold();require(key not in unique or unique[key]==v,'NO_PIN_ALIAS_DRIFT');unique[key]=v
    return h,sh,sm,rh,rm,canonical,list(unique.values()),targets,old,new
def execute(mode,adopter_review_ref=None):
    require(mode in ('check','activate'),'MODE')
    h,sh,sm,rh,rm,canonical,refs,targets,old,new=prepare()
    if mode=='activate':
        require(adopter_review_ref is not None,'ADOPTER_INDEPENDENT_REVIEW_REQUIRED')
        a=decode(adopter_review_ref)
        require(a['decision']=='SOURCE_ACCEPTED_FOR_ROOT_PROFILE_V4_PUBLICATION' and a['actor_role']=='INDEPENDENT_NON_AUTHOR' and a['actor_id']!=ACTOR,'ROOT_ADOPTER_NONSIGNED_SOURCE_REVIEW')
        require(a['writer_ref']==pin(__file__) and a['profile_source_handoff_ref']==sh and a['profile_source_review_handoff_ref']==rh,'ADOPTER_EXACT_BINDING')
        refs.append(adopter_review_ref)
    m=types.ModuleType('profile_v4_guard');m.__file__=GP['path'];sys.modules[m.__name__]=m;exec(compile(read(GP),GP['path'],'exec'),m.__dict__)
    guard=m.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=512*1024*1024)
    phase='SOURCE_GUARD';error=None;published=False
    guard.acquire(refs)
    try:
        require(targets[0].read_bytes()==old and not targets[1].exists(),'RECHECK_TARGET_CAS')
        before=save('publication.intent.'+mode+'.json',dict(issued_by=ACTOR,source_handoff_ref=sh,source_manifest_ref=sm,source_review_handoff_ref=rh,source_review_manifest_ref=rm,canonical_refs=canonical,before_index_ref=h['original_index_ref'],before_profile='ABSENT',after_refs=h['after_refs'],formal_case_accepted_delta=0,parent_acceptance=False,publication_order=['profile','index_anchor'],automatic_retry=False))
        if mode=='activate':
            phase='PROFILE_CREATE_EXCLUSIVE'
            with targets[1].open('xb') as f:f.write(new[1]);f.flush();os.fsync(f.fileno())
            require(targets[1].read_bytes()==new[1],'PROFILE_DURABLE_BYTES')
            phase='INDEX_STAGE'
            stage=targets[0].with_name('formal_case_index.adoptv4-20261009.stage')
            with stage.open('xb') as f:f.write(new[0]);f.flush();os.fsync(f.fileno())
            phase='INDEX_COMPARE_AND_PUBLISH'
            require(targets[0].read_bytes()==old and targets[1].read_bytes()==new[1],'PUBLICATION_LAST_CAS')
            os.replace(stage,targets[0]);published=True
            require([p.read_bytes() for p in targets]==new,'EXACT_TWO_TARGETS_AFTER')
            phase='TWO_TARGETS_VERIFIED'
        else:require(targets[0].read_bytes()==old and not targets[1].exists(),'CHECK_NO_MAIN_WRITES')
        for v in canonical:read(v)
    except BaseException as exc:error=repr(exc)
    finally:
        cleanup=guard.close();cleanup_ref=save('source-guard.cleanup.'+mode+'.json',cleanup)
        if cleanup['closed'] is not True or cleanup['errors'] or cleanup['retained_handles_count']!=0:error=(error+'; ' if error else '')+'GUARD_NOT_CLOSED'
    outcome=save('publication.outcome.'+mode+'.json',dict(mode=mode,issued_by=ACTOR,phase=phase,error=error,index_anchor_published=published,profile_source_handoff_ref=sh,profile_source_review_handoff_ref=rh,adopter_independent_review_ref=adopter_review_ref,before_index_ref=h['original_index_ref'],before_profile='ABSENT',after_target_refs=[pin(p) for p in targets if p.exists()],guard_cleanup_ref=cleanup_ref,all_handles_closed=cleanup['closed'],retained_handles_count=cleanup['retained_handles_count'],canonical_unchanged=True if error is None else None,formal_case_accepted_delta=0,parent_acceptance=False,actual_formal_evidence_evaluated=False,automatic_retry=False,automatic_rollback=False))
    require(error is None,'PUBLICATION_FAILED_PRESERVE_OUTCOME_AND_RECONCILE')
    return outcome
if __name__=='__main__':
    require(len(sys.argv) in (2,5),'MODE [REVIEW_PATH REVIEW_SHA REVIEW_BYTES]')
    r=dict(path=sys.argv[2],sha256=sys.argv[3],bytes=int(sys.argv[4])) if len(sys.argv)==5 else None
    print(json.dumps(dict(outcome_ref=execute(sys.argv[1],r)),ensure_ascii=False),flush=True)
