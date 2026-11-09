"""Source compiler only: no subprocess, Go, SQL, dispatcher or model invocation."""
import ast, copy, difflib, hashlib, json, os, sys, types, uuid
from pathlib import Path
sys.dont_write_bytecode=True
R=Path('D:/作品集/ResearchOS/research-os');N=Path(__file__).resolve().parent
B=R/'execution/v2.4/receipts/W09/W09-99/w09_c19_main_root_producer_v2_source_codex/mainc19p2-1a11fe4'
G=R/'execution/v2.4/receipts/W09/W09-99/full_w09_native_gap_source_review_codex'
AUTHOR='codex:/root/native_temp_independent_review'
def pin(p):
    p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def load(p):return json.loads(Path(p).read_bytes())
def save(name,value):
    p=N/name
    with p.open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
    return pin(p)
def write(name,text):
    with (N/name).open('xb') as f:f.write(text.encode())
    return pin(N/name)
def check(ok,message):
    if not ok:raise ValueError(message)
def checked(p,digest):
    check(pin(p)['sha256']==digest,'INPUT_DRIFT '+str(p));return p.read_bytes()
def replace_one(text,old,new):
    check(text.count(old)==1,'REPLACEMENT_CARDINALITY '+old);return text.replace(old,new)
def main():
    gap=load(G/'Source-gap-report.json');check(pin(G/'Source-gap-report.json')['sha256']=='9b7bb0a54314560e285f5245d95d0ce44cb5c2510c31ef5bff3996f1602e93e5','GAP_PIN')
    plan=next(v for v in gap['next_source_tasks'] if v['id']=='SOURCE_THREE_SELECTOR_MAIN_PRODUCER')
    base=checked(B/'main_c19_runtime.source.py','790ad022d0600e53cedaf06c93661bd76ac00a57d7c8f8e7e18defaf318c533f').decode()
    old=load(B/'source.choice.json');blueprint=load(Path(old['compiler_blueprint_ref']['path']))
    check(pin(Path(old['compiler_blueprint_ref']['path']))==old['compiler_blueprint_ref'],'BASE_BLUEPRINT_PIN')
    for ref in plan['source21']:check(pin(ref['path'])==ref,'CURRENT_SOURCE21')
    guardmod=types.ModuleType('source_guard');guardmod.__file__=old['guard_ref']['path']
    check(pin(old['guard_ref']['path'])==old['guard_ref'],'SOURCE_GUARD_PIN')
    exec(compile(Path(old['guard_ref']['path']).read_bytes(),old['guard_ref']['path'],'exec'),guardmod.__dict__)
    stable=[pin(ref['path']) for ref in blueprint['stable_input_refs']]
    changed=[dict(before=a,after=b) for a,b in zip(blueprint['stable_input_refs'],stable) if a!=b]
    guard=guardmod.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
    guard.acquire(stable)
    try:
        for ref in stable:check(pin(ref['path'])==ref,'CURRENT_HELD_COMPILER_SOURCE')
        dirs=sorted({str(Path(ref['path']).parent) for ref in stable if Path(ref['path']).is_relative_to(R) and not Path(ref['path']).is_relative_to(R/'.local')})
        inv={p:sorted(child.name for child in Path(p).iterdir() if child.is_file()) for p in dirs}
        adapter='researchos.local/research-os/adapters/retrieval';domain='researchos.local/research-os/internal/domain'
        allowed=sorted(set(blueprint['package_roster'])|{adapter+' ['+adapter+'.test]',adapter+'.test'})
        bp=dict(schema='researchos.w09-three-selector-source-compiler-blueprint.v1',source_only=True,actual_package_count=None,
            required_packages=['./adapters/retrieval','./internal/domain'],allowed_package_roster=allowed,
            required_test_packages=[adapter,adapter+' ['+adapter+'.test]',adapter+'.test',domain,domain+' ['+domain+'.test]',domain+'.test'],
            stable_input_refs=stable,module_go_mod_refs=[pin(ref['path']) for ref in blueprint['module_go_mod_refs']],
            main_directory_inventory=inv,base_blueprint_ref=old['compiler_blueprint_ref'],changed_stable_source_refs=changed,
            provenance='Prior C19 metadata bounds potential imports only; later actual two-package Go list establishes closure.',
            no_prior_program_or_test_result_reuse=True)
        bpref=save('compiler-source-blueprint.json',bp)
        override=(N/'runtime-overrides.source.py').read_text(encoding='utf-8')
        nodes={n.name:n for n in ast.parse(override).body if isinstance(n,ast.FunctionDef)}
        lines=base.splitlines(keepends=True)
        replacements=[]
        for node in ast.parse(base).body:
            if isinstance(node,ast.FunctionDef) and node.name in nodes:
                new=ast.get_source_segment(override,nodes[node.name])+'\n'
                replacements.append((node.lineno-1,node.end_lineno,new));nodes.pop(node.name)
        for start,end,new in reversed(replacements):lines[start:end]=[new]
        runtime=''.join(lines)+'\n'+'\n\n'.join(ast.get_source_segment(override,n) for n in nodes.values())+'\n'
        for a,b in [('main_c19','full_w09'),('w09-main-c19','w09-three-selector'),('w09-c19-main-producer','w09-selector-main-producer'),
                    ('MAIN_C19_NATIVE_PACKET','MAIN_SELECTOR_NATIVE_PACKET'),("AUTHOR='codex:/root/command_queue_impl'","AUTHOR='"+AUTHOR+"'"),
                    ("OWNER_KEY='c19_main_root_native_producer'","OWNER_KEY='full_w09_main_native_producer'"),
                    ("SLICE='C19_MAIN_ROOT_NATIVE_PRODUCER'","SLICE='FULL_W09_MAIN_NATIVE_PRODUCER'")]:runtime=runtime.replace(a,b)
        runtime=runtime.replace('Future two-stage Main C19 producer.','Future three-selector Main W09 producer.')
        runtime=replace_one(runtime,"ROOT_ACTOR='codex:/root'","ROOT_ACTOR='codex:/root'\nROOT_THREAD_ID='01a11007-5233-7ca1-b71f-9e9e5ce84c98'\nROOT_AUDIT=r'C:\\Users\\yqyyds\\.codex\\sessions\\2026\\10\\06\\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl'")
        runtime=replace_one(runtime,"'RESEARCHOS_TASK_ID':'W09','RESEARCHOS_CHECK_ID':'','RESEARCHOS_CASE_ID':'C19','RESEARCHOS_RETRIEVAL_MODE':'fixture'",
            "'RESEARCHOS_TASK_ID':'W09','RESEARCHOS_CHECK_ID':c['selector']['check_id'],'RESEARCHOS_CASE_ID':c['selector']['case_id'],'RESEARCHOS_RETRIEVAL_MODE':('live' if c['mode']=='LIVE_WINDOWS' else 'fixture')")
        runtime=replace_one(runtime,"require(kind in ('prepare','run') and len(args)==3,'THREE_EXACT_ROOT_REQUEST_ARGUMENTS')\n    request_ref=dict(path=args[0],sha256=args[1],bytes=int(args[2]));c=choice()",
            "require(kind in ('prepare','run') and len(args)==4,'SELECTOR_AND_THREE_EXACT_ROOT_REQUEST_ARGUMENTS')\n    c=choice(args[0]);request_ref=dict(path=args[1],sha256=args[2],bytes=int(args[3]))")
        runtime=replace_one(runtime,"require(len(packages)==351 and sorted(packages)==sorted(bp['package_roster']),'EXACT_ACTUAL_351_PACKAGE_ROSTER')",
            "require(packages and len(packages)==len(set(packages)) and set(packages)<=set(bp['allowed_package_roster'])\n        and set(bp['required_test_packages'])<=set(packages),'FINITE_TWO_PACKAGE_TEST_CLOSURE')\n    verify_directories(bp)")
        runtime=replace_one(runtime,"package_count=351,packages=packages,","package_count=len(packages),packages=packages,")
        runtime=replace_one(runtime,"result['error'] is None and result['actual_exit']==0", "result['error'] is None and type(result['actual_exit']) is int and result['actual_exit']==0")
        runtime=replace_one(runtime,"receipt,_=invoke(helper,stage_root,'compiler-input-list'","validate_authority(request_ref,c);verify_directories(bp)\n            receipt,_=invoke(helper,stage_root,'compiler-input-list'")
        runtime=replace_one(runtime,"run_id=c['run_id'],output_root=c['output_root'],launcher_ref=pin(N/'full_w09_launcher.source.py'),",
            "selector=c['selector_key'],run_id=c['run_id'],output_root=c['output_root'],launcher_ref=pin(N/'full_w09_launcher.source.py'),")
        runtime=replace_one(runtime,"receipt,_=invoke(helper,stage_root,'w09-selector-main-producer'",
            "validate_authority(request_ref,c);verify_directories(bp)\n            receipt,_=invoke(helper,stage_root,'w09-selector-main-producer'")
        runtime=replace_one(runtime,"summary=validate_packet(c,output);", "validate_authority(request_ref,c);verify_directories(bp)\n            summary=validate_packet(c,output);")
        ast.parse(runtime);runtime_ref=write('full_w09_runtime.source.py',runtime)
        launcher=checked(B/'main_c19_launcher.source.py','49396e724a4670951ec325d8672c588360c4733a200c12eff0a58dc7a6a4efda').decode()
        launcher=launcher.replace('main_c19','full_w09').replace('w09-main-c19','w09-three-selector').replace('790ad022d0600e53cedaf06c93661bd76ac00a57d7c8f8e7e18defaf318c533f',runtime_ref['sha256'])
        launcher=replace_one(launcher,'c=m.choice()',"c=m.choice(permit['selector'])")
        launcher=replace_one(launcher,"{'schema','request_ref','run_id','output_root','launcher_ref','runner_ref','environment'}","{'schema','request_ref','selector','run_id','output_root','launcher_ref','runner_ref','environment'}")
        write('full_w09_launcher.source.py',launcher)
        for kind,oldname,newname in [('prepare','prepare_main_c19.actual_owned.py','prepare_full_w09.source.py'),('run','run_main_c19.actual_owned.py','run_full_w09.source.py')]:
            text=(B/oldname).read_text(encoding='utf-8').replace('main_c19','full_w09').replace('790ad022d0600e53cedaf06c93661bd76ac00a57d7c8f8e7e18defaf318c533f',runtime_ref['sha256'])
            write(newname,text)
        runner=types.ModuleType('source_inert_runner');runner.__file__=str(R/'ops/ci/retrieval.py')
        exec(compile((R/'ops/ci/retrieval.py').read_bytes(),runner.__file__,'exec'),runner.__dict__)
        common={k:old[k] for k in ('source_root','source21','guard_ref','owned_job_ref','toolchain_ref','tool_refs','identity_ref','spec_manifest_ref','expected_git_head','list_timeout_seconds','producer_timeout_seconds','inner_Go_timeout_seconds')}
        common['compiler_blueprint_ref']=bpref
        selectors={}
        for job in plan['jobs']:
            key=job['selector']['check_id'] or job['selector']['case_id'];run=uuid.uuid4().hex
            selected=runner.GROUPS[key] if key.startswith('W09-') else runner.CASES[key]
            check(selected==job['selected_tests'],'GAP_MAIN_SELECTED_PARITY')
            actual_ids=[aid for test in selected for aid in runner.TESTS[test][1]]
            check(actual_ids==job['expected_native_ids'],'GAP_MAIN_IDS_PARITY')
            c={k:job[k] for k in ('selector','mode','native_scope','selected_tests','expected_native_ids','packages','go_test_argv_suffix')}
            c.update(selector_key=key,run_id=run,receipt_root=str(N/('actual-'+key+'-'+run)),
                scratch_root=str(R/'.local'/('w09-full-'+key+'-'+run)),output_root=str(R/'execution/receipts/W09/retrieval'/('run-'+run)),
                list_argv_suffix=job['go_list_argv_suffix'],assertion_owner={aid:test for test in selected for aid in runner.TESTS[test][1]},
                required_independent_modes=2 if key=='A06' else 1)
            check(all(not Path(c[k]).exists() for k in ('receipt_root','scratch_root','output_root')),'FRESH_PATHS_ABSENT')
            selectors[key]=c
        save('source.choice.json',dict(schema='researchos.w09-three-selector-producer-source-choice.v1',actor_id=AUTHOR,
            common=common,selectors=selectors,source_only=True,execution_grant=False,actual_Main_producer=False,formal_case_accepted_delta=0))
        bindings=dict(prepare_caller_ref='prepare_full_w09.source.py',producer_caller_ref='run_full_w09.source.py',launcher_ref='full_w09_launcher.source.py',
            runtime_ref='full_w09_runtime.source.py',choice_ref='source.choice.json',compiler_blueprint_ref='compiler-source-blueprint.json')
        fields=['schema','status','issued_by','executor','source_handoff_ref','source_manifest_ref',*bindings,'source_review_handoff_ref','source_review_manifest_ref',
            'source_review_decision_ref','source_author_audit_ref','source_review_audit_ref','selector_key','selector','mode','native_scope','packages','source_root',
            'run_id','receipt_root','scratch_root','output_root','selected_tests','expected_native_ids','source21','lease_id','lease_issued_at','lease_expires_at',
            'list_timeout_seconds','producer_timeout_seconds','inner_Go_timeout_seconds','maximum_go_test_runs','maximum_go_list_runs',
            'formal_dispatcher','formal_acceptance','Source_mutation','checkpoint_write','ownership_write','step_state_write','worktree_creation','automatic_retry',
            'formal_case_accepted_delta','external_model_provider_requests','paid_provider_requests','production_DB_writes']
        contract=dict(schema='researchos.w09-three-selector-producer-root-calling-contract.v1',status='SOURCE_ONLY_NO_EXECUTION_GRANT',author=AUTHOR,
            source_file_bindings=bindings,bound_source_refs={k:pin(N/v) for k,v in bindings.items()},scope_required_fields=fields,
            request_exact_fields=['schema','issued_by','selector','scope_ref','canonical_vector_ref','calling_contract_ref','scope_audit_ref'],
            request_schema='researchos.root-w09-three-selector-native-request.v1',scope_schema='researchos.root-w09-three-selector-native-scope.v1',
            review_schema='researchos.w09-three-selector-producer-independent-source-decision.v1',
            review_decision='SOURCE_ACCEPTED_FOR_ROOT_THREE_SELECTOR_NATIVE',review_binding_fields=['source_handoff_ref','source_manifest_ref','calling_contract_ref',*bindings,'selectors','source21','actual_executed','formal_case_accepted_delta'],
            Root_issuer_executor='codex:/root',source_actor=AUTHOR,source_thread_id=os.environ.get('CODEX_THREAD_ID'),
            canonical_registration=dict(checkpoint_wip='w09_native_producer_scopes[selector_key]',ownership_subtask='full_w09_main_native_producer_<selector_key>',worker_slice='FULL_W09_MAIN_NATIVE_PRODUCER_<selector_key>'),
            future_argv={kind:[old['tool_refs']['python']['path'],'-I','-S','-B','-X','utf8',str(N/name),'<selector-key>','<Root-request-absolute-path>','<request-sha256>','<request-bytes>']
                for kind,name in [('prepare','prepare_full_w09.source.py'),('run','run_full_w09.source.py')]},
            future_root_scope=None,future_request=None,future_registration=None,future_mode_proofs=None,future_route_leases=None,future_capture_index=None,
            no_standalone_C19=True,no_old_dispatcher_rerun=True,source_only=True,execution_grant=False,formal_case_accepted_delta=0)
        save('root-calling-contract.json',contract)
        write('runtime.forward.diff',''.join(difflib.unified_diff(base.splitlines(True),runtime.splitlines(True),fromfile='C19-v2-runtime',tofile='three-selector-runtime')))
        write('runtime.inverse.diff',''.join(difflib.unified_diff(runtime.splitlines(True),base.splitlines(True),fromfile='three-selector-runtime',tofile='C19-v2-runtime')))
        save('source-build-observation.json',dict(status='SOURCE_BUILT_PENDING_CONTROLS',actor_id=AUTHOR,source_thread_id=os.environ.get('CODEX_THREAD_ID'),
            gap_ref=pin(G/'Source-gap-report.json'),base_runtime_ref=pin(B/'main_c19_runtime.source.py'),stable_input_count=len(stable),
            changed_stable_refs=changed,allowed_package_count=len(allowed),actual_package_count=None,actual_Go_runs=0,actual_Native_runs=0,
            current_Canon_held=False,Main_writes=False,Canon_writes=False,formal_case_accepted_delta=0))
    finally:
        closed=guard.close();save('source-build-guard.closed.json',closed)
        check(closed['closed'] is True and not closed['errors'] and closed['retained_handles_count']==0,'SOURCE_GUARD_CLOSED')
    print(json.dumps(dict(status='SOURCE_BUILT_PENDING_CONTROLS',namespace=str(N),stable_input_count=len(stable),allowed_package_count=len(allowed),actual_native=None)))
if __name__=='__main__':main()
