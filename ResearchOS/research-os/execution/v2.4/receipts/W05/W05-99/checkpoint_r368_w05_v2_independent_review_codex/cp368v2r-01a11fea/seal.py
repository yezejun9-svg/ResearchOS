import hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent
def pin(p):
 p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(name,v):
 with (N/name).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
r=json.loads((N/'result.json').read_bytes());d=json.loads((N/'source-decision.json').read_bytes());refs=json.loads((N/'input-pins.json').read_bytes());g=json.loads((N/'source-guard.cleanup.actual.json').read_bytes())
assert r['status']=='SOURCE_ACCEPTED_FOR_ROOT_CP368_W05_REGISTRATION' and r['checks']==731 and r['negative_controls']==4 and r['pins']==216
assert g['closed'] is True and not g['errors'] and g['retained_handles_count']==0
assert all(pin(v['path'])==v for v in refs)
save('MF.json',dict(schema='researchos.cp368-w05-v2-source-review-manifest.v1',members=[pin(p) for p in sorted(N.iterdir()) if p.is_file()]))
save('HDF.json',dict(schema='researchos.cp368-w05-v2-independent-source-review.v1',actor_id=d['actor_id'],actor_role=d['actor_role'],status=d['decision'],manifest_ref=pin(N/'MF.json'),source_decision_ref=pin(N/'source-decision.json'),source_handoff_ref=d['source_handoff_ref'],source_manifest_ref=d['source_manifest_ref'],writer_ref=d['writer_ref'],facts_ref=d['facts_ref'],scope_ref=d['scope_ref'],prior_review_handoff_ref=d['prior_review_handoff_ref'],prior_review_manifest_ref=d['prior_review_manifest_ref'],prior_review_postseal_ref=d['prior_review_postseal_ref'],resolved_finding_ref=pin(N/'resolved-finding.json'),P1_findings=0,independent_checks=731,negative_controls=4,finite_held_inputs=216,guard_cleanup_ref=pin(N/'source-guard.cleanup.actual.json'),all_handles_closed=True,retained_handles_count=0,actual_executed=False,Main_Canon_written=False,formal_acceptance=False,formal_case_accepted_delta=0,product_execution_grant=False,fresh_Root_postseal_context_required=True,reviewed_source_snapshot_live=954,Root_reported_live_next=956,required_known_postcut_ordinals=[953,954,955],new_original_failures=[],source_cutoff=d['source_cutoff'],STOP=True,FINAL=True))
assert all(pin(v['path'])==v for v in refs)
save('postseal.json',dict(status='PASS_V2_SOURCE_REVIEW_INPUTS_STABLE',handoff_ref=pin(N/'HDF.json'),manifest_ref=pin(N/'MF.json'),decision_ref=pin(N/'source-decision.json'),all_input_pins_stable=True))
print(json.dumps(dict(handoff_ref=pin(N/'HDF.json'),manifest_ref=pin(N/'MF.json'),decision_ref=pin(N/'source-decision.json'),postseal_ref=pin(N/'postseal.json'))))

