"""Seal actual registered Canon and append a Root resume; no acceptance or consumers."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,os

N=Path(__file__).resolve().parent
W=N.parent.parent
R=Path('D:/作品集/ResearchOS/research-os')
S=W/'checkpoint_r369_native_source_root/cp369-c19-20261009'
V4=W/'checkpoint_r370_c19_dispatcher_source_codex/cp370proposal-20261009-v4'

def pin(path):
    path=path.resolve(strict=True);raw=path.read_bytes()
    return dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))

def read(ref):
    assert set(ref)=={'path','sha256','bytes'} and pin(Path(ref['path']))==ref
    return Path(ref['path']).read_bytes()

def save(path,value):
    with path.open('xb') as file:
        file.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode());file.flush();os.fsync(file.fileno())
    return pin(path)

resume=json.loads((S/'RESUME.cp369-main-profile-adopted.postseal.live1005.root.json').read_bytes())
before=resume['canonical_refs']
result_ref=pin(V4/'registration.activate.root.json')
assert result_ref['sha256']=='4a41818929e31b7c194c42a9b54a84980bbb2d7f92882946d501162406d642a1' and result_ref['bytes']==1594
result=json.loads(read(result_ref))
refs=[pin(R/'execution/v2.4'/(name+'.json')) for name in ('checkpoint','path_ownership','step_state','commands')]
assert refs[:2]==[result['transaction']['checkpoint_ref'],result['transaction']['ownership_ref']]
assert refs[2:]==before[2:]
cp,ow=[json.loads(read(ref)) for ref in refs[:2]]
assert cp['revision']==370 and cp['expected_previous_revision']==369 and ow['revision']==174
assert len(cp['failure_counters'])==1002 and cp['work_in_progress']['root_next_failure_ordinal_live']==1005
archives=[]
for name,ref in zip(('checkpoint','path_ownership','step_state','commands'),refs):
    path=N/('historical.cp370.'+name+'.json')
    with path.open('xb') as file:file.write(read(ref));file.flush();os.fsync(file.fileno())
    archive=pin(path);assert archive['sha256']==ref['sha256'] and archive['bytes']==ref['bytes'];archives.append(archive)
vector=dict(schema='researchos.w09-c19-consumer-current-canonical-vector.v1',issued_by='codex:/root',created_utc=datetime.now(timezone.utc).isoformat(),
    checkpoint_revision=370,path_ownership_revision=174,refs=refs)
vector_ref=save(N/'Main-C19-consumers-current-canonical-vector.actual.root.json',vector)
resume.update(created_utc=datetime.now(timezone.utc).isoformat(),canonical_refs=refs,historical_cp369_canonical_refs=resume['historical_canonical_refs'],
    historical_canonical_refs=archives,CP370_status='ACTUAL_ROOT_REGISTERED_PENDING_INDEPENDENT_ACTUAL_REVIEW',registration_result_ref=result_ref,
    consumer_current_vector_ref=vector_ref,registered_failure_count=1002,highest_registered_ordinal=1004,next_original_failure_ordinal_live=1005,
    CP370_actual_original_tool_io_ref=pin(N/'registrar-v4-activate.actual.original-tool-io.root.json'),C19_actual_consumers_status='NOT_RUN')
ri=R/'execution/v2.4/receipts/W05/W05-99/genuine_schema22_resource_independent_review_codex/schema22-20261009-01'
resume['W05_schema22_programme_provenance_review_refs']=[pin(ri/name) for name in ('HDF.json','MF.json','decision.json')]
resume['W05_schema22_programme_provenance_status']='PINNED_SCHEMA22_PROGRAMME_PROVENANCE_ACCEPTED_FORMAL_RELEASE_OPEN'
for ref in refs:read(ref)
resume_ref=save(N/'RESUME.cp370-registered.live1005.root.json',resume)
print(json.dumps(dict(resume_ref=resume_ref,current_vector_ref=vector_ref,canonical_refs=refs,next_original=1005,
    registered_failure_count=1002,dispatcher_run=False,Native_rerun=False,formal_delta=0),ensure_ascii=False),flush=True)
