"""Future four-selector Main W09 producer. Import is inert; Root authority is required."""
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import types

R=Path('D:/作品集/ResearchOS/research-os')
N=Path(__file__).resolve().parent
W=R/'execution/v2.4/receipts/W09/W09-99'
AUTHOR='codex:/root/attach_restore_independent_review'
ROOT_ACTOR='codex:/root'
ROOT_THREAD_ID='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
ROOT_AUDIT=r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl'
CANON=tuple(R/'execution/v2.4'/f'{n}.json' for n in ('checkpoint','path_ownership','step_state','commands'))
MAX=256*1024*1024
BOOL_FALSE=('formal_dispatcher','formal_acceptance','Source_mutation','checkpoint_write','ownership_write','step_state_write','worktree_creation','automatic_retry')
ZERO=('formal_case_accepted_delta','external_model_provider_requests','paid_provider_requests','production_DB_writes')
OWNER_KEY='full_w09_main_native_producer_fullw09-20261010-05'
SLICE='FULL_W09_MAIN_NATIVE_PRODUCER_fullw09-20261010-05'

def require(ok,code):
    if not ok:raise ValueError(code)
def decode(raw):
    def unique(pairs):
        result={}
        for k,v in pairs:
            require(k not in result,'DUPLICATE_JSON_KEY');result[k]=v
        return result
    return json.loads(raw,object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('NONFINITE_JSON')))
def exact_path(p,absent=False):
    p=Path(p)
    require(p.is_absolute() and str(p)==str(p.absolute()) and '..' not in p.parts,'ABSOLUTE_CANONICAL_PATH')
    for ancestor in reversed((p,*p.parents)):
        if not ancestor.exists():
            require(absent and ancestor==p,'MISSING_PARENT_OR_INPUT');continue
        item=ancestor.lstat()
        require(not ancestor.is_symlink() and not ancestor.is_junction() and not (getattr(item,'st_file_attributes',0)&0x400),'REPARSE_PATH')
    require(p.resolve(strict=not absent)==p,'PATH_ALIAS');return p
def raw_pin(p,raw):return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def read_ref(ref):
    require(type(ref) is dict and set(ref)=={'path','sha256','bytes'},'EXACT_REF')
    require(type(ref['path']) is str and type(ref['sha256']) is str and re.fullmatch('[0-9a-f]{64}',ref['sha256'])
            and type(ref['bytes']) is int and 0<=ref['bytes']<=MAX,'TYPED_REF')
    p=exact_path(ref['path']);require(str(p)==ref['path'] and p.is_file(),'REGULAR_REF')
    with p.open('rb') as f:raw=f.read(ref['bytes']+1)
    require(raw_pin(p,raw)==ref,'REF_DRIFT');return raw
def pin(p):
    p=exact_path(p)
    with p.open('rb') as f:raw=f.read(MAX+1)
    require(len(raw)<=MAX,'FILE_CAP');return raw_pin(p,raw)
def save(root,name,value):
    require('/' not in name and '\\' not in name and name not in ('','.','..'),'FIXED_RECEIPT_NAME')
    p=exact_path(root)/name;exact_path(p,True)
    raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
    with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    return raw_pin(p,raw)
def module(ref):
    m=types.ModuleType('full_w09_'+Path(ref['path']).stem);m.__file__=ref['path'];sys.modules[m.__name__]=m
    exec(compile(read_ref(ref),ref['path'],'exec'),m.__dict__);return m
def unique(refs):
    seen={}
    for ref in refs:
        read_ref(ref);key=ref['path'].casefold()
        require(key not in seen or seen[key]==ref,'CONFLICTING_PIN');seen[key]=ref
    return list(seen.values())
def pair(href,mref):
    h=decode(read_ref(href));m=decode(read_ref(mref));home=Path(mref['path']).parent
    require(h['manifest_ref']==mref and Path(href['path']).parent==home,'PAIR_BINDING')
    require(type(m['members']) is list and m['members'],'LOCAL_LIST_MANIFEST')
    refs=[href,mref];seen=set()
    for ref in m['members']:
        require(Path(ref['path']).is_relative_to(home) and ref['path'].casefold() not in seen,'LOCAL_UNIQUE_MEMBER')
        seen.add(ref['path'].casefold());read_ref(ref);refs.append(ref)
    return h,refs
def choice(selector):
    require(selector in ('W09-G01','W09-G02','A06','C19'),'FOUR_SELECTORS_ONLY')
    all_choices=decode((N/'source.choice.json').read_bytes())
    require(set(all_choices['selectors'])=={'W09-G01','W09-G02','A06','C19'},'EXACT_FOUR_CHOICES')
    return dict(all_choices['common'],**all_choices['selectors'][selector])
def package_refs():
    h,m=pin(N/'HDF.json'),pin(N/'MF.json');obj,refs=pair(h,m)
    require(obj['actor_id']==AUTHOR and obj['status']=='SOURCE_READY_PENDING_INDEPENDENT_REVIEW','SOURCE_PACKAGE')
    return h,m,refs

def validate_authority(request_ref,c):
    from datetime import datetime, timezone
    q=decode(read_ref(request_ref))
    require(set(q)=={'schema','issued_by','selector','scope_ref','canonical_vector_ref','calling_contract_ref','scope_audit_ref'},'REQUEST_FIELDS')
    require(q['schema']=='researchos.root-w09-four-selector-native-request.v1' and q['issued_by']==ROOT_ACTOR
        and q['selector']==c['selector_key'] and Path(request_ref['path']).is_relative_to(W),'ROOT_REQUEST')
    sr=q['scope_ref'];scope=decode(read_ref(sr));contract_ref=pin(N/'root-calling-contract.json')
    require(q['calling_contract_ref']==contract_ref,'CURRENT_CALLING_CONTRACT')
    contract=decode(read_ref(contract_ref));require(set(scope)==set(contract['scope_required_fields']),'SCOPE_FIELDS')
    require(scope['schema']=='researchos.root-w09-four-selector-native-scope.v1'
        and scope['status']=='ROOT_AUTHORIZED_SINGLE_SELECTOR_NATIVE' and scope['issued_by']==scope['executor']==ROOT_ACTOR,'ROOT_SCOPE')
    require(all(scope[k] is False for k in BOOL_FALSE) and all(type(scope[k]) is int and scope[k]==0 for k in ZERO),'SCOPE_BOUNDARY')
    require(all(type(scope[k]) is int and scope[k]==v for k,v in {'maximum_go_test_runs':1,'maximum_go_list_runs':1,
        'list_timeout_seconds':240,'producer_timeout_seconds':420,'inner_Go_timeout_seconds':180}.items()),'FINITE_EXECUTION_BUDGET')
    href,mref,refs=package_refs()
    require(scope['source_handoff_ref']==href and scope['source_manifest_ref']==mref,'EXACT_SOURCE_PAIR')
    bound={key:pin(N/name) for key,name in contract['source_file_bindings'].items()}
    require(all(scope[k]==v for k,v in bound.items()),'EXACT_SOURCE_CALLERS')
    for key in ('selector_key','selector','mode','native_scope','packages','source_root','run_id','receipt_root','scratch_root',
                'output_root','selected_tests','expected_native_ids','source21','generation','resource_parent_ref','resource_owner_ref','resource_audit_ref'):
        require(scope[key]==c[key],'EXACT_SCOPE_'+key)
    review,rr=pair(scope['source_review_handoff_ref'],scope['source_review_manifest_ref'])
    dr=scope['source_review_decision_ref'];decision=decode(read_ref(dr));actor=decision.get('actor_id')
    require(dr in rr and review['source_decision_ref']==dr and review['actor_id']==actor,'SOURCE_DECISION_MEMBER')
    require(decision['schema']=='researchos.w09-four-selector-producer-independent-source-decision.v1'
        and decision['decision']=='SOURCE_ACCEPTED_FOR_ROOT_FOUR_SELECTOR_NATIVE'
        and decision['actor_role']=='INDEPENDENT_NON_AUTHOR' and type(actor) is str
        and actor.startswith('codex:/root/') and actor not in (AUTHOR,ROOT_ACTOR),'INDEPENDENT_SOURCE_DECISION')
    for key,want in dict(source_handoff_ref=href,source_manifest_ref=mref,calling_contract_ref=contract_ref,**bound).items():
        require(decision[key]==want,'REVIEW_BINDING_'+key)
    all_choices=decode(read_ref(bound['choice_ref']))
    require(decision['selectors']==all_choices['selectors'] and decision['source21']==c['source21']
        and decision['actual_executed'] is False and type(decision['formal_case_accepted_delta']) is int
        and decision['formal_case_accepted_delta']==0,'SOURCE_REVIEW_BOUNDARY')
    audits=[]
    for ref,who,digest in ((scope['source_author_audit_ref'],AUTHOR,href['sha256']),
        (scope['source_review_audit_ref'],actor,dr['sha256']),(q['scope_audit_ref'],ROOT_ACTOR,sr['sha256'])):
        audits.extend(actual_audit(ref,who,digest))
    issued=datetime.fromisoformat(scope['lease_issued_at']);expires=datetime.fromisoformat(scope['lease_expires_at'])
    require(issued.tzinfo is not None and expires.tzinfo is not None and 0<(expires-issued).total_seconds()<=3600
        and issued<=datetime.now(timezone.utc)<expires and type(scope['lease_id']) is str
        and re.fullmatch('[0-9a-f]{32}',scope['lease_id']),'CURRENT_FINITE_LEASE')
    vr=q['canonical_vector_ref'];vector=decode(read_ref(vr))
    require(set(vector)=={'schema','checkpoint_revision','ownership_revision','refs'}
        and vector['schema']=='researchos.w09-four-selector-native-canonical-vector.v1'
        and type(vector['checkpoint_revision']) is int and vector['checkpoint_revision']>371
        and type(vector['ownership_revision']) is int and vector['ownership_revision']>175,'POST_REVIEW_CANONICAL_VECTOR')
    require(len(vector['refs'])==4 and [r['path'] for r in vector['refs']]==[str(p) for p in CANON],'FOUR_ORDERED_CURRENT_CANONICAL')
    cp,ow,ss,commands=[decode(read_ref(r)) for r in vector['refs']]
    require(cp['revision']==vector['checkpoint_revision'] and ow['revision']==vector['ownership_revision']
        and cp['project_id']=='aede0678-7308-43dc-b9f2-cfe3d90cfdfb' and cp['head']==c['expected_git_head'],'CURRENT_PROJECT_VECTOR')
    require(ow['active_integrator']['id']==ROOT_ACTOR and ow['shared_integrator']=='qoder-desktop:/root/platform_owner'
        and ow['card_path_bindings']['W09-99']['owner']==ROOT_ACTOR,'ROOT_CURRENT_ROLE')
    require(cp['work_in_progress']['w09_native_producer_scope_generations'][c['generation']][c['selector_key']]==sr,'CANONICAL_SCOPE_REGISTRATION')
    owner=dict(generation=c['generation'],owner=ROOT_ACTOR,current_source_writer=None,state='ROOT_REGISTERED_PENDING_SELECTOR_NATIVE',scope_ref=sr,
        source_handoff_ref=href,source_manifest_ref=mref,source_review_handoff_ref=scope['source_review_handoff_ref'],
        source_review_manifest_ref=scope['source_review_manifest_ref'],source_root=str(R),selector=c['selector_key'],
        run_id=c['run_id'],receipt_root=c['receipt_root'],scratch_root=c['scratch_root'],output_root=c['output_root'],
        lease_id=scope['lease_id'],lease_issued_at=scope['lease_issued_at'],lease_expires_at=scope['lease_expires_at'],
        formal_case_accepted_delta=0,parent_acceptance=False)
    require(ow['card_path_bindings']['W09-99']['subtasks'][OWNER_KEY+'_'+c['selector_key']]==owner,'EXACT_REGISTERED_OWNER')
    worker=dict(generation=c['generation'],step_id='W09-99',slice_id=SLICE+'_'+c['selector_key'],owner=ROOT_ACTOR,state=owner['state'],scope_ref=sr,
        source_handoff_ref=href,source_review_handoff_ref=scope['source_review_handoff_ref'],run_id=c['run_id'],lease_id=scope['lease_id'])
    require([v for v in cp['workers'] if v.get('slice_id')==worker['slice_id']]==[worker],'UNIQUE_REGISTERED_WORKER')
    require(c['generation']=='fullw09-20261010-05' and c['source_root']==str(R) and re.fullmatch('[0-9a-f]{32}',c['run_id'])
        and c['output_root']==str(R/'execution/receipts/W09/retrieval'/('run-'+c['run_id']))
        and c['receipt_root']==str(N/('actual-'+c['selector_key']+'-'+c['run_id']))
        and c['scratch_root']==str(Path('C:/Users/yqyyds/.researchos/w09-native-v5')/(c['selector_key']+'-'+c['run_id'])),'FIXED_PRIVATE_PATHS')
    resource_refs=validate_scratch_parent(c)
    for ref in c['source21']:read_ref(ref)
    return unique(refs+rr+audits+resource_refs+[request_ref,sr,contract_ref,dr,vr,*vector['refs'],*bound.values()]),scope,vector

def build_environment(c):
    scratch=Path(c['scratch_root']);go=Path(c['tool_refs']['go']['path']);git=Path(c['tool_refs']['git']['path'])
    return {'SystemRoot':'C:/Windows','WINDIR':'C:/Windows','ComSpec':'C:/Windows/System32/cmd.exe',
        'PATH':str(go.parent)+';'+str(git.parent)+';C:/Windows/System32','PATHEXT':'.COM;.EXE;.BAT;.CMD',
        'USERPROFILE':str(scratch/'profile'),'LOCALAPPDATA':str(scratch/'profile'),'APPDATA':str(scratch/'profile'),
        'TEMP':str(scratch/'temp'),'TMP':str(scratch/'temp'),'GOROOT':str(go.parent.parent),'GOPATH':str(R/'.local/gopath'),
        'GOCACHE':str(scratch/'gocache'),'GOENV':'off','GOTOOLCHAIN':'local','GOPROXY':'off','GOSUMDB':'off','GOWORK':'off',
        'CGO_ENABLED':'0','GOFLAGS':'-mod=readonly -p=1','GOMAXPROCS':'2','RESEARCHOS_GO':str(go),
        'RESEARCHOS_TASK_ID':'W09','RESEARCHOS_CHECK_ID':c['selector']['check_id'],'RESEARCHOS_CASE_ID':c['selector']['case_id'],'RESEARCHOS_RETRIEVAL_MODE':('live' if c['mode']=='LIVE_WINDOWS' else 'fixture'),
        'GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'NUL','GIT_TERMINAL_PROMPT':'0','GIT_OPTIONAL_LOCKS':'0'}

def read_inputs(c):
    bp=decode(read_ref(c['compiler_blueprint_ref']));verify_directories(bp)
    refs=[pin(N/'source.choice.json'),c['compiler_blueprint_ref'],c['guard_ref'],c['owned_job_ref'],c['toolchain_ref'],
        c['identity_ref'],c['spec_manifest_ref'],*c['tool_refs'].values(),*c['source21'],*bp['stable_input_refs']]
    require(bp['source_only'] is True and bp['actual_package_count'] is None
        and bp['required_packages']==['./adapters/retrieval','./internal/domain'] and set(c['packages']).issubset(bp['required_packages']) and len(bp['allowed_package_roster'])==len(set(bp['allowed_package_roster'])),'SOURCE_COMPILER_BLUEPRINT')
    lock=decode(read_ref(c['toolchain_ref']))
    for key,ref in c['tool_refs'].items():
        require(lock['tools'][key]['path']==ref['path'] and lock['tools'][key]['sha256']==ref['sha256'],'LOCKED_TOOL_'+key)
    require(pin(sys.executable)==c['tool_refs']['python'],'LOCKED_PYTHON_EXECUTION')
    require(decode(read_ref(c['identity_ref']))['project_id']=='aede0678-7308-43dc-b9f2-cfe3d90cfdfb','IDENTITY')
    for mod in tuple(sys.modules.values()):
        for field in ('__file__','__cached__'):
            path=getattr(mod,field,None)
            if path and Path(path).is_file():refs.append(pin(Path(path).resolve()))
    return unique(refs),bp

def job_closed(result):
    if type(result) is not dict:return False
    cleanup=result.get('job_cleanup',{})
    return (type(result.get('owned_child_pid')) is int and 0<result['owned_child_pid']<=0xffffffff
        and type(result.get('creation_time_100ns')) is int and 0<result['creation_time_100ns']<=0xffffffffffffffff
        and type(cleanup.get('active_processes_last_observed')) is int and cleanup['active_processes_last_observed']==0
        and not cleanup.get('errors') and all(cleanup.get(k) is True for k in
        ('unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed')))

class EvidenceFailure(RuntimeError):
    """Keep the original exception object and independent evidence errors."""
    def __init__(self,phase,primary_exception,secondary_errors,diagnostics):
        super().__init__(phase+': '+json.dumps(dict(original_error=repr(primary_exception) if primary_exception is not None else None,
            evidence_errors=secondary_errors),ensure_ascii=False))
        self.primary_exception=primary_exception
        self.secondary_errors=list(secondary_errors)
        self.diagnostics=diagnostics


def evidence_error(errors,phase,exc,label=None):
    errors.append(dict(phase=phase,label=label,exception_type=type(exc).__name__,error=repr(exc)))


def invoke(helper,root,label,argv,env,wall):
    out=root/(label+'.stdout.raw');err=root/(label+'.stderr.raw')
    result=None;primary=None;errors=[];receipt=None
    try:
        with out.open('xb') as stdout,err.open('xb') as stderr:
            result=helper.run_owned(argv,str(R),env,stdout,stderr,wall,creation_flags=0x08000000)
        require(job_closed(result),'OWNED_JOB_UNCLOSED_OR_EXCEPTION')
        require(result['error'] is None and type(result['actual_exit']) is int and result['actual_exit']==0 and result['timed_out'] is False,'FIRST_NATIVE_FAILURE_STOP')
    except BaseException as exc:primary=exc
    # Every observation is independent; no receipt failure masks the helper error.
    streams={}
    for name,path in (('stdout',out),('stderr',err)):
        streams[name+'_ref']=None
        try:
            if path.is_file():streams[name+'_ref']=pin(path)
        except BaseException as exc:evidence_error(errors,'invocation-stream-pin',exc,name)
    creation=result.get('creation_time_100ns') if type(result) is dict else None
    record=dict(argv=argv,cwd=str(R),public_environment=env,timeout_seconds=wall,result=result,
        exception=repr(primary) if primary is not None else None,
        actual_outer_exit=result.get('actual_exit') if type(result) is dict else None,individual_child_numeric_exit=None,
        creation_time_100ns_decimal=str(creation) if type(creation) is int else None,**streams,
        evidence_errors=errors,external_model_provider_requests=0,paid_provider_requests=0,production_DB_writes=0)
    try:receipt=save(root,label+'.invocation.json',record)
    except BaseException as exc:evidence_error(errors,'invocation-receipt-save',exc,label)
    try:
        print(json.dumps(dict(progress=label,receipt_ref=receipt,actual_outer_exit=record['actual_outer_exit'],
            creation_time_100ns_decimal=record['creation_time_100ns_decimal'],original_error=record['exception'],
            evidence_errors=errors,unsaved_invocation=record if receipt is None else None)),flush=True)
    except BaseException as exc:evidence_error(errors,'invocation-progress-write',exc,label)
    if primary is not None or errors:
        raise EvidenceFailure('INVOCATION_FAILED_NO_AUTOMATIC_RETRY',primary,errors,record) from primary
    return receipt,result


def observe_invocation(root,label,errors):
    row=dict(label=label,ref=None,record=None,verified=False,job_closed=False)
    path=root/(label+'.invocation.json')
    try:present=path.is_file()
    except BaseException as exc:
        evidence_error(errors,'invocation-presence',exc,label);return row
    if not present:
        evidence_error(errors,'invocation-missing',FileNotFoundError(str(path)),label);return row
    try:row['ref']=pin(path)
    except BaseException as exc:evidence_error(errors,'invocation-pin',exc,label)
    raw=None
    try:raw=path.read_bytes()
    except BaseException as exc:evidence_error(errors,'invocation-read',exc,label)
    if raw is not None:
        try:
            record=decode(raw);require(type(record) is dict,'INVOCATION_OBJECT_REQUIRED');row['record']=record
        except BaseException as exc:evidence_error(errors,'invocation-decode',exc,label)
    if row['ref'] is not None and raw is not None and row['record'] is not None:
        try:
            require(raw_pin(path,raw)==row['ref'],'INVOCATION_CHANGED_DURING_INSPECTION')
            row['verified']=True;row['job_closed']=job_closed(row['record'].get('result'))
        except BaseException as exc:evidence_error(errors,'invocation-closure',exc,label)
    return row


def close_stage_resources(kind,created,c,stage_root,output,guards):
    errors=[];observations=[];cleanups=[];packet_ref=None
    # Guard shutdown is in the outer finally, independent of all packet inspection.
    try:
        if created and kind=='run':
            for label in ('compiler-input-list','w09-selector-main-producer'):
                try:observations.append(observe_invocation(stage_root,label,errors))
                except BaseException as exc:
                    evidence_error(errors,'invocation-inspection',exc,label)
                    observations.append(dict(label=label,ref=None,record=None,verified=False,job_closed=False))
            producer=observations[-1]
            if producer['verified'] and producer['job_closed']:
                try:
                    if output.is_dir():packet_ref=capture_packet(c,stage_root)
                except BaseException as exc:evidence_error(errors,'packet-archive',exc)
    except BaseException as exc:evidence_error(errors,'packet-inspection',exc)
    finally:
        for label,guard in reversed(guards):
            row=dict(label=label,ref=None,closed=False,observation=None,receipt_saved=not created)
            # Close, classify and save are isolated; a save error does not erase a successful close.
            try:row['observation']=guard.close()
            except BaseException as exc:evidence_error(errors,'guard-close',exc,label)
            if row['observation'] is not None:
                try:row['closed']=guard_cleanup_ok(row['observation'])
                except BaseException as exc:evidence_error(errors,'guard-close-observation',exc,label)
                if created:
                    try:
                        row['ref']=save(stage_root,label+'-guard.cleanup.actual.json',row['observation']);row['receipt_saved']=True
                    except BaseException as exc:evidence_error(errors,'guard-cleanup-save',exc,label)
            cleanups.append(row)
    return dict(errors=errors,invocations=observations,guard_cleanups=cleanups,packet_ref=packet_ref,
        all_guards_closed=all(row['closed'] for row in cleanups) and len(cleanups)==len(guards),
        all_cleanup_receipts_saved=all(row['receipt_saved'] for row in cleanups),
        all_owned_jobs_closed=(kind=='prepare' or (len(observations)==2 and all(row['verified'] and row['job_closed'] for row in observations))))


def compiler_inventory(text,c,bp):
    decoder=json.JSONDecoder();pos=0;packages=[];stable={};generated={};exports={};gomods={};embeds=[]
    cache=Path(c['scratch_root'])/'gocache'
    fields=('GoFiles','CgoFiles','CFiles','CXXFiles','MFiles','HFiles','FFiles','SFiles','SwigFiles','SwigCXXFiles','SysoFiles','CompiledGoFiles','TestGoFiles','XTestGoFiles','EmbedFiles','TestEmbedFiles','XTestEmbedFiles')
    expected={x['path']:x for x in bp['stable_input_refs']}
    while pos<len(text):
        while pos<len(text) and text[pos].isspace():pos+=1
        if pos==len(text):break
        pkg,pos=decoder.raw_decode(text,pos);require(not pkg.get('Error') and not pkg.get('DepsErrors'),'GO_LIST_PACKAGE_ERROR')
        packages.append(pkg.get('ImportPath'));directory=Path(pkg['Dir']) if pkg.get('Dir') else None
        for field in fields:
            for name in pkg.get(field,[]):
                require(directory is not None,'GO_LIST_INPUT_DIR');p=Path(name);p=p if p.is_absolute() else directory/p;p=exact_path(p)
                ref=pin(p)
                if p.is_relative_to(cache):generated[ref['path']]=ref
                else:
                    require(expected.get(ref['path'])==ref,'GO_LIST_UNHELD_OR_DRIFTED_INPUT');stable[ref['path']]=ref
                if field.endswith('EmbedFiles'):embeds.append(dict(package=pkg['ImportPath'],field=field,ref=ref))
        mod=pkg.get('Module')
        while mod:
            if mod.get('GoMod'):
                ref=pin(mod['GoMod']);require(expected.get(ref['path'])==ref,'MODULE_GOMOD_NOT_HELD');gomods[ref['path']]=ref
            mod=mod.get('Replace')
        if pkg.get('Export'):
            p=exact_path(pkg['Export']);require(p.is_relative_to(cache),'EXPORT_NOT_PRIVATE_GOCACHE');ref=pin(p);exports[ref['path']]=ref
        elif not pkg.get('DepOnly') and pkg.get('Name') not in (None,'main'):
            require(pkg.get('ImportPath') in ('unsafe','builtin'),'REQUIRED_EXPORT_MISSING')
    require(packages and len(packages)==len(set(packages)) and set(packages)<=set(bp['allowed_package_roster'])
        and set(bp['required_test_packages'])<=set(packages),'FINITE_TWO_PACKAGE_TEST_CLOSURE')
    verify_directories(bp)
    require(gomods=={x['path']:x for x in bp['module_go_mod_refs']},'EXACT_MODULE_GOMOD_SET')
    require(exports and generated,'ACTUAL_EXPORT_AND_GENERATED_INPUTS_REQUIRED')
    return dict(schema='researchos.w09-four-selector-actual-compiler-input-inventory.v1',package_count=len(packages),packages=packages,
        stable_build_input_refs=list(stable.values()),private_generated_input_refs=list(generated.values()),private_export_refs=list(exports.values()),
        module_go_mod_refs=list(gomods.values()),actual_embed_files=embeds,blueprint_ref=c['compiler_blueprint_ref'],
        source_root=str(R),private_GOCACHE=str(cache),actual_go_list_export=True,source21=c['source21'],formal_acceptance=False)

def validate_packet(c,packet):
    report_path=packet/'report.json';tool_path=packet/'native-tool-run.json'
    report=decode(report_path.read_bytes());tool=decode(tool_path.read_bytes())
    require(packet==Path(c['output_root']) and report['run_id']==c['run_id']==tool['run_id'],'FIXED_MAIN_NATIVE_RUN')
    require(report['version_manifest']['git_head']==c['expected_git_head'],'ACTUAL_HEAD')
    require(report['version_manifest']['source_sha256']=={Path(ref['path']).relative_to(R).as_posix():'sha256:'+ref['sha256'] for ref in c['source21']},'EXACT_SOURCE21')
    relative=report_path.relative_to(R).as_posix();source=dict(report);source['report_reference']=relative
    require(tool['report_ref']==relative and tool['report_sha256']==pin(report_path)['sha256'],'TOOL_SAME_REPORT')
    require(tool['schema']=='researchos.w09-native-producer-tool-run.v1' and tool['formal_acceptance']=='NOT_RUN','TOOL_SCHEMA')
    require(report['actual_invocation']==tool['actual_invocation']==[c['tool_refs']['go']['path'],*c['go_test_argv_suffix']],'EXACT_NATIVE_ARGV')
    require(report['task_id']=='W09' and report['check_id']==(c['selector']['check_id'] or None)
        and report['case_id']==(c['selector']['case_id'] or None) and report['scope']==c['native_scope'],'EXACT_ROUTE_MODE')
    require(tool['stdout_ref']==report['raw_evidence_references'][0] and tool['stderr_ref']==report['raw_evidence_references'][1]
        and tool['stdout_sha256']==pin(packet/'go-test.stdout.jsonl')['sha256']
        and tool['stderr_sha256']==pin(packet/'go-test.stderr.txt')['sha256'],'EXACT_ORIGINAL_STREAMS')
    require(type(tool['native_exit_code']) is int and tool['native_exit_code']==0 and type(report['exit_code']) is int
        and report['exit_code']==0 and report['timed_out'] is False and report['status']=='PASS','ACTUAL_NATIVE_PASS')
    require(report['formal_construction_acceptance']=='NOT_RUN_POSTRUN_REVIEW_PENDING'
        and type(report['formal_case_accepted_delta']) is int and report['formal_case_accepted_delta']==0,'NATIVE_NOT_FORMAL')
    require(report['selected_tests']==c['selected_tests'] and sorted(report['assertion_ids'])==sorted(c['expected_native_ids']),'EXACT_SELECTED_TESTS_ASSERTIONS')
    closure=module(next(ref for ref in c['source21'] if ref['path']==str(R/'ops/ci/w09_evidence_closure.py')))
    closure.verify_native(R,source,report,c['expected_native_ids'],c['selected_tests'])
    owned=closure.verify_owned(R,source,report,c['selected_tests'],c['assertion_owner'])
    if c['selector_key'] in ('W09-G01','C19'):closure.verify_c19(owned)
    if c['selector_key'] in ('W09-G01','W09-G02','A06'):closure.verify_a06(owned)
    require(all(Path(rec['owned_export_ref']['path']).is_relative_to(packet/'owned') for rec in report['assertion_results']),'ABSOLUTE_ASSERTION_PINS')
    return dict(report_ref=pin(report_path),tool_run_ref=pin(tool_path),run_id=c['run_id'],source_root=str(R),
        selector=c['selector'],mode=c['mode'],native_ids=c['expected_native_ids'],native_test_exit=report['exit_code'],
        owned_members=len(owned['members']),mode_independent_review='NOT_RUN_REQUIRED',formal_acceptance=False)

def guard_cleanup_ok(v):return v['closed'] is True and not v['errors'] and v['retained_handles_count']==0

def capture_packet(c,root):
    packet=exact_path(c['output_root']);require(packet.is_dir(),'FIXED_PACKET_DIRECTORY')
    archive=root/'native-packet';exact_path(archive,True);archive.mkdir()
    mapping=[]
    for p in sorted(packet.rglob('*')):
        exact_path(p);require(p.is_relative_to(packet),'PACKET_ESCAPE')
        if p.is_file():
            relative=p.relative_to(packet);target=archive/relative;target.parent.mkdir(parents=True,exist_ok=True)
            exact_path(target,True)
            with target.open('xb') as f:f.write(p.read_bytes());f.flush();os.fsync(f.fileno())
            original=pin(p);copied=pin(target)
            require((original['sha256'],original['bytes'])==(copied['sha256'],copied['bytes']),'EXACT_RAW_ARCHIVE')
            mapping.append(dict(original_ref=original,archive_ref=copied))
    return save(root,'native-packet.public-index.json',dict(schema='researchos.w09-four-selector-native-packet.v1',
        run_id=c['run_id'],consumer_source_root=str(R),original_report_ref=pin(packet/'report.json') if (packet/'report.json').is_file() else None,
        original_tool_run_ref=pin(packet/'native-tool-run.json') if (packet/'native-tool-run.json').is_file() else None,
        raw_copy_mapping=mapping,immutable_original_bytes=True,formal_acceptance=False))

def stage(kind,args):
    require(kind in ('prepare','run') and len(args)==4,'SELECTOR_AND_THREE_EXACT_ROOT_REQUEST_ARGUMENTS')
    c=choice(args[0]);request_ref=dict(path=args[1],sha256=args[2],bytes=int(args[3]))
    auth_refs,scope,vector=validate_authority(request_ref,c)
    gm=module(c['guard_ref']);helper=module(c['owned_job_ref'])
    input_refs,bp=read_inputs(c)
    input_refs=unique(auth_refs+input_refs)
    guards=[];cleanups=[];receipts=[];error=None;primary=None;success=False;created=False;summary=None;packet_ref=None
    actual=Path(c['receipt_root']);scratch=Path(c['scratch_root']);output=Path(c['output_root'])
    stage_root=actual if kind=='prepare' else actual/'producer'
    def acquire(label,refs):
        guard=gm.SourceReadGuard(per_file_cap=MAX,total_cap=2*1024*1024*1024);guards.append((label,guard));guard.acquire(unique(refs));return guard
    try:
        acquire('input',input_refs)
        acquire('runtime',[pin(p) for p in helper.runtime_resource_paths()])
        validate_authority(request_ref,c)
        exact_path(output,True);require(not output.exists(),'ONE_SHOT_OUTPUT_ALREADY_EXISTS')
        if kind=='prepare':
            require(not actual.exists() and not scratch.exists(),'ONE_SHOT_PREPARATION_ALREADY_EXISTS')
            exact_path(actual,True);actual.mkdir();created=True
            exact_path(scratch,True);scratch.mkdir()
            for name in ('profile','temp','gocache'):(scratch/name).mkdir()
            save(actual,'preparation.intent.json',dict(request_ref=request_ref,canonical_vector_ref=pin(scope_path(request_ref)),
                source_root=str(R),run_id=c['run_id'],output_root=str(output),scratch_root=str(scratch),
                source21=c['source21'],all_actual_product_calls=0,formal_acceptance=False))
            summary=dict(schema='researchos.w09-four-selector-preparation-ready.v1',request_ref=request_ref,canonical_vector=vector,
                source_choice_ref=pin(N/'source.choice.json'),environment=build_environment(c),source21=c['source21'],
                run_id=c['run_id'],source_root=str(R),output_root=str(output),scratch_root=str(scratch),
                native_started=False,Main_source_written=False,Canon_written=False)
        else:
            ready_ref=pin(actual/'prepare.ready.json');ready=decode(read_ref(ready_ref))
            require(ready['request_ref']==request_ref and ready['canonical_vector']==vector and ready['status']=='PREPARED_ALL_GUARDS_CLOSED','SAME_PREPARE_VECTOR_REQUEST')
            require(ready['source_choice_ref']==pin(N/'source.choice.json') and ready['source21']==c['source21'] and ready['all_guards_closed'] is True,'PREPARE_CURRENT_SOURCE')
            for ref in ready['guard_cleanup_refs']:require(guard_cleanup_ok(decode(read_ref(ref))),'PREPARE_CLEANUP')
            acquire('preparation',[ready_ref,*ready['guard_cleanup_refs']])
            require(not stage_root.exists(),'ONE_SHOT_PRODUCER_ALREADY_ATTEMPTED');exact_path(stage_root,True);stage_root.mkdir();created=True
            env=build_environment(c);require(env==ready['environment'],'SAME_EXPLICIT_ENVIRONMENT')
            for name in ('profile','temp','gocache'):exact_path(scratch/name)
            require(not any((scratch/'gocache').iterdir()),'FRESH_PRIVATE_GOCACHE')
            save(stage_root,'attempt.intent.json',dict(request_ref=request_ref,canonical_vector=vector,run_id=c['run_id'],
                actual_environment=env,one_go_list=True,one_go_test=True,no_automatic_retry=True))
            list_argv=[c['tool_refs']['go']['path'],*c['list_argv_suffix']]
            validate_authority(request_ref,c);verify_directories(bp)
            receipt,_=invoke(helper,stage_root,'compiler-input-list',list_argv,env,c['list_timeout_seconds']);receipts.append(receipt)
            inv=compiler_inventory((stage_root/'compiler-input-list.stdout.raw').read_text(encoding='utf-8'),c,bp)
            inventory_ref=save(stage_root,'actual-compiler-input-inventory.json',inv)
            acquire('compiler-exports',[inventory_ref,*inv['private_generated_input_refs'],*inv['private_export_refs'],*inv['module_go_mod_refs']])
            permit=save(stage_root,'launcher.permit.json',dict(schema='researchos.w09-four-selector-launcher-permit.v1',request_ref=request_ref,
                selector=c['selector_key'],run_id=c['run_id'],output_root=c['output_root'],launcher_ref=pin(N/'full_w09_launcher.source.py'),
                runner_ref=next(ref for ref in c['source21'] if ref['path']==str(R/'ops/ci/retrieval.py')),environment=env))
            acquire('launcher-permit',[permit])
            argv=[c['tool_refs']['python']['path'],'-I','-S','-B','-X','utf8',str(N/'full_w09_launcher.source.py'),permit['path'],permit['sha256'],str(permit['bytes'])]
            validate_authority(request_ref,c);verify_directories(bp)
            receipt,_=invoke(helper,stage_root,'w09-selector-main-producer',argv,env,c['producer_timeout_seconds']);receipts.append(receipt)
            # Bind the emitted exact run, never select a latest directory or glob.
            emitted=decode((stage_root/'w09-selector-main-producer.stdout.raw').read_bytes())
            require(emitted['report_reference']==(output/'report.json').relative_to(R).as_posix()
                    and emitted['tool_run_reference']==(output/'native-tool-run.json').relative_to(R).as_posix(),'EXACT_PRODUCER_STDOUT_REFS')
            validate_authority(request_ref,c);verify_directories(bp)
            summary=validate_packet(c,output);summary.update(compiler_inventory_ref=inventory_ref,launcher_permit_ref=permit,prepare_ready_ref=ready_ref)
        for ref in input_refs:read_ref(ref)
        success=True
    except BaseException as exc:primary=exc;error=repr(exc)
    finally:
        closed=close_stage_resources(kind,created,c,stage_root,output,guards)
    cleanups=closed['guard_cleanups'];errors=closed['errors'];packet_ref=closed['packet_ref']
    receipts=[row['ref'] for row in closed['invocations'] if row['ref'] is not None]
    all_closed=closed['all_guards_closed'];all_jobs_closed=closed['all_owned_jobs_closed']
    success=success and all_closed and closed['all_cleanup_receipts_saved'] and not errors
    if kind=='run':success=success and packet_ref is not None and len(receipts)==2 and all_jobs_closed
    result=dict(schema='researchos.w09-four-selector-stage-closed.v2',stage=kind,
        status=('PREPARED_ALL_GUARDS_CLOSED' if kind=='prepare' else 'MAIN_SELECTOR_NATIVE_PACKET_CLOSED_PENDING_INDEPENDENT_REVIEW') if success else 'FAILED_NO_AUTOMATIC_RETRY',
        error=error,original_exception_type=type(primary).__name__ if primary is not None else None,
        original_invocation_diagnostics=primary.diagnostics if isinstance(primary,EvidenceFailure) else None,
        original_invocation_errors=primary.secondary_errors if isinstance(primary,EvidenceFailure) else [],
        cleanup_errors=errors,summary=summary,native_packet_ref=packet_ref,request_ref=request_ref,
        invocation_refs=receipts,invocation_observations=closed['invocations'],guard_cleanups=cleanups,
        all_guards_closed=all_closed,all_cleanup_receipts_saved=closed['all_cleanup_receipts_saved'],
        actual_formal_consumers=False,formal_case_accepted_delta=0,all_owned_jobs_closed=all_jobs_closed,
        individual_unobserved_native_exits=None,external_model_provider_requests=0,paid_provider_requests=0,
        Main_source_written=False,Canon_written=False,process_loss_requires_explicit_Root_reconciliation=True,automatic_retry=False)
    published=False
    if created:
        try:
            if success and kind=='prepare':
                result.update(summary);result['guard_cleanup_refs']=[row['ref'] for row in cleanups]
                save(actual,'prepare.ready.json',result)
            else:save(stage_root,'validation.closed.json',result)
            published=True
        except BaseException as exc:
            evidence_error(errors,'stage-result-save',exc);result['status']='FAILED_NO_AUTOMATIC_RETRY';success=False
    try:
        print(json.dumps(dict(status=result['status'],stage=kind,receipt_root=str(stage_root),error=error,
            cleanup_errors=errors,all_guards_closed=all_closed,all_owned_jobs_closed=all_jobs_closed,
            unsaved_stage_result=result if not published else None)),flush=True)
    except BaseException as exc:
        evidence_error(errors,'stage-progress-write',exc);result['status']='FAILED_NO_AUTOMATIC_RETRY';success=False
    if not success:
        raise EvidenceFailure('STAGE_FAILED_NO_AUTOMATIC_RETRY',primary,errors,result) from primary

def scope_path(request_ref):return decode(read_ref(request_ref))['canonical_vector_ref']['path']

def exact_host_peer_author(actor):
    """Map a canonical Codex peer identity to its exact host message author."""
    require(type(actor) is str and re.fullmatch(r'codex:/root/[a-z0-9_]+(?:/[a-z0-9_]+)*',actor) is not None,'CANONICAL_PEER_ACTOR')
    return actor.removeprefix('codex:')

def actual_audit(ref,actor,binding):
    """Verify finite original Root audit records, not self-reported provenance."""
    a=decode(read_ref(ref))
    require(set(a)=={'schema','actor_id','Root_thread_id','source_audit_path','source_line_offsets',
                    'original_line_sha256','source_prefix_size_observed','original_capture_ref','binding_sha256'},'AUDIT_FIELDS')
    require(a['schema']=='researchos.w09-native-producer.actual-audit.v1' and a['actor_id']==actor
        and a['Root_thread_id']==ROOT_THREAD_ID and a['source_audit_path']==ROOT_AUDIT
        and a['binding_sha256']==binding,'AUDIT_FIXED_ROOT_ACTOR_BINDING')
    raw=read_ref(a['original_capture_ref']);lines=raw.splitlines(keepends=True)
    require(len(lines)==3 and all(line.endswith(b'\n') for line in lines),'THREE_ORIGINAL_AUDIT_RECORDS')
    head,call,result=[decode(line) for line in lines]
    require(head.get('type')=='session_meta' and head.get('ordinal')==0
        and head.get('payload',{}).get('id')==ROOT_THREAD_ID,'ROOT_AUDIT_SESSION')
    first,last=call.get('payload',{}),result.get('payload',{})
    require(type(call.get('ordinal')) is int and type(result.get('ordinal')) is int
        and 0<call['ordinal']<result['ordinal'],'AUDIT_ORDER')
    if actor==ROOT_ACTOR:
        require(call.get('type')==result.get('type')=='response_item'
            and first.get('type') in ('function_call','custom_tool_call')
            and last.get('type') in ('function_call_output','custom_tool_call_output')
            and type(first.get('call_id')) is str and bool(first['call_id'])
            and first['call_id']==last.get('call_id') and type(first.get('name')) is str,'ROOT_ACTUAL_TOOL_PAIR')
    else:
        host_author=exact_host_peer_author(actor)
        require(call.get('type')=='inter_agent_communication_metadata' and result.get('type')=='response_item'
            and result['ordinal']==call['ordinal']+1 and call.get('timestamp')==result.get('timestamp')
            and last.get('type')=='agent_message' and last.get('author')==host_author and last.get('recipient')=='/root'
            and result.get('metadata',{}).get('client_authored') is False
            and type(last.get('content')) is list and len(last['content'])==1
            and last['content'][0].get('type')=='input_text','ACTUAL_PEER_DELIVERY')
    require(binding in lines[1].decode('utf-8')+lines[2].decode('utf-8'),'AUDIT_ARTIFACT_BINDING')
    offsets=a['source_line_offsets'];hashes=a['original_line_sha256'];size=a['source_prefix_size_observed']
    require(type(offsets) is list and len(offsets)==3 and offsets==sorted(set(offsets))
        and all(type(v) is int and v>=0 for v in offsets) and offsets[0]==0
        and type(hashes) is list and len(hashes)==3 and type(size) is int and size>0,'AUDIT_RANGES')
    with Path(ROOT_AUDIT).open('rb') as stream:
        for offset,digest,line in zip(offsets,hashes,lines):
            require(offset+len(line)<=size and hashlib.sha256(line).hexdigest()==digest,'AUDIT_RANGE_DIGEST')
            stream.seek(offset);require(stream.read(len(line))==line,'ACTUAL_ROOT_AUDIT_BYTES')
    return [ref,a['original_capture_ref']]

def verify_directories(bp):
    for directory,names in bp['main_directory_inventory'].items():
        p=exact_path(directory)
        actual=sorted(child.name for child in p.iterdir() if child.is_file())
        require(actual==names,'MAIN_COMPILE_DIRECTORY_INVENTORY_DRIFT')

def validate_scratch_parent(c):
    """Bind actual Root resource provenance and reobserve the exact physical C path."""
    parent=Path('C:/Users/yqyyds/.researchos/w09-native-v5')
    resource=decode(read_ref(c['resource_parent_ref']))
    require(resource['schema']=='researchos.w09-fixed-physical-C-resource-parent-intent.v1'
        and resource['actor_id']==ROOT_ACTOR and resource['project_identity_ref']==c['identity_ref']
        and resource['exact_parent_paths']==[str(parent.parent),str(parent)]
        and resource['resource_scope_only'] is True and resource['execution_grant'] is False
        and resource['RootScope_issued'] is False and resource['Native_calls']==0
        and resource['resource_owner_marker_ref']==c['resource_owner_ref'],'EXACT_ROOT_RESOURCE_ONLY')
    for directory in (parent.parent,parent):
        require(exact_path(directory).is_dir(),'ACTUAL_PHYSICAL_C_RESOURCE_PARENT')
    require(c['resource_owner_ref']['path']==str(parent/'RESOURCE_OWNER.json'),'EXACT_RESOURCE_OWNER_PATH')
    owner=decode(read_ref(c['resource_owner_ref']))
    require(owner==dict(schema='researchos.w09-native-private-resource-owner.v1',
        project_id='aede0678-7308-43dc-b9f2-cfe3d90cfdfb',repository_root=str(R),scratch_parent=str(parent)),
        'EXACT_PROJECT_RESOURCE_OWNER')
    audits=actual_audit(c['resource_audit_ref'],ROOT_ACTOR,c['resource_parent_ref']['sha256'])
    return [c['resource_parent_ref'],c['resource_owner_ref'],*audits]
