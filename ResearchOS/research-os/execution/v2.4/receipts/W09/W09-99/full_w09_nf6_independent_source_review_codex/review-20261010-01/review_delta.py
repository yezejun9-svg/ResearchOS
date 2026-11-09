import ast,copy,datetime,hashlib,json,ntpath,sys,traceback,types
from pathlib import Path

R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W09/W09-99';Q=Path(__file__).resolve().parent
U=B/'w09_nf6_registration_independent_source_review_codex/review-20261010-01'
P=B/'full_w09_main_native_producer_source_codex/fullw09-20261010-06';G=B/'w09_nf6_root_registration_source_codex/register-20261010-01'
S=B/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
OLD=B/'full_w09_nf5_independent_source_review_codex/review-nf5-20261010-01'
MAIN_REVIEW=B/'c19_order_Main_actual_independent_review_codex/review-20261010-01'
AUTHOR='codex:/root/full_w09_source_review';REVIEWER='codex:/root/backup_regression_resources'

def norm(p):return ntpath.normcase(ntpath.normpath(str(p)))
def pin(p):
    raw=Path(p).read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def doc(p):return json.loads(Path(p).read_bytes())
def save(p,v):
    with p.open('xb')as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    return pin(p)
def walk(v):
    yield v
    if type(v)is dict:
        for x in v.values():yield from walk(x)
    elif type(v)is list:
        for x in v:yield from walk(x)
def shape(v):return type(v)is dict and set(v)=={'path','sha256','bytes'}and type(v['bytes'])is int
def load(raw,path,name):
    m=types.ModuleType(name);m.__file__=str(path);exec(compile(raw,str(path),'exec'),m.__dict__);return m
def main():
    ph=doc(P/'HDF.json');rh=doc(G/'HDF.json');pm=doc(P/'MF.json');rm=doc(G/'MF.json')
    pc=doc(ph['calling_contract_ref']['path']);rc=doc(rh['contract_ref']['path'])
    ch=doc(ph['source_choice_ref']['path']);bp=doc(ph['compiler_blueprint_ref']['path']);ins=doc(rh['input_pins_ref']['path'])
    pd=doc(ph['source_delta_ref']['path']);rd=doc(rh['source_delta_ref']['path']);old=doc(OLD/'HDF.json')
    mh=doc(MAIN_REVIEW/'HDF.json');author_witness=doc(S/'w09.nf6-conditional-producer-registrar-source.actual-audit.root.json')
    main_witness=doc(S/'w09.c19-Main-adoption-component-independent-review.actual-audit.root.json')
    refs=[pin(P/'HDF.json'),pin(P/'MF.json'),pin(G/'HDF.json'),pin(G/'MF.json'),*pm['members'],*rm['members'],
          *ch['common']['source21'],ch['common']['guard_ref'],ch['common']['owned_job_ref'],ch['common']['toolchain_ref'],
          ch['common']['identity_ref'],ch['common']['spec_manifest_ref'],*ch['common']['tool_refs'].values(),
          pin(OLD/'HDF.json'),old['producer']['hdf_ref'],old['producer']['mf_ref'],old['producer']['decision_ref'],
          old['registrar']['hdf_ref'],old['registrar']['mf_ref'],old['registrar']['decision_ref'],
          old['runtime_resource_qualification_ref'],old['calling_contract_review_ref'],
          pin(MAIN_REVIEW/'HDF.json'),mh['manifest_ref'],mh['decision_ref'],
          pin(S/'w09.nf6-conditional-producer-registrar-source.actual-audit.root.json'),author_witness['original_capture_ref'],
          pin(S/'w09.c19-Main-adoption-component-independent-review.actual-audit.root.json'),main_witness['original_capture_ref'],
          ch['common']['resource_parent_ref'],ch['common']['resource_owner_ref'],ch['common']['resource_audit_ref']]
    for delta in (pd,rd):
        for row in delta['byte_inverse_records']:refs.extend((row['before_ref'],row['after_ref']))
    # Baseline archives are historical inputs only. Do not open the live Canon pair.
    refs.extend(v for v in ins['refs'].values()if shape(v)and norm(v['path'])not in {norm(R/('execution/v2.4/'+n+'.json'))for n in ('checkpoint','path_ownership','step_state','commands')})
    refs.extend((ph['prior_source_hdf_ref'],ph['prior_source_mf_ref'],rh['prior_source_hdf_ref'],rh['prior_source_mf_ref']))
    unique={}
    for ref in refs:
        if not shape(ref):raise ValueError('EXACT_RESOURCE_REF')
        key=norm(ref['path'])
        if '\\.codex\\sessions\\'in key or '\\private\\'in key or key.endswith(('.key','owner.token')):
            raise ValueError('FORBIDDEN_PRIVATE_OR_LIVE_AUDIT')
        if key in unique and (unique[key]['sha256'],unique[key]['bytes'])!=(ref['sha256'],ref['bytes']):
            raise ValueError('CONFLICTING_CONTROL_RESOURCE_PIN')
        unique[key]=ref
    gm=load(Path(ch['common']['guard_ref']['path']).read_bytes(),ch['common']['guard_ref']['path'],'nf6_review_guard')
    guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=512*1024*1024)
    result=dict(schema='researchos.w09-nf6-independent-source-delta.v1',actor_id=REVIEWER,source_author=AUTHOR,
        controls=[],findings=[],old_successful_controls_rerun=False,compiler_3905_controls_rerun=False,
        actual_Root_stages_called=[],Native=None,Go=None,SQL=None,model=None,TP=None,dispatcher=None,
        reviewer_scope_only=True,execution_grant=False,formal_acceptance=False,Source21_qualification=False)
    primary=None
    def control(name,condition,detail):
        if not condition:result['findings'].append(dict(id=name,detail=detail))
        result['controls'].append(dict(id=name,passed=bool(condition),detail=detail))
    try:
        guard.acquire(list(unique.values()))
        def held(ref):return guard.get_buffer(ref['path'])
        def held_doc(ref):return json.loads(held(ref))
        control('NF6-CURRENT-MAIN-ADOPTION',ph['conditional_Main_after_ref']==rh['conditional_Main_after_ref']
            and ph['conditional_Main_after_ref']['sha256']=='b85fb90d9927a2427ee29a5ff756b8e7d18b0639e9a3910a7621991bc3788f11'
            and ph['conditional_Main_after_ref']['bytes']==14545
            and mh['decision']=='ACCEPTED_ACTUAL_MAIN_ADOPTION_COMPONENT_ONLY'
            and mh['actor_id']not in(AUTHOR,'codex:/root')and mh['Root_executor']=='codex:/root',
            dict(current_Main_ref=ph['conditional_Main_after_ref'],independent_actual_handoff_ref=pin(MAIN_REVIEW/'HDF.json'),independent_actual_decision_ref=mh['decision_ref'],formal_or_Runtime_grant=False))
        inverse_results=[]
        for label,delta in (('producer',pd),('registrar',rd)):
            for row in delta['byte_inverse_records']:
                before=held(row['before_ref']);after=held(row['after_ref']);built=before
                for rep in row['replacements']:
                    a=rep['before'].encode('utf-8');b=rep['after'].encode('utf-8')
                    if built.count(a)!=rep['occurrences']:raise ValueError('EXACT_REPLACEMENT_COUNT_'+row['file'])
                    built=built.replace(a,b)
                restored=after
                for rep in reversed(row['replacements']):restored=restored.replace(rep['after'].encode('utf-8'),rep['before'].encode('utf-8'))
                inverse_results.append(dict(component=label,file=row['file'],before_ref=row['before_ref'],after_ref=row['after_ref'],
                    complete_forward=built==after,complete_inverse=restored==before))
        control('NF6-EXACT-BYTE-INVERSE',all(x['complete_forward']and x['complete_inverse']for x in inverse_results),inverse_results)
        oldp=held_doc(ph['prior_source_hdf_ref']);oldchoice=doc(oldp['source_choice_ref']['path'])
        oldbp=doc(oldp['compiler_blueprint_ref']['path'])
        current21=ch['common']['source21'];old21=oldchoice['common']['source21']
        changed21=[dict(before=a,after=b)for a,b in zip(old21,current21)if a!=b]
        changedstable=[dict(before=a,after=b)for a,b in zip(oldbp['stable_input_refs'],bp['stable_input_refs'])if a!=b]
        control('NF6-SOURCE21-BLUEPRINT-DELTA',len(current21)==21 and ph['source21']==current21
            and len(changed21)==1 and changed21[0]['after']==ph['conditional_Main_after_ref']
            and len(bp['stable_input_refs'])==len(oldbp['stable_input_refs'])==3905
            and len(changedstable)==1 and changedstable[0]['after']==ph['conditional_Main_after_ref']
            and bp['module_go_mod_refs']==oldbp['module_go_mod_refs'] and len(bp['module_go_mod_refs'])==19
            and bp['main_directory_inventory']==oldbp['main_directory_inventory']
            and bp['allowed_package_roster']==oldbp['allowed_package_roster'],
            dict(source21_changed=changed21,blueprint_changed=changedstable,unchanged_3904_stable_refs_not_rehashed=True,
                 unchanged_19_module_refs_not_rehashed=True,base_runtime_qualification_ref=old['runtime_resource_qualification_ref']))
        mtree=ast.parse(held(ph['conditional_Main_after_ref']).decode('utf-8'))
        constants={}
        allowed=[]
        for node in mtree.body:
            if isinstance(node,ast.Assign)and len(node.targets)==1 and isinstance(node.targets[0],ast.Name)and node.targets[0].id in('TESTS','GROUPS','CASES'):
                allowed.append(node)
        exec(compile(ast.Module(body=allowed,type_ignores=[]),'<actual Main pure selector constants>','exec'),constants)
        selected={}
        for key,c in ch['selectors'].items():
            check,case=c['selector']['check_id'],c['selector']['case_id']
            names=constants['GROUPS'][check]if check else[name for name in constants['CASES'][case]if name in constants['TESTS']]
            if case:names=[name for name in names if name in constants['CASES'][case]]
            ids=sorted({x for name in names for x in constants['TESTS'][name][1]})
            selected[key]=dict(names=names,ids=ids,exact_names=names==c['selected_tests'],exact_ids=ids==sorted(c['expected_native_ids']))
        control('NF6-C19-AND-FOUR-SELECTOR-MAIN-ORDER',all(v['exact_names']and v['exact_ids']for v in selected.values())
            and len(selected['C19']['names'])==2 and len(selected['C19']['ids'])==5,selected)
        oldids={c['run_id']for c in oldchoice['selectors'].values()};fresh=[]
        for key,part in ch['selectors'].items():
            c={**ch['common'],**part};fresh.append(dict(selector=key,run_id=c['run_id'],
                receipt_root=c['receipt_root'],scratch_root=c['scratch_root'],output_root=c['output_root'],
                all_three_paths_not_created=not any(Path(c[x]).exists()for x in('receipt_root','scratch_root','output_root'))))
        control('NF6-DISTINCT-NEW-GENERATION-PATHS',ch['common']['generation']==ph['generation']==rh['generation']=='fullw09-20261010-06'
            and len({x['run_id']for x in fresh})==4 and all(x['run_id']not in oldids and x['all_three_paths_not_created']for x in fresh),
            dict(fresh=fresh,old_generation_preserved=True,new_scope_not_issued=True,Root_finite_leases_still_required=True))
        core=load(held(rh['core_ref']),rh['core_ref']['path'],'nf6_pure_core')
        runtime_tree=ast.parse(held(ph['runtime_ref']).decode('utf-8'));caller_tree=ast.parse(held(rh['caller_ref']).decode('utf-8'))
        fn={x.name:x for x in runtime_tree.body if isinstance(x,ast.FunctionDef)}
        auth=ast.get_source_segment(held(ph['runtime_ref']).decode('utf-8'),fn['validate_authority'])
        package=ast.get_source_segment(held(ph['runtime_ref']).decode('utf-8'),fn['package_refs'])
        control('NF6-CONDITIONAL-METADATA-STILL-ROOT-GATED','CONDITIONAL_SOURCE_PENDING_MAIN_ADOPTION'in package
            and all(token in auth for token in('INDEPENDENT_SOURCE_DECISION','EXACT_SOURCE_PAIR','EXACT_SOURCE_CALLERS','CURRENT_FINITE_LEASE','CURRENT_PROJECT_VECTOR','CANONICAL_SCOPE_REGISTRATION','EXACT_REGISTERED_OWNER','UNIQUE_REGISTERED_WORKER','read_ref(ref)')),
            dict(conditional_handoff_status_is_not_grant=True,authority_function_lines=[fn['validate_authority'].lineno,fn['validate_authority'].end_lineno],
                 source_review_schema=pc['review_schema'],source_review_decision=pc['review_decision'],Root_issuance_and_current4_reobserved_before_stage=True))
        bindings={k:rh[k]for k in('caller_ref','core_ref','contract_ref')}
        synthetic=dict(schema=rc['review_schema'],decision=rc['review_decision'],actor_id=REVIEWER,actor_role='INDEPENDENT_NON_AUTHOR',
            source_author_id=AUTHOR,source_handoff_ref=pin(G/'HDF.json'),source_manifest_ref=pin(G/'MF.json'),**bindings,
            actual_executed=False,formal_acceptance=False,execution_grant=False)
        tests=[]
        for name,change,accept in [('new-backup-reviewer',{},True),('Source-author-self-review',{'actor_id':AUTHOR},False),
                ('Root-self-review',{'actor_id':'codex:/root'},False),('old-Source-author-misattributed',{'source_author_id':'codex:/root/attach_restore_independent_review'},False),
                ('execution-grant-injected',{'execution_grant':True},False)]:
            v={**synthetic,**change};actual=True
            try:core.validate_own_review(v,pin(G/'HDF.json'),pin(G/'MF.json'),bindings)
            except ValueError:actual=False
            tests.append(dict(case=name,expected_accept=accept,actual_accept=actual,synthetic_Source_control_only=True))
        control('NF6-REGISTRAR-NEW-AUTHOR-NONAUTHOR-GATE',all(x['expected_accept']==x['actual_accept']for x in tests),tests)
        regfn={x.name:x for x in caller_tree.body if isinstance(x,ast.FunctionDef)}
        model=ast.get_source_segment(held(rh['caller_ref']).decode('utf-8'),regfn['model'])
        requestctx=ast.get_source_segment(held(rh['caller_ref']).decode('utf-8'),regfn['request_context'])
        control('NF6-REGISTRAR-FUTURE-INPUT-BOUNDARY',all(token in requestctx for token in('producer_review_handoff_ref','producer_review_manifest_ref','producer_review_decision_ref','FOUR_ORDERED_CURRENT_REFS','core.validate_times','native_leases'))
            and all(token in model for token in('core.merge_pending','core.make_native_scopes','validate_scratch_parent','COMPLETE_ORIGINAL_BYTE_INVERSE')),
            dict(registrar_review_schema=rc['review_schema'],registrar_review_decision=rc['review_decision'],dynamic_current4_and_pending=True,
                 frozen_old_registry_review_cannot_substitute_new_producer_review=True,TP_and_Canon_not_called=True))
        pub=held(author_witness['original_capture_ref']);lines=pub.splitlines(keepends=True)
        parsed=[json.loads(x)for x in lines]
        meta,final=parsed[1],parsed[2];text='\n'.join(x['text']for x in final['payload']['content']if x['type']=='input_text')
        marker='Message Type: FINAL_ANSWER\nTask name: /root\nSender: /root/full_w09_source_review\nPayload:\n'
        published=json.loads(text[len(marker):]if text.startswith(marker)else text)
        pubrefs=[x for x in walk(published)if shape(x)]
        wants=[pin(P/'HDF.json'),pin(P/'MF.json'),pin(G/'HDF.json'),pin(G/'MF.json')]
        match=lambda a,b:norm(a['path'])==norm(b['path'])and a['sha256']==b['sha256']and a['bytes']==b['bytes']
        control('NF6-TRUE-FULL-AUTHOR-FINAL',len(lines)==3 and [hashlib.sha256(x).hexdigest()for x in lines]==author_witness['original_line_sha256']
            and parsed[0]['payload']['id']==author_witness['Root_thread_id']=='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
            and meta['timestamp']==final['timestamp']and final['payload']['author']=='/root/full_w09_source_review'
            and final['payload']['recipient']=='/root'and final['metadata']['client_authored']is False
            and author_witness['binding_sha256']==wants[0]['sha256']and all(any(match(a,b)for a in pubrefs)for b in wants),
            dict(author_witness_ref=pin(S/'w09.nf6-conditional-producer-registrar-source.actual-audit.root.json'),raw_ref=author_witness['original_capture_ref'],
                 producer_and_registrar_real_published_refs_bound=True))
        result['Source21_qualification']=not result['findings']
        result['producer_nine_refs']=dict(source_handoff_ref=pin(P/'HDF.json'),source_manifest_ref=pin(P/'MF.json'),calling_contract_ref=ph['calling_contract_ref'],**pc['bound_source_refs'])
        result['registration_five_refs']=dict(source_handoff_ref=pin(G/'HDF.json'),source_manifest_ref=pin(G/'MF.json'),**bindings)
        result['prior_qualified_source_handoff_ref']=pin(OLD/'HDF.json')
        result['prior_guard_qualification_not_rerun']=old['runtime_resource_qualification_ref']
        result['actual_Main_component_handoff_ref']=pin(MAIN_REVIEW/'HDF.json')
        result['actual_Main_component_decision_ref']=mh['decision_ref']
        result['actual_Main_component_real_peer_audit_ref']=pin(S/'w09.c19-Main-adoption-component-independent-review.actual-audit.root.json')
        result['future_Root_loaded_runtime_and_actual_Go_list_closure_required']=True
        result['parallel_wave_limit_is_Root_scheduling_obligation']=pc['parallel_schedule']
        result['unchanged_choice_actor_id_is_retained_prior_contributor_metadata']=ch['actor_id']
    except BaseException as exc:
        primary=dict(type=type(exc).__name__,message=str(exc));traceback.print_exc()
    finally:
        close=guard.close();close_ref=save(Q/'SourceGuard.closed.json',close)
        result['guard_cleanup_ref']=close_ref;result['primary_error']=primary
        result['guard_closed']=close['closed'];result['retained_handles_count']=close['retained_handles_count']
        result_ref=save(Q/'delta-review-result.json',result)
        reg_result_ref=save(U/'delta-review-reference.json',dict(combined_result_ref=result_ref,source_guard_ref=close_ref,
            registrar_source_handoff_ref=pin(G/'HDF.json'),registrar_source_manifest_ref=pin(G/'MF.json'),execution_grant=False,formal_acceptance=False))
        print(json.dumps(dict(result_ref=result_ref,registration_result_ref=reg_result_ref,source_guard_ref=close_ref,
            checks=len(result['controls']),failed=sum(not x['passed']for x in result['controls']),primary_error=primary,
            guards_closed=close['closed'],retained_handles=close['retained_handles_count'],verified_resources=len(close['entries'])),ensure_ascii=False))
    return 1 if primary is not None or not close['closed']or close['errors']else 0
if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
