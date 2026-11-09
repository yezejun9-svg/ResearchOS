from pathlib import Path
import types,json,hashlib,datetime,tempfile,re,ast
p=Path(__file__).with_name('review_support.py');m=types.ModuleType('support');m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__)
P=m.N/'actual-W09-G01-4fd62ca511684dc39d62c5571d8ddaf5/producer'
v=json.loads((P/'validation.closed.json').read_bytes());ready=json.loads((P.parent/'prepare.ready.json').read_bytes())
authority=json.loads((m.D/'G01.authority-observation.json').read_bytes());scope=authority['scope.W09-G01.json'];vector=authority['native.canonical-vector.json']
lead=json.loads((m.D/'G01.discovered-closure.json').read_bytes())['references']
lead.extend(m.refs(authority))
for key in ('source_author_audit_ref','source_review_audit_ref'):
    doc=json.loads(Path(scope[key]['path']).read_bytes());lead.extend(m.refs(doc))
for ref in vector['refs']:
    archive=m.S/('historical.cp376.before-native.'+Path(ref['path']).name)
    archived=m.pin(archive);assert archived['sha256']==ref['sha256'] and archived['bytes']==ref['bytes'];lead.append(archived)
lead.extend([m.GREF,m.pin(P/'validation.closed.json'),m.pin(P/'native-packet.public-index.json'),m.pin(P.parent/'prepare.ready.json'),m.pin(m.N/'HDF.json'),m.pin(m.S/'w09.G01-native-run-final.actual-audit.root.json')])
live={r['path'] for r in vector['refs']};unique={}
for ref in lead:
    ref=m.absolute(ref)
    if ref['path'] in live:continue
    assert unique.get(ref['path'],ref)==ref;unique[ref['path']]=ref
checks=[];g=m.guard();mode_refs=None
def check(label,condition,detail=None):
    item={'check':label,'passed':bool(condition),'detail':detail};checks.append(item)
    with (m.D/'G01.checks-progress.jsonl').open('ab') as f:f.write((json.dumps(item,ensure_ascii=False)+'\n').encode())
    if not condition:raise ValueError(label)
def doc(ref):return json.loads(g.get_buffer(m.absolute(ref)['path']))
def source_doc(path):return json.loads(g.get_buffer(str(path)))
def equal_raw(ref):
    raw=g.get_buffer(m.absolute(ref)['path']);return hashlib.sha256(raw).hexdigest()==ref['sha256'] and len(raw)==ref['bytes']
try:
    print(json.dumps({'stage':'hold_complete_G01_closure','unique_refs':len(unique),'unique_bytes':sum(r['bytes'] for r in unique.values()),'live_Canon_handles':0}),flush=True)
    g.acquire(list(unique.values()))
    check('all_full_closure_pins_held',True,{'refs':len(unique),'bytes':sum(r['bytes'] for r in unique.values())})
    choice=source_doc(m.N/'source.choice.json');c={**choice['common'],**choice['selectors']['W09-G01']}
    report=doc(v['summary']['report_ref']);tool=doc(v['summary']['tool_run_ref']);packet=doc(v['native_packet_ref']);inventory=doc(v['summary']['compiler_inventory_ref']);bp=doc(c['compiler_blueprint_ref'])
    check('Source21_exact_current_report',scope['source21']==ready['source21']==inventory['source21']==c['source21'] and len(c['source21'])==21 and report['version_manifest']['source_sha256']=={Path(r['path']).relative_to(m.R).as_posix():'sha256:'+r['sha256'] for r in c['source21']})
    check('Source_manifest_complete_held',all(r['path'] in unique for r in source_doc(m.N/'MF.json')['members']))
    check('native_mode_route_roster',report['status']=='PASS' and report['exit_code']==tool['native_exit_code']==0 and type(report['exit_code']) is int and not report['timed_out'] and report['selected_tests']==c['selected_tests'] and sorted(report['assertion_ids'])==sorted(c['expected_native_ids']) and v['summary']['run_id']==report['run_id']==tool['run_id']==scope['run_id'])
    check('native_original_archives_byte_identical',len(packet['raw_copy_mapping'])==651 and all(g.get_buffer(r['original_ref']['path'])==g.get_buffer(r['archive_ref']['path']) for r in packet['raw_copy_mapping']))
    check('native_no_formal_or_automatic_retry',v['actual_formal_consumers'] is False and v['formal_case_accepted_delta']==0 and v['automatic_retry'] is False and v['Main_source_written'] is False and v['Canon_written'] is False and tool['formal_acceptance']=='NOT_RUN')
    for observation in v['invocation_observations']:
        invocation=doc(observation['ref']);result=invocation['result'];cleanup=result['job_cleanup'];ft=result['creation_time_100ns']
        check(observation['label']+'_OwnedJob_and_integer_FILETIME',type(ft) is int and 0<ft<=0xffffffffffffffff and str(ft)==invocation['creation_time_100ns_decimal'] and result['actual_exit']==0 and not result['timed_out'] and result['error'] is None and cleanup['active_processes_last_observed']==0 and type(cleanup['active_processes_last_observed']) is int and not cleanup['errors'] and all(cleanup[k] is True for k in ('unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed')) and invocation['individual_child_numeric_exit'] is None,{'creation_time_100ns_decimal':str(ft),'primary_exit':result['actual_exit'],'unobserved_child_exit':None})
        check(observation['label']+'_actual_streams_environment',invocation['public_environment']==ready['environment'] and invocation['evidence_errors']==[] and equal_raw(invocation['stdout_ref']) and equal_raw(invocation['stderr_ref']))
    check('all_actual_Source_guards_closed',v['all_guards_closed'] is True and v['all_owned_jobs_closed'] is True and v['all_cleanup_receipts_saved'] is True and not v['cleanup_errors'] and all(doc(x['ref'])['closed'] is True and doc(x['ref'])['retained_handles_count']==0 and not doc(x['ref'])['errors'] for x in v['guard_cleanups']) and all(doc(x['ref'])['closed'] is True and doc(x['ref'])['retained_handles_count']==0 for x in ready['guard_cleanups']))
    decoder=json.JSONDecoder();text=g.get_buffer(doc(v['invocation_refs'][0])['stdout_ref']['path']).decode('utf-8');pos=0;pkgs=[];stable={};generated={};exports={};gomods={};embeds=[]
    cache=Path(c['scratch_root'])/'gocache';bound={r['path']:r for r in bp['stable_input_refs']}
    input_fields=('GoFiles','CgoFiles','CFiles','CXXFiles','MFiles','HFiles','FFiles','SFiles','SwigFiles','SwigCXXFiles','SysoFiles','CompiledGoFiles','TestGoFiles','XTestGoFiles','EmbedFiles','TestEmbedFiles','XTestEmbedFiles')
    def actual_pin(path):
        path=Path(path);ref=unique.get(str(path));assert ref is not None,str(path);return ref
    while pos<len(text):
        while pos<len(text) and text[pos].isspace():pos+=1
        if pos==len(text):break
        pkg,pos=decoder.raw_decode(text,pos);assert not pkg.get('Error') and not pkg.get('DepsErrors');pkgs.append(pkg['ImportPath'])
        directory=Path(pkg['Dir']) if pkg.get('Dir') else None
        for field in input_fields:
            for name in pkg.get(field,[]):
                path=Path(name);path=path if path.is_absolute() else directory/path;ref=actual_pin(path)
                if path.is_relative_to(cache):generated[ref['path']]=ref
                else:assert bound.get(ref['path'])==ref;stable[ref['path']]=ref
                if field.endswith('EmbedFiles'):embeds.append({'package':pkg['ImportPath'],'field':field,'ref':ref})
        mod=pkg.get('Module')
        while mod:
            if mod.get('GoMod'):
                ref=actual_pin(mod['GoMod']);assert bound.get(ref['path'])==ref;gomods[ref['path']]=ref
            mod=mod.get('Replace')
        if pkg.get('Export'):
            path=Path(pkg['Export']);assert path.is_relative_to(cache);ref=actual_pin(path);exports[ref['path']]=ref
        elif not pkg.get('DepOnly') and pkg.get('Name') not in (None,'main'):assert pkg['ImportPath'] in ('unsafe','builtin')
    check('actual_two_package_variants_full_compiler_replay',len(pkgs)==len(set(pkgs))==353 and set(pkgs)<=set(bp['allowed_package_roster']) and set(bp['required_test_packages'])<=set(pkgs) and inventory['packages']==pkgs and inventory['stable_build_input_refs']==list(stable.values()) and inventory['private_generated_input_refs']==list(generated.values()) and inventory['private_export_refs']==list(exports.values()) and inventory['module_go_mod_refs']==list(gomods.values()) and inventory['actual_embed_files']==embeds and gomods=={r['path']:r for r in bp['module_go_mod_refs']},{'allowed_pins':len(bp['stable_input_refs']),'actual_stable':len(stable),'generated':len(generated),'exports':len(exports),'packages':len(pkgs),'required_test_packages':bp['required_test_packages']})
    closure_ref=next(r for r in c['source21'] if Path(r['path']).name=='w09_evidence_closure.py');closure=m.inert(closure_ref['path'],g.get_buffer(closure_ref['path']))
    source={**report,'report_reference':Path(v['summary']['report_ref']['path']).relative_to(m.R).as_posix()}
    native=closure.verify_native(m.R,source,report,c['expected_native_ids'],c['selected_tests']);check('Main_verify_native_Go_JSONL_replay',True)
    owned=closure.verify_owned(m.R,source,report,c['selected_tests'],c['assertion_owner']);check('Main_verify_owned_all_export_assertions',len(owned['members'])==647)
    closure.verify_c19(owned);check('Main_verify_c19_actual_invalidation',True)
    closure.verify_a06(owned);check('Main_verify_a06_actual_HTTP_context_FTS',True)
    issued=datetime.datetime.fromisoformat(scope['lease_issued_at']);expires=datetime.datetime.fromisoformat(scope['lease_expires_at']);started=datetime.datetime.fromisoformat(report['started_at']);ended=datetime.datetime.fromisoformat(report['ended_at'])
    check('actual_Root_scope_lease_causal_order',issued<=started<=ended<=expires and scope['issued_by']==scope['executor']=='codex:/root' and scope['maximum_go_list_runs']==scope['maximum_go_test_runs']==1 and vector['checkpoint_revision']==376 and vector['ownership_revision']==180)
    # Root's immutable capture, not a synthesized hostpair, supplies actual original offsets.
    audit=source_doc(m.S/'w09.G01-native-run-final.actual-audit.root.json');raw=g.get_buffer(audit['original_capture_ref']['path']);lines=raw.splitlines(keepends=True)
    check('Root_actual3LF_original_hashes',len(lines)==3 and [hashlib.sha256(x).hexdigest() for x in lines]==audit['original_line_sha256'] and json.loads(lines[0])['payload']['id']==audit['Root_thread_id'] and audit['binding_sha256']==v['invocation_refs'][1]['sha256'])
    with Path(audit['source_audit_path']).open('rb') as f:
        for offset,line in zip(audit['source_line_offsets'],lines):f.seek(offset);assert f.read(len(line))==line
    check('Root_actual3LF_original_offsets',True)
    rawcall=json.loads(lines[1])['payload'];rawreturn=json.loads(lines[2])['payload'];check('Root_actual_call_return_pair',rawcall['call_id']==rawreturn['call_id'])
    rootTemp=Path(ready['environment']['TEMP']);state_roots=[x['value']['root_path'] for k,vs in owned['events'].items() if k.startswith('state-') for x in vs if x['value'].get('root_path')]
    check('FIXTURE_real_owned_TEMP_and_HTTP_delivery',any(Path(x).is_relative_to(rootTemp) for x in state_roots) and all(x['value'].get('delivery')=='IN_PROCESS_HTTptest_RECORDER' for x in owned['events'].get('http-exchange',[])),{'producer_TEMP':str(rootTemp),'formal_consumer_TEMP_required':str(rootTemp)})
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();review={'schema':'researchos.w09-independent-mode-review.v1','actor_id':'/root/full_w09_source_review','actor_role':'INDEPENDENT_NON_AUTHOR','producer_id':'codex:/root','run_id':native['run_id'],'report_sha256':v['summary']['report_ref']['sha256'],'source_sha256':native['source_hashes'],'go_executable':native['go'],'run_os':report['version_manifest']['os'],'run_os_release':report['version_manifest']['os_release'],'decision':'QUALIFIED','issued_at':stamp,'execution_grant':False,'formal_acceptance':False,'actual_consumers_executed':False,'checks_ref':m.write('G01.independent-checks.json',{'checks':checks,'product_calls':0,'Source_controls_repeated':False})}
    review_ref=m.write('G01.independent-mode-review.json',review);relative_review={**review_ref,'path':Path(review_ref['path']).relative_to(m.R).as_posix()}
    decision={'schema':'researchos.w09-mode-decision.v2','route':['test.retrieval','W09','W09-G01',''],'mode':'FIXTURE','run_id':native['run_id'],'report_ref':source['report_reference'],'report_sha256':review['report_sha256'],'stdout_sha256':native['stdout']['sha256'],'source_sha256':native['source_hashes'],'go_executable':native['go'],'producer_id':'codex:/root','reviewer_id':'/root/full_w09_source_review','reviewer_role':'INDEPENDENT_NON_AUTHOR','issuer_id':'/root/full_w09_source_review','decision':'QUALIFIED','input_origin':'OWNED_TEMP_DIR','independent_review_ref':relative_review,'issued_at':stamp,'producer_TEMP':str(rootTemp),'execution_grant':False,'formal_acceptance':False}
    decision_ref=m.write('G01.mode-decision.json',decision)
    tempfile.tempdir=str(rootTemp)
    closure.verify_mode(m.R,source,report,tuple(decision['route']),owned,native,Path(decision_ref['path']).relative_to(m.R).as_posix(),decision_ref['sha256'])
    check('Main_verify_mode_exact_published_refs',True)
    mode_refs={'independent_review_ref':review_ref,'mode_decision_ref':decision_ref}
    print(json.dumps({'G01':'QUALIFIED_INDEPENDENT_MODE_ONLY','mode_refs':mode_refs,'checks':len(checks),'product_calls':0,'formal_acceptance':False},ensure_ascii=False),flush=True)
finally:
    closed=g.close();ref=m.write('G01.full-closure.guard.closed.json',closed)
    result=m.write('G01.review-result.json',{'selector':'W09-G01','checks':checks,'mode_refs':mode_refs,'guard_ref':ref,'all_closed':closed['closed'],'retained_handles_count':closed['retained_handles_count'],'Source_controls_repeated':False,'product_calls':0,'formal_acceptance':False,'execution_grant':False})
    print(json.dumps({'review_result_ref':result,'guard_ref':ref,'closed':closed['closed'],'retained_handles_count':closed['retained_handles_count']},ensure_ascii=False),flush=True)
