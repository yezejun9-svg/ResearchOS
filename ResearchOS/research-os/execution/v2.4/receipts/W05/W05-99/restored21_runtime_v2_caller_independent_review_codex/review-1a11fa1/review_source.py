from pathlib import Path,PurePosixPath
import ast,copy,difflib,hashlib,json,re,symtable,types
from datetime import datetime,timezone

R=Path('D:/作品集/ResearchOS/research-os')
N=R/'execution/v2.4/receipts/W05/W05-99/restored21_session_runtime_caller_source_codex/r21v2caller-20261009-02'
O=Path(__file__).resolve().parent
ACTOR='codex:/root/native_temp_independent_review'
checks=[];examples=[]
def pin(p):
    p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(r):
    b=Path(r['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==r['sha256'] and ('bytes' not in r or len(b)==r['bytes']),r['path'];return b
def save(name,obj):
    p=O/name
    with p.open('xb') as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
    return pin(p)
def check(name,value,detail=None):
    assert value,name
    checks.append(dict(name=name,passed=True,detail=detail))
def compile_probe(nodes,scope,name='probe'):
    f=ast.FunctionDef(name=name,args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=copy.deepcopy(nodes),decorator_list=[])
    exec(compile(ast.fix_missing_locations(ast.Module(body=[f],type_ignores=[])),'<independent-memory-only-AST-probe>','exec'),scope)
    return scope[name]
def capture(fn):
    try:fn()
    except BaseException as e:return dict(exception=type(e).__name__,message=str(e))
    return dict(exception=None,message=None)
hr=dict(path=str(N/'HDF.json'),sha256='2d172df967d25c2a0d502be1b44fb37a205224fa49b6fb7a7eafe44b4e246850',bytes=4432)
mr=dict(path=str(N/'MF.json'),sha256='a5b2cb8fab4da322d15df9a37e7daf9344459cdbe995215186122004c574b90d',bytes=4422)
h=json.loads(read(hr));m=json.loads(read(mr));C=json.loads(read(h['contract_ref']))
check('source_manifest_pair',h['manifest_ref']==mr)
members=[{k:r[k] for k in ('path','sha256','bytes')} for r in m['members']]
for r in members:read(r);check('member_'+Path(r['path']).name,Path(r['path']).parent==N)
priorcleanup=json.loads(read(h['guard_cleanup_ref']))
refs=[{k:r[k] for k in ('path','sha256','bytes')} for r in priorcleanup['entries']]+[hr,mr,*members]
refs={str(Path(r['path']).resolve()).casefold():dict(r,path=str(Path(r['path']).resolve())) for r in refs}
gp=C['source_guard'];gm=types.ModuleType('a21v2_independent_readguard');gm.__file__=gp['path'];exec(compile(read(gp),gp['path'],'exec'),gm.__dict__)
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
try:
    guard.acquire(list(refs.values()))
    for r in refs.values():check('held_'+r['path'],guard.get_buffer(r['path'])==read(r))
    texts={name:(N/name).read_text() for name in ['prepare_root_actual.py','validate_root_actual.py','check_source.py']}
    trees={name:ast.parse(text) for name,text in texts.items()}
    vtree=trees['validate_root_actual.py'];ptree=trees['prepare_root_actual.py']
    vm=next(x for x in vtree.body if isinstance(x,ast.FunctionDef) and x.name=='main')
    pm=next(x for x in ptree.body if isinstance(x,ast.FunctionDef) and x.name=='main')
    oldN=Path(C['superseded_caller_handoff']['path']).parent
    generated=''.join(''.join(difflib.unified_diff((oldN/name).read_text().splitlines(keepends=True),(N/name).read_text().splitlines(keepends=True),fromfile='v1/'+name,tofile='v2/'+name)) for name in ['contract.json','prepare_root_actual.py','validate_root_actual.py','check_source.py'])
    check('complete_four_file_reversible_diff',generated==(N/'reversible-v1-to-v2.diff').read_text())
    old=json.loads(read(C['h20_source_overlay']))['sources'];overlay=json.loads(read(C['a21_v2_overlay']));new=overlay['files'];composed={**old,**new}
    roster=json.loads(read(C['exact_source_roster']))
    check('exact_63_roster',len(old)==61 and len(new)==5 and len(composed)==63 and roster['sources']==composed)
    check('five_A21_overlay_paths',set(new)==set(C['overlay_exact_paths']) and len(set(new)-set(old))==2)
    check('changed_and_preserved_A21_paths',set(overlay['changed_paths'])=={'internal/domain/backup_restored21_upgrade.go','internal/domain/backup.go','internal/domain/backup_restored21_upgrade_test.go'} and set(overlay['unchanged_paths'])=={'internal/domain/backup_upgrade.go','ops/backup/main.go'})
    T=Path(C['worktree'])
    pathloop=next(x for x in vm.body if isinstance(x,ast.For) and isinstance(x.target,ast.Name) and x.target.id=='name' and isinstance(x.iter,ast.Name) and x.iter.id=='sources')
    scope=dict(sources=composed,PurePosixPath=PurePosixPath,T=T)
    exec(compile(ast.Module(body=[pathloop],type_ignores=[]),'<pure63pathpredicate>','exec'),scope)
    for name,r in composed.items():read(r);check('reviewed63_'+name,True)
    check('SQL_and_non_domain_kept',all(any(k.startswith(prefix) for k in composed) for prefix in ['migrations/sqlite/','apps/control/','ops/supervisor/','internal/recoveryauthority/']))
    for bad in ['../escape.go','internal/../escape.go','C:/escape.go','internal\\bad.go','/absolute.go','internal//x.go','internal/./x.go']:
        trial=dict(sources={bad:{}},PurePosixPath=PurePosixPath,T=T)
        check('unsafe_path_rejected_'+bad,capture(lambda:exec(compile(ast.Module(body=[pathloop],type_ignores=[]),'<purebadpath>','exec'),trial))['exception']=='AssertionError')
    troster_path=Path(C['a21_v2_source_handoff']['path']).with_name('test-roster.json');troster=json.loads(troster_path.read_bytes());parents=troster['parent_tests'];leaves=troster['drift_subtests'];dp='TestRestored21RejectsForeignPartialSessionAndMissingFence';terminals=set(parents)|{dp+'/'+x for x in leaves}
    test=read(new['internal/domain/backup_restored21_upgrade_test.go']).decode()
    check('nine_parents_four_leaves_13_unique',len(parents)==len(set(parents))==9 and len(leaves)==4 and len(terminals)==13 and all('func '+p+'(' in test for p in parents))
    check('genuine_H20_fixture_to_plain21_source_route','history20Fixture(t)' in test and 'UpgradeLocal(context.Background(),prior)' in test and 'if len(before["schema_migrations"])!=21' in test and 'PUBLIC_FIXTURE_MAINTENANCE22_PROGRAM_BYTES' in test)
    check('report_disk_full_recovery_equal','Bytes(report.Recovery),Bytes(persisted.Recovery)' in test and 'got!=target' in test)
    check('source_only_old_reviews_bound',json.loads(read(C['h20_actual_review_handoff']))['status']=='COMPONENT_VALIDATION_ACCEPTED_A20_TO_PLAIN21_ONLY' and json.loads(read(C['a21_v2_review_handoff']))['status']=='SOURCE_ACCEPTED_P2_ADDRESSED_PENDING_RUNTIME_QUALIFICATION')
    vtry=next(x for x in vm.body if isinstance(x,ast.Try))
    ptry=next(x for x in pm.body if isinstance(x,ast.Try))
    # P1: exact source call and assignment retain Python lexical scoping, while
    # all filesystem/process expressions remain unreachable in this probe.
    gmcall=next(x for x in vm.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='gm' for t in x.targets))
    modassign=next(x for x in ast.walk(vm) if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='module' for t in x.targets))
    calls=[];probe_scope=dict(module=lambda *a:calls.append(a),gp=dict(path='NEVER_READ'),pkg={})
    lexical=capture(compile_probe([gmcall,modassign],probe_scope))
    symbols=next(x for x in symtable.symtable(texts['validate_root_actual.py'],'validate_root_actual.py','exec').get_children() if x.get_name()=='main')
    check('reproduced_module_local_shadow',lexical['exception']=='UnboundLocalError' and not calls and symbols.lookup('module').is_local())
    examples.append(dict(id='A21V2CALL-01',scope='Pure extracted call and assignment; no caller execution',call_line=gmcall.lineno,assignment_line=modassign.lineno,result=lexical,global_loader_calls=calls))
    class FakeGuard:
        def __init__(self,name,fail_close=False,fail_acquire=False):self.name=name;self.fail_close=fail_close;self.fail_acquire=fail_acquire;self.calls=[]
        def acquire(self,items):
            self.calls.append('acquire')
            if self.fail_acquire:raise OSError('IN_MEMORY_INPUT_PIN_DRIFT')
        def close(self):
            self.calls.append('close')
            if self.fail_close:raise OSError('IN_MEMORY_CLOSE_ERROR')
            return dict(closed=True,errors=[],retained_handles_count=0)
    # P1: input guard acquisition fails before the local closed() definition.
    # Original except/finally and post-try branch are retained as exact AST.
    cdef=next(x for x in vtry.body if isinstance(x,ast.FunctionDef) and x.name=='closed')
    early=copy.deepcopy(vtry);early.body=[copy.deepcopy(vtry.body[0]),copy.deepcopy(cdef)]
    index=vm.body.index(vtry);tail=vm.body[index+1:]
    fake=FakeGuard('input',fail_acquire=True);written=[]
    escope=dict(input_guard=fake,inputs=[],binary_guard=None,compiler_guard=None,evidence_guard=None,candidate_guard=None,runtime_guard=None,jobs=[],invocations=[],before={},main_before={},save=lambda n,v:written.append(n) or {'path':n})
    initial=ast.parse('phase_error=None\nguard_cleanup_refs=[]\nall_guards_closed=True\ndevelopment_tests_observed=False').body
    earlyresult=capture(compile_probe([*initial,early,*tail],escope))
    check('reproduced_early_failure_closed_unbound',earlyresult['exception']=='UnboundLocalError' and fake.calls==['acquire','close'] and 'validation.closed.json' not in written)
    examples.append(dict(id='A21V2CALL-02',trigger='Input pin/read-guard acquisition fails before closed is defined',definition_line=cdef.lineno,first_guard_line=vtry.body[0].lineno,result=earlyresult,guard_calls=fake.calls,saved_receipts=written))
    # Both stages do continue when close() alone throws. A receipt write error
    # is outside that handler and still prevents later close attempts.
    for stage,block in [('prepare',ptry),('validate',vtry)]:
        for fail_save in [False,True]:
            first=FakeGuard('first',fail_close=True);second=FakeGuard('second');written=[]
            def recorder(name,value):
                written.append(name)
                if fail_save:raise OSError('IN_MEMORY_CLEANUP_RECEIPT_WRITE_ERROR')
                return dict(path=name)
            sc=dict(runtime_guard=first,guard=second,binary_guard=first,compiler_guard=second,evidence_guard=None,candidate_guard=None,input_guard=None,save=recorder)
            if stage=='validate':sc['runtime_guard']=None
            init=ast.parse('cleanup_refs=[]\ncleanup_ok=True\nguard_cleanup_refs=[]\nall_guards_closed=True').body
            result=capture(compile_probe([*init,*block.finalbody],sc))
            if fail_save:
                check('reproduced_cleanup_receipt_skips_later_guard_'+stage,result['exception']=='OSError' and first.calls==['close'] and not second.calls)
                examples.append(dict(id='A21V2CALL-03',stage=stage,result=result,first_guard_calls=first.calls,later_guard_calls=second.calls,attempted_receipts=written))
            else:check('close_exception_continues_other_guard_'+stage,result['exception'] is None and first.calls==second.calls==['close'] and len(written)==2)
    # Positive integer structures and CP Root revision matching are real
    # assertions from each main(), not recreated predicates.
    for stage,main in [('prepare',pm),('validate',vm)]:
        tests=[x for x in main.body if isinstance(x,ast.Assert) and 'type(checkpoint_revision)' in ast.unparse(x) or isinstance(x,ast.Assert) and 'type(ownership_revision)' in ast.unparse(x)]
        check('two_revision_assertions_'+stage,len(tests)==2)
        for cv,ov,arg,wanted in [(367,171,'367',True),(True,171,'1',False),(367.0,171,'367',False),(0,171,'0',False),(367,True,'367',False),(367,171.0,'367',False),(367,0,'367',False),(367,171,'368',False)]:
            sc=dict(checkpoint_revision=cv,ownership_revision=ov,values=['','',''+arg])
            err=capture(lambda:exec(compile(ast.Module(body=tests,type_ignores=[]),'<pure-revision-gates>','exec'),sc))
            check('revision_'+stage+'_'+repr((cv,ov,arg)),(err['exception'] is None)==wanted)
    # Exact selected event parser handles 13 distinct runs; absence/duplication
    # never becomes 13-pass. No test executable is launched here.
    parse_loop=next(x for x in vtry.body if isinstance(x,ast.For) and isinstance(x.target,ast.Name) and x.target.id=='event')
    pi=vtry.body.index(parse_loop);gates=vtry.body[pi:pi+4]
    events=[]
    for t in sorted(terminals):events.extend([dict(Package='researchos.local/research-os/internal/domain',Test=t,Action='run'),dict(Package='researchos.local/research-os/internal/domain',Test=t,Action='pass')])
    events.append(dict(Package='researchos.local/research-os/internal/domain',Action='pass'))
    for kind,ev,wanted in [('13_unique',events,True),('missing_one',events[2:],False),('duplicate_run',[events[0],*events],False)]:
        sc=dict(events=ev,terminals=terminals,started=set(),actions={},result=dict(actual_exit=0))
        result=capture(lambda:exec(compile(ast.Module(body=gates,type_ignores=[]),'<pure13eventparser>','exec'),sc))
        check('development_event_parser_'+kind,(result['exception'] is None)==wanted)
    validator=texts['validate_root_actual.py'];prepare=texts['prepare_root_actual.py']
    check('13_PASS_must_remain_partial','DEVELOPMENT_TESTS_13_ACTUAL_PASS_COMPONENT_PARTIAL_NATIVE_QUALIFICATION_OPEN' in validator and "'native_qualification_accepted': False" in validator and "'component_validation_accepted': False" in validator and "'descendant_test_binary_exit': None" in validator)
    check('prepare_ready_after_cleanup',prepare.index("ready = save('isolation.ready.json'")>prepare.index('assert len(cleanup_refs) == 2 and cleanup_ok'))
    check('prepare_cleanup_refs_bound_by_validator',all(s in validator for s in ["exact(isolated['cleanup_closed_ref'])","len(preparation_cleanup['guard_refs']) == 2","*[exact(ref) for ref in preparation_cleanup['guard_refs']]","isolated['canonical_refs'] == expected"]))
    check('jobs_recorded_before_result_rejection',all(text.index("jobs.append(")<text.index("assert exception is None",text.index("jobs.append(")) for text in [validator,prepare]))
    check('no_empty_job_closure','bool(jobs) and len(jobs) == len(invocations)' in validator and 'jobs_closed = bool(jobs) and all(' in validator)
    check('compiler_export_module_private_cache_source',all(s in validator for s in ["'list', '-export', '-test', '-deps', '-compiled'","pkg.get('Export')","module.get('GoMod')","'GOCACHE': str(scratch / 'gocache')",'*module_manifests.values(), *compiler_tools, go, inventory_ref']))
    f948=json.loads(read(h['original_failure_948_ref']));check('948_tool_failure_not_numeric_product_exit',f948['ordinal']==948 and all(f948[k] is None for k in ['outer_exit','python_exit','native_exit','model_exit']) and f948['product_execution'] is False)
    check('Native_full_scope_still_OPEN',C['real_21_22_release_program_provenance']==C['public_late_failure_no_publication']==C['overall20to24']=='OPEN' and C['formal_acceptance'] is False)
    for r in refs.values():check('unchanged_'+r['path'],read(r)==guard.get_buffer(r['path']))
finally:
    cleanup=guard.close();save('source-guard.cleanup.actual.json',cleanup)
check('actual_read_guard_all_closed',cleanup['closed'] and cleanup['verification']=='PASSED' and cleanup['retained_handles_count']==0 and not cleanup['errors'])
findings=[
 dict(id='A21V2CALL-01',priority='P1',file=str(N/'validate_root_actual.py'),line=274,related_lines=[148,274],title='Local module assignment prevents the validation stage from starting',impact='Python binds module locally throughout main because package metadata is assigned to module at line 274. The loader call at line 148 raises UnboundLocalError before guards, compilation or the selected tests can run.',required_fix='Rename the package metadata variable or the loader without changing the reviewed source inventory; add a pure lexical/reachability regression check. Preserve this sealed v2 and issue a successor.'),
 dict(id='A21V2CALL-02',priority='P1',file=str(N/'validate_root_actual.py'),line=216,related_lines=[159,216,396],title='Early guarded failure cannot publish the failed closure receipt',impact='closed() is defined inside the guarded try after input acquisition, runtime acquisition and scratch setup. If input_guard.acquire raises, cleanup runs but the final failed branch calls an uninitialized local closed, replacing the original error with UnboundLocalError and leaving validation.closed.json absent.',required_fix='Make failure finalization available before every guarded failure and retain the original phase error, observed Job ledger and cleanup state. Exercise input/runtime acquisition failures with pure adapters.'),
 dict(id='A21V2CALL-03',priority='P2',file=str(N/'validate_root_actual.py'),line=383,related_files=[dict(file=str(N/'prepare_root_actual.py'),line=176)],title='Cleanup receipt failure still skips later guard closes',impact='Both finally loops catch guard.close errors but write each receipt outside that handler before advancing to the next guard. An ordinary receipt write OSError after the first close aborts the loop, leaving later guards without close attempts or observations.',required_fix='Complete all guard close attempts independently of receipt persistence, retain both close and persistence errors, and only then publish cleanup/failed state; do not publish ready or partial success on persistence failure.')]
save('findings.json',findings);save('counterexamples.json',examples);save('checks.json',dict(count=len(checks),checks=checks,failed_checks=0,interpretation='All independent checks confirmed review observations, including expected defect counterexamples; this is not caller acceptance'))
save('verified-input-pins.json',list(refs.values()))
decision=dict(schema='researchos.a21-v2-runtime-caller-independent-source-decision.v1',actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR',source_author=False,status='REQUEST_CHANGES',source_handoff_ref=hr,source_manifest_ref=mr,prepare_ref=pin(N/'prepare_root_actual.py'),validator_ref=pin(N/'validate_root_actual.py'),findings_ref=pin(O/'findings.json'),P1_findings=2,P2_findings=1,development_13_test_branch='BLOCKED_BY_SOURCE_DEFECTS',full_native_branch='BLOCKED_MISSING_TYPED_DESCENDANT_QUALIFICATION',scope_after_source_fixes='DEVELOPMENT_TESTS_ONLY_13_PASS_REMAINS_COMPONENT_PARTIAL_NATIVE_QUALIFICATION_OPEN',actual_test_count=0,expected_parent_count=9,expected_leaf_count=4,expected_unique_test_runs=13,composed_source_count=63,native_qualification='OPEN',real21_22_program_provenance='OPEN',public_late_failure_no_publication='OPEN',B='OPEN',Owner='OPEN',overall20to24='OPEN',formal_acceptance=False,formal_case_accepted_delta=0,execution_grant=False,new_original_failures=[],prior_failure_948_ref=h['original_failure_948_ref'],reviewed_at=datetime.now(timezone.utc).isoformat())
save('source-decision.json',decision)
report='A21 v2 Root caller 独立 Source 审查：REQUEST_CHANGES。两个 P1：validator 的局部 module 变量遮蔽加载函数，line 148 必然 UnboundLocalError；input guard 等早期异常发生在 closed() 局部定义之前，最终失败分支再次 UnboundLocalError，缺少 validation.closed 回执。一个 P2：两阶段 cleanup 回执写入失败仍会跳过后续 guard.close。均以纯 AST 和内存适配器复现，未执行 caller。\n\n已确认 v1 四文件完整 diff、精确 63 roster、SQL 与非 domain 源保留、9 parent+4 leaf、H20 UpgradeLocal plain21 fixture 路径与 report/disk 比较、正整数 revision、失败 Job 先登记及非空检查、ready 后置、prepare cleanup pins、fresh private GOCACHE 与 export/module 清单意图。13 PASS 收窄为 PARTIAL 的资格表述正确，未提供 typed descendant corpus；真实 Native、release/program provenance、public late failure、B、Owner、20→24 均 OPEN。修复 Source 之前连 development 13 tests 也不可执行。\n\n真实 SourceReadGuard 全部关闭，输入保持不变。未运行 Git/Go/compiler/SQL/native/product CLI/model，未写 Main/Canon、原 Source 或实际候选目录；本次无新增工具失败。948 保持 apply_patch 语义失败，全部 numeric exit 为 NULL。\n'
with (O/'REPORT.md').open('x',encoding='utf-8') as f:f.write(report)
members=[pin(p) for p in sorted(O.iterdir()) if p.is_file()]
mf=save('MF.json',dict(schema='researchos.a21-v2-runtime-caller-independent-source-manifest.v1',members=members,source_handoff_ref=hr,source_manifest_ref=mr))
hf=save('HDF.json',dict(schema='researchos.a21-v2-runtime-caller-independent-source-review.v1',actor_id=ACTOR,status='REQUEST_CHANGES',source_handoff_ref=hr,source_manifest_ref=mr,manifest_ref=mf,source_decision_ref=pin(O/'source-decision.json'),findings_ref=pin(O/'findings.json'),counterexamples_ref=pin(O/'counterexamples.json'),P1_findings=2,P2_findings=1,checks=len(checks),held_inputs=len(refs),guard_cleanup_ref=pin(O/'source-guard.cleanup.actual.json'),all_acquired_guards_closed=True,actual_test_count=0,actual_caller_executed=False,actual_Git_Go_compiler_SQL_native_CLI_model=False,Main_Canon_old_Source_written=False,new_original_failures=[],development_13_test_branch='BLOCKED_BY_SOURCE_DEFECTS',full_native_branch='BLOCKED_MISSING_TYPED_DESCENDANT_QUALIFICATION',formal_case_accepted_delta=0,formal_acceptance=False,execution_grant=False,STOP=True,FINAL=True))
for r in members+[mf,hf]:read(r)
print(json.dumps(dict(HDF=hf,MF=mf,decision=pin(O/'source-decision.json'),checks=len(checks),held_inputs=len(refs),P1=2,P2=1),ensure_ascii=False))
