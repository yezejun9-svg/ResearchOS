"""Owned source-review metadata IO only; no candidate execution."""
import pathlib,json,hashlib
OWN=pathlib.Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-03/desktop58_root_metadata_binding_independent_source_review_codex/e6a34fbc3c714f23b58781b5f6c913d0")
AUTHOR=pathlib.Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-03/desktop58_root_metadata_binding_preparation_codex/a03b8a59d79049ae87694932ac40ce5d")
def pin(p):
 raw=p.read_bytes()
 return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(name,value):
 with (OWN/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
review=json.loads((OWN/'review.json').read_bytes())
assert review['decision']=='REQUEST_CHANGES'
assert not (OWN/'manifest.json').exists() and not (OWN/'handoff.json').exists()
m=json.loads((AUTHOR/'manifest.json').read_bytes())
ins=json.loads((AUTHOR/'inputs.final.json').read_bytes())['entries']
for row in m['members']+ins: assert pin(pathlib.Path(row['path']))==row
snapshots=[]
for key,name in [('selected_pipeline_ref','pipeline.snapshot.txt'),('selected_builder_ref','builder.snapshot.txt'),('selected_resource_staging_ref','resource-staging.snapshot.txt')]:
 row=review[key];assert pin(pathlib.Path(row['path']))==row
 with (OWN/name).open('xb') as f:f.write(pathlib.Path(row['path']).read_bytes())
 snapshots.append(pin(OWN/name))
save('verification.json',{'schema':'researchos.independent-source-review-pure-io-verification.v1',
 'author_members':len(m['members']),'frozen_inputs':len(ins),'hash_drift':0,
 'snapshots':snapshots,'verification':review['verification'],'candidate_calls':0,'new_failure_origins':[]})
save('handoff.json',{'schema':'researchos.desktop58-root-metadata-binding-independent-source-review-handoff.v1',
 'reviewer':'codex:/root/f08_whole_scope_review','decision':'REQUEST_CHANGES','status':'STOPPED',
 'review_ref':pin(OWN/'review.json'),'tool_observations_ref':pin(OWN/'tool-observations.json'),
 'verification_ref':pin(OWN/'verification.json'),'selected_pipeline_ref':review['selected_pipeline_ref'],
 'selected_builder_ref':review['selected_builder_ref'],'requested_changes':['D58-META-R01'],
 'metadata_failed_count':0,'new_failure_origins':[],'source_acceptance':False,'formal_increment':0,
 'candidate_calls':0,'canonical_writes':0,
 'postseal_annex':'postseal-tool-observations.annex.json; explicit MF-excluded seal response annex'})
members=[pin(p) for p in sorted(OWN.iterdir()) if p.is_file()]
save('manifest.json',{'schema':'researchos.independent-source-review-manifest.v1','members':members,
 'count':len(members),'excluded_only_self':True,'postseal_annex_excluded':'postseal-tool-observations.annex.json',
 'source_acceptance':False,'formal_increment':0})
print(json.dumps({'review':pin(OWN/'review.json'),'handoff':pin(OWN/'handoff.json'),
 'manifest':pin(OWN/'manifest.json'),'members':len(members),'author_members':len(m['members']),
 'frozen_inputs':len(ins),'new_origins':0,'status':'STOPPED'},ensure_ascii=False))

