from pathlib import Path
import types,json,hashlib,datetime
p=Path(__file__).with_name('review_support.py');m=types.ModuleType('support');m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__)
runs={'W09-G02':('28aa266121d24ad2988d578df02d23a4',1121),'A06':('ba9a185f551c4d4caf123da7eafb4245',1125)}
g01_inventory=json.loads((m.N/'actual-W09-G01-4fd62ca511684dc39d62c5571d8ddaf5/producer/actual-compiler-input-inventory.json').read_bytes());shared={r['path']:r for r in g01_inventory['stable_build_input_refs']}
choice=json.loads((m.N/'source.choice.json').read_bytes());common=choice['common'];allrefs=[m.GREF,*common['source21'],common['toolchain_ref'],common['tool_refs']['go']];data={}
failure_audits={'W09-G02':m.S/'w09.G02-native-failed-original1121.actual-audit.root.json','A06':m.S/'native.A06-final-original1125.actual-host.binding.json'}
metadata=json.loads((m.D/'failed-selectors.metadata.json').read_bytes())
for selector,(run,ordinal) in runs.items():
    P=m.N/('actual-'+selector+'-'+run)/'producer';v=json.loads((P/'validation.closed.json').read_bytes());packet=json.loads(Path(v['native_packet_ref']['path']).read_bytes());report=json.loads(Path(packet['original_report_ref']['path']).read_bytes());request=json.loads(Path(v['request_ref']['path']).read_bytes());scope=json.loads(Path(request['scope_ref']['path']).read_bytes());audit=json.loads(failure_audits[selector].read_bytes())
    data[selector]={'P':P,'v':v,'packet':packet,'scope':scope,'audit':audit,'report':report}
    allrefs.extend([m.pin(P/'validation.closed.json'),v['native_packet_ref'],v['request_ref'],request['scope_ref'],m.pin(failure_audits[selector]),audit['original_capture_ref'],m.pin(P/'actual-compiler-input-inventory.json'),m.pin(P.parent/'prepare.ready.json')])
    allrefs.extend(metadata[selector]['refs']);allrefs.extend(m.refs(report))
    allrefs.extend(m.refs(json.loads((P.parent/'prepare.ready.json').read_bytes()).get('guard_cleanups')))
    for relative in report['raw_evidence_references']:allrefs.append(m.pin(m.R/relative))
unique={};reused=[]
need_read={r['path'] for r in common['source21']}
for ref in allrefs:
    ref=m.absolute(ref)
    if ref['path'] in shared and ref['path'] not in need_read:
        assert shared[ref['path']]==ref;reused.append(ref);continue
    assert unique.get(ref['path'],ref)==ref;unique[ref['path']]=ref
g=m.guard();results={}
def read(ref):return json.loads(g.get_buffer(m.absolute(ref)['path']))
try:
    g.acquire(list(unique.values()))
    closure_ref=next(r for r in common['source21'] if Path(r['path']).name=='w09_evidence_closure.py');closure=m.inert(closure_ref['path'],g.get_buffer(closure_ref['path']))
    for selector,(run,ordinal) in runs.items():
        d=data[selector];P=d['P'];v=d['v'];packet=d['packet'];scope=d['scope'];audit=d['audit'];report=read(packet['original_report_ref']);tool=read(packet['original_tool_run_ref']);inventory=read(m.pin(P/'actual-compiler-input-inventory.json'));c={**common,**choice['selectors'][selector]};checks=[]
        def check(name,ok,detail=None):
            checks.append({'check':name,'passed':bool(ok),'detail':detail})
            if not ok:raise ValueError(selector+':'+name)
        check('current_Source21_matches_original_failed_run',report['version_manifest']['source_sha256']=={Path(r['path']).relative_to(m.R).as_posix():'sha256:'+r['sha256'] for r in c['source21']} and inventory['source21']==scope['source21']==c['source21'])
        check('actual_original_failure_kept',v['status']=='FAILED_NO_AUTOMATIC_RETRY' and v['summary'] is None and v['automatic_retry'] is False and report['exit_code']==tool['native_exit_code']==1 and report['timed_out'] is False and v['formal_case_accepted_delta']==0 and v['actual_formal_consumers'] is False and report['missing_assertion_ids']==['W09-G02-LEGACY-ROOT'],{'original_failure_ordinal':ordinal,'Go_exit':1,'launcher_exit':1,'unobserved_child_exits':None})
        check('complete_failed_packet_archives_same_bytes',len(packet['raw_copy_mapping'])==279 and all(g.get_buffer(r['original_ref']['path'])==g.get_buffer(r['archive_ref']['path']) for r in packet['raw_copy_mapping']))
        check('all_failed_stage_guards_and_owned_jobs_closed',v['all_guards_closed'] is True and v['all_owned_jobs_closed'] is True and v['all_cleanup_receipts_saved'] is True and not v['cleanup_errors'] and all(read(row['ref'])['closed'] is True and read(row['ref'])['retained_handles_count']==0 and not read(row['ref'])['errors'] for row in v['guard_cleanups']))
        creations=[]
        for row in v['invocation_observations']:
            invocation=read(row['ref']);result=invocation['result'];ft=result['creation_time_100ns'];cleanup=result['job_cleanup'];creations.append(str(ft))
            check(row['label']+'_integer_FILETIME_OwnedJob_closed',type(ft) is int and str(ft)==invocation['creation_time_100ns_decimal'] and 0<ft<=0xffffffffffffffff and type(cleanup['active_processes_last_observed']) is int and cleanup['active_processes_last_observed']==0 and not cleanup['errors'] and all(cleanup[k] is True for k in ('unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed')) and invocation['individual_child_numeric_exit'] is None)
        check('same_full_stable_compiler_inputs_reused_from_G01',inventory['stable_build_input_refs']==g01_inventory['stable_build_input_refs'] and inventory['module_go_mod_refs']==g01_inventory['module_go_mod_refs'] and inventory['package_count']==353 and inventory['packages']==g01_inventory['packages'] and len(inventory['private_export_refs'])==352 and len(inventory['private_generated_input_refs'])==2)
        streams=[g.get_buffer(str(m.R/ref)) for ref in report['raw_evidence_references']];events=[json.loads(line) for line in streams[0].decode().splitlines()]
        selected=c['selected_tests'];passed=[e['Test'] for e in events if e.get('Action')=='pass' and e.get('Test') in selected];failed=[e['Test'] for e in events if e.get('Action')=='fail' and e.get('Test') in selected]
        expected_failure='TestW09LegacyRootMigrationRevokesUnidentifiedRoot';cause=[e.get('Output','') for e in events if e.get('Test')==expected_failure and 'MIGRATION_' in e.get('Output','')]
        check('actual_Go_seven_PASS_Legacy_FAIL',len(passed)==7 and set(passed)==set(selected)-{expected_failure} and failed==[expected_failure] and report['passed_tests']==passed and streams[1]==b'' and cause and all('MIGRATION_UNSUPPORTED_OR_GAPPED_VERSION' in x for x in cause),{'passed_tests':passed,'failed_tests':failed,'actual_failure_output':cause})
        source={**report,'report_reference':Path(packet['original_report_ref']['path']).relative_to(m.R).as_posix()}
        rejected=None
        try:closure.verify_native(m.R,source,report,c['expected_native_ids'],selected)
        except ValueError as exc:rejected=str(exc)
        check('Main_rejects_failed_native_mode',rejected=='GO_TEST_ROSTER_NOT_PASS',{'Main_rejection':rejected})
        check('Root_scope_lease_true_original_run',datetime.datetime.fromisoformat(scope['lease_issued_at'])<=datetime.datetime.fromisoformat(report['started_at'])<=datetime.datetime.fromisoformat(report['ended_at'])<=datetime.datetime.fromisoformat(scope['lease_expires_at']) and scope['issued_by']==scope['executor']=='codex:/root' and scope['run_id']==run)
        lines=g.get_buffer(audit['original_capture_ref']['path']).splitlines(keepends=True)
        check('Root_actual3_original_hashes_and_callid',len(lines)==3 and [hashlib.sha256(x).hexdigest() for x in lines]==audit['original_line_sha256'] and json.loads(lines[0])['payload']['id']==audit['Root_thread_id'] and json.loads(lines[1])['payload']['call_id']==json.loads(lines[2])['payload']['call_id'])
        with Path(audit['source_audit_path']).open('rb') as f:
            for offset,line in zip(audit['source_line_offsets'],lines):f.seek(offset);assert f.read(len(line))==line
        check('Root_actual3_original_byte_offsets',True)
        review={'schema':'researchos.w09-independent-mode-review.v1','actor_id':'/root/full_w09_source_review','actor_role':'INDEPENDENT_NON_AUTHOR','producer_id':'codex:/root','run_id':run,'report_sha256':packet['original_report_ref']['sha256'],'source_sha256':report['version_manifest']['source_sha256'],'go_executable':report['go_executable'],'run_os':report['version_manifest']['os'],'run_os_release':report['version_manifest']['os_release'],'decision':'NOT_QUALIFIED','reason':'ACTUAL_NATIVE_GO_TEST_FAILURE','original_failure_ordinal':ordinal,'observed_Go_exit':1,'unobserved_child_numeric_exits':None,'actual_legacy_failure_output':cause,'issued_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks,'execution_grant':False,'formal_acceptance':False}
        review_ref=m.write(selector+'.independent-mode-review.json',review)
        routes=[['test.retrieval','W09','W09-G02','']] if selector=='W09-G02' else [['test.retrieval','W09','','A06'],['test.security','W09','','A06']]
        decisions=[]
        for index,route in enumerate(routes):
            decision={'schema':'researchos.w09-mode-decision.v2','route':route,'mode':'LIVE_WINDOWS' if selector=='W09-G02' else 'FIXTURE','run_id':run,'report_ref':source['report_reference'],'report_sha256':review['report_sha256'],'stdout_sha256':hashlib.sha256(streams[0]).hexdigest(),'source_sha256':review['source_sha256'],'go_executable':report['go_executable'],'producer_id':'codex:/root','reviewer_id':'/root/full_w09_source_review','issuer_id':'/root/full_w09_source_review','reviewer_role':'INDEPENDENT_NON_AUTHOR','decision':'NOT_QUALIFIED','independent_review_ref':{**review_ref,'path':Path(review_ref['path']).relative_to(m.R).as_posix()},'original_failure_ordinal':ordinal,'reason':review['reason'],'execution_grant':False,'formal_acceptance':False}
            decisions.append(m.write(selector+'.mode-decision.'+str(index)+'.json',decision))
        results[selector]={'review_ref':review_ref,'mode_decision_refs':decisions,'validation_ref':m.pin(P/'validation.closed.json'),'native_packet_ref':v['native_packet_ref'],'report_ref':packet['original_report_ref'],'tool_run_ref':packet['original_tool_run_ref'],'original_failure_ordinal':ordinal,'mode':'NOT_QUALIFIED','checks':len(checks),'creation_FILETIME_decimal':creations,'Go_exit':1,'formal_acceptance':False}
    ref=m.write('failed-selectors.independent-result.json',{'selectors':results,'new_guard_refs':len(unique),'stable_compiler_pins_reused':len({r['path'] for r in reused}),'G01_full_pin_proof_ref':m.pin(m.D/'G01.full-closure.guard.closed.json'),'old_Source_controls_repeated':False,'actual_products_rerun':0,'execution_grant':False,'formal_acceptance':False})
    print(json.dumps({'result_ref':ref,'selectors':results},ensure_ascii=False),flush=True)
finally:
    c=g.close();ref=m.write('failed-selectors.full.guard.closed.json',c);print(json.dumps({'guard_ref':ref,'closed':c['closed'],'retained_handles_count':c['retained_handles_count']},ensure_ascii=False),flush=True)
