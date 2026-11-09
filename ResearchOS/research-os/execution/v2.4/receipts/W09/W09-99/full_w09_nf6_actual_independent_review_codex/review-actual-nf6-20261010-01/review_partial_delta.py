import ast,datetime,hashlib,json,ntpath,re,sys,traceback,types
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W09/W09-99';Q=Path(__file__).resolve().parent
P=B/'full_w09_main_native_producer_source_codex/fullw09-20261010-06'
S=B/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
ACTOR='codex:/root/backup_regression_resources';ROOT='codex:/root'
GUARD=R/'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'

def need(ok,code):
    if not ok:raise ValueError(code)
def pin(path):
    raw=Path(path).read_bytes();return dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def write(name,value):
    raw=(json.dumps(value,ensure_ascii=False,indent=2,default=lambda x:x.isoformat() if isinstance(x,datetime.datetime) else str(x))+'\n').encode('utf-8')
    path=Q/name
    with path.open('xb')as out:out.write(raw)
    return pin(path)
def support():
    path=Q/'review_partial_actual.py';tree=ast.parse(path.read_bytes())
    nodes=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom,ast.Assign,ast.AnnAssign)) or isinstance(n,ast.FunctionDef)and n.name!='main']
    lib=types.ModuleType('nf6_delta_support');lib.__file__=str(path)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path)+'#definitions-only','exec'),lib.__dict__)
    return lib
def progress_refs(key):
    short=key.removeprefix('W09-')
    return {label:pin(S/('nf6-'+short+'-'+phase+'-progress.host-pair.root.json'))for label,phase in [('compiler-input-list','compiler'),('w09-selector-main-producer','producer')]}
def root_run(lib,m,initial_ref,completed_ref,invocation_ref,c,request_ref):
    first,last=lib.bound_pair(m,initial_ref,completed_ref)
    source=first['call_payload'].get('input','')
    need("load('NF6_finalized_native')"in source and 'f.future_argv[k].run.map(q)'in source and 'tools.exec_command('in source,'TRUE_NF6_RUN_DISPATCH')
    closed=m.decode(m.read_ref(pin(Path(c['receipt_root'])/'producer/validation.closed.json')))
    wanted={x['label']:x['ref']for x in closed['invocation_observations']}
    pairs=[];session=first['actual_host_result']['session_id']
    for label,ref in progress_refs(c['selector_key']).items():
        item=m.root_capture(ref,wanted[label]);host=item['actual_host_result']
        need(host.get('session_id')==session and host.get('exit_code')is None and first['output_ordinal']<item['call_ordinal']<item['output_ordinal']<last['call_ordinal'],'SAME_ROOT_YIELDED_PROGRESS_THEN_COMPLETE')
        docs=[v for v in m.nested_documents(host['output'])if type(v)is dict and v.get('progress')==label]
        need(len(docs)==1 and m.same_ref(docs[0]['receipt_ref'],wanted[label])and type(docs[0]['actual_outer_exit'])is int and docs[0]['actual_outer_exit']==0 and docs[0]['original_error']is None and docs[0]['evidence_errors']==[]and docs[0]['unsaved_invocation']is None,'EXACT_INNER_INVOCATION_PUBLICATION')
        actual=m.decode(m.read_ref(wanted[label]));ft=actual['result']['creation_time_100ns']
        need(type(ft)is int and ft>0 and docs[0]['creation_time_100ns_decimal']==str(ft),'EXACT_INTEGER_FILETIME_PROGRESS')
        pairs.append(item)
    return [first,*pairs,last]
def g01_pending(lib,m,closure,row,c):
    prefix=pin(Q/'G01.original1192-successful-prefix.json')
    closed=m.decode(m.read_ref(row['producer_closed_ref']));summary=closed['summary']
    report=m.decode(m.read_ref(summary['report_ref']));permit=m.decode(m.read_ref(summary['launcher_permit_ref']))
    started_ref=pin(Path(c['receipt_root'])/'producer/launcher.started.json');ended_ref=pin(Path(c['receipt_root'])/'producer/launcher.closed.json')
    started=m.decode(m.read_ref(started_ref));ended=m.decode(m.read_ref(ended_ref))
    need(m.same_ref(started['permit_ref'],summary['launcher_permit_ref'])and m.same_ref(ended['permit_ref'],summary['launcher_permit_ref'])and m.same_ref(started['runner_ref'],permit['runner_ref'])and m.same_ref(ended['runner_ref'],permit['runner_ref'])and m.same_ref(started['launcher_ref'],permit['launcher_ref'])and m.same_ref(ended['launcher_ref'],permit['launcher_ref']),'G01_EXACT_LAUNCHER_PROVENANCE_PENDING')
    need(started['fixed_run_id']==c['run_id']and started['fixed_output_root']==c['output_root']and started['source_root']==str(R)and started['Source21']==c['source21']and started['adapter']=='RUNNER_PRIVATE_UUID_OBJECT_ONLY'and started['stdlib_uuid_modified']is False and started['Main_source_modified']is False,'G01_SINGLE_EXACT_LAUNCHER_PENDING')
    need(type(ended['runner_returned_exit'])is int and ended['runner_returned_exit']==0 and ended['error']is None and ended['one_uuid_consumed']is True and ended['cleanup_errors']==[]and ended['stdlib_uuid_modified']is False and ended['Main_source_modified']is False and ended['unknown_individual_descendant_exit']is None,'G01_LAUNCHER_CLOSED_PENDING')
    ctx={'events':{},'members':{}}
    for claim in report['owned_export']['members']:
        path=m.ref_shape(claim);label=path.name.split('-',1)[1][:-4]
        if label=='http-exchange'or label.startswith('state-'):
            raw=m.decode(m.read_ref(claim));need(raw['_run_id']==c['run_id']and raw['_test_name']==path.parent.name,'G01_PENDING_EVENT_CURRENT_RUN')
            ctx['events'].setdefault(label,[]).append({'value':raw,'path':path,'pin':claim,'test':path.parent.name})
    native={'source_hashes':report['version_manifest']['source_sha256'],'go':report['go_executable']}
    facts=lib.mode_facts(m,closure,ctx,report,c,native)
    captures=root_run(lib,m,row['run_initial_Root_capture_ref'],row['run_completed_Root_capture_ref'],closed['invocation_observations'][-1]['ref'],c,closed['request_ref'])
    return dict(selector=c['selector_key'],run_id=c['run_id'],report_ref=summary['report_ref'],tool_run_ref=summary['tool_run_ref'],prior_successful_prefix_ref=prefix,prior_1931_resource_guard_ref=pin(Q/'partial-actual-SourceGuard.closed.json'),prior_business_compiler_Job_Guard_checks_replayed=False,pending_Root_run_pairs=captures,mode_predicate_facts=facts,launcher_started_ref=started_ref,launcher_closed_ref=ended_ref,actual_native_exit=0,formal_case_accepted_delta=0,formal_acceptance=False)
def main():
    lib=support();m=lib.reused_module();packet=json.loads((Q/'partial-input-observed.json').read_bytes());src=json.loads((P/'source.choice.json').read_bytes())
    choices={key:{**src['common'],**src['selectors'][key]}for key in packet['groups']}
    bp=m.decode(m.read_ref(choices['W09-G02']['compiler_blueprint_ref']))
    refs=m.collect_actual_refs({'groups':{'W09-G02':packet['groups']['W09-G02']}},choices)
    g1=packet['groups']['W09-G01'];closed=m.decode(m.read_ref(g1['producer_closed_ref']));report=m.decode(m.read_ref(closed['summary']['report_ref']))
    refs += [g1['producer_closed_ref'],closed['summary']['report_ref'],closed['summary']['launcher_permit_ref'],g1['run_initial_Root_capture_ref'],g1['run_completed_Root_capture_ref'],pin(Q/'G01.original1192-successful-prefix.json'),pin(Q/'partial-actual-SourceGuard.closed.json')]
    refs += [x['ref']for x in closed['invocation_observations']]
    refs += [pin(Path(choices['W09-G01']['receipt_root'])/'producer'/name)for name in ('launcher.started.json','launcher.closed.json')]
    refs += [x for x in report['owned_export']['members']if (Path(x['path']).name.split('-',1)[1][:-4]=='http-exchange'or Path(x['path']).name.split('-',1)[1][:-4].startswith('state-'))]
    for key in choices:
        for ref in progress_refs(key).values():
            refs.append(ref);refs.append(m.decode(m.read_ref(ref))['original_capture_ref'])
    for ref in (g1['run_initial_Root_capture_ref'],g1['run_completed_Root_capture_ref']):refs.append(m.decode(m.read_ref(ref))['original_capture_ref'])
    refs += [pin(R/'ops/ci/w09_evidence_closure.py'),pin(R/'execution/v2.4/formal_profile_w09.py'),pin(P/'source.choice.json'),choices['W09-G02']['compiler_blueprint_ref'],pin(Q/'partial-input-observed.json')]
    unique={}
    for ref in refs:
        path=m.ref_shape(ref);key=ntpath.normcase(ntpath.normpath(str(path)))
        if key in unique:need(unique[key]['sha256']==ref['sha256']and unique[key]['bytes']==ref['bytes'],'CONSISTENT_DELTA_RESOURCE_PIN')
        unique[key]=dict(ref,path=str(path))
    raw=GUARD.read_bytes();need(hashlib.sha256(raw).hexdigest()=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85','SOURCE_GUARD_EXACT')
    gm=types.ModuleType('nf6_delta_guard');gm.__file__=str(GUARD);exec(compile(raw,str(GUARD),'exec'),gm.__dict__)
    guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=512*1024*1024);error=None
    result=dict(schema='researchos.w09-nf6-two-actual-independent-delta.v1',actor_id=ACTOR,reviewer_id='/root/backup_regression_resources',executor=ROOT,groups={},Mode_issued=False,overall_qualified=False,formal_acceptance=False,formal_case_accepted_delta=0,new_Native_runs=0,new_Go_runs=0,Canon_written=False,live_Canon_read=False)
    try:
        guard.acquire(list(unique.values()));m.read_ref=lambda ref:guard.get_buffer(str(m.ref_shape(ref)))
        closure=m.load_module(m.read_ref(pin(R/'ops/ci/w09_evidence_closure.py')),R/'ops/ci/w09_evidence_closure.py')
        m.root_prepare_pair=lambda *args:lib.root_prepare(m,*args)
        m.root_run_pair=lambda *args:root_run(lib,m,*args)
        m.mode_facts=lambda *args:lib.mode_facts(m,*args)
        facts=g01_pending(lib,m,closure,g1,choices['W09-G01']);result['groups']['W09-G01']=facts;write('G01.pending-delta.facts.json',facts)
        facts=m.review_group(packet['groups']['W09-G02'],choices['W09-G02'],closure,m.read_ref(pin(R/'execution/v2.4/formal_profile_w09.py')),bp)
        result['groups']['W09-G02']=facts;write('G02.actual.facts.json',facts)
    except BaseException as exc:error={'type':type(exc).__name__,'message':str(exc)};traceback.print_exc()
    finally:
        close=guard.close();cr=write('partial-delta-SourceGuard.closed.json',close)
        result.update(primary_error=error,guard_cleanup_ref=cr,all_review_guards_closed=close['closed'],retained_handles_count=close['retained_handles_count'],held_resources=len(close['entries']))
        rr=write('partial-delta-result.json',result)
        print(json.dumps({'result_ref':rr,'guard_cleanup_ref':cr,'completed_groups':list(result['groups']),'primary_error':error,'closed':close['closed'],'retained_handles_count':close['retained_handles_count'],'held_resources':len(close['entries']),'Mode_issued':False},ensure_ascii=False))
    return 0 if error is None and close['closed']and close['errors']==[]and close['retained_handles_count']==0 else 1
if __name__=='__main__':
    code=main();print('ROOT_PYTHON_EXIT='+str(code));sys.exit(code)
