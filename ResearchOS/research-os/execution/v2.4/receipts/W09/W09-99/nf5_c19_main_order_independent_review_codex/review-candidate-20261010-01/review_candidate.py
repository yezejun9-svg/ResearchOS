import ast,hashlib,json,ntpath,sys,traceback,types
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os')
Q=Path(__file__).resolve().parent
C=R/'execution/v2.4/receipts/W09/W09-99/nf5_c19_main_order_candidate_source_codex/candidate-20261010-01'
G=R/'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
ACTOR='codex:/root/backup_regression_resources'
AUTHOR='codex:/root/full_w09_source_review'
ROOT_THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
def require(ok,label):
    if not ok:raise ValueError(label)
def decode(raw):
    def pairs(rows):
        obj={}
        for k,v in rows:
            require(k not in obj,'DUPLICATE_JSON_KEY');obj[k]=v
        return obj
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in()).throw(ValueError('NONFINITE_JSON')))
def pin(p):
    b=Path(p).read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def shape(ref):
    require(type(ref)is dict and set(ref)=={'path','sha256','bytes'}and type(ref['path'])is str and type(ref['sha256'])is str and len(ref['sha256'])==64 and type(ref['bytes'])is int,'THREE_FIELD_REF')
    p=Path(ref['path']);require(p.is_absolute(),'ABSOLUTE_SOURCE_REF');return p
def read(ref):
    p=shape(ref);raw=p.read_bytes();require(len(raw)==ref['bytes']and hashlib.sha256(raw).hexdigest()==ref['sha256'],'EXACT_RESOURCE_PIN');return raw
def key(ref):return(ntpath.normcase(str(shape(ref).absolute())),ref['sha256'],ref['bytes'])
def same(a,b):return key(a)==key(b)
def write(name,value):
    p=Q/name
    with p.open('xb')as f:f.write(value if type(value)is bytes else(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    return pin(p)
def docs(value):
    if type(value)in(dict,list):
        yield value
        for x in(value.values()if type(value)is dict else value):yield from docs(x)
    elif type(value)is str:
        for text in dict.fromkeys((value,*value.splitlines())):
            try:parsed=decode(text)
            except(ValueError,TypeError):continue
            if parsed!=value:yield from docs(parsed)
def main():
    hdfref=dict(path=str(C/'HDF.json'),sha256='0c89a869cb1d7a69d415cebaf52b75878d93b9a254ea7e7cea17a1d44d6ad8fd',bytes=7060)
    h=decode(read(hdfref));mfref=h['manifest_ref'];require(mfref['sha256']=='88535fa592ee630d86bab32338e9addb4cf0d255908c38d0be17c5c5e3505af5'and mfref['bytes']==4449,'ROOT_PROVIDED_SOURCE_MANIFEST_PIN')
    mf=decode(read(mfref));contract=decode(read(h['calling_contract_ref']));inputs=decode(read(h['input_pins_ref']))
    rolekeys={'retrieval','router','closure','profile','NF5_runtime','NF5_choice','NF5_HDF','NF5_MF'}
    require(set(inputs['current_input_refs'])==rolekeys,'EXACT_EIGHT_SOURCE_ROLES')
    refs=[hdfref,mfref,*mf['members'],*inputs['current_input_refs'].values(),pin(G),pin(Path(__file__))]
    unique={key(ref):dict(ref,path=str(shape(ref).absolute()))for ref in refs}
    graw=G.read_bytes();require(hashlib.sha256(graw).hexdigest()=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85','PINNED_GUARD_SOURCE')
    gm=types.ModuleType('candidate_review_known_guard');gm.__file__=str(G);exec(compile(graw,str(G),'exec'),gm.__dict__)
    guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=128*1024*1024);primary=None;checks=[];details={}
    def check(name,passed,evidence=None):checks.append(dict(name=name,passed=bool(passed),evidence=evidence))
    try:
        guard.acquire(list(unique.values()))
        check('published_whole_package_and_exact_eight_resources_held',mf['member_count']==len(mf['members'])==12,dict(held_refs=len(unique),eight_roles=sorted(rolekeys),Main_refs_are_read_only=True))
        raw=read(h['actual_publication_host']['raw_ref']);lines=raw.splitlines(keepends=True);require(len(lines)==3 and all(x.endswith(b'\n')for x in lines),'THREE_COMPLETE_AUTHOR_LINES')
        head,call,out=[decode(x)for x in lines];binding=decode(read(h['actual_publication_host']['binding_ref']))
        caller,returned=call['payload'],out['payload'];observations={x['chunk_id']:x for x in docs(returned)if type(x)is dict and type(x.get('chunk_id'))is str and'output'in x}
        observation=observations.get(binding['actual_chunk_id']);offsets=binding['source_line_offsets']
        author_ok=(h['source_author']==AUTHOR and ACTOR not in(AUTHOR,'codex:/root')and contract['source_author']==AUTHOR
            and h['source_author_backend']==binding['actor_id']=='/root/full_w09_source_review'
            and h['source_author_thread_id']==binding['actor_thread_id']==head['payload']['id']=='01a1215b-7210-7613-b033-756b9d553b83'
            and h['root_thread_id']==contract['root_thread_id']==ROOT_THREAD and head['type']=='session_meta'and head['ordinal']==0
            and caller['call_id']==returned['call_id']==binding['actual_call_id']and 0<call['ordinal']<out['ordinal']
            and offsets==sorted(set(offsets))and offsets[0]==0 and all(type(v)is int for v in offsets)
            and binding['original_line_bytes']==[len(x)for x in lines]and binding['original_line_sha256']==[hashlib.sha256(x).hexdigest()for x in lines]
            and all(n+len(line)<=binding['source_prefix_size_observed']for n,line in zip(offsets,lines))
            and observation is not None and observation.get('exit_code')==binding['actual_outer_exit']==binding['actual_python_exit']==0)
        check('actual_Full_author_publication_and_non_author_Backup_review',author_ok,dict(author=AUTHOR,reviewer=ACTOR,Root_executor='codex:/root',author_original_host_ref=h['actual_publication_host']['binding_ref'],author_header_source=head['payload'].get('source'),Root_peer_witness='Root must capture this actual review Final after publication; not pre-issued here'))
        before=read(h['before_source_ref']);actual=read(h['before_main_ref']);candidate=read(h['sourcecandidate_ref'])
        old=b'selected = GROUPS[check] if check else list(TESTS)';new=b'selected = GROUPS[check] if check else [name for name in CASES[case] if name in TESTS]'
        base_tree=ast.parse(before);tree=ast.parse(candidate);compile(tree,str(C/'retrieval.source.py'),'exec')
        byte_ok=(before==actual and before.count(old)==candidate.count(new)==1 and before.replace(old,new)==candidate and candidate.replace(new,old)==before)
        check('full_candidate_exact_single_expression_and_inverse',byte_ok,dict(before_ref=h['before_main_ref'],candidate_ref=h['sourcecandidate_ref'],whole_byte_inverse=byte_ok,Main_entry_executed=False))
        constants={}
        for node in tree.body:
            if isinstance(node,ast.Assign)and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):constants[node.targets[0].id]=node.value
        tests=ast.literal_eval(constants['TESTS']);cases_node=constants['CASES'];c19=next(ast.literal_eval(v)for k,v in zip(cases_node.keys,cases_node.values)if ast.literal_eval(k)=='C19')
        selected=[name for name in c19 if name in tests];ids=[item for name in selected for item in tests[name][1]];packages=sorted({tests[name][0]for name in selected})
        choice=decode(read(inputs['current_input_refs']['NF5_choice']));c=dict(choice['common'],**choice['selectors']['C19']);regexp='^(?:'+'|'.join(selected)+')$'
        check('new_actual_candidate_C19_exact_frozen_two_tests_five_ids_argv',selected==c['selected_tests']and ids==c['expected_native_ids']and c['go_test_argv_suffix']==['test','-count=1','-json','-run',regexp,*packages],dict(selected_tests=selected,assertion_ids=ids,go_argv_suffix=['test','-count=1','-json','-run',regexp,*packages],synthetic_AST_observation=True,no_Native_run=True))
        source21=ast.literal_eval(constants['SOURCES']);check('Source21_target_membership_and_original_gates_preserved',len(source21)==21 and 'ops/ci/retrieval.py'in source21 and byte_ok and same(inputs['current_input_refs']['retrieval'],h['before_main_ref']),dict(complete_Source21_requalified=False,router_closure_profile_NF5_refs=inputs['current_input_refs'],unchanged_rest_of_source_bytes=True))
        policy=contract['mandatory_independent_review'];sequence=contract['Root_single_target_adoption_sequence']
        check('Root_adoption_requires_real_peer_review_exclusive_CAS_archive_and_finally',all(policy[k]is True for k in('required_before_Main_adoption','reviewer_cannot_equal_source_author','reviewer_cannot_be_Root_executor','review_must_bind_exact_candidate_HDF_MF_contract_and_candidate_refs','Root_must_observe_actual_backend_peer_delivery_and_original_byte_offsets'))and policy['independent_review_refs']is None and policy['actual_Root_peer_witness_ref']is None and len(sequence)==8 and 'share_mode=0'in sequence[3]and 'archive'in sequence[4]and 'finally'in sequence[7]and contract['implementation_kind']=='SOURCE_CONTRACT_ONLY_NO_ADOPTION_EXECUTABLE',dict(sequence=sequence,adoption_executable_reviewed=False,Root_must_materialize_fresh_authority_and_request=True))
        after=contract['after_adoption_qualification'];routes=[(x['command'],x['week'],x['check'],x['case'])for x in after['fresh_CM40_routes_required']]
        wanted=[('test.retrieval','W09','W09-G01',''),('test.retrieval','W09','W09-G02',''),('test.research.fixture','W09','','C19'),('test.retrieval','W09','','C19'),('test.retrieval','W09','','A06'),('test.security','W09','','A06')]
        check('all_four_old_Native_historical_four_fresh_six_CM40_required',after['all_four_prior_Native_reports_become_historical_for_current_Source21']is True and after['historical_passes_and_all_original_failures_must_remain_byte_unchanged']is True and after['fresh_Native_selectors_required']==['W09-G01','W09-G02','A06','C19']and routes==wanted and after['fresh_current_Source21_generation_and_independent_Source_review_required']is True and after['fresh_Root_issued_Native_Scopes_and_runtime_resource_qualification_required']is True,dict(future_selectors=after['fresh_Native_selectors_required'],future_routes=routes,no_prior_Native_promoted=True))
        check('Source_contract_issues_no_execution_or_product_acceptance',all(contract[k]is False for k in('execution_grant','formal_acceptance','candidate_independently_accepted','Main_adopted','RootScope_lease_or_qualification_issued'))and all(h[k]is False for k in('Main_Canon_NF5_Scope_written','execution_grant','formal_acceptance','Source21_qualification','Mode_qualification'))and contract['original_failure_ordinals_retained']==h['original_failure_ordinals_retained']==[1158,1159]and contract['prior_Root_C19_authority_failure']['original_ordinal']==1156,dict(originals_preserved=[1156,1158,1159],future_runtime_qualification=False,execution_grant=False))
        details=dict(candidate_HDF_ref=hdfref,candidate_MF_ref=mfref,candidate_contract_ref=h['calling_contract_ref'],candidate_ref=h['sourcecandidate_ref'],before_main_ref=h['before_main_ref'],eight_input_refs=inputs['current_input_refs'],reused_old18_properties_ref=h['reused_advisory_properties_ref'],old18_controls_rerun=False,author6_controls_rerun=False,Root_actual_new_peer_witness_ref=None)
    except BaseException as exc:primary=exc
    finally:
        cleanup=guard.close();guardref=write('candidate-review.guard.closed.json',cleanup)
    if primary is not None:raise primary
    require(cleanup['closed']is True and cleanup['retained_handles_count']==0 and not cleanup['errors']and cleanup['failure']is None and all(e['closed']is True and e['verified']is True and e['final_path_match']is True for e in cleanup['entries']),'INDEPENDENT_GUARD_CLOSED_0')
    verdict='ACCEPTED_SOURCE_ONLY'if all(c['passed']for c in checks)else'SOURCE_CHANGES_REQUIRED'
    result=dict(schema='researchos.w09-c19-main-order-independent-source-review.v1',decision=verdict,reviewer=ACTOR,reviewer_backend='/root/backup_regression_resources',reviewer_thread_id='01a11cee-bf59-7a01-be0e-9f799f9b1084',source_author=AUTHOR,Root_executor='codex:/root',Root_thread_id=ROOT_THREAD,checks=checks,checks_passed=sum(x['passed']for x in checks),guard_ref=guardref,**details,Main_adoption=False,Source21_qualification=False,runtime_qualification=False,Mode_qualification=False,RootScope_lease_or_qualification_issued=False,formal_acceptance=False,execution_grant=False,actual_Go_Native_SQL_model_TP_calls=0)
    ref=write('decision.unsealed.json',result);print(json.dumps(dict(decision=verdict,checks_passed=result['checks_passed'],decision_ref=ref,guard_ref=guardref),ensure_ascii=False));return 0
if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
