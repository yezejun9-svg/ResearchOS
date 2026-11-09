"""Read-only candidate Main delta review. This never executes any producer/stage."""
from pathlib import Path
import ast, copy, difflib, hashlib, json, os, tempfile, types
R=Path(r'D:\作品集\ResearchOS\research-os')
W=R/'execution/v2.4/receipts/W09/W09-99'
D=Path(__file__).resolve().parent
P=W/'main_w09_formal_router_sequence_root/fix-20261010-01'
SEED=W/'w09_br6_actual_root/actual-20261010-01/seed-7960283ac5b549e28bfe045d7f90b59e/context-seed.json'
HELPER=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
s=types.ModuleType('receipt_support');s.__file__=str(HELPER)
exec(compile(HELPER.read_bytes(),str(HELPER),'exec'),s.__dict__);s.D=D
inventory=json.loads((D/'input-inventory.json').read_bytes())
context=json.loads(SEED.read_bytes())
refs={}
def add(ref):
    path=Path(ref['path'])
    if not path.is_absolute():path=R/path
    path=path.resolve(strict=True)
    claim=dict(path=str(path),sha256=ref['sha256'],bytes=ref.get('bytes',path.stat().st_size))
    previous=refs.get(str(path));assert previous is None or previous==claim
    refs[str(path)]=claim
for key in ('seed_ref','candidate_ref','before_ref','proposal_ref','current_Main_ref'):add(inventory[key])
for path in (__file__,HELPER,D/'input-inventory.json',D/'inspect_inputs.py'):add(s.pin(path))
for group in ('spec_files','source_files','input_files','lock_files','tool_files'):
    for ref in context['version_vector'][group]:add(ref)
reports={};modes={}
for row in context['registered_commands']:
    for key in ('native_report_ref','native_tool_run_ref','mode_decision_ref'):add(row[key])
    path=R/row['native_report_ref']['path']
    report=reports.setdefault(str(path),json.loads(path.read_bytes()))
    tool=json.loads((R/row['native_tool_run_ref']['path']).read_bytes())
    for stream_key,sha_key in (('stdout_ref','stdout_sha256'),('stderr_ref','stderr_sha256')):
        add(dict(path=tool[stream_key],sha256=tool[sha_key]))
    for ref in report['owned_export']['members']:add(ref)
    mode=json.loads((R/row['mode_decision_ref']['path']).read_bytes());modes[row['mode_decision_ref']['path']]=mode
    for key in ('independent_review_ref','host_witness','junction_witness'):
        if mode.get(key) is not None:add(mode[key])
locked=json.loads((R/'execution/toolchains/locked.json').read_bytes())
add(dict(path=locked['tools']['go']['path'],sha256=locked['tools']['go']['sha256']))
assert not any(Path(ref['path']).name in ('checkpoint.json','path_ownership.json','step_state.json') for ref in refs.values())
s.write('guard-inputs.json',dict(refs=list(refs.values()),live_CP_OW_SS_refs=0,private_key_refs=0,
    candidate_only=True,resource_inventory_built_from_actual_seed_and_report_members=True))
g=s.guard();checks=[];actual_rows=[];failure=None;reader=None
temp_saved={key:os.environ.get(key) for key in ('TEMP','TMP')};cached_temp=tempfile.tempdir
def check(name,value,detail=None):
    checks.append(dict(name=name,passed=bool(value),detail=detail))
    if not value:raise ValueError(name)
try:
    g.acquire(list(refs.values()))
    old=g.get_buffer(str(P/'formal_profile_w09.before.py'))
    candidate=g.get_buffer(str(P/'formal_profile_w09.candidate.py'))
    main=g.get_buffer(str(R/'execution/v2.4/formal_profile_w09.py'))
    check('given_exact_source_pins',
        hashlib.sha256(old).hexdigest()=='d44500a9fceb9633109884f3860390e5d10bc877b4f3a66986ffd6e2038dc35f' and len(old)==71397
        and hashlib.sha256(candidate).hexdigest()=='1e04865beef37fdbffa06d649d072721d7b6eb0ef5e525d87bb867da414e4087' and len(candidate)==71403
        and inventory['seed_ref']['sha256']=='fb0ad4286940e17723ba4a12df23dddc05a1dfb9cf4a3a7db1c112dc875b3257')
    check('current_Main_still_exact_before',main==old)
    before_line=b'api.exact_ids(router["FORMAL"][route], IDS[key], "router formal IDs")'
    after_line=b'api.exact_ids(list(router["FORMAL"][route]), IDS[key], "router formal IDs")'
    check('single_line_delta_and_full_byte_inverse',old.count(before_line)==1 and candidate.count(after_line)==1
        and old.replace(before_line,after_line)==candidate and candidate.replace(after_line,before_line)==old)
    a=ast.parse(old);b=ast.parse(candidate)
    af={node.name:node for node in a.body if isinstance(node,(ast.FunctionDef,ast.ClassDef))}
    bf={node.name:node for node in b.body if isinstance(node,(ast.FunctionDef,ast.ClassDef))}
    changed=[name for name in af if ast.dump(af[name],include_attributes=False)!=ast.dump(bf[name],include_attributes=False)]
    check('only_native_function_AST_changes',set(af)==set(bf) and changed==['_native'])
    restored=ast.parse(candidate.replace(after_line,before_line))
    check('complete_module_AST_inverse',ast.dump(a,include_attributes=False)==ast.dump(restored,include_attributes=False))
    diff=''.join(difflib.unified_diff(old.decode().splitlines(keepends=True),candidate.decode().splitlines(keepends=True),
        fromfile=str(P/'formal_profile_w09.before.py'),tofile=str(P/'formal_profile_w09.candidate.py')))
    with (D/'independent-candidate.diff').open('xb') as f:f.write(diff.encode())
    api=s.inert(R/'execution/v2.4/formal_case_index.py',g.get_buffer(str(R/'execution/v2.4/formal_case_index.py')))
    profile=s.inert(P/'formal_profile_w09.candidate.py',candidate)
    reader=api.Reader(R);reader.w09_owned_inventories=[];reader.w09_audit_ranges=[]
    facade=api._profile_api()
    pinned=profile._vector(facade,reader,context)
    check('real_seed_vector_keeps_old_current_Main_pin',pinned[reader.path('execution/v2.4/formal_profile_w09.py')]==hashlib.sha256(old).hexdigest())
    router=profile._router_contract(facade,reader,pinned)
    producer_sources=profile._producer_sources(facade,reader,pinned)
    check('profile_not_in_Native_Source21_and_exact_inventory_retained',len(producer_sources)==21
        and 'execution/v2.4/formal_profile_w09.py' not in producer_sources)
    closure=profile._trusted_closure(facade,reader,pinned)
    routes=context['registered_commands']
    check('six_existing_Mode_refs_four_existing_Native_runs',len(routes)==6
        and len({row['mode_decision_ref']['path'] for row in routes})==6
        and len({row['native_report_ref']['path'] for row in routes})==4
        and {(row['command_key'],row['check_id'],row['case_id']) for row in routes}==set(profile.ROUTES))
    for row in routes:
        route=(row['command_key'],'W09',row['check_id'],row['case_id']);key=row['check_id'] or row['case_id']
        ident='|'.join(route)
        formal=router['FORMAL'][route]
        check('trusted_FORMAL_tuple_'+ident,type(formal) is tuple)
        api.exact_ids(list(formal),profile.IDS[key],'candidate route')
        check('positive_exact_ids_'+ident,True)
        for label,value,expected in (
            ('missing',list(formal)[:-1],'TYPE_ARRAY' if len(formal)==1 else 'ID_SET'),
            ('duplicate',list(formal)+[formal[0]],'DUPLICATE_ID'),
            ('wrong_id',list(formal)[:-1]+['W09-INDEPENDENT-INVALID-ID'],'ID_SET')):
            error=None
            try:api.exact_ids(value,profile.IDS[key],'candidate route negative Source fixture')
            except api.InvalidEvidence as exc:error=exc.code
            check(label+'_rejected_'+ident,error==expected,dict(actual_error=error,Source_fixture_only=True))
    os.environ['TEMP']=os.environ['TMP']=r'C:\Users\yqyyds\.researchos\w09-native-v5'
    tempfile.tempdir=None
    check('exact_existing_Readonly_Main_temp_parent',tempfile.gettempdir()==r'C:\Users\yqyyds\.researchos\w09-native-v5')
    for row in routes:
        report,native,mode,clocks=profile._native(facade,reader,row,closure,router,pinned,producer_sources)
        actual=dict(route=[row['command_key'],'W09',row['check_id'],row['case_id']],
            report_ref=row['native_report_ref'],tool_ref=row['native_tool_run_ref'],mode_decision_ref=row['mode_decision_ref'],
            run_id=report['run_id'],Native_original_exit=report['exit_code'],mode=mode,
            native_started_at=report['started_at'],native_ended_at=report['ended_at'],
            Main_readonly_gate='CANDIDATE_NATIVE_PASSED',candidate_only=True,actual_new_Native_calls=0)
        actual_rows.append(actual)
        check('candidate_real_native_gate_'+'|'.join(actual['route']),mode['formal_authority'] is False)
    reader.finish()
    check('actual_reader_compare_after_read',True,dict(unique_read_hashes=len(reader.read_hashes),owned_inventories=len(reader.w09_owned_inventories)))
    check('all_four_Native_Source21_current_and_no_formal_profile_repin_required',
        len({item['run_id'] for item in actual_rows})==4 and all(item['Native_original_exit']==0 for item in actual_rows))
except BaseException as exc:
    failure=dict(type=type(exc).__name__,message=str(exc),code=getattr(exc,'code',None));raise
finally:
    for key,value in temp_saved.items():
        if value is None:os.environ.pop(key,None)
        else:os.environ[key]=value
    tempfile.tempdir=cached_temp
    guard_ref=s.write('source-guard.closed.json',g.close())
    result_ref=s.write('independent-review-result.json',dict(checks=checks,count=len(checks),passed=sum(item['passed'] for item in checks),
        failure=failure,actual_candidate_native_rows=actual_rows,source_guard_ref=guard_ref,held_count=len(refs),
        current_Main_ref=inventory['current_Main_ref'],candidate_ref=inventory['candidate_ref'],
        seed_ref=inventory['seed_ref'],reader_hash_count=len(reader.read_hashes) if reader else None,
        candidate_only=True,Main_changed=False,Canon_changed=False,execution_grant=False,formal_acceptance=False,
        product_calls=dict(Native=0,Go=0,SQL=0,dispatcher=0,TP=0,RootStage=0,model=0)))
print(json.dumps(dict(count=len(checks),passed=sum(item['passed'] for item in checks),failure=failure,
    actual_candidate_routes=len(actual_rows),actual_candidate_runs=len({item['run_id'] for item in actual_rows}),
    source_guard_ref=guard_ref,result_ref=result_ref,candidate_only=True,Main_changed=False,formal_acceptance=False),ensure_ascii=False))
