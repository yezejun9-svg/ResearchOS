import hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent
def pin(p):
 p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,v):
 with (N/n).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
refs=json.loads((N/'input-pins.json').read_bytes());q=json.loads((N/'qualification.json').read_bytes());cleanup=json.loads((N/'source-guard.cleanup.actual.json').read_bytes())
assert all(pin(r['path'])==r for r in refs)
assert q['checks']==13 and q['pins']==32 and cleanup['closed'] and not cleanup['errors'] and cleanup['retained_handles_count']==0
save('MF.json',dict(schema='researchos.cp367-live-context-independent-review-manifest.v1',members=[pin(p) for p in sorted(N.iterdir()) if p.is_file()]))
save('HDF.json',dict(schema='researchos.cp367-live-context-independent-review.v1',actor_id='codex:/root/attach_fixture_source_review',actor_role='INDEPENDENT_NON_AUTHOR',decision=q['status'],status=q['status'],manifest_ref=pin(N/'MF.json'),qualification_ref=pin(N/'qualification.json'),context_ref=q['context_ref'],mapping_ref=q['mapping_ref'],source_handoff_ref=q['source_handoff_ref'],source_manifest_ref=q['source_manifest_ref'],prior_independent_review_ref=q['prior_independent_review_ref'],root_registration_qualified=True,qualified_scope=q['scope'],qualification_lapses_if=q['qualification_lapses_if'],freshness_ref=pin(N/'freshness.json'),guard_cleanup_ref=pin(N/'source-guard.cleanup.actual.json'),all_acquired_guards_closed=True,retained_handles=0,independent_checks=13,finite_exact_inputs=32,new_original_failures=[],actual_registration_executed=False,actual_Main_Canon_written=False,Go_SQL_API_model_executed=False,formal_acceptance=False,formal_case_accepted_delta=0,STOP=True,FINAL=True))
assert all(pin(r['path'])==r for r in refs)
save('postseal.json',dict(status='PASS_PACKAGE_INPUTS_STABLE',handoff_ref=pin(N/'HDF.json'),manifest_ref=pin(N/'MF.json'),input_count=len(refs)))
print(json.dumps(dict(handoff_ref=pin(N/'HDF.json'),manifest_ref=pin(N/'MF.json'),postseal_ref=pin(N/'postseal.json'))))
