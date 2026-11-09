import hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent
C=N.parents[1]/'checkpoint_r367_main_registration_source_root/cp367-main-20261009'
def pin(path):
 p=Path(path).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,value):
 with (N/name).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
refs=json.loads((N/'input-pins.json').read_bytes());result=json.loads((N/'result.json').read_bytes());cleanup=json.loads((N/'source-guard.cleanup.actual.json').read_bytes())
assert all(pin(r['path'])==r for r in refs)
assert result['status']=='REQUEST_CHANGES' and result['independent_checks']==26 and len(refs)==191
assert cleanup['closed'] and cleanup['errors']==[] and cleanup['retained_handles_count']==0
save('findings.json',[dict(id='CP367-SOURCE-P1-LIVE-CUTOFF',priority=1,source_ref=pin(C/'register_cp367.source.py'),function='transform',problem='Unconditional live next overwrite 949 to cut next948 and pending948 erasure',counterexample_ref=pin(N/'counterexample.json'),source_preview_ref=pin(C/'source-preview-proof.json'),required_change='Bind independently sealed Root live context; live >= cut next and complete pending interval with exact origin refs; keep immutable cut947/948')])
save('MF.json',dict(schema='researchos.cp367-independent-source-review-manifest.v1',members=[pin(p) for p in sorted(N.iterdir()) if p.is_file()]))
save('HDF.json',dict(schema='researchos.cp367-independent-source-review.v1',actor_id='codex:/root/attach_fixture_source_review',actor_role='INDEPENDENT_NON_AUTHOR',decision='REQUEST_CHANGES',status='REQUEST_CHANGES',manifest_ref=pin(N/'MF.json'),source_handoff_ref=pin(C/'HDF.json'),source_manifest_ref=pin(C/'MF.json'),report_ref=pin(N/'REPORT.md'),findings_ref=pin(N/'findings.json'),result_ref=pin(N/'result.json'),counterexample_ref=pin(N/'counterexample.json'),guard_cleanup_ref=pin(N/'source-guard.cleanup.actual.json'),independent_checks=26,finite_exact_pins=191,all_acquired_guards_closed=True,retained_handles=0,old934_plus11_registration_cut_pass=True,complete_inverse_pass=True,scope_owner_worker_pass=True,P1_findings=1,new_original_failures=[],actual_canonical_written=False,actual_Main_written=False,actual_main_writer_executed=False,Go_SQL_API_model_executed=False,formal_acceptance=False,formal_case_accepted_delta=0,execution_grant=False,STOP=True,FINAL=True))
assert all(pin(r['path'])==r for r in refs)
save('postseal.json',dict(status='PASS_REVIEW_PACKAGE_STABLE',stable_input_pins=len(refs),handoff_ref=pin(N/'HDF.json'),manifest_ref=pin(N/'MF.json')))
print(json.dumps(dict(handoff_ref=pin(N/'HDF.json'),manifest_ref=pin(N/'MF.json'),postseal_ref=pin(N/'postseal.json'))))
