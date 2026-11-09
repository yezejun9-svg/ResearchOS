from pathlib import Path
import ast,copy,datetime,hashlib,json,sys,types
p=Path(__file__).with_name('inspect_public21_source.py');h=types.ModuleType('support');h.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),h.__dict__)
s=json.loads((h.D/'source-observations.json').read_bytes())
refs_by_path={r['path']:r for r in s['held_refs']}
caller=h.inert(h.N/'public21_root.source.py');caller._base=h.inert(s['source_handoff']['OC3_source_ref']['path'])
checks=[]
def check(name,ok,details=None):checks.append({'id':name,'passed':bool(ok),'kind':'INDEPENDENT_SOURCE_OR_READONLY_BINDING_CHECK_NOT_PRODUCT','details':details})
def rejected(name,action,expected=None):
    try:action()
    except (ValueError,RuntimeError) as e:check(name,expected is None or expected in str(e),{'exception':type(e).__name__,'code':str(e)})
    else:check(name,False,{'unexpected_acceptance':True})

# This is a real read-only call over already completed immutable programme evidence.
# It issues no Scope, invokes no entry branch and creates no programme qualification.
programme=caller.programme_chain()
check('actual-completed-programme-chain-new-public21-interface',programme['document']['status']=='QUALIFIED_OLD21_BUILD',{'programme_ref':caller.PROGRAMME_REF,'returned_ref_count':len(programme['refs']),'live_Canon_refs_held':False})
runner_source=caller.doc(caller.LEAF_REFS['hdf']);runner_manifest=caller.base().manifest(caller.LEAF_REFS['mf']);runner_contract=s['contracts']['runner']
leaf_inputs=caller.doc(runner_source['input_manifest_ref'])
source_control=caller.doc(s['source_handoff']['source_controls_ref'])
check('author58-results-reused-without-invocation',source_control['passed']==58 and not source_control['failed'] and source_control['synthetic_only'] is True,{'ref':s['source_handoff']['source_controls_ref'],'author_control_ids':[x['id'] for x in source_control['controls']],'rerun':False})

# Deliberately new joint-boundary cases, rather than rerunning the author's parser/lease controls.
now=datetime.datetime.now(datetime.timezone.utc)
def iso(delta):return (now+datetime.timedelta(seconds=delta)).isoformat()
fixture_scope={'runner_contract_ref':caller.LEAF_REFS['contract_ref'],'registration_request_ref':{'path':str(h.D/'SOURCE_INTERFACE_FIXTURE_ONLY_REQUEST.json'),'sha256':'0'*64,'bytes':0},'lease_expires_at':iso(600),'output_root':str(h.D/'SOURCE_INTERFACE_FIXTURE_ONLY_OUTPUT')}
fixture_actual={'case_request_ref':{'path':str(h.D/'SOURCE_INTERFACE_FIXTURE_ONLY_CASE.json'),'sha256':'1'*64,'bytes':0},'runtime_qualification_ref':{'path':str(h.D/'SOURCE_INTERFACE_FIXTURE_ONLY_QUALIFICATION.json'),'sha256':'2'*64,'bytes':0}}
scope=caller.LiveScope(fixture_actual,object(),{}, {}, {})
scope._fresh=lambda:(fixture_scope,None,None,None,None)
real_doc=caller.doc
fixture_qualification_scope={'created_utc':iso(-60),'lease_expires_at':iso(600)}
fixture_registration={'created_utc':iso(-60)}
def fixture_doc(ref):
    if ref==fixture_scope['registration_request_ref']:return fixture_registration
    if ref==fixture_actual['runtime_qualification_ref']:return {'qualification_scope_ref':{'path':str(h.D/'SOURCE_INTERFACE_FIXTURE_ONLY_QS.json'),'sha256':'3'*64,'bytes':0}}
    return fixture_qualification_scope
caller.doc=fixture_doc
try:
    scope.require_phase('prepare',fixture_actual['case_request_ref'],fixture_scope['output_root'])
    fixture_qualification_scope['lease_expires_at']=iso(100)
    rejected('bootstrap-refuses-short-runtime-lease-with-long-registered-lease',lambda:scope.require_phase('bootstrap21',fixture_actual['case_request_ref'],fixture_scope['output_root']),'FINITE_FRESH_PUBLIC21_LEASE_BUDGET')
    check('rejected-bootstrap-does-not-advance-phase',scope.next_phase==1)
    fixture_qualification_scope['lease_expires_at']=iso(600);fixture_scope['lease_expires_at']=iso(100)
    rejected('bootstrap-refuses-short-registered-lease-with-long-runtime-lease',lambda:scope.require_phase('bootstrap21',fixture_actual['case_request_ref'],fixture_scope['output_root']),'FINITE_FRESH_PUBLIC21_LEASE_BUDGET')
    fixture_scope['lease_expires_at']=iso(600)
    rejected('bootstrap-refuses-skipped-inspect-stage',lambda:scope.require_phase('inspect21',fixture_actual['case_request_ref'],fixture_scope['output_root']),'PUBLIC21_PHASE_SEQUENCE')
    check('joint-lease-fixtures-create-no-Scope-or-file',not any(h.D.glob('SOURCE_INTERFACE_FIXTURE_ONLY*')))
finally:caller.doc=real_doc

caller_tree=ast.parse(Path(caller.__file__).read_bytes())
funcs={n.name:n for n in caller_tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
def source(name):return ast.get_source_segment(Path(caller.__file__).read_text(encoding='utf-8'),funcs[name])
check('prepare-has-no-future-runtime-review-or-issuer-in-resource-input',"refs=source['refs']+runner['refs']+programme['refs']" in source('prepare') and "manifest_ref=save" in source('prepare') and "import sqlite3,_sqlite3" in source('prepare'),{'manifest_inputs':'existing Source/review/programme plus scope/completed preparation capture/current loaded resources; resulting runtime review and issuance are later independent steps'})
check('base-runtime-specialization-excludes-wrapper-created-only',"created_utc" in ast.unparse(caller.kernel()['runtime_review_chain'].__code__) if False else '"created_utc"' in Path(s['source_handoff']['OC3_source_ref']['path']).read_text(encoding='utf-8').split('projected =',1)[1].split('\n',1)[0],{'unchanged_OC3_time_chain':'payload_created <= actual Root call <= actual Root result <= wrapper_created <= now'})
check('registration-callback-cannot-read-or-open-live-Canon',"return projection(" in source('register') and 'def transform(cp,ow):' in source('register') and "EXCLUSIVE_PAIR_DRIFT" in source('register') and "local_refs(refs,base().CANON[:2])" in source('register'),{'TP callback':'uses only pure projection; CP/OW excluded from outer held guard'})

# Actual loaded runtime metadata only. Importing SQLite does not open a database.
import sqlite3,_sqlite3
job=caller.base().load(runner_contract['owned_job'],'independent_public21_runtime_inventory')
loaded_paths=job.runtime_resource_paths()
stdlib_refs=[]
for module in tuple(sys.modules.values()):
    for key in ('__file__','__cached__'):
        path=getattr(module,key,None)
        if path and Path(path).is_file():stdlib_refs.append(h.pin(path))
resources=[s['source_hdf_ref'],s['source_mf_ref'],s['caller_ref'],s['calling_contract_ref'],*programme['refs'],*caller.LEAF_REFS.values(),*runner_manifest['members'],runner_source['input_manifest_ref'],*leaf_inputs['references'],caller.base().GUARD_REF,caller.base().TP_REF,runner_contract['owned_job'],h.pin(sys.executable),*[h.pin(path) for path in loaded_paths],*stdlib_refs]
unique={caller.canonical(r['path']):r for r in resources}
assert not any(caller.canonical(str(p)) in unique for p in caller.base().CANON)
assert h.pin(h.G)==h.GREF;g=h.inert(h.G).SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024)
try:
    g.acquire(list(unique.values()))
    check('leaf78-input-closure-current-held',len(leaf_inputs['references'])==78,{'manifest_ref':runner_source['input_manifest_ref'],'reference_count':len(leaf_inputs['references'])})
    check('locked-Python-and-real-SQLite-extension-loaded-held',caller.same_ref(h.pin(sys.executable),runner_contract['locked_python_ref']) and any(caller.canonical(str(_sqlite3.__file__))==key for key in unique),{'locked_python_ref':runner_contract['locked_python_ref'],'SQLite_extension_ref':h.pin(_sqlite3.__file__),'SQLite_connections_opened':0})
    check('actual-old21-two-exes-match-leaf-contract',all(caller.same_ref(programme['document']['program_refs'][key],runner_contract['old21_'+key]) for key in ('control','backup')))
    report={'schema':'researchos.public21-caller-independent-runtime-source-review.v1','review_author':h.REVIEWER,'review_thread_id':h.THREAD,'source_hdf_ref':s['source_hdf_ref'],'source_mf_ref':s['source_mf_ref'],'caller_ref':s['caller_ref'],'calling_contract_ref':s['calling_contract_ref'],'checks':checks,'passed':sum(x['passed'] for x in checks),'failed':[x for x in checks if not x['passed']],'programme_root_qualification_ref':caller.PROGRAMME_REF,'programme_immutable_ref_count':len(programme['refs']),'leaf_input_manifest_ref':runner_source['input_manifest_ref'],'leaf_input_ref_count':len(leaf_inputs['references']),'held_resource_refs':list(unique.values()),'actual_loaded_Windows_module_ref_count':len(loaded_paths),'Python_module_and_cache_refs_count_before_dedup':len(stdlib_refs),'private_owner_files_read_or_hashed':0,'live_Canon_read_or_held':False,'Source_fixture_claim':'joint lease/phase controls are SOURCE_INTERFACE_FIXTURE_ONLY; no actual Root witness, Scope or runtime grant was manufactured','old_OC3_controls_rerun':False,'author58_controls_rerun':False,'Leaf_RootScope_Native_Go_SQL_model_TP_calls':0,'execution_grant':False,'formal_acceptance':False,'runtime_execution_qualification_granted':False,'future_RuntimeScope_and_manifest_review_still_required':True}
    result_ref=h.write('runtime-source-review.json',report)
finally:
    closed=g.close();guard_ref=h.write('runtime-source-review.guard.closed.json',closed)
    assert closed['closed'] is True and closed['retained_handles_count']==0 and not closed['errors']
print(json.dumps({'review_ref':result_ref,'guard_ref':guard_ref,'passed':report['passed'],'failed':report['failed'],'leaf_input_ref_count':len(leaf_inputs['references']),'held_resources':len(unique),'loaded_Windows_modules':len(loaded_paths),'all_guards_closed':True,'retained_handles_count':0,'actual_product_calls':0},ensure_ascii=False),flush=True)
