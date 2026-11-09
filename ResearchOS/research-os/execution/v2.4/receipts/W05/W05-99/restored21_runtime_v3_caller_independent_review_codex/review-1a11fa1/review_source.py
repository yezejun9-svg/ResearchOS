from pathlib import Path
import ast,base64,copy,difflib,hashlib,json,symtable,types
from datetime import datetime,timezone
R=Path('D:/作品集/ResearchOS/research-os')
N=R/'execution/v2.4/receipts/W05/W05-99/restored21_session_runtime_caller_v3_source_codex/r21v3caller-20261009-01'
O=Path(__file__).resolve().parent
ACTOR='codex:/root/native_temp_independent_review'
checks=[];observations=[]
def pin(p):
    p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(r):
    b=Path(r['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==r['sha256'] and ('bytes' not in r or len(b)==r['bytes']),r['path'];return b
def check(n,v,detail=None):
    assert v,n
    checks.append(dict(name=n,passed=True,detail=detail))
def save(n,v):
    p=O/n
    with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
    return pin(p)
def capture(f):
    try:f()
    except BaseException as e:return dict(type=type(e).__name__,message=str(e))
    return dict(type=None,message=None)
def compile_probe(nodes,ns):
    f=ast.FunctionDef(name='probe',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=copy.deepcopy(nodes),decorator_list=[])
    exec(compile(ast.fix_missing_locations(ast.Module(body=[f],type_ignores=[])),'<new-independent-v3-pure-AST>','exec'),ns)
    return ns['probe']
hr=dict(path=str(N/'HDF.json'),sha256='72df2851c4c8fe5f8db37c283dad9cfcaba0921554606f4b3d0b51f0c6e856fd',bytes=4821)
mr=dict(path=str(N/'MF.json'),sha256='5aadb19d3312853749e3bcdb5cd45d199010b15d306952f9f73610bd8a4d0b62',bytes=5073)
h=json.loads(read(hr));mf=json.loads(read(mr));C=json.loads(read(h['contract_ref']));oldN=Path(h['v2_source_handoff_ref']['path']).parent
oldreview=json.loads(read(h['v2_review_handoff_ref']));oldpins=json.loads(read(next(x for x in json.loads(read(h['v2_review_manifest_ref']))['members'] if Path(x['path']).name=='verified-input-pins.json')))
check('new_source_pair_exact',h['manifest_ref']==mr)
check('prior_review_is_REQUEST_CHANGES',oldreview['status']=='REQUEST_CHANGES' and oldreview['P1_findings']==2 and oldreview['P2_findings']==1)
refs=[hr,mr,*mf['members'],*oldpins,h['v2_review_handoff_ref'],h['v2_review_manifest_ref']]
refs={str(Path(r['path']).resolve()).casefold():dict(path=str(Path(r['path']).resolve()),sha256=r['sha256'],bytes=r['bytes']) for r in refs}
gp=C['source_guard'];gm=types.ModuleType('independent_v3_source_guard');gm.__file__=gp['path'];exec(compile(read(gp),gp['path'],'exec'),gm.__dict__)
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
try:
    guard.acquire(list(refs.values()))
    check('all_finite_refs_pinned_and_held',all(guard.get_buffer(r['path'])==read(r) for r in refs.values()),len(refs))
    for r in mf['members']:check('v3_member_'+Path(r['path']).name,Path(r['path']).parent==N and read(r)==guard.get_buffer(r['path']))
    changed=['contract.json','prepare_root_actual.py','validate_root_actual.py']
    generated=''.join(''.join(difflib.unified_diff((oldN/n).read_text().splitlines(keepends=True),(N/n).read_text().splitlines(keepends=True),fromfile='v2/'+n,tofile='v3/'+n)) for n in changed)
    check('complete_three_file_diff',generated==read(h['reversible_diff_ref']).decode())
    inverse=json.loads(read(h['byte_inverse_ref']));check('exact_inverse_roster',[r['name'] for r in inverse['files']]==changed)
    for row in inverse['files']:
        raw=base64.b64decode(row['v2_original_bytes_base64']);actual=(oldN/row['name']).read_bytes();new=(N/row['name']).read_bytes()
        check('full_byte_inverse_'+row['name'],raw==actual and (hashlib.sha256(raw).hexdigest(),len(raw))==(row['v2_sha256'],row['v2_bytes']) and (hashlib.sha256(new).hexdigest(),len(new))==(row['v3_sha256'],row['v3_bytes']))
    oldC=json.loads((oldN/'contract.json').read_bytes());changedkeys={k for k in oldC if oldC[k]!=C[k]}
    check('contract_only_version_and_output_paths_changed',changedkeys=={'schema','worktree','environment','isolation_output','validation_output'} and set(C)-set(oldC)=={'v2_source_handoff','v2_source_manifest','v2_review_handoff','v2_review_manifest'})
    texts={n:(N/n).read_text() for n in changed[1:]};trees={n:ast.parse(t) for n,t in texts.items()};mains={n:next(x for x in tr.body if isinstance(x,ast.FunctionDef) and x.name=='main') for n,tr in trees.items()}
    vm=mains['validate_root_actual.py'];pm=mains['prepare_root_actual.py'];vtry=next(x for x in vm.body if isinstance(x,ast.Try));ptry=next(x for x in pm.body if isinstance(x,ast.Try))
    sym=next(x for x in symtable.symtable(texts['validate_root_actual.py'],'validator','exec').get_children() if x.get_name()=='main')
    check('loader_is_global_not_shadowed',sym.lookup('module').is_global() and not sym.lookup('module').is_local() and sym.lookup('go_module_info').is_local())
    loader=next(x for x in vm.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='gm' for t in x.targets));metadata=next(x for x in ast.walk(vm) if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='go_module_info' for t in x.targets))
    loadercalls=[];scope=dict(module=lambda *args:loadercalls.append(args),gp=dict(path='MEMORY_ONLY'),Path=lambda p:types.SimpleNamespace(read_bytes=lambda:b'PURE_BUFFER'),pkg=dict(Module=dict(GoMod='MEMORY_ONLY')))
    check('exact_loader_call_reachable',capture(compile_probe([loader,metadata],scope))['type'] is None and loadercalls==[('MEMORY_ONLY',b'PURE_BUFFER')])
    finalizer=next(x for x in vm.body if isinstance(x,ast.FunctionDef) and x.name=='closed');check('closed_defined_before_first_guard',finalizer.lineno<vtry.lineno)
    class FakeGuard:
        def __init__(self,label,acquire_fail=False,close_fail=False):self.label=label;self.acquire_fail=acquire_fail;self.close_fail=close_fail;self.calls=[]
        def acquire(self,refs):
            self.calls.append('acquire')
            if self.acquire_fail:raise OSError('PURE_'+self.label+'_ACQUIRE_FAILURE')
        def get_buffer(self,p):return b'PURE_BUFFER'
        def close(self):
            self.calls.append('close')
            if self.close_fail:raise OSError('PURE_'+self.label+'_CLOSE_FAILURE')
            return dict(closed=True,errors=[],retained_handles_count=0)
    class FakePath:
        def __init__(self,value='MEMORY',mkdir_fail=False):self.value=str(value);self.mkdir_fail=mkdir_fail
        def __truediv__(self,part):return FakePath(self.value+'/'+str(part),self.mkdir_fail)
        def __str__(self):return self.value
        def exists(self):return False
        def mkdir(self,**kw):
            if self.mkdir_fail:raise OSError('PURE_SCRATCH_MKDIR_FAILURE')
        def open(self,*args,**kw):return self
        def __enter__(self):return self
        def __exit__(self,*args):return False
    init_start=next(i for i,x in enumerate(vm.body) if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='runtime_guard' for t in x.targets))
    vi=vm.body.index(vtry);initial=vm.body[init_start:vi];tail=vm.body[vi+1:]
    # Keep exact guarded prefix through first scratch mkdir; no real Path,
    # module loader, runtime helper or executable is used in these controls.
    prefix=[]
    for x in vtry.body:
        prefix.append(x)
        if isinstance(x,ast.For) and isinstance(x.target,ast.Name) and x.target.id=='sub':break
    for failure in ['input','runtime','scratch']:
        ig=FakeGuard('INPUT',acquire_fail=failure=='input');rg=FakeGuard('RUNTIME',acquire_fail=failure=='runtime');saved={}
        def recorder(name,value):saved[name]=copy.deepcopy(value);return dict(path='MEMORY/'+name,sha256='0'*64,bytes=1)
        fakehelper=types.SimpleNamespace(runtime_resource_paths=lambda:[])
        sc=dict(input_guard=ig,inputs=[],gm=types.SimpleNamespace(SourceReadGuard=lambda **kw:rg),module=lambda *a:fakehelper,hp=dict(path='MEMORY'),unique=lambda x:x,pin=lambda p:dict(path=str(p)),Path=lambda p:FakePath(p,mkdir_fail=failure=='scratch'),C=C,before={},main_before={},sources={},parents=[],terminals=set(),expected=[],preparation_cleanup_ref={},save=recorder,json=json,print=lambda *a,**k:None)
        t=copy.deepcopy(vtry);t.body=copy.deepcopy(prefix)
        result=capture(compile_probe([*initial,t,*tail],sc));closed=saved.get('validation.closed.json')
        check('early_'+failure+'_has_original_error_closed_receipt',result['type']=='RuntimeError' and closed is not None and closed['status']=='FAILED_RESTORED21_V2_ACTUAL_CLOSED_NO_COMPONENT_ACCEPTANCE' and 'PURE_' in closed['error'] and closed['all_owned_jobs_closed'] is False and closed['native_qualification_accepted'] is False)
        check('early_'+failure+'_all_acquired_guards_closed',ig.calls[-1]=='close' and (failure=='input' or rg.calls[-1]=='close') and 'validation.cleanup.attempts.json' in saved)
        observations.append(dict(kind='early_failure',failure=failure,result=result,closed=closed,guard_calls=dict(input=ig.calls,runtime=rg.calls)))
    # Failed per-guard receipts and even the aggregate attempts receipt cannot
    # prevent later close attempts. Storage persistence is not invented.
    for stage,block in [('prepare',ptry),('validate',vtry)]:
        for fail_attempts in [False,True]:
            guards=[FakeGuard(str(i),close_fail=i==0) for i in range(2 if stage=='prepare' else 6)];saved={};attempted=[];printed=[]
            def recorder(name,value):
                attempted.append(name)
                if len(attempted)==1 or fail_attempts and name.endswith('.attempts.json'):raise OSError('PURE_RECEIPT_STORAGE_FAILURE')
                saved[name]=copy.deepcopy(value);return dict(path='MEMORY/'+name)
            sc=dict(save=recorder,json=json,print=lambda *a,**k:printed.append(a),jobs=[])
            if stage=='prepare':sc.update(runtime_guard=guards[0],guard=guards[1])
            else:sc.update(zip(['binary_guard','compiler_guard','evidence_guard','candidate_guard','runtime_guard','input_guard'],guards))
            init=ast.parse('cleanup_refs=[]\ncleanup_errors=[]\ncleanup_ok=True\nattempts_ref=None\nguard_cleanup_refs=[]\nguard_cleanup_errors=[]\nall_guards_closed=True\ncleanup_attempts_ref=None').body
            ret=ast.parse('return locals()').body
            state=compile_probe([*init,*block.finalbody,*ret],sc)()
            key='cleanup_errors' if stage=='prepare' else 'guard_cleanup_errors';flag='cleanup_ok' if stage=='prepare' else 'all_guards_closed'
            check('cleanup_all_close_despite_storage_'+stage+str(fail_attempts),all(g.calls==['close'] for g in guards) and state[flag] is False and len(state[key])==(3 if fail_attempts else 2))
            check('cleanup_attempts_observed_or_error_printed_'+stage+str(fail_attempts),any(n.endswith('.attempts.json') for n in attempted) and (bool(printed) if fail_attempts else any(n.endswith('.attempts.json') for n in saved)))
            observations.append(dict(kind='cleanup_failure',stage=stage,aggregate_save_fails=fail_attempts,close_calls=[g.calls for g in guards],attempted_receipts=attempted,errors=state[key],success_flag=state[flag],printed_error=printed))
    # Failed OwnedJob results are recorded before assert. This runs only the
    # nested invoke function with memory-backed file/context objects.
    for stage,block in [('prepare',ptry),('validate',vtry)]:
        invoke=next(x for x in block.body if isinstance(x,ast.FunctionDef) and x.name=='invoke')
        for raises in [False,True]:
            inv=[];jobs=[];saved={}
            def run_owned(*a,**kw):
                if raises:raise OSError('PURE_OWNED_JOB_FAILURE')
                return dict(actual_exit=1,timed_out=False,error='PURE_UNCONFIRMED_JOB',job_cleanup=dict(errors=['PURE_CLOSE_ERROR'],active_processes_last_observed=1),owned_child_pid=1,creation_time_100ns=2)
            def recorder(name,value):saved[name]=copy.deepcopy(value);return dict(path='MEMORY/'+name)
            sc=dict(T=FakePath(),R=FakePath(),O=FakePath(),env={},helper=types.SimpleNamespace(run_owned=run_owned),save=recorder,pin=lambda p:dict(path=str(p)),invocations=inv,jobs=jobs,json=json,print=lambda *a,**k:None)
            exec(compile(ast.Module(body=[invoke],type_ignores=[]),'<pure_owned_job_invocation>','exec'),sc)
            result=capture(lambda:sc['invoke']('failed-job',['MEMORY'],1))
            check('failed_job_ledger_'+stage+str(raises),result['type']=='AssertionError' and len(inv)==len(jobs)==1 and jobs[0]['closed'] is False and len(saved)==1)
            observations.append(dict(kind='failed_job',stage=stage,helper_raises=raises,result=result,jobs=jobs,invocation=saved))
    roster=json.loads(read(C['exact_source_roster']));old=json.loads(read(C['h20_source_overlay']))['sources'];new=json.loads(read(C['a21_v2_overlay']))['files']
    check('same_exact63_roster',len(roster['sources'])==63 and roster['sources']=={**old,**new} and C['exact_source_roster']==oldC['exact_source_roster'])
    check('source63_pins_freshly_verified',all(read(r)==guard.get_buffer(str(Path(r['path']).resolve())) for r in roster['sources'].values()))
    check('nonGo_and_authority_paths_preserved',all(any(p.startswith(k) for p in roster['sources']) for k in ['apps/control/','ops/supervisor/','internal/recoveryauthority/','migrations/sqlite/']))
    testr=json.loads(Path(C['a21_v2_source_handoff']['path']).with_name('test-roster.json').read_bytes())
    check('unchanged_9_plus4_13_roster',len(testr['parent_tests'])==9 and len(testr['drift_subtests'])==4 and testr['planned_test2json_unique_runs']==13 and C['expected_unique_test_runs']==13)
    validator=texts['validate_root_actual.py'];prepare=texts['prepare_root_actual.py']
    check('prepare_ready_after_all_attempts',prepare.index("ready = save('isolation.ready.json'")>prepare.index('assert len(cleanup_refs) == 2 and cleanup_ok and not cleanup_errors and attempts_ref is not None'))
    check('validator_prepare_attempts_pinned',all(t in validator for t in ["exact(preparation_cleanup['attempts_ref'])","preparation_attempts['guard_refs'] == preparation_cleanup['guard_refs']","preparation_attempts['all_guards_closed'] is True and not preparation_attempts['errors']","preparation_attempts_ref,"]))
    check('13_development_pass_remains_partial',all(t in validator for t in ['DEVELOPMENT_TESTS_13_ACTUAL_PASS_COMPONENT_PARTIAL_NATIVE_QUALIFICATION_OPEN',"'native_qualification_accepted': False","'component_validation_accepted': False","'descendant_test_binary_exit': None"]))
    check('compiler_export_module_closure_preserved',all(t in validator for t in ["'list', '-export', '-test', '-deps', '-compiled'","go_module_info.get('GoMod')","pkg.get('Export')","'GOCACHE': str(scratch / 'gocache')",'*module_manifests.values(), *compiler_tools, go, inventory_ref']))
    check('CP_OW_positive_int_and_four_vector_gates_preserved',all(all(t in text for t in ['type(checkpoint_revision) is int and checkpoint_revision > 0 and checkpoint_revision == int(values[2])','type(ownership_revision) is int and ownership_revision > 0']) for text in [validator,prepare]) and "isolated['canonical_refs'] == expected" in validator)
    failure=json.loads(read(h['original_failure_950_ref']));check('950_is_source_python1_not_native',failure['ordinal_assigned_by_root']==950 and failure['source_python_exit']==1 and failure['tools_exec_command_result']['exit_code'] is None and failure['product_native_exit'] is None and failure['Root_Git_Go_SQL_native_product_CLI_model_executed'] is False)
    check('all_held_inputs_unchanged',all(read(r)==guard.get_buffer(r['path']) for r in refs.values()))
finally:
    cleanup=guard.close();save('source-guard.cleanup.actual.json',cleanup)
check('actual_review_guard_closed',cleanup['closed'] and cleanup['retained_handles_count']==0 and not cleanup['errors'] and cleanup['verification']=='PASSED')
save('checks.json',dict(count=len(checks),checks=checks,prior_v2_410_checks_rerun=False,author_v3_21_checks_rerun=False,actual_caller_executed=False))
save('pure-control-observations.json',observations);save('verified-input-pins.json',list(refs.values()))
root_contract=dict(schema='researchos.a21-v3-independent-root-execution-guidance.v1',source_handoff_ref=hr,source_manifest_ref=mr,review_status='SOURCE_ACCEPTED_FOR_ROOT_DEVELOPMENT_TESTS_ONLY',caller_does_not_parse_RootScope_or_verify_owner_fields=True,external_root_scope_requirements=['Root records the exact source and independent-review HDF/MF plus prepare/validator/contract/roster pins before execution.','Root records the current W05 execution owner in the canonical governance schema; this caller checks OW revision/pin but does not enforce owner identity.','Capture one current HEAD and ordered CP/OW/SS/commands vector after external authorization; keep the same vector through both stages.','Authorize only the fixed candidate, private environment and two receipt outputs below; no Main adoption, formal dispatcher, product trial or model execution.'],prepare_argv=C['prepare_argv'],validate_argv=C['validate_argv'],checkpoint_revision_rule='positive type-int, equals explicit Root argument',ownership_revision_rule='positive type-int, exact OW SHA/bytes; no separate OW revision CLI argument',canonical_order=C['four_exact_current_canonical_refs'],worktree=C['worktree'],environment=C['environment'],isolation_output=C['isolation_output'],validation_output=C['validation_output'],stage1_required_outputs=['isolation.ready.json','isolation.cleanup.closed.json','isolation.cleanup.attempts.json','runtime-source-guard.cleanup.actual.json','input-source-guard.cleanup.actual.json'],stage2_required_outputs=['validation.closed.json','validation.cleanup.attempts.json','actual-tagged-compiler-input-inventory.json','formatted.source-members.json','source-overlay.json','typed-evidence-inventory.json','restored21-v2-nine-parent-jsonl.invocation.json','restored21-v2-nine-parent-jsonl.stdout.raw','restored21-v2-nine-parent-jsonl.stderr.raw'],stage2_ready_pin_rule='append stage1 isolation.ready SHA256 and bytes to the identical ten Root arguments',max_qualification='DEVELOPMENT_TESTS_13_ACTUAL_PASS_COMPONENT_PARTIAL_NATIVE_QUALIFICATION_OPEN',full_native_gate='OPEN: exact typed descendant identity, raw streams, exit and closure corpus plus independent qualification are not supplied by selected tests',formal_case_accepted_delta=0)
save('root-execution-guidance.json',root_contract)
decision=dict(schema='researchos.a21-v3-runtime-caller-independent-source-decision.v1',actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR',source_author=False,prior_v2_review_author=True,status='SOURCE_ACCEPTED_FOR_ROOT_DEVELOPMENT_TESTS_ONLY',source_handoff_ref=hr,source_manifest_ref=mr,prepare_ref=pin(N/'prepare_root_actual.py'),validator_ref=pin(N/'validate_root_actual.py'),contract_ref=h['contract_ref'],exact_roster_ref=C['exact_source_roster'],resolved_findings=['A21V2CALL-01','A21V2CALL-02','A21V2CALL-03'],findings=[],new_independent_check_count=len(checks),prior_v2_410_checks_rerun=False,author_v3_21_checks_rerun=False,actual_test_count=0,expected_parent_count=9,expected_leaf_count=4,expected_unique_test_runs=13,maximum_future_qualification=root_contract['max_qualification'],native_qualification='OPEN',real21_22_program_provenance='OPEN',public_late_failure_no_publication='OPEN',B='OPEN',Owner='OPEN',overall20to24='OPEN',parent_acceptance=False,formal_acceptance=False,formal_case_accepted_delta=0,actual_execution_grant=False,new_original_failures=[],prior_source_failure_950_ref=h['original_failure_950_ref'],reviewed_at=datetime.now(timezone.utc).isoformat())
save('source-decision.json',decision)
report='A21 caller v3 独立 Source 审查通过，仅接受 Root 后续开发测试。v2 的两个 P1 和一个 P2 均由新纯 AST/内存控制验证修复：loader 调用可达；input/runtime acquisition 与 scratch mkdir 失败均保留原错误并产出 failed validation.closed；每个 guard close 与回执 persistence 异常独立处理，aggregate attempts 无法落盘时仍完成全部 close 并打印错误。失败 Owned Job 在拒绝前进入 ledger。\n\n完整三文件 diff/byte inverse、新 Source pins、复用的63文件 roster、工具链/编译 export/module/private-cache 声明与9+4选择范围核对。没有重跑旧410检查或作者21检查；本包只报告本次新检查计数。真实SourceReadGuard关闭且输入未变；未运行 caller/Git/Go/compiler/SQL/native/product CLI/model，未写 Main/Canon/旧Source。950保持 Source Python1、outer未知NULL、Native NULL；本次无新增工具失败。\n\n13 PASS至多PARTIAL，Native qualification、真实21/22程序、public late failure、B、Owner、20→24、parent与Formal保持OPEN/未接受。Root须另行记录精确Source/独审pins和外层scope/owner授权；caller不解析RootScope或核验owner身份。两阶段使用相同HEAD+四Canon向量与CP revision，第二阶段追加实际ready SHA/bytes。具体路径与输出列于root-execution-guidance.json。\n'
with (O/'REPORT.md').open('x',encoding='utf-8') as f:f.write(report)
members=[pin(p) for p in sorted(O.iterdir()) if p.is_file()]
mref=save('MF.json',dict(schema='researchos.a21-v3-independent-source-manifest.v1',members=members,source_handoff_ref=hr,source_manifest_ref=mr))
href=save('HDF.json',dict(schema='researchos.a21-v3-independent-source-review.v1',actor_id=ACTOR,status=decision['status'],manifest_ref=mref,source_decision_ref=pin(O/'source-decision.json'),source_handoff_ref=hr,source_manifest_ref=mr,root_execution_guidance_ref=pin(O/'root-execution-guidance.json'),resolved_findings=decision['resolved_findings'],P1_findings=0,P2_findings=0,new_independent_checks=len(checks),held_inputs=len(refs),guard_cleanup_ref=pin(O/'source-guard.cleanup.actual.json'),all_acquired_guards_closed=True,actual_test_count=0,actual_caller_executed=False,Main_Canon_old_Source_written=False,native_qualification='OPEN',formal_case_accepted_delta=0,formal_acceptance=False,execution_grant=False,new_original_failures=[],STOP=True,FINAL=True))
for r in members+[mref,href]:read(r)
print(json.dumps(dict(HDF=href,MF=mref,decision=pin(O/'source-decision.json'),root_guidance=pin(O/'root-execution-guidance.json'),new_checks=len(checks),held_inputs=len(refs)),ensure_ascii=False))
