"""Future two-stage Main C19 producer. Import is inert; Root authority is required."""
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
AUTHOR='codex:/root/command_queue_impl'
ROOT_ACTOR='codex:/root'
CANON=tuple(R/'execution/v2.4'/f'{n}.json' for n in ('checkpoint','path_ownership','step_state','commands'))
MAX=256*1024*1024
BOOL_FALSE=('formal_dispatcher','formal_acceptance','Source_mutation','checkpoint_write','ownership_write','step_state_write','worktree_creation','automatic_retry')
ZERO=('formal_case_accepted_delta','external_model_provider_requests','paid_provider_requests','production_DB_writes')
OWNER_KEY='c19_main_root_native_producer'
SLICE='C19_MAIN_ROOT_NATIVE_PRODUCER'

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
    m=types.ModuleType('main_c19_'+Path(ref['path']).stem);m.__file__=ref['path'];sys.modules[m.__name__]=m
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
def choice():return decode((N/'source.choice.json').read_bytes())
def package_refs():
    h,m=pin(N/'HDF.json'),pin(N/'MF.json');obj,refs=pair(h,m)
    require(obj['actor_id']==AUTHOR and obj['status']=='SOURCE_READY_PENDING_INDEPENDENT_REVIEW','SOURCE_PACKAGE')
    return h,m,refs

def validate_authority(request_ref,c):
    q=decode(read_ref(request_ref));require(set(q)=={'schema','issued_by','scope_ref','canonical_vector_ref','calling_contract_ref'},'REQUEST_FIELDS')
    require(q['schema']=='researchos.root-w09-main-c19-native-request.v1' and q['issued_by']==ROOT_ACTOR,'ROOT_REQUEST')
    require(Path(request_ref['path']).is_relative_to(W),'ROOT_REQUEST_NAMESPACE')
    sr=q['scope_ref'];scope=decode(read_ref(sr));contract_ref=pin(N/'root-calling-contract.json')
    require(q['calling_contract_ref']==contract_ref,'CURRENT_CALLING_CONTRACT')
    contract=decode(read_ref(contract_ref));require(set(scope)==set(contract['scope_required_fields']),'SCOPE_FIELDS')
    require(scope['schema']=='researchos.root-w09-main-c19-native-scope.v1' and scope['status']=='ROOT_AUTHORIZED_SINGLE_MAIN_C19_PRODUCER'
            and scope['issued_by']==scope['executor']==ROOT_ACTOR,'ROOT_EXPLICIT_SCOPE')
    require(all(scope[k] is False for k in BOOL_FALSE) and all(type(scope[k]) is int and scope[k]==0 for k in ZERO),'SCOPE_BOUNDARY')
    require(type(scope['maximum_go_test_runs']) is int and scope['maximum_go_test_runs']==1
            and type(scope['maximum_go_list_runs']) is int and scope['maximum_go_list_runs']==1,'ONE_GO_LIST_ONE_TEST')
    href,mref,refs=package_refs()
    require(scope['source_handoff_ref']==href and scope['source_manifest_ref']==mref,'CURRENT_SOURCE_PAIR')
    bound={field:pin(N/name) for field,name in contract['source_file_bindings'].items()}
    require(all(scope[k]==v for k,v in bound.items()),'ALL_EXACT_CALLERS_AND_ADAPTER')
    for key in ('source_root','run_id','receipt_root','scratch_root','output_root','selected_tests','expected_native_ids'):
        require(scope[key]==c[key],'EXACT_SCOPE_'+key)
    require(scope['source21']==c['source21'] and scope['main_seven_after_refs']==c['main_seven_after_refs'],'CURRENT_MAIN_ROSTER')
    require(scope['list_timeout_seconds']==240 and type(scope['list_timeout_seconds']) is int
            and scope['producer_timeout_seconds']==420 and type(scope['producer_timeout_seconds']) is int
            and scope['inner_Go_timeout_seconds']==180 and type(scope['inner_Go_timeout_seconds']) is int,'FIXED_TIMEOUTS')
    review,rr=pair(scope['source_review_handoff_ref'],scope['source_review_manifest_ref'])
    dr=scope['source_review_decision_ref'];d=decode(read_ref(dr))
    require(dr in rr and review['source_decision_ref']==dr and review['actor_id']==d['actor_id'],'SOURCE_DECISION_MEMBER')
    require(d['schema']=='researchos.w09-main-c19-producer-independent-source-decision.v1'
            and d['decision']=='SOURCE_ACCEPTED_FOR_ROOT_SINGLE_MAIN_C19_PRODUCER'
            and d['actor_role']=='INDEPENDENT_NON_AUTHOR' and d['actor_id'] not in (AUTHOR,ROOT_ACTOR),'INDEPENDENT_SOURCE_DECISION')
    for key,want in dict(source_handoff_ref=href,source_manifest_ref=mref,calling_contract_ref=contract_ref,**bound).items():
        require(d[key]==want,'SOURCE_REVIEW_FULL_BINDING_'+key)
    require(d['run_id']==c['run_id'] and d['output_root']==c['output_root'] and d['source21']==c['source21']
            and d['actual_executed'] is False and type(d['formal_case_accepted_delta']) is int and d['formal_case_accepted_delta']==0,'SOURCE_REVIEW_BOUNDARY')
    ar=scope['adoption_outcome_ref'];require(ar['path']==c['future_adoption_outcome_path'],'EXACT_MAIN_ADOPTION_OUTCOME')
    adopted=decode(read_ref(ar))
    require(adopted['status']=='SOURCE_ADOPTED_PENDING_REAL_DISPATCH_AND_FORMAL_REVIEW' and adopted['final_matches_expected_commit_or_rollback'] is True
            and adopted['final_target_refs']==c['main_seven_after_refs'] and adopted['transaction']['status']=='SEVEN_SOURCE_TARGETS_COMMITTED','ACTUAL_MAIN_SEVEN_ADOPTED')
    for k in ('owned_cleanup','guard_cleanup'):
        require(adopted[k]['closed'] is True and not adopted[k]['errors'],'ACTUAL_ADOPTION_CLEANUP')
    require(adopted['formal_dispatcher'] is False and adopted['new_Go_SQL_API_model_calls']==0 and adopted['formal_case_accepted_delta']==0,'ADOPTION_NOT_NATIVE')
    ah,arefs=pair(scope['adoption_review_handoff_ref'],scope['adoption_review_manifest_ref'])
    adr=scope['adoption_review_decision_ref'];ad=decode(read_ref(adr))
    require(adr in arefs and ah['actual_decision_ref']==adr and ah['actor_id']==ad['actor_id'],'ADOPTION_REVIEW_MEMBER')
    require(ad['schema']=='researchos.w09-main-c19-independent-adoption-decision.v1'
            and ad['decision']=='ACTUAL_SEVEN_TARGET_ADOPTION_VERIFIED' and ad['actor_role']=='INDEPENDENT_NON_AUTHOR'
            and ad['actor_id'] not in (AUTHOR,ROOT_ACTOR),'INDEPENDENT_ACTUAL_ADOPTION')
    require(ad['adoption_outcome_ref']==ar and ad['source_handoff_ref']==c['adoption_source_handoff_ref']
            and ad['source_manifest_ref']==c['adoption_source_manifest_ref'] and ad['final_target_refs']==c['main_seven_after_refs']
            and ad['source21']==c['source21'] and ad['all_handles_closed'] is True
            and ad['formal_acceptance'] is False and type(ad['formal_case_accepted_delta']) is int and ad['formal_case_accepted_delta']==0,'ADOPTION_REVIEW_BINDING')
    vr=q['canonical_vector_ref'];vector=decode(read_ref(vr))
    require(set(vector)=={'schema','checkpoint_revision','ownership_revision','refs'}
            and vector['schema']=='researchos.w09-main-c19-native-canonical-vector.v1'
            and type(vector['checkpoint_revision']) is int and vector['checkpoint_revision']>367
            and type(vector['ownership_revision']) is int and vector['ownership_revision']>171,'NEW_POST_ADOPTION_VECTOR')
    require(len(vector['refs'])==4 and [r['path'] for r in vector['refs']]==[str(p) for p in CANON],'FOUR_ORDERED_CANONICAL')
    docs=[decode(read_ref(r)) for r in vector['refs']];cp,ow,ss,commands=docs
    require(cp['revision']==vector['checkpoint_revision'] and ow['revision']==vector['ownership_revision'],'CURRENT_VECTOR_REVISIONS')
    require(cp['project_id']=='aede0678-7308-43dc-b9f2-cfe3d90cfdfb' and cp['head']==c['expected_git_head'],'CURRENT_PROJECT_HEAD')
    require(vector['refs'][3]==c['main_seven_after_refs'][6],'ADOPTED_COMMANDS_VECTOR')
    require(ow['active_integrator']['id']==ROOT_ACTOR and ow['shared_integrator']=='qoder-desktop:/root/platform_owner'
            and ow['card_path_bindings']['W09-99']['owner']==ROOT_ACTOR,'ROOT_CURRENT_ROLE')
    owner=dict(owner=ROOT_ACTOR,current_source_writer=None,state='ROOT_REGISTERED_PENDING_MAIN_C19_NATIVE',scope_ref=sr,
        source_handoff_ref=href,source_manifest_ref=mref,source_review_handoff_ref=scope['source_review_handoff_ref'],
        source_review_manifest_ref=scope['source_review_manifest_ref'],adoption_outcome_ref=ar,
        adoption_review_handoff_ref=scope['adoption_review_handoff_ref'],source_root=str(R),run_id=c['run_id'],
        receipt_root=c['receipt_root'],scratch_root=c['scratch_root'],output_root=c['output_root'],formal_case_accepted_delta=0,parent_acceptance=False)
    require(ow['card_path_bindings']['W09-99']['subtasks'][OWNER_KEY]==owner,'EXACT_REGISTERED_NATIVE_OWNER')
    worker=dict(step_id='W09-99',slice_id=SLICE,owner=ROOT_ACTOR,state=owner['state'],scope_ref=sr,
        source_handoff_ref=href,source_review_handoff_ref=scope['source_review_handoff_ref'],adoption_outcome_ref=ar,run_id=c['run_id'])
    require([v for v in cp['workers'] if v.get('slice_id')==SLICE]==[worker],'EXACT_UNIQUE_NATIVE_WORKER')
    for ref in c['main_seven_after_refs']+c['source21']:read_ref(ref)
    require(c['source_root']==str(R) and re.fullmatch('[0-9a-f]{32}',c['run_id']),'MAIN_FIXED_RUN')
    require(c['output_root']==str(R/'execution/receipts/W09/retrieval'/('run-'+c['run_id']))
            and c['receipt_root']==str(N/'actual-main-root')
            and c['scratch_root']==str(R/'.local'/('w09-c19-main-'+c['run_id'])),'FIXED_PRIVATE_PATHS')
    return unique(refs+rr+arefs+[request_ref,sr,contract_ref,dr,ar,adr,vr,*vector['refs'],*bound.values()]),scope,vector

def build_environment(c):
    scratch=Path(c['scratch_root']);go=Path(c['tool_refs']['go']['path']);git=Path(c['tool_refs']['git']['path'])
    return {'SystemRoot':'C:/Windows','WINDIR':'C:/Windows','ComSpec':'C:/Windows/System32/cmd.exe',
        'PATH':str(go.parent)+';'+str(git.parent)+';C:/Windows/System32','PATHEXT':'.COM;.EXE;.BAT;.CMD',
        'USERPROFILE':str(scratch/'profile'),'LOCALAPPDATA':str(scratch/'profile'),'APPDATA':str(scratch/'profile'),
        'TEMP':str(scratch/'temp'),'TMP':str(scratch/'temp'),'GOROOT':str(go.parent.parent),'GOPATH':str(R/'.local/gopath'),
        'GOCACHE':str(scratch/'gocache'),'GOENV':'off','GOTOOLCHAIN':'local','GOPROXY':'off','GOSUMDB':'off','GOWORK':'off',
        'CGO_ENABLED':'0','GOFLAGS':'-mod=readonly -p=1','GOMAXPROCS':'2','RESEARCHOS_GO':str(go),
        'RESEARCHOS_TASK_ID':'W09','RESEARCHOS_CHECK_ID':'','RESEARCHOS_CASE_ID':'C19','RESEARCHOS_RETRIEVAL_MODE':'fixture',
        'GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'NUL','GIT_TERMINAL_PROMPT':'0','GIT_OPTIONAL_LOCKS':'0'}

def read_inputs(c):
    bp=decode(read_ref(c['compiler_blueprint_ref']))
    refs=[pin(N/'source.choice.json'),c['compiler_blueprint_ref'],c['guard_ref'],c['owned_job_ref'],c['toolchain_ref'],
        c['identity_ref'],c['spec_manifest_ref'],*c['tool_refs'].values(),*c['source21'],*bp['stable_input_refs']]
    require(bp['package_count']==351 and len(bp['package_roster'])==351,'351_EXPECTED_PACKAGES')
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
    c=result.get('job_cleanup',{})
    return not c.get('errors') and c.get('active_processes_last_observed')==0 and all(c.get(k) is True for k in
        ('unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed'))

def invoke(helper,root,label,argv,env,wall):
    out=root/(label+'.stdout.raw');err=root/(label+'.stderr.raw');result=None;error=None
    try:
        with out.open('xb') as stdout,err.open('xb') as stderr:
            result=helper.run_owned(argv,str(R),env,stdout,stderr,wall,creation_flags=0x08000000)
    except BaseException as exc:error=repr(exc)
    finally:
        # Python integers retain every FILETIME bit. Progress only exposes its decimal string.
        creation=result.get('creation_time_100ns') if result else None
        record=dict(argv=argv,cwd=str(R),public_environment=env,timeout_seconds=wall,result=result,exception=error,
            actual_outer_exit=result.get('actual_exit') if result else None,individual_child_numeric_exit=None,
            creation_time_100ns_decimal=str(creation) if type(creation) is int else None,
            stdout_ref=pin(out) if out.is_file() else None,stderr_ref=pin(err) if err.is_file() else None,
            external_model_provider_requests=0,paid_provider_requests=0,production_DB_writes=0)
        receipt=save(root,label+'.invocation.json',record)
        print(json.dumps(dict(progress=label,receipt_ref=receipt,actual_outer_exit=record['actual_outer_exit'],
            creation_time_100ns_decimal=record['creation_time_100ns_decimal'])),flush=True)
    require(error is None and job_closed(result),'OWNED_JOB_UNCLOSED_OR_EXCEPTION')
    require(result['error'] is None and result['actual_exit']==0 and result['timed_out'] is False,'FIRST_NATIVE_FAILURE_STOP')
    return receipt,result

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
    require(len(packages)==351 and sorted(packages)==sorted(bp['package_roster']),'EXACT_ACTUAL_351_PACKAGE_ROSTER')
    require(gomods=={x['path']:x for x in bp['module_go_mod_refs']},'EXACT_MODULE_GOMOD_SET')
    require(exports and generated,'ACTUAL_EXPORT_AND_GENERATED_INPUTS_REQUIRED')
    return dict(schema='researchos.w09-main-c19-actual-compiler-input-inventory.v1',package_count=351,packages=packages,
        stable_build_input_refs=list(stable.values()),private_generated_input_refs=list(generated.values()),private_export_refs=list(exports.values()),
        module_go_mod_refs=list(gomods.values()),actual_embed_files=embeds,blueprint_ref=c['compiler_blueprint_ref'],
        source_root=str(R),private_GOCACHE=str(cache),actual_go_list_export=True,source21=c['source21'],formal_acceptance=False)

def validate_packet(c,packet):
    report_path=packet/'report.json';tool_path=packet/'native-tool-run.json'
    report=decode(report_path.read_bytes());tool=decode(tool_path.read_bytes())
    require(packet==Path(c['output_root']) and report['run_id']==c['run_id']==tool['run_id'],'FIXED_MAIN_NATIVE_RUN')
    require(report['version_manifest']['git_head']==c['expected_git_head'],'ACTUAL_HEAD')
    require(report['version_manifest']['source_sha256']=={str(Path(ref['path']).relative_to(R)).replace('\\','/'):'sha256:'+ref['sha256'] for ref in c['source21']},'EXACT_ACTUAL_SOURCE21')
    relative=report_path.relative_to(R).as_posix();source=dict(report);source['report_reference']=relative
    require(tool['report_ref']==relative and tool['report_sha256']==pin(report_path)['sha256'],'TOOL_SAME_REPORT')
    require(tool['schema']=='researchos.w09-native-producer-tool-run.v1' and tool['formal_acceptance']=='NOT_RUN','EXACT_TOOL_RUN_SCHEMA')
    expected_argv=[c['tool_refs']['go']['path'],'test','-count=1','-json','-run','^(?:'+'|'.join(c['selected_tests'])+')$','./internal/domain']
    require(report['actual_invocation']==tool['actual_invocation']==expected_argv,'EXACT_MAIN_NATIVE_ARGV')
    require(report['task_id']=='W09' and report['check_id'] is None and report['case_id']=='C19'
            and report['scope']=='FIXTURE_IMPLEMENTED_SERVICE','EXACT_C19_REPORT_ROUTE')
    require(tool['stdout_ref']==report['raw_evidence_references'][0] and tool['stderr_ref']==report['raw_evidence_references'][1]
            and tool['stdout_sha256']==pin(packet/'go-test.stdout.jsonl')['sha256']
            and tool['stderr_sha256']==pin(packet/'go-test.stderr.txt')['sha256'],'TOOL_EXACT_ORIGINAL_STREAMS')
    require(tool['native_exit_code']==0 and report['exit_code']==0 and report['timed_out'] is False and report['status']=='PASS','NATIVE_REPORT_PASS')
    require(report['formal_construction_acceptance']=='NOT_RUN_POSTRUN_REVIEW_PENDING' and report['formal_case_accepted_delta']==0,'NATIVE_NOT_FORMAL')
    require(report['selected_tests']==c['selected_tests'] and sorted(report['assertion_ids'])==c['expected_native_ids'],'EXACT_TWO_TESTS_FIVE_ASSERTIONS')
    closure=module(next(ref for ref in c['source21'] if ref['path']==str(R/'ops/ci/w09_evidence_closure.py')))
    native=closure.verify_native(R,source,report,c['expected_native_ids'],c['selected_tests'])
    owner={aid:('TestW09C19ChainInvalidation' if aid=='C19-05' else 'TestW09C19ExplicitOriginAndUnknown') for aid in c['expected_native_ids']}
    owned=closure.verify_owned(R,source,report,c['selected_tests'],owner);closure.verify_c19(owned)
    require(all(Path(rec['owned_export_ref']['path']).is_relative_to(packet/'owned') for rec in report['assertion_results']),'MAIN_ABSOLUTE_ASSERTION_PINS')
    return dict(report_ref=pin(report_path),tool_run_ref=pin(tool_path),run_id=c['run_id'],source_root=str(R),
        native_ids=c['expected_native_ids'],native_test_exit=report['exit_code'],owned_members=len(owned['members']),
        mode_independent_review='NOT_RUN_REQUIRED',formal_acceptance=False)

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
    return save(root,'native-packet.public-index.json',dict(schema='researchos.w09-main-c19-native-packet.v1',
        run_id=c['run_id'],consumer_source_root=str(R),original_report_ref=pin(packet/'report.json') if (packet/'report.json').is_file() else None,
        original_tool_run_ref=pin(packet/'native-tool-run.json') if (packet/'native-tool-run.json').is_file() else None,
        raw_copy_mapping=mapping,immutable_original_bytes=True,formal_acceptance=False))

def stage(kind,args):
    require(kind in ('prepare','run') and len(args)==3,'THREE_EXACT_ROOT_REQUEST_ARGUMENTS')
    request_ref=dict(path=args[0],sha256=args[1],bytes=int(args[2]));c=choice()
    auth_refs,scope,vector=validate_authority(request_ref,c)
    gm=module(c['guard_ref']);helper=module(c['owned_job_ref'])
    input_refs,bp=read_inputs(c)
    input_refs=unique(auth_refs+input_refs)
    guards=[];cleanups=[];receipts=[];error=None;success=False;created=False;summary=None;packet_ref=None;archive_error=None
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
            summary=dict(schema='researchos.w09-main-c19-preparation-ready.v1',request_ref=request_ref,canonical_vector=vector,
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
            receipt,_=invoke(helper,stage_root,'compiler-input-list',list_argv,env,c['list_timeout_seconds']);receipts.append(receipt)
            inv=compiler_inventory((stage_root/'compiler-input-list.stdout.raw').read_text(encoding='utf-8'),c,bp)
            inventory_ref=save(stage_root,'actual-compiler-input-inventory.json',inv)
            acquire('compiler-exports',[inventory_ref,*inv['private_generated_input_refs'],*inv['private_export_refs'],*inv['module_go_mod_refs']])
            permit=save(stage_root,'launcher.permit.json',dict(schema='researchos.w09-main-c19-launcher-permit.v1',request_ref=request_ref,
                run_id=c['run_id'],output_root=c['output_root'],launcher_ref=pin(N/'main_c19_launcher.source.py'),
                runner_ref=next(ref for ref in c['source21'] if ref['path']==str(R/'ops/ci/retrieval.py')),environment=env))
            acquire('launcher-permit',[permit])
            argv=[c['tool_refs']['python']['path'],'-I','-S','-B','-X','utf8',str(N/'main_c19_launcher.source.py'),permit['path'],permit['sha256'],str(permit['bytes'])]
            receipt,_=invoke(helper,stage_root,'w09-c19-main-producer',argv,env,c['producer_timeout_seconds']);receipts.append(receipt)
            # Bind the emitted exact run, never select a latest directory or glob.
            emitted=decode((stage_root/'w09-c19-main-producer.stdout.raw').read_bytes())
            require(emitted['report_reference']==(output/'report.json').relative_to(R).as_posix()
                    and emitted['tool_run_reference']==(output/'native-tool-run.json').relative_to(R).as_posix(),'EXACT_PRODUCER_STDOUT_REFS')
            summary=validate_packet(c,output);summary.update(compiler_inventory_ref=inventory_ref,launcher_permit_ref=permit,prepare_ready_ref=ready_ref)
        for ref in input_refs:read_ref(ref)
        success=True
    except BaseException as exc:error=repr(exc)
    finally:
        if created and kind=='run':
            receipts=[pin(stage_root/(label+'.invocation.json')) for label in ('compiler-input-list','w09-c19-main-producer')
                      if (stage_root/(label+'.invocation.json')).is_file()]
            producer=stage_root/'w09-c19-main-producer.invocation.json'
            if producer.is_file() and output.is_dir() and job_closed(decode(producer.read_bytes()).get('result')):
                try:packet_ref=capture_packet(c,stage_root)
                except BaseException as exc:archive_error=repr(exc);success=False
        # Each independent guard is attempted even if a previous close fails.
        for label,guard in reversed(guards):
            try:
                cleanup=guard.close();ref=save(stage_root,label+'-guard.cleanup.actual.json',cleanup) if created else None
                cleanups.append(dict(label=label,ref=ref,closed=guard_cleanup_ok(cleanup),observation=cleanup if ref is None else None))
            except BaseException as exc:cleanups.append(dict(label=label,ref=None,closed=False,error=repr(exc)))
    all_closed=all(row['closed'] for row in cleanups)
    all_jobs_closed=all(job_closed(decode(read_ref(ref)).get('result')) for ref in receipts)
    if kind=='run' and success:success=packet_ref is not None and len(receipts)==2 and all_jobs_closed
    if created:
        result=dict(schema='researchos.w09-main-c19-stage-closed.v1',stage=kind,
            status=('PREPARED_ALL_GUARDS_CLOSED' if kind=='prepare' else 'MAIN_C19_NATIVE_PACKET_CLOSED_PENDING_INDEPENDENT_REVIEW') if success and all_closed else 'FAILED_NO_AUTOMATIC_RETRY',
            error=error,archive_error=archive_error,summary=summary,native_packet_ref=packet_ref,request_ref=request_ref,invocation_refs=receipts,guard_cleanups=cleanups,
            all_guards_closed=all_closed,actual_formal_consumers=False,formal_case_accepted_delta=0,
            all_owned_jobs_closed=all_jobs_closed,individual_unobserved_native_exits=None,
            external_model_provider_requests=0,paid_provider_requests=0,Main_source_written=False,Canon_written=False,
            process_loss_requires_explicit_Root_reconciliation=True,automatic_retry=False)
        if success and all_closed and kind=='prepare':
            result.update(summary);result['guard_cleanup_refs']=[row['ref'] for row in cleanups];save(actual,'prepare.ready.json',result)
        else:save(stage_root,'validation.closed.json',result)
        print(json.dumps(dict(status=result['status'],stage=kind,receipt_root=str(stage_root),error=error)),flush=True)
    require(success and all_closed,'STAGE_FAILED_OR_GUARD_CLEANUP_UNCONFIRMED')

def scope_path(request_ref):return decode(read_ref(request_ref))['canonical_vector_ref']['path']
