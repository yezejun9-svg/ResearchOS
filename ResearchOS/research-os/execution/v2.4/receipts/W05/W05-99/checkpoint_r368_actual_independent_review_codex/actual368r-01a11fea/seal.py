import hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent
def pin(p):
 p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(name,v):
 with (N/name).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
refs=json.loads((N/'input-pins.json').read_bytes());r=json.loads((N/'result.json').read_bytes());s=json.loads((N/'actual-summary.json').read_bytes());g=json.loads((N/'source-guard.cleanup.actual.json').read_bytes())
assert r['status']=='ACTUAL_CP368_OW172_W05_REGISTRATION_VERIFIED_PASS' and r['checks']==37 and r['pins']==227
assert g['closed'] is True and not g['errors'] and g['retained_handles_count']==0
assert all(pin(v['path'])==v for v in refs)
newrefs=[dict(ordinal=i,origin_ref=pin(N/f'failure{i}.original-tool-io.json')) for i in range(959,964)]
save('post-registration-pending.json',dict(CP_snapshot_live=958,CP_snapshot_pending_ordinals=list(range(953,958)),Root_reported_current_live=964,post_registration_pending_ordinals=list(range(958,964)),original958=dict(ordinal=958,classification='Root-reported functions.exec parsing SyntaxError before shell invocation; all numerical exits NULL',independently_read_origin=False,origin_ref=None),reviewer_originals=newrefs,Canon_rewritten=False,original_actual_registration_result_unchanged=True))
save('actual-decision.json',dict(schema='researchos.cp368-w05-independent-actual-decision.v1',decision=r['status'],actor_id='codex:/root/attach_fixture_source_review',actor_role='INDEPENDENT_NON_AUTHOR',actual_summary_ref=pin(N/'actual-summary.json'),Source_review_handoff_ref=s['Source_review_ref'],actual_proof_ref=s['actual_proof_ref'],actual_live_context_ref=s['actual_live_context_ref'],checkpoint_ref=s['checkpoint_ref'],ownership_ref=s['ownership_ref'],step_state_ref=s['step_state_ref'],commands_ref=s['commands_ref'],commands_document_revision=39,registered_failure_count=950,source_cutoff=dict(highest_ordinal=952,next_failure_ordinal=953),actual_shared_and_nested_live=958,actual_pending_ordinals=list(range(953,958)),all_handles_closed=True,formal_acceptance=False,formal_case_accepted_delta=0,parent_acceptance=False,actual_registration_replayed=False,product_calls=0,Main_Canon_written_by_reviewer=False,new_reviewer_original_failures=newrefs,Root_reported_current_live=964,post_registration_pending_ref=pin(N/'post-registration-pending.json'),W05_actual_validation_reviewed=False))
save('MF.json',dict(schema='researchos.cp368-w05-independent-actual-review-manifest.v1',members=[pin(p) for p in sorted(N.iterdir()) if p.is_file()]))
save('HDF.json',dict(schema='researchos.cp368-w05-independent-actual-review.v1',actor_id='codex:/root/attach_fixture_source_review',actor_role='INDEPENDENT_NON_AUTHOR',status=r['status'],manifest_ref=pin(N/'MF.json'),actual_decision_ref=pin(N/'actual-decision.json'),report_ref=pin(N/'REPORT.md'),result_ref=pin(N/'result.json'),actual_summary_ref=pin(N/'actual-summary.json'),guard_cleanup_ref=pin(N/'source-guard.cleanup.actual.json'),independent_checks=37,finite_held_inputs=227,all_handles_closed=True,retained_handles_count=0,checkpoint_ref=s['checkpoint_ref'],ownership_ref=s['ownership_ref'],actual_live_context_ref=s['actual_live_context_ref'],formal_acceptance=False,formal_case_accepted_delta=0,parent_acceptance=False,Main_Canon_written_by_reviewer=False,W05_actual_outputs_not_read_or_guarded=True,new_reviewer_original_failures=newrefs,Root_reported_current_live=964,post_registration_pending_ref=pin(N/'post-registration-pending.json'),STOP=True,FINAL=True))
mf=json.loads((N/'MF.json').read_bytes())
assert all(pin(v['path'])==v for v in refs+mf['members'])
save('postseal.json',dict(status='PASS_ACTUAL_CP368_REVIEW_INPUTS_STABLE',handoff_ref=pin(N/'HDF.json'),manifest_ref=pin(N/'MF.json'),actual_decision_ref=pin(N/'actual-decision.json'),held_input_count=len(refs),all_input_pins_stable=True))
print(json.dumps(dict(handoff_ref=pin(N/'HDF.json'),manifest_ref=pin(N/'MF.json'),actual_decision_ref=pin(N/'actual-decision.json'),postseal_ref=pin(N/'postseal.json'))))

