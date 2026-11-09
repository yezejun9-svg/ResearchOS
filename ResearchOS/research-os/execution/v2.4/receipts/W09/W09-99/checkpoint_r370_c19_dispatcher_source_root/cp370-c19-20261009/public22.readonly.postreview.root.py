from pathlib import Path
import hashlib,json,os
R=Path(r'D:\作品集\ResearchOS\research-os')
N=Path(__file__).resolve().parent
def pin(p):
    raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
refs=[pin(R/'execution/v2.4'/name) for name in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')]
expected=[
('667f1515a5b62e2d7ee4948bf17055b7f9a0cce6391ad66c76ea70dde99255ba',4533514),
('4e294919209b1d65b5f869f613ada3a706a16ccaa8fb194dfca1d8982ddb7d3a',211140),
('fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149',257446),
('28b4ba18ce2ab3ce03287651e311ae2bd36293b53fd8c298e5bf1f231f56d027',68968)]
assert [(x['sha256'],x['bytes']) for x in refs]==expected
decision=pin(R/'execution/v2.4/receipts/W05/W05-99/public22_existing_observation_root_caller_independent_source_review_codex/review-20261010-01/decision.json')
assert (decision['sha256'],decision['bytes'])==('6fdd5d4e5bd08e82070c63cf0c6ea80f6889f44cdbe7db97290dbfc489a61893',5182)
case=pin(N/'public22.v4.case-request.actual.root.json')
assert (case['sha256'],case['bytes'])==('df1c909f1675fec2a44ab8dc9285147c181bcfdf629f127305d2f529e1c3a48f',241)
result=dict(schema='researchos.root-public22-existing-postreview-read.v1',issued_by='codex:/root',
    root_thread_id='01a11007-5233-7ca1-b71f-9e9e5ce84c98',canonical_refs=refs,
    expected_revisions=dict(checkpoint=371,path_ownership=175,step_state=None,commands=39),
    review_decision_ref=decision,case_request_ref=case,formal_acceptance=False,new_native_children=0)
with (N/'public22.readonly.postreview.observed.root.json').open('xb') as f:
    f.write((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf-8'));f.flush();os.fsync(f.fileno())
print(json.dumps(result,ensure_ascii=False,indent=2))

