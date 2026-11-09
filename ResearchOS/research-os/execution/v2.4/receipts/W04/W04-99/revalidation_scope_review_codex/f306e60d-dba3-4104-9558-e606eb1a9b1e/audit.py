from pathlib import Path
import json,hashlib,datetime
ROOT=Path('D:/作品集/ResearchOS/research-os');D=Path(__file__).resolve().parent;P=ROOT/'.local/worktrees/codex-w0599-command-queue/execution/v2.4/receipts/W05/W05-99/historical_fixture_executor_codex/w04-revalidation-readonly-d54d2059-7026-4717-b353-c287d9991e6a'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):return {'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def verify(r):
 p=Path(r['path']);p=p if p.is_absolute() else ROOT/p
 assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'].removeprefix('sha256:'),str(p)
 return p
assert ref(P/'proposal.json')['sha256']=='5e880857f67d35c712ca9813ce3ae6dd18e9f1c632aa4a9b6ef9234f40a03218'
for r in read(P/'manifest.json'):verify(dict(r,path=str(P/r['path'])))
assert read(P/'inputs.before.json')==read(P/'inputs.after.json')
state=read(ROOT/'execution/v2.4/step_state.json');oldrow=read(P/'previous_row.observed.json');current=next(x for x in state['steps'] if x['id']=='W04-99');assert current==oldrow
roots={};oldrefs=[]
for r in oldrow['evidence']:
 p=verify({'path':'execution/v2.4/'+r['path'],'sha256':r['sha256']});v=read(p);oldrefs.append(ref(p))
 if v.get('schema') in ['researchos.w04.independent-review.v1','researchos.w04.current-context.v1','researchos.w04.root-observed-issuance.v1']:roots[v['schema']]=p
assert len(roots)==3
context=read(roots['researchos.w04.current-context.v1']);review=read(roots['researchos.w04.independent-review.v1']);issue=read(roots['researchos.w04.root-observed-issuance.v1']);message=read(verify(issue['message_ref']));assert message['sender']==issue['issuer_id']==review['verifier_id']==oldrow['verifier_id'];assert message['review_sha256']==ref(roots['researchos.w04.independent-review.v1'])['sha256'];assert issue['observer_id'] not in [review['executor_id'],review['verifier_id']];assert review['executor_id']==oldrow['executor_id']
verify(review['current_context_ref']);verify(issue['current_context_ref']);verify(issue['review_ref']);verify(review['evidence_index_ref']);verify(context['execution_index'])
diffs=[]
for g in ['source_files','lock_files']:
 for r in context['version_vector'][g]:
  p=ROOT/r['path'];h=ref(p)['sha256'] if p.is_file() else None
  if h!=r['sha256']:diffs.append({'group':g,'path':r['path'],'old_sha256':r['sha256'],'current_sha256':h})
assert diffs==read(P/'old_vector_current_differences.json') and len(diffs)==30
formal=ROOT/'execution/v2.4/formal_case_index.py';raw=formal.read_bytes();prefix={'bytes':51719,'sha256':hashlib.sha256(raw[:51719]).hexdigest()}
a={'schema':'researchos.w04.revalidation-scope-audit.v1','actor':'codex:/root/w05_merge_review','proposal_bundle':[ref(p) for p in sorted(P.glob('*.json'))],'canonical_state':ref(ROOT/'execution/v2.4/step_state.json'),'previous_row_matches_current':True,'old_evidence_refs':oldrefs,'old_root_count':3,'old_issuance_message':ref(verify(issue['message_ref'])),'old_actor_chain_consistent':True,'current_differences':diffs,'formal_reader':ref(formal),'protected_prefix':prefix,'policy_sources':[ref(ROOT/p) for p in ['execution/v2.4/receipts/W04/W04-99/formal_validator_codex/README.md','execution/v2.4/receipts/W04/W04-99/formal_validator_codex/validate.py','execution/v2.4/formal_profile_w07.py','.local/worktrees/v24-continuation/spec/v2.4/contracts/acceptance.json']],'no_execution_or_canonical_mutation':True}
(D/'audit.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'audit':ref(D/'audit.json'),'prefix':prefix,'differences':len(diffs)}))

