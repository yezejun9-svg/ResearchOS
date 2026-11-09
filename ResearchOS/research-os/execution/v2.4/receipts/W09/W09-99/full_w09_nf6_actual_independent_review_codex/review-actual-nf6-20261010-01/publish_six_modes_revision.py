import ast,datetime,hashlib,json,ntpath,os,platform,sys,tempfile,traceback,types
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W09/W09-99';Q=Path(__file__).resolve().parent
P=B/'full_w09_main_native_producer_source_codex/fullw09-20261010-06'
GUARD=R/'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
TEMP_PARENT=Path('C:/Users/yqyyds/.researchos/w09-native-v5')
ACTOR='codex:/root/backup_regression_resources';REVIEWER='/root/backup_regression_resources';ROOT='codex:/root'
def need(ok,code):
    if not ok:raise ValueError(code)
def pin(path):
    raw=Path(path).read_bytes();return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def rel(ref):return dict(ref,path=Path(ref['path']).relative_to(R).as_posix())
def save(path,doc):
    with Path(path).open('xb')as out:out.write((json.dumps(doc,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    return pin(path)
def definitions(path):
    tree=ast.parse(path.read_bytes());lib=types.ModuleType('nf6_mode_support');lib.__file__=str(path)
    exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom,ast.Assign,ast.FunctionDef))],type_ignores=[]),str(path)+'#definitions-only','exec'),lib.__dict__)
    return lib
def main():
    delta=definitions(Q/'review_partial_delta.py');lib=delta.support();m=lib.reused_module()
    prior_ref=pin(Q/'four-actual-facts.result.json');prior=m.decode(m.read_ref(prior_ref))
    need(prior['decision']=='FOUR_ACTUAL_GROUPS_FACTS_VERIFIED_PENDING_SIX_MODE_PUBLICATION'and prior['primary_error']is None and prior['all_review_guards_closed']is True and prior['retained_handles_count']==0 and set(prior['groups'])=={'W09-G01','W09-G02','A06','C19'},'ALL_FOUR_ACTUAL_FACTS_REQUIRED_BEFORE_MODE')
    spec=m.decode((Q/'six-mode-schema.json').read_bytes());need(len(spec['six_route_specs'])==6,'SIX_DISTINCT_ROUTES')
    src=m.decode((P/'source.choice.json').read_bytes());choices={key:{**src['common'],**src['selectors'][key]}for key in prior['groups']}
    facts={key:m.decode((Q/(('G01'if key=='W09-G01'else key)+'.actual.facts.json')).read_bytes())for key in prior['groups']}
    refs=[prior_ref,prior['guard_cleanup_ref'],pin(Q/'six-mode-schema.json'),pin(R/'ops/ci/w09_evidence_closure.py'),pin(R/'execution/toolchains/locked.json')]
    report_data={}
    for key,fact in facts.items():
        report=m.decode(m.read_ref(fact['report_ref']));report_data[key]=report;refs.extend([fact['report_ref'],fact['tool_run_ref'],pin(Q/(('G01'if key=='W09-G01'else key)+'.actual.facts.json'))])
        for claim in report['owned_export']['members']:
            label=Path(claim['path']).name.split('-',1)[1][:-4]
            if label=='http-exchange'or label.startswith('state-')or(key=='W09-G02'and label in('g02-os-branch','g02-junction-command','g02-junction-stdout')):refs.append(claim)
    unique={}
    for ref in refs:
        path=m.ref_shape(ref);key=ntpath.normcase(ntpath.normpath(str(path)))
        if key in unique:need(unique[key]['sha256']==ref['sha256']and unique[key]['bytes']==ref['bytes'],'MODE_RESOURCE_NO_PIN_CONFLICT')
        unique[key]=dict(ref,path=str(path))
    raw=GUARD.read_bytes();need(hashlib.sha256(raw).hexdigest()=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85','MODE_GUARD_RESOURCE')
    gm=types.ModuleType('nf6_mode_guard');gm.__file__=str(GUARD);exec(compile(raw,str(GUARD),'exec'),gm.__dict__)
    guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=512*1024*1024);publication_guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=128*1024*1024)
    published=[];verified=[];error=None;old_temp={key:os.environ.get(key)for key in('TEMP','TMP')};old_tempdir=tempfile.tempdir
    result={'schema':'researchos.w09-nf6-six-mode-publication.v1','actor_id':ACTOR,'reviewer_id':REVIEWER,'source_author':'codex:/root/full_w09_source_review','executor':ROOT,'four_actual_facts_ref':prior_ref,'mode_decisions':published,'Main_verifier_results':verified,'formal_acceptance':False,'formal_case_accepted_delta':0,'new_Native_runs':0,'new_Go_runs':0,'new_SQL_connections':0,'new_model_requests':0,'Main_written':False,'Canon_written':False,'Root_execution_grant':False,'future_consumer_public_environment':{'TEMP':str(TEMP_PARENT),'TMP':str(TEMP_PARENT)}}
    try:
        guard.acquire(list(unique.values()));m.read_ref=lambda ref:guard.get_buffer(str(m.ref_shape(ref)))
        closure=m.load_module(m.read_ref(pin(R/'ops/ci/w09_evidence_closure.py')),R/'ops/ci/w09_evidence_closure.py')
        locked=m.decode(m.read_ref(pin(R/'execution/toolchains/locked.json')))
        out=Q/'modes';out.mkdir(exist_ok=False)
        g02=facts['W09-G02']['mode_predicate_facts'];witness_common={'run_id':g02['run_id'],'report_sha256':facts['W09-G02']['report_ref']['sha256'],'source_sha256':g02['source_sha256'],'go_executable':g02['go_executable'],'actual_platform':'Windows 11 x64','reviewer_id':REVIEWER,'Root_producer_id':ROOT,'actual_fact_ref':pin(Q/'W09-G02.actual.facts.json'),'formal_authority':False,'new_Native_runs':0}
        host={**witness_common,'schema':'researchos.w09-host-witness.v1','actual_branch':g02['go_branch_actual'],'actual_branch_event_ref':g02['host_event_ref'],'review_host':{'os_name':os.name,'platform_system':platform.system(),'machine':platform.machine(),'version':platform.version(),'build':sys.getwindowsversion().build}}
        junction={**witness_common,'schema':'researchos.w09-junction-witness.v1','command':g02['junction_actual']['command'],'output_pin':g02['junction_actual']['output'],'root_path':g02['junction_actual']['root_path'],'target_path':g02['junction_actual']['target_path'],'actual_exit':0,'actual_event_ref':g02['junction_event_ref']}
        hr=save(out/'G02.host-witness.json',host);jr=save(out/'G02.junction-witness.json',junction)
        result['host_witness_ref']=hr;result['junction_witness_ref']=jr;new_refs=[hr,jr]
        for index,route_spec in enumerate(spec['six_route_specs'],1):
            key=route_spec['selector_key'];fact=facts[key];mf=fact['mode_predicate_facts'];report=report_data[key];tool=m.decode(m.read_ref(fact['tool_run_ref']))
            common={'run_id':fact['run_id'],'report_sha256':fact['report_ref']['sha256'],'source_sha256':mf['source_sha256'],'go_executable':mf['go_executable'],'producer_id':ROOT,'decision':'QUALIFIED'}
            receipt={**common,'schema':'researchos.w09-independent-mode-review.v1','actor_id':REVIEWER,'actor_role':'INDEPENDENT_NON_AUTHOR','metadata_canonical_actor':ACTOR,'Source_author':'codex:/root/full_w09_source_review','run_os':report['version_manifest']['os'],'run_os_release':report['version_manifest']['os_release'],'route':route_spec['route'],'actual_fact_ref':pin(Q/(('G01'if key=='W09-G01'else key)+'.actual.facts.json')),'four_actual_fact_ref':prior_ref,'Root_execution_grant':False,'formal_acceptance':False,'formal_case_accepted_delta':0}
            rr=save(out/(str(index).zfill(2)+'.independent-mode-review.json'),receipt)
            mode={**common,'schema':'researchos.w09-mode-decision.v2','route':route_spec['route'],'mode':route_spec['mode'],'report_ref':Path(fact['report_ref']['path']).relative_to(R).as_posix(),'stdout_sha256':tool['stdout_sha256'],'reviewer_id':REVIEWER,'reviewer_role':'INDEPENDENT_NON_AUTHOR','independent_review_ref':rel(rr),'formal_authority':False,'formal_case_accepted_delta':0}
            if mode['mode']=='FIXTURE':mode['input_origin']='OWNED_TEMP_DIR'
            else:mode.update(locked_go_sha256=locked['tools']['go']['sha256'],host_witness=rel(hr),junction_witness=rel(jr),witness_allowlist=[rel(hr),rel(jr)],junction_root_path=g02['junction_actual']['root_path'],junction_target_path=g02['junction_actual']['target_path'])
            mr=save(out/(str(index).zfill(2)+'.mode-decision.json'),mode);new_refs.extend([rr,mr])
            published.append({'route':route_spec['route'],'selector_key':key,'mode':mode['mode'],'run_id':fact['run_id'],'mode_ref':mr,'mode_consumption_ref':rel(mr),'independent_review_ref':rr})
        publication_guard.acquire(new_refs)
        os.environ['TEMP']=os.environ['TMP']=str(TEMP_PARENT);tempfile.tempdir=None
        need(Path(tempfile.gettempdir()).resolve(strict=True)==TEMP_PARENT.resolve(strict=True),'EXACT_COMMON_CONSUMER_TEMP')
        for row in published:
            key=row['selector_key'];fact=facts[key];report=report_data[key];source=dict(report,report_reference=Path(fact['report_ref']['path']).relative_to(R).as_posix());mf=fact['mode_predicate_facts'];tool=m.decode(m.read_ref(fact['tool_run_ref']))
            ctx={'events':{},'members':{}}
            for claim in report['owned_export']['members']:
                path=m.ref_shape(claim);ctx['members'][path]=claim;label=path.name.split('-',1)[1][:-4]
                if label=='http-exchange'or label.startswith('state-')or(key=='W09-G02'and label in('g02-os-branch','g02-junction-command')):
                    item=m.decode(m.read_ref(claim));ctx['events'].setdefault(label,[]).append({'value':item,'path':path,'pin':claim,'test':path.parent.name})
            native={'run_id':fact['run_id'],'stdout':{'sha256':tool['stdout_sha256']},'source_hashes':mf['source_sha256'],'go':mf['go_executable']}
            observation=closure.verify_mode(R,source,report,tuple(row['route']),ctx,native,row['mode_consumption_ref']['path'],row['mode_ref']['sha256'])
            verified.append({'route':row['route'],'mode_ref':row['mode_ref'],'actual_Main_verify_mode_result':observation,'synthetic_run':False,'new_product_run':False})
        need(len(verified)==6 and len({tuple(x['route'])for x in verified})==6,'SIX_EXACT_CURRENT_MODE_GATES')
        result['decision']='SIX_CURRENT_NATIVE_MODES_QUALIFIED_COMPONENT_ONLY'
    except BaseException as exc:error={'type':type(exc).__name__,'message':str(exc)};traceback.print_exc()
    finally:
        for key,value in old_temp.items():
            if value is None:os.environ.pop(key,None)
            else:os.environ[key]=value
        tempfile.tempdir=old_tempdir
        pc=publication_guard.close();gc=guard.close();pcr=save(Q/'Mode-publication-SourceGuard.closed.json',pc);gcr=save(Q/'Mode-input-SourceGuard.closed.json',gc)
        result.update(primary_error=error,publication_guard_cleanup_ref=pcr,input_guard_cleanup_ref=gcr,all_guards_closed=pc['closed']and gc['closed'],retained_handles_count=pc['retained_handles_count']+gc['retained_handles_count'],Mode_verified_count=len(verified),input_resources_held=len(gc['entries']),publication_resources_held=len(pc['entries']))
        rr=save(Q/'six-Mode-publication.result.json',result)
        print(json.dumps({'result_ref':rr,'guard_cleanup_refs':[pcr,gcr],'verified_Mode_count':len(verified),'primary_error':error,'all_guards_closed':result['all_guards_closed'],'retained_handles_count':result['retained_handles_count'],'formal_case_accepted_delta':0},ensure_ascii=False))
    return 0 if error is None and result['all_guards_closed']and result['retained_handles_count']==0 and pc['errors']==gc['errors']==[] else 1
if __name__=='__main__':
    code=main();print('ROOT_PYTHON_EXIT='+str(code));sys.exit(code)
