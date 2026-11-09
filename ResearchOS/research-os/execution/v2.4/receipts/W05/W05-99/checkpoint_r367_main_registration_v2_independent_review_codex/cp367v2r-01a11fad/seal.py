import hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent
C=N.parents[1]/'checkpoint_r367_main_registration_v2_source_root/cp367-main-v2-20261009'
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(n,v):
 with (N/n).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
refs=json.loads((N/'input-pins.json').read_bytes());result=json.loads((N/'result.json').read_bytes());cleanup=json.loads((N/'source-guard.cleanup.actual.json').read_bytes())
assert all(pin(r['path'])==r for r in refs)
assert result['checks']==40 and result['pins']==216 and cleanup['closed'] and not cleanup['errors'] and cleanup['retained_handles_count']==0
failure=dict(ordinal=None,assignment='Root assigns once in separate immutable registration; do not modify this Source review',chunk_id='b7b538',origin_ref=pin(N/'failure-read.original-tool-io.json'),outer_exit=1,python_exit=None,native_exit=None,model_exit=None,original_calls=1,rerun=False)
save('failure-disposition.json',dict(new_original_failures=[failure],product_failure=False))
save('MF.json',dict(schema='researchos.cp367v2-independent-source-review-manifest.v1',members=[pin(p) for p in sorted(N.iterdir()) if p.is_file()]))
save('HDF.json',dict(schema='researchos.cp367v2-independent-source-review.v1',actor_id='codex:/root/attach_fixture_source_review',actor_role='INDEPENDENT_NON_AUTHOR',decision=result['status'],status=result['status'],manifest_ref=pin(N/'MF.json'),source_handoff_ref=pin(C/'HDF.json'),source_manifest_ref=pin(C/'MF.json'),report_ref=pin(N/'REPORT.md'),result_ref=pin(N/'result.json'),guard_cleanup_ref=pin(N/'source-guard.cleanup.actual.json'),source_v1_P1_fixed=True,source_complete_byte_inverse_pass=True,canonical_complete_semantic_inverse_pass=True,scope_owner_worker_pass=True,old934_plus11_pass=True,independent_checks=40,finite_exact_inputs=216,all_acquired_guards_closed=True,retained_handles=0,new_original_failures=[failure],actual_registration_qualified_now=False,actual_registration_condition=result['condition'],preview_context_actual_authorization=False,actual_canonical_written=False,actual_Main_written=False,Go_SQL_API_model_executed=False,formal_acceptance=False,formal_case_accepted_delta=0,execution_grant=False,STOP=True,FINAL=True))
assert all(pin(r['path'])==r for r in refs)
save('postseal.json',dict(status='PASS_REVIEW_PACKAGE_STABLE',stable_input_pins=len(refs),handoff_ref=pin(N/'HDF.json'),manifest_ref=pin(N/'MF.json')))
print(json.dumps(dict(handoff_ref=pin(N/'HDF.json'),manifest_ref=pin(N/'MF.json'),postseal_ref=pin(N/'postseal.json'))))
