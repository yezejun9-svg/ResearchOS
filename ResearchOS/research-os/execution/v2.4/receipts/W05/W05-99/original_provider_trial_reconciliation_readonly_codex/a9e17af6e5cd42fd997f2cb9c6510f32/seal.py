import sys
sys.dont_write_bytecode=True
import importlib.util
import hashlib
import json
from pathlib import Path
import traceback

Q=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('trial_seal_guard',Q/'guard-library.py')
lib=importlib.util.module_from_spec(spec)
spec.loader.exec_module(lib)

def pin(path):
    raw=path.read_bytes()
    return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}

def main():
    assert not (Q/'HDF.json').exists() and not (Q/'MF.json').exists(),'new seal only'
    report=(Q/'report.md').read_text(encoding='utf-8')
    assert len(report.splitlines())<=150
    discovery=json.loads((Q/'discovery.json').read_text(encoding='utf-8'))
    originals=json.loads((Q/'original-tool-io.json').read_text(encoding='utf-8'))
    assert len(originals['calls'])==30 and originals['new_original_failure_ordinals']==[1008]
    failure=json.loads((Q/'failure-origin.1008.json').read_text(encoding='utf-8'))
    previous_guards=sorted(Q.glob('*source-guard.closed.json'))
    rows={}
    for path in previous_guards:
        closed=json.loads(path.read_text(encoding='utf-8'))
        assert closed['all_handles_closed'] is True and closed['holding_continues_after_process'] is False
        for item in closed['records']:
            assert item['end_identity_and_bytes_equal'] is True
            ref=item['ref']
            key=(lib.normalize(ref['path']).casefold(),ref['sha256'],ref['bytes'])
            rows.setdefault(key,{'ref':ref,'observed_by':[]})['observed_by'].append(pin(path))
    guard=lib.Guard()
    finished=False
    try:
        cp_path=lib.normalize(str(lib.CP)).casefold()
        for item in rows.values():
            ref=item['ref']
            if lib.normalize(ref['path']).casefold()!=cp_path:
                guard.read(lib.normalize(ref['path']),ref)
        closed=guard.close();finished=True
        final_guard_ref=lib.save('seal-public-source-guard.closed.json',closed)
    finally:
        if not finished:
            for stream in guard.held:
                stream.close()
    sourcepins_ref=lib.save('source-pins.json',{'schema':'researchos.original-provider-reconciliation-source-pins.v1','authority':'NONE','checkpoint_observation_ref':discovery['checkpoint_ref'],'checkpoint_was_not_reopened_at_seal':'CP370 observation retains its original closed guard; no live canonical lock during seal','public_audit_HDF_ref':discovery['canonical_public_audit_HDF_ref'],'public_audit_MF_ref':discovery['canonical_public_audit_MF_ref'],'sources':list(rows.values()),'seal_public_source_guard_ref':final_guard_ref,'private_reads':0,'sql_native_provider_model_execution':False})
    decision={'schema':'researchos.original-provider-trial-readonly-reconciliation.v1','decision':'READONLY_RECONCILIATION','authority':'NONE','status':'FINANCIAL_OPEN_ORIGINAL_ACCOUNT_AUDIT_SOURCE_UNAVAILABLE','checkpoint_observation_ref':discovery['checkpoint_ref'],'original_opaque_credential_ref':discovery['credential_ref'],'original_trial_namespace':'integration_codex/root-model-trial-v5-870ecc93e109c85ee985e1566ff','original_failure_ordinal':745,'original_trial_state':'FAILED_EXECUTION_CLOSED','local_dispatch_not_started_proof':'independent review confirms Host GO canonical FILETIME mismatch before ExecuteClaimedAt/RunAdmitted','original_native_timeout':False,'local_owned_job_close_proven':True,'local_job_primary_actual_exits':{'host-admit-only':0,'host-execute-admitted':1},'configured_upper_bound_seconds':300,'observed_provider_timeout':None,'original_provider_request_count':None,'original_model_request_count':None,'original_account_binding':'UNKNOWN','original_provider_response_or_timeout':'UNKNOWN','original_server_request_termination':'UNKNOWN','original_actual_cost':None,'original_billing_finality':'UNKNOWN','financial_coverage_proven':False,'local_scope_effects_observed':0,'local_scope_BudgetLedger_entries_observed':0,'prohibited_inferences':['local Job closure implies server cancellation','local effects/BudgetLedger zero implies provider requests/cost zero','max3 is actual request count','300s configured bound is actual provider timeout','opaque local credential reference proves account ownership','missing UsageTable row proves no request','current balance proves historical net cost'],'known_model_resource':{'model':'deepseek-v4.1-flash','provider':'opencode-go','api':'openai-completions','endpoint':'https://opencode.ai/zen/go/v1/chat/completions','local_opaque_profile_binding_proven':True,'account_or_credential_validity_proven':False},'readable_recovery_sources_required':[{'kind':'ORIGINAL_ACCOUNT_KEY_WORKSPACE_BINDING','status':'UNAVAILABLE_IN_PINNED_ASSOCIATED_PUBLIC_SCOPE','required':'Non-secret Original account/workspace/keyID and trial-time subscription/useBalance/migration state for the fixed opaque ref'},{'kind':'ORIGINAL_REQUEST_AND_RESPONSE_AUDIT','status':'UNAVAILABLE_IN_PINNED_ASSOCIATED_PUBLIC_SCOPE','required':'Original provider request/status/response-or-timeout/finality keyed by upstream requestID and keyID/sessionID for UTC16:56:27.158744 to17:01:27.158744 on 2026-10-08, including bounded skew/late finalization'},{'kind':'ORIGINAL_SERVER_TERMINATION','status':'UNKNOWN','required':'Same requestID server terminal/cancel acknowledgment or audited server nonacceptance/nonexecution; local handles/exits cannot substitute'},{'kind':'ORIGINAL_USAGE_CHARGE_CREDIT_BILLING','status':'UNAVAILABLE_IN_PINNED_ASSOCIATED_PUBLIC_SCOPE','required':'Complete paginated window usages/charges/credits/refunds, balance/transaction reconciliation, final settlement/inflight status'}],'available_public_query_contracts':{'legacy_GET_usage':'/zen/go/v1/usage rolling/weekly/monthly percentages+resetsAt; no full per-request financial/request-terminal audit','authenticated_console':'usage.list/Billing.usages and billing.get/payment.list exist in fixed public Source; Original authenticated workspace source/export absent','current_account_migration_or_server_deployment':'UNKNOWN','public_source_commit':'388406238bd5ca15564a762840a2362c3a45bd9c','official_current_go_doc':'https://opencode.ai/docs/go/'},'this_reconciliation_actuals':{'new_account_queries':0,'new_provider_model_paid_requests':0,'topups_or_account_changes':0,'private_credential_reads':0,'original_DataRoot_reads':0,'sql_execution':0,'native_product_execution':0,'main_canonical_or_old_evidence_writes':0,'new_mechanical_failure_ordinals':[1008],'historical_failure_count_reset':False},'formal_product_or_model_acceptance':False,'next_branch':'Only Original provider/account/financial reconciliation remains blocked on precise read-only Original sources; unrelated resource-ready implementation may proceed','source_pins_ref':sourcepins_ref,'report_ref':pin(Q/'report.md'),'failure_origin_1008_ref':pin(Q/'failure-origin.1008.json')}
    decision_ref=lib.save('decision.json',decision)
    guards=[pin(p) for p in sorted(Q.glob('*source-guard.closed.json'))]
    handoff={'schema':'researchos.readonly-reconciliation-handoff.v1','authority':'NONE','decision_ref':decision_ref,'report_ref':pin(Q/'report.md'),'source_pins_ref':sourcepins_ref,'finite_closed_SourceGuard_refs':guards,'failure_origin_1008_ref':pin(Q/'failure-origin.1008.json'),'original_tool_io_ref':pin(Q/'original-tool-io.json'),'supplement_tool_io_ref':pin(Q/'preseal-tool-io.supplement.json'),'manifest_policy':{'path':str(Q/'MF.json'),'members_include_HDF':True,'HDF_and_MF_exact_pins_delivered_externally':True,'excluded_top_level_files':['MF.json','postseal-tool-io.json'],'postseal_tool_io_is_only_seal_and_reporting_io':True},'execution':'Read-only public evidence reconciliation only. No new product/model/provider/account executions. No automatic formal acceptance. STOP after seal.'}
    hdf_ref=lib.save('HDF.json',handoff)
    excluded={'MF.json','postseal-tool-io.json'}
    members=[]
    for path in sorted(Q.rglob('*')):
        if path.is_file() and path.relative_to(Q).as_posix() not in excluded:
            ref=pin(path)
            members.append({'relative_path':path.relative_to(Q).as_posix(),'sha256':ref['sha256'],'bytes':ref['bytes']})
    mf_ref=lib.save('MF.json',{'schema':'researchos.immutable-readonly-reconciliation-manifest.v1','authority':'NONE','root':str(Q),'members':members,'member_count':len(members),'excluded_top_level_files':sorted(excluded),'failure_ordinals_preserved':[745,1008],'new_paid_model_requests':0,'formal_acceptance':False})
    for item in members:
        actual=pin(Q/item['relative_path'])
        assert (actual['sha256'],actual['bytes'])==(item['sha256'],item['bytes'])
    print(json.dumps({'HDF_ref':hdf_ref,'MF_ref':mf_ref,'decision_ref':decision_ref,'report_ref':pin(Q/'report.md'),'source_pins_ref':sourcepins_ref,'source_guard_ref':final_guard_ref,'failure_origin_1008_ref':pin(Q/'failure-origin.1008.json'),'member_count':len(members),'public_source_pin_count':len(rows),'original_tool_io_ref':pin(Q/'original-tool-io.json'),'status':decision['status'],'authority':'NONE'},ensure_ascii=False))

code=0
try:
    main()
except Exception:
    traceback.print_exc()
    code=1
print('ROOT_PYTHON_EXIT='+str(code))
sys.exit(code)
