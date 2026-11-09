"""Pure boundary controls and Source guards; all future authority stays in memory."""
import ast
import base64
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import types
import uuid

N=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os')
checks=[]
def check(name,value):
    assert value,name
    checks.append(dict(name=name,passed=True))
def pin(p):
    p=Path(p).resolve(strict=True);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,v):
    with (N/name).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
    return pin(N/name)
def load(p):return json.loads(Path(p).read_bytes())
def mod(p):
    m=types.ModuleType('pure_'+Path(p).stem);m.__file__=str(p)
    exec(compile(Path(p).read_bytes(),str(p),'exec'),m.__dict__);return m

def run():
    c=load(N/'source.choice.json');contract=load(N/'root-calling-contract.json');bp=load(N/'compiler-source-blueprint.json')
    m=mod(N/'main_c19_runtime.source.py');original_read=m.read_ref;original_pin=m.pin
    files=[p for p in N.iterdir() if p.is_file()]
    for p in files:
        if p.suffix=='.py':compile(p.read_bytes(),str(p),'exec')
    check('all_Source_python_compile_without_execution',True)
    old=Path(c['producer_r3_handoff_ref']['path']).parent
    inverse=load(N/'caller.complete-byte-inverse.json')
    for row in inverse['files']:
        check('complete_after_bytes_'+Path(row['proposed_ref']['path']).name,base64.b64decode(row['whole_after_base64'])==Path(row['proposed_ref']['path']).read_bytes())
        if row['original_ref']:
            check('complete_old_caller_inverse_'+Path(row['original_ref']['path']).name,base64.b64decode(row['whole_before_base64'])==Path(row['original_ref']['path']).read_bytes())
        else:check('new_Source_absence_inverse_'+Path(row['proposed_ref']['path']).name,row['whole_before_base64'] is None)
    check('futureSource21_exact21',len(c['source21'])==21 and len({r['path'] for r in c['source21']})==21)
    check('futureMain7_count',len(c['main_seven_after_refs'])==7)
    check('blueprint351_metadata_only',bp['package_count']==351 and bp['metadata_only_not_previous_Native_acceptance'] is True)
    check('blueprint_private_generated_rule',bp['historical_generated_cache_entries']==1 and all('/.local/gocache/' not in r['path'].replace('\\','/') for r in bp['stable_input_refs']))
    check('explicit19_GoMod_refs',len(bp['module_go_mod_refs'])==19)
    for key,name in contract['source_file_bindings'].items():check('source_binding_'+key,contract['bound_source_refs'][key]==pin(N/name))
    for stage in ('prepare','run'):
        entry=(N/(stage+'_main_c19.actual_owned.py')).read_text(encoding='utf-8')
        check('entry_runtime_pin_'+stage,pin(N/'main_c19_runtime.source.py')['sha256'] in entry)
        check('entry_explicit_stage_'+stage,"m.stage("+repr(stage)+",sys.argv[1:])" in entry)
    launcher=mod(N/'main_c19_launcher.source.py')
    check('launcher_runtime_pin',launcher.RUNTIME_SHA==pin(N/'main_c19_runtime.source.py')['sha256'])
    stdlib_uuid4=uuid.uuid4;p=launcher.OneShotEvidenceUUID(c['run_id'])
    check('adapter_exact_uuid',p.uuid4().hex==c['run_id'])
    try:p.uuid4()
    except ValueError:check('adapter_second_call_rejected',True)
    else:raise AssertionError('adapter repeated')
    for attr in ('uuid1','UUID','hex','_used','__dict__'):
        try:getattr(p,attr)
        except ValueError:check('adapter_other_attribute_'+attr,True)
        else:raise AssertionError('adapter attribute accepted')
    check('stdlib_uuid_function_identity_preserved',uuid.uuid4 is stdlib_uuid4)
    runner_source=Path(c['sealed_six_source_refs']['ops/ci/retrieval.py']['path']).read_bytes()
    runner_tree=ast.parse(runner_source)
    usages=[v for v in ast.walk(runner_tree) if isinstance(v,ast.Attribute) and isinstance(v.value,ast.Name) and v.value.id=='uuid']
    check('runner_exact_one_uuid4_usage',len(usages)==1 and usages[0].attr=='uuid4')
    inner=next(v for v in runner_tree.body if isinstance(v,ast.FunctionDef) and v.name=='run')
    check('inner_timeout180_unchanged',ast.literal_eval(inner.args.defaults[0])==180)
    env=m.build_environment(c)
    check('private_fresh_cache_path',env['GOCACHE']==str(Path(c['scratch_root'])/'gocache'))
    check('private_fixture_TEMP',env['TEMP']==env['TMP']==str(Path(c['scratch_root'])/'temp'))
    check('offline_Go_env',all(env[k]=='off' for k in ('GOPROXY','GOSUMDB','GOWORK','GOENV')) and env['GOTOOLCHAIN']=='local')
    check('no_inherited_provider_env',not any('KEY' in k or 'TOKEN' in k or 'SECRET' in k for k in env))
    check('exact_C19_selector',env['RESEARCHOS_TASK_ID']=='W09' and env['RESEARCHOS_CASE_ID']=='C19' and env['RESEARCHOS_CHECK_ID']=='')
    for raw in ('{"a":1,"a":2}','{"x":NaN}'):
        try:m.decode(raw)
        except ValueError:check('json_reject_'+raw,True)
        else:raise AssertionError('ambiguous JSON accepted')

    def authority_trial(mutate=None):
        memory={};documents={}
        def put(path,value):
            raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode();ref=m.raw_pin(path,raw);memory[str(path)]=raw;return ref
        def read(ref):
            if ref['path'] in memory:
                raw=memory[ref['path']]
                m.require(m.raw_pin(ref['path'],raw)==ref,'PURE_PIN_DRIFT');return raw
            return original_read(ref)
        def mempin(path):
            key=str(Path(path));return m.raw_pin(key,memory[key]) if key in memory else original_pin(path)
        for ref in c['main_seven_after_refs']:
            relative=Path(ref['path']).relative_to(R).as_posix()
            source=(Path(c['sealed_six_source_refs'][relative]['path']) if relative in c['sealed_six_source_refs']
                    else Path(c['adoption_source_handoff_ref']['path']).parent/'commands.proposed.json')
            memory[ref['path']]=source.read_bytes();assert m.raw_pin(ref['path'],memory[ref['path']])==ref
        members=[pin(p) for p in files]
        sm=put(N/'MF.json',dict(members=members));sh=put(N/'HDF.json',dict(status='SOURCE_READY_PENDING_INDEPENDENT_REVIEW',actor_id=m.AUTHOR,manifest_ref=sm))
        d=dict(schema=contract['source_review_requirement']['decision_schema'],decision=contract['source_review_requirement']['decision'],
            actor_role='INDEPENDENT_NON_AUTHOR',actor_id='SYNTHETIC_SOURCE_REVIEWER_NOT_ACTUAL',source_handoff_ref=sh,source_manifest_ref=sm,
            calling_contract_ref=pin(N/'root-calling-contract.json'),**contract['bound_source_refs'],run_id=c['run_id'],output_root=c['output_root'],
            source21=c['source21'],actual_executed=False,formal_case_accepted_delta=0)
        ad=dict(schema=contract['current_adoption_requirement']['decision_schema'],decision=contract['current_adoption_requirement']['decision'],
            actor_role='INDEPENDENT_NON_AUTHOR',actor_id='SYNTHETIC_ADOPTION_REVIEWER_NOT_ACTUAL',
            source_handoff_ref=c['adoption_source_handoff_ref'],source_manifest_ref=c['adoption_source_manifest_ref'],
            final_target_refs=c['main_seven_after_refs'],source21=c['source21'],all_handles_closed=True,formal_acceptance=False,formal_case_accepted_delta=0)
        outcome=dict(status='SOURCE_ADOPTED_PENDING_REAL_DISPATCH_AND_FORMAL_REVIEW',final_matches_expected_commit_or_rollback=True,
            final_target_refs=c['main_seven_after_refs'],transaction=dict(status='SEVEN_SOURCE_TARGETS_COMMITTED'),
            owned_cleanup=dict(closed=True,errors=[]),guard_cleanup=dict(closed=True,errors=[]),formal_dispatcher=False,new_Go_SQL_API_model_calls=0,formal_case_accepted_delta=0)
        data=dict(source_decision=d,adoption_decision=ad,outcome=outcome,scope_changes={},cp_revision=368,ow_revision=172,wrong_owner=False,duplicate_worker=False,reverse_vector=False)
        if mutate:mutate(data)
        ar=put(Path(c['future_adoption_outcome_path']),data['outcome']);ad['adoption_outcome_ref']=ar
        qhome=N/'SYNTHETIC_SOURCE_REVIEW_NEVER_WRITTEN';dr=put(qhome/'decision.json',d);qm=put(qhome/'MF.json',dict(members=[dr]));qh=put(qhome/'HDF.json',dict(manifest_ref=qm,actor_id=d['actor_id'],source_decision_ref=dr))
        ahome=N/'SYNTHETIC_ADOPTION_REVIEW_NEVER_WRITTEN';adr=put(ahome/'decision.json',ad);am=put(ahome/'MF.json',dict(members=[adr]));ah=put(ahome/'HDF.json',dict(manifest_ref=am,actor_id=ad['actor_id'],actual_decision_ref=adr))
        scope=dict(schema=contract['root_scope_schema'],status=contract['root_scope_status'],issued_by=m.ROOT_ACTOR,executor=m.ROOT_ACTOR,
            source_handoff_ref=sh,source_manifest_ref=sm,**contract['bound_source_refs'],source_review_handoff_ref=qh,source_review_manifest_ref=qm,
            source_review_decision_ref=dr,adoption_outcome_ref=ar,adoption_review_handoff_ref=ah,adoption_review_manifest_ref=am,adoption_review_decision_ref=adr,
            **{k:c[k] for k in ('source_root','run_id','receipt_root','scratch_root','output_root','selected_tests','expected_native_ids','source21','main_seven_after_refs',
                'list_timeout_seconds','producer_timeout_seconds','inner_Go_timeout_seconds')},maximum_go_test_runs=1,maximum_go_list_runs=1,
            **{k:False for k in m.BOOL_FALSE},**{k:0 for k in m.ZERO})
        scope.update(data['scope_changes'])
        sr=put(N/'SYNTHETIC_ROOT_SCOPE_NEVER_WRITTEN.json',scope)
        owner=dict(owner=m.ROOT_ACTOR,current_source_writer=None,state=contract['registered_state'],scope_ref=sr,
            source_handoff_ref=sh,source_manifest_ref=sm,source_review_handoff_ref=qh,source_review_manifest_ref=qm,
            adoption_outcome_ref=ar,adoption_review_handoff_ref=ah,source_root=str(R),run_id=c['run_id'],receipt_root=c['receipt_root'],
            scratch_root=c['scratch_root'],output_root=c['output_root'],formal_case_accepted_delta=0,parent_acceptance=False)
        worker=dict(step_id='W09-99',slice_id=m.SLICE,owner=m.ROOT_ACTOR,state=owner['state'],scope_ref=sr,source_handoff_ref=sh,
            source_review_handoff_ref=qh,adoption_outcome_ref=ar,run_id=c['run_id'])
        if data['wrong_owner']:owner['owner']='SYNTHETIC_FOREIGN'
        cp=dict(project_id='aede0678-7308-43dc-b9f2-cfe3d90cfdfb',head=c['expected_git_head'],revision=data['cp_revision'],workers=[worker]*(2 if data['duplicate_worker'] else 1))
        ow=dict(revision=data['ow_revision'],active_integrator=dict(id=m.ROOT_ACTOR),shared_integrator='qoder-desktop:/root/platform_owner',
            card_path_bindings={'W09-99':dict(owner=m.ROOT_ACTOR,subtasks={m.OWNER_KEY:owner})})
        refs=[put(m.CANON[0],cp),put(m.CANON[1],ow),put(m.CANON[2],dict(schema='SYNTHETIC_STATE')),c['main_seven_after_refs'][6]]
        if data['reverse_vector']:refs.reverse()
        vr=put(N/'SYNTHETIC_VECTOR_NEVER_WRITTEN.json',dict(schema=contract['canonical_vector']['schema'],checkpoint_revision=data['cp_revision'],ownership_revision=data['ow_revision'],refs=refs))
        qr=put(N/'SYNTHETIC_REQUEST_NEVER_WRITTEN.json',dict(schema=contract['request_schema'],issued_by=m.ROOT_ACTOR,scope_ref=sr,
            canonical_vector_ref=vr,calling_contract_ref=pin(N/'root-calling-contract.json')))
        m.read_ref=read;m.pin=mempin
        try:
            returned=m.validate_authority(qr,c)
            return dict(passed=True,refs=len(returned[0]))
        except (ValueError,KeyError,TypeError) as exc:return dict(passed=False,error=str(exc))
        finally:m.read_ref=original_read;m.pin=original_pin
    result=authority_trial();check('complete_future_Main_adoption_review_scope_vector_owner_gate',result['passed'])
    changes={
        'old_CP366':lambda x:x.update(cp_revision=366),
        'adoption_CP367_not_new_scope':lambda x:x.update(cp_revision=367),
        'old_OW170':lambda x:x.update(ow_revision=170),
        'adoption_OW171_not_new_scope':lambda x:x.update(ow_revision=171),
        'wrong_native_owner':lambda x:x.update(wrong_owner=True),
        'duplicate_worker':lambda x:x.update(duplicate_worker=True),
        'unordered_vector':lambda x:x.update(reverse_vector=True),
        'Source_self_review':lambda x:x['source_decision'].update(actor_id=m.AUTHOR),
        'Root_self_review':lambda x:x['source_decision'].update(actor_id=m.ROOT_ACTOR),
        'pending_Source_review':lambda x:x['source_decision'].update(decision='PENDING'),
        'adoption_not_actual':lambda x:x['outcome'].update(status='SOURCE_ONLY'),
        'adoption_unclosed':lambda x:x['outcome']['guard_cleanup'].update(closed=False),
        'adoption_review_not_actual':lambda x:x['adoption_decision'].update(decision='SOURCE_ACCEPTED'),
        'adoption_review_self':lambda x:x['adoption_decision'].update(actor_id=m.ROOT_ACTOR),
        'adoption_changed_Source21':lambda x:x['adoption_decision'].update(source21=[]),
        'foreign_launcher_review':lambda x:x['source_decision'].update(launcher_ref=dict(path='FOREIGN',sha256='0'*64,bytes=0)),
    }
    for field,value in [('run_id','0'*32),('source_root',str(R/'.local/worktrees/foreign')),('output_root',str(R/'FOREIGN')),
                        ('source21',[]),('maximum_go_test_runs',2),('maximum_go_test_runs',True),('maximum_go_list_runs',2),
                        ('list_timeout_seconds',1200),('producer_timeout_seconds',1200),('inner_Go_timeout_seconds',1200),
                        ('formal_case_accepted_delta',False),('formal_case_accepted_delta',0.0),('external_model_provider_requests',1),
                        ('automatic_retry',True),('worktree_creation',True),('Source_mutation',True),('formal_acceptance',True)]:
        label='scope_'+field+'_'+repr(value)
        changes[label]=lambda x,f=field,v=value:x['scope_changes'].update({f:v})
    for name,mutate in changes.items():check('authority_reject_'+name,not authority_trial(mutate)['passed'])

    stable_ref=next(r for r in bp['stable_input_refs'] if r['path']==str(R/'internal/domain/retrieval.go'))
    cache=Path(c['scratch_root'])/'gocache'
    synthetic_packages=[]
    for i,name in enumerate(bp['package_roster']):
        pkg=dict(ImportPath=name,Name='synthetic_package',Dir=str(R/'internal/domain'),GoFiles=['retrieval.go'],Export=str(cache/(str(i)+'-d')))
        if i==0:pkg['CompiledGoFiles']=[str(cache/'generated-d')]
        if i<len(bp['module_go_mod_refs']):pkg['Module']=dict(GoMod=bp['module_go_mod_refs'][i]['path'])
        synthetic_packages.append(pkg)
    exact=m.exact_path
    def compiler_trial(mutate=None,drift=False):
        packages=copy.deepcopy(synthetic_packages)
        if mutate:mutate(packages)
        fixed={r['path']:r for r in bp['stable_input_refs']}
        def fakepin(path):
            p=Path(path)
            if str(p) in fixed:
                ref=copy.deepcopy(fixed[str(p)])
                if drift and str(p)==stable_ref['path']:ref['sha256']='0'*64
                return ref
            return m.raw_pin(p,b'SYNTHETIC_FRESH_EXPORT_OR_UNKNOWN_FILE')
        m.exact_path=lambda p,absent=False:Path(p);m.pin=fakepin
        try:
            result=m.compiler_inventory('\n'.join(json.dumps(p) for p in packages),c,bp)
            return dict(passed=True,result=result)
        except (ValueError,KeyError,TypeError) as exc:return dict(passed=False,error=str(exc))
        finally:m.exact_path=exact;m.pin=original_pin
    result=compiler_trial();check('compiler351_exports_GoMod_generated_closure_pure',result['passed'] and len(result['result']['private_export_refs'])==351 and len(result['result']['module_go_mod_refs'])==19)
    for label,mutate in [('missing_package',lambda p:p.pop()),('package_error',lambda p:p[0].update(Error={'Err':'SYNTHETIC'})),
                        ('foreign_export_cache',lambda p:p[0].update(Export=str(R/'.local/gocache/old-d'))),
                        ('unknown_source',lambda p:p[0].update(GoFiles=['not-in-blueprint.go'])),
                        ('missing_generated',lambda p:p[0].pop('CompiledGoFiles')),
                        ('missing_export',lambda p:p[0].pop('Export')),
                        ('missing_GoMod',lambda p:p[0].pop('Module')),
                        ('wrong_roster',lambda p:p[0].update(ImportPath='SYNTHETIC_UNKNOWN_PACKAGE'))]:
        check('compiler_reject_'+label,not compiler_trial(mutate)['passed'])
    check('compiler_reject_held_source_drift',not compiler_trial(drift=True)['passed'])

    # The actual invocation function is exercised against memory streams only.
    storage={};records={}
    class Stream(io.BytesIO):
        def __init__(self,path):super().__init__();self.path=path
        def close(self):
            if not self.closed:storage[self.path]=self.getvalue()
            super().close()
    class MemPath:
        def __init__(self,path):self.path=path
        def __truediv__(self,name):return MemPath(self.path+'/'+name)
        def open(self,mode):assert mode=='xb' and self.path not in storage;return Stream(self.path)
        def is_file(self):return self.path in storage
        def __str__(self):return self.path
    helper_result=dict(actual_exit=0,timed_out=False,error=None,creation_time_100ns=133713371337133713,
        job_cleanup=dict(errors=[],active_processes_last_observed=0,**{k:True for k in ('unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed')}))
    class Helper:
        def __init__(self,result):self.calls=0;self.result=result
        def run_owned(self,argv,cwd,env,stdout,stderr,wall,creation_flags):
            self.calls+=1;stdout.write(b'original\x00stdout\r\n');stderr.write(b'original stderr\n');return copy.deepcopy(self.result)
    oldsave=m.save;m.pin=lambda p:m.raw_pin(str(p),storage[str(p)])
    def memsave(root,name,value):
        records[name]=copy.deepcopy(value);return m.raw_pin(str(root/name),json.dumps(value).encode())
    m.save=memsave
    try:
        helper=Helper(helper_result);m.invoke(helper,MemPath('MEMORY'),'success',['exact'],{},240)
        rec=records['success.invocation.json']
        check('Owned_helper_exact_single_call',helper.calls==1)
        check('raw_stdout_bytes_unchanged',storage['MEMORY/success.stdout.raw']==b'original\x00stdout\r\n')
        check('FILETIME_integer_lossless',rec['result']['creation_time_100ns']==133713371337133713 and type(rec['result']['creation_time_100ns']) is int)
        check('FILETIME_decimal_string_lossless',rec['creation_time_100ns_decimal']=='133713371337133713')
        check('unknown_individual_exit_null',rec['individual_child_numeric_exit'] is None)
        for label,mutate in [('nonzero',lambda v:v.update(actual_exit=7)),('unknown',lambda v:v.update(actual_exit=None)),
                              ('timeout',lambda v:v.update(timed_out=True)),('unclosed',lambda v:v['job_cleanup'].update(handles_closed=False))]:
            value=copy.deepcopy(helper_result);mutate(value);helper=Helper(value)
            try:m.invoke(helper,MemPath('MEMORY'),label,['exact'],{},240)
            except ValueError:check('first_failure_stop_'+label,helper.calls==1 and records[label+'.invocation.json']['result']==value)
            else:raise AssertionError('failure accepted')
    finally:m.save=oldsave;m.pin=original_pin
    # Execute the exact finally-loop AST with a failing first close; the next guard must still close.
    tree=ast.parse((N/'main_c19_runtime.source.py').read_bytes());stage_node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='stage')
    trynode=next(n for n in stage_node.body if isinstance(n,ast.Try))
    close_loop=next(n for n in trynode.finalbody if isinstance(n,ast.For))
    called=[]
    class FakeGuard:
        def __init__(self,name,fail=False):self.name=name;self.fail=fail
        def close(self):
            called.append(self.name)
            if self.fail:raise OSError('SYNTHETIC_CLOSE_FAILURE')
            return dict(closed=True,errors=[],retained_handles_count=0)
    scope=dict(guards=[('second',FakeGuard('second')),('first',FakeGuard('first',True))],cleanups=[],created=False,stage_root=None,guard_cleanup_ok=m.guard_cleanup_ok)
    exec(compile(ast.Module(body=[close_loop],type_ignores=[]),'<pure-exact-cleanup-loop>','exec'),scope)
    check('all_guards_attempted_after_close_failure',called==['first','second'] and len(scope['cleanups'])==2 and not scope['cleanups'][0]['closed'] and scope['cleanups'][1]['closed'])
    invoke_calls=[n for n in ast.walk(stage_node) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='invoke']
    check('exact_two_bounded_invocations_in_run_Source',len(invoke_calls)==2)
    text=ast.unparse(stage_node)
    check('fixed_output_no_latest_glob_selection',"output = Path(c['output_root'])" in text and '.iterdir()' not in text.replace("(scratch / 'gocache').iterdir()",''))
    check('guards_loaded_before_runtime_module_inventory',text.index("helper = module(c['owned_job_ref'])")<text.index('input_refs, bp = read_inputs(c)'))
    check('closed_packet_requires_two_jobs_and_archive','packet_ref is not None and len(receipts) == 2 and all_jobs_closed' in text)
    packet_node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='validate_packet')
    packet_source=ast.unparse(packet_node)
    check('packet_binds_report_tool_exact_native_argv',"report['actual_invocation'] == tool['actual_invocation'] == expected_argv" in packet_source)
    check('packet_binds_tool_original_streams',all(v in packet_source for v in ('TOOL_EXACT_ORIGINAL_STREAMS',"tool['stdout_sha256']", "tool['stderr_sha256']")))
    check('packet_requires_actual_C19_route',"EXACT_C19_REPORT_ROUTE" in packet_source and "report['check_id'] is None" in packet_source)
    check('no_product_subprocess_implementation',all(not isinstance(n,ast.Call) or ast.unparse(n.func) not in ('subprocess.run','subprocess.Popen','os.system','os.popen') for n in ast.walk(tree)))
    check('future_outputs_still_absent',all(not Path(c[k]).exists() for k in ('receipt_root','scratch_root','output_root')))
    check('no_future_authority_files_written',not (N/'SYNTHETIC_ROOT_SCOPE_NEVER_WRITTEN.json').exists() and not (N/'SYNTHETIC_SOURCE_REVIEW_NEVER_WRITTEN').exists())
    return dict(schema='researchos.w09-main-c19-producer-pure-Source-controls.v1',status='PASS',new_check_count=len(checks),checks=checks,
        real_producer_runs=0,actual_Main_preparation=False,actual_dispatcher=False,Git_Go_SQL_API_model_calls=0,
        future_authority_documents_only_in_memory=True,old_Native_component_PASS_not_promoted=True,formal_case_accepted_delta=0)

def main():
    assert sys.argv[1:] in ([],['--revision2'])
    suffix='.revision2' if sys.argv[1:] else ''
    c=load(N/'source.choice.json');inputs=load(N/'source-input-pins.original.json')['refs']
    forbidden={r['path'].casefold() for r in c['main_seven_after_refs']}|{str(R/'execution/v2.4'/f'{n}.json').casefold() for n in ('checkpoint','path_ownership','step_state','commands')}
    check('Source_guards_exclude_Root_seven_targets_and_Canon',not forbidden&{r['path'].casefold() for r in inputs})
    refs={r['path'].casefold():r for r in inputs}
    for p in N.iterdir():
        if p.is_file():refs[str(p).casefold()]=pin(p)
    gm=mod(c['guard_ref']['path']);guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
    result=None
    try:
        guard.acquire(list(refs.values()));result=run()
        for ref in inputs:assert pin(ref['path'])==ref
    finally:
        cleanup=guard.close();cref=save('source-controls'+suffix+'.guard.cleanup.actual.json',cleanup)
    assert cleanup['closed'] and not cleanup['errors'] and cleanup['retained_handles_count']==0
    result.update(original_inputs_unchanged=len(inputs),guard_cleanup_ref=cref)
    save('source-controls'+suffix+'.json',result)
    print(json.dumps(dict(status=result['status'],new_checks=result['new_check_count'],inputs=len(inputs),actual=False)))

if __name__=='__main__':main()
