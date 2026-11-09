import hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent
C=N.parents[1]/'checkpoint_r367_scope_namespace_v3_source_root/cp367-scope-v3-20261009'
def pin(p):
 p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,v):
 with (N/n).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
refs=json.loads((N/'input-pins.json').read_bytes());r=json.loads((N/'result.json').read_bytes());cleanup=json.loads((N/'source-guard.cleanup.actual.json').read_bytes());cx=json.loads((N/'counterexample.json').read_bytes())
assert all(pin(x['path'])==x for x in refs)
assert r['checks']==20 and r['pins']==240 and cleanup['closed'] and not cleanup['errors'] and cleanup['retained_handles_count']==0
save('findings.json',[dict(id='CP367-V3-P1-CROSS-CALLER-INT-BOOL',priority=1,main_caller_ref=cx['main_caller_ref'],main_start_line=181,main_end_line=183,registration_writer_ref=cx['registration_writer_ref'],scope_ref=cx['source_scope_ref'],counterexample_ref=pin(N/'counterexample.json'),problem='Exact integer0 required by registration is rejected by Main is-False tuple; Boolean False is rejected by registration',required_change='Make author-owned Main Source predicate agree with integer-zero contract; new sealed reviewed source/bindings required')])
save('MF.json',dict(schema='researchos.cp367v3-independent-source-review-manifest.v1',members=[pin(p) for p in sorted(N.iterdir()) if p.is_file()]))
save('HDF.json',dict(schema='researchos.cp367v3-independent-source-review.v1',actor_id='codex:/root/attach_fixture_source_review',actor_role='INDEPENDENT_NON_AUTHOR',decision=r['status'],status=r['status'],manifest_ref=pin(N/'MF.json'),source_handoff_ref=pin(C/'HDF.json'),source_manifest_ref=pin(C/'MF.json'),report_ref=pin(N/'REPORT.md'),result_ref=pin(N/'result.json'),findings_ref=pin(N/'findings.json'),counterexample_ref=pin(N/'counterexample.json'),guard_cleanup_ref=pin(N/'source-guard.cleanup.actual.json'),P1_findings=1,scope_namespace_fix_pass=True,source_single_pointer_byte_inverse_pass=True,canonical_inverse_pass=True,old934_raw_prefix_plus11_pass=True,independent_checks=20,finite_exact_inputs=240,all_acquired_guards_closed=True,retained_handles=0,new_original_failures=[],actual_registration_qualified=False,actual_registration_executed=False,actual_Main_Canon_written=False,Go_SQL_API_model_executed=False,formal_acceptance=False,formal_case_accepted_delta=0,STOP=True,FINAL=True))
assert all(pin(x['path'])==x for x in refs)
save('postseal.json',dict(status='PASS_PACKAGE_INPUTS_STABLE',handoff_ref=pin(N/'HDF.json'),manifest_ref=pin(N/'MF.json'),input_count=len(refs)))
print(json.dumps(dict(handoff_ref=pin(N/'HDF.json'),manifest_ref=pin(N/'MF.json'),postseal_ref=pin(N/'postseal.json'))))
