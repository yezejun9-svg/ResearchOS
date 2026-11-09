"""Seal owned independent source review metadata only."""
import pathlib,json,hashlib
OWN=pathlib.Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-03/current58_cli_terminal_closure_revision_independent_source_review_codex/4829c493cfa7484480869e8c3196d68d")
AUTHOR=pathlib.Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-03/current58_cli_terminal_closure_revision_preparation_codex/f7d6a38fd86e45af951cf022cf7514b5")
def pin(p):
 raw=p.read_bytes()
 return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(name,value):
 with (OWN/name).open('xb') as out:
  out.write((json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
review=json.loads((OWN/'review.json').read_bytes())
assert review['decision']=='READY_SOURCE_PREPARATION_ONLY'
assert not (OWN/'handoff.json').exists() and not (OWN/'manifest.json').exists()
author=json.loads((AUTHOR/'manifest.json').read_bytes())
inputs=json.loads((AUTHOR/'inputs.before.json').read_bytes())
for row in author['members']+inputs: assert pin(pathlib.Path(row['path']))==row
source=review['selected_producer_ref']
raw=pathlib.Path(source['path']).read_bytes()
assert len(raw)==source['bytes'] and hashlib.sha256(raw).hexdigest()==source['sha256']
with (OWN/'reviewed-source.snapshot.txt').open('xb') as out: out.write(raw)
save('verification.json',{'schema':'researchos.independent-source-review-pure-io-verification.v1',
 'author_members':len(author['members']),'frozen_inputs':len(inputs),'drift':0,
 'facts':review['verification']['facts'],'candidate_calls':0,'current_dynamic_reads':0,
 'failure_origin_ref':pin(OWN/'failure-origin.review-js-parser.json')})
save('handoff.json',{'schema':'researchos.current58-root-terminal-closure-independent-source-review-handoff.v1',
 'reviewer':'codex:/root/f08_whole_scope_review','status':'STOPPED','decision':'READY_SOURCE_PREPARATION_ONLY',
 'review_ref':pin(OWN/'review.json'),'tool_observations_ref':pin(OWN/'tool-observations.json'),
 'verification_ref':pin(OWN/'verification.json'),'selected_producer_ref':source,
 'prior_REQUEST_ref':review['previous_REQUEST_ref'],'closed_findings':['C58-CLOSE-R01','C58-CLOSE-R02'],
 'new_failure_origins':[pin(OWN/'failure-origin.review-js-parser.json')],
 'metadata_failed_count':1,'failure_numeric_outer':None,'failure_numeric_native':None,
 'candidate_calls':0,'canonical_writes':0,'source_acceptance':False,'case_qualification':False,
 'formal_increment':0,'actual_authorization':'OPEN','manifest_name':'manifest.json',
 'postseal_annex':'postseal-tool-observations.annex.json; explicit MF-excluded seal-result annex'})
members=[pin(p) for p in sorted(OWN.iterdir()) if p.is_file()]
save('manifest.json',{'schema':'researchos.independent-source-review-manifest.v1',
 'members':members,'count':len(members),'excluded_only_self':True,
 'postseal_annex_excluded':'postseal-tool-observations.annex.json',
 'source_acceptance':False,'formal_increment':0})
print(json.dumps({'review':pin(OWN/'review.json'),'handoff':pin(OWN/'handoff.json'),
 'manifest':pin(OWN/'manifest.json'),'failure_origin':pin(OWN/'failure-origin.review-js-parser.json'),
 'members':len(members),'author_members':len(author['members']),'frozen_inputs':len(inputs),
 'new_origins':1,'status':'STOPPED'},ensure_ascii=False))

