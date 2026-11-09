import ast,hashlib,json,ntpath,os,platform,re,sys,traceback,types
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W09/W09-99';Q=Path(__file__).resolve().parent
P=B/'full_w09_main_native_producer_source_codex/fullw09-20261010-06'
OLD=B/'full_w09_nf5_actual_independent_review_codex/review-actual-nf5-20261010-01/review_actual_nf5.v7.py'
GUARD=R/'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
ACTOR='codex:/root/backup_regression_resources';ROOT='codex:/root';TEMP=Path('C:/Users/yqyyds/.researchos/w09-native-v5')

def pin(p):
    raw=Path(p).read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(p,v):
    with p.open('xb')as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    return pin(p)
def norm(p):return ntpath.normcase(ntpath.normpath(str(p)))
def require(ok,code):
    if not ok:raise ValueError(code)
def reused_module():
    raw=OLD.read_bytes();tree=ast.parse(raw)
    names={'require','digest','decode','ref_shape','key','same_ref','read_ref','pin','uint','job','guard_receipt','load_module','clock','event_interval','nested_documents','has_ref','root_pair','root_capture','packet_artifacts','reviewed_runtime_closure','reviewed_launcher_tail','collect_actual_refs','review_group'}
    nodes=[]
    for node in tree.body:
        if isinstance(node,(ast.Import,ast.ImportFrom)) or isinstance(node,ast.ClassDef) and node.name=='API':nodes.append(node)
        elif isinstance(node,ast.FunctionDef) and node.name in names:
            if node.name=='review_group':
                text=ast.get_source_segment(raw.decode('utf-8'),node)
                old="scope['generation']=='fullw09-20261010-05'";new="scope['generation']==c['generation']"
                require(text.count(old)==1,'ONE_REVIEWER_GENERATION_REPLACEMENT')
                node=ast.parse(text.replace(old,new)).body[0]
            nodes.append(node)
    m=types.ModuleType('nf6_partial_reused_readonly');m.__file__=str(OLD)
    m.__dict__.update(R=R,Q=Q,ACTOR=ACTOR,ROOT_ACTOR=ROOT,ROOT_THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98',TEMP_PARENT=TEMP,BASE=P)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(OLD)+'#read-only-helper-extraction','exec'),m.__dict__)
    return m

def bound_pair(m,initial_ref,completed_ref,artifact_ref=None):
    first=m.root_pair(initial_ref);last=m.root_capture(completed_ref,artifact_ref) if artifact_ref is not None else m.root_pair(completed_ref)
    a,b=first['actual_host_result'],last['actual_host_result'];session=a.get('session_id')
    require(type(session)is int and session>0 and a.get('exit_code') is None,'TRUE_INITIAL_YIELDED_SESSION')
    sessions=[int(x)for x in re.findall(r'tools\.write_stdin\(\{session_id\s*:\s*([0-9]+)',last['call_payload'].get('input',''))]
    require(session in sessions and first['output_ordinal']<last['call_ordinal'],'EXACT_ORIGINAL_SESSION_TO_COMPLETION')
    require(type(b.get('exit_code'))is int and b['exit_code']==0 and 'ROOT_ACTUAL_PYTHON_EXIT=0'in b['output'].splitlines(),'TRUE_COMPLETED_ROOT_EXIT_AND_MARKER')
    return first,last
def root_prepare(m,initial_ref,completed_ref,ready,c,request_ref):
    a,b=bound_pair(m,initial_ref,completed_ref)
    text=a['call_payload'].get('input','')
    require("load('NF6_finalized_native')"in text and "['W09-G01','W09-G02']"in text and 'f.future_argv[k].prepare.map(q)'in text and 'tools.exec_command('in text,'EXACT_OBSERVED_NF6_PREPARE_DISPATCH')
    progress=[x for x in m.nested_documents(b['actual_host_result']['output'])if type(x)is dict and x.get('stage')=='prepare']
    require(len(progress)==1 and progress[0]['status']==ready['status']=='PREPARED_ALL_GUARDS_CLOSED'and norm(progress[0]['receipt_root'])==norm(c['receipt_root'])and progress[0]['error']is None and progress[0]['cleanup_errors']==[] and progress[0]['all_guards_closed']is True and progress[0]['all_owned_jobs_closed']is True and progress[0]['unsaved_stage_result']is None,'ACTUAL_PREPARE_PUBLICATION_FOR_BOUND_HOST')
    return [a,b]
def root_run(m,initial_ref,completed_ref,invocation_ref,c,request_ref):
    a,b=bound_pair(m,initial_ref,completed_ref,invocation_ref)
    text=a['call_payload'].get('input','')
    require("load('NF6_finalized_native')"in text and "['W09-G01','W09-G02']"in text and 'f.future_argv[k].run.map(q)'in text and 'tools.exec_command('in text,'EXACT_OBSERVED_NF6_RUN_DISPATCH')
    return [a,b]
def mode_facts(m,closure,ctx,report,c,native):
    facts=dict(required_mode=c['mode'],producer_id=ROOT,independent_fact_reviewer='/root/backup_regression_resources',run_id=c['run_id'],source_sha256=native['source_hashes'],go_executable=native['go'],final_mode_decision_issued=False)
    if c['mode']=='FIXTURE':
        http=ctx['events'].get('http-exchange',[])
        require(http and all(x['value'].get('delivery')=='IN_PROCESS_HTTptest_RECORDER'for x in http),'ACTUAL_FIXTURE_HTTP_RECORDER')
        states=[x for label,group in ctx['events'].items()if label.startswith('state-')for x in group]
        require(any(Path(x['value'].get('root_path','')).is_relative_to(TEMP)for x in states),'ACTUAL_FIXTURE_OWNED_CONTROLLED_TEMP')
        facts.update(input_origin='OWNED_TEMP_DIR',actual_http_delivery='IN_PROCESS_HTTptest_RECORDER',state_event_refs=[x['pin']for x in states])
    else:
        require(os.name=='nt' and platform.system()=='Windows' and platform.machine().casefold()in('amd64','x86_64') and sys.getwindowsversion().build>=22000,'WINDOWS11_X64_ACTUAL_REVIEW_HOST')
        branch=closure.only(ctx['events'],'g02-os-branch','TestW09RootReplacementCannotFeedProduct')
        command=closure.only(ctx['events'],'g02-junction-command','TestW09RootReplacementCannotFeedProduct')
        require(branch['goos']=='windows' and branch['goarch']=='amd64' and branch['junction_branch']is True,'ACTUAL_GO_WINDOWS_JUNCTION_BRANCH')
        root,target=Path(command['root_path']),Path(command['target_path'])
        require(root.is_absolute() and target.is_absolute() and root!=target and type(command['exit_code'])is int and command['exit_code']==0 and command['command']==['cmd.exe','/c','mklink','/J',str(root),str(target)],'ACTUAL_MKLINK_J_COMMAND_EXIT')
        output=closure._raw_pin(command['output'],ctx['members'],'TestW09RootReplacementCannotFeedProduct')
        facts.update(actual_platform='Windows 11 x64',run_os=report['version_manifest']['os'],run_os_release=report['version_manifest']['os_release'],go_branch_actual=branch,junction_actual=command,junction_output_sha256=hashlib.sha256(output).hexdigest(),junction_event_ref=ctx['events']['g02-junction-command'][0]['pin'],host_event_ref=ctx['events']['g02-os-branch'][0]['pin'])
    return facts
def main():
    packet=json.loads((Q/'partial-input-observed.json').read_bytes());choices=json.loads((P/'source.choice.json').read_bytes())
    require(set(packet['groups'])=={'W09-G01','W09-G02'},'EXACT_TWO_ALREADY_CLOSED_GROUPS')
    m=reused_module()
    m.root_prepare_pair=lambda *args:root_prepare(m,*args)
    m.root_run_pair=lambda *args:root_run(m,*args)
    m.mode_facts=lambda *args:mode_facts(m,*args)
    choice={key:{**choices['common'],**choices['selectors'][key]}for key in packet['groups']}
    bp=m.decode(m.read_ref(choice['W09-G01']['compiler_blueprint_ref']))
    refs=m.collect_actual_refs(packet,choice)
    source_refs=[pin(OLD),pin(P/'source.choice.json'),choice['W09-G01']['compiler_blueprint_ref'],pin(R/'ops/ci/w09_evidence_closure.py'),pin(R/'execution/v2.4/formal_profile_w09.py'),pin(Q/'partial-input-observed.json')]
    unique={}
    for ref in [*refs,*source_refs]:
        path=m.ref_shape(ref);absolute=dict(ref,path=str(path));key=norm(path)
        if key in unique:require((unique[key]['sha256'],unique[key]['bytes'])==(ref['sha256'],ref['bytes']),'NO_CONFLICTING_ACTUAL_RESOURCE_PINS')
        unique[key]=absolute
    guard_bytes=GUARD.read_bytes();require(hashlib.sha256(guard_bytes).hexdigest()=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85','PINNED_SOURCE_GUARD')
    gm=types.ModuleType('nf6_partial_actual_guard');gm.__file__=str(GUARD);exec(compile(guard_bytes,str(GUARD),'exec'),gm.__dict__)
    guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=512*1024*1024)
    result=dict(schema='researchos.w09-nf6-two-actual-independent-prefix.v1',actor_id=ACTOR,backend_actor='/root/backup_regression_resources',source_author='codex:/root/full_w09_source_review',executor=ROOT,groups={},pending_groups=['A06','C19'],overall_qualified=False,Mode_issued=False,formal_acceptance=False,formal_case_accepted_delta=0,new_Native_runs=0,new_Go_runs=0,new_model_requests=0,Canon_written=False,Main_written=False,current_Canon_not_read=True,actual_canonical_ledger_archive_join_pending=True,prior_passed_Source_compiler_checks_replayed=False)
    primary=None
    try:
        guard.acquire(list(unique.values()))
        m.read_ref=lambda ref:guard.get_buffer(str(m.ref_shape(ref)))
        closure=m.load_module(m.read_ref(pin(R/'ops/ci/w09_evidence_closure.py')),R/'ops/ci/w09_evidence_closure.py')
        profile_raw=m.read_ref(pin(R/'execution/v2.4/formal_profile_w09.py'))
        for key in ('W09-G01','W09-G02'):
            facts=m.review_group(packet['groups'][key],choice[key],closure,profile_raw,bp)
            result['groups'][key]=facts
            save(Q/('partial-'+key+'.facts.json'),facts)
        result['partial_status']='TWO_GROUPS_ACTUAL_FACTS_REVIEWED_PENDING_REMAINDER'
    except BaseException as exc:
        primary=dict(type=type(exc).__name__,message=str(exc));traceback.print_exc()
    finally:
        close=guard.close();close_ref=save(Q/'partial-actual-SourceGuard.closed.json',close)
        result.update(primary_error=primary,guard_cleanup_ref=close_ref,all_review_guards_closed=close['closed'],retained_handles_count=close['retained_handles_count'],held_actual_resource_count=len(close['entries']))
        result_ref=save(Q/'partial-actual-review-result.json',result)
        print(json.dumps(dict(result_ref=result_ref,guard_cleanup_ref=close_ref,completed_group_keys=list(result['groups']),primary_error=primary,all_guards_closed=close['closed'],retained_handles_count=close['retained_handles_count'],held_resources=len(close['entries']),Mode_issued=False,overall_qualified=False),ensure_ascii=False))
    return 0 if primary is None and close['closed'] and close['errors']==[] and close['retained_handles_count']==0 else 1
if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
