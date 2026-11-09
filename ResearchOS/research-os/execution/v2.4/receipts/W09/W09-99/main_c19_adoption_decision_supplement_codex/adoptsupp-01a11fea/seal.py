import hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent
def pin(p):
 p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(name,v):
 with (N/name).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
refs=json.loads((N/'input-pins.json').read_bytes());r=json.loads((N/'result.json').read_bytes());p=json.loads((N/'provenance.json').read_bytes());d=json.loads((N/'actual-decision.json').read_bytes());g=json.loads((N/'source-guard.cleanup.actual.json').read_bytes())
assert all(pin(v['path'])==v for v in refs)
assert r['status']=='PASS' and r['checks']==25 and r['finite_held_inputs']==71
assert g['closed'] is True and g['retained_handles_count']==0 and g['errors']==[] and g['verification']=='PASSED'
assert d['all_handles_closed'] is True and d['formal_acceptance'] is False and type(d['formal_case_accepted_delta']) is int and d['formal_case_accepted_delta']==0
save('MF.json',dict(schema='researchos.w09-main-c19-independent-adoption-manifest.v1',members=[pin(f) for f in sorted(N.iterdir()) if f.is_file()]))
save('HDF.json',dict(schema='researchos.w09-main-c19-independent-adoption-handoff.v1',actor_id=d['actor_id'],actor_role=d['actor_role'],status=d['decision'],manifest_ref=pin(N/'MF.json'),actual_decision_ref=pin(N/'actual-decision.json'),provenance_ref=pin(N/'provenance.json'),original_actual_review_handoff_ref=p['original_actual_review_handoff_ref'],original_actual_review_manifest_ref=p['original_actual_review_manifest_ref'],original_actual_review_postseal_ref=p['original_actual_review_postseal_ref'],calling_contract_ref=p['calling_contract_ref'],adoption_outcome_ref=d['adoption_outcome_ref'],source_handoff_ref=d['source_handoff_ref'],source_manifest_ref=d['source_manifest_ref'],guard_cleanup_ref=pin(N/'source-guard.cleanup.actual.json'),result_ref=pin(N/'result.json'),independent_checks=25,finite_held_inputs=71,all_handles_closed=True,formal_acceptance=False,formal_case_accepted_delta=0,actual_invocations_rerun=False,Main_or_Canon_written=False,new_original_failures=[],Root_reported_next_failure=953,pending_ordinals=[952],STOP=True,FINAL=True))
mf=json.loads((N/'MF.json').read_bytes());h=json.loads((N/'HDF.json').read_bytes())
assert h['actual_decision_ref'] in mf['members']
assert all(pin(v['path'])==v for v in refs+mf['members'])
save('postseal.json',dict(status='PASS_SUPPLEMENTAL_ADOPTION_DECISION_SEALED',handoff_ref=pin(N/'HDF.json'),manifest_ref=pin(N/'MF.json'),actual_decision_ref=pin(N/'actual-decision.json'),finite_input_count=len(refs),all_inputs_stable=True))
print(json.dumps(dict(handoff_ref=pin(N/'HDF.json'),manifest_ref=pin(N/'MF.json'),actual_decision_ref=pin(N/'actual-decision.json'),postseal_ref=pin(N/'postseal.json'))))

