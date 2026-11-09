"""Read the four current Canon files after the independent Source review."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,os
N=Path(__file__).resolve().parent
R=Path(r'D:\作品集\ResearchOS\research-os');V=R/'execution/v2.4'
THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
def pin(p):
    raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,v):
    p=N/name
    with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
    return pin(p)
before=[pin(V/(x+'.json')) for x in ('checkpoint','path_ownership','step_state','commands')]
documents=[json.loads(Path(x['path']).read_bytes()) for x in before]
expected=dict(zip(('checkpoint','path_ownership','step_state','commands'),[x.get('revision') for x in documents]))
assert expected==dict(checkpoint=372,path_ownership=176,step_state=None,commands=39)
prior=json.loads((N/'RESUME.cp372-main23-qualified-runtime.live1067.root.json').read_bytes())
assert before==prior['canonical_refs'] and documents[0]['work_in_progress']['root_next_failure_ordinal_live']==1024
review=json.loads((N/'main23.v4.source-review.observer-input.root.json').read_bytes())
decision_ref=review['observed_refs'][2]
decision=json.loads(Path(decision_ref['path']).read_bytes())
assert decision['verdict']=='SOURCE_ACCEPTED_FOR_ROOT_REGISTRATION' and decision['review_author']=='codex:/root/full_w09_source_review'
now=datetime.now(timezone.utc)
assert now>datetime.fromisoformat(json.loads(Path(review['observed_refs'][0]['path']).read_bytes())['reviewed_utc'].replace('Z','+00:00'))
resume=save('main23.v4.postreview.resume.actual.root.json',dict(prior,created_utc=now.isoformat(),
    Main23='M4_SOURCE_AND_RUNTIME_NONAUTHOR_QUALIFIED_PENDING_ROOT_REGISTRATION_NO_ACTUAL_BUILD',
    source_review_refs=review['observed_refs'],source_review_witness_ref=pin(N/'main23.v4.source-review-witness.artifact.actual.root.json')))
request=save('main23.v4.postreview-current4.observer-input.root.json',dict(
    operation='POSTREVIEW_CURRENT_FOUR',observed_refs=before,peer_actor=None,
    expected_revisions=expected,root_resume_ref=resume,review_decision_ref=decision_ref))
print(json.dumps(dict(observer_input_ref=request,root_resume_ref=resume,
    current_canonical_refs=before,expected_revisions=expected),ensure_ascii=False,indent=2))
