import ast,datetime,hashlib,json,ntpath,sys,traceback,types
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W09/W09-99';Q=Path(__file__).resolve().parent
P=B/'full_w09_main_native_producer_source_codex/fullw09-20261010-06';S=B/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
GUARD=R/'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
ROOT='codex:/root';ACTOR='codex:/root/backup_regression_resources'
INPUT={'path':str(S/'nf6-four-closed-actual-input.root.json'),'sha256':'7233219f2478fab5a30533c0be3f8a8db987fd3b144eb1f8481657b09a2236bf','bytes':9401}
PROGRESS={'path':str(S/'nf6-four-progress-actual-input.root.json'),'sha256':'18b288a60b890aa46542dc7d6294dd68e04fa0175fa65d95fb5aab5a15e2d569','bytes':3042}
def need(ok,code):
    if not ok:raise ValueError(code)
def pin(path):
    raw=Path(path).read_bytes();return dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,doc):
    raw=(json.dumps(doc,ensure_ascii=False,indent=2,default=lambda x:x.isoformat()if isinstance(x,datetime.datetime)else str(x))+'\n').encode('utf-8');path=Q/name
    with path.open('xb')as out:out.write(raw)
    return pin(path)
def definitions(path):
    tree=ast.parse(path.read_bytes());module=types.ModuleType('nf6_remaining_support');module.__file__=str(path)
    nodes=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom,ast.Assign,ast.FunctionDef))]
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path)+'#definitions-only','exec'),module.__dict__)
    return module
def fixed(m,ref):
    raw=Path(ref['path']).read_bytes();need(hashlib.sha256(raw).hexdigest()==ref['sha256']and len(raw)==ref['bytes'],'ROOT_FIXED_INPUT_PIN');return m.decode(raw)
def initial_source(pair,c,phase):
    text=pair['call_payload'].get('input','');wave="['W09-G01','W09-G02']"if c['selector_key'].startswith('W09-')else"['A06','C19']"
    need("load('NF6_finalized_native')"in text and wave in text and 'f.future_argv[k].'+phase+'.map(q)'in text and 'tools.exec_command('in text,'EXACT_ORIGINAL_NF6_'+phase.upper()+'_DISPATCH')
def root_prepare(lib,m,first_ref,last_ref,ready,c,request_ref):
    first,last=lib.bound_pair(m,first_ref,last_ref);initial_source(first,c,'prepare')
    docs=[m.decode(line)for line in last['actual_host_result']['output'].splitlines()if line.lstrip().startswith('{')]
    docs=[v for v in docs if type(v)is dict and v.get('stage')=='prepare']
    need(len(docs)==1 and docs[0]['status']==ready['status']=='PREPARED_ALL_GUARDS_CLOSED'and lib.norm(docs[0]['receipt_root'])==lib.norm(c['receipt_root'])and docs[0]['error']is None and docs[0]['cleanup_errors']==[]and docs[0]['all_guards_closed']is True and docs[0]['all_owned_jobs_closed']is True and docs[0]['unsaved_stage_result']is None,'EXACT_PREPARE_COMPLETED_PUBLICATION')
    return [first,last]
def root_run(lib,m,row,c,closed,progress):
    first,last=lib.bound_pair(m,row['run_initial_Root_capture_ref'],row['run_completed_Root_capture_ref']);initial_source(first,c,'run')
    session=first['actual_host_result']['session_id'];wanted={x['label']:x['ref']for x in closed['invocation_observations']};pairs=[]
    for label,field in [('compiler-input-list','compiler_progress_ref'),('w09-selector-main-producer','producer_progress_ref')]:
        pair=m.root_capture(progress[c['selector_key']][field],wanted[label]);host=pair['actual_host_result']
        need(host.get('session_id')==session and host.get('exit_code')is None and first['output_ordinal']<pair['call_ordinal']<pair['output_ordinal']<last['call_ordinal'],'TRUE_YIELDED_PROGRESS_SESSION_ORDER')
        docs=[m.decode(line)for line in host['output'].splitlines()if line.strip()]
        docs=[doc for doc in docs if type(doc)is dict and doc.get('progress')==label and m.same_ref(doc.get('receipt_ref'),wanted[label])]
        need(len(docs)==1 and type(docs[0]['actual_outer_exit'])is int and docs[0]['actual_outer_exit']==0 and docs[0]['original_error']is None and docs[0]['evidence_errors']==[]and docs[0]['unsaved_invocation']is None,'EXACT_SINGLE_INNER_INVOCATION_PUBLICATION')
        invocation=m.decode(m.read_ref(wanted[label]));ft=invocation['result']['creation_time_100ns']
        need(type(ft)is int and 0<ft<2**64 and docs[0]['creation_time_100ns_decimal']==invocation['creation_time_100ns_decimal']==str(ft),'EXACT_ROOT_PROGRESS_UINT64_FILETIME')
        pairs.append(pair)
    docs=[m.decode(line)for line in last['actual_host_result']['output'].splitlines()if line.lstrip().startswith('{')]
    docs=[v for v in docs if type(v)is dict and v.get('stage')=='run']
    need(len(docs)==1 and docs[0]['status']==closed['status']and lib.norm(docs[0]['receipt_root'])==lib.norm(Path(c['receipt_root'])/'producer')and docs[0]['error']is None and docs[0]['cleanup_errors']==[]and docs[0]['all_guards_closed']is True and docs[0]['all_owned_jobs_closed']is True and docs[0]['unsaved_stage_result']is None,'EXACT_COMPLETED_ROOT_RUN_PUBLICATION')
    return [first,*pairs,last]
def g01_reused_pending(lib,m,row,c,progress):
    closed=m.decode(m.read_ref(row['producer_closed_ref']));summary=closed['summary'];report=m.decode(m.read_ref(summary['report_ref']))
    # These predicates executed successfully before original1196's progress count gate.
    # Derive the publication values; do not execute their successful checks again.
    state_refs=[]
    for ref in report['owned_export']['members']:
        if Path(ref['path']).name.split('-',1)[1][:-4].startswith('state-'):state_refs.append(ref)
    mode={'required_mode':'FIXTURE','producer_id':ROOT,'independent_fact_reviewer':'/root/backup_regression_resources','run_id':c['run_id'],'source_sha256':report['version_manifest']['source_sha256'],'go_executable':report['go_executable'],'input_origin':'OWNED_TEMP_DIR','actual_http_delivery':'IN_PROCESS_HTTptest_RECORDER','state_event_refs':state_refs,'final_mode_decision_issued':False,'predicate_verified_by_original1196_successful_prefix_ref':pin(Q/'G01.original1196-successful-delta-prefix.json')}
    pairs=root_run(lib,m,row,c,closed,progress)
    return {'selector':c['selector_key'],'run_id':c['run_id'],'report_ref':summary['report_ref'],'tool_run_ref':summary['tool_run_ref'],'selected_tests':c['selected_tests'],'assertions':c['expected_native_ids'],'actual_native_exit':0,'prior_successful_prefix_ref':pin(Q/'G01.original1192-successful-prefix.json'),'prior_successful_delta_prefix_ref':pin(Q/'G01.original1196-successful-delta-prefix.json'),'prior_1931_guard_ref':pin(Q/'partial-actual-SourceGuard.closed.json'),'prior_successful_predicates_replayed':False,'Root_run_pairs':pairs,'mode_predicate_facts':mode,'launcher_started_ref':pin(Path(c['receipt_root'])/'producer/launcher.started.json'),'launcher_closed_ref':pin(Path(c['receipt_root'])/'producer/launcher.closed.json'),'launcher_predicates_verified_by_original1196':True,'formal_acceptance':False,'formal_case_accepted_delta':0}
def main():
    delta=definitions(Q/'review_partial_delta.py');lib=delta.support();m=lib.reused_module()
    packet=fixed(m,INPUT);progress=fixed(m,PROGRESS)
    need(set(packet)=={'schema','source_review_ref','groups'}and packet['schema']=='researchos.w09-nf6-four-actual-review-input.v1'and set(packet['groups'])=={'W09-G01','W09-G02','A06','C19'},'EXACT_COMPLETE_FOUR_INPUT')
    need(progress['schema']=='researchos.w09-nf6-genuine-progress-host-pairs.v1'and set(progress['groups'])==set(packet['groups']),'EXACT_FOUR_REAL_PROGRESS_INPUT')
    src=m.decode((P/'source.choice.json').read_bytes());choices={k:{**src['common'],**src['selectors'][k]}for k in packet['groups']};bp=m.decode(m.read_ref(choices['W09-G02']['compiler_blueprint_ref']))
    fresh={'groups':{k:packet['groups'][k]for k in ('W09-G02','A06','C19')}}
    refs=m.collect_actual_refs(fresh,choices);g1=packet['groups']['W09-G01'];closed=m.decode(m.read_ref(g1['producer_closed_ref']))
    refs += [INPUT,PROGRESS,packet['source_review_ref'],g1['producer_closed_ref'],closed['summary']['report_ref'],g1['run_initial_Root_capture_ref'],g1['run_completed_Root_capture_ref'],pin(Q/'G01.original1192-successful-prefix.json'),pin(Q/'G01.original1196-successful-delta-prefix.json'),pin(Q/'partial-actual-SourceGuard.closed.json'),pin(Q/'partial-delta-SourceGuard.closed.json')]
    refs += [x['ref']for x in closed['invocation_observations']]
    for key,rows in progress['groups'].items():
        need(set(rows)=={'compiler_progress_ref','producer_progress_ref'},'EXACT_TWO_EXISTING_PROGRESS_REFS')
        for ref in rows.values():refs.extend([ref,m.decode(m.read_ref(ref))['original_capture_ref']])
    for ref in (g1['run_initial_Root_capture_ref'],g1['run_completed_Root_capture_ref']):refs.append(m.decode(m.read_ref(ref))['original_capture_ref'])
    refs += [pin(R/'ops/ci/w09_evidence_closure.py'),pin(R/'execution/v2.4/formal_profile_w09.py'),pin(P/'source.choice.json'),choices['W09-G02']['compiler_blueprint_ref']]
    unique={}
    for ref in refs:
        path=m.ref_shape(ref);key=ntpath.normcase(ntpath.normpath(str(path)))
        if key in unique:need(unique[key]['sha256']==ref['sha256']and unique[key]['bytes']==ref['bytes'],'UNAMBIGUOUS_ACTUAL_REF')
        unique[key]=dict(ref,path=str(path))
    raw=GUARD.read_bytes();need(hashlib.sha256(raw).hexdigest()=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85','GUARD_FIXED_RESOURCE')
    gm=types.ModuleType('nf6_remaining_guard');gm.__file__=str(GUARD);exec(compile(raw,str(GUARD),'exec'),gm.__dict__)
    guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=512*1024*1024)
    result={'schema':'researchos.w09-nf6-four-actual-independent-facts.v1','actor_id':ACTOR,'reviewer_id':'/root/backup_regression_resources','actor_role':'INDEPENDENT_NON_AUTHOR','Source_author':'codex:/root/full_w09_source_review','executor':ROOT,'input_ref':INPUT,'progress_input_ref':PROGRESS,'groups':{},'six_Mode_issued':False,'formal_acceptance':False,'formal_case_accepted_delta':0,'new_Native_runs':0,'new_Go_runs':0,'new_SQL_connections':0,'new_model_requests':0,'Main_written':False,'Canon_written':False,'live_Canon_read':False,'prior_successful_G01_predicates_replayed':False}
    error=None
    try:
        guard.acquire(list(unique.values()));m.read_ref=lambda ref:guard.get_buffer(str(m.ref_shape(ref)))
        closure=m.load_module(m.read_ref(pin(R/'ops/ci/w09_evidence_closure.py')),R/'ops/ci/w09_evidence_closure.py')
        m.root_prepare_pair=lambda *args:root_prepare(lib,m,*args)
        def bound_run(first,last,inv,c,request):return root_run(lib,m,packet['groups'][c['selector_key']],c,m.decode(m.read_ref(packet['groups'][c['selector_key']]['producer_closed_ref'])),progress['groups'])
        m.root_run_pair=bound_run;m.mode_facts=lambda *args:lib.mode_facts(m,*args)
        facts=g01_reused_pending(lib,m,g1,choices['W09-G01'],progress['groups']);result['groups']['W09-G01']=facts;save('G01.actual.facts.json',facts)
        for key in ('W09-G02','A06','C19'):
            facts=m.review_group(packet['groups'][key],choices[key],closure,m.read_ref(pin(R/'execution/v2.4/formal_profile_w09.py')),bp)
            result['groups'][key]=facts;save(key+'.actual.facts.json',facts)
        result['decision']='FOUR_ACTUAL_GROUPS_FACTS_VERIFIED_PENDING_SIX_MODE_PUBLICATION'
    except BaseException as exc:error={'type':type(exc).__name__,'message':str(exc)};traceback.print_exc()
    finally:
        closed_guard=guard.close();cr=save('remaining-actual-SourceGuard.closed.json',closed_guard)
        result.update(primary_error=error,guard_cleanup_ref=cr,all_review_guards_closed=closed_guard['closed'],retained_handles_count=closed_guard['retained_handles_count'],held_resources=len(closed_guard['entries']))
        rr=save('four-actual-facts.result.json',result)
        print(json.dumps({'result_ref':rr,'guard_cleanup_ref':cr,'completed_group_keys':list(result['groups']),'error':error,'closed':closed_guard['closed'],'retained_handles_count':closed_guard['retained_handles_count'],'held_resources':len(closed_guard['entries']),'Mode_issued':False},ensure_ascii=False))
    return 0 if error is None and closed_guard['closed']and closed_guard['retained_handles_count']==0 and closed_guard['errors']==[] else 1
if __name__=='__main__':
    code=main();print('ROOT_PYTHON_EXIT='+str(code));sys.exit(code)
