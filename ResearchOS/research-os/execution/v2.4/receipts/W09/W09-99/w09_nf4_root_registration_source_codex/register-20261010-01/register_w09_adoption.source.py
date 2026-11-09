"""Future Root-only NF4 generation Scope registration.

No entrypoint executes on import. Existing reviewed Q/NF4 code is not changed.
Root must supply a completed actual request host pair, a current exact vector,
an independently accepted copy of this Source, and bounded leases. Only explicit
activate mode can write shared files; Source controls call neither.
"""
import ast,copy,hashlib,json,os,re,sys,types
from datetime import datetime,timezone
from pathlib import Path

R=Path(r'D:/作品集/ResearchOS/research-os');V=R/'execution/v2.4';W=V/'receipts/W09/W09-99'
N=Path(__file__).resolve().parent
ROOT='codex:/root';AUTHOR='codex:/root/attach_restore_independent_review'
ROOT_THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
CANON=tuple(V/(x+'.json') for x in ('checkpoint','path_ownership','step_state','commands'))
MAIN=(V/'formal_profile_w09.py',V/'commands.json')
INDEX=V/'formal_case_index.py'
OUTPUT_BASE=W/'w09_nf4_root_registration_root'
INPUT_PINS_SHA='f42d5711474c116e3e36fa1b030811e043c71ceb84110212d8bb3d4582052ff3'
REQUEST_FIELDS={'schema','issued_by','created_utc','kind','case_id','output_root','before_canonical_refs','main_profile_ref',
 'formal_index_ref','pending_ref','main23_qualification_ref','reviewed_source_audits_ref','reviewed_source_audit_refs',
 'source_handoff_ref','source_manifest_ref','source_review_handoff_ref','source_review_manifest_ref','source_review_decision_ref',
 'source_author_audit_ref','source_review_audit_ref','generation','producer_review_handoff_ref','producer_review_manifest_ref','producer_review_decision_ref','lease','native_leases','profile_commit_ref','profile_commit_audit_ref',
 'formal_acceptance','parent_acceptance','formal_dispatcher','automatic_retry','formal_case_accepted_delta',
 'external_model_provider_requests','paid_provider_requests','production_DB_writes'}

def require(ok,code):
    if not ok:raise ValueError(code)

def decode(raw):
    def unique(items):
        out={}
        for key,value in items:
            require(key not in out,'DUPLICATE_JSON_KEY');out[key]=value
        return out
    def nonfinite(value):raise ValueError('NONFINITE_JSON:'+value)
    return json.loads(raw,object_pairs_hook=unique,parse_constant=nonfinite)

def encoded(obj):return (json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
def sha(raw):return hashlib.sha256(raw).hexdigest()
def now():return datetime.now(timezone.utc)
def now_text():return now().isoformat()

def path_checked(value,absent=False):
    require(type(value) is str and re.match(r'^[A-Za-z]:[\\/]',value) is not None and '\x00' not in value,'ABSOLUTE_LOCAL_PATH')
    require(':' not in value[2:] and not value.startswith(('\\\\?\\', '\\\\.\\')),'REGULAR_LOCAL_PATH')
    p=Path(value)
    require('..' not in p.parts and str(p)==str(p.absolute()),'NO_PATH_TRAVERSAL')
    for ancestor in (p,*p.parents):
        if not ancestor.exists():
            require(absent and ancestor==p,'EXISTING_PARENT_REQUIRED');continue
        require(not ancestor.is_symlink() and not ancestor.is_junction()
                and not (getattr(ancestor.stat(),'st_file_attributes',0)&0x400),'NO_REPARSE_PATH')
    require(p.resolve(strict=not absent)==p,'NO_PATH_ALIAS')
    return p

def ref_shape(ref):
    require(type(ref) is dict and set(ref)=={'path','sha256','bytes'} and type(ref['path']) is str
            and type(ref['sha256']) is str and re.fullmatch('[0-9a-f]{64}',ref['sha256']) is not None
            and type(ref['bytes']) is int and 0<=ref['bytes']<=512*1024*1024,'EXACT_REF')
    return ref

def pin_raw(path,raw):return dict(path=str(path),sha256=sha(raw),bytes=len(raw))
def pin(path):
    p=path_checked(str(path));require(p.is_file(),'REGULAR_FILE');return pin_raw(p,p.read_bytes())
def read_ref(ref):
    ref_shape(ref);p=path_checked(ref['path']);require(p.is_file(),'REGULAR_REF')
    raw=p.read_bytes();require(pin_raw(p,raw)==ref,'REF_DRIFT');return raw
def doc(ref):return decode(read_ref(ref))

def save_raw(path,raw):
    with Path(path).open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    return pin_raw(path,raw)
def save(path,obj):return save_raw(path,encoded(obj))
def load_module(ref,name):
    raw=read_ref(ref);module=types.ModuleType(name);module.__file__=ref['path']
    exec(compile(raw,ref['path'],'exec'),module.__dict__);return module

def inputs():
    p=N/'input-pins.json';raw=p.read_bytes();require(sha(raw)==INPUT_PINS_SHA,'INPUT_SOURCE_PINS_DRIFT')
    return decode(raw),pin_raw(p,raw)

def fixed_modules(pins):
    # Own modules become executable only after their exact HDF refs are checked.
    core=load_module(pin(N/'adoption_core.source.py'),'w09_adoption_core')
    native=load_module(pins['NF_runtime'],'w09_existing_reviewed_nf4_runtime')
    return core,native

def unique_refs(refs):
    out={}
    for ref in refs:
        ref_shape(ref);key=str(Path(ref['path'])).casefold()
        require(key not in out or out[key]==ref,'CONFLICTING_REFS');out[key]=ref
    return list(out.values())

def actual_audit(native,ref,actor,digest):
    held=native.actual_audit(ref,actor,digest)
    a=doc(ref);lines=read_ref(a['original_capture_ref']).splitlines()
    result=decode(lines[-1]);stamp=result.get('timestamp')
    require(type(stamp) is str,'ACTUAL_AUDIT_TIME_REQUIRED')
    return held,stamp,lines[-1].decode('utf-8')

def reviewed_dependencies(pins,peers,native,core):
    """Use already accepted decisions and actual peer origins; no control reruns."""
    qh,qm,qrh,qrm,qr=[doc(pins[k]) for k in ('Q_hdf','Q_mf','QR_hdf','QR_mf','QR_decision')]
    nh,nm,nrh,nrm,nr=[doc(pins[k]) for k in ('NF_hdf','NF_mf','NR_hdf','NR_mf','NR_decision')]
    require(qh['manifest_ref']==pins['Q_mf'] and qrh['manifest_ref']==pins['QR_mf']
            and qrh['source_decision_ref']==pins['QR_decision'] and pins['QR_decision'] in qrm['members'],'Q_REVIEW_PAIR')
    require(qr['decision']=='ACCEPTED_SOURCE_ONLY' and qr['independent_non_author'] is True
            and qr['source_hdf_ref']==pins['Q_hdf'] and qr['source_mf_ref']==pins['Q_mf']
            and qr['profile_ref']==pins['Q_profile'] and qr['commands_proposal_ref']==pins['Q_commands']
            and qh['candidate_profile_ref']==pins['Q_profile'] and qh['candidate_CM40_ref']==pins['Q_commands']
            and pins['Q_profile'] in qm['members'] and pins['Q_commands'] in qm['members'],'EXACT_REVIEWED_Q')
    require(nh['manifest_ref']==pins['NF_mf'] and nrh['manifest_ref']==pins['NR_mf']
            and nrh['source_decision_ref']==pins['NR_decision'] and pins['NR_decision'] in nrm['members'],'NF4_REVIEW_PAIR')
    require(nr['decision']=='SOURCE_ACCEPTED_FOR_ROOT_FOUR_SELECTOR_NATIVE' and nr['actor_role']=='INDEPENDENT_NON_AUTHOR'
            and nr['source_handoff_ref']==pins['NF_hdf'] and nr['source_manifest_ref']==pins['NF_mf']
            and nr['calling_contract_ref']==pins['NF_contract'] and nr['runtime_ref']==pins['NF_runtime']
            and pins['NF_runtime'] in nm['members'],'EXACT_REVIEWED_NF4')
    require(qr['formal_acceptance'] is False and qr['execution_grant'] is False
            and nr['actual_executed'] is False and nr['formal_case_accepted_delta']==0,'SOURCE_ONLY_DEPENDENCIES')
    core.validate_peer_roles(qh['Source_author'],qr['review_author'],nh['actor_id'],nr['actor_id'])
    facts=(('profile-author',qh['Source_author'],pins['Q_hdf']['sha256']),
           ('profile-review',qr['review_author'],pins['QR_hdf']['sha256']),
           ('producer-author',nh['actor_id'],pins['NF_hdf']['sha256']),
           ('producer-review',nr['actor_id'],pins['NR_decision']['sha256']))
    refs=[];times=[]
    for key,actor,digest in facts:
        held,stamp,_=actual_audit(native,peers[key],actor,digest);refs.extend(held);times.append(stamp)
    # This read-only qualification is carried as context, never as W09 authority.
    qualification=doc(pins['main23_qualification'])
    require(qualification['schema']=='researchos.root-current-main23-programme-qualification.v1'
            and qualification['status']=='QUALIFIED_CURRENT_MAIN23_BUILD' and qualification['issued_by']==ROOT
            and qualification['formal_acceptance'] is False and qualification['execution_grant'] is False,'BOUND_MAIN23_CONTEXT_ONLY')
    return refs,times

def own_source(request,native,core):
    href=request['source_handoff_ref'];mref=request['source_manifest_ref'];h=doc(href);m=doc(mref)
    require(href==pin(N/'HDF.json') and mref==pin(N/'MF.json') and h['manifest_ref']==mref
        and h['schema']=='researchos.w09-nf4-registration-source-handoff.v1' and h['actor_id']==AUTHOR
        and h['execution_grant'] is False and h['formal_acceptance'] is False,'OWN_SOURCE_HANDOFF')
    bindings={k:pin(N/name) for k,name in {'caller_ref':'register_w09_adoption.source.py','core_ref':'adoption_core.source.py',
             'contract_ref':'root-calling-contract.source.json'}.items()}
    require(all(h[k]==ref and ref in m['members'] for k,ref in bindings.items()),'OWN_SOURCE_FILES')
    rhref=request['source_review_handoff_ref'];rmref=request['source_review_manifest_ref'];dref=request['source_review_decision_ref']
    rh,rm,d=doc(rhref),doc(rmref),doc(dref);actor=d.get('actor_id')
    require(rh['manifest_ref']==rmref and rh['source_decision_ref']==dref and dref in rm['members']
        and rh['actor_id']==actor,'OWN_REVIEW_PAIR')
    core.validate_own_review(d,href,mref,bindings)
    refs=[href,mref,rhref,rmref,dref,*bindings.values()];times=[]
    for ref,who,digest in ((request['source_author_audit_ref'],AUTHOR,href['sha256']),
            (request['source_review_audit_ref'],actor,dref['sha256'])):
        held,stamp,_=actual_audit(native,ref,who,digest);refs.extend(held);times.append(stamp)
    return dict(hdf=href,mf=mref,decision=dref,**bindings),refs,times

def pending_refs(pending):
    refs=[]
    for row in pending['pending']:
        ref=row['origin_ref'];raw=read_ref(ref);binding=doc(row['capture_binding_ref'])
        require(binding.get('schema')=='researchos.root-original-diagnostic-binding.v1' and binding.get('issued_by')==ROOT
                and binding.get('original_capture_ref')==ref and binding.get('original_ordinal')==row['ordinal']
                and binding.get('original_bytes_unchanged') is True and binding.get('formal_authority') is False,'ROOT_DIAGNOSTIC_BINDING')
        origin_binding=binding['original_source_binding_ref'];read_ref(origin_binding)
        require(type(binding.get('original_source_binding_selector')) is str and bool(binding['original_source_binding_selector'])
                and bool(raw),'COMPLETE_ORIGINAL_DIAGNOSTIC_REF')
        refs.extend((ref,row['capture_binding_ref'],origin_binding))
    return refs

def request_context(request_ref,audit_ref):
    source,pinref=inputs();pins=copy.deepcopy(source['refs']);request=doc(request_ref)
    for k,qk in {'NR_hdf':'producer_review_handoff_ref','NR_mf':'producer_review_manifest_ref','NR_decision':'producer_review_decision_ref'}.items():pins[k]=ref_shape(request[qk])
    core,native=fixed_modules(pins)
    require(set(request)==REQUEST_FIELDS and request['schema']=='researchos.root-w09-nf4-registration-request.v1'
            and request['issued_by']==ROOT and request['kind']=='NATIVE_SCOPES' and request['generation']==core.GENERATION,'ROOT_REQUEST_FIELDS')
    core.check_no_grant(request)
    require(type(request['case_id']) is str and re.fullmatch('[0-9a-f]{32}',request['case_id']) is not None,'ROOT_CASE_ID')
    out=Path(request['output_root'])
    require(out==OUTPUT_BASE/request['case_id'] and Path(request_ref['path']).is_relative_to(W),'ROOT_OUTPUT_NAMESPACE')
    require(type(request['before_canonical_refs']) is list and len(request['before_canonical_refs'])==4
            and [ref_shape(r)['path'] for r in request['before_canonical_refs']]==[str(p) for p in CANON],'FOUR_ORDERED_CURRENT_REFS')
    require(request['main_profile_ref']['path']==str(MAIN[0]) and request['formal_index_ref']['path']==str(INDEX)
            and request['formal_index_ref']['sha256']==pins['Q_index_before']['sha256']
            and request['formal_index_ref']['bytes']==pins['Q_index_before']['bytes'],'FIXED_MAIN_INDEX_AND_PROFILE')
    require(request['main23_qualification_ref']==pins['main23_qualification']
            and request['reviewed_source_audits_ref']==pins['peer_audits']
            and set(request['reviewed_source_audit_refs'])==set(source['peer_audit_refs'])
            and all(request['reviewed_source_audit_refs'][k]==source['peer_audit_refs'][k] for k in ('profile-author','profile-review')),'EXACT_CONTEXT_AND_FOUR_PEERS')
    peer_refs,peer_times=reviewed_dependencies(pins,request['reviewed_source_audit_refs'],native,core)
    own,ownrefs,owntimes=own_source(request,native,core)
    rootrefs,rootstamp,_=actual_audit(native,audit_ref,ROOT,request_ref['sha256'])
    core.validate_times(request['created_utc'],rootstamp,peer_times+owntimes,request['lease'],now())
    require(Path(request['pending_ref']['path']).is_relative_to(W),'ROOT_PENDING_PUBLIC_BOUNDARY')
    pending=doc(request['pending_ref'])
    require(set(request['native_leases'])==set(core.SELECTORS),'EXACT_SELECTOR_LEASES')
    for lease in request['native_leases'].values():
        core.validate_lease(lease,now(),core.utc(request['created_utc']))
        require(core.utc(lease['lease_expires_at'])<=core.utc(request['lease']['lease_expires_at']),'NATIVE_LEASE_WITHIN_ROOT_LEASE')
    ref_shape(request['profile_commit_ref']);ref_shape(request['profile_commit_audit_ref'])
    required_keys=('Q_hdf','Q_mf','QR_hdf','QR_mf','QR_decision','Q_profile','Q_commands','Q_profile_before','Q_contract',
        'Q_index_before','NF_hdf','NF_mf','NR_hdf','NR_mf','NR_decision','NF_contract','NF_choice','NF_runtime','NF_prepare',
        'NF_run','NF_launcher','NF_blueprint','peer_audits','main23_qualification','CM39_archive','TP','guard','locked')
    refs=[pinref,request_ref,audit_ref,request['pending_ref'],*peer_refs,*ownrefs,*rootrefs,
          *[pins[k] for k in required_keys],*pending_refs(pending)]
    for r in refs:read_ref(r)
    # Require execution through the locked interpreter; no environment discovery.
    locked=doc(pins['locked'])['tools']['python'];pythonref=pin(sys.executable)
    require(pythonref['path']==locked['path'] and pythonref['sha256']==locked['sha256'],'LOCKED_PYTHON')
    refs.append(pythonref)
    return dict(request=request,request_ref=request_ref,audit_ref=audit_ref,source=source,pins=pins,core=core,native=native,
                own=own,pending=pending,refs=unique_refs(refs),out=out)

def project_commands(profile_raw,cm39):
    tree=ast.parse(profile_raw);functions=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='_cm40_commands']
    require(len(functions)==1,'REVIEWED_CM40_PROJECTION_FUNCTION')
    globals_={'json':json};exec(compile(ast.Module(body=functions,type_ignores=[]),'<reviewed _cm40_commands>','exec'),globals_)
    return globals_['_cm40_commands'](cm39)


def validate_profile_commit(ctx,cp,ow):
    request=ctx['request'];pins=ctx['pins'];ref=request['profile_commit_ref'];commit=doc(ref)
    require(Path(ref['path']).is_relative_to(W/'w09_profile_nf3_root_adoption_root') and Path(ref['path']).name=='apply-profile.completed.json'
            and commit['schema']=='researchos.root-w09-profile-adoption-completed.v1'
            and commit['status']=='W09_PROFILE_ADOPTED_CM40' and commit['issued_by']==ROOT
            and commit['all_guards_closed'] is True and commit['formal_acceptance'] is False,'ACTUAL_PROFILE_COMMIT')
    qscope=doc(commit['scope_ref'])
    require(cp['work_in_progress']['w09_profile_adoption_scope_ref']==commit['scope_ref']
            and ow['card_path_bindings']['W09-99']['subtasks'][ctx['core'].QKEY]['scope_ref']==commit['scope_ref'],
            'CURRENT_REGISTERED_PROFILE_SCOPE')
    targets=commit['target_after_refs'];require(targets==qscope['target_after_refs']
        and targets==[pin(p) for p in MAIN] and targets[0]['sha256']==pins['Q_profile']['sha256'],'CURRENT_ADOPTED_PROFILE_TARGETS')
    commands=doc(targets[1]);proposal=doc(pins['Q_commands'])
    require(commands=={**proposal,'updated_at':qscope['created_utc']}
        and commands['commands']==project_commands(read_ref(pins['Q_profile']),doc(pins['CM39_archive'])),'ADOPTED_EXACT_CM40')
    held,stamp,result=actual_audit(ctx['native'],request['profile_commit_audit_ref'],ROOT,ref['sha256'])
    require(ctx['core'].utc(commit['completed_utc'])<=ctx['core'].utc(stamp)<=ctx['core'].utc(request['created_utc'])
        and 'W09_PROFILE_ADOPTED_CM40' in result,'PROFILE_ACTUAL_COMPLETION_PRECEDES_NATIVE_REQUEST')
    ctx['refs']=unique_refs(ctx['refs']+[ref,commit['scope_ref'],*held,*targets])
    return commit

def model(ctx,before_raw,archive_refs):
    request=ctx['request'];core=ctx['core'];pins=ctx['pins'];out=ctx['out']
    require(len(before_raw)==4 and [pin_raw(p,b) for p,b in zip(CANON,before_raw)]==request['before_canonical_refs'],'EXACT_COMPLETE_BEFORE4')
    docs=[decode(raw) for raw in before_raw];cp,ow=docs[:2]
    require(encoded(cp)==before_raw[0] and encoded(ow)==before_raw[1],'CANON_PAIR_BYTE_INVERSE_ENCODING')
    core.merge_pending(cp,ctx['pending'],request['before_canonical_refs'])
    validate_profile_commit(ctx,cp,ow)
    choice=doc(pins['NF_choice']);contract=doc(pins['NF_contract'])
    require(choice['common']['generation']==request['generation']==core.GENERATION,'EXACT_NF4_GENERATION')
    scopes=core.make_native_scopes(request,pins,choice,contract)
    for scope in scopes.values():
        for path in (scope['receipt_root'],scope['scratch_root'],scope['output_root']):
            path_checked(path,True);require(not Path(path).exists(),'NATIVE_ONE_SHOT_PATH_ALREADY_EXISTS')
        for source_ref in scope['source21']:read_ref(source_ref);ctx['refs'].append(source_ref)
    target_before=[];target_after=[];after_refs=[];main_proposals=[]
    scope_refs={key:pin_raw(out/('scope.'+key+'.json'),encoded(value)) for key,value in scopes.items()}
    ca,oa,cops,oops=core.canonical_changes(cp,ow,request,scope_refs,scopes,ctx['pending'],archive_refs,ctx['own'],request['profile_commit_ref'])
    require(encoded(core.inverse_operations(ca,cops))==before_raw[0]
            and encoded(core.inverse_operations(oa,oops))==before_raw[1],'COMPLETE_ORIGINAL_BYTE_INVERSE')
    after_raw=[encoded(ca),encoded(oa)]
    proposed=[pin_raw(out/name,raw) for name,raw in zip(('checkpoint.after.proposed.json','path_ownership.after.proposed.json'),after_raw)]
    result=dict(schema='researchos.root-w09-nf4-registration-plan.v1',kind=request['kind'],issued_by=ROOT,
        request_ref=ctx['request_ref'],root_request_audit_ref=ctx['audit_ref'],output_root=str(out),
        before_canonical_refs=request['before_canonical_refs'],before_archive_refs=archive_refs,
        scope_refs=scope_refs,canonical_after_refs=[pin_raw(p,b) for p,b in zip(CANON[:2],after_raw)]+request['before_canonical_refs'][2:],
        canonical_proposal_refs=proposed,checkpoint_operations=cops,ownership_operations=oops,
        target_before_refs=target_before,target_after_refs=after_refs,main_proposal_refs=main_proposals,
        complete_byte_inverse=True,pending_ref=request['pending_ref'],next_original_failure_ordinal=ctx['pending']['next_original_failure_ordinal'],
        formal_acceptance=False,parent_acceptance=False,formal_case_accepted_delta=0,automatic_retry=False)
    return result,scopes,after_raw,target_after

class GuardedFailure(RuntimeError):
    def __init__(self,primary,cleanup):
        self.primary=primary;self.cleanup=cleanup
        super().__init__('GUARDED_STAGE_FAILED: '+repr(primary))

def guarded(ctx,refs,operation):
    gm=load_module(ctx['pins']['guard'],'w09_adoption_held_sources')
    guard=gm.SourceReadGuard(total_cap=256*1024*1024);primary=None;result=None;audit=None
    try:
        guard.acquire(unique_refs(refs));result=operation()
    except BaseException as exc:primary=exc
    finally:
        try:audit=guard.close()
        except BaseException as exc:audit=dict(closed=False,errors=[repr(exc)],retained_handles_count=None)
    if primary is not None or not (audit.get('closed') is True and audit.get('errors')==[] and audit.get('retained_handles_count')==0):
        raise GuardedFailure(primary,audit) from primary
    return result,audit

def propose(request_ref,audit_ref):
    ctx=request_context(request_ref,audit_ref);request=ctx['request'];out=ctx['out']
    require(OUTPUT_BASE.is_dir(),'ROOT_MUST_CREATE_PUBLIC_OUTPUT_PARENT')
    path_checked(str(out),True);require(not out.exists(),'FRESH_REGISTRATION_OUTPUT')
    before=[read_ref(r) for r in request['before_canonical_refs']]
    archives=[pin_raw(out/('before.'+name+'.raw'),raw) for name,raw in zip(('checkpoint','path_ownership','step_state','commands'),before)]
    plan,scopes,after,main_after=model(ctx,before,archives)
    held=ctx['refs']+request['before_canonical_refs']+[request['main_profile_ref'],request['formal_index_ref']]
    def operation():
        # Repeat all provenance/time predicates under the immutable resource guard.
        request_context(request_ref,audit_ref)
        require([pin(p) for p in CANON]==request['before_canonical_refs'],'PROPOSE_CURRENT4')
        out.mkdir()
        for ref,raw in zip(archives,before):require(save_raw(ref['path'],raw)==ref,'ARCHIVE_PUBLICATION')
        for key,value in scopes.items():require(save(plan['scope_refs'][key]['path'],value)==plan['scope_refs'][key],'SCOPE_PUBLICATION')
        for ref,raw in zip(plan['canonical_proposal_refs'],after):require(save_raw(ref['path'],raw)==ref,'CANON_PROPOSAL_PUBLICATION')
        for ref,raw in zip(plan['main_proposal_refs'],main_after):require(save_raw(ref['path'],raw)==ref,'MAIN_PROPOSAL_PUBLICATION')
        return save(out/'registration.plan.json',plan)
    planref,audit=guarded(ctx,held,operation)
    guardref=save(out/'propose.guard.closed.json',audit)
    return dict(status='ROOT_PLAN_PREPARED_NOT_REGISTERED',plan_ref=planref,scope_refs=plan['scope_refs'],guard_ref=guardref,
        current_pair_written=False,Main_written=False,formal_acceptance=False)

def plan_context(plan_ref):
    plan=doc(plan_ref)
    require(plan.get('schema')=='researchos.root-w09-nf4-registration-plan.v1','PLAN_SCHEMA')
    ctx=request_context(plan['request_ref'],plan['root_request_audit_ref'])
    require(Path(plan_ref['path'])==ctx['out']/'registration.plan.json','EXACT_PLAN_LOCATION')
    before=[read_ref(r) for r in plan['before_archive_refs']]
    expected,scopes,after,main_after=model(ctx,before,plan['before_archive_refs'])
    require(plan==expected,'EXACT_RECOMPUTED_PLAN')
    for key,value in scopes.items():require(read_ref(plan['scope_refs'][key])==encoded(value),'EXACT_SCOPE_BYTES')
    for ref,raw in zip(plan['canonical_proposal_refs'],after):require(read_ref(ref)==raw,'EXACT_CANON_PROPOSAL_BYTES')
    for ref,raw in zip(plan['main_proposal_refs'],main_after):require(read_ref(ref)==raw,'EXACT_MAIN_PROPOSAL_BYTES')
    ctx.update(plan=plan,plan_ref=plan_ref,before_raw=before,scopes=scopes,after_raw=after,main_after=main_after)
    ctx['refs']=unique_refs(ctx['refs']+[plan_ref,*plan['before_archive_refs'],*plan['scope_refs'].values(),
        *plan['canonical_proposal_refs'],*plan['main_proposal_refs']])
    return ctx

def check_or_activate(mode,plan_ref):
    require(mode in ('check','activate'),'CANON_STAGE')
    ctx=plan_context(plan_ref);plan=ctx['plan'];request=ctx['request'];out=ctx['out']
    require([pin(p) for p in CANON]==plan['before_canonical_refs'],'CURRENT4_BEFORE_REGISTRATION')
    require(not (out/'activate.intent.json').exists() and not (out/'activate.completed.json').exists(),'REGISTRATION_ALREADY_ATTEMPTED')
    excluded=set(CANON[:2]) if mode=='activate' else set()
    refs=ctx['refs']+plan['before_canonical_refs']+[request['main_profile_ref'],request['formal_index_ref']]
    refs=[r for r in refs if Path(r['path']) not in excluded]
    def operation():
        again=plan_context(plan_ref)
        require(again['plan']==plan and [pin(p) for p in CANON]==plan['before_canonical_refs'],'GUARDED_PLAN_CURRENT4')
        if mode=='check':return dict(complete_byte_inverse=True,canonical_after_refs=plan['canonical_after_refs'])
        save(out/'activate.intent.json',dict(plan_ref=plan_ref,created_utc=now_text(),automatic_retry=False,
            expected_pair=plan['before_canonical_refs'][:2],shared_TP_ref=ctx['pins']['TP']))
        tp=load_module(ctx['pins']['TP'],'w09_accepted_shared_canonical_transactions')
        def transform(cp,ow):
            require(encoded(cp)==ctx['before_raw'][0] and encoded(ow)==ctx['before_raw'][1],'TP_OWNED_EXACT_BEFORE')
            ctx['core'].validate_lease(request['lease'],now(),ctx['core'].utc(request['created_utc']))
            expected,_,after,_=model(ctx,ctx['before_raw'],plan['before_archive_refs'])
            require(expected==plan,'TP_OWNED_EXACT_AFTER_PLAN')
            return decode(after[0]),decode(after[1])
        return tp.update_pair(plan['before_canonical_refs'][:2],transform,out,'activate')
    result,audit=guarded(ctx,refs,operation)
    guardref=save(out/(mode+'.guard.closed.json'),audit)
    if mode=='check':return dict(status='ROOT_PLAN_CHECKED_NOT_REGISTERED',plan_ref=plan_ref,guard_ref=guardref,**result)
    require([pin(p) for p in CANON]==plan['canonical_after_refs'],'ACTIVATED_CURRENT4_EXACT')
    completed=dict(schema='researchos.root-w09-nf4-registration-completed.v1',status='ROOT_SCOPE_REGISTERED',issued_by=ROOT,
        completed_utc=now_text(),plan_ref=plan_ref,kind=plan['kind'],scope_refs=plan['scope_refs'],canonical_after_refs=plan['canonical_after_refs'],
        transaction=result,guard_ref=guardref,all_guards_closed=True,formal_acceptance=False,parent_acceptance=False,formal_case_accepted_delta=0)
    ref=save(out/'activate.completed.json',completed)
    return dict(status='ROOT_SCOPE_REGISTERED',activation_ref=ref,scope_refs=plan['scope_refs'],canonical_after_refs=plan['canonical_after_refs'])

def activated_context(plan_ref):
    ctx=plan_context(plan_ref);out=ctx['out'];plan=ctx['plan'];ref=pin(out/'activate.completed.json');completed=doc(ref)
    require(completed['schema']=='researchos.root-w09-nf4-registration-completed.v1'
        and completed['status']=='ROOT_SCOPE_REGISTERED' and completed['plan_ref']==plan_ref and completed['scope_refs']==plan['scope_refs']
        and completed['canonical_after_refs']==plan['canonical_after_refs'] and completed['all_guards_closed'] is True,'REGISTERED_ACTIVATION_RECEIPT')
    ctx.update(activation_ref=ref,activation=completed)
    ctx['refs']=unique_refs(ctx['refs']+[ref,completed['guard_ref']])
    return ctx


def finalize_native_requests(plan_ref,audits_ref):
    ctx=activated_context(plan_ref);plan=ctx['plan'];out=ctx['out'];core=ctx['core'];request=ctx['request']
    require(plan['kind']=='NATIVE_SCOPES','NATIVE_PLAN_ONLY')
    require([pin(p) for p in CANON]==plan['canonical_after_refs'],'NATIVE_CURRENT4_AFTER_ACTIVATION')
    audits=doc(audits_ref)
    require(set(audits)=={'schema','issued_by','activation_ref','scope_audit_refs'}
        and audits['schema']=='researchos.root-w09-native-scope-actual-audits.v1' and audits['issued_by']==ROOT
        and audits['activation_ref']==ctx['activation_ref'] and set(audits['scope_audit_refs'])==set(core.SELECTORS),'ACTUAL_SCOPE_AUDIT_BUNDLE')
    held=[audits_ref]
    for key in core.SELECTORS:
        refs,stamp,returned=actual_audit(ctx['native'],audits['scope_audit_refs'][key],ROOT,plan['scope_refs'][key]['sha256'])
        require(core.utc(ctx['activation']['completed_utc'])<=core.utc(stamp)<=now()
            and ctx['activation_ref']['sha256'] in returned and 'ROOT_SCOPE_REGISTERED' in returned,
            'COMPLETE_ACTIVATION_RETURN_PRECEDES_NATIVE_REQUEST')
        held.extend(refs)
    refs=ctx['refs']+held+plan['canonical_after_refs']+[request['main_profile_ref'],request['formal_index_ref']]
    def operation():
        require([pin(p) for p in CANON]==plan['canonical_after_refs'],'FINALIZE_CURRENT4')
        cp=decode(read_ref(plan['canonical_after_refs'][0]));ow=decode(read_ref(plan['canonical_after_refs'][1]))
        vector=dict(schema='researchos.w09-four-selector-native-canonical-vector.v1',checkpoint_revision=cp['revision'],
                    ownership_revision=ow['revision'],refs=plan['canonical_after_refs'])
        require(type(cp['revision']) is int and cp['revision']>371 and type(ow['revision']) is int and ow['revision']>175,'NF4_CURRENT_REVISIONS')
        vr=save(out/'native.canonical-vector.json',vector);requests={};commands={}
        for selector in core.SELECTORS:
            scope=ctx['scopes'][selector]
            core.validate_lease({k:scope[k] for k in ('lease_id','lease_issued_at','lease_expires_at')},now())
            q=dict(schema='researchos.root-w09-four-selector-native-request.v1',issued_by=ROOT,selector=selector,
                scope_ref=plan['scope_refs'][selector],canonical_vector_ref=vr,calling_contract_ref=ctx['pins']['NF_contract'],
                scope_audit_ref=audits['scope_audit_refs'][selector])
            qr=save(out/('native.request.'+selector+'.json'),q)
            # Authority-only validation: no NF4 prepare/run branch is called here.
            ctx['native'].validate_authority(qr,ctx['native'].choice(selector))
            requests[selector]=qr
            python=ctx['native'].choice(selector)['tool_refs']['python']['path']
            commands[selector]={stage:[python,'-I','-S','-B','-X','utf8',ctx['pins']['NF_'+stage]['path'],selector,
                qr['path'],qr['sha256'],str(qr['bytes'])] for stage in ('prepare','run')}
        return dict(vector_ref=vr,request_refs=requests,future_argv=commands)
    result,audit=guarded(ctx,refs,operation);guardref=save(out/'native-requests.guard.closed.json',audit)
    return dict(status='ROOT_NATIVE_REQUESTS_READY_NOT_EXECUTED',activation_ref=ctx['activation_ref'],scope_refs=plan['scope_refs'],
        guard_ref=guardref,actual_Go_runs=0,actual_Native_runs=0,formal_acceptance=False,**result)

def main(args):
    require(len(args) in (4,7),'MODE_AND_EXACT_REFS')
    mode=args[0];ref=dict(path=args[1],sha256=args[2],bytes=int(args[3]));ref_shape(ref)
    if mode=='propose':
        require(len(args)==7,'PROPOSE_REQUIRES_COMPLETED_ROOT_REQUEST_AUDIT')
        result=propose(ref,dict(path=args[4],sha256=args[5],bytes=int(args[6])))
    elif mode in ('check','activate'):
        require(len(args)==4,'CANON_STAGE_ARGUMENTS');result=check_or_activate(mode,ref)
    elif mode=='finalize-native-requests':
        require(len(args)==7,'FINALIZE_REQUIRES_COMPLETED_ACTIVATION_AUDITS')
        result=finalize_native_requests(ref,dict(path=args[4],sha256=args[5],bytes=int(args[6])))
    else:raise ValueError('UNKNOWN_STAGE')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':
    try:main(sys.argv[1:])
    except BaseException as exc:
        # The actual Root host pair retains this complete failure observation.
        # No unknown child exit is replaced with the Python/outer process exit.
        print(json.dumps(dict(status='FAILED_STOP_NO_AUTOMATIC_RETRY',exception=repr(exc),
            primary_exception=repr(getattr(exc,'primary',exc)),guard_cleanup=getattr(exc,'cleanup',None),
            secondary_errors=getattr(exc,'secondary',None),transaction_journal=getattr(exc,'journal',None),
            actual_native_exit=None,actual_Go_exit=None,actual_SQL_exit=None,formal_acceptance=False),ensure_ascii=False))
        raise
