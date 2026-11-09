import hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent
C=N.parents[1]/'checkpoint_r367_main_v2_binding_v4_source_root/cp367-bind-v4-20261009'
def pin(p):
 p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,v):
 with (N/n).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
refs=json.loads((N/'input-pins.json').read_bytes());r=json.loads((N/'result.json').read_bytes());cleanup=json.loads((N/'source-guard.cleanup.actual.json').read_bytes())
assert all(pin(v['path'])==v for v in refs)
assert r['checks']==27 and r['pins']==228 and cleanup['closed'] and not cleanup['errors'] and cleanup['retained_handles_count']==0
save('MF.json',dict(schema='researchos.cp367v4-independent-source-review-manifest.v1',members=[pin(p) for p in sorted(N.iterdir()) if p.is_file()]))
save('HDF.json',dict(schema='researchos.cp367v4-independent-source-review.v1',actor_id='codex:/root/attach_fixture_source_review',actor_role='INDEPENDENT_NON_AUTHOR',decision=r['status'],status=r['status'],manifest_ref=pin(N/'MF.json'),source_handoff_ref=pin(C/'HDF.json'),source_manifest_ref=pin(C/'MF.json'),report_ref=pin(N/'REPORT.md'),result_ref=pin(N/'result.json'),diagnostic_audit_ref=pin(N/'diagnostic-audit.json'),guard_cleanup_ref=pin(N/'source-guard.cleanup.actual.json'),independent_checks=27,finite_exact_inputs=228,facts_complete_byte_inverse_pass=True,canonical_complete_inverse_pass=True,old934_raw_semantic_plus14_pass=True,new14_numeric_origins_qualified=True,Scope_Main_source_review_binding_pass=True,full_Main_v2_validate_scope_pass=True,W05_authority_expanded=False,all_acquired_guards_closed=True,retained_handles=0,new_original_failures=[],actual_registration_qualified_now=False,actual_registration_condition=r['condition'],actual_Main_Canon_written=False,Go_SQL_API_model_executed=False,formal_acceptance=False,formal_case_accepted_delta=0,execution_grant=False,STOP=True,FINAL=True))
assert all(pin(v['path'])==v for v in refs)
save('postseal.json',dict(status='PASS_REVIEW_PACKAGE_INPUTS_STABLE',handoff_ref=pin(N/'HDF.json'),manifest_ref=pin(N/'MF.json'),input_count=len(refs)))
print(json.dumps(dict(handoff_ref=pin(N/'HDF.json'),manifest_ref=pin(N/'MF.json'),postseal_ref=pin(N/'postseal.json'))))
