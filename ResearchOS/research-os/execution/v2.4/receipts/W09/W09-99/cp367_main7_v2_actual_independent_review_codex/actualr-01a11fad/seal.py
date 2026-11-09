import hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent;W=N.parents[1]
def pin(p):
 p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,v):
 with (N/n).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
refs=json.loads((N/'input-pins.json').read_bytes());r=json.loads((N/'result.json').read_bytes());cl=json.loads((N/'source-guard.cleanup.actual.json').read_bytes());summary=json.loads((N/'actual-summary.json').read_bytes())
assert all(pin(v['path'])==v for v in refs)
assert r['checks']==70 and r['pins']==312 and cl['closed'] and not cl['errors'] and cl['retained_handles_count']==0
p=W/'w09_c19_main_root_producer_source_codex/mainc19p-1a11fbc/failure952.original-tool-io.json'
pending_ref=dict(path=str(p),sha256='a7b5854ed63594d0362bbe902f7101f7ce92c7b8005b479c60e95619df19a935',bytes=31394)
assert pin(p)==pending_ref
pending=json.loads(p.read_bytes())
assert pending['root_assigned_ordinal']==952 and pending['original_chunk_id']=='b2f026' and pending['outer_exit']==1 and all(pending[k] is None for k in ('SourcePython_exit','Go_exit','Native_exit','Model_exit'))
save('post-adoption-pending.json',dict(ordinal=952,origin_ref=pending_ref,outer_exit=1,SourcePython_exit=None,Go_exit=None,Native_exit=None,Model_exit=None,root_live_after_assignment=953,registered_in_CP367=False,original_actual_invocations_unchanged=True,classification='External Source actor read-query failure after administrative and Main adoption success; successor checkpoint pending'))
save('MF.json',dict(schema='researchos.cp367-main7-v2-independent-actual-review-manifest.v1',members=[pin(p) for p in sorted(N.iterdir()) if p.is_file()]))
save('HDF.json',dict(schema='researchos.cp367-main7-v2-independent-actual-review.v1',actor_id='codex:/root/attach_fixture_source_review',actor_role='INDEPENDENT_NON_AUTHOR',decision=r['status'],status=r['status'],manifest_ref=pin(N/'MF.json'),report_ref=pin(N/'REPORT.md'),result_ref=pin(N/'result.json'),actual_summary_ref=pin(N/'actual-summary.json'),checkpoint_ref=summary['checkpoint_ref'],ownership_ref=summary['ownership_ref'],step_state_ref=summary['step_state_ref'],commands_ref=summary['commands_ref'],commands_document_revision=39,actual_administrative_registration_verified=True,actual_Main7_source_adoption_verified=True,current_Source21_bytes_match=True,old934_raw_semantic_preserved=True,registered_failures=949,Source_cut951_next952=True,root_live_at_successful_invocations=952,current_Root_reported_live=953,post_adoption_pending_ref=pin(N/'post-adoption-pending.json'),all_actual_guard_files_directories_closed=True,all_review_guards_closed=True,retained_handles=0,review_guard_cleanup_ref=pin(N/'source-guard.cleanup.actual.json'),independent_checks=70,finite_exact_held_inputs=312,additional_post_adoption_origin_pin_verified=True,new_reviewer_original_failures=[],Main_native_packet_current=False,real_dispatcher_current=False,formal_acceptance=False,formal_case_accepted_delta=0,new_parent_acceptance=0,product_Go_SQL_API_model_calls=0,actual_invocations_rerun=False,STOP=True,FINAL=True))
assert all(pin(v['path'])==v for v in refs) and pin(p)==pending_ref
save('postseal.json',dict(status='PASS_ACTUAL_REVIEW_INPUTS_STABLE',handoff_ref=pin(N/'HDF.json'),manifest_ref=pin(N/'MF.json'),held_input_count=len(refs),post_adoption_origin_ref=pending_ref))
print(json.dumps(dict(handoff_ref=pin(N/'HDF.json'),manifest_ref=pin(N/'MF.json'),postseal_ref=pin(N/'postseal.json'))))
