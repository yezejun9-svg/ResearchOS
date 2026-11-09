"""Pure IO sealer for this review namespace only; never imports candidate."""
import pathlib,json,hashlib
OWN=pathlib.Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-03/current58_cli_terminal_closure_independent_source_review_codex/7c2f53785d284c10b329e9aa7c6c3541")
AUTHOR=pathlib.Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-03/current58_cli_terminal_closure_preparation_codex/25b9dd0b813a48689256356402789b13")
def pin(path):
 raw=path.read_bytes()
 return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(name,obj):
 with (OWN/name).open('xb') as s:
  s.write((json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
review=json.loads((OWN/'review.json').read_bytes())
assert review['decision']=='REQUEST_CHANGES'
assert not (OWN/'manifest.json').exists() and not (OWN/'handoff.json').exists()
mf=json.loads((AUTHOR/'manifest.json').read_bytes())
for row in mf['members']:
 assert pin(pathlib.Path(row['path']))==row
inputs=json.loads((AUTHOR/'static.final.json').read_bytes())['inputs']
for row in inputs:
 assert pin(pathlib.Path(row['path']))==row
source=review['selected_producer_ref']
raw=pathlib.Path(source['path']).read_bytes()
assert len(raw)==source['bytes'] and hashlib.sha256(raw).hexdigest()==source['sha256']
with (OWN/'reviewed-source.snapshot.txt').open('xb') as s: s.write(raw)
save('verification.json',{
 'schema':'researchos.independent-source-review-pure-io-verification.v1',
 'author_members_verified':len(mf['members']),'frozen_inputs_verified':len(inputs),
 'drift':0,'selected_source_ref':source,'readonly_snapshot_ref':pin(OWN/'reviewed-source.snapshot.txt'),
 'candidate_calls':0,'target_calls':0,'canonical_writes':0,'new_failure_origins':[],
 'checks':review['verification']['checks']})
save('handoff.json',{
 'schema':'researchos.current58-root-terminal-closure-independent-source-review-handoff.v1',
 'reviewer':'codex:/root/f08_whole_scope_review','status':'STOPPED','decision':'REQUEST_CHANGES',
 'review_ref':pin(OWN/'review.json'),'original_tool_observations_ref':pin(OWN/'tool-observations.json'),
 'verification_ref':pin(OWN/'verification.json'),'selected_producer_ref':source,
 'requested_change_ids':['C58-CLOSE-R01','C58-CLOSE-R02'],
 'source_acceptance':False,'case_qualification':False,'formal_increment':0,
 'candidate_calls':0,'new_failure_origins':[],'metadata_failed_count':0,
 'canonical_writes':0,'future_actual_authorization':'OPEN',
 'manifest_name':'manifest.json',
 'postseal_annex':'postseal-tool-observations.annex.json; explicitly outside manifest to avoid seal tool-result hash cycles'})
members=[pin(x) for x in sorted(OWN.iterdir()) if x.is_file()]
save('manifest.json',{
 'schema':'researchos.independent-source-review-manifest.v1',
 'members':members,'count':len(members),'excluded_only_self':True,
 'postseal_annex_excluded':'postseal-tool-observations.annex.json',
 'source_acceptance':False,'formal_increment':0})
print(json.dumps({'review':pin(OWN/'review.json'),'handoff':pin(OWN/'handoff.json'),
 'manifest':pin(OWN/'manifest.json'),'members':len(members),'author_members':len(mf['members']),
 'frozen_inputs':len(inputs),'new_origins':0,'status':'STOPPED'},ensure_ascii=False))

