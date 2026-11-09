"""Prepare exact live current-four readback after the independent Source review."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os
N=Path(__file__).resolve().parent;R=Path(r'D:\作品集\ResearchOS\research-os')
def pin(p):
    raw=Path(p).read_bytes();return dict(path=str(Path(p)),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,v):
    p=N/name
    with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
    return pin(p)
resume_ref=pin(N/'RESUME.cp373-source-adoptions.live1097.root.json')
resume=json.loads(Path(resume_ref['path']).read_bytes())
current=[pin(R/'execution/v2.4'/(name+'.json')) for name in ('checkpoint','path_ownership','step_state','commands')]
assert current==resume['canonical_refs']
prepared=json.loads((N/'old21.v3.prepared-review-bindings.root.json').read_bytes())
payload=save('old21.v3.postreview-current4.payload.actual.root.json',dict(
    schema='researchos.root-old21-postreview-current-four.v1',issued_by='codex:/root',canonical_refs=current,
    expected_revisions=resume['expected_revisions'],root_resume_ref=resume_ref,
    review_decision_ref=prepared['caller']['review_refs'][2],created_utc=datetime.now(timezone.utc).isoformat()))
observer=save('old21.v3.postreview-current4.observer-input.root.json',dict(
    operation='POSTREVIEW_CURRENT_FOUR',observed_refs=current,peer_actor=None))
print(json.dumps(dict(payload_ref=payload,observer_input_ref=observer,current_canonical_refs=current),ensure_ascii=False,indent=2))
