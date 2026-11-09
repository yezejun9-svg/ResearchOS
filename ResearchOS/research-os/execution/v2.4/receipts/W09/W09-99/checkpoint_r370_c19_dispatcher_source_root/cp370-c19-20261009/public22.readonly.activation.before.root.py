from pathlib import Path
import hashlib,json,os
R=Path(r'D:\作品集\ResearchOS\research-os')
N=Path(__file__).resolve().parent
def pin(p):
    raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
facts=pin(R/'execution/v2.4/receipts/W05/W05-99/integration_codex/public22-recheck-registration-b9fbaa2bb39e4d85857f0354f2425dba/facts.root.json')
assert (facts['sha256'],facts['bytes'])==('2222f5d94aa798c657bbff4152d0beaff1074509be70ffb2fc49850d2275d38a',3716)
f=json.loads(Path(facts['path']).read_bytes())
current=[pin(R/'execution/v2.4'/name) for name in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')]
assert current==f['before_canonical_refs']
result=dict(schema='researchos.root-public22-existing-activation-before-observation.v1',issued_by='codex:/root',
    root_thread_id='01a11007-5233-7ca1-b71f-9e9e5ce84c98',facts_ref=facts,before_canonical_refs=current,formal_acceptance=False,new_native_children=0)
with (N/'public22.readonly.activation.before.observed.root.json').open('xb') as out:
    out.write((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf-8'));out.flush();os.fsync(out.fileno())
print(json.dumps(result,ensure_ascii=False,indent=2))

