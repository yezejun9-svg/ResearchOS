import hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent
def pin(p):
 p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(name,v):
 with (N/name).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
r=json.loads((N/'result.json').read_bytes());d=json.loads((N/'source-decision.json').read_bytes());refs=json.loads((N/'input-pins.json').read_bytes());g=json.loads((N/'source-guard.cleanup.actual.json').read_bytes())
assert r['status']=='REQUEST_CHANGES' and r['checks']==45 and r['negative_controls']==12 and r['pins']==187
assert g['closed'] is True and not g['errors'] and g['retained_handles_count']==0
assert all(pin(v['path'])==v for v in refs)
save('MF.json',dict(schema='researchos.cp368-w05-source-review-manifest.v1',members=[pin(p) for p in sorted(N.iterdir()) if p.is_file()]))
save('HDF.json',dict(schema='researchos.cp368-w05-independent-source-review.v1',actor_id=d['actor_id'],actor_role=d['actor_role'],status=d['decision'],manifest_ref=pin(N/'MF.json'),source_decision_ref=pin(N/'source-decision.json'),source_handoff_ref=d['source_handoff_ref'],source_manifest_ref=d['source_manifest_ref'],findings_ref=d['findings_ref'],P1_findings=1,independent_checks=45,negative_controls=12,finite_held_inputs=187,guard_cleanup_ref=pin(N/'source-guard.cleanup.actual.json'),all_handles_closed=True,retained_handles_count=0,actual_executed=False,Main_Canon_written=False,formal_acceptance=False,formal_case_accepted_delta=0,execution_grant=False,new_original_failures=d['new_reviewer_original_failures'],Root_reported_live_next=954,source_cutoff=d['source_cutoff'],STOP=True,FINAL=True))
assert all(pin(v['path'])==v for v in refs)
save('postseal.json',dict(status='REQUEST_CHANGES_SEALED_INPUTS_STABLE',handoff_ref=pin(N/'HDF.json'),manifest_ref=pin(N/'MF.json'),decision_ref=pin(N/'source-decision.json'),all_input_pins_stable=True))
print(json.dumps(dict(handoff_ref=pin(N/'HDF.json'),manifest_ref=pin(N/'MF.json'),decision_ref=pin(N/'source-decision.json'),postseal_ref=pin(N/'postseal.json'))))

