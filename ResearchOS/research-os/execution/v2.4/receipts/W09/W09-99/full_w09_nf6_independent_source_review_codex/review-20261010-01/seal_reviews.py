import ast, datetime, hashlib, json, ntpath, sys, traceback, types
from pathlib import Path

R=Path('D:/作品集/ResearchOS/research-os')
B=R/'execution/v2.4/receipts/W09/W09-99'
Q=Path(__file__).resolve().parent
U=B/'w09_nf6_registration_independent_source_review_codex/review-20261010-01'
P=B/'full_w09_main_native_producer_source_codex/fullw09-20261010-06'
G=B/'w09_nf6_root_registration_source_codex/register-20261010-01'
S=B/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
ACTOR='codex:/root/backup_regression_resources'
AUTHOR='codex:/root/full_w09_source_review'
THREAD='01a11cee-bf59-7a01-be0e-9f799f9b1084'
A=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T03-12-51-01a11cee-bf59-7a01-be0e-9f799f9b1084.jsonl')
CAPTURE=R/'execution/v2.4/receipts/W05/W05-99/public22_to_main23_continuation_independent_review_codex/review-20261010-01/seal_review_revision.py'

def pin(p):
    raw=Path(p).read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def doc(p):return json.loads(Path(p).read_bytes())
def save(p,v):
    with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    return pin(p)
def same(a,b):
    return (ntpath.normcase(ntpath.normpath(a['path'])),a['sha256'],a['bytes'])==(ntpath.normcase(ntpath.normpath(b['path'])),b['sha256'],b['bytes'])
def closed(p):
    value=doc(p)
    return value['closed'] is True and value['retained_handles_count']==0 and value['errors']==[] and all(e['verified'] and e['closed'] for e in value['entries'])
def capture(chunks):
    # Extract only previously verified read-only capture helpers. Never execute its old main.
    source=CAPTURE.read_text(encoding='utf-8');tree=ast.parse(source)
    names={'pin','save','walk','nested','actual_pairs'}
    selected=[node for node in tree.body if isinstance(node,(ast.Import,ast.ImportFrom)) or isinstance(node,ast.FunctionDef) and node.name in names]
    module=types.ModuleType('nf6_independent_capture')
    module.__dict__.update(Q=Q,A=A,ACTOR=ACTOR,THREAD=THREAD)
    exec(compile(ast.Module(body=selected,type_ignores=[]),str(CAPTURE)+'#capture-functions-only','exec'),module.__dict__)
    return module.actual_pairs(chunks)

def main():
    ph=doc(P/'HDF.json');rh=doc(G/'HDF.json')
    pc=doc(ph['calling_contract_ref']['path']);rc=doc(rh['contract_ref']['path'])
    choice=doc(ph['source_choice_ref']['path'])
    delta=doc(Q/'delta-review-result.json');supplement=doc(Q/'registrar-author-supplement-result.json')
    if len(delta['controls'])!=9 or delta['findings'] or delta['primary_error'] is not None or not all(c['passed'] for c in delta['controls']):raise ValueError('ALREADY_COMPLETED_NINE_DELTA_CONTROLS')
    if not delta['Source21_qualification'] or not closed(Q/'SourceGuard.closed.json'):raise ValueError('CURRENT_SOURCE_DELTA_RESOURCE_CLOSURE')
    if not supplement['passed'] or supplement['primary_error'] is not None or not closed(Q/'registrar-author-SourceGuard.closed.json'):raise ValueError('REGISTRAR_AUTHOR_SUPPLEMENT_CLOSED')
    if pc['review_schema']!='researchos.w09-four-selector-producer-independent-source-decision.v1' or rc['review_schema']!='researchos.w09-nf4-registration-independent-source-decision.v1':raise ValueError('EXACT_CONTRACT_REVIEW_SCHEMAS')
    pairs=capture({'3c1360','fd6ec9','822839'})
    for ref in pairs.values():
        pair=doc(ref['path'])
        if pair['actual_outer_exit']!=0 or pair['actual_python_exit']!=0:raise ValueError('EXACT_SUCCESSFUL_SOURCE_TOOL_PAIR')
    reviewed=datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z')
    cleanup_refs=[pin(Q/'SourceGuard.closed.json'),pin(Q/'registrar-author-SourceGuard.closed.json')]
    qualification=save(Q/'source-runtime-delta-qualification.json',dict(
        schema='researchos.w09-nf6-source-runtime-delta-qualification.v1',actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR',source_author_id=AUTHOR,
        decision='SOURCE_RESOURCE_DELTA_QUALIFIED_FOR_ROOT_SCOPE_REBINDING',generation=ph['generation'],
        current_source21=choice['common']['source21'],conditional_Main_after_ref=ph['conditional_Main_after_ref'],Main_condition_met=True,
        Main_actual_independent_handoff_ref=delta['actual_Main_component_handoff_ref'],Main_actual_independent_decision_ref=delta['actual_Main_component_decision_ref'],Main_actual_real_peer_audit_ref=delta['actual_Main_component_real_peer_audit_ref'],
        prior_qualified_source_handoff_ref=delta['prior_qualified_source_handoff_ref'],prior_runtime_resource_qualification_ref=delta['prior_guard_qualification_not_rerun'],
        compiler_stable_resource_count=3905,unchanged_stable_resource_count_reused=3904,unchanged_module_resource_count_reused=19,
        compiler_blueprint_ref=ph['compiler_blueprint_ref'],new_delta_controls_ref=pin(Q/'delta-review-result.json'),new_author_control_ref=pin(Q/'registrar-author-supplement-result.json'),
        acquired_public_resource_counts=[111,2],SourceGuard_cleanup_refs=cleanup_refs,all_guards_closed=True,retained_handles_count=0,
        unchanged_successful_controls_rerun=False,unchanged_3905_full_resource_scan_rerun=False,
        future_Root_CLI_loaded_runtime_closure_required=True,future_Root_GoList_actual_compile_inputs_all_3905_and_module_export_closure_required=True,
        qualification_is_execution_grant=False,actual_Root_stages_executed=False,Native=None,Go=None,SQL=None,model=None,TP=None,dispatcher=None,
        Mode_issued=False,formal_acceptance=False,formal_case_accepted_delta=0,reviewed_utc=reviewed))
    calling=save(Q/'review-calling-contract.json',dict(
        schema='researchos.w09-nf6-independent-source-review-calling-contract.v1',actor_id=ACTOR,source_author_id=AUTHOR,Root_issuer_executor='codex:/root',
        producer_required_review_schema=pc['review_schema'],producer_required_review_decision=pc['review_decision'],registrar_required_review_schema=rc['review_schema'],registrar_required_review_decision=rc['review_decision'],
        producer_original_calling_contract_ref=ph['calling_contract_ref'],registrar_original_calling_contract_ref=rh['contract_ref'],
        producer_future_argv=pc['future_argv'],registrar_future_CLI=rc['CLI'],
        current4='Root observes exact CP/OW/SS/CM at future entry and CAS; historical baseline is not current authority.',
        new_registered_generation=ph['generation'],parallel_schedule=pc['parallel_schedule'],
        dynamic_future_Root_request_ref=None,dynamic_future_Root_scope_ref=None,dynamic_future_review_audit_refs=None,dynamic_future_actual_reports=None,
        preentry_complete_Root_registration_qualification_activation_host_pairs_required=True,postreturn_Root_actual_host_capture_and_Job_reconciliation_required=True,
        old_closed_scopes_and_failure_counter_prefix_preserved=True,source_review_is_execution_grant=False,formal_acceptance=False,
        locked_python_flags=['-I','-S','-B','-X','utf8'],all_product_execution_here=False))
    common=dict(actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR',source_author_id=AUTHOR,
        reviewer_thread_id=THREAD,Root_executor='codex:/root',reviewed_utc=reviewed,actual_executed=False,
        formal_acceptance=False,execution_grant=False,formal_case_accepted_delta=0,findings=[],
        new_delta_controls_ref=pin(Q/'delta-review-result.json'),new_author_control_ref=pin(Q/'registrar-author-supplement-result.json'),
        source_runtime_delta_qualification_ref=qualification,review_calling_contract_ref=calling,actual_source_guard_cleanup_refs=cleanup_refs,
        actual_source_tool_pairs=pairs,original_tool_io_ref=pin(Q/'original-tool-io.reencoded.json'),read_only_capture_helper_source_ref=pin(CAPTURE),
        unchanged_successful_controls_rerun=False,Native=None,Go=None,SQL=None,model=None,TP=None,dispatcher=None,
        future_Root_issuance_current4_finite_lease_owner_worker_and_runtime_resources_required=True,
        future_Mode_or_formal_qualification=None,reviewer_original_failures_this_task=[])
    producer=dict(common,schema=pc['review_schema'],decision=pc['review_decision'],source_handoff_ref=pin(P/'HDF.json'),source_manifest_ref=pin(P/'MF.json'),calling_contract_ref=ph['calling_contract_ref'],
        **pc['bound_source_refs'],selectors=choice['selectors'],source21=choice['common']['source21'],overrides_ref=ph['overrides_ref'],
        Main_condition_met=True,conditional_Main_after_ref=ph['conditional_Main_after_ref'],
        actual_Main_component_handoff_ref=delta['actual_Main_component_handoff_ref'],actual_Main_component_decision_ref=delta['actual_Main_component_decision_ref'],
        real_source_author_audit_ref=pin(S/'w09.nf6-conditional-producer-registrar-source.actual-audit.root.json'),
        generation=ph['generation'],Root_prepare_or_run_called=False,Mode_issued=False)
    producer_decision_ref=save(Q/'decision.json',producer)
    members=[pin(p) for p in sorted(Q.iterdir(),key=lambda p:p.name) if p.is_file() and p.name not in ('HDF.json','MF.json')]
    producer_mf_ref=save(Q/'MF.json',dict(schema='researchos.independent-source-review-manifest.v1',actor_id=ACTOR,members=members))
    producer_hdf_ref=save(Q/'HDF.json',dict(schema='researchos.w09-four-selector-producer-independent-source-HDF.v1',actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR',source_author_id=AUTHOR,
        manifest_ref=producer_mf_ref,source_decision_ref=producer_decision_ref,source_handoff_ref=producer['source_handoff_ref'],source_manifest_ref=producer['source_manifest_ref'],
        calling_contract_ref=ph['calling_contract_ref'],source_runtime_delta_qualification_ref=qualification,
        actual_source_tool_pairs=pairs,all_acquired_source_guards_closed=True,retained_handles_count=0,execution_grant=False,formal_acceptance=False,reviewed_utc=reviewed))
    registrar=dict(common,schema=rc['review_schema'],decision=rc['review_decision'],source_handoff_ref=pin(G/'HDF.json'),source_manifest_ref=pin(G/'MF.json'),
        caller_ref=rh['caller_ref'],core_ref=rh['core_ref'],contract_ref=rh['contract_ref'],generation=rh['generation'],Main_condition_met=True,
        conditional_Main_after_ref=rh['conditional_Main_after_ref'],real_source_author_audit_ref=supplement['author_audit_ref'],real_source_author_original_ref=supplement['author_original_raw_ref'],
        producer_review_handoff_ref=producer_hdf_ref,producer_review_manifest_ref=producer_mf_ref,producer_review_decision_ref=producer_decision_ref,
        Root_propose_check_activate_finalize_called=False,Mode_issued=False)
    registrar_decision_ref=save(U/'decision.json',registrar)
    registrar_members=[pin(p) for p in sorted(U.iterdir(),key=lambda p:p.name) if p.is_file() and p.name not in ('HDF.json','MF.json')]
    registrar_mf_ref=save(U/'MF.json',dict(schema='researchos.independent-source-review-manifest.v1',actor_id=ACTOR,members=registrar_members))
    registrar_hdf_ref=save(U/'HDF.json',dict(schema='researchos.w09-nf4-registration-independent-source-HDF.v1',actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR',source_author_id=AUTHOR,
        manifest_ref=registrar_mf_ref,source_decision_ref=registrar_decision_ref,source_handoff_ref=registrar['source_handoff_ref'],source_manifest_ref=registrar['source_manifest_ref'],
        caller_ref=rh['caller_ref'],core_ref=rh['core_ref'],contract_ref=rh['contract_ref'],source_runtime_delta_qualification_ref=qualification,
        producer_review_handoff_ref=producer_hdf_ref,producer_review_manifest_ref=producer_mf_ref,producer_review_decision_ref=producer_decision_ref,
        actual_source_tool_pairs=pairs,all_acquired_source_guards_closed=True,retained_handles_count=0,execution_grant=False,formal_acceptance=False,reviewed_utc=reviewed))
    print(json.dumps(dict(schema='researchos.w09-nf6-independent-source-review-FINAL.v1',actor_id=ACTOR,
        producer=dict(decision=pc['review_decision'],HDF_ref=producer_hdf_ref,MF_ref=producer_mf_ref,decision_ref=producer_decision_ref),
        registrar=dict(decision=rc['review_decision'],HDF_ref=registrar_hdf_ref,MF_ref=registrar_mf_ref,decision_ref=registrar_decision_ref),
        new_delta_check_groups=9,new_author_binding_check=1,all_guards_closed=True,retained_handles_count=0,execution_grant=False,formal_acceptance=False,formal_case_accepted_delta=0),ensure_ascii=False))
    return 0

if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
