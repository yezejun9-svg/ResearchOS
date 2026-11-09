import hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent;C=N.parents[1]/'checkpoint_r367_transaction_operation_v5_source_root/cp367-operation-v5-20261009'
def pin(p):
 p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,v):
 with (N/n).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
refs=json.loads((N/'input-pins.json').read_bytes());r=json.loads((N/'result.json').read_bytes());cl=json.loads((N/'source-guard.cleanup.actual.json').read_bytes())
assert all(pin(v['path'])==v for v in refs)
assert r['checks']==22 and r['pins']==253 and cl['closed'] and not cl['errors'] and cl['retained_handles_count']==0
save('MF.json',dict(schema='researchos.cp367v5-independent-source-review-manifest.v1',members=[pin(p) for p in sorted(N.iterdir()) if p.is_file()]))
save('HDF.json',dict(schema='researchos.cp367v5-independent-source-review.v1',actor_id='codex:/root/attach_fixture_source_review',actor_role='INDEPENDENT_NON_AUTHOR',decision=r['status'],status=r['status'],manifest_ref=pin(N/'MF.json'),source_handoff_ref=pin(C/'HDF.json'),source_manifest_ref=pin(C/'MF.json'),report_ref=pin(N/'REPORT.md'),result_ref=pin(N/'result.json'),helper_prelude_controls_ref=pin(N/'helper-prelude-controls.json'),guard_cleanup_ref=pin(N/'source-guard.cleanup.actual.json'),independent_checks=22,finite_exact_inputs=253,one_writer_span_complete_byte_inverse_pass=True,facts_complete_byte_inverse_pass=True,operation_activate_reaches_stubbed_WinDLL_boundary=True,actual_helper_WinAPI_or_filesystem_executed=False,canonical_automatic_inverse=False,partial_failure_requires_explicit_Root_reconciliation=True,old934_raw_semantic_plus15_total949_pass=True,Source_cut951_next952=True,Scope_Source_review_bindings_unchanged=True,W05_authority_expanded=False,all_acquired_guards_closed=True,retained_handles=0,new_original_failures=[],actual_registration_qualified_now=False,actual_registration_condition=r['condition'],actual_Main_Canon_written=False,Go_SQL_API_model_executed=False,formal_acceptance=False,formal_case_accepted_delta=0,execution_grant=False,STOP=True,FINAL=True))
assert all(pin(v['path'])==v for v in refs)
save('postseal.json',dict(status='PASS_REVIEW_PACKAGE_INPUTS_STABLE',handoff_ref=pin(N/'HDF.json'),manifest_ref=pin(N/'MF.json'),input_count=len(refs)))
print(json.dumps(dict(handoff_ref=pin(N/'HDF.json'),manifest_ref=pin(N/'MF.json'),postseal_ref=pin(N/'postseal.json'))))
