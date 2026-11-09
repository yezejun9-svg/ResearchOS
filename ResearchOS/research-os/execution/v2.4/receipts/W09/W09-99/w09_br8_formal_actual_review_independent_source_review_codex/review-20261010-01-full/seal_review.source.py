from pathlib import Path
import datetime, hashlib, json, types

R = Path(r'D:/作品集/ResearchOS/research-os')
W = R/'execution/v2.4/receipts/W09/W09-99'
D = Path(__file__).resolve().parent
support = W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
raw = support.read_bytes()
assert len(raw)==4940 and hashlib.sha256(raw).hexdigest()=='567f53cadfab3781d6345ed1c6b04b52b85135e0843ce3c217e2f7fadf2a021a'
s=types.ModuleType('frev_seal_support');s.__file__=str(support)
exec(compile(raw,str(support),'exec'),s.__dict__);s.D=D
actual_pair=s.capture('4e0e7b',0,0)
refs=[s.pin(p) for p in sorted(D.iterdir()) if p.is_file()]
g=s.guard()
try:
 g.acquire(refs)
 checks=json.loads(g.get_buffer(str(D/'independent-delta-checks.json')))
 observation=json.loads(g.get_buffer(str(D/'source-review-guard.closed.json')))
 assert checks['count']==checks['passed']==11 and checks['failed']==0 and checks['failure'] is None
 assert observation['verification']=='PASSED' and observation['closed'] is True and observation['retained_handles_count']==0 and observation['failure'] is None and observation['errors']==[]
 assert all(x['verified'] is True and x['closed'] is True for x in observation['entries'])
 evidence=checks['evidence']
finally:
 closed=g.close();seal_guard_ref=s.write('seal-source-guard.closed.json',closed)
assert closed['closed'] is True and closed['retained_handles_count']==0 and closed['errors']==[] and closed['failure'] is None
shared={
 'review_author':'codex:/root/full_w09_source_review',
 'backend_actor_id':'/root/full_w09_source_review',
 'actor_thread_id':'01a1215b-7210-7613-b033-756b9d553b83',
 'root_thread_id':'01a11007-5233-7ca1-b71f-9e9e5ce84c98',
 'source_author':'codex:/root/backup_regression_resources',
 'source_author_backend':'/root/backup_regression_resources',
 'independent_non_author':True,
 'reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z'),
 'source_hdf_ref':evidence['source_refs'][0],
 'source_mf_ref':evidence['source_refs'][1],
 'source_decision_ref':evidence['source_refs'][2],
 'caller_ref':evidence['source_refs'][3],
 'calling_contract_ref':evidence['source_refs'][4],
 'basis_ref':evidence['source_refs'][5],
 'source_author_actual_audit_ref':evidence['author_audit_ref'],
 'source_author_original_capture_ref':evidence['author_original_capture_ref'],
 'base_source_ref':evidence['base_source_ref'],
 'base_hdf_ref':evidence['base_hdf_ref'],
 'base_mf_ref':evidence['base_mf_ref'],
 'delta_check_ref':s.pin(D/'independent-delta-checks.json'),
 'source_guard_ref':s.pin(D/'source-review-guard.closed.json'),
 'seal_guard_ref':seal_guard_ref,
 'actual_independent_source_review_hostpair':actual_pair,
 'new_independent_Source_checks':11,
 'reused_author_controls':{'prefix':4,'tail':2,'replayed':False},
 'old_NF6_four_Native_and_six_Mode_checks_replayed':False,
 'actual_formal_review_called':False,
 'future_Root_scope':None,
 'future_input_bundle':None,
 'future_actual_review_ref':None,
 'future_Root_capture_ref':None,
 'future_Root_issuance_ref':None,
 'future_owner_acceptance_ref':None,
 'Main_Canon_Scope_Registry_writes':0,
 'product_calls':0,
 'all_guards_closed_zero':True,
 'retained_handles_count':0,
 'live_Canon_handles_held':0,
 'private_material_read_or_hashed':False,
 'new_review_failures':[],
 'original1235_binding_ref':evidence['original1235_binding_ref'],
 'original1235_raw_ref':evidence['original1235_raw_ref'],
 'original1235_status':'FAILED_RETAINED_SOURCE_CONTROL_FIXTURE_METADATA_ONLY',
 'failure_counter_reset':False,
 'execution_grant':False,
 'formal_acceptance':False,
 'parent_acceptance':False,
 'STOP':True,
}
decision={
 'schema':'researchos.w09-formal-review-independent-source-decision.v1',
 **shared,
 'status':'ACCEPTED_SOURCE_ONLY',
 'verdict':'ACCEPTED_SOURCE_ONLY',
 'decision':'SOURCE_ACCEPTED_FOR_FUTURE_ROOT_AUTHORIZED_FORMAL_REVIEW',
 'complete_byte_inverse':True,
 'changed_function_AST':['review_actual'],
 'changed_byte_spans':3,
 'basis_bytes_unchanged':True,
 'findings':[],
 'input_resource_rule':'Bundle resource_refs excludes its own canonical path. External exact input_ref is verified before parsing, rejects any canonical self-reference, is authorized independently, and is held together with every original resource by SourceReadGuard.',
 'preserved_gates':'All previous helpers/schema, six routes and consumer closure, actual mode qualification, role identity/provenance, GLOBAL facts, Current4/source pins, temporal cutoff, Main gates, reader-held closure and cleanup retain original AST/contract rules.',
 'source_only_limit':'The eleven checks are finite Source bytes/AST/provenance checks. No synthetic control, immutable preparation document or this review is a formal product result, Root Scope, actual independent review, owner AcceptanceReceipt or execution grant.',
 'Root_next_actual_inputs':'Provide the closed six current-CM40 consumers, final immutable assembled context, fresh exact publication Scope/owner/roles/current4, actual Root captures, eight GLOBAL documents and the full authorized public resource set. Compute the bundle hash externally without embedding its own pin.',
 'future_actual_sequence':'Under a later authorized actual task, Backup calls this reviewed entry and publishes its actual review only after all existing Main gates succeed and every handle closes. Root then captures the genuine Backup Final and alone publishes issuance/capture index and invokes existing Bridge check/derive.',
}
decision_ref=s.write('review-decision.json',decision)
members=[s.pin(p) for p in sorted(D.iterdir()) if p.is_file() and p.name not in ('HDF.json','MF.json')]
mf_ref=s.write('MF.json',{'schema':'researchos.w09-formal-review-independent-source-manifest.v1','actor_id':shared['review_author'],'backend_actor_id':shared['backend_actor_id'],'member_count':len(members),'members':members,'HDF_MF_excluded_to_avoid_self_reference':True,'formal_acceptance':False,'execution_grant':False})
hdf_ref=s.write('HDF.json',{'schema':'researchos.w09-formal-review-independent-source-handoff.v1',**shared,'status':'ACCEPTED_SOURCE_ONLY','verdict':'ACCEPTED_SOURCE_ONLY','decision':'SOURCE_ACCEPTED_FOR_FUTURE_ROOT_AUTHORIZED_FORMAL_REVIEW','decision_ref':decision_ref,'manifest_ref':mf_ref,'checks':{'count':11,'passed':11,'failed':0}})
print(json.dumps({'HDF_ref':hdf_ref,'MF_ref':mf_ref,'decision_ref':decision_ref,'checks':11,'passed':11,'verdict':'ACCEPTED_SOURCE_ONLY','retained_handles_count':0,'formal_acceptance':False,'execution_grant':False},ensure_ascii=False))
