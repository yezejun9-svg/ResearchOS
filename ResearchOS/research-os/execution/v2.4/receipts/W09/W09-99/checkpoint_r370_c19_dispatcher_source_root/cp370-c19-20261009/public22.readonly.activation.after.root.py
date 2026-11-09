from pathlib import Path
import hashlib,json,os
R=Path(r'D:\作品集\ResearchOS\research-os')
N=Path(__file__).resolve().parent
def pin(p):
    raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
registration=pin(R/'execution/v2.4/receipts/W05/W05-99/integration_codex/public22-recheck-registration-b9fbaa2bb39e4d85857f0354f2425dba/activate.result.json')
assert (registration['sha256'],registration['bytes'])==('7205f75fffa0ad2aabc45787f8cc0304629bb735c7199c4d0e2ee0d0f4d15876',2068)
a=json.loads(Path(registration['path']).read_bytes())
current=[pin(R/'execution/v2.4'/name) for name in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')]
assert current[:2]==a['proposed_after_refs']
assert json.loads(Path(current[0]['path']).read_bytes())['revision']==372
assert json.loads(Path(current[1]['path']).read_bytes())['revision']==176
q=json.loads((N/'public22.readonly.registration-request.actual.root.json').read_bytes())
assert current[2:]==q['before_canonical_refs'][2:]
scope=a['scope_ref'];actualscope=pin(Path(scope['path']))
assert (scope['sha256'],scope['bytes'])==(actualscope['sha256'],actualscope['bytes'])
archives=[]
for name,ref in zip(('checkpoint','path_ownership','step_state','commands'),current):
    p=N/('historical.cp372.'+name+'.json');raw=Path(ref['path']).read_bytes()
    with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    archive=pin(p);assert (archive['sha256'],archive['bytes'])==(ref['sha256'],ref['bytes']);archives.append(archive)
result=dict(schema='researchos.root-public22-existing-actual-registration-observation.v1',issued_by='codex:/root',
    root_thread_id='01a11007-5233-7ca1-b71f-9e9e5ce84c98',registration_result_ref=registration,scope_ref=scope,
    current_canonical_refs=current,archive_refs=archives,new_native_children=0,formal_acceptance=False)
with (N/'public22.readonly.activation.after.observed.root.json').open('xb') as f:
    f.write((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf-8'));f.flush();os.fsync(f.fileno())
print(json.dumps(result,ensure_ascii=False,indent=2))

