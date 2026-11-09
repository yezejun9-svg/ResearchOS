from pathlib import Path
import datetime, hashlib, json, types

R = Path(r'D:/作品集/ResearchOS/research-os')
W = R/'execution/v2.4/receipts/W09/W09-99'
D = Path(__file__).resolve().parent
SUPPORT = W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
raw = SUPPORT.read_bytes()
assert len(raw) == 4940 and hashlib.sha256(raw).hexdigest() == '567f53cadfab3781d6345ed1c6b04b52b85135e0843ce3c217e2f7fadf2a021a'
s = types.ModuleType('source_review_seal_support');s.__file__ = str(SUPPORT)
exec(compile(raw, str(SUPPORT), 'exec'), s.__dict__);s.D = D
actual_pair = s.capture('b53ca3', 0, 0)
refs = [s.pin(p) for p in sorted(D.iterdir()) if p.is_file()]
g = s.guard()
try:
    g.acquire(refs)
    checks = json.loads(g.get_buffer(str(D/'source-review-checks.json')))
    closed_review = json.loads(g.get_buffer(str(D/'source-review-guard.closed.json')))
    assert checks['count'] == checks['passed'] == 23 and checks['failed'] == 0 and checks['failure'] is None
    assert closed_review['verification'] == 'PASSED' and closed_review['closed'] is True and closed_review['retained_handles_count'] == 0 and closed_review['failure'] is None and closed_review['errors'] == []
    assert all(e['verified'] is True and e['closed'] is True for e in closed_review['entries'])
    evidence = checks['evidence']
finally:
    closed = g.close()
    seal_guard_ref = s.write('seal-source-guard.closed.json', closed)
assert closed['closed'] is True and closed['retained_handles_count'] == 0 and closed['failure'] is None and closed['errors'] == []
reviewed_utc = datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z')
shared = {
    'review_author': 'codex:/root/full_w09_source_review',
    'backend_actor_id': '/root/full_w09_source_review',
    'actor_thread_id': '01a1215b-7210-7613-b033-756b9d553b83',
    'root_thread_id': '01a11007-5233-7ca1-b71f-9e9e5ce84c98',
    'source_author': 'codex:/root/attach_restore_independent_review',
    'independent_non_author': True,
    'reviewed_utc': reviewed_utc,
    'source_hdf_ref': evidence['Source_hdf_ref'],
    'source_mf_ref': evidence['Source_mf_ref'],
    'source_contract_ref': evidence['Source_contract_ref'],
    'source_refs': evidence['source_refs'],
    'integration_targets_ref': evidence['integration_targets_ref'],
    'source_checks_ref': s.pin(D/'source-review-checks.json'),
    'source_guard_ref': s.pin(D/'source-review-guard.closed.json'),
    'seal_guard_ref': seal_guard_ref,
    'actual_source_review_hostpair': actual_pair,
    'all_guards_closed_zero': True,
    'retained_handles_count': 0,
    'live_Canon_handles_held': 0,
    'private_key_owner_contents_read_or_hashed': False,
    'old_successful_controls_replayed': False,
    'Go_tests_compiled_or_executed': False,
    'product_calls': 0,
    'new_review_failures': [],
    'Main_adopted': False,
    'runtime_programme_qualification_issued': False,
    'execution_grant': False,
    'formal_acceptance': False,
    'parent_acceptance': False,
    'formal_case_accepted_delta': 0,
    'full20to24': 'OPEN',
    'STOP': True,
}
decision = {
    'schema': 'researchos.public23-to24-independent-source-decision.v1',
    **shared,
    'status': 'ACCEPTED_SOURCE_ONLY',
    'verdict': 'ACCEPTED_SOURCE_ONLY',
    'decision': 'SOURCE_ACCEPTED_FOR_ROOT_INTEGRATION',
    'scope': 'Only the new isolated ordinary public Main23 backup handoff to a distinct Target24 coordinator; it does not qualify original-root apply or future execution.',
    'new_static_source_checks': {'count': 23, 'passed': 23, 'failed': 0, 'kind': 'Actual immutable byte/function/source boundary inspection; no Go runtime behavior is claimed.'},
    'findings': [],
    'identity_boundary': 'The unchanged old upgrade-local entry binds its source program. New upgrade-prepared-backup binds the actual coordinator to TargetProgram and requires distinct full SourceProgram/TargetProgram digests.',
    'provenance_boundary': 'Pinned binding/stdout/observation metadata remains an external input, never authenticated execution proof or permission. Root must independently bind the actual preserved Main23 create invocation before constructing it.',
    'original_apply_boundary': 'Eleven inherited files retain the old Native MigrationToken/Owner/lease apply contract. The new handoff receipt has a different schema and filename and cannot satisfy that original apply contract.',
    'failure_boundary': 'Preserve failed invocations and any isolated destination left after publication. Use a fresh authorized destination for a later attempt; no automatic reuse, retry or cleanup.',
    'Root_followup_required': [
        'Compose the declared base candidate prerequisites and preserve independently changed Main source; integrate only four exact reviewed targets.',
        'Build and qualify a genuinely distinct Target24 program with exact release/runtime closure under a fresh actual Root Scope.',
        'Run the newly authored metadata boundary tests and regression checks justified by the two changed production files, without replaying already-successful historical commands.',
        'Execute the new public handoff against the preserved actual Main23 backup and independently verify target24 schema/ledger, original and backup preservation, restore effects, DDL rollback/commit, receipt and all cleanup.',
        'Separately verify matching Target24 backup/restore and all remaining full20to24 gates before broader W05 acceptance.'
    ],
    'Source_author_identity_basis': 'Root dispatch identifies Attach and the exact sealed HDF/MF byte package was independently held and verified. Root must retain its genuine backend Source Final proof when issuing future Scope; this review invents no peer capture.',
}
decision_ref = s.write('review-decision.json', decision)
members = [s.pin(p) for p in sorted(D.iterdir()) if p.is_file() and p.name not in ('HDF.json','MF.json')]
mf_ref = s.write('MF.json', {'schema':'researchos.public23-to24-independent-source-review-manifest.v1','actor_id':shared['review_author'],'backend_actor_id':shared['backend_actor_id'],'members':members,'member_count':len(members),'HDF_MF_excluded_to_avoid_self_reference':True,'execution_grant':False,'formal_acceptance':False})
hdf_ref = s.write('HDF.json', {'schema':'researchos.public23-to24-independent-source-review-handoff.v1',**shared,'status':'ACCEPTED_SOURCE_ONLY','verdict':'ACCEPTED_SOURCE_ONLY','decision':'SOURCE_ACCEPTED_FOR_ROOT_INTEGRATION','decision_ref':decision_ref,'manifest_ref':mf_ref,'new_static_source_checks':{'count':23,'passed':23,'failed':0},'source_ref_count':len(evidence['source_refs']),'integration_target_count':4,'inherited_unchanged_sources':11})
print(json.dumps({'HDF_ref':hdf_ref,'MF_ref':mf_ref,'decision_ref':decision_ref,'checks':23,'passed':23,'verdict':'ACCEPTED_SOURCE_ONLY','retained_handles_count':0,'execution_grant':False,'formal_acceptance':False},ensure_ascii=False))
