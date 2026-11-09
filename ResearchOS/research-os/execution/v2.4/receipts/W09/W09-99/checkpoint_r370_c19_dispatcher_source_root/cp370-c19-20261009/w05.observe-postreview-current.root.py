"""Root read-only current observation, callable after all NF6 scopes close."""
from pathlib import Path
import hashlib,json
R=Path(r'D:\作品集\ResearchOS\research-os');V=R/'execution/v2.4';B=V/'receipts/W05/W05-99'
def pin(p):
    raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
current=[pin(V/n) for n in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')]
cp,ow,ss,cm=[json.loads(Path(ref['path']).read_bytes()) for ref in current]
assert cp['revision']>=384 and ow['revision']>=188
workers=[x for x in cp['workers'] if x.get('generation')=='fullw09-20261010-06']
assert len(workers)==4 and all(x.get('one_shot_consumed') is True and x.get('future_execution_permitted') is False and x['state']=='CLOSED_ACTUAL_NATIVE_PENDING_FORMAL_MODE' for x in workers)
review=B/'public22_to_main23_continuation_independent_review_codex/review-20261010-02-full/decision.json'
dr=pin(review);assert dr['sha256']=='98a9d6e9eb085f2b2a65827aee2f08aba787d821088914df7513ddf9015a3b08' and dr['bytes']==8959
i=json.loads((B/'public22_to_main23_continuation_caller_source_codex/continue-20261010-02/source-inputs.json').read_bytes());case=i['case_request_ref']
assert pin(Path(case['path']))==case
print(json.dumps(dict(schema='researchos.root-public22-continuation-current-observation.v1',issued_by='codex:/root',before_canonical_refs=current,expected_revisions=dict(checkpoint=cp['revision'],path_ownership=ow['revision'],step_state=ss.get('revision'),commands=cm['revision']),review_decision_ref=dr,case_request_ref=case,read_only=True,Canon_written=False,formal_acceptance=False,execution_grant=False),ensure_ascii=False))
