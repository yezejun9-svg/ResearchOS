"""Task100 non-author Source review. Never invoke any subject CLI or stage."""
import ast,copy,hashlib,json,os,re,sys,types,traceback
from datetime import datetime,timezone
from pathlib import Path
Q=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os')
V=R/'execution/v2.4'
ROOT='codex:/root'
AUTHOR='codex:/root/attach_restore_independent_review'
ACTOR='codex:/root/backup_regression_resources'
THREAD='01a11cee-bf59-7a01-be0e-9f799f9b1084'
ROOT_THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT=r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl'
AUTHOR_AUDIT={'path':str(V/'receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009/w09.nf5-source-author.actual-audit.root.json'),
 'sha256':'a0bfb28e35ef31c1cca7a04eff6233b103319524a2df31cc18ca9fcfc07a4e0b','bytes':1118}
LIVE={str(V/(name+'.json')).casefold()for name in ('checkpoint','path_ownership','step_state','commands')}
CHECKS=[]
USED=[]
def encoded(v):return (json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
def save(name,v):
    with (Q/name).open('xb')as f:f.write(encoded(v))
def ref(p):
    p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def read(r):
    if type(r) is not dict or set(r)!={'path','sha256','bytes'}:raise ValueError('REF_SHAPE')
    if str(Path(r['path'])).casefold()in LIVE:raise ValueError('LIVE_CANON_FORBIDDEN')
    p=Path(r['path']);raw=p.read_bytes()
    if ref(p)!={**r,'path':str(p)}:raise ValueError('INPUT_PIN_DRIFT:'+str(p))
    USED.append(r);return raw
def doc(r):return json.loads(read(r))
def check(name,value,evidence=None):
    CHECKS.append(dict(name=name,passed=bool(value),evidence=evidence))
def refs_in(value):
    if type(value)is dict:
        if set(value)=={'path','sha256','bytes'}:yield value
        else:
            for v in value.values():yield from refs_in(v)
    elif type(value)is list:
        for v in value:yield from refs_in(v)
def canonical(refs):
    out={}
    for r in refs:
        k=str(Path(r['path'])).casefold()
        if k in LIVE:continue
        if k in out and (r['sha256'],r['bytes'])!=(out[k]['sha256'],out[k]['bytes']):raise ValueError('CONFLICTING_RESOURCE_PIN:'+k)
        out[k]={**r,'path':str(Path(r['path']))}
    return list(out.values())
def ast_functions(raw,names,globals_):
    tree=ast.parse(raw)
    nodes=[x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name in names]
    if {x.name for x in nodes}!=set(names):raise ValueError('AST_REQUIRED_FUNCTIONS')
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'<exact-reviewed-Source-functions>','exec'),globals_)
    return tree
def function_text(raw,name):
    tree=ast.parse(raw)
    node=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name==name)
    return ast.get_source_segment(raw.decode('utf-8'),node),dict(line=node.lineno,end_line=node.end_lineno)
def pins_package(href):
    h=doc(href);mref=h['manifest_ref'];m=doc(mref)
    home=Path(href['path']).parent;members=m['members']
    ok=len(members)==len({str(Path(x['path'])).casefold()for x in members})
    ok=ok and all(Path(x['path']).is_relative_to(home)for x in members)
    for r in members:read(r)
    return h,m,mref,ok
def main():
    shapes=json.loads((Q/'input-shapes.json').read_bytes())
    nh,nm,nmf,nok=pins_package(shapes['producer_hdf_ref'])
    sh,sm,smf,sok=pins_package(shapes['registrar_hdf_ref'])
    check('producer_local_manifest_exact',nok,dict(member_count=len(nm['members'])))
    check('registrar_local_manifest_exact',sok,dict(member_count=len(sm['members'])))
    choice=doc(nh['source_choice_ref']);common=choice['common'];bp=doc(nh['compiler_blueprint_ref'])
    nc=doc(nh['calling_contract_ref']);sc=doc(sh['contract_ref']);pins=doc(sh['input_pins_ref'])
    runtime_raw=read(nh['runtime_ref']);caller_raw=read(sh['caller_ref']);core_raw=read(sh['core_ref'])
    runtime=runtime_raw.decode('utf-8');caller=caller_raw.decode('utf-8');core=core_raw.decode('utf-8')
    for r in (nh['runtime_ref'],nh['overrides_ref'],nh['launcher_ref'],nh['prepare_caller_ref'],nh['producer_caller_ref'],sh['caller_ref'],sh['core_ref']):
        compile(read(r),r['path'],'exec')
    check('seven_changed_Source_files_compile_as_Python',True)
    inverse=[]
    delta=doc(nh['source_delta_ref'])
    for edit in delta['source_edits']:
        base=read(edit['base_ref']);candidate=read(edit['candidate_ref']);text=candidate.decode('utf-8');app=edit['appended']
        ok=not app or text.endswith(app)
        if app and ok:text=text[:-len(app)]
        for item in reversed(edit['replacements']):
            ok=ok and text.count(item['after'])==item['count']
            text=text.replace(item['after'],item['before'])
        restored=text.encode('utf-8');ok=ok and restored==base
        item=dict(file=edit['file'],base_ref=edit['base_ref'],candidate_ref=edit['candidate_ref'],restored_sha256=hashlib.sha256(restored).hexdigest(),exact=ok)
        inverse.append(item);check('producer_inverse_'+edit['file'],ok,item)
    sdelta=doc(sh['source_delta_ref'])
    for edit in sdelta['source_deltas']:
        base=read(edit['base_ref']);candidate=read(edit['candidate_ref']);text=candidate.decode('utf-8');ok=True
        for item in reversed(edit['inverse_edits']):
            start,end=item['new_start'],item['new_end']
            ok=ok and text[start:end]==item['after']
            text=text[:start]+item['before']+text[end:]
        restored=text.encode('utf-8');ok=ok and restored==base
        item=dict(file=edit['file'],base_ref=edit['base_ref'],candidate_ref=edit['candidate_ref'],restored_sha256=hashlib.sha256(restored).hexdigest(),offset_units='verified Unicode Source spans; restored original UTF-8 bytes',exact=ok)
        inverse.append(item);check('registrar_inverse_'+edit['file'],ok,item)
    prior=doc(nh['prior_source_hdf_ref'])
    check('NF4_to_NF5_Source21_and_blueprint_byte_unchanged',nh['source21']==prior['source21']and nh['compiler_blueprint_ref']['sha256']==prior['compiler_blueprint_ref']['sha256'])
    testrefs=[r for r in common['source21']if Path(r['path'])==R/'internal/domain/retrieval_test.go']
    check('current_1254_test_in_Source21_and_3905_blueprint',len(common['source21'])==21 and len(testrefs)==1 and testrefs[0]['sha256']=='1254f8c7524638cac6bee492fe7d4daf685722250779f86e36e97b0e7a9f1141'and testrefs[0]in bp['stable_input_refs'])
    routes=choice['selectors'];c19=routes['C19']
    router_raw=read(next(r for r in common['source21']if Path(r['path'])==R/'ops/ci/w09_formal_router.py'))
    router_tree=ast.parse(router_raw);selected_node=next(x for x in router_tree.body if isinstance(x,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='SELECTED'for t in x.targets))
    selected=ast.literal_eval(selected_node.value)
    check('C19_true_two_Main_tests_five_IDs',c19['selected_tests']==['TestW09C19ExplicitOriginAndUnknown','TestW09C19ChainInvalidation']and c19['expected_native_ids']==['C19-01','C19-02','C19-03','C19-04','C19-05']and tuple(c19['selected_tests'])==selected[('test.retrieval','W09','','C19')])
    check('four_fresh_generation_choices',set(routes)=={'W09-G01','W09-G02','A06','C19'}and len({x['run_id']for x in routes.values()})==4 and common['generation']=='fullw09-20261010-05')
    scratch_parent=Path('C:/Users/yqyyds/.researchos/w09-native-v5')
    absent=[]
    for key,c in routes.items():
        paths=[Path(c[k])for k in ('scratch_root','receipt_root','output_root')]
        absent.append(dict(selector=key,paths=[str(p)for p in paths],all_not_created=all(not p.exists()for p in paths)))
    check('four_one_shot_roots_not_created',all(x['all_not_created']for x in absent),absent)
    scopekeys=set(nc['scope_required_fields'])
    maker,lines=function_text(core_raw,'make_native_scopes')
    check('generation_resource_trio_bound_at_both_Scope_edges',all("'"+k+"'"in maker and "'"+k+"'"in function_text(runtime_raw,'validate_authority')[0]for k in ('generation','resource_parent_ref','resource_owner_ref','resource_audit_ref'))and set(sc['selectors'])==set(routes),lines)
    g={'Path':Path,'hashlib':hashlib,'json':json,'os':os,'re':re,'R':R,'MAX':256*1024*1024,'ROOT_ACTOR':ROOT,'ROOT_THREAD_ID':ROOT_THREAD,'ROOT_AUDIT':AUDIT}
    ast_functions(runtime_raw,{'require','decode','exact_path','raw_pin','read_ref','exact_host_peer_author','actual_audit','validate_scratch_parent','verify_directories','build_environment'},g)
    resource_refs=g['validate_scratch_parent'](common)
    check('actual_Root_resource_host_and_project_marker_physical_C',True,dict(resource_refs=resource_refs,resource_only=True,execution_grant=False))
    audit_refs=g['actual_audit'](AUTHOR_AUDIT,AUTHOR,shapes['producer_hdf_ref']['sha256'])
    original=doc(AUTHOR_AUDIT)['original_capture_ref'];head,meta,final=[json.loads(x)for x in read(original).splitlines()]
    body=final['payload']['content'][0]['text']
    check('real_Task97_Final_binds_both_Source_HDFs',shapes['producer_hdf_ref']['sha256']in body and shapes['registrar_hdf_ref']['sha256']in body,
        dict(audit_ref=AUTHOR_AUDIT,metadata_ordinal=meta['ordinal'],Final_ordinal=final['ordinal'],metadata_time=meta['timestamp'],Final_time=final['timestamp'],backend_author=final['payload']['author']))
    g['verify_directories'](bp)
    check('3905_compile_inputs_19_modules_51_directories',len(bp['stable_input_refs'])==3905 and len(bp['module_go_mod_refs'])==19 and len(bp['main_directory_inventory'])==51 and all(r in bp['stable_input_refs']for r in bp['module_go_mod_refs']))
    inventory_fn,inventory_lines=function_text(runtime_raw,'compiler_inventory')
    stage,stage_lines=function_text(runtime_raw,'stage')
    check('actual_go_list_export_generated_closure_held_before_producer',all(x in inventory_fn for x in ('GO_LIST_UNHELD_OR_DRIFTED_INPUT','EXPORT_NOT_PRIVATE_GOCACHE','ACTUAL_EXPORT_AND_GENERATED_INPUTS_REQUIRED','EXACT_MODULE_GOMOD_SET'))and 'private_generated_input_refs' in stage and 'private_export_refs'in stage and stage.index('compiler-input-list')<stage.index('w09-selector-main-producer'),dict(compiler=inventory_lines,stage=stage_lines))
    envs=[g['build_environment']({**common,**c})for c in routes.values()]
    check('explicit_Private_TEMP_TMP_and_empty_cache_policy',all(e['TEMP']==e['TMP'] and Path(e['TEMP']).is_relative_to(scratch_parent)and e['GOPROXY']=='off'and e['GOENV']=='off'for e in envs)and 'FRESH_PRIVATE_GOCACHE'in stage)
    prepare_branch=next(x for x in ast.walk(ast.parse(runtime_raw))if isinstance(x,ast.If)and ast.unparse(x.test)=="kind == 'prepare'")
    prepare_calls={ast.unparse(x.func)for x in ast.walk(prepare_branch)if isinstance(x,ast.Call)}
    check('prepare_branch_has_no_process_or_stage_recursion',not any('run_owned'in x or x in ('invoke','stage','subprocess.run','os.system')for x in prepare_calls),sorted(prepare_calls))
    activation,activation_lines=function_text(caller_raw,'check_or_activate');model,model_lines=function_text(caller_raw,'model')
    check('activation_excludes_CP_OW_and_TP_transform_uses_cached_full_bytes',"set(CANON[:2]) if mode=='activate' else set()"in activation and "Path(r['path']) not in excluded"in activation and "ctx['before_raw']"in activation and 'read_ref(r)'not in model and 'for p in CANON'not in model,dict(activation=activation_lines,model=model_lines))
    merge,merge_lines=function_text(core_raw,'merge_pending');changes,change_lines=function_text(core_raw,'canonical_changes')
    check('strict_contiguous_nonreset_NULL_counters_and_old_scopes_preserved',all(x in merge for x in ('type(stop) is int and stop>=start','UNKNOWN_EXITS_MUST_REMAIN_NULL','ORIGINAL_COUNTER_PREFIX_UNCHANGED','type(row.get(\'ordinal\')) is int'))and all(x in changes for x in ('OLD_SCOPE_REFS_UNCHANGED','ALL_OLD_FAILURES_UNCHANGED','OLD_NATIVE_MUST_BE_CLOSED','COMPLETE_STRUCTURAL_INVERSE','before_canonical_archive_refs=archives')),dict(merge=merge_lines,changes=change_lines))
    own,own_lines=function_text(caller_raw,'own_source')
    check('independent_schema_exact_Source_only_review_and_actual_peer_required',sc['review_schema']=='researchos.w09-nf4-registration-independent-source-decision.v1'and nc['review_schema']=='researchos.w09-four-selector-producer-independent-source-decision.v1'and 'source_decision_ref'in own and 'source_review_audit_ref'in own and 'actual_audit'in own,own_lines)
    # One actual held closure for public Source, not a product/runtime grant.
    refs=[*USED,*bp['stable_input_refs'],*common['source21'],*common['tool_refs'].values(),common['guard_ref'],common['owned_job_ref'],common['toolchain_ref'],common['identity_ref'],common['spec_manifest_ref'],AUTHOR_AUDIT,*resource_refs,*audit_refs]
    refs.extend(refs_in(pins));refs.extend(refs_in(nh));refs.extend(refs_in(sh))
    guard_ref=common['guard_ref'];guard_module=types.ModuleType('task100_exact_source_guard');guard_module.__file__=guard_ref['path']
    exec(compile(read(guard_ref),guard_ref['path'],'exec'),guard_module.__dict__)
    owned_ref=common['owned_job_ref'];owned_module=types.ModuleType('task100_metadata_owned_helper');owned_module.__file__=owned_ref['path']
    exec(compile(read(owned_ref),owned_ref['path'],'exec'),owned_module.__dict__)
    loaded=[ref(Path(p))for p in owned_module.runtime_resource_paths()]
    for mod in tuple(sys.modules.values()):
        for field in ('__file__','__cached__'):
            p=getattr(mod,field,None)
            if p and Path(p).is_file():loaded.append(ref(Path(p).resolve()))
    refs=canonical(refs+loaded+[ref(sys.executable),ref(__file__)])
    save('public-resource-manifest.json',dict(schema='researchos.w09-nf5-independent-public-resource-manifest.v1',refs=refs,loaded_runtime_refs=canonical(loaded),compiler_blueprint_ref=nh['compiler_blueprint_ref'],stable_compile_input_count=3905,Live_Canon_excluded=sorted(LIVE),Source_actor=ACTOR,source_only=True,execution_grant=False))
    guard=guard_module.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=1024*1024*1024)
    cleanup=None
    try:
        guard.acquire(refs)
        check('actual_all_public_Source_compiler_runtime_refs_held',len(guard.buffers)==len(refs),dict(unique_refs=len(refs),loaded_runtime_refs=len(canonical(loaded))))
    finally:
        cleanup=guard.close();save('SourceGuard.closed.json',cleanup)
    check('actual_SourceGuard_all_closed_zero_retained',cleanup['verification']=='PASSED'and cleanup['closed']is True and cleanup['retained_handles_count']==0 and not cleanup['errors'])
    save('exact-inverses.json',dict(schema='researchos.w09-nf5-independent-exact-Source-inverses.v1',entries=inverse,all_exact=all(x['exact']for x in inverse),Source_mutation=False))
    result=dict(schema='researchos.w09-nf5-independent-finite-review.v1',actor_id=ACTOR,Source_thread=THREAD,checks=CHECKS,passed=sum(x['passed']for x in CHECKS),failed=sum(not x['passed']for x in CHECKS),old_controls_rerun=False,actual_stage_calls=0,actual_Go=0,actual_Native=0,actual_SQL=0,actual_model=0,actual_TP=0,Main_written=False,Canon_written=False,SourceAuthor=AUTHOR,SourceAuthor_actual_audit_ref=AUTHOR_AUDIT,current_live_Canon_held=False)
    save('finite-review.json',result)
    print(json.dumps(dict(passed=result['passed'],failed=result['failed'],guards_closed=cleanup['closed'],retained_handles=cleanup['retained_handles_count'],resource_refs=len(refs),runtime_refs=len(canonical(loaded)),no_stages=True),ensure_ascii=False));return 0
if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
